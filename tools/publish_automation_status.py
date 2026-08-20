from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"data/automation_regression.json"
ENVS={"DEV","SIT","UAT","PPD","PROD"}
STATUSES={"PASSED","FAILED","BLOCKED","NOT_EXECUTED","N/A"}

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))

def validate(payload):
    assert payload.get("schema_version")=="ng-automation-0.5", "unsupported automation schema"
    cap_ids=set(); feature_ids=set(); scenario_ids=set(); test_ids=set()
    for c in payload.get("capabilities",[]):
        assert c["id"] not in cap_ids, f"duplicate capability: {c['id']}"; cap_ids.add(c["id"])
        for f in c.get("features",[]):
            assert f["id"] not in feature_ids, f"duplicate feature: {f['id']}"; feature_ids.add(f["id"])
            for s in f.get("scenarios",[]):
                assert s["id"] not in scenario_ids, f"duplicate scenario: {s['id']}"; scenario_ids.add(s["id"])
                assert s["automation_test_id"] not in test_ids, f"duplicate Automation Test ID: {s['automation_test_id']}"; test_ids.add(s["automation_test_id"])
                applicable=set(s.get("applicable_environments",[]))
                assert applicable<=ENVS, f"invalid environment: {s['automation_test_id']}"
                results=s.get("results",{})
                assert set(results)==ENVS, f"incomplete environment matrix: {s['automation_test_id']}"
                assert set(results.values())<=STATUSES, f"invalid result: {s['automation_test_id']}"
                for e in ENVS-applicable: assert results[e]=="N/A", f"{s['automation_test_id']} {e} must be N/A"
                for e in applicable: assert results[e]!="N/A", f"{s['automation_test_id']} {e} is applicable but marked N/A"
    return len(cap_ids),len(test_ids)

def main():
    p=argparse.ArgumentParser(description="Validate or publish the durable Regression / Automation operator workspace.")
    p.add_argument("automation_file")
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",action="store_true")
    mode.add_argument("--apply",action="store_true")
    a=p.parse_args()
    path=(ROOT/a.automation_file).resolve()
    if not path.is_file(): raise SystemExit(f"Automation workspace not found: {path}")
    try:
        payload=load(path); caps,tests=validate(payload)
    except (AssertionError,KeyError,ValueError) as e:
        print(f"ERROR: {e}",file=sys.stderr); raise SystemExit(1)
    print("Automation workspace validation passed")
    print(f"  capabilities: {caps}")
    print(f"  automated scenarios: {tests}")
    if a.dry_run:
        print("DRY RUN: canonical automation data was not changed")
        return
    shutil.copyfile(path,TARGET)
    print(f"Published automation workspace to {TARGET.relative_to(ROOT)}")
    subprocess.run([sys.executable,"tools/run_uat_checks.py"],cwd=ROOT,check=True)
    print("Automation publish completed successfully")

if __name__=="__main__": main()
