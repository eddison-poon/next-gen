from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(cmd, label):
    print(f"\n== {label} ==")
    print("$", " ".join(str(x) for x in cmd))
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"ERROR: {label} failed with exit code {e.returncode}")


def main():
    p=argparse.ArgumentParser(description="Run the v0.8 internal-UAT operator preflight checks.")
    p.add_argument("--bundle", help="Optional Release Data Bundle to validate, e.g. input/runtime-2.9")
    p.add_argument("--automation-file", default="input/automation_regression.json", help="Automation operator workspace to validate if present")
    p.add_argument("--skip-automation", action="store_true", help="Skip automation workspace validation")
    a=p.parse_args()

    if a.bundle:
        bundle=(ROOT/a.bundle).resolve()
        if not bundle.is_dir() or not (bundle/"bundle.json").is_file():
            raise SystemExit(f"ERROR: Release Data Bundle not found or incomplete: {bundle}")
        run([sys.executable,"tools/publish_release_bundle.py",a.bundle,"--dry-run"],"Release bundle dry-run")

    if not a.skip_automation:
        auto=(ROOT/a.automation_file).resolve()
        if auto.is_file():
            run([sys.executable,"tools/publish_automation_status.py",a.automation_file,"--dry-run"],"Automation workspace dry-run")
        else:
            print(f"\nINFO: automation workspace not found; skipped: {auto}")

    run([sys.executable,"tools/run_uat_checks.py"],"Repository UAT checks")
    print("\nINTERNAL UAT PREFLIGHT PASSED")
    if a.bundle:
        print(f"  release bundle: {a.bundle}")
    if not a.skip_automation:
        print(f"  automation workspace: {a.automation_file}")
    print("Safe to continue operator testing / publishing.")


if __name__=="__main__":
    main()
