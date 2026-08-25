from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def manual_ids_from_scope(scope):
    return {
        feature["manual_test_id"]
        for item in scope.get("scope", {}).get("release_items", [])
        for feature in item.get("features", [])
    }


def prune_performance(performance, stream_id, release_id, keep_builds):
    if performance.get("schema_version") == "ng-performance-0.6":
        executions = [
            x for x in performance.get("executions", [])
            if x["stream_id"] == stream_id
            and x["release_id"] == release_id
            and x["build"] in keep_builds
        ]
        keep_test_ids = {x["performance_test_id"] for x in executions}
        definitions = [
            x for x in performance.get("definitions", [])
            if x["performance_test_id"] in keep_test_ids
        ]
        return {**performance, "definitions": definitions, "executions": executions}
    return {
        **performance,
        "results": [
            x for x in performance.get("results", [])
            if x["stream_id"] == stream_id
            and x["release_id"] == release_id
            and x["build"] in keep_builds
        ],
    }


def build_pruned_state(registry, definitions, executions, performance, keep_scope):
    stream_id = keep_scope["stream"]["id"]
    release_id = keep_scope["release"]["id"]
    keep_builds = set(keep_scope["release"]["builds"])
    keep_manual_ids = manual_ids_from_scope(keep_scope)

    source_stream = next((s for s in registry["streams"] if s["id"] == stream_id), None)
    if source_stream is None:
        raise AssertionError(f"Release Stream is not published: {stream_id}")
    source_release = next((r for r in source_stream["releases"] if r["id"] == release_id), None)
    if source_release is None:
        raise AssertionError(f"Release is not published: {release_id}")

    pruned_registry = {
        **registry,
        "streams": [
            {
                "id": stream_id,
                "name": keep_scope["stream"]["name"],
                "releases": [
                    {
                        "id": release_id,
                        "name": keep_scope["release"]["name"],
                        "manifest": source_release["manifest"],
                    }
                ],
            }
        ],
    }

    pruned_definitions = {
        **definitions,
        "definitions": [
            x for x in definitions["definitions"] if x["manual_test_id"] in keep_manual_ids
        ],
    }
    pruned_executions = {
        **executions,
        "executions": [
            x
            for x in executions["executions"]
            if x["stream_id"] == stream_id
            and x["release_id"] == release_id
            and x["manual_test_id"] in keep_manual_ids
            and x["build"] in keep_builds
        ],
    }
    pruned_performance = prune_performance(
        performance, stream_id, release_id, keep_builds
    )
    return pruned_registry, pruned_definitions, pruned_executions, pruned_performance


def obsolete_manifests(registry, keep_manifest):
    paths = []
    for stream in registry["streams"]:
        for release in stream["releases"]:
            manifest = release["manifest"]
            if manifest != keep_manifest:
                paths.append(ROOT / manifest)
    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Remove all published Release data except the Release represented by one bundle."
    )
    parser.add_argument("bundle_dir")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    bundle_dir = (ROOT / args.bundle_dir).resolve()
    if not bundle_dir.is_dir() or not (bundle_dir / "bundle.json").exists():
        raise SystemExit(f"Invalid bundle directory: {bundle_dir}")

    bundle = load(bundle_dir / "bundle.json")
    scope_name = bundle.get("release_scope")
    if not scope_name:
        raise SystemExit("Bundle does not reference release_scope")
    keep_scope = load(bundle_dir / scope_name)

    registry = load(DATA / "release_registry.json")
    definitions = load(DATA / "manual_test_definitions.json")
    executions = load(DATA / "manual_executions.json")
    performance = load(DATA / "performance_results.json")

    try:
        pruned = build_pruned_state(
            registry, definitions, executions, performance, keep_scope
        )
    except AssertionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

    pruned_registry, pruned_definitions, pruned_executions, pruned_performance = pruned
    keep_manifest = pruned_registry["streams"][0]["releases"][0]["manifest"]
    obsolete = obsolete_manifests(registry, keep_manifest)

    print("Release cleanup validation passed")
    print(f"  keep stream: {keep_scope['stream']['name']}")
    print(f"  keep release: {keep_scope['release']['name']}")
    print(f"  keep builds: {', '.join(keep_scope['release']['builds'])}")
    print(f"  keep release items: {len(keep_scope['scope']['release_items'])}")
    print(f"  keep Manual definitions: {len(pruned_definitions['definitions'])}")
    print(f"  keep Manual executions: {len(pruned_executions['executions'])}")
    if pruned_performance.get("schema_version") == "ng-performance-0.6":
        print(f"  keep Performance definitions: {len(pruned_performance.get('definitions', []))}")
        print(f"  keep Performance executions: {len(pruned_performance.get('executions', []))}")
    else:
        print(f"  keep Performance results: {len(pruned_performance.get('results', []))}")
    print(f"  remove release manifests: {len(obsolete)}")

    if args.dry_run:
        print("DRY RUN: canonical data was not changed")
        return

    write(DATA / "release_registry.json", pruned_registry)
    write(DATA / "manual_test_definitions.json", pruned_definitions)
    write(DATA / "manual_executions.json", pruned_executions)
    write(DATA / "performance_results.json", pruned_performance)

    for path in obsolete:
        if path.exists():
            path.unlink()
            print(f"Removed: {path.relative_to(ROOT)}")

    subprocess.run([sys.executable, "tools/build_release_snapshot.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "tools/validate_release_data.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "tools/validate_uat_candidate.py"], cwd=ROOT, check=True)
    print("Applied cleanup and rebuilt dashboard snapshot")
    print("Next: python tools/run_uat_checks.py")


if __name__ == "__main__":
    main()
