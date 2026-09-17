from __future__ import annotations
import argparse, json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"input/release_bundle_template"

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def write(path:Path,payload): path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")

def main():
    p=argparse.ArgumentParser(description="Create a new v0.8 functional Release Data Bundle (MTD -> Execution Variant -> Result).")
    p.add_argument("--stream-id",required=True)
    p.add_argument("--stream-name",required=True)
    p.add_argument("--release-id",required=True)
    p.add_argument("--release-name",required=True)
    p.add_argument("--build",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()

    out=ROOT/a.output
    if out.exists(): raise SystemExit(f"Output already exists: {out}")
    shutil.copytree(TEMPLATE,out)

    scope=load(out/"release_scope.json")
    scope["schema_version"]="ng-release-scope-0.8"
    scope["effective_at"]=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    scope["stream"]={"id":a.stream_id,"name":a.stream_name}
    scope["release"]={"id":a.release_id,"name":a.release_name,"builds":[a.build],"current_build":a.build}
    scope["scope"]={"release_items":[]}
    scope["notes"]="v0.8: Release Item = MTD Jira; Feature = independently assignable Execution Variant Jira."
    write(out/"release_scope.json",scope)

    defs=load(out/"manual_test_definitions.json"); defs["schema_version"]="ng-manual-definition-index-0.8"; defs["definitions"]=[]; write(out/"manual_test_definitions.json",defs)
    executions=load(out/"manual_executions.json"); executions["schema_version"]="ng-manual-execution-index-0.8"; executions["executions"]=[]; write(out/"manual_executions.json",executions)

    print(f"Created v0.8 release bundle: {out.relative_to(ROOT)}")
    print("Add MTD Jira records and their Execution Variant Jira records.")
    print("Then: python tools/publish_release_bundle.py <bundle_dir> --dry-run")

if __name__=="__main__": main()
