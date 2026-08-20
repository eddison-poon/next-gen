# Team UAT Runbook — v0.9

v0.9 moves the dashboard from operator validation into controlled internal team UAT. The dashboard architecture and data model remain unchanged.

## Start of day

1. Pull the latest repository changes.
2. Restore durable Release Data Bundles if needed:

```cmd
python .\tools\rebuild_from_bundles.py --apply
```

3. Run the operator preflight:

```cmd
python .\tools\operator_preflight.py --bundle input\runtime-2.9
```

4. Review the concise UAT status:

```cmd
python .\tools\team_uat_status.py input\runtime-2.9
```

## During UAT

### Manual / Release Focus

Record each new real execution as a new row:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-12920-01 --environment UAT --status PASSED
```

Inspect before publish:

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
```

Dry-run and apply:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

### Regression / Automation

Update the latest supporting regression signal:

```cmd
python .\tools\record_automation_result.py input\automation_regression.json --automation-test-id MCP-JIRA-A-002 --environment UAT --status PASSED
```

Inspect and publish:

```cmd
python .\tools\show_automation_status.py input\automation_regression.json
python .\tools\publish_automation_status.py input\automation_regression.json --dry-run
python .\tools\publish_automation_status.py input\automation_regression.json --apply
```

## Feedback and defect handling

Use `docs/UAT_FEEDBACK_TEMPLATE.md` for dashboard/process feedback. Product defects discovered while testing the release remain normal release Jira defects and should be linked to the relevant Release Item where appropriate.

Classify dashboard UAT feedback as:

- `BLOCKER` — prevents team operation or produces materially wrong release status.
- `HIGH` — important workflow or calculation issue with a workaround.
- `MEDIUM` — usability/reporting issue that does not invalidate status.
- `LOW` — cosmetic or future enhancement.

Do not change canonical JSON directly to work around a dashboard defect. Preserve the failing input and command output so the issue is reproducible.

## End of day

1. Run:

```cmd
python .\tools\team_uat_status.py input\runtime-2.9
```

2. Confirm the browser matches the command-line status.
3. Capture new dashboard/process feedback.
4. Run the full check suite before committing controlled input changes:

```cmd
python .\tools\run_uat_checks.py
```

## Exit criteria for internal UAT

The candidate is ready to move beyond internal UAT when:

- no open BLOCKER dashboard/process defects remain;
- release scope changes can be applied without losing historical executions;
- Manual status is correct across all applicable environments;
- Automation remains a non-governing supporting signal;
- repository refresh + durable bundle restore is proven;
- operators can complete daily updates without hand-editing normal execution/result JSON;
- dashboard values match the source bundle/status commands for the agreed UAT period.
