# v0.7 Internal UAT Data Onboarding

## Objective

The dashboard should accept new Release data without editing HTML, CSS, or JavaScript.

The operational boundary is now:

`Team input bundle → importer → canonical data → reporting snapshot → dashboard`

## Release data bundle

Each bundle contains:

- `release_scope.json` — Release Stream, Release, Builds, Jira Release Items, Features, Scenario/Test references, environment applicability.
- `manual_test_definitions.json` — new or changed Manual Test Definitions used by the release.
- `manual_executions.json` — Manual execution facts for the release/build/environment.
- `automation_regression.json` — optional complete automation snapshot. Leave `capabilities` empty if automation is not being changed.
- `performance_results.json` — optional new performance runs. Leave `results` empty if none are being imported.

## Safe onboarding sequence

```bash
python tools/create_release_bundle.py --stream-id agent-runtime --stream-name "Agent Runtime" --release-id runtime-2.9 --release-name "Release 2.9" --build 2.9.1 --output input/runtime-2.9
```

Edit the generated files.

Validate only:

```bash
python tools/import_data_bundle.py input/runtime-2.9 --dry-run
```

Apply:

```bash
python tools/import_data_bundle.py input/runtime-2.9 --apply
```

Rebuild and regression-check:

```bash
python tools/run_uat_checks.py
```

Serve:

```bash
python -m http.server 8000
```

## Operating rules

- One Jira ticket = one Release Item.
- A Release Item may contain N Features.
- Each Feature references one Scenario and one Manual Test Definition.
- Applicable environments are explicit; omitted environments are N/A.
- Scope can change. Re-importing the same release updates the current release manifest rather than treating the change as an error.
- Manual Test Definitions are upserted by `manual_test_id`.
- Manual executions are upserted by `execution_id`.
- Performance runs are upserted by `test_run`.
- Automation import is optional and treated as a complete automation snapshot when supplied.
- The importer does not modify UI code.
