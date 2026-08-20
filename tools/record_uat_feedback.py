from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEVERITIES={"BLOCKER","HIGH","MEDIUM","LOW"}
TYPES={"CALCULATION","DATA","WORKFLOW","VALIDATION","UI","DOCUMENTATION","OTHER"}
TABS={"RELEASE","AUTOMATION","PERFORMANCE","GENERAL"}


def main():
    p=argparse.ArgumentParser(description="Record one structured Team UAT finding without changing dashboard data.")
    p.add_argument("--summary",required=True)
    p.add_argument("--severity",required=True,choices=sorted(SEVERITIES))
    p.add_argument("--type",required=True,choices=sorted(TYPES))
    p.add_argument("--tab",default="GENERAL",choices=sorted(TABS))
    p.add_argument("--tester",default="")
    p.add_argument("--stream",default="")
    p.add_argument("--release",default="")
    p.add_argument("--build",default="")
    p.add_argument("--expected",default="")
    p.add_argument("--actual",default="")
    p.add_argument("--evidence",default="")
    p.add_argument("--impact",default="")
    p.add_argument("--workaround",default="")
    p.add_argument("--output",default="input/uat_feedback.json")
    a=p.parse_args()

    path=(ROOT/a.output).resolve()
    path.parent.mkdir(parents=True,exist_ok=True)
    payload={"findings":[]}
    if path.exists():
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload.get("findings"),list):
            raise SystemExit(f"Invalid feedback file: {path}")

    now=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    finding_id=f"UAT-{len(payload['findings'])+1:03d}"
    finding={
        "id":finding_id,"recorded_at":now,"status":"OPEN","tester":a.tester,
        "stream":a.stream,"release":a.release,"build":a.build,"tab":a.tab,
        "severity":a.severity,"type":a.type,"summary":a.summary,
        "expected":a.expected,"actual":a.actual,"evidence":a.evidence,
        "impact":a.impact,"workaround":a.workaround,
    }
    payload["findings"].append(finding)
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Recorded {finding_id}: {a.severity} | {a.type} | {a.summary}")
    print(f"Feedback file: {path.relative_to(ROOT)}")

if __name__=="__main__":
    main()
