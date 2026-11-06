// abinitioKeys.js — Lee un bloque de PARAMETROS de Ab Initio (los que se ven en el
// GDE: Name | Value, p.ej. GEN_REDACTION_DB_USER, GEN_REDACTION_DB_TERADATA_NAME,
// ..._ENCRYPTED_PASSWD, ..._TNS, ..._INIT_FILE) y los traduce a los campos de
// conexion de "Datos Remotos". TODO ES OPCIONAL: sin llaves, el panel funciona igual.
//
// Reglas de seguridad:
//  * ..._ENCRYPTED_PASSWD / ..._ENCRYPTED_PASSWORD son blobs cifrados con la llave de
//    Ab Initio: BNX NO puede descifrarlos y NO los usa como password. Solo se avisa.
//  * Un password en claro (..._PASSWD / ..._PASSWORD) se usa solo en memoria; nunca
//    se persiste (ver sanitizeKeysText).

// Parsea texto pegado del GDE / .pset / shell a { NOMBRE: valor }.
// Acepta: "NOMBRE<TAB>valor" (copiado de la grilla), "NOMBRE = valor",
// "export NOMBRE=valor", y "NOMBRE  valor" (2+ espacios o un espacio).
export function parseAbinitioParams(text) {
  const params = {}
  for (const raw of String(text || '').split(/\r?\n/)) {
    const line = raw.trim()
    if (!line || line.startsWith('#') || line.startsWith('//')) continue
    let name = null
    let value = null
    let m
    if (line.includes('\t')) {
      const i = line.indexOf('\t')
      name = line.slice(0, i).trim()
      value = line.slice(i + 1).trim()
    } else if ((m = line.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_.]*)\s*=\s*(.*)$/))) {
      name = m[1]; value = m[2]
    } else if ((m = line.match(/^([A-Za-z_][A-Za-z0-9_.]*)\s{2,}(\S.*)$/))) {
      name = m[1]; value = m[2]
    } else if ((m = line.match(/^([A-Z][A-Z0-9_]*)\s+(\S.*)$/))) {
      name = m[1]; value = m[2]
    }
    if (!name || !/^[A-Za-z_][A-Za-z0-9_.]*$/.test(name)) continue
    value = String(value ?? '').trim().replace(/^(["'])(.*)\1$/, '$2')
    params[name] = value
  }
  return params
}

const isEncryptedPwd = (k) => /ENCRYPTED_?(PASSWD|PASSWORD)$/i.test(k)
const isPlainPwd = (k) => /(PASSWD|PASSWORD)$/i.test(k) && !isEncryptedPwd(k)
const isTeradataKey = (k) => /TERADATA/i.test(k)

// Primer parametro cuyo nombre cumple el patron, dentro del grupo correcto
// (Teradata vs. el resto de bases: Oracle/Hive/etc.).
function pick(params, wantTeradata, re) {
  for (const k of Object.keys(params)) {
    if (isTeradataKey(k) !== wantTeradata) continue
    if (re.test(k) && String(params[k]).trim() !== '') return [k, params[k]]
  }
  return null
}

// Traduce las llaves a campos de conexion segun la fuente elegida.
// Devuelve { fields:{user,host,database,password}, used:{campo: NOMBRE}, encrypted:[...],
//            extras:{NOMBRE: valor}, found: n }
export function mapAbinitioToConnection(params, sourceType) {
  const td = sourceType === 'teradata'
  const fields = {}
  const used = {}
  const take = (field, hit, transform) => {
    if (!hit) return
    const [k, v] = hit
    fields[field] = transform ? transform(v) : v
    used[field] = k
  }

  take('user', pick(params, td, /(^|_)USER$/i))
  if (td) {
    // En Teradata el "NAME" es el TDPID/alias del servidor (p.ej. edwdev).
    take('host', pick(params, true, /(^|_)NAME$/i) || pick(params, true, /(^|_)NODES$/i))
  } else {
    // Otras bases: NODES = host; NAME = servicio/alias (se quita el '@' de Oracle).
    take('host', pick(params, false, /(^|_)NODES$/i))
    take('database', pick(params, false, /(^|_)NAME$/i), (v) => String(v).replace(/^@/, ''))
  }
  // Password en claro (raro): solo memoria. Los cifrados NO se usan.
  const plain = Object.keys(params).find((k) => isTeradataKey(k) === td && isPlainPwd(k) && params[k])
  if (plain) { fields.password = params[plain]; used.password = plain }

  const encrypted = Object.keys(params).filter((k) => isEncryptedPwd(k) && params[k])
  // Otras llaves informativas (rutas/versiones): no se mapean a un campo, pero se
  // muestran y se guardan con la conexion (no son secretos).
  const extras = {}
  for (const k of Object.keys(params)) {
    if (Object.values(used).includes(k) || isEncryptedPwd(k) || isPlainPwd(k)) continue
    if (isTeradataKey(k) !== td) continue
    if (/(HOME|TNS|VERSION|INIT_FILE|ODBC|WALLET|KEYTAB|PRINCIPAL|REALM)/i.test(k)) extras[k] = params[k]
  }
  return { fields, used, encrypted, extras, found: Object.keys(params).length }
}

// Quita del texto las lineas con passwords/secretos (cifrados o no) para poder
// guardar las demas llaves junto a la conexion sin persistir credenciales.
export function sanitizeKeysText(text) {
  return String(text || '').split(/\r?\n/).filter((raw) => {
    const m = raw.trim().match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_.]*)/)
    return !(m && /(PASSWD|PASSWORD|SECRET|TOKEN)/i.test(m[1]))
  }).join('\n')
}
