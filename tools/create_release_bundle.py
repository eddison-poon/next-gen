from __future__ import annotations
import argparse, json, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"input/release_bundle_template"

def main():
    p=argparse.ArgumentParser(description="Create a new v0.7 Release Data Bundle.")
    p.add_argument("--stream-id",required=True)
    p.add_argument("--stream-name",required=True)
    p.add_argument("--release-id",required=True)
    p.add_argument("--release-name",required=True)
    p.add_argument("--build",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()

    out=ROOT/a.output
    if out.exists():
        raise SystemExit(f"Output already exists: {out}")
    shutil.copytree(TEMPLATE,out)

    scope=json.loads((out/"release_scope.json").read_text(encoding="utf-8"))
    scope["effective_at"]=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    scope["stream"]={"id":a.stream_id,"name":a.stream_name}
    scope["release"]={"id":a.release_id,"name":a.release_name,"builds":[a.build],"current_build":a.build}
    (out/"release_scope.json").write_text(json.dumps(scope,indent=2)+"\n",encoding="utf-8")
    print(f"Created release bundle: {out.relative_to(ROOT)}")
    print("Next: add Release Items, Manual definitions/executions, then run import_data_bundle.py --dry-run")

if __name__=="__main__":
    main()
