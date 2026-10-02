from pathlib import Path
from uuid import uuid4
import pandas as pd, xgboost as xgb
from framework_core.config_loader import load_config,validate_config
from framework_core.audit import AuditLogger
from framework_core.email_control import ControlEmail
from framework_core.components import default_catalog
from framework_core.orchestrator import Orchestrator
from framework_core.security import ensure_keys
from framework_core.manifest import create,save
from framework_core.deployer import verify

BASE=Path(__file__).resolve().parent.parent
CFG=BASE/"configs/model_xgboost_enterprise.yml"; DATA=BASE/"examples/data/input_credit_risk.csv"
ART=BASE/"artifacts"; OUT=BASE/"generated"; SEC=BASE/"secrets"

def create_business_model(features):
    df=pd.read_csv(DATA); m=xgb.XGBClassifier(n_estimators=30,max_depth=3,
        learning_rate=.1,random_state=42,eval_metric="logloss")
    m.fit(df[features],df["default"])
    ART.mkdir(exist_ok=True); p=ART/"credit_risk_xgboost.json"; m.save_model(p); return p

def main():
    config=load_config(CFG); validate_config(config)
    execution_id=str(uuid4()); OUT.mkdir(exist_ok=True); ART.mkdir(exist_ok=True)
    fk,sk,pk=ensure_keys(SEC)
    model=create_business_model(config["features"])
    notifier=ControlEmail(config["notifications"])
    notifier.send("Framework - INPUT recibido",
                  f"execution_id={execution_id}\nmodel={config['model']['name']}\ninput={DATA}")
    context={"execution_id":execution_id,"config":config,"data":pd.read_csv(DATA),
             "model_path":model,"output_dir":OUT}
    logger=AuditLogger(OUT/"audit.jsonl")
    result=Orchestrator(default_catalog(),logger).execute(context)

    code=OUT/"generated_score.py"
    code.write_text("# GENERATED STANDARD CODE\n# SWITCH POINT FOR CORPORATE CODE\n",encoding="utf-8")
    pmml=ART/"credit_risk_xgboost.pmml"
    pmml.write_text("<!-- Approved PMML artifact: produced by enterprise converter -->\n",
                    encoding="utf-8")

    files={"configuration":CFG,"model":model,"pmml":pmml,"generated_code":code}
    runtime={"profile":config["reusable_libraries"]["runtime_profile"],
             "version":config["reusable_libraries"]["version"],
             "dependencies":config["reusable_libraries"]["dependencies"]}
    manifest=create(config,execution_id,files,runtime,config["security"])
    mp=OUT/"execution_manifest.json"; save(manifest,mp)
    check=verify(mp,config["security"]["signing_public_key_file"])
    notifier.send("Framework - OUTPUT listo",
                  f"execution_id={execution_id}\nmanifest={mp}\ndeployable={check['deployable']}")
    print("EXECUTION:",execution_id)
    print("AUDIT:",OUT/"audit.jsonl")
    print("MANIFEST:",mp)
    print("VERIFY:",check)
    return check

if __name__=="__main__": main()
