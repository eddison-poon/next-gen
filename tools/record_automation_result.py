from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENVS={"DEV","SIT","UAT","PPD","PROD"}
STATUSES={"PASSED","FAILED","BLOCKED","NOT_EXECUTED"}

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def write(path:Path,payload): path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")

def find_scenario(payload,test_id):
    found=[]
    for capability in payload.get("capabilities",[]):
        for feature in capability.get("features",[]):
            for scenario in feature.get("scenarios",[]):
                if scenario.get("automation_test_id")==test_id:
                    found.append((capability,feature,scenario))
    if not found: raise SystemExit(f"Automation Test ID not found: {test_id}")
    if len(found)>1: raise SystemExit(f"Automation Test ID is not unique: {test_id}")
    return found[0]

def main():
    p=argparse.ArgumentParser(description="Safely update the latest Regression / Automation result in an operator workspace.")
    p.add_argument("automation_file")
    p.add_argument("--automation-test-id",required=True)
    p.add_argument("--environment",required=True,choices=sorted(ENVS))
    p.add_argument("--status",required=True,choices=sorted(STATUSES))
    a=p.parse_args()
    path=(ROOT/a.automation_file).resolve()
    if not path.is_file(): raise SystemExit(f"Automation workspace not found: {path}")
    payload=load(path)
    if payload.get("schema_version")!="ng-automation-0.5": raise SystemExit("Unsupported automation schema")
    capability,feature,scenario=find_scenario(payload,a.automation_test_id)
    applicable=set(scenario.get("applicable_environments",[]))
    if a.environment not in applicable:
        raise SystemExit(f"{a.environment} is N/A for {a.automation_test_id}; applicable environments: {', '.join(scenario.get('applicable_environments',[]))}")
    old=scenario.get("results",{}).get(a.environment,"NOT_EXECUTED")
    scenario.setdefault("results",{})[a.environment]=a.status
    for env in ENVS-applicable:
        scenario["results"][env]="N/A"
    payload["generated_at"]=datetime.now().astimezone().isoformat(timespec="seconds")
    write(path,payload)
    print("Automation result updated")
    print(f"  capability: {capability['name']}")
    print(f"  feature: {feature['name']}")
    print(f"  test: {a.automation_test_id}")
    print(f"  environment: {a.environment}")
    print(f"  previous: {old}")
    print(f"  current: {a.status}")
    print("Note: automation_regression.json stores the latest regression signal, not execution history.")

if __name__=="__main__": main()
