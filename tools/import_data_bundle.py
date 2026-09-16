from __future__ import annotations
import argparse, copy, json, sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"
ENVIRONMENTS={"DEV","SIT","UAT","PPD","PROD"}; MANUAL_STATUS={"PASSED","FAILED","BLOCKED"}

def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def write(path:Path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
def require_bundle_file(bundle_dir,bundle,key):
    name=bundle.get(key)
    if not name:return None
    path=bundle_dir/name
    if not path.exists():raise AssertionError(f"bundle references missing file: {name}")
    return path

def validate_definitions(definitions):
    ids=set(); jira=set()
    for d in definitions:
        for key in ("manual_test_id","title","priority","jira_key","jira_url"):
            assert d.get(key),f"Manual Test Definition missing {key}: {d.get('manual_test_id','unknown')}"
        assert d["manual_test_id"] not in ids,f"duplicate Manual Test Definition: {d['manual_test_id']}"; ids.add(d["manual_test_id"])
        assert d["jira_key"] not in jira,f"duplicate MTD Jira: {d['jira_key']}"; jira.add(d["jira_key"])
        scenarios=d.get("scenario_ids") or ([d["scenario_id"]] if d.get("scenario_id") else [])
        assert scenarios,f"MTD has no Business Scenario traceability: {d['manual_test_id']}"
        assert len(scenarios)==len(set(scenarios)),f"duplicate scenario reference: {d['manual_test_id']}"

def validate_scope(scope,defs_by_id):
    assert scope["schema_version"] in {"ng-release-scope-0.4","ng-release-scope-0.8"}
    assert scope["release"]["current_build"] in scope["release"]["builds"]
    parent_jira=set(); variants=set(); variant_jira=set()
    for item in scope["scope"]["release_items"]:
        assert item["jira_key"] not in parent_jira,f"duplicate MTD Jira Release Item: {item['jira_key']}"; parent_jira.add(item["jira_key"])
        assert item["features"],f"MTD has no execution variants: {item['jira_key']}"
        mtd_ids={f["manual_test_id"] for f in item["features"]}
        assert len(mtd_ids)==1,f"Release Item must represent one MTD: {item['jira_key']}"
        mtd_id=next(iter(mtd_ids)); assert mtd_id in defs_by_id,f"missing Manual Test Definition: {mtd_id}"
        d=defs_by_id[mtd_id]; assert d["jira_key"]==item["jira_key"],f"MTD Jira mismatch: {mtd_id}"
        for f in item["features"]:
            assert f["id"] not in variants,f"duplicate execution variant: {f['id']}"; variants.add(f["id"])
            for key in ("name","jira_key","jira_url"):
                assert f.get(key),f"execution variant missing {key}: {f['id']}"
            assert f["jira_key"] not in variant_jira,f"duplicate execution variant Jira: {f['jira_key']}"; variant_jira.add(f["jira_key"])
            envs=f["applicable_environments"]; assert envs,f"no applicable environments: {f['id']}"; assert len(envs)==len(set(envs)); assert set(envs)<=ENVIRONMENTS

def merge_by_id(existing,incoming,key):
    result={x[key]:copy.deepcopy(x) for x in existing}
    for x in incoming:result[x[key]]=copy.deepcopy(x)
    return list(result.values())

def validate_execution_rows(rows,defs_by_id,scope):
    builds=set(scope["release"]["builds"]); sid=scope["stream"]["id"]; rid=scope["release"]["id"]
    variant_to_mtd={f["id"]:f["manual_test_id"] for item in scope["scope"]["release_items"] for f in item["features"]}; ids=set()
    for x in rows:
        assert x["execution_id"] not in ids,f"duplicate execution ID in bundle: {x['execution_id']}"; ids.add(x["execution_id"])
        vid=x.get("execution_variant_id")
        if vid:
            assert vid in variant_to_mtd,f"execution references unknown variant: {vid}"
            assert x["manual_test_id"]==variant_to_mtd[vid],f"execution variant/MTD mismatch: {x['execution_id']}"
        assert x["manual_test_id"] in defs_by_id
        assert x["stream_id"]==sid and x["release_id"]==rid; assert x["build"] in builds; assert x["environment"] in ENVIRONMENTS; assert x["status"] in MANUAL_STATUS; datetime.fromisoformat(x["executed_at"])

def apply_bundle(bundle_dir:Path,dry_run:bool):
    bundle=load(bundle_dir/"bundle.json"); assert bundle["schema_version"] in {"ng-release-data-bundle-0.7","ng-release-data-bundle-0.8"}
    scope=load(require_bundle_file(bundle_dir,bundle,"release_scope")); incoming_defs=load(require_bundle_file(bundle_dir,bundle,"manual_test_definitions")).get("definitions",[]); incoming_exec=load(require_bundle_file(bundle_dir,bundle,"manual_executions")).get("executions",[])
    current_defs=load(DATA/"manual_test_definitions.json"); merged_defs=merge_by_id(current_defs["definitions"],incoming_defs,"manual_test_id"); validate_definitions(merged_defs); defs_by_id={x["manual_test_id"]:x for x in merged_defs}; validate_scope(scope,defs_by_id); validate_execution_rows(incoming_exec,defs_by_id,scope)
    registry=load(DATA/"release_registry.json"); stream=next((s for s in registry["streams"] if s["id"]==scope["stream"]["id"]),None); manifest_rel=f"data/releases/{scope['stream']['id']}/{scope['release']['id']}.json"
    if stream is None:stream={"id":scope["stream"]["id"],"name":scope["stream"]["name"],"releases":[]}; registry["streams"].append(stream)
    release_ref=next((r for r in stream["releases"] if r["id"]==scope["release"]["id"]),None)
    if release_ref is None:stream["releases"].append({"id":scope["release"]["id"],"name":scope["release"]["name"],"manifest":manifest_rel})
    else:release_ref.update({"name":scope["release"]["name"],"manifest":manifest_rel})
    current_exec=load(DATA/"manual_executions.json"); merged_exec=merge_by_id(current_exec["executions"],incoming_exec,"execution_id")
    print("v0.8 Release Data Bundle validation passed"); print(f"  MTDs: {len(incoming_defs)}"); print(f"  execution results: {len(incoming_exec)}")
    if dry_run:print("DRY RUN: canonical data was not changed"); return
    write(DATA/"release_registry.json",registry); write(ROOT/manifest_rel,scope); current_defs["schema_version"]="ng-manual-definition-index-0.8"; current_defs["definitions"]=merged_defs; write(DATA/"manual_test_definitions.json",current_defs); current_exec["schema_version"]="ng-manual-execution-index-0.8"; current_exec["executions"]=merged_exec; write(DATA/"manual_executions.json",current_exec); print("Applied v0.8 bundle to canonical data")

def main():
    p=argparse.ArgumentParser(description="Validate or import a v0.8 functional Release Data Bundle."); p.add_argument("bundle_dir"); mode=p.add_mutually_exclusive_group(required=True); mode.add_argument("--dry-run",action="store_true"); mode.add_argument("--apply",action="store_true"); a=p.parse_args(); path=(ROOT/a.bundle_dir).resolve()
    if not path.is_dir() or not (path/"bundle.json").exists():raise SystemExit(f"Invalid bundle directory: {path}")
    try:apply_bundle(path,a.dry_run)
    except (AssertionError,KeyError,ValueError) as e:print(f"ERROR: {e}",file=sys.stderr); raise SystemExit(1)
if __name__=="__main__":main()
