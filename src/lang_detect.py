"""Deteccion automatica del lenguaje fuente legacy a partir del contenido.

Soporta: COBOL (.cbl/.cob), ALGOL (Unisys MCP, .alg) y Ab Initio (.mp).
La deteccion es por PUNTUACION de marcadores sintacticos: cada lenguaje suma
puntos por patrones que le son propios y el ganador es el de mayor puntaje.
Esto es mas robusto que mirar solo la extension (util cuando se pega codigo
en un textarea sin extension o el archivo viene como .txt).

Uso:
    from src.lang_detect import detect_language
    lang, scores = detect_language(source_text, filename="programa.txt")
    # lang in {"cobol", "algol", "abinitio", "unknown"}
"""
import os
import re

# Marcadores por lenguaje. Cada tupla es (regex, peso). Los pesos altos son
# para patrones casi exclusivos de ese lenguaje; los bajos para pistas debiles.
_COBOL_MARKERS = [
    (r"\bIDENTIFICATION\s+DIVISION\b", 5),
    (r"\bPROCEDURE\s+DIVISION\b", 5),
    (r"\bDATA\s+DIVISION\b", 4),
    (r"\bENVIRONMENT\s+DIVISION\b", 4),
    (r"\bWORKING-STORAGE\s+SECTION\b", 4),
    (r"\bFILE\s+SECTION\b", 3),
    (r"\bPIC(?:TURE)?\s+[9XSVA(]", 4),
    (r"\bCOMP-3\b", 3),
    (r"\bPERFORM\b", 2),
    (r"\bMOVE\b.+\bTO\b", 2),
    (r"\bOCCURS\b", 2),
    (r"^\s*\d{6}\b", 1),            # numeracion de columnas (COBOL fijo)
    (r"\bSTOP\s+RUN\b", 2),
]

_ALGOL_MARKERS = [
    (r":=", 3),                     # asignacion ALGOL
    (r"\bPROCEDURE\b", 2),
    (r"\bFILE\b\s+\w+\s*\(", 3),    # declaracion de FILE con atributos
    (r"\bRECORD\b", 2),
    (r"\bREAL\b", 2),
    (r"\bINTEGER\b", 2),
    (r"\bBEGIN\b", 2),
    (r"\bEND\b\s*[.;]", 2),
    (r"\bEBCDIC\b", 3),
    (r"\bDO\b.+\bUNTIL\b", 2),
    (r"\bWHILE\b.+\bDO\b", 2),
    (r"\barray\b", 1),
    (r"%.*$", 1),                   # comentario ALGOL con %
]

_ABINITIO_MARKERS = [
    (r"^\s*NODE\s+\w+\s*:", 4),     # formato .mp de este proyecto
    (r"\w+\s*->\s*\w+", 3),         # aristas
    (r"\bmp_", 2),
    (r"\binput_file\b|\boutput_file\b|\breformat\b|\bjoin\b", 2),
]


def _score(text, markers):
    total = 0
    for pattern, weight in markers:
        hits = len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))
        if hits:
            # Cada marcador suma su peso una vez, mas un extra decreciente por
            # repeticiones (evita que un solo patron repetido domine el score).
            total += weight + min(hits - 1, 3)
    return total


def detect_language(text, filename=""):
    """Devuelve (lang, scores). lang in {cobol, algol, abinitio, unknown}.

    La extension del archivo (si viene) actua como fuerte desempate: un .cbl
    siempre es cobol, .alg siempre algol, .mp siempre abinitio. Si la extension
    no es concluyente, decide la puntuacion por contenido.
    """
    text = text or ""
    ext = os.path.splitext(filename or "")[1].lower().lstrip(".")

    # Extension concluyente -> ruteo directo (pero igual calculamos scores).
    ext_lang = {
        "cbl": "cobol", "cob": "cobol", "cobol": "cobol",
        "alg": "algol", "algol": "algol",
        "mp": "abinitio",
    }.get(ext)

    scores = {
        "cobol": _score(text, _COBOL_MARKERS),
        "algol": _score(text, _ALGOL_MARKERS),
        "abinitio": _score(text, _ABINITIO_MARKERS),
    }

    if ext_lang:
        return ext_lang, scores

    # Sin extension util: ganador por puntuacion, con umbral minimo.
    best = max(scores, key=scores.get)
    if scores[best] < 3:
        return "unknown", scores
    return best, scores
