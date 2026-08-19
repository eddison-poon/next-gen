from __future__ import annotations
import importlib.util, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
    print("$"," ".join(str(x) for x in cmd))
    subprocess.run(cmd,cwd=ROOT,check=True)

def load_tests(path:Path, name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [getattr(mod,n) for n in dir(mod) if n.startswith("test_") and callable(getattr(mod,n))]

run([sys.executable,"tools/build_release_snapshot.py"])
run([sys.executable,"tools/validate_release_data.py"])
run([sys.executable,"tools/validate_uat_candidate.py"])

tests=[]
tests += load_tests(ROOT/"tests/test_release_reporting.py","release_reporting_tests")
tests += load_tests(ROOT/"tests/test_data_onboarding.py","data_onboarding_tests")
tests += load_tests(ROOT/"tests/test_uat_operator_workflow.py","uat_operator_workflow_tests")

for test in tests:
    test()
    print("PASS",test.__name__)

print(f"UAT smoke/regression checks passed: {len(tests)} tests")
