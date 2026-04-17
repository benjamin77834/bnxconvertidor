# src/refactor_engine.py
"""
Refactoring engine for legacy code migration:
- Spark 2.x → Spark 3.x
- Python 2.7 → Python 3.11+
- Glue 2.0 → Glue 4.0

Applies regex-based transformations for known API changes,
deprecated patterns, and syntax upgrades.
"""
import re


# ═══════════════════════════════════════════════════════════════
# SPARK 2 → SPARK 3 RULES
# ═══════════════════════════════════════════════════════════════

SPARK_RULES = [
    # SparkContext → SparkSession
    {
        "name": "SparkContext to SparkSession",
        "pattern": r'sc\s*=\s*SparkContext\(\)',
        "replacement": 'spark = SparkSession.builder.appName("BNX_Refactored").getOrCreate()\nsc = spark.sparkContext',
        "desc": "Spark 3 usa SparkSession como entry point principal",
    },
    {
        "name": "SQLContext deprecated",
        "pattern": r'sqlContext\s*=\s*SQLContext\(sc\)',
        "replacement": '# SQLContext deprecated in Spark 3 — use SparkSession directly\n# sqlContext = SQLContext(sc)',
        "desc": "SQLContext fue deprecado en Spark 2.0, removido en 3.x",
    },
    {
        "name": "HiveContext deprecated",
        "pattern": r'hiveContext\s*=\s*HiveContext\(sc\)',
        "replacement": 'spark = SparkSession.builder.enableHiveSupport().getOrCreate()',
        "desc": "HiveContext reemplazado por SparkSession.enableHiveSupport()",
    },
    # DataFrame API changes
    {
        "name": "registerTempTable → createOrReplaceTempView",
        "pattern": r'\.registerTempTable\(',
        "replacement": '.createOrReplaceTempView(',
        "desc": "registerTempTable deprecado en Spark 2.0, removido en 3.x",
    },
    {
        "name": "unionAll → union",
        "pattern": r'\.unionAll\(',
        "replacement": '.union(',
        "desc": "unionAll renombrado a union en Spark 2.0+",
    },
    # Read/Write changes
    {
        "name": "spark.read.json string → path",
        "pattern": r'sqlContext\.read\.json\(',
        "replacement": 'spark.read.json(',
        "desc": "Usar SparkSession.read en vez de SQLContext.read",
    },
    {
        "name": "sqlContext.read → spark.read",
        "pattern": r'sqlContext\.read\.',
        "replacement": 'spark.read.',
        "desc": "Migrar de SQLContext a SparkSession",
    },
    {
        "name": "sqlContext.sql → spark.sql",
        "pattern": r'sqlContext\.sql\(',
        "replacement": 'spark.sql(',
        "desc": "Migrar SQL queries a SparkSession",
    },
    # Pandas UDF changes (Spark 3)
    {
        "name": "PandasUDFType deprecated",
        "pattern": r'from pyspark\.sql\.functions import PandasUDFType',
        "replacement": '# PandasUDFType deprecated in Spark 3.0 — use type hints instead',
        "desc": "Spark 3 usa type hints para Pandas UDFs",
    },
    {
        "name": "pandas_udf with PandasUDFType.SCALAR",
        "pattern": r'@pandas_udf\(([^,]+),\s*PandasUDFType\.SCALAR\)',
        "replacement": r'@pandas_udf(\1)',
        "desc": "Spark 3: pandas_udf infiere el tipo automáticamente",
    },
    # Deprecated configs
    {
        "name": "spark.sql.execution.arrow.enabled",
        "pattern": r'spark\.conf\.set\("spark\.sql\.execution\.arrow\.enabled",\s*"true"\)',
        "replacement": 'spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")',
        "desc": "Config renombrada en Spark 3.0",
    },
    # Partition discovery
    {
        "name": "spark.sql.sources.partitionColumnTypeInference.enabled",
        "pattern": r'"spark\.sql\.sources\.partitionColumnTypeInference\.enabled"',
        "replacement": '"spark.sql.sources.partitionColumnTypeInference.enabled"  # Review: behavior changed in Spark 3',
        "desc": "Partition type inference cambió en Spark 3",
    },
    # Timestamp changes
    {
        "name": "Timestamp rebase config",
        "pattern": r'(spark\s*=\s*SparkSession\.builder)',
        "replacement": r'\1\n    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")',
        "desc": "Spark 3 cambió el parsing de timestamps — LEGACY mantiene compatibilidad",
        "once": True,
    },
]


# ═══════════════════════════════════════════════════════════════
# PYTHON 2 → PYTHON 3 RULES
# ═══════════════════════════════════════════════════════════════

