# src/mlops_deploy.py
"""
Operacionalizacion / gobierno del paquete MLOps v2: FIRMA el codigo PySpark
generado por BNX y produce un MANIFIESTO verificable de despliegue.

Replica el modelo del framework MVP de gobierno (hash de integridad + firma de
autenticidad), pero aplicado al PySpark REAL que genera el Framework MLOps v2
(no un placeholder). Flujo:

  sign_package(files)  -> {manifest, signature, public_key_pem, private_key_pem?}
  verify_package(manifest, files, public_key_pem) -> {signature, hashes, deployable}

Integridad:  SHA-256 por archivo (detecta cualquier manipulacion posterior).
Autenticidad: firma Ed25519 del manifiesto canonico (detecta manifiestos falsos).

Sin estado global: las llaves se generan por firma (o se pueden pasar). La clave
PRIVADA solo se devuelve si se pide explicitamente (para que el usuario la guarde
en su gestor de secretos); por defecto NO se expone.
"""
import base64
import hashlib
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)


def _sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _canonical(manifest_without_sig):
    """Bytes canonicos del manifiesto (sin el bloque de firma) para firmar/verificar.
    JSON ordenado y compacto -> determinista."""
    return json.dumps(manifest_without_sig, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _pub_pem(pub):
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def sign_package(files, model_name="framework_mlops_v2", execution_id=None,
                 private_key_pem=None, expose_private_key=False):
    """Firma un paquete de archivos (dict {ruta: contenido texto}).

    Devuelve dict:
      {ok, manifest, public_key_pem, [private_key_pem si expose_private_key]}
    El manifest incluye artifacts{ruta: sha256}, metadata y security.signature.
    """
    if private_key_pem:
        priv = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        if not isinstance(priv, Ed25519PrivateKey):
            raise ValueError("La clave privada no es Ed25519.")
    else:
        priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    artifacts = {path: {"sha256": _sha256_text(content)}
                 for path, content in sorted((files or {}).items())}

    manifest_core = {
        "model": {"name": model_name},
        "execution_id": execution_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "algorithm": {"hash": "SHA-256", "signature": "Ed25519"},
    }
    signature = priv.sign(_canonical(manifest_core))
    manifest = dict(manifest_core)
    manifest["security"] = {
        "signature": {"alg": "Ed25519", "value": base64.b64encode(signature).decode("ascii")},
    }
    out = {"ok": True, "manifest": manifest, "public_key_pem": _pub_pem(pub)}
    if expose_private_key:
        out["private_key_pem"] = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
    return out


def verify_package(manifest, files, public_key_pem):
    """Verifica firma + hashes de un paquete. Devuelve
    {signature, hashes, deployable, [reason]}. No lanza: reporta el fallo."""
    result = {"signature": "INVALID", "hashes": "UNKNOWN", "deployable": False}
    try:
        core = {k: v for k, v in manifest.items() if k != "security"}
        sig = base64.b64decode(manifest["security"]["signature"]["value"])
        pub = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(pub, Ed25519PublicKey):
            result["reason"] = "clave publica no Ed25519"
            return result
        pub.verify(sig, _canonical(core))           # lanza si la firma no cuadra
        result["signature"] = "VALID"
    except Exception as e:
        result["reason"] = f"firma invalida: {type(e).__name__}"
        return result

    # Hashes: comparar el sha256 de cada artefacto contra el manifiesto.
    mismatches = []
    arts = manifest.get("artifacts", {})
    for path, meta in arts.items():
        actual = _sha256_text((files or {}).get(path, None) if path in (files or {}) else None)
        if path not in (files or {}):
            mismatches.append(f"falta: {path}")
        elif actual != meta.get("sha256"):
            mismatches.append(f"alterado: {path}")
    if mismatches:
        result["hashes"] = "INVALID"
        result["reason"] = "; ".join(mismatches[:6])
        return result

    result["hashes"] = "VALID"
    result["deployable"] = True
    return result
