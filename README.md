# Next Generation Dashboard — v0.8 Internal UAT Candidate

v0.8 keeps the stable three-tab dashboard architecture and the v0.7 durable Release Data Bundle model. Its purpose is to make day-to-day internal UAT operation safer and simpler for testers without editing dashboard code or canonical data directly.

## Operating model

**Durable operator input → Safe update → Inspect → Dry-run → Publish → Canonical Data → Reporting Snapshot → Dashboard**

Release Focus remains Manual and release-governing. Regression / Automation remains a supporting regression signal. Performance remains release/build-specific.

## Start-of-day preflight

For a release bundle such as Runtime 2.9:

```cmd
python .\tools\operator_preflight.py --bundle input\runtime-2.9
```

The preflight validates the selected Release Data Bundle, validates `input\automation_regression.json` when present, and runs the repository UAT suite without publishing changes.

## Create a Release Data Bundle

```cmd
python .\tools\create_release_bundle.py --stream-id agent-runtime --stream-name "Agent Runtime" --release-id runtime-2.9 --release-name "Release 2.9" --build 2.9.1 --output input/runtime-2.9
```

The bundle contains the current release scope, Manual Test Definitions, execution history, and optional Automation / Performance inputs.

## Manual / Release Focus operator flow

Inspect:

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
```

Record a new Manual execution:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment UAT --status PASSED
```

Validate and publish:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

Manual execution history is append-only for normal operations. Retests should create new execution rows; the latest Release + Build + Manual Test + Environment execution drives the current dashboard state.

## Regression / Automation operator flow

Initialize the durable workspace from the canonical baseline when needed:

```cmd
python .\tools\init_automation_workspace.py
```

Inspect:

```cmd
python .\tools\show_automation_status.py input\automation_regression.json
```

Update the latest regression result:

```cmd
python .\tools\record_automation_result.py input\automation_regression.json --automation-test-id MCP-JIRA-A-002 --environment UAT --status PASSED
```

Validate and publish:

```cmd
python .\tools\publish_automation_status.py input\automation_regression.json --dry-run
python .\tools\publish_automation_status.py input\automation_regression.json --apply
```

Automation stores the latest regression signal per applicable environment rather than full execution history.

## Restore durable releases after a repository refresh

```cmd
python .\tools\rebuild_from_bundles.py --dry-run
python .\tools\rebuild_from_bundles.py --apply
python .\tools\run_uat_checks.py
```

`input\release_bundle_template` is excluded from automatic discovery. Real release bundle folders are the durable Manual source; canonical dashboard data can be rebuilt from them.

## UAT validation

No pytest dependency is required:

```cmd
python .\tools\run_uat_checks.py
```

The v0.8 regression suite now covers Release reporting calculations, bundle onboarding/durability, Manual operator safety and Automation operator safety, including non-destructive dry-runs and N/A/duplicate protections.

## Documentation

- `docs/UAT_DATA_ONBOARDING.md` — data onboarding model
- `docs/INTERNAL_UAT_OPERATOR_GUIDE.md` — complete v0.8 day-to-day runbook

## Internal UAT rule

During internal UAT, manually prepare Release scope and Test Definitions, then use operator commands for execution/result updates and publishing. Jira extraction and other third-party ingestion should be added only after this manual operating model is accepted as stable.
