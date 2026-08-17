from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
ENVS={"DEV","SIT","UAT","PPD","PROD"}

def load(name): return json.loads((DATA/name).read_text(encoding="utf-8"))

def main():
    subprocess.run([sys.executable,"tools/validate_release_data.py"],cwd=ROOT,check=True)

    auto=load("automation_regression.json")
    caps=set()
    for c in auto["capabilities"]:
        assert c["id"] not in caps; caps.add(c["id"])
        for f in c["features"]:
            for s in f["scenarios"]:
                assert set(s["results"].keys())==ENVS
                assert set(s["applicable_environments"])<=ENVS
                for e in ENVS-set(s["applicable_environments"]):
                    assert s["results"][e]=="N/A"

    perf=load("performance_results.json")
    registry=load("release_registry.json")
    valid=set()
    for stream in registry["streams"]:
        for rr in stream["releases"]:
            m=json.loads((ROOT/rr["manifest"]).read_text(encoding="utf-8"))
            for b in m["release"]["builds"]:
                valid.add((stream["id"],rr["id"],b))

    for r in perf["results"]:
        assert (r["stream_id"],r["release_id"],r["build"]) in valid
        assert r["assessment"] in {"GREEN","AMBER","RED"}
        for m in r["metrics"]:
            assert m["status"] in {"PASSED","FAILED"}

    print("v0.5 UAT Candidate validation passed")
    print(f"Automation capabilities: {len(auto['capabilities'])}")
    print(f"Automation scenarios: {sum(len(f['scenarios']) for c in auto['capabilities'] for f in c['features'])}")
    print(f"Performance results: {len(perf['results'])}")

if __name__=="__main__":
    main()
