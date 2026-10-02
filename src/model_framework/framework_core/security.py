from pathlib import Path
import base64, hashlib, json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def ensure_keys(directory):
    d=Path(directory); d.mkdir(parents=True,exist_ok=True)
    fk=d/"demo_fernet.key"; sk=d/"demo_ed25519_private.pem"; pk=d/"demo_ed25519_public.pem"
    if not fk.exists(): fk.write_bytes(Fernet.generate_key())
    if not sk.exists():
        k=Ed25519PrivateKey.generate()
        sk.write_bytes(k.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        pk.write_bytes(k.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    return fk,sk,pk

def encrypt_file(src,dst,key):
    data=Fernet(Path(key).read_bytes()).encrypt(Path(src).read_bytes())
    Path(dst).write_bytes(data); return hashlib.sha256(data).hexdigest()

def canonical(m):
    import copy

    x = copy.deepcopy(m)

    # La firma NO forma parte del contenido firmado.
    # El algoritmo sí forma parte del contrato.
    # Solo eliminamos el valor de la firma.
    if "security" in x and "signature" in x["security"]:
        x["security"]["signature"].pop("value", None)

    return json.dumps(
        x,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

def sign(data,key):
    k=serialization.load_pem_private_key(Path(key).read_bytes(),password=None)
    return base64.b64encode(k.sign(data)).decode()
