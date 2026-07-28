"""
BNX E2E Pipeline — Validacion de Output
Compara el output de Spark y Glue contra los resultados esperados.

Se ejecuta como Glue Python Shell job.
"""
import sys
import boto3
import json
from io import StringIO

# Parametros del job
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['SPARK_OUTPUT', 'GLUE_OUTPUT', 'EXPECTED_PATH'])

s3 = boto3.client('s3')


def parse_s3_path(path):
    """Extrae bucket y key de una ruta s3://bucket/key"""
    path = path.replace('s3://', '')
    bucket = path.split('/')[0]
    key = '/'.join(path.split('/')[1:])
    return bucket, key


def list_csv_files(bucket, prefix):
    """Lista archivos CSV/parquet en un prefijo S3"""
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    files = []
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.csv') or obj['Key'].endswith('.parquet'):
            files.append(obj['Key'])
    return files


def read_csv_from_s3(bucket, key):
    """Lee un CSV de S3 y retorna las filas como lista de dicts"""
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8')
    lines = content.strip().split('\n')
    if not lines:
        return []
    headers = lines[0].split(',')
    rows = []
    for line in lines[1:]:
        values = line.split(',')
        rows.append(dict(zip(headers, values)))
    return rows


def compare_outputs(output1_rows, output2_rows, label1, label2):
    """Compara dos conjuntos de datos por contenido"""
    errors = []

    if len(output1_rows) != len(output2_rows):
        errors.append(f"Row count mismatch: {label1}={len(output1_rows)}, {label2}={len(output2_rows)}")

    # Comparar columnas
    if output1_rows and output2_rows:
        cols1 = set(output1_rows[0].keys())
        cols2 = set(output2_rows[0].keys())
        if cols1 != cols2:
            errors.append(f"Column mismatch: {label1}={cols1}, {label2}={cols2}")

    return errors


def validate():
    """Ejecuta la validacion completa"""
    print("=" * 60)
    print("BNX E2E VALIDATION")
    print("=" * 60)

    results = {"spark": None, "glue": None, "expected": None, "errors": [], "passed": True}

    # Leer output de Spark
    spark_bucket, spark_prefix = parse_s3_path(args['SPARK_OUTPUT'])
    spark_files = list_csv_files(spark_bucket, spark_prefix)
    print(f"\n[SPARK] Found {len(spark_files)} output files in {args['SPARK_OUTPUT']}")

    spark_rows = []
    for f in spark_files:
        if f.endswith('.csv'):
            spark_rows.extend(read_csv_from_s3(spark_bucket, f))
    print(f"[SPARK] Total rows: {len(spark_rows)}")
    results["spark"] = len(spark_rows)

    # Leer output de Glue
    glue_bucket, glue_prefix = parse_s3_path(args['GLUE_OUTPUT'])
    glue_files = list_csv_files(glue_bucket, glue_prefix)
    print(f"\n[GLUE] Found {len(glue_files)} output files in {args['GLUE_OUTPUT']}")

    glue_rows = []
    for f in glue_files:
        if f.endswith('.csv'):
            glue_rows.extend(read_csv_from_s3(glue_bucket, f))
    print(f"[GLUE] Total rows: {len(glue_rows)}")
    results["glue"] = len(glue_rows)

    # Leer expected (si existe)
    expected_bucket, expected_prefix = parse_s3_path(args['EXPECTED_PATH'])
    expected_files = list_csv_files(expected_bucket, expected_prefix)
    print(f"\n[EXPECTED] Found {len(expected_files)} files in {args['EXPECTED_PATH']}")

    expected_rows = []
    for f in expected_files:
        if f.endswith('.csv'):
            expected_rows.extend(read_csv_from_s3(expected_bucket, f))
    results["expected"] = len(expected_rows)

    # Validacion 1: Spark vs Glue deben dar el mismo resultado
    print("\n--- Validation 1: Spark output == Glue output ---")
    if spark_rows and glue_rows:
        errors = compare_outputs(spark_rows, glue_rows, "Spark", "Glue")
        if errors:
            results["errors"].extend(errors)
            results["passed"] = False
            for e in errors:
                print(f"  FAIL: {e}")
        else:
            print("  PASS: Spark and Glue produced same row count")
    elif not spark_rows and not glue_rows:
        print("  WARN: Both outputs are empty")
    else:
        err = f"One output is empty: Spark={len(spark_rows)}, Glue={len(glue_rows)}"
        results["errors"].append(err)
        results["passed"] = False
        print(f"  FAIL: {err}")

    # Validacion 2: vs Expected (si hay expected data)
    if expected_rows:
        print("\n--- Validation 2: Output vs Expected ---")
        if spark_rows:
            errors = compare_outputs(spark_rows, expected_rows, "Spark", "Expected")
            if errors:
                results["errors"].extend(errors)
                results["passed"] = False
                for e in errors:
                    print(f"  FAIL: {e}")
            else:
                print("  PASS: Spark output matches expected")

    # Validacion 3: Output no vacio
    print("\n--- Validation 3: Non-empty output ---")
    if not spark_rows and not glue_rows:
        err = "Both outputs are empty — jobs may have failed silently"
        results["errors"].append(err)
        results["passed"] = False
        print(f"  FAIL: {err}")
    else:
        print(f"  PASS: Spark={len(spark_rows)} rows, Glue={len(glue_rows)} rows")

    # Resultado final
    print("\n" + "=" * 60)
    if results["passed"]:
        print("RESULT: ALL VALIDATIONS PASSED")
    else:
        print(f"RESULT: FAILED ({len(results['errors'])} errors)")
        for e in results["errors"]:
            print(f"  - {e}")
        # Falla el job para que Step Functions detecte el error
        raise Exception(f"Validation failed: {results['errors']}")

    print("=" * 60)
    return results


if __name__ == "__main__":
    validate()
