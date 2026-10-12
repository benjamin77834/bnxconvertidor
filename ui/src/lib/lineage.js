// ============================================================
// BNX Lineage — utilidades para derivar el linaje de un grafo
// convertido (nivel NODO y nivel COLUMNA) desde el `result` que
// devuelve el backend (/compile).
//
// Nivel NODO:   quien alimenta a quien (upstream/downstream) usando
//               edges/parents/children ya presentes en el grafo.
// Nivel COLUMNA: de donde viene cada columna de un nodo, trazada
//               hacia atras hasta las columnas de los SOURCE, usando
//               rule.select / rule.dml_fields / rule.join_key y el
//               dml_schema (columnas por source).
//
// Todo es best-effort y determinístico: si una regla no permite
// resolver una columna, se marca como "passthrough" o "derivada".
// ============================================================

// ---------- helpers de grafo ----------
function buildIndex(data) {
  const nodes = data?.nodes || []
  const edges = data?.edges || []
  const byId = {}
  nodes.forEach(n => { byId[n.id] = n })
  const parents = {}   // id -> [ids]
  const children = {}  // id -> [ids]
  nodes.forEach(n => { parents[n.id] = []; children[n.id] = [] })
  edges.forEach(e => {
    if (children[e.from]) children[e.from].push(e.to)
    if (parents[e.to]) parents[e.to].push(e.from)
  })
  // fallback a parents/children declarados en el nodo si no hubo edges
  nodes.forEach(n => {
    if (parents[n.id].length === 0 && Array.isArray(n.parents)) parents[n.id] = [...n.parents]
    if (children[n.id].length === 0 && Array.isArray(n.children)) children[n.id] = [...n.children]
  })
  return { nodes, edges, byId, parents, children }
}

// Recorrido transitivo (BFS) en una direccion. Devuelve niveles:
// [{depth, ids:[...]}] para poder dibujar la cadena ordenada.
function traverse(startId, adj) {
  const levels = []
  let frontier = [...(adj[startId] || [])]
  const seen = new Set([startId])
  let depth = 1
  while (frontier.length) {
    const uniq = frontier.filter(id => !seen.has(id))
    if (uniq.length === 0) break
    uniq.forEach(id => seen.add(id))
    levels.push({ depth, ids: uniq })
    const next = []
    uniq.forEach(id => (adj[id] || []).forEach(x => { if (!seen.has(x)) next.push(x) }))
    frontier = next
    depth++
    if (depth > 200) break // guard anti-ciclo
  }
  return levels
}

// ---------- LINAJE DE NODOS ----------
// Para un nodo dado: cadena aguas arriba (de donde vienen los datos)
// y aguas abajo (a donde van). Si no se pasa nodeId, devuelve el
// resumen global source->sink de todo el grafo.
export function nodeLineage(data, nodeId) {
  const idx = buildIndex(data)
  if (!nodeId) {
    // Resumen global: por cada SINK, los SOURCE que lo alcanzan.
    const sinks = idx.nodes.filter(n => (n.type || '').toUpperCase() === 'SINK')
    const sources = idx.nodes.filter(n => (n.type || '').toUpperCase() === 'SOURCE')
    return {
      kind: 'global',
      sources: sources.map(n => n.id),
      sinks: sinks.map(n => n.id),
      chains: sinks.map(sink => ({
        sink: sink.id,
        upstream: traverse(sink.id, idx.parents),
      })),
    }
  }
  return {
    kind: 'node',
    node: idx.byId[nodeId],
    upstream: traverse(nodeId, idx.parents),
    downstream: traverse(nodeId, idx.children),
  }
}

// ---------- LINAJE DE COLUMNAS ----------
// Columnas "declaradas" de un nodo a partir de su regla.
function columnsFromRule(rule) {
  if (!rule) return null
  // SELECT col1, col2 as alias, ...
  // Nota: el parser BNX pone select:"*" por defecto; eso NO es una columna
  // declarada, es passthrough -> devolver null para que se herede de padres.
  const sel = (rule.select || '').trim()
  if (sel && sel !== '*') {
    const cols = sel.split(',').map(s => s.trim()).filter(Boolean)
    return cols.map(c => {
      const m = c.match(/^(.*?)\s+as\s+(\w+)$/i)
      if (m) return { out: m[2], srcExpr: m[1].trim(), kind: 'select' }
      return { out: c, srcExpr: c, kind: 'select' }
    })
  }
  // dml_fields: [{field, expr, type}] (out.field :: expr)
  if (Array.isArray(rule.dml_fields) && rule.dml_fields.length) {
    return rule.dml_fields.map(f => ({
      out: f.field,
      srcExpr: f.expr || '',
      kind: f.type || 'derived',
    }))
  }
  return null
}

