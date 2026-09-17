from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; ENVIRONMENTS=["DEV","SIT","UAT","PPD","PROD"]
def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def latest(rows): return max(rows,key=lambda x:datetime.fromisoformat(x["executed_at"])) if rows else None

def main():
    p=argparse.ArgumentParser(description="Show v0.8 MTD / Execution Variant status before import."); p.add_argument("bundle_dir"); a=p.parse_args(); bundle_dir=(ROOT/a.bundle_dir).resolve()
    bundle=load(bundle_dir/"bundle.json"); scope=load(bundle_dir/bundle["release_scope"]); definitions=load(bundle_dir/bundle["manual_test_definitions"]).get("definitions",[]); executions=load(bundle_dir/bundle["manual_executions"]).get("executions",[]); defs={d["manual_test_id"]:d for d in definitions}
    items=scope["scope"]["release_items"]; variants=sum(len(x["features"]) for x in items)
    print(f"{scope['stream']['name']} | {scope['release']['name']} | build {scope['release']['current_build']}"); print(f"scope version: {scope['scope_version']}"); print(f"MTDs: {len(items)} | Execution Variants: {variants} | Recorded Results: {len(executions)}")
    for item in items:
        mtd_id=item["features"][0]["manual_test_id"] if item["features"] else "UNKNOWN"; d=defs.get(mtd_id,{})
        print(f"\n{mtd_id} | {item['summary']} | {d.get('priority',item.get('priority','-'))} | Jira {item['jira_key']}")
        for f in item["features"]:
            states=[]
            for env in ENVIRONMENTS:
                if env not in f["applicable_environments"]: states.append(f"{env}=N/A"); continue
                rows=[x for x in executions if (x.get("execution_variant_id")==f["id"] or (not x.get("execution_variant_id") and x["manual_test_id"]==f["manual_test_id"])) and x["environment"]==env and x["build"]==scope["release"]["current_build"]]
                row=latest(rows); states.append(f"{env}={row['status'] if row else 'NOT_EXECUTED'}")
            details=[]
            if f.get("role"): details.append(f"role={f['role']}")
            if f.get("expected_access"): details.append(f"access={f['expected_access']}")
            suffix=(" | "+" | ".join(details)) if details else ""
            print(f"  {f['id']} | {f['name']} | Jira {f['jira_key']}{suffix}"); print("    "+" | ".join(states))
if __name__=="__main__": main()
