from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ENVIRONMENTS = {"DEV","SIT","UAT","PPD","PROD"}
EXEC_STATUSES = {"PASSED","FAILED","BLOCKED"}

def load_path(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load(name: str):
    return load_path(DATA / name)

def manifest_path(ref: str) -> Path:
    prefix = "data/"
    if not ref.startswith(prefix):
        raise AssertionError(f"manifest reference must start with data/: {ref}")
    return ROOT / ref

def main():
    registry = load("release_registry.json")
    defs = load("manual_test_definitions.json")
    execs = load("manual_executions.json")

    definition_by_id = {x["manual_test_id"]:x for x in defs["definitions"]}
    assert len(definition_by_id) == len(defs["definitions"]), "duplicate manual_test_id"

    release_ids=set()
    manifests=[]

    for stream in registry["streams"]:
        for r in stream["releases"]:
            path = manifest_path(r["manifest"])
            assert path.exists(), f"missing release manifest: {r['manifest']}"
            m = load_path(path)
            manifests.append(m)

            assert m["stream"]["id"] == stream["id"], f"stream mismatch in {r['manifest']}"
            assert m["release"]["id"] == r["id"], f"release mismatch in {r['manifest']}"
            assert m["release"]["name"] == r["name"], f"release name mismatch in {r['manifest']}"
            assert m["scope_version"] >= 1, f"invalid scope version in {r['manifest']}"
            assert m["release"]["current_build"] in m["release"]["builds"], f"current build missing in {r['manifest']}"

            rid=(stream["id"],r["id"])
            assert rid not in release_ids, f"duplicate release {rid}"
            release_ids.add(rid)

            # Feature and scenario identifiers are scoped to a release manifest.
            # Reusing the same logical feature/scenario in another release is valid;
            # duplicates within this release remain invalid.
            jira_keys=set()
            feature_ids=set()
            scenario_ids=set()
            for item in m["scope"]["release_items"]:
                assert item["jira_key"] not in jira_keys, f"duplicate release item {item['jira_key']} in {rid}"
                jira_keys.add(item["jira_key"])

                for f in item["features"]:
                    assert f["id"] not in feature_ids, f"duplicate feature {f['id']} in {rid}"
                    feature_ids.add(f["id"])
                    assert f["scenario_id"] not in scenario_ids, f"duplicate scenario {f['scenario_id']} in {rid}"
                    scenario_ids.add(f["scenario_id"])
                    assert f["manual_test_id"] in definition_by_id, f"missing definition {f['manual_test_id']}"
                    d=definition_by_id[f["manual_test_id"]]
                    assert d["scenario_id"]==f["scenario_id"], f"scenario mismatch for {f['manual_test_id']}"
                    assert d["jira_key"]==item["jira_key"], f"jira mismatch for {f['manual_test_id']}"
                    envs=f["applicable_environments"]
                    assert len(envs)==len(set(envs)), f"duplicate applicable environment in {f['id']}"
                    assert set(envs)<=ENVIRONMENTS, f"invalid applicable environment in {f['id']}"

    execution_ids=set()
    for x in execs["executions"]:
        assert x["execution_id"] not in execution_ids, f"duplicate execution {x['execution_id']}"
        execution_ids.add(x["execution_id"])
        assert x["manual_test_id"] in definition_by_id, f"execution references unknown test {x['manual_test_id']}"
        assert (x["stream_id"],x["release_id"]) in release_ids, f"execution references unknown release {x['release_id']}"
        assert x["environment"] in ENVIRONMENTS, f"invalid environment {x['environment']}"
        assert x["status"] in EXEC_STATUSES, f"invalid status {x['status']}"

    print("Release Focus v0.4 data validation passed")
    print(f"Streams: {len(registry['streams'])}")
    print(f"Releases / manifests: {len(manifests)}")
    print(f"Manual definitions: {len(definition_by_id)}")
    print(f"Manual executions: {len(execution_ids)}")

def validate_generated():
    target = ROOT/"data/generated/release_focus_snapshot.json"
    if not target.exists():
        return
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "ng-release-focus-snapshot-0.4"
    for snap in payload["snapshots"]:
        k = snap["kpis"]
        assert k["executed"] == k["passed"] + k["failed"] + k["blocked"]
        assert k["total_applicable_gates"] == k["executed"] + k["not_executed"]
    print(f"Generated snapshots validated: {len(payload['snapshots'])}")

if __name__=="__main__":
    main()
    validate_generated()
