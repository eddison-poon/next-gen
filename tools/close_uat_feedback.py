from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description="Close one Team UAT finding after resolution and retest, preserving history.")
    p.add_argument("finding_id")
    p.add_argument("--retested-by",required=True)
    p.add_argument("--retest-result",required=True,choices=["PASSED","FAILED"])
    p.add_argument("--resolution",required=True)
    p.add_argument("--fix-version",default="")
    p.add_argument("--notes",default="")
    p.add_argument("--feedback-file",default="input/uat_feedback.json")
    a=p.parse_args()

    path=(ROOT/a.feedback_file).resolve()
    if not path.is_file():
        raise SystemExit(f"Feedback file not found: {path}")
    payload=json.loads(path.read_text(encoding="utf-8"))
    findings=payload.get("findings",[])
    matches=[x for x in findings if x.get("id")==a.finding_id]
    if not matches:
        raise SystemExit(f"Finding not found: {a.finding_id}")
    if len(matches)>1:
        raise SystemExit(f"Duplicate finding ID: {a.finding_id}")

    finding=matches[0]
    if finding.get("status","OPEN")!="OPEN":
        raise SystemExit(f"Finding is already {finding.get('status')}: {a.finding_id}")
    if a.retest_result!="PASSED":
        raise SystemExit("Retest result is FAILED; finding remains OPEN. Close only after PASSED retest.")

    finding["status"]="CLOSED"
    finding["closed_at"]=datetime.now().astimezone().isoformat(timespec="seconds")
    finding["resolution"]={
        "summary":a.resolution,
        "fix_version":a.fix_version,
        "retested_by":a.retested_by,
        "retest_result":a.retest_result,
        "notes":a.notes,
    }
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Closed {a.finding_id}: {finding.get('summary','')}")
    print(f"  retest: {a.retest_result} by {a.retested_by}")
    if a.fix_version:
        print(f"  fix version: {a.fix_version}")

if __name__=="__main__":
    main()
