# Next Generation Dashboard — v0.9 Team UAT Candidate

v0.9 promotes the validated v0.8 operator workflow into controlled internal team UAT. The dashboard architecture and v0.7/v0.8 data/operator model remain unchanged.

## Operating model

**Durable operator input → Safe update → Inspect → Dry-run → Publish → Canonical Data → Reporting Snapshot → Dashboard → Team UAT feedback**

Release Focus remains Manual and release-governing. Regression / Automation remains a supporting regression signal. Performance remains release/build-specific.

## Start-of-day preflight

For a release bundle such as Runtime 2.9:

```cmd
python .\tools\operator_preflight.py --bundle input\runtime-2.9
```

Then review the concise team-UAT status:

```cmd
python .\tools\team_uat_status.py input\runtime-2.9
```

The status command summarizes Release/Build, scope version, Manual gate progress, pass/fail/blocked/not-executed counts, testing health, exceptions, outstanding gates and the optional Automation supporting signal.

## Manual / Release Focus operator flow

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment UAT --status PASSED
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

Manual execution history is append-only for normal operations. Retests create new execution rows; the latest Release + Build + Manual Test + Environment execution drives current dashboard state.

## Regression / Automation operator flow

```cmd
python .\tools\init_automation_workspace.py
python .\tools\show_automation_status.py input\automation_regression.json
python .\tools\record_automation_result.py input\automation_regression.json --automation-test-id MCP-JIRA-A-002 --environment UAT --status PASSED
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

## Team UAT documentation

- `docs/UAT_DATA_ONBOARDING.md` — data onboarding model
- `docs/INTERNAL_UAT_OPERATOR_GUIDE.md` — operator commands and safeguards
- `docs/TEAM_UAT_RUNBOOK.md` — start-of-day, during-UAT and end-of-day team workflow
- `docs/UAT_FEEDBACK_TEMPLATE.md` — structured dashboard/process feedback capture

## Team UAT rule

During internal UAT, manually prepare Release scope and Test Definitions, use operator commands for execution/result updates and publishing, and capture dashboard/process findings using the feedback template. Product defects remain normal release Jira defects.

Jira extraction and other third-party ingestion should be added only after this complete manual operating model is accepted as stable by the internal team.
