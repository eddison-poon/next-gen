from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("builder", ROOT / "tools/build_release_snapshot.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def fixture_manifest():
    return {
        "schema_version": "ng-release-scope-0.4",
        "scope_version": 1,
        "effective_at": "2026-08-25T10:00:00+08:00",
        "stream": {"id": "fixture-stream", "name": "Fixture Stream"},
        "release": {
            "id": "fixture-1.0",
            "name": "Fixture 1.0",
            "builds": ["1.0.1"],
            "current_build": "1.0.1",
        },
        "scope": {
            "release_items": [
                {
                    "jira_key": "FIX-1",
                    "summary": "Fixture release item",
                    "issue_type": "Story",
                    "jira_url": "https://jira.example/browse/FIX-1",
                    "features": [
                        {
                            "id": "F-FIX-1",
                            "name": "Fixture feature one",
                            "scenario_id": "SC-FIX-1",
                            "manual_test_id": "M-FIX-1",
                            "applicable_environments": ["SIT", "UAT", "PPD"],
                        },
                        {
                            "id": "F-FIX-2",
                            "name": "Fixture feature two",
                            "scenario_id": "SC-FIX-2",
                            "manual_test_id": "M-FIX-2",
                            "applicable_environments": ["SIT", "UAT"],
                        },
                    ],
                }
            ]
        },
    }


def fixture_definitions():
    return [
        {
            "manual_test_id": "M-FIX-1",
            "scenario_id": "SC-FIX-1",
            "title": "Verify fixture one",
            "jira_key": "FIX-1",
            "test_jira_key": "TEST-101",
            "test_jira_url": "https://jira.example/browse/TEST-101",
        },
        {
            "manual_test_id": "M-FIX-2",
            "scenario_id": "SC-FIX-2",
            "title": "Verify fixture two",
            "jira_key": "FIX-1",
        },
    ]


def fixture_executions():
    base = {
        "stream_id": "fixture-stream",
        "release_id": "fixture-1.0",
        "build": "1.0.1",
    }
    return [
        {
            **base,
            "execution_id": "FIX-EXE-001",
            "manual_test_id": "M-FIX-1",
            "environment": "SIT",
            "status": "PASSED",
            "executed_at": "2026-08-25T10:01:00+08:00",
        },
        {
            **base,
            "execution_id": "FIX-EXE-002",
            "manual_test_id": "M-FIX-1",
            "environment": "UAT",
            "status": "FAILED",
            "executed_at": "2026-08-25T10:02:00+08:00",
        },
        {
            **base,
            "execution_id": "FIX-EXE-003",
            "manual_test_id": "M-FIX-2",
            "environment": "SIT",
            "status": "PASSED",
            "executed_at": "2026-08-25T10:03:00+08:00",
        },
        {
            **base,
            "execution_id": "FIX-EXE-004",
            "manual_test_id": "M-FIX-2",
            "environment": "UAT",
            "status": "BLOCKED",
            "executed_at": "2026-08-25T10:04:00+08:00",
        },
    ]


def snapshot():
    return builder.build_release_snapshot(
        fixture_manifest(), "1.0.1", fixture_definitions(), fixture_executions()
    )


def test_release_kpi_regression():
    snap = snapshot()
    assert snap["release"]["release_item_count"] == 1
    assert snap["kpis"]["total_applicable_gates"] == 5
    assert snap["kpis"]["executed"] == 4
    assert snap["kpis"]["passed"] == 2
    assert snap["kpis"]["failed"] == 1
    assert snap["kpis"]["blocked"] == 1
    assert snap["kpis"]["not_executed"] == 1
    assert snap["kpis"]["execution_progress"] == 80.0
    assert snap["kpis"]["pass_rate"] == 66.7


def test_release_item_environment_gate():
    item = snapshot()["release_items"][0]
    assert item["environment_gate"]["SIT"] == "PASSED"
    assert item["environment_gate"]["UAT"] == "FAILED"
    assert item["environment_gate"]["PPD"] == "NOT_EXECUTED"
    assert item["environment_gate"]["DEV"] == "N/A"


def test_manual_test_jira_traceability():
    scenario = snapshot()["release_items"][0]["features"][0]["scenario"]
    assert scenario["jira_key"] == "FIX-1"
    assert scenario["test_jira_key"] == "TEST-101"
    assert scenario["test_jira_url"].endswith("/TEST-101")
