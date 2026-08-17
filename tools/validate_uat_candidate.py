
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
ENVS={"DEV","SIT","UAT","PPD","PROD"}
AUTO_STATUS={"PASSED","FAILED","BLOCKED","NOT_EXECUTED","N/A"}

def load(name): return json.loads((DATA/name).read_text(encoding="utf-8"))

def main():
    subprocess.run([sys.executable,"tools/validate_release_data.py"],cwd=ROOT,check=True)

    auto=load("automation_regression.json")
    cap_ids=set(); feature_ids=set(); scenario_ids=set(); test_ids=set()
    for c in auto["capabilities"]:
        assert c["id"] not in cap_ids; cap_ids.add(c["id"])
        for f in c["features"]:
            assert f["id"] not in feature_ids; feature_ids.add(f["id"])
            for s in f["scenarios"]:
                assert s["id"] not in scenario_ids; scenario_ids.add(s["id"])
                assert s["automation_test_id"] not in test_ids; test_ids.add(s["automation_test_id"])
                assert set(s["results"].keys())==ENVS
                assert set(s["results"].values())<=AUTO_STATUS
                assert set(s["applicable_environments"])<=ENVS
                for e in ENVS-set(s["applicable_environments"]):
                    assert s["results"][e]=="N/A"
                for e in set(s["applicable_environments"]):
                    assert s["results"][e]!="N/A"

    perf=load("performance_results.json")
    registry=load("release_registry.json")
    valid=set()
    for stream in registry["streams"]:
        for rr in stream["releases"]:
            m=json.loads((ROOT/rr["manifest"]).read_text(encoding="utf-8"))
            for b in m["release"]["builds"]:
                valid.add((stream["id"],rr["id"],b))
    run_ids=set()
    for r in perf["results"]:
        assert r["test_run"] not in run_ids; run_ids.add(r["test_run"])
        assert (r["stream_id"],r["release_id"],r["build"]) in valid
        assert r["assessment"] in {"GREEN","AMBER","RED"}
        assert r["metrics"]
        for m in r["metrics"]:
            assert m["status"] in {"PASSED","FAILED"}

    print("v0.6 UAT Candidate validation passed")
    print(f"Automation capabilities: {len(cap_ids)}")
    print(f"Automation scenarios: {len(scenario_ids)}")
    print(f"Performance results: {len(perf['results'])}")

if __name__=="__main__":
    main()
