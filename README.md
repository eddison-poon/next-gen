# Next Generation Dashboard — v0.7 UAT Readiness / Real Data Onboarding

v0.7 shifts the project from dashboard construction to **operational onboarding of real project data**. The Release, Regression / Automation, and Performance tab architecture remains unchanged.

## v0.7 objective

A team should be able to add or update a Release without editing HTML, CSS, or JavaScript.

The operating path is now:

**Release Data Bundle → Import / Validate → Canonical Data → Reporting Snapshot → Dashboard**

## New: Release Data Bundle

Use:

```bash
python tools/create_release_bundle.py --stream-id agent-runtime --stream-name "Agent Runtime" --release-id runtime-2.9 --release-name "Release 2.9" --build 2.9.1 --output input/runtime-2.9
```

The generated bundle contains:

- `release_scope.json`
- `manual_test_definitions.json`
- `manual_executions.json`
- `automation_regression.json`
- `performance_results.json`

Edit only these input files for the new release.

## Validate before changing dashboard data

```bash
python tools/import_data_bundle.py input/runtime-2.9 --dry-run
```

A dry run validates the Release hierarchy, Manual Test Definition references, execution Release/Build/Environment mapping, and input structure without modifying canonical dashboard data.

## Apply

```bash
python tools/import_data_bundle.py input/runtime-2.9 --apply
python tools/run_uat_checks.py
```

The importer:

- adds or updates the Release Stream / Release registry;
- writes the current Release Scope manifest;
- upserts Manual Test Definitions by `manual_test_id`;
- upserts Manual executions by `execution_id`;
- optionally replaces the Automation snapshot when a non-empty automation file is supplied;
- optionally upserts Performance results by `test_run`;
- records the scope import in the Release Scope Log.

## Regression / Automation UI consistency

The v0.6 UI correction is included: Automation now follows the same interaction model as Release Focus:

**Capability → Feature → Selected Feature → Automated Scenarios**

## UAT checks

No pytest dependency is required:

```bash
python tools/run_uat_checks.py
```

v0.7 adds onboarding regression checks to ensure dry-run imports are non-destructive and bundle generation works correctly.

## Documentation

See:

`docs/UAT_DATA_ONBOARDING.md`

## Recommended internal UAT flow

1. Pull the repository.
2. Run `python tools/run_uat_checks.py`.
3. Create a new test Release Data Bundle.
4. Populate 1–2 real Jira Release Items and their Manual Test data.
5. Run `--dry-run`.
6. Apply the bundle.
7. Run UAT checks again.
8. Start the local dashboard and confirm the new Release appears without any UI code changes.

If this flow works cleanly with your team's real data, the next phase should be UAT feedback fixes and production connector/automation work rather than further data-model redesign.
