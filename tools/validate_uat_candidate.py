from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
ENVS={"DEV","SIT","UAT","PPD","PROD"}
AUTO_STATUS={"PASSED","FAILED","BLOCKED","NOT_EXECUTED","N/A"}
PERF_ASSESSMENTS={"PASSED","FAILED","AMBER"}
PERF_METRIC_STATUS={"PASSED","FAILED","AMBER"}

def load(name): return json.loads((DATA/name).read_text(encoding="utf-8"))

def valid_release_builds():
    registry=load("release_registry.json")
    valid=set()
    for stream in registry["streams"]:
        for rr in stream["releases"]:
            m=json.loads((ROOT/rr["manifest"]).read_text(encoding="utf-8"))
            for b in m["release"]["builds"]:
                valid.add((stream["id"],rr["id"],b))
    return valid

def validate_performance(perf, valid):
    if perf.get("schema_version")=="ng-performance-0.6":
        definitions=perf.get("definitions",[])
        executions=perf.get("executions",[])
        def_ids=set(); scenario_ids=set()
        for d in definitions:
            assert d["performance_test_id"] not in def_ids; def_ids.add(d["performance_test_id"])
            assert d["performance_scenario_id"] not in scenario_ids; scenario_ids.add(d["performance_scenario_id"])
            assert d["jira_key"] and d["title"] and d["objective"]
        execution_ids=set()
        for r in executions:
            assert r["performance_execution_id"] not in execution_ids; execution_ids.add(r["performance_execution_id"])
            assert r["performance_test_id"] in def_ids
            assert (r["stream_id"],r["release_id"],r["build"]) in valid
            assert r["assessment"] in PERF_ASSESSMENTS
            assert r.get("executed_at")
            assert isinstance(r.get("workload",[]),list)
            assert isinstance(r.get("results",[]),list)
            assert isinstance(r.get("environment",{}),dict)
            assert isinstance(r.get("hardware_utilization",[]),list)
            for metric in r.get("results",[]):
                if metric.get("status") is not None:
                    assert metric["status"] in PERF_METRIC_STATUS
            for component in r.get("hardware_utilization",[]):
                assert component.get("component")
                assert isinstance(component.get("metrics",[]),list)
        return len(definitions),len(executions)

    # Backward compatibility for repositories not yet migrated from ng-performance-0.5.
    results=perf.get("results",[])
    run_ids=set()
    for r in results:
        assert r["test_run"] not in run_ids; run_ids.add(r["test_run"])
        assert (r["stream_id"],r["release_id"],r["build"]) in valid
        assert r["assessment"] in {"GREEN","AMBER","RED"}
        assert r["metrics"]
        for m in r["metrics"]:
            assert m["status"] in {"PASSED","FAILED"}
    return 0,len(results)

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
    perf_definitions,perf_executions=validate_performance(perf,valid_release_builds())

    print("v0.6 UAT Candidate validation passed")
    print(f"Automation capabilities: {len(cap_ids)}")
    print(f"Automation scenarios: {len(scenario_ids)}")
    print(f"Performance definitions: {perf_definitions}")
    print(f"Performance executions: {perf_executions}")

if __name__=="__main__":
    main()
