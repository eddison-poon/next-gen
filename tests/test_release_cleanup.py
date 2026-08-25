from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cleanup", ROOT / "tools/prune_to_release_bundle.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def test_prune_keeps_only_selected_release_data():
    registry = {
        "schema_version": "ng-release-registry-0.4",
        "generated_at": "2026-08-25T10:00:00+08:00",
        "streams": [
            {"id": "old-stream", "name": "Old Stream", "releases": [{"id": "old-1.0", "name": "Old 1.0", "manifest": "data/releases/old-stream/old-1.0.json"}]},
            {"id": "tenant-runtime", "name": "Tenant Based Runtime", "releases": [{"id": "sandbox-1.0.5", "name": "AgentHub Sandbox v1.0.5", "manifest": "data/releases/tenant-runtime/sandbox-1.0.5.json"}]},
        ],
    }
    definitions = {
        "schema_version": "ng-manual-definition-index-0.2",
        "definitions": [
            {"manual_test_id": "M-OLD", "scenario_id": "SC-OLD", "title": "Old", "jira_key": "OLD-1"},
            {"manual_test_id": "M-KEEP", "scenario_id": "SC-KEEP", "title": "Keep", "jira_key": "NEW-1"},
        ],
    }
    executions = {
        "schema_version": "ng-manual-execution-0.2",
        "executions": [
            {"execution_id": "OLD-EXE", "manual_test_id": "M-OLD", "stream_id": "old-stream", "release_id": "old-1.0", "build": "1.0.0", "environment": "SIT", "status": "PASSED", "executed_at": "2026-08-25T10:00:00+08:00"},
            {"execution_id": "KEEP-EXE", "manual_test_id": "M-KEEP", "stream_id": "tenant-runtime", "release_id": "sandbox-1.0.5", "build": "1.0.5", "environment": "UAT", "status": "PASSED", "executed_at": "2026-08-25T10:01:00+08:00"},
        ],
    }
    performance = {
        "schema_version": "ng-performance-0.6",
        "definitions": [
            {"performance_test_id": "PT-OLD", "performance_scenario_id": "PS-OLD", "jira_key": "OLD-PERF", "title": "Old perf", "objective": "Old"},
            {"performance_test_id": "PT-KEEP", "performance_scenario_id": "PS-KEEP", "jira_key": "NEW-PERF", "title": "Keep perf", "objective": "Keep"},
        ],
        "executions": [
            {"performance_execution_id": "OLD-PERF-EXE", "performance_test_id": "PT-OLD", "stream_id": "old-stream", "release_id": "old-1.0", "build": "1.0.0"},
            {"performance_execution_id": "KEEP-PERF-EXE", "performance_test_id": "PT-KEEP", "stream_id": "tenant-runtime", "release_id": "sandbox-1.0.5", "build": "1.0.5"},
        ],
    }
    scope = {
        "stream": {"id": "tenant-runtime", "name": "Tenant Based Runtime"},
        "release": {"id": "sandbox-1.0.5", "name": "AgentHub Sandbox v1.0.5", "builds": ["1.0.5"]},
        "scope": {"release_items": [{"jira_key": "NEW-1", "features": [{"manual_test_id": "M-KEEP"}]}]},
    }

    r, d, e, p = cleanup.build_pruned_state(registry, definitions, executions, performance, scope)
    assert [x["id"] for x in r["streams"]] == ["tenant-runtime"]
    assert [x["id"] for x in r["streams"][0]["releases"]] == ["sandbox-1.0.5"]
    assert [x["manual_test_id"] for x in d["definitions"]] == ["M-KEEP"]
    assert [x["execution_id"] for x in e["executions"]] == ["KEEP-EXE"]
    assert [x["performance_test_id"] for x in p["definitions"]] == ["PT-KEEP"]
    assert [x["performance_execution_id"] for x in p["executions"]] == ["KEEP-PERF-EXE"]
