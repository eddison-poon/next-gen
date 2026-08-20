from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/automation_regression.json"

def load(path): return json.loads(path.read_text(encoding="utf-8"))

def make_workspace(tmp):
    p=Path(tmp)/"automation.json"
    p.write_text(SOURCE.read_text(encoding="utf-8"),encoding="utf-8")
    return p

def rel(path): return str(path.relative_to(ROOT))

def test_record_automation_result_updates_only_selected_gate():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        p=make_workspace(tmp); before=load(p)
        target=next(s for c in before["capabilities"] for f in c["features"] for s in f["scenarios"] if s["automation_test_id"]=="MCP-JIRA-A-002")
        old_ppd=target["results"]["PPD"]
        subprocess.run([sys.executable,"tools/record_automation_result.py",rel(p),"--automation-test-id","MCP-JIRA-A-002","--environment","UAT","--status","PASSED"],cwd=ROOT,check=True)
        after=load(p); target2=next(s for c in after["capabilities"] for f in c["features"] for s in f["scenarios"] if s["automation_test_id"]=="MCP-JIRA-A-002")
        assert target2["results"]["UAT"]=="PASSED"
        assert target2["results"]["PPD"]==old_ppd
        assert target2["results"]["PROD"]=="N/A"

def test_record_automation_result_rejects_na_environment():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        p=make_workspace(tmp)
        r=subprocess.run([sys.executable,"tools/record_automation_result.py",rel(p),"--automation-test-id","MCP-JIRA-A-004","--environment","PROD","--status","PASSED"],cwd=ROOT)
        assert r.returncode!=0

def test_automation_publish_dry_run_is_non_destructive():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        p=make_workspace(tmp)
        before=SOURCE.read_bytes()
        subprocess.run([sys.executable,"tools/publish_automation_status.py",rel(p),"--dry-run"],cwd=ROOT,check=True)
        assert SOURCE.read_bytes()==before
