from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENVS={"DEV","SIT","UAT","PPD","PROD"}
STATUSES={"PASSED","FAILED","BLOCKED","NOT_EXECUTED"}


def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path:Path,payload):
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")


def find_scenario(payload,test_id):
    found=[]
    for capability in payload.get("capabilities",[]):
        for feature in capability.get("features",[]):
            for scenario in feature.get("scenarios",[]):
                if scenario.get("automation_test_id")==test_id:
                    found.append((capability,feature,scenario))
    assert found, f"Automation Test ID not found: {test_id}"
    assert len(found)==1, f"Automation Test ID is not unique: {test_id}"
    return found[0]


def update_result(path:Path,test_id:str,environment:str,status:str):
    assert path.is_file(), f"Automation workspace not found: {path}"
    payload=load(path)
    assert payload.get("schema_version")=="ng-automation-0.5", "unsupported automation schema"
    capability,feature,scenario=find_scenario(payload,test_id)
    applicable=set(scenario.get("applicable_environments",[]))
    assert environment in applicable, f"{environment} is N/A for {test_id}; applicable environments: {', '.join(scenario.get('applicable_environments',[]))}"
    results=scenario.setdefault("results",{})
    assert set(results)==ENVS, f"incomplete environment matrix for {test_id}"
    old=results.get(environment,"NOT_EXECUTED")
    results[environment]=status
    for env in ENVS-applicable:
        results[env]="N/A"
    payload["generated_at"]=datetime.now().astimezone().isoformat(timespec="seconds")
    write(path,payload)
    return capability,feature,old


def main():
    p=argparse.ArgumentParser(description="Safely update the latest Regression / Automation result in an operator workspace.")
    p.add_argument("automation_file")
    p.add_argument("--automation-test-id",required=True)
    p.add_argument("--environment",required=True,choices=sorted(ENVS))
    p.add_argument("--status",required=True,choices=sorted(STATUSES))
    a=p.parse_args()
    path=(ROOT/a.automation_file).resolve()
    try:
        capability,feature,old=update_result(path,a.automation_test_id,a.environment,a.status)
    except (AssertionError,KeyError,ValueError,json.JSONDecodeError,OSError) as e:
        raise SystemExit(f"ERROR: {e}")
    print("Automation result updated")
    print(f"  capability: {capability['name']}")
    print(f"  feature: {feature['name']}")
    print(f"  test: {a.automation_test_id}")
    print(f"  environment: {a.environment}")
    print(f"  previous: {old}")
    print(f"  current: {a.status}")
    if old==a.status:
        print("  note: status was already set to this value")
    print("Note: automation_regression.json stores the latest regression signal, not execution history.")
    print("Next: python tools/show_automation_status.py <automation_file>")
    print("Then: python tools/publish_automation_status.py <automation_file> --dry-run")

if __name__=="__main__":
    main()
