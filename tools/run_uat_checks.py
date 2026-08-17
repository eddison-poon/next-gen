
from __future__ import annotations
import importlib.util, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
    print("$"," ".join(str(x) for x in cmd))
    subprocess.run(cmd,cwd=ROOT,check=True)

run([sys.executable,"tools/build_release_snapshot.py"])
run([sys.executable,"tools/validate_release_data.py"])
run([sys.executable,"tools/validate_uat_candidate.py"])

spec=importlib.util.spec_from_file_location("tests",ROOT/"tests/test_release_reporting.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
tests=[getattr(mod,n) for n in dir(mod) if n.startswith("test_") and callable(getattr(mod,n))]
for test in tests:
    test()
    print("PASS",test.__name__)
print(f"UAT smoke/regression checks passed: {len(tests)} tests")