PYTHON_RULES = [
    # Print statement → function
    {
        "name": "print statement → print()",
        "pattern": r'^(\s*)print\s+(?![\(])(.*?)$',
        "replacement": r'\1print(\2)',
        "desc": "Python 3: print es función, no statement",
        "multiline": True,
    },
    # Division
    {
        "name": "Integer division",
        "pattern": r'(?<!\/)\/(?!\/)',
        "replacement": '/',
        "desc": "Python 3: / siempre es float division. Usar // para integer division",
        "skip": True,  # Just warn, don't replace
    },
    # Unicode
    {
        "name": "unicode() → str()",
        "pattern": r'\bunicode\(',
        "replacement": 'str(',
        "desc": "Python 3: no existe unicode(), todo es str (Unicode por defecto)",
    },
    {
        "name": "u'' string prefix",
        "pattern": r"\bu'",
        "replacement": "'",
        "desc": "Python 3: strings son Unicode por defecto, u'' prefix innecesario",
    },
    {
        "name": "u\"\" string prefix",
        "pattern": r'\bu"',
        "replacement": '"',
        "desc": "Python 3: strings son Unicode por defecto",
    },
    # Dict methods
    {
        "name": ".has_key() → in",
        "pattern": r'(\w+)\.has_key\(([^)]+)\)',
        "replacement": r'\2 in \1',
        "desc": "Python 3: dict.has_key() removido, usar 'key in dict'",
    },
    {
        "name": ".iteritems() → .items()",
        "pattern": r'\.iteritems\(\)',
        "replacement": '.items()',
        "desc": "Python 3: dict.iteritems() removido, .items() retorna view",
    },
    {
        "name": ".itervalues() → .values()",
        "pattern": r'\.itervalues\(\)',
        "replacement": '.values()',
        "desc": "Python 3: dict.itervalues() removido",
    },
    {
        "name": ".iterkeys() → .keys()",
        "pattern": r'\.iterkeys\(\)',
        "replacement": '.keys()',
        "desc": "Python 3: dict.iterkeys() removido",
    },
    # Exceptions
    {
        "name": "except Exception, e → except Exception as e",
        "pattern": r'except\s+(\w+)\s*,\s*(\w+)',
        "replacement": r'except \1 as \2',
        "desc": "Python 3: usar 'as' en vez de coma para capturar excepciones",
    },
    # Range
    {
        "name": "xrange → range",
        "pattern": r'\bxrange\(',
        "replacement": 'range(',
        "desc": "Python 3: xrange removido, range() es lazy por defecto",
    },
    # Imports
    {
        "name": "from __future__ import (cleanup)",
        "pattern": r'from __future__ import (?:print_function|division|unicode_literals|absolute_import)',
        "replacement": '# __future__ import no longer needed in Python 3',
        "desc": "Python 3: estos imports de __future__ ya no son necesarios",
    },
    # Raw input
    {
        "name": "raw_input → input",
        "pattern": r'\braw_input\(',
        "replacement": 'input(',
        "desc": "Python 3: raw_input() renombrado a input()",
    },
    # Long type
    {
        "name": "long → int",
        "pattern": r'\blong\(',
        "replacement": 'int(',
        "desc": "Python 3: long removido, int maneja enteros arbitrarios",
    },
    # String types
    {
        "name": "basestring check",
        "pattern": r'\bbasestring\b',
        "replacement": 'str',
        "desc": "Python 3: basestring removido, usar str",
    },
    # Map/filter return iterators
    {
        "name": "map() returns iterator",
        "pattern": r'(?<!\blist\()map\(',
        "replacement": 'list(map(',
        "desc": "Python 3: map() retorna iterator, envolver en list() si se necesita lista",
        "skip": True,  # Just warn
    },
]


# ═══════════════════════════════════════════════════════════════
# GLUE 2.0 → GLUE 4.0 RULES
# ═══════════════════════════════════════════════════════════════

GLUE_RULES = [
    {
        "name": "GlueVersion 2.0 → 4.0",
        "pattern": r'GlueVersion.*["\']2\.0["\']',
        "replacement": 'GlueVersion: "4.0"',
        "desc": "Glue 4.0 usa Spark 3.3 + Python 3.10",
    },
    {
        "name": "Python 2 shebang",
        "pattern": r'#!/usr/bin/env python$',
        "replacement": '#!/usr/bin/env python3',
        "desc": "Glue 4.0 requiere Python 3",
        "multiline": True,
    },
    {
        "name": "from awsglue.transforms import *",
        "pattern": r'from awsglue\.transforms import \*',
        "replacement": 'from awsglue.transforms import *  # Glue 4.0 compatible',
        "desc": "Verificar compatibilidad de transforms con Glue 4.0",
    },
    {
        "name": "DynamicFrame.fromDF deprecated args",
        "pattern": r'DynamicFrame\.fromDF\(([^,]+),\s*glueContext,\s*"([^"]+)"\)',
        "replacement": r'DynamicFrame.fromDF(\1, glueContext, "\2")',
        "desc": "Verificar args de DynamicFrame.fromDF en Glue 4.0",
    },
]


def refactor_code(code, source_version="spark2", target_version="spark3"):
    """
    Refactor code from source_version to target_version.
    Returns (refactored_code, changes_log).
    """
    changes = []

    if source_version in ("spark2", "spark2.x"):
        rules = SPARK_RULES
    elif source_version in ("python2", "python2.7"):
        rules = PYTHON_RULES
    elif source_version in ("glue2", "glue2.0"):
        rules = GLUE_RULES
    elif source_version == "all":
        rules = PYTHON_RULES + SPARK_RULES + GLUE_RULES
    else:
        rules = SPARK_RULES + PYTHON_RULES + GLUE_RULES

    result = code
    for rule in rules:
        if rule.get("skip"):
            # Just detect and warn, don't replace
            matches = re.findall(rule["pattern"], result, re.MULTILINE if rule.get("multiline") else 0)
            if matches:
                changes.append({
                    "name": rule["name"],
                    "desc": rule["desc"],
                    "count": len(matches),
                    "action": "⚠️ WARNING — review manually",
                })
            continue

        flags = re.MULTILINE if rule.get("multiline") else 0
        if rule.get("once"):
            new_result, count = re.subn(rule["pattern"], rule["replacement"], result, count=1, flags=flags)
        else:
            new_result = re.sub(rule["pattern"], rule["replacement"], result, flags=flags)
            count = len(re.findall(rule["pattern"], result, flags=flags))

        if new_result != result and count > 0:
            changes.append({
                "name": rule["name"],
                "desc": rule["desc"],
                "count": count,
                "action": "✅ APPLIED",
            })
            result = new_result

    return result, changes
