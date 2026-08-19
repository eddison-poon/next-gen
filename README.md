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

## Durable manual bundle restore

The manually maintained folders under `input/` are the durable source for manually onboarded releases. Canonical `data/` files may be refreshed by Git, so they must be reproducible from these bundles.

After a fresh pull or canonical-data reset, validate every real bundle under `input/` with:

```bash
python tools/rebuild_from_bundles.py --dry-run
```

Then restore all discovered bundles and rebuild the generated snapshot with:

```bash
python tools/rebuild_from_bundles.py --apply
python tools/run_uat_checks.py
```

`release_bundle_template` is intentionally excluded from automatic discovery. Only subfolders containing a `bundle.json` are treated as real Release Data Bundles.

For long-term durability, real release bundle folders should be retained as controlled project inputs (and committed to the appropriate project repository when company policy allows). The generated/canonical dashboard files remain rebuildable outputs.

## Regression / Automation UI consistency

The v0.6 UI correction is included: Automation now follows the same interaction model as Release Focus:

**Capability → Feature → Selected Feature → Automated Scenarios**

## UAT checks

No pytest dependency is required:

```bash
python tools/run_uat_checks.py
```

v0.7 adds onboarding regression checks to ensure dry-run imports are non-destructive, bundle generation works correctly, and durable-bundle discovery excludes the template while finding real release bundles.

## Documentation

See:

`docs/UAT_DATA_ONBOARDING.md`

## Recommended internal UAT flow

1. Pull the repository.
2. If real bundles already exist under `input/`, run `python tools/rebuild_from_bundles.py --apply`.
3. Run `python tools/run_uat_checks.py`.
4. Create or update a Release Data Bundle.
5. Populate real Jira Release Items and their Manual Test data.
6. Run the bundle `--dry-run` import.
7. Apply the bundle.
8. Run UAT checks again.
9. Start the local dashboard and confirm the Release appears without any UI code changes.

If this flow works cleanly with your team's real data, the next phase should be UAT feedback fixes and production connector/automation work rather than further data-model redesign.
