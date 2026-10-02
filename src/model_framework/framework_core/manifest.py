from pathlib import Path
import json
from .security import sha256_file, encrypt_file, canonical, sign

def create(config, execution_id, files, runtime, security):
    m={"manifest_version":"2.0","execution_id":execution_id,
       "framework":config["framework"],"model":config["model"],
       "algorithm":config["algorithm"],"runtime":runtime,
       "components":config["pipeline"],
       "artifacts":{n:{"path":str(p),"sha256":sha256_file(p)} for n,p in files.items()},
       "security":{"encryption":None,"signature":None},
       "deployment_control":{"immutable":True,"verify_before_deploy":True}}
    code=files.get("generated_code")
    if code and security["encrypt_generated_code"]:
        enc=Path(str(code)+".enc")
        h=encrypt_file(code,enc,security["encryption_key_file"])
        m["security"]["encryption"]={"algorithm":"Fernet","path":str(enc),
                                     "sha256":h,"purpose":"confidentiality"}
    m["security"]["signature"]={"algorithm":"Ed25519"}
    m["security"]["signature"]["value"]=sign(canonical(m),
                                             security["signing_private_key_file"])
    return m

def save(m,path):
    Path(path).write_text(json.dumps(m,indent=2,sort_keys=True),encoding="utf-8")
