# Ejercicio: 3 planes Ab Initio de banca

Proyecto pequeño para practicar el Orquestador. Todos los datos son inventados (sin PII real).

## Qué hace cada plan

| Plan | Pasos (en orden) | Qué hace |
|---|---|---|
| `Plan_ingesta_clientes.plan` | `Prepara_directorios` (.ksh) → `Run_ingesta_clientes` → `Run_segmenta_clientes` | Limpia clientes (trim, mayúsculas, solo activos, sin duplicados) y les asigna nivel PREMIUM/ESTANDAR según su límite. |
| `Plan_transacciones_diarias.plan` | `Run_filtra_transacciones` → `Run_resumen_transacciones` → `Log_estado_ok` | Deja solo transacciones válidas, suma monto y cantidad por cliente y cruza con los clientes segmentados. El último paso es un `print` sin traducción automática (se ve como "sin acción"). |
| `Plan_reporte_riesgo.plan` | `Run_score_riesgo` → `Notifica_reporte` (.ksh) | Calcula un score de riesgo (monto / límite) y deja solo los clientes con score >= 60. |

Flujo de datos entre planes (`/banca/<nombre>.dat`):

```
clientes_raw -> [plan 1] -> clientes_segmentados --\
transacciones_raw -> [plan 2: filtra] -> transacciones_validas -> [plan 2: resumen] -> resumen_cliente_diario -> [plan 3] -> reporte_riesgo
```

## Cómo se relacionan plan -> pset -> mp

```
Plan_x.plan --(tarea Graph_Task: ab_task_graph $AI_PSET/y.pset)--> y.pset --(!prototype $AI_MP/y.mp)--> y.mp
                                                                                            \--> $AI_XFR/*.xfr, $AI_DML/*.dml
Plan_x.plan --(tarea Program_Task: ab_task_script $AI_KSH/z.ksh)--> z.ksh
```

| Pset | Grafo (.mp) | Componentes | xfr / dml |
|---|---|---|---|
| `ingesta_clientes.pset` | `ingesta_clientes.mp` | Input → Reformat → Filter → Dedup → Output | `limpia_clientes.xfr`, `clientes_raw.dml`, `clientes_limpios.dml` |
| `segmenta_clientes.pset` | `segmenta_clientes.mp` | Input → Reformat → Output | `asigna_nivel.xfr`, `clientes_segmentados.dml` |
| `filtra_transacciones.pset` | `filtra_transacciones.mp` | Input → Filter → Reformat → Output | `normaliza_tx.xfr`, `transacciones.dml` |
| `resumen_transacciones.pset` | `resumen_transacciones.mp` | 2 Input → Rollup + Join → Output | `suma_por_cliente.xfr`, `cruza_clientes.xfr`, `resumen_cliente.dml` |
| `score_riesgo.pset` | `score_riesgo.mp` | Input → Reformat → Filter → Output | `calcula_score.xfr`, `reporte_riesgo.dml` |

Notas:
- La lógica real de cada Reformat/Rollup/Join va embebida en el `.mp`; los `.xfr` y `.dml` son la referencia (`$AI_XFR`, `$AI_DML`) para que el mapa los vea.
- El Join sale como `left` (el grafo no declara el tipo de join).
- Los planes no tienen pset propio, por eso hay 3 orquestaciones (una por plan). Si agregas un pset con `!prototype|P|||$AI_PLAN/Plan_x.plan`, aparece una variante más por cada pset.

## Cómo generarlo (ya está hecho en `output/ejercicio_3_planes/`)

```bash
.venv/bin/python scripts/convertir_lote.py abinitio/ejercicio_3_planes --out output/ejercicio_3_planes
.venv/bin/python -m src.pset_map abinitio/ejercicio_3_planes
.venv/bin/python -m src.orquestador generar abinitio/ejercicio_3_planes output/ejercicio_3_planes
.venv/bin/python -m src.orquestador componer output/ejercicio_3_planes/orquestacion_Plan_ingesta_clientes.json \
    output/ejercicio_3_planes/orquestacion_Plan_transacciones_diarias.json \
    output/ejercicio_3_planes/orquestacion_Plan_reporte_riesgo.json --nombre ejercicio_3_planes
```

## Ejercicios en la GUI (portal, página Orquestador, puerto 8081)

1. Ver el mapa: abre `abinitio/ejercicio_3_planes/pset_map.json`. Debe mostrar 0 faltantes y cada plan con sus tareas, psets y scripts.
2. Ver una orquestación: abre `orquestacion_Plan_ingesta_clientes.json` y revisa el diagrama de pasos y el enlace sugerido entre ingesta y segmentación.
3. Reordenar pasos: en `Plan_transacciones_diarias` agrega una dependencia para que `Log_estado_ok` corra después de `Run_filtra_transacciones`, o deshabilita `Log_estado_ok`. Prueba "invertir" y vuelve a invertir.
4. Agregar un enlace: en `PLANES_ejercicio_3_planes` ya hay dos (p1 → p2 y p2 → p3). Quita uno, corre el dry-run y verás que ese plan ya no recibe su entrada. Vuelve a agregarlo con `output/banca/<dataset>.dat` → `raw/banca/<dataset>.dat`.
5. Dry-run: ejecuta cada plan y el plan de planes sin marcar "ejecutar". Revisa el orden y los pasos sin acción.
6. Datos sintéticos: botón "datos" (o `orquestador datos <json> --filas 15`). Genera parquet en `output/ejercicio_3_planes/datos/raw/banca/`. Son valores al azar, así que los filtros (`estatus == "A"`, `"OK"`) dejan pocas o ninguna fila. Para ver resultados reales, reemplaza `clientes_raw.dat` y `transacciones_raw.dat` por parquet con esos valores.
7. Ejecución real: con `base_path` definido (ya apunta a `output/ejercicio_3_planes/datos`) y modo `python`, ejecuta el plan 1 y luego el plan de planes.
8. Plan de planes: arma uno nuevo con solo 2 de los 3 planes, o sin cadena, y acomódalo.
9. Airflow: genera el DAG de cada plan y del plan de planes (`dag_*.py` en `output/ejercicio_3_planes/`). El de planes dispara los DAG de cada plan.

