from __future__ import annotations
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

recorder=load_module(ROOT/"tools/record_manual_execution.py","record_manual_execution")

def write(path,payload): path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")

def make_bundle(tmp):
    rel=Path(tmp).relative_to(ROOT)/"bundle"
    subprocess.run([
        sys.executable,"tools/create_release_bundle.py",
        "--stream-id","operator-test","--stream-name","Operator Test",
        "--release-id","operator-1.0","--release-name","Release 1.0",
        "--build","1.0.1","--output",str(rel)
    ],cwd=ROOT,check=True)
    b=ROOT/rel
    scope=json.loads((b/"release_scope.json").read_text(encoding="utf-8"))
    scope["scope"]["release_items"]=[{
        "jira_key":"TEST-1","summary":"Operator workflow","issue_type":"Story","jira_url":"#",
        "features":[{"id":"F-TEST-1","name":"Feature","scenario_id":"SC-TEST-1","manual_test_id":"M-TEST-1","applicable_environments":["SIT","UAT"]}]
    }]
    write(b/"release_scope.json",scope)
    defs=json.loads((b/"manual_test_definitions.json").read_text(encoding="utf-8"))
    defs["definitions"]=[{"manual_test_id":"M-TEST-1","scenario_id":"SC-TEST-1","title":"Verify workflow","jira_key":"TEST-1"}]
    write(b/"manual_test_definitions.json",defs)
    return b

def test_execution_recorder_adds_valid_row():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        b=make_bundle(tmp)
        row=recorder.add_execution(b,"M-TEST-1","SIT","PASSED","TEST-SIT-001","2026-08-19T10:00:00+08:00")
        assert row["stream_id"]=="operator-test"
        assert row["release_id"]=="operator-1.0"
        assert row["build"]=="1.0.1"
        payload=json.loads((b/"manual_executions.json").read_text(encoding="utf-8"))
        assert payload["executions"][0]["environment"]=="SIT"

def test_execution_recorder_rejects_non_applicable_environment():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        b=make_bundle(tmp)
        try:
            recorder.add_execution(b,"M-TEST-1","PROD","PASSED","TEST-PROD-001","2026-08-19T10:00:00+08:00")
        except AssertionError as e:
            assert "not applicable" in str(e)
        else:
            raise AssertionError("non-applicable environment was accepted")

def test_execution_recorder_rejects_duplicate_id():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        b=make_bundle(tmp)
        recorder.add_execution(b,"M-TEST-1","SIT","PASSED","DUP-001","2026-08-19T10:00:00+08:00")
        try:
            recorder.add_execution(b,"M-TEST-1","UAT","PASSED","DUP-001","2026-08-19T11:00:00+08:00")
        except AssertionError as e:
            assert "duplicate execution ID" in str(e)
        else:
            raise AssertionError("duplicate execution ID was accepted")
