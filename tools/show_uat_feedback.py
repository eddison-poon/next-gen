from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description="Show concise Team UAT feedback summary.")
    p.add_argument("feedback_file",nargs="?",default="input/uat_feedback.json")
    a=p.parse_args()
    path=(ROOT/a.feedback_file).resolve()
    if not path.is_file():
        print("No Team UAT findings recorded.")
        return
    findings=json.loads(path.read_text(encoding="utf-8")).get("findings",[])
    open_rows=[x for x in findings if x.get("status","OPEN")=="OPEN"]
    closed_rows=[x for x in findings if x.get("status")=="CLOSED"]
    print(f"Team UAT findings: {len(findings)} | open: {len(open_rows)} | closed: {len(closed_rows)}")
    if not findings: return
    sev=Counter(x.get("severity","UNKNOWN") for x in open_rows)
    typ=Counter(x.get("type","UNKNOWN") for x in open_rows)
    print("Open by severity: "+" | ".join(f"{k}={sev.get(k,0)}" for k in ["BLOCKER","HIGH","MEDIUM","LOW"]))
    print("Open by type: "+(" | ".join(f"{k}={v}" for k,v in sorted(typ.items())) if typ else "None"))
    if open_rows:
        print("\nOpen findings:")
        for x in open_rows:
            context=" / ".join(v for v in [x.get("stream",""),x.get("release",""),x.get("build","")] if v)
            suffix=f" | {context}" if context else ""
            print(f"  {x['id']} | {x['severity']} | {x['type']} | {x.get('tab','GENERAL')} | {x['summary']}{suffix}")
    if closed_rows:
        print("\nRecently closed:")
        for x in closed_rows[-5:]:
            retest=x.get("resolution",{}).get("retest_result","")
            print(f"  {x['id']} | {x['severity']} | {x['summary']} | retest={retest}")

if __name__=="__main__":
    main()
