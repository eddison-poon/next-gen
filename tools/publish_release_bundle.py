from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
    print("$"," ".join(str(x) for x in cmd))
    subprocess.run(cmd,cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser(description="Validate or publish one Release Data Bundle using the v0.8 UAT workflow.")
    p.add_argument("bundle_dir")
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",action="store_true")
    mode.add_argument("--apply",action="store_true")
    a=p.parse_args()

    bundle=Path(a.bundle_dir)
    run([sys.executable,"tools/import_data_bundle.py",str(bundle),"--dry-run"])
    if a.dry_run:
        print("Bundle is ready to publish. Canonical data was not changed.")
        return

    run([sys.executable,"tools/import_data_bundle.py",str(bundle),"--apply"])
    run([sys.executable,"tools/run_uat_checks.py"])
    print("Bundle published and UAT checks passed")

if __name__=="__main__": main()
