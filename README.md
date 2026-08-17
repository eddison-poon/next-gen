# Next Generation Dashboard — Release Focus Reporting Layer v0.3

v0.3 keeps the accepted v0.1 layout and the v0.2 raw-data model, and introduces the first derived reporting layer.

## Why v0.3

The browser no longer calculates release metrics directly from raw manifest / definition / execution files.

Instead:

`Release Manifest + Manual Definitions + Manual Executions`
→ `build_release_snapshot.py`
→ `data/generated/release_focus_snapshot.json`
→ Dashboard UI

This creates a stable boundary between raw repository data and presentation.

## Added

- `tools/build_release_snapshot.py`
  - derives latest execution state per Manual Test × Environment for the selected Build
  - applies environment applicability / N/A rules
  - calculates Release Test Coverage
  - calculates Manual Execution Progress
  - calculates Pass Rate
  - calculates per-environment pass rate
  - derives Release Item environment gates
  - prepares Feature and Selected Feature per-environment status

- `data/generated/release_focus_snapshot.json`
  - generated UI contract
  - includes all Release Stream / Release / Build combinations

- Dashboard JS now consumes only the generated snapshot for Release Focus.

## Current calculation rules

### Release Test Coverage / Execution Progress

`Executed applicable Scenario × Environment gates / Total applicable Scenario × Environment gates`

Passed, Failed and Blocked count as executed. N/A is excluded.

### Pass Rate

`Passed / (Passed + Failed)`

Blocked is excluded.

### Environment Health

For each environment:

`Passed Manual scenario results / (Passed + Failed Manual scenario results)`

This percentage is shown only at Environment Health level.

### Feature / Selected Feature

Per environment:

- ✓ Passed
- ✕ Failed
- ! Blocked
- — Not Executed
- N/A Not Applicable

No Feature-level percentage is shown.

### Release Item environment gate

A Release Item passes an environment only when **all applicable Features under that item have Passed** in that environment.

## Commands

From `next_gen_preview`:

```bash
python tools/validate_release_data.py
python tools/build_release_snapshot.py
python tools/validate_release_data.py
python -m http.server 8000
```

Then open `http://localhost:8000`.

## v0.3 purpose

Establish the release-focused reporting contract before connecting Jira ingestion, repository-managed Manual Test Definitions, and operational execution feeds.
