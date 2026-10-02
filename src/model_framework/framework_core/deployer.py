from pathlib import Path
import json
from .security import sha256_file, canonical
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import base64

def verify(manifest_path, public_key):
    m=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    key=serialization.load_pem_public_key(Path(public_key).read_bytes())
    sig=base64.b64decode(m["security"]["signature"]["value"])
    key.verify(sig, canonical(m))
    for name,a in m["artifacts"].items():
        if sha256_file(a["path"]) != a["sha256"]:
            raise ValueError(f"Hash mismatch: {name}")
    return {"signature":"VALID","hashes":"VALID","deployable":True}
