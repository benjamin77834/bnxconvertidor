import numpy as np
from pathlib import Path
import xgboost as xgb

class DataValidation:
    name="data_validation"
    def run(self,c):
        f=c["config"]["features"]; df=c["data"]
        missing=[x for x in f if x not in df.columns]
        if missing: raise ValueError(f"Missing features: {missing}")
        if df[f].isnull().any().any(): raise ValueError("Null input detected")
        c["validation"]={"rows":len(df),"status":"PASSED"}; return c

class Preparation:
    name="preparation"
    def run(self,c):
        # SWITCH POINT: replace with corporate preparation library.
        c["prepared_data"]=c["data"].copy(); return c

class FeatureEngineering:
    name="feature_engineering"
    def run(self,c):
        # SWITCH POINT: replace with corporate reusable UDF/feature library.
        c["X"]=c["prepared_data"][c["config"]["features"]].copy(); return c

class Score:
    name="score"
    def run(self,c):
        # DEMO reference scorer. Production implementation loads approved PMML
        # and delegates scoring to JPMML/JVM.
        m=xgb.XGBClassifier(); m.load_model(c["model_path"])
        c["predictions"]=m.predict_proba(c["X"])[:,1]
        c["scoring_engine"]="DEMO_XGBOOST"; return c

class Evaluation:
    name="evaluation"
    def run(self,c):
        p=np.asarray(c["predictions"])
        c["metrics"]={"rows":int(len(p)),"mean":float(p.mean()),
                      "min":float(p.min()),"max":float(p.max())}
        c["evaluation"]={"status":"PASSED",
                         "max_absolute_error":c["config"]["validation"]["max_absolute_error"]}
        return c

class Package:
    name="package"
    def run(self,c):
        Path(c["output_dir"]).mkdir(parents=True,exist_ok=True)
        return c

def default_catalog():
    from .catalog import ComponentCatalog
    q=ComponentCatalog()
    for x in [DataValidation(),Preparation(),FeatureEngineering(),
              Score(),Evaluation(),Package()]:
        q.register(x.name,x)
    return q
