from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENTS = {"PASSED", "FAILED", "BLOCKED"}
PERFORMANCE_SCHEMA = "ng-performance-0.6"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def bundle_paths(bundle_dir: Path):
    bundle = load(bundle_dir / "bundle.json")
    return bundle, bundle_dir / bundle["release_scope"], bundle_dir / bundle["performance_results"]


def require(mapping: dict, key: str, where: str):
    assert key in mapping and mapping[key] not in (None, ""), f"missing {where}.{key}"
    return mapping[key]


def validate_hardware(items):
    assert isinstance(items, list), "hardware_utilization must be a list"
    for index, item in enumerate(items, start=1):
        assert isinstance(item, dict), f"hardware_utilization[{index}] must be an object"
        require(item, "component", f"hardware_utilization[{index}]")
        metrics = require(item, "metrics", f"hardware_utilization[{index}]")
        assert isinstance(metrics, dict) and metrics, f"hardware_utilization[{index}].metrics must be a non-empty object"


def normalize_sample(sample: dict):
    definition = require(sample, "definition", "sample")
    execution = require(sample, "execution", "sample")
    assert isinstance(definition, dict), "sample.definition must be an object"
    assert isinstance(execution, dict), "sample.execution must be an object"

    for key in ("performance_test_id", "performance_scenario_id", "jira_key", "title", "objective"):
        require(definition, key, "definition")

    for key in (
        "performance_execution_id", "performance_test_id", "stream_id", "release_id", "build",
        "executed_at", "executed_by", "assessment", "workload", "results", "environment"
    ):
        require(execution, key, "execution")

    assert str(execution["performance_test_id"]) == str(definition["performance_test_id"]), \
        "definition/execution performance_test_id mismatch"

    execution["assessment"] = str(execution["assessment"]).upper()
    assert execution["assessment"] in ASSESSMENTS, f"invalid assessment: {execution['assessment']}"

    workload = execution["workload"]
    results = execution["results"]
    environment = execution["environment"]
    assert isinstance(workload, dict), "execution.workload must be an object"
    assert isinstance(results, dict), "execution.results must be an object"
    assert isinstance(environment, dict), "execution.environment must be an object"

    require(workload, "concurrent_users", "execution.workload")
    target = workload.get("target_transactions", results.get("target_transactions"))
    assert target is not None, "missing target_transactions in workload/results"
    workload["target_transactions"] = int(target)
    require(workload, "duration", "execution.workload")

    attempted = int(require(results, "attempted_transactions", "execution.results"))
    passed = int(require(results, "passed_transactions", "execution.results"))
    failed = int(require(results, "failed_transactions", "execution.results"))
    assert attempted >= 0 and passed >= 0 and failed >= 0, "transaction counts cannot be negative"
    assert passed + failed == attempted, \
        f"transaction counts do not reconcile: passed({passed}) + failed({failed}) != attempted({attempted})"

    results["attempted_transactions"] = attempted
    results["passed_transactions"] = passed
    results["failed_transactions"] = failed
    results["transaction_pass_rate_percent"] = round((passed / attempted * 100) if attempted else 0.0, 2)
    results["transaction_failure_rate_percent"] = round((failed / attempted * 100) if attempted else 0.0, 2)
    require(results, "p95_completion", "execution.results")

    require(environment, "name", "execution.environment")
    require(environment, "tenant", "execution.environment")
    require(environment, "task_type", "execution.environment")

    hardware = execution.setdefault("hardware_utilization", [])
    validate_hardware(hardware)
    execution.setdefault("notes", "")
    return definition, execution


def upgrade_payload(payload: dict):
    if payload.get("schema_version") != PERFORMANCE_SCHEMA:
        payload["schema_version"] = PERFORMANCE_SCHEMA
    payload.pop("results", None)
    payload.setdefault("definitions", [])
    payload.setdefault("executions", [])
    return payload


def record(bundle_dir: Path, sample_path: Path):
    _, scope_path, perf_path = bundle_paths(bundle_dir)
    scope = load(scope_path)
    payload = upgrade_payload(load(perf_path))
    sample = load(sample_path)
    definition, execution = normalize_sample(sample)

    stream = scope["stream"]
    release = scope["release"]
    assert execution["stream_id"] == stream["id"], \
        f"stream mismatch: sample={execution['stream_id']} bundle={stream['id']}"
    assert execution["release_id"] == release["id"], \
        f"release mismatch: sample={execution['release_id']} bundle={release['id']}"
    assert str(execution["build"]) == str(release["current_build"]), \
        f"build mismatch: sample={execution['build']} bundle={release['current_build']}"

    definitions = payload["definitions"]
    executions = payload["executions"]
    test_id = str(definition["performance_test_id"])

    existing_definition = next((d for d in definitions if str(d.get("performance_test_id")) == test_id), None)
    if existing_definition is None:
        definitions.append(definition)
    else:
        assert existing_definition == definition, \
            f"Performance Test {test_id} already exists with a different definition"

    execution_id = execution["performance_execution_id"]
    assert all(x.get("performance_execution_id") != execution_id for x in executions), \
        f"duplicate performance execution ID in bundle: {execution_id}"
    executions.append(execution)
    write(perf_path, payload)
    return definition, execution


def main():
    parser = argparse.ArgumentParser(description="Safely append a Performance Test definition/execution to a Release Data Bundle.")
    parser.add_argument("bundle_dir")
    parser.add_argument("execution_json")
    args = parser.parse_args()

    bundle_dir = resolve(ROOT, args.bundle_dir)
    sample_path = resolve(ROOT, args.execution_json)
    try:
        definition, execution = record(bundle_dir, sample_path)
    except (AssertionError, KeyError, TypeError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: {exc}")

    results = execution["results"]
    print("Performance execution recorded")
    print(f"  performance_test_id: {definition['performance_test_id']}")
    print(f"  execution_id: {execution['performance_execution_id']}")
    print(f"  assessment: {execution['assessment']}")
    print(f"  attempted: {results['attempted_transactions']}")
    print(f"  passed: {results['passed_transactions']}")
    print(f"  failed: {results['failed_transactions']}")
    print(f"  pass_rate: {results['transaction_pass_rate_percent']:.2f}%")
    print(f"  failure_rate: {results['transaction_failure_rate_percent']:.2f}%")
    print(f"  performance_schema: {PERFORMANCE_SCHEMA}")
    print("Next: python tools/publish_release_bundle.py <bundle_dir> --dry-run")


if __name__ == "__main__":
    main()
