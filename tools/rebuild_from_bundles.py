from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_ROOT=ROOT/"input"
EXCLUDED_DIRS={"release_bundle_template"}

def discover_bundles(bundle_root:Path):
    bundles=[]
    if not bundle_root.exists():
        return bundles
    for path in sorted(bundle_root.iterdir(), key=lambda p:p.name.lower()):
        if not path.is_dir() or path.name in EXCLUDED_DIRS:
            continue
        if (path/"bundle.json").exists():
            bundles.append(path)
    return bundles

def main():
    p=argparse.ArgumentParser(description="Restore canonical dashboard data from durable v0.7 Release Data Bundles.")
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run",action="store_true",help="Validate every discovered bundle without changing canonical data.")
    mode.add_argument("--apply",action="store_true",help="Apply every discovered bundle, then rebuild the dashboard snapshot.")
    p.add_argument("--bundle-root",default="input",help="Directory containing Release Data Bundle subfolders. Default: input")
    a=p.parse_args()

    bundle_root=(ROOT/a.bundle_root).resolve()
    bundles=discover_bundles(bundle_root)
    if not bundles:
        raise SystemExit(f"No Release Data Bundles found under: {bundle_root}")

    print(f"Discovered Release Data Bundles: {len(bundles)}")
    for b in bundles:
        print(f"  - {b.relative_to(ROOT)}")

    mode_arg="--dry-run" if a.dry_run else "--apply"
    for b in bundles:
        rel=b.relative_to(ROOT)
        print(f"\n== {rel} ==")
        subprocess.run([sys.executable,"tools/import_data_bundle.py",str(rel),mode_arg],cwd=ROOT,check=True)

    if a.apply:
        print("\nRebuilding generated Release Focus snapshot...")
        subprocess.run([sys.executable,"tools/build_release_snapshot.py"],cwd=ROOT,check=True)
        print("Validating restored canonical data...")
        subprocess.run([sys.executable,"tools/validate_release_data.py"],cwd=ROOT,check=True)
        print("Canonical data restored from Release Data Bundles.")
    else:
        print("\nDRY RUN COMPLETE: all discovered bundles validated; canonical data was not changed.")

if __name__=="__main__":
    main()
