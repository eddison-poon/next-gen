from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_SOURCE=ROOT/"data/automation_regression.json"
DEFAULT_TARGET=ROOT/"input/automation_regression.json"

def main():
    p=argparse.ArgumentParser(description="Create a durable operator workspace for Regression / Automation data.")
    p.add_argument("--source",default=str(DEFAULT_SOURCE.relative_to(ROOT)))
    p.add_argument("--output",default=str(DEFAULT_TARGET.relative_to(ROOT)))
    p.add_argument("--force",action="store_true",help="Replace an existing workspace.")
    a=p.parse_args()
    source=(ROOT/a.source).resolve(); target=(ROOT/a.output).resolve()
    if not source.is_file(): raise SystemExit(f"Automation source not found: {source}")
    payload=json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version")!="ng-automation-0.5": raise SystemExit("Unsupported automation schema")
    if target.exists() and not a.force:
        raise SystemExit(f"Automation workspace already exists: {target.relative_to(ROOT)} (use --force only when replacement is intended)")
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    scenarios=sum(len(f.get("scenarios",[])) for c in payload.get("capabilities",[]) for f in c.get("features",[]))
    print(f"Automation workspace created: {target.relative_to(ROOT)}")
    print(f"Capabilities: {len(payload.get('capabilities',[]))}")
    print(f"Automated scenarios: {scenarios}")
    print("Next: use record_automation_result.py and show_automation_status.py")

if __name__=="__main__": main()
