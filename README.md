# Next Generation Dashboard — v0.8 Internal UAT Operator Candidate

v0.8 keeps the stable three-tab dashboard architecture and the v0.7 durable Release Data Bundle model. Its purpose is to make day-to-day internal UAT operation safer and simpler for testers.

## Operating model

**Durable Release Data Bundle → Safe operator update → Dry-run → Publish → Canonical Data → Reporting Snapshot → Dashboard**

Release, Regression / Automation and Performance remain separate functional tabs. Manual testing remains the release-governing signal.

## Create a Release Data Bundle

```cmd
python .\tools\create_release_bundle.py --stream-id agent-runtime --stream-name "Agent Runtime" --release-id runtime-2.9 --release-name "Release 2.9" --build 2.9.1 --output input/runtime-2.9
```

The bundle contains the current release scope, Manual Test Definitions, execution history, and optional Automation / Performance inputs.

## v0.8: inspect current bundle state

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
```

This shows the latest status in each environment before publishing.

## v0.8: record Manual executions safely

Instead of hand-editing normal execution rows:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment UAT --status PASSED
```

The recorder:

- derives Release Stream, Release and Build from the bundle;
- generates an execution ID and timestamp when omitted;
- rejects non-applicable environments;
- rejects duplicate execution IDs;
- preserves previous execution history by appending a new row.

## v0.8: validate / publish one bundle

Dry-run:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
```

Apply:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

`--apply` always performs the dry-run first. Only after validation succeeds does it import the bundle and run the full UAT regression suite.

## Restore durable bundles after a repository refresh

```cmd
python .\tools\rebuild_from_bundles.py --dry-run
python .\tools\rebuild_from_bundles.py --apply
python .\tools\run_uat_checks.py
```

`input/release_bundle_template` is excluded from automatic discovery. Real bundle folders are the durable manual source; canonical dashboard data can be rebuilt from them.

## UAT validation

No pytest dependency is required:

```cmd
python .\tools\run_uat_checks.py
```

v0.8 adds operator-workflow regression checks covering valid execution entry, non-applicable environment rejection and duplicate execution-ID protection.

## Documentation

- `docs/UAT_DATA_ONBOARDING.md` — v0.7 data onboarding model
- `docs/INTERNAL_UAT_OPERATOR_GUIDE.md` — v0.8 day-to-day operator workflow

## Internal UAT recommendation

Use manually prepared release scope and definitions first. During normal execution, record new results through `record_manual_execution.py`, inspect them with `show_bundle_status.py`, and publish them with `publish_release_bundle.py`.

Third-party Jira extraction, execution connectors and other automated ingestion should be added only after this complete manual operating process is accepted by the internal team.