// Extrae nombres de columna de entrada referidos en una expresion
// (col("X"), in.X, o un identificador simple).
function refsInExpr(expr) {
  if (!expr) return []
  const refs = new Set()
  let m
  const reCol = /col\(\s*["'](\w+)["']\s*\)/g
  while ((m = reCol.exec(expr))) refs.add(m[1])
  const reIn = /\bin\d*\.(\w+)/g
  while ((m = reIn.exec(expr))) refs.add(m[1])
  if (refs.size === 0) {
    const simple = expr.trim().match(/^(\w+)$/)
    if (simple) refs.add(simple[1])
  }
  return [...refs]
}

// Linaje de columnas para un nodo: devuelve filas
// { out, from: [{node, col}], kind } trazando una vez hacia atras
// hasta los padres (y por nombre hasta sus columnas conocidas).
export function columnLineage(data, nodeId) {
  const idx = buildIndex(data)
  const node = idx.byId[nodeId]
  if (!node) return { kind: 'none', rows: [] }

  const dmlSchema = data?.dml_schema || {}

  // Columnas conocidas de un nodo (recursivo best-effort, 1 nivel para
  // SOURCE via dml_schema; para transforms se usa su propia regla).
  const knownCols = (nid) => {
    const n = idx.byId[nid]
    if (!n) return []
    if ((n.type || '').toUpperCase() === 'SOURCE') {
      const sc = dmlSchema[n.id] || dmlSchema[n.name] || {}
      return Object.keys(sc)
    }
    const rc = columnsFromRule(n.rule)
    if (rc) return rc.map(c => c.out)
    // sin regla: hereda columnas de sus padres (passthrough)
    const ps = idx.parents[nid] || []
    const inh = new Set()
    ps.forEach(p => knownCols(p).forEach(c => inh.add(c)))
    return [...inh]
  }

  const parents = idx.parents[nodeId] || []
  const declared = columnsFromRule(node.rule)

  // Caso SOURCE: sus columnas son el origen (del dml_schema).
  if ((node.type || '').toUpperCase() === 'SOURCE') {
    const sc = dmlSchema[node.id] || dmlSchema[node.name] || {}
    return {
      kind: 'source',
      rows: Object.entries(sc).map(([col, typ]) => ({
        out: col, from: [{ node: node.id, col }], kind: 'origin', dtype: typ,
      })),
    }
  }

  // Mapa col -> nodo padre que la provee (para resolver procedencia).
  const provider = {}
  parents.forEach(p => knownCols(p).forEach(c => {
    if (!(c in provider)) provider[c] = p
  }))

  const resolveFrom = (colNames) => {
    const out = []
    colNames.forEach(c => {
      const p = provider[c]
      if (p) out.push({ node: p, col: c })
      else if (parents.length === 1) out.push({ node: parents[0], col: c })
    })
    return out
  }

  // Nodo con regla declarada (select / dml_fields).
  if (declared) {
    return {
      kind: node.type ? node.type.toLowerCase() : 'transform',
      rows: declared.map(d => ({
        out: d.out,
        from: resolveFrom(refsInExpr(d.srcExpr)),
        kind: d.kind,
        expr: d.srcExpr && d.srcExpr !== d.out ? d.srcExpr : undefined,
      })),
    }
  }

  // Sin regla (p.ej. Sort/Join passthrough): todas las columnas de los
  // padres pasan de largo. Para JOIN marcamos la llave.
  const joinKey = (node.rule && node.rule.join_key) || null
  const allCols = new Set()
  parents.forEach(p => knownCols(p).forEach(c => allCols.add(c)))
  return {
    kind: (node.type || 'passthrough').toLowerCase(),
    joinKey,
    rows: [...allCols].map(c => ({
      out: c,
      from: resolveFrom([c]),
      kind: joinKey && c === joinKey ? 'join-key' : 'passthrough',
    })),
  }
}

// ============================================================
// EXPORTERS DE METADATA (frontend). Reutilizan columnLineage para
// construir un modelo canonico y derivar OpenLineage / Glue / Databricks.
// Equivalente a src/metadata.py (mantener en sync si cambia uno).
// ============================================================

// ---------- modelo canonico ----------
export function buildCanonical(data) {
  const idx = buildIndex(data)
  const nodes = (data?.nodes || []).map(n => {
    const lin = columnLineage(data, n.id)
    return {
      id: n.id,
      name: n.name || n.id,
      type: (n.type || '').toUpperCase(),
      parents: idx.parents[n.id] || [],
      children: idx.children[n.id] || [],
      rule: n.rule || {},
      columns: lin.rows,
    }
  })
  return {
    bnx_metadata_version: '1.0',
    generated_at: new Date().toISOString(),
    graph: {
      name: data?.graph_name || 'grafo',
      description: data?.description || '',
      params: data?.params || {},
      node_count: nodes.length,
      edge_count: (data?.edges || []).length,
    },
    nodes,
    edges: (data?.edges || []).map(e => ({ from: e.from, to: e.to })),
  }
}

// ---------- tipos ----------
const GLUE_TYPES = {
  string: 'string', int: 'int', integer: 'int', long: 'bigint',
  double: 'double', float: 'float', decimal: 'decimal(38,10)',
  date: 'date', timestamp: 'timestamp', boolean: 'boolean',
}
const glueType = (t) => GLUE_TYPES[(t || 'string').toLowerCase()] || 'string'

// Tablas source/sink con tipos propagados transitivamente hasta el SOURCE.
function sourceSinkTables(canonical) {
  const byId = {}; canonical.nodes.forEach(n => { byId[n.id] = n })
  const dtypeAt = {}
  canonical.nodes.forEach(n => {
    if (n.type === 'SOURCE') n.columns.forEach(r => { dtypeAt[`${n.id}|${r.out}`] = r.dtype || 'string' })
  })
  const resolveDtype = (nodeId, col, seen = new Set()) => {
    const key = `${nodeId}|${col}`
    if (key in dtypeAt) return dtypeAt[key]
    if (seen.has(key)) return 'string'
    seen.add(key)
    const n = byId[nodeId]
    if (!n) return 'string'
    for (const r of n.columns) {
      if (r.out === col) {
        for (const f of (r.from || [])) {
          const dt = resolveDtype(f.node, f.col, seen)
          if (dt && dt !== 'string') { dtypeAt[key] = dt; return dt }
        }
      }
    }
    return 'string'
  }
  const sources = {}, sinks = {}
  canonical.nodes.forEach(n => {
    if (n.type === 'SOURCE') sources[n.id] = n.columns.map(r => [r.out, r.dtype || 'string'])
    if (n.type === 'SINK') sinks[n.id] = n.columns.map(r => [r.out, resolveDtype(n.id, r.out)])
  })
  return { sources, sinks }
}

// ---------- OpenLineage ----------
export function buildOpenLineage(canonical) {
  const ns = 'bnx'
  const jobName = canonical.graph.name
  const now = canonical.generated_at
  const byId = {}; canonical.nodes.forEach(n => { byId[n.id] = n })
  const events = canonical.nodes.map(n => {
    const inputs = [], outputs = []
    n.parents.forEach(p => {
      const pn = byId[p]
      if (pn && (pn.type === 'SOURCE' || pn.type === 'SINK')) inputs.push({ namespace: ns, name: p })
    })
    if (n.type === 'SOURCE' || n.type === 'SINK') {
      const fields = [], colLineage = {}
      n.columns.forEach(r => {
        fields.push({ name: r.out, type: r.dtype || 'string' })
        if (r.from && r.from.length) {
          colLineage[r.out] = { inputFields: r.from.map(f => ({ namespace: ns, name: f.node, field: f.col })) }
        }
      })
      const ds = {
        namespace: ns, name: n.id,
        facets: {
          schema: { _producer: 'bnx-convertidor', _schemaURL: 'https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json', fields },
          documentation: { _producer: 'bnx-convertidor', _schemaURL: 'https://openlineage.io/spec/facets/1-0-0/DocumentationDatasetFacet.json', description: canonical.graph.description },
        },
      }
      if (Object.keys(colLineage).length) {
        ds.facets.columnLineage = { _producer: 'bnx-convertidor', _schemaURL: 'https://openlineage.io/spec/facets/1-0-0/ColumnLineageDatasetFacet.json', fields: colLineage }
      }
      outputs.push(ds)
    }
    return {
      eventType: 'COMPLETE', eventTime: now, producer: 'bnx-convertidor',
      job: { namespace: ns, name: `${jobName}.${n.id}` },
      run: { runId: `${jobName}-${n.id}` },
      inputs, outputs,
    }
  })
  return { openlineage_version: '1.0.0', namespace: ns, events }
}

// ---------- Glue (boto3) ----------
export function buildGlueScript(canonical, database = 'bnx_catalog') {
  const { sources, sinks } = sourceSinkTables(canonical)
  const tables = { ...sources, ...sinks }
  const desc = (canonical.graph.description || '').replace(/"/g, "'")
  const lineageObj = {}; canonical.nodes.forEach(n => { lineageObj[n.id] = n.columns })
  const L = []
  L.push('"""')
  L.push('BNX -> AWS Glue Data Catalog')
  L.push(`Grafo: ${canonical.graph.name}`)
  L.push(`Generado: ${canonical.generated_at}`)
  L.push('Crea las tablas source/sink con columnas, descripcion y linaje (en Parameters).')
  L.push('"""')
  L.push('import boto3, json')
  L.push('')
  L.push("glue = boto3.client('glue')")
  L.push(`DATABASE = ${JSON.stringify(database)}`)
  L.push('')
  L.push('try:')
  L.push(`    glue.create_database(DatabaseInput={'Name': DATABASE, 'Description': ${JSON.stringify(desc)}})`)
  L.push('except glue.exceptions.AlreadyExistsException:')
  L.push('    pass')
  L.push('')
  L.push(`GRAPH_LINEAGE = json.loads(${JSON.stringify(JSON.stringify(lineageObj))})`)
  L.push('')
  Object.entries(tables).forEach(([tname, cols]) => {
    const kind = tname in sources ? 'SOURCE' : 'SINK'
    const colPy = cols.map(([c, t]) => `{'Name': ${JSON.stringify(c)}, 'Type': ${JSON.stringify(glueType(t))}}`).join(', ')
    L.push(`# [${kind}] ${tname}`)
    L.push('glue.create_table(')
    L.push('    DatabaseName=DATABASE,')
    L.push('    TableInput={')
    L.push(`        'Name': ${JSON.stringify(tname.toLowerCase())},`)
    L.push(`        'Description': ${JSON.stringify(desc)},`)
    L.push('        \'Parameters\': {')
    L.push(`            'bnx_graph': ${JSON.stringify(canonical.graph.name)},`)
    L.push(`            'bnx_node_type': ${JSON.stringify(kind)},`)
    L.push(`            'bnx_column_lineage': json.dumps(GRAPH_LINEAGE.get(${JSON.stringify(tname)}, [])),`)
    L.push("            'classification': 'parquet',")
    L.push('        },')
    L.push('        \'StorageDescriptor\': {')
    L.push(`            'Columns': [${colPy}],`)
    L.push(`            'Location': 's3://CHANGE_ME/' + ${JSON.stringify(tname.toLowerCase())},`)
    L.push("            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',")
    L.push("            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',")
    L.push("            'SerdeInfo': {'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'},")
    L.push('        },')
    L.push('    },')
    L.push(')')
    L.push(`print('[ok] tabla creada: ' + DATABASE + '.' + ${JSON.stringify(tname.toLowerCase())})`)
    L.push('')
  })
  L.push("print('[ok] BNX -> Glue Catalog completado')")
  return L.join('\n')
}

// ---------- Databricks Unity Catalog (DDL) ----------
export function buildDatabricksDDL(canonical, catalog = 'bnx_catalog', schema = 'default') {
  const { sources, sinks } = sourceSinkTables(canonical)
  const tables = { ...sources, ...sinks }
  const gname = canonical.graph.name
  const q = (s) => String(s).replace(/'/g, "''")
  const gdesc = q(canonical.graph.description || '')
  const byId = {}; canonical.nodes.forEach(n => { byId[n.id] = n })
  const L = []
  L.push(`-- BNX -> Databricks Unity Catalog`)
  L.push(`-- Grafo: ${gname}`)
  L.push(`-- Generado: ${canonical.generated_at}`)
  L.push('')
  L.push(`CREATE CATALOG IF NOT EXISTS ${catalog};`)
  L.push(`CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema} COMMENT '${gdesc}';`)
  L.push('')
  Object.entries(tables).forEach(([tname, cols]) => {
    const kind = tname in sources ? 'SOURCE' : 'SINK'
    const node = byId[tname]
    const lineageByCol = {}
    if (node) node.columns.forEach(r => {
      if (r.from && r.from.length) lineageByCol[r.out] = r.from.map(f => `${f.node}.${f.col}`).join(', ')
    })
    L.push(`-- [${kind}] ${tname}`)
    L.push(`CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.${tname.toLowerCase()} (`)
    const colLines = cols.map(([c, t]) => {
      const dt = glueType(t)
      const cm = lineageByCol[c]
      return cm ? `    ${c} ${dt} COMMENT 'lineage: ${q(cm)}'` : `    ${c} ${dt}`
    })
    L.push(colLines.join(',\n'))
    L.push(')')
    L.push('USING DELTA')
    L.push(`COMMENT '${gdesc}'`)
    L.push('TBLPROPERTIES (')
    L.push(`    'bnx_graph' = '${q(gname)}',`)
    L.push(`    'bnx_node_type' = '${kind}'`)
    L.push(');')
    L.push('')
  })
  return L.join('\n')
}

// Conjunto completo (igual shape que src.metadata.build_all).
export function buildAllMetadata(data) {
  const canonical = buildCanonical(data)
  return {
    canonical,
    openlineage: buildOpenLineage(canonical),
    glue_script: buildGlueScript(canonical),
    databricks_ddl: buildDatabricksDDL(canonical),
  }
}