## Orquestación desde cero (sin .plan), local / remoto / nube
Una orquestación no necesita un `.plan`: puedes crearla vacía y armar los pasos tú. Sirve, por ejemplo, para un `.mp` sin plan (como `raton77`), o para mezclar jobs convertidos con llamadas a otros sistemas. Queda marcada `"origen": "manual"`, tiene el mismo esquema que las generadas desde planes, y funciona igual con `mostrar`, `ejecutar` (dry-run por defecto), `dep-add`, `componer` y `airflow`.

Ejemplo ya armado: `orquestacion_ejercicio_desde_cero.json` (copia versionada; la generada está en `output/ejercicio_3_planes/`). Cadena de 6 pasos: esperar un archivo (local) → grafo `ingesta_clientes_spark.py` (local) → subir a S3 (nube) → job de Glue (nube) → aviso por HTTP (remoto) → comando por SSH (remoto). Los nombres de bucket, host y URL son de ejemplo.

```bash
J=output/ejercicio_3_planes/orquestacion_ejercicio_desde_cero.json
.venv/bin/python -m src.orquestador nueva ejercicio_desde_cero --proyecto ejercicio_3_planes
.venv/bin/python -m src.orquestador paso-add $J --tipo esperar_archivo --nombre Espera_archivo_clientes \
    --campo ruta=/tmp/bnx/entrada/clientes_listo.ok --campo timeout_s=600
.venv/bin/python -m src.orquestador paso-add $J --tipo graph --nombre Ingesta_clientes --despues-de t1 \
    --campo target=output/ejercicio_3_planes/ingesta_clientes_spark.py
.venv/bin/python -m src.orquestador paso-add $J --tipo s3_copy --nombre Sube_resultado_a_S3 --despues-de t2 \
    --campo origen=output/ejercicio_3_planes/datos/output/ --campo destino=s3://mi-bucket-bnx/ejercicio_3_planes/output/ \
    --campo recursivo=true --campo profile=bnx-dev --campo region=us-east-1
# ... glue_job, http y ssh igual (ver el JSON)
.venv/bin/python -m src.orquestador ejecutar $J          # dry-run: muestra los comandos exactos
.venv/bin/python -m src.orquestador paso-rm  $J Glue_enriquecer
```
En la GUI (Orquestador): botón "Nueva orquestación" (nombre + proyecto), luego "Agregar paso" en el panel derecho (formulario por tipo; para un paso grafo eliges un `*_spark.py` ya convertido del proyecto), dependencias, y "Guardar". Los nodos se colorean por ubicación: Local (azul), Remoto (verde azulado), Nube (naranja).

### Tipos de paso
| Tipo | Ubicación | Campos (obligatorios en negrita) | Comando que se construye |
|---|---|---|---|
| `graph` | Local | **target** (`*_spark.py`) | `python job.py` o `spark-submit` según `ejecucion.modo` |
| `python` | Local | **target**, args | `python script.py args...` |
| `shell` | Local | **comando** | argv del comando (`.ksh` → `ksh`, `.sh` → `bash`), sin shell |
| `spark_submit` | Local | **target**, master, spark_args, args | `spark-submit --master M ... job.py args` |
| `esperar_archivo` | Local (Nube si es `s3://`) | **ruta** (admite `*`), timeout_s, intervalo_s | sensor: `python -m src.orquestador esperar RUTA` |
| `ssh` | Remoto | **host**, **comando**, usuario, puerto, identidad (ruta de la clave) | `ssh -o BatchMode=yes ... usuario@host 'comando'` |
| `http` | Remoto | **url**, metodo, body (JSON), headers, token_env, timeout_s | `curl -sS --fail -X M ... URL` |
| `glue_job` | Nube | **job_name**, args (`{"--k": "v"}`), profile, region | `aws glue start-job-run --job-name J --arguments '{...}'` |
| `emr_step` | Nube | **cluster_id** (`j-XXXX`), **script** (`s3://`), args, nombre, action_on_failure | `aws emr add-steps --cluster-id C --steps '[...]'` |
| `lambda` | Nube | **function_name**, payload (JSON) | `aws lambda invoke --function-name F --payload '{...}' /dev/null` |
| `s3_copy` | Nube | **origen**, **destino** (uno debe ser `s3://`), recursivo | `aws s3 cp [--recursive] ORIGEN DESTINO` |

Reglas de seguridad:
- Nada de credenciales en el JSON. `ssh` usa tu clave o `ssh-agent` (`BatchMode=yes`: nunca pide contraseña); `identidad` es solo la ruta. `aws` usa su cadena normal de credenciales; `profile` y `region` son opcionales por paso o globales en `ejecucion.aws`.
- `http` no acepta headers con secretos (Authorization, X-Api-Key...). Para un token, `token_env` es el NOMBRE de una variable de entorno; se lee al ejecutar y se envía a `curl` por stdin, así no aparece en el JSON, en el dry-run ni en `ps`.
- Todo se ejecuta como lista de argumentos, sin `shell=True`: un `;` o `$(...)` en un campo es texto, no se interpreta.
- El dry-run (por defecto, y lo único disponible en la GUI) solo imprime el comando exacto. La ejecución real es `ejecutar --ejecutar`.
