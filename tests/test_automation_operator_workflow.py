from __future__ import annotations
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANONICAL=ROOT/"data/automation_regression.json"


def digest(path:Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scenario(payload,test_id):
    for capability in payload["capabilities"]:
        for feature in capability["features"]:
            for item in feature["scenarios"]:
                if item["automation_test_id"]==test_id:
                    return item
    raise AssertionError(f"test not found: {test_id}")


def temp_workspace(tmp):
    path=Path(tmp)/"automation_regression.json"
    shutil.copyfile(CANONICAL,path)
    return path


def test_automation_recorder_updates_only_target_gate():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        path=temp_workspace(tmp)
        before=json.loads(path.read_text(encoding="utf-8"))
        target_before=scenario(before,"MCP-JIRA-A-002")["results"].copy()
        other_before=scenario(before,"MCP-JIRA-A-003")["results"].copy()
        rel=path.relative_to(ROOT)
        subprocess.run([
            sys.executable,"tools/record_automation_result.py",str(rel),
            "--automation-test-id","MCP-JIRA-A-002","--environment","UAT","--status","PASSED"
        ],cwd=ROOT,check=True)
        after=json.loads(path.read_text(encoding="utf-8"))
        target_after=scenario(after,"MCP-JIRA-A-002")["results"]
        other_after=scenario(after,"MCP-JIRA-A-003")["results"]
        assert target_after["UAT"]=="PASSED"
        for env,value in target_before.items():
            if env!="UAT": assert target_after[env]==value
        assert other_after==other_before


def test_automation_recorder_rejects_na_environment():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        path=temp_workspace(tmp)
        before=digest(path)
        rel=path.relative_to(ROOT)
        p=subprocess.run([
            sys.executable,"tools/record_automation_result.py",str(rel),
            "--automation-test-id","MCP-JIRA-A-004","--environment","PPD","--status","PASSED"
        ],cwd=ROOT,text=True,capture_output=True)
        assert p.returncode!=0
        assert "N/A" in (p.stdout+p.stderr)
        assert digest(path)==before


def test_automation_publish_dry_run_is_non_destructive():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        path=temp_workspace(tmp)
        rel=path.relative_to(ROOT)
        before=digest(CANONICAL)
        subprocess.run([sys.executable,"tools/publish_automation_status.py",str(rel),"--dry-run"],cwd=ROOT,check=True)
        assert digest(CANONICAL)==before
