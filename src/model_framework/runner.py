# src/model_framework/runner.py
"""Runner del Framework de Modelos para el servidor BNX.

Adapta examples/run_colab.py para ejecutarse desde serve_ui.py: trabaja en un
directorio AISLADO (no ensucia el repo), acepta un YAML y dataset opcionales, y
devuelve un dict con todo el resultado (manifest, audit, codigo, pmml, deployable).

Flujo (igual al notebook):
  cargar+validar YAML -> claves -> modelo demo (XGBoost) -> INPUT email ->
  Orchestrator (data_validation..package) -> codigo + PMML -> manifest
  (SHA-256 + cifrado Fernet + firma Ed25519) -> verify -> OUTPUT email.

El entrenamiento NO es parte del framework: create_business_model solo simula el
artefacto que negocio ya habria entregado.
"""
from pathlib import Path
from uuid import uuid4
import json
import os
import shutil
import tempfile

_HERE = Path(__file__).resolve().parent
_DEFAULT_CFG = _HERE / "configs" / "model_xgboost_enterprise.yml"
_DEFAULT_DATA = _HERE / "examples" / "data" / "input_credit_risk.csv"
_DEFAULT_MODEL = _HERE / "artifacts" / "credit_risk_xgboost.json"


def _read_jsonl(path):
    rows = []
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def run_framework(config_yaml=None, data_csv=None, work_dir=None, train_model=True):
    """Ejecuta el framework completo y devuelve un dict con el resultado.

    config_yaml: contenido YAML (str) o None para usar el de ejemplo.
    data_csv:    contenido CSV (str) o None para usar el dataset de ejemplo.
    work_dir:    directorio de trabajo; si None se crea un temporal.
    train_model: si True, genera el modelo demo con XGBoost (simula el entregado
                 por negocio); si False, usa el artifact .json ya presente.

    El resultado incluye: ok, execution_id, deployable, verify, manifest, audit,
    generated_code, pmml, emails, artifacts, lines/warnings.
    """
    import pandas as pd
    from .framework_core.config_loader import load_config, validate_config
    from .framework_core.audit import AuditLogger
    from .framework_core.email_control import ControlEmail
    from .framework_core.components import default_catalog
    from .framework_core.orchestrator import Orchestrator
    from .framework_core.security import ensure_keys
    from .framework_core.manifest import create, save
    from .framework_core.deployer import verify

    created_tmp = False
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="bnx_modelfw_")
        created_tmp = True
    work = Path(work_dir)
    (work / "configs").mkdir(parents=True, exist_ok=True)
    (work / "data").mkdir(parents=True, exist_ok=True)
    out = work / "generated"
    art = work / "artifacts"
    sec = work / "secrets"
    out.mkdir(parents=True, exist_ok=True)
    art.mkdir(parents=True, exist_ok=True)

    # Config y datos: usar los provistos o los de ejemplo.
    cfg_path = work / "configs" / "model.yml"
    cfg_path.write_text(config_yaml if config_yaml else _DEFAULT_CFG.read_text(encoding="utf-8"),
                        encoding="utf-8")
    data_path = work / "data" / "input.csv"
    data_path.write_text(data_csv if data_csv else _DEFAULT_DATA.read_text(encoding="utf-8"),
                         encoding="utf-8")

    # ControlEmail escribe a 'generated/emails' RELATIVO al CWD; ejecutamos con el
    # CWD en el work_dir para aislar todo lo que el framework escribe por ruta rel.
    prev_cwd = os.getcwd()
    try:
        os.chdir(work)
        config = load_config(cfg_path)
        validate_config(config)
        execution_id = str(uuid4())
        ensure_keys(sec)

        # Modelo "entregado por negocio" (demo). Si train_model, se entrena un
        # XGBoost pequeno sobre el dataset; si no, se reusa el artifact de ejemplo.
        model_path = art / "credit_risk_xgboost.json"
        if train_model:
            import xgboost as xgb
            df_train = pd.read_csv(data_path)
            feats = config["features"]
            m = xgb.XGBClassifier(n_estimators=30, max_depth=3, learning_rate=.1,
                                  random_state=42, eval_metric="logloss")
            m.fit(df_train[feats], df_train["default"])
            m.save_model(model_path)
        else:
            shutil.copy(_DEFAULT_MODEL, model_path)

        notifier = ControlEmail(config["notifications"])
        notifier.send("Framework - INPUT recibido",
                      f"execution_id={execution_id}\nmodel={config['model']['name']}\ninput={data_path}")

        context = {"execution_id": execution_id, "config": config,
                   "data": pd.read_csv(data_path), "model_path": str(model_path),
                   "output_dir": str(out)}
        logger = AuditLogger(out / "audit.jsonl")
        result_ctx = Orchestrator(default_catalog(), logger).execute(context)

        # Codigo generado + PMML (puntos de switch a librerias corporativas).
        code = out / "generated_score.py"
        code.write_text("# GENERATED STANDARD CODE\n# SWITCH POINT FOR CORPORATE CODE\n",
                        encoding="utf-8")
        pmml = art / "credit_risk_xgboost.pmml"
        pmml.write_text("<!-- Approved PMML artifact: produced by enterprise converter -->\n",
                        encoding="utf-8")

        files = {"configuration": cfg_path, "model": model_path, "pmml": pmml,
                 "generated_code": code}
        runtime = {"profile": config["reusable_libraries"]["runtime_profile"],
                   "version": config["reusable_libraries"]["version"],
                   "dependencies": config["reusable_libraries"]["dependencies"]}
        manifest = create(config, execution_id, files, runtime, config["security"])
        mp = out / "execution_manifest.json"
        save(manifest, mp)

        check = verify(mp, config["security"]["signing_public_key_file"])

        notifier.send("Framework - OUTPUT listo",
                      f"execution_id={execution_id}\nmanifest={mp}\ndeployable={check['deployable']}")

        emails = []
        edir = out / "emails"
        if edir.exists():
            for ef in sorted(edir.glob("*.eml")):
                emails.append({"name": ef.name, "content": ef.read_text(encoding="utf-8")})

        metrics = result_ctx.get("metrics", {})
        return {
            "ok": True,
            "execution_id": execution_id,
            "deployable": check.get("deployable", False),
            "verify": check,
            "manifest": manifest,
            "audit": _read_jsonl(out / "audit.jsonl"),
            "generated_code": code.read_text(encoding="utf-8"),
            "pmml": pmml.read_text(encoding="utf-8"),
            "emails": emails,
            "metrics": metrics,
            "pipeline": config.get("pipeline", []),
            "work_dir": str(work),
        }
    finally:
        os.chdir(prev_cwd)
        # No borramos work_dir si el caller lo paso (puede querer /model/verify luego).
        if created_tmp and work_dir and os.path.isdir(work_dir):
            # Mantener para una posible verificacion posterior; el caller limpia.
            pass


def verify_manifest(manifest_path, public_key_path):
    """Verifica un manifest ya generado (firma Ed25519 + hashes). Devuelve dict
    {deployable, ...} o {error}. Usado por la demo altero->rechazo->restauro."""
    from .framework_core.deployer import verify
    try:
        return verify(manifest_path, public_key_path)
    except Exception as e:
        return {"deployable": False, "error": f"{type(e).__name__}: {e}"}
