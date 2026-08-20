# Internal UAT Operator Guide — v0.8

v0.8 keeps Release Data Bundles as the durable Manual source and adds safer operator commands so testers do not need to hand-edit execution JSON for normal daily updates. Regression / Automation uses a separate durable operator workspace because it is a supporting regression signal and does not govern release readiness.

## Start-of-day preflight

For a release bundle such as Runtime 2.9:

```cmd
python .\tools\operator_preflight.py --bundle input\runtime-2.9
```

This validates the selected Release Data Bundle, validates the Automation workspace when present, and runs the repository UAT regression suite. It does not publish changes.

After a fresh Git pull or canonical-data reset, restore durable release bundles first:

```cmd
python .\tools\rebuild_from_bundles.py --apply
python .\tools\operator_preflight.py --bundle input\runtime-2.9
```

## Manual / Release Focus workflow

### Inspect the bundle

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
```

This shows each Release Item / Feature / Manual Test and the latest bundle status for DEV, SIT, UAT, PPD and PROD.

### Record a Manual execution

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment UAT --status PASSED
```

The tool automatically uses the bundle's Release Stream, Release and current Build, creates an execution ID and timestamp, and rejects environments that are not applicable to the selected Manual Test.

Optional explicit values:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment PPD --status FAILED --execution-id ETIVAI-13005-PPD-003 --executed-at 2026-08-19T16:30:00+08:00
```

Historical executions must be preserved. A retest is a new execution row, not an edit of an older real result. The dashboard uses the latest execution for the current Release + Build + Manual Test + Environment state.

### Validate before publishing

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
```

### Publish

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

Apply always performs a dry-run first. If validation passes, it imports the bundle and runs the full UAT regression checks.

## Regression / Automation workflow

### Initialize the durable Automation workspace

Run once, or again only when intentionally resetting the operator workspace from the canonical baseline:

```cmd
python .\tools\init_automation_workspace.py
```

This creates/refreshes:

```text
input\automation_regression.json
```

Do not run this casually after recording unpublished Automation changes because it refreshes the workspace from canonical data.

### Inspect Automation status

```cmd
python .\tools\show_automation_status.py input\automation_regression.json
```

### Record the latest Automation result

```cmd
python .\tools\record_automation_result.py input\automation_regression.json --automation-test-id MCP-JIRA-A-002 --environment UAT --status PASSED
```

Automation stores the latest regression signal per applicable environment; it is not a full execution-history store. N/A environments are rejected.

### Validate before publishing

```cmd
python .\tools\publish_automation_status.py input\automation_regression.json --dry-run
```

### Publish

```cmd
python .\tools\publish_automation_status.py input\automation_regression.json --apply
```

Publishing copies the validated operator workspace into canonical Automation data and runs the full UAT regression suite.

## Scope changes during a release

Release scope can change without deleting historical data. Add or remove Release Items only in the release bundle's `release_scope.json`; keep Manual Test Definitions and historical executions unless they are genuinely invalid data.

A removed Release Item disappears from the active release view. If it is added back later, its preserved Release/Build execution history is reused automatically.

## Operating rules

- Treat `input/<release>/` as the durable source for manually onboarded releases.
- Treat `input/automation_regression.json` as the durable Automation operator workspace.
- Do not hand-edit Manual execution rows during normal operation; use `record_manual_execution.py`.
- Do not edit historical Manual results to represent a retest; add a new execution.
- Use `show_bundle_status.py` / `show_automation_status.py` before publishing.
- Use `--dry-run` before every publish.
- After a repository refresh, restore release bundles with `rebuild_from_bundles.py --apply`.
- Manual Release Focus is release-governing; Regression / Automation is a supporting signal only.
- Performance remains release/build-specific and independent of Manual release readiness.

## End-of-update verification

After publishing Manual and/or Automation changes:

```cmd
python .\tools\run_uat_checks.py
```

Then refresh the browser and verify only the intended Release / Build / Environment statuses changed.

## Expected v0.8 operator outcome

A tester should be able to perform normal internal-UAT updates using operator commands without editing dashboard HTML, CSS, JavaScript or canonical `data/` files directly.
