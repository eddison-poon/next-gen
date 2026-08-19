# Internal UAT Operator Guide — v0.8

v0.8 keeps Release Data Bundles as the durable manual source and adds safer operator commands so testers do not need to hand-edit execution JSON for normal daily updates.

## 1. Inspect a bundle

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
```

This shows each Release Item / Feature / Manual Test and the latest bundle status for DEV, SIT, UAT, PPD and PROD.

## 2. Record a Manual execution safely

Example:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment UAT --status PASSED
```

The tool automatically uses the bundle's Release Stream, Release and current Build, creates an execution ID and timestamp, and rejects environments that are not applicable to the selected Manual Test.

Optional explicit values:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-13005-01 --environment PPD --status FAILED --execution-id ETIVAI-13005-PPD-003 --executed-at 2026-08-19T16:30:00+08:00
```

Historical executions should be preserved. A retest is a new execution row, not an edit of an older real result.

## 3. Validate before publishing

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
```

This runs the normal Release Data Bundle validation without changing canonical dashboard data.

## 4. Publish

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

Apply always performs a dry-run first. If validation passes, it imports the bundle and runs the full UAT regression checks.

## 5. Restore all durable bundles after a repository refresh

```cmd
python .\tools\rebuild_from_bundles.py --apply
python .\tools\run_uat_checks.py
```

## Daily operating rule

- Release scope and Manual Test Definitions remain manually prepared during internal UAT.
- Use `record_manual_execution.py` for normal execution updates instead of hand-editing `manual_executions.json`.
- Keep all historical execution rows in the bundle.
- Use `show_bundle_status.py` before publishing when multiple results have been added.
- Use `publish_release_bundle.py --dry-run` before every apply.
- Automation and Performance data remain optional and independent of Manual release readiness.
