from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENVS=["DEV","SIT","UAT","PPD","PROD"]

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))

def main():
    p=argparse.ArgumentParser(description="Show human-readable Regression / Automation operator status.")
    p.add_argument("automation_file")
    a=p.parse_args()
    path=(ROOT/a.automation_file).resolve()
    if not path.is_file(): raise SystemExit(f"Automation workspace not found: {path}")
    payload=load(path)
    if payload.get("schema_version")!="ng-automation-0.5": raise SystemExit("Unsupported automation schema")
    print(f"Automation workspace: {path.relative_to(ROOT)}")
    print(f"Generated at: {payload.get('generated_at','—')}")
    for capability in payload.get("capabilities",[]):
        print(f"\n{capability['name']} | {len(capability.get('features',[]))} features")
        for feature in capability.get("features",[]):
            print(f"  {feature['id']} | {feature['name']}")
            for scenario in feature.get("scenarios",[]):
                results=scenario.get("results",{})
                matrix=" | ".join(f"{e}={results.get(e,'NOT_EXECUTED')}" for e in ENVS)
                print(f"    {scenario['automation_test_id']} | {scenario['name']}")
                print(f"      {matrix}")

if __name__=="__main__": main()
