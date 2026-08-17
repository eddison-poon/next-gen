from __future__ import annotations
import argparse, copy, json, sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
ENVIRONMENTS={"DEV","SIT","UAT","PPD","PROD"}
MANUAL_STATUS={"PASSED","FAILED","BLOCKED"}

def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path:Path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")

def require_bundle_file(bundle_dir, bundle, key):
    name=bundle.get(key)
    if not name:
        return None
    path=bundle_dir/name
    if not path.exists():
        raise AssertionError(f"bundle references missing file: {name}")
    return path

def validate_scope(scope, defs_by_id):
    assert scope["schema_version"]=="ng-release-scope-0.4"
    assert scope["release"]["current_build"] in scope["release"]["builds"]
    jira=set(); features=set(); scenarios=set()
    for item in scope["scope"]["release_items"]:
        assert item["jira_key"] not in jira, f"duplicate Jira Release Item: {item['jira_key']}"
        jira.add(item["jira_key"])
        assert item["features"], f"Release Item has no features: {item['jira_key']}"
        for f in item["features"]:
            assert f["id"] not in features, f"duplicate feature: {f['id']}"; features.add(f["id"])
            assert f["scenario_id"] not in scenarios, f"duplicate scenario: {f['scenario_id']}"; scenarios.add(f["scenario_id"])
            assert f["manual_test_id"] in defs_by_id, f"missing Manual Test Definition: {f['manual_test_id']}"
            d=defs_by_id[f["manual_test_id"]]
            assert d["scenario_id"]==f["scenario_id"], f"scenario mismatch: {f['manual_test_id']}"
            assert d["jira_key"]==item["jira_key"], f"Jira mismatch: {f['manual_test_id']}"
            envs=f["applicable_environments"]
            assert envs, f"no applicable environments: {f['id']}"
            assert len(envs)==len(set(envs)), f"duplicate applicable environment: {f['id']}"
            assert set(envs)<=ENVIRONMENTS, f"invalid environment: {f['id']}"

def merge_by_id(existing, incoming, key):
    result={x[key]:copy.deepcopy(x) for x in existing}
    for x in incoming:
        result[x[key]]=copy.deepcopy(x)
    return list(result.values())

def validate_execution_rows(rows, defs_by_id, scope):
    builds=set(scope["release"]["builds"])
    sid=scope["stream"]["id"]; rid=scope["release"]["id"]
    ids=set()
    for x in rows:
        assert x["execution_id"] not in ids, f"duplicate execution ID in bundle: {x['execution_id']}"; ids.add(x["execution_id"])
        assert x["manual_test_id"] in defs_by_id, f"execution references unknown Manual Test Definition: {x['manual_test_id']}"
        assert x["stream_id"]==sid and x["release_id"]==rid, f"execution release mismatch: {x['execution_id']}"
        assert x["build"] in builds, f"execution build not in Release Manifest: {x['execution_id']}"
        assert x["environment"] in ENVIRONMENTS
        assert x["status"] in MANUAL_STATUS
        datetime.fromisoformat(x["executed_at"])

def apply_bundle(bundle_dir:Path, dry_run:bool):
    bundle=load(bundle_dir/"bundle.json")
    assert bundle["schema_version"]=="ng-release-data-bundle-0.7"
    scope=load(require_bundle_file(bundle_dir,bundle,"release_scope"))
    incoming_defs=load(require_bundle_file(bundle_dir,bundle,"manual_test_definitions")).get("definitions",[])
    incoming_exec=load(require_bundle_file(bundle_dir,bundle,"manual_executions")).get("executions",[])

    current_defs=load(DATA/"manual_test_definitions.json")
    merged_defs=merge_by_id(current_defs["definitions"],incoming_defs,"manual_test_id")
    defs_by_id={x["manual_test_id"]:x for x in merged_defs}

    validate_scope(scope,defs_by_id)
    validate_execution_rows(incoming_exec,defs_by_id,scope)

    registry=load(DATA/"release_registry.json")
    stream=next((s for s in registry["streams"] if s["id"]==scope["stream"]["id"]),None)
    manifest_rel=f"data/releases/{scope['stream']['id']}/{scope['release']['id']}.json"
    if stream is None:
        stream={"id":scope["stream"]["id"],"name":scope["stream"]["name"],"releases":[]}
        registry["streams"].append(stream)
    else:
        stream["name"]=scope["stream"]["name"]
    release_ref=next((r for r in stream["releases"] if r["id"]==scope["release"]["id"]),None)
    if release_ref is None:
        stream["releases"].append({"id":scope["release"]["id"],"name":scope["release"]["name"],"manifest":manifest_rel})
    else:
        release_ref.update({"name":scope["release"]["name"],"manifest":manifest_rel})

    current_exec=load(DATA/"manual_executions.json")
    merged_exec=merge_by_id(current_exec["executions"],incoming_exec,"execution_id")

    print("Release Data Bundle validation passed")
    print(f"  stream: {scope['stream']['name']}")
    print(f"  release: {scope['release']['name']}")
    print(f"  build(s): {', '.join(scope['release']['builds'])}")
    print(f"  release items: {len(scope['scope']['release_items'])}")
    print(f"  incoming Manual definitions: {len(incoming_defs)}")
    print(f"  incoming Manual executions: {len(incoming_exec)}")

    if dry_run:
        print("DRY RUN: canonical data was not changed")
        return

    write(DATA/"release_registry.json",registry)
    write(ROOT/manifest_rel,scope)
    current_defs["definitions"]=merged_defs; write(DATA/"manual_test_definitions.json",current_defs)
    current_exec["executions"]=merged_exec; write(DATA/"manual_executions.json",current_exec)

    auto_path=require_bundle_file(bundle_dir,bundle,"automation_regression")
    if auto_path:
        auto=load(auto_path)
        if auto.get("capabilities"):
            write(DATA/"automation_regression.json",auto)
    perf_path=require_bundle_file(bundle_dir,bundle,"performance_results")
    if perf_path:
        incoming_perf=load(perf_path)
        if incoming_perf.get("results"):
            current_perf=load(DATA/"performance_results.json")
            current_perf["results"]=merge_by_id(current_perf["results"],incoming_perf["results"],"test_run")
            current_perf["generated_at"]=incoming_perf.get("generated_at",current_perf.get("generated_at"))
            write(DATA/"performance_results.json",current_perf)

    scope_log=load(DATA/"release_scope_log.json")
    scope_log["changes"].append({
        "effective_at":scope["effective_at"],
        "stream_id":scope["stream"]["id"],
        "release_id":scope["release"]["id"],
        "scope_version":scope["scope_version"],
        "change_type":"DATA_BUNDLE_IMPORT",
        "notes":f"Imported from {bundle_dir.relative_to(ROOT)}"
    })
    write(DATA/"release_scope_log.json",scope_log)

    print("Applied bundle to canonical data")
    print("Next: python tools/run_uat_checks.py")

def main():
    p=argparse.ArgumentParser(description="Validate or import a v0.7 Release Data Bundle.")
    p.add_argument("bundle_dir")
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",action="store_true")
    mode.add_argument("--apply",action="store_true")
    a=p.parse_args()
    path=(ROOT/a.bundle_dir).resolve()
    if not path.is_dir() or not (path/"bundle.json").exists():
        raise SystemExit(f"Invalid bundle directory: {path}")
    try:
        apply_bundle(path,a.dry_run)
    except (AssertionError,KeyError,ValueError) as e:
        print(f"ERROR: {e}",file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":
    main()
