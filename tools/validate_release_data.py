from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENTS = {"DEV","SIT","UAT","PPD","PROD"}
STATUSES = {"PASSED","FAILED","BLOCKED"}

def load(name):
    return json.loads((ROOT/"data"/name).read_text(encoding="utf-8"))

def main():
    manifest = load("release_manifest.json")
    defs = load("manual_test_definitions.json")
    execs = load("manual_executions.json")

    definition_by_id = {x["manual_test_id"]:x for x in defs["definitions"]}
    assert len(definition_by_id) == len(defs["definitions"]), "duplicate manual_test_id"

    release_ids=set()
    feature_ids=set()
    scenario_ids=set()

    for stream in manifest["streams"]:
        for release in stream["releases"]:
            rid=(stream["id"],release["id"])
            assert rid not in release_ids, f"duplicate release {rid}"
            release_ids.add(rid)
            assert release["current_build"] in release["builds"], f"current build missing from builds for {rid}"
            for item in release["scope"]["release_items"]:
                for f in item["features"]:
                    assert f["id"] not in feature_ids, f"duplicate feature {f['id']}"
                    feature_ids.add(f["id"])
                    assert f["scenario_id"] not in scenario_ids, f"duplicate scenario {f['scenario_id']}"
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
        assert x["status"] in STATUSES, f"invalid status {x['status']}"

    print("Release Focus v0.2 data validation passed")
    print(f"Streams: {len(manifest['streams'])}")
    print(f"Releases: {len(release_ids)}")
    print(f"Manual definitions: {len(definition_by_id)}")
    print(f"Manual executions: {len(execution_ids)}")

if __name__=="__main__":
    main()


def validate_generated():
    target = ROOT/"data/generated/release_focus_snapshot.json"
    if not target.exists():
        return
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "ng-release-focus-snapshot-0.3"
    for snap in payload["snapshots"]:
        k = snap["kpis"]
        assert k["executed"] == k["passed"] + k["failed"] + k["blocked"]
        assert k["total_applicable_gates"] == k["executed"] + k["not_executed"]
    print(f"Generated snapshots validated: {len(payload['snapshots'])}")

# Re-run generated validation when this module is invoked.
if __name__=="__main__":
    validate_generated()
