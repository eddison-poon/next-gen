from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def digest(path:Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_template_bundle_dry_run_is_non_destructive():
    canonical=[
        ROOT/"data/release_registry.json",
        ROOT/"data/manual_test_definitions.json",
        ROOT/"data/manual_executions.json",
        ROOT/"data/automation_regression.json",
        ROOT/"data/performance_results.json",
    ]
    before={p:digest(p) for p in canonical}
    subprocess.run([sys.executable,"tools/import_data_bundle.py","input/release_bundle_template","--dry-run"],cwd=ROOT,check=True)
    after={p:digest(p) for p in canonical}
    assert before==after

def test_bundle_creator_generates_expected_context():
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        rel=Path(tmp).relative_to(ROOT)/"bundle"
        subprocess.run([
            sys.executable,"tools/create_release_bundle.py",
            "--stream-id","test-stream","--stream-name","Test Stream",
            "--release-id","test-1.0","--release-name","Release 1.0",
            "--build","1.0.1","--output",str(rel)
        ],cwd=ROOT,check=True)
        scope=json.loads((ROOT/rel/"release_scope.json").read_text(encoding="utf-8"))
        assert scope["stream"]["id"]=="test-stream"
        assert scope["release"]["id"]=="test-1.0"
        assert scope["release"]["current_build"]=="1.0.1"
