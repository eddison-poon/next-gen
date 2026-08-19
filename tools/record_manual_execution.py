from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENVIRONMENTS={"DEV","SIT","UAT","PPD","PROD"}
STATUSES={"PASSED","FAILED","BLOCKED"}

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def write(path:Path,payload): path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")

def bundle_paths(bundle_dir:Path):
    bundle=load(bundle_dir/"bundle.json")
    return bundle, bundle_dir/bundle["release_scope"], bundle_dir/bundle["manual_executions"]

def add_execution(bundle_dir:Path, manual_test_id:str, environment:str, status:str, execution_id:str|None=None, executed_at:str|None=None):
    environment=environment.upper(); status=status.upper()
    assert environment in ENVIRONMENTS, f"invalid environment: {environment}"
    assert status in STATUSES, f"invalid status: {status}"
    _,scope_path,exec_path=bundle_paths(bundle_dir)
    scope=load(scope_path); payload=load(exec_path)

    feature=None
    for item in scope["scope"]["release_items"]:
        for f in item["features"]:
            if f["manual_test_id"]==manual_test_id:
                feature=f; break
        if feature: break
    assert feature is not None, f"Manual Test is not in current release scope: {manual_test_id}"
    assert environment in feature["applicable_environments"], f"{environment} is not applicable for {manual_test_id}"

    when=executed_at or datetime.now().astimezone().isoformat(timespec="seconds")
    datetime.fromisoformat(when)
    if execution_id is None:
        stamp=datetime.fromisoformat(when).strftime("%Y%m%d%H%M%S")
        execution_id=f"{manual_test_id}-{environment}-{stamp}"

    ids={x["execution_id"] for x in payload.get("executions",[])}
    assert execution_id not in ids, f"duplicate execution ID in bundle: {execution_id}"

    row={
        "execution_id":execution_id,
        "manual_test_id":manual_test_id,
        "stream_id":scope["stream"]["id"],
        "release_id":scope["release"]["id"],
        "build":scope["release"]["current_build"],
        "environment":environment,
        "status":status,
        "executed_at":when,
    }
    payload.setdefault("executions",[]).append(row)
    write(exec_path,payload)
    return row

def main():
    p=argparse.ArgumentParser(description="Safely append a Manual execution to a Release Data Bundle.")
    p.add_argument("bundle_dir")
    p.add_argument("--manual-test-id",required=True)
    p.add_argument("--environment",required=True,choices=sorted(ENVIRONMENTS))
    p.add_argument("--status",required=True,choices=sorted(STATUSES))
    p.add_argument("--execution-id")
    p.add_argument("--executed-at")
    a=p.parse_args()
    path=(ROOT/a.bundle_dir).resolve()
    try:
        row=add_execution(path,a.manual_test_id,a.environment,a.status,a.execution_id,a.executed_at)
    except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:
        raise SystemExit(f"ERROR: {e}")
    print("Manual execution recorded")
    print(f"  execution_id: {row['execution_id']}")
    print(f"  test: {row['manual_test_id']}")
    print(f"  environment: {row['environment']}")
    print(f"  status: {row['status']}")
    print(f"  executed_at: {row['executed_at']}")
    print("Next: python tools/publish_release_bundle.py <bundle_dir> --dry-run")

if __name__=="__main__": main()
