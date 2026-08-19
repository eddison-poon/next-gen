from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENVIRONMENTS=["DEV","SIT","UAT","PPD","PROD"]

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))

def latest(rows):
    if not rows: return None
    return max(rows,key=lambda x:datetime.fromisoformat(x["executed_at"]))

def main():
    p=argparse.ArgumentParser(description="Show the current status of one Release Data Bundle before import.")
    p.add_argument("bundle_dir")
    a=p.parse_args()
    bundle_dir=(ROOT/a.bundle_dir).resolve()
    bundle=load(bundle_dir/"bundle.json")
    scope=load(bundle_dir/bundle["release_scope"])
    executions=load(bundle_dir/bundle["manual_executions"]).get("executions",[])

    print(f"{scope['stream']['name']} | {scope['release']['name']} | build {scope['release']['current_build']}")
    print(f"scope version: {scope['scope_version']}")
    print(f"release items: {len(scope['scope']['release_items'])}")
    for item in scope["scope"]["release_items"]:
        print(f"\n{item['jira_key']} | {item['summary']}")
        for f in item["features"]:
            states=[]
            for env in ENVIRONMENTS:
                if env not in f["applicable_environments"]:
                    states.append(f"{env}=N/A")
                    continue
                rows=[x for x in executions if x["manual_test_id"]==f["manual_test_id"] and x["environment"]==env and x["build"]==scope["release"]["current_build"]]
                row=latest(rows)
                states.append(f"{env}={row['status'] if row else 'NOT_EXECUTED'}")
            print(f"  {f['id']} | {f['name']}")
            print(f"    {f['manual_test_id']} | "+" | ".join(states))

if __name__=="__main__": main()
