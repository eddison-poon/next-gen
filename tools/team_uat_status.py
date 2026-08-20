from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
ENVS=["DEV","SIT","UAT","PPD","PROD"]

def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))

def latest(rows):
    return max(rows,key=lambda x: datetime.fromisoformat(x["executed_at"])) if rows else None

def main():
    p=argparse.ArgumentParser(description="Show a concise internal-UAT readiness summary for one Release Data Bundle.")
    p.add_argument("bundle_dir")
    p.add_argument("--automation-file",default="input/automation_regression.json")
    a=p.parse_args()

    bundle_dir=(ROOT/a.bundle_dir).resolve()
    if not bundle_dir.is_dir(): raise SystemExit(f"Bundle directory not found: {bundle_dir}")
    bundle=load(bundle_dir/"bundle.json")
    scope=load(bundle_dir/bundle["release_scope"])
    executions=load(bundle_dir/bundle["manual_executions"]).get("executions",[])

    gates=[]
    for item in scope["scope"]["release_items"]:
        for f in item["features"]:
            for env in f["applicable_environments"]:
                rows=[x for x in executions if x["manual_test_id"]==f["manual_test_id"] and x["stream_id"]==scope["stream"]["id"] and x["release_id"]==scope["release"]["id"] and x["build"]==scope["release"]["current_build"] and x["environment"]==env]
                r=latest(rows)
                gates.append({"jira":item["jira_key"],"feature":f["name"],"test":f["manual_test_id"],"environment":env,"status":r["status"] if r else "NOT_EXECUTED"})

    total=len(gates); executed=sum(g["status"]!="NOT_EXECUTED" for g in gates)
    passed=sum(g["status"]=="PASSED" for g in gates); failed=sum(g["status"]=="FAILED" for g in gates); blocked=sum(g["status"]=="BLOCKED" for g in gates)
    not_exec=total-executed
    completion=round(executed/total*100,1) if total else 0
    pass_rate=round(passed/(passed+failed)*100,1) if passed+failed else None
    health="RED" if blocked or failed else ("GREEN" if total and passed==total else "AMBER")

    print(f"{scope['stream']['name']} | {scope['release']['name']} | build {scope['release']['current_build']}")
    print(f"scope version: {scope['scope_version']}")
    print(f"release items: {len(scope['scope']['release_items'])}")
    print(f"manual gates: {total}")
    print(f"executed: {executed} | passed: {passed} | failed: {failed} | blocked: {blocked} | not executed: {not_exec}")
    print(f"execution progress: {completion}%")
    print(f"pass rate: {'—' if pass_rate is None else str(pass_rate)+'%'}")
    print(f"testing health: {health}")

    exceptions=[g for g in gates if g["status"] in {"FAILED","BLOCKED"}]
    pending=[g for g in gates if g["status"]=="NOT_EXECUTED"]
    if exceptions:
        print("\nExceptions:")
        for g in exceptions:
            print(f"  {g['status']}: {g['jira']} | {g['test']} | {g['environment']} | {g['feature']}")
    if pending:
        print("\nOutstanding gates:")
        for g in pending:
            print(f"  {g['jira']} | {g['test']} | {g['environment']} | {g['feature']}")

    auto=(ROOT/a.automation_file).resolve()
    if auto.is_file():
        payload=load(auto)
        scenarios=[]
        for c in payload.get("capabilities",[]):
            for f in c.get("features",[]):
                for s in f.get("scenarios",[]):
                    scenarios.append(s)
        applicable=sum(len(s.get("applicable_environments",[])) for s in scenarios)
        executed_auto=sum(1 for s in scenarios for e in s.get("applicable_environments",[]) if s.get("results",{}).get(e,"NOT_EXECUTED")!="NOT_EXECUTED")
        coverage=round(executed_auto/applicable*100,1) if applicable else 0
        print("\nAutomation supporting signal:")
        print(f"  scenarios: {len(scenarios)} | coverage: {coverage}% ({executed_auto}/{applicable} gates)")

if __name__=="__main__":
    main()
