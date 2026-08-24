# Test Lead UAT Guide — v0.9

This guide is for the Test Lead operating the Functional Testing Dashboard during internal UAT.

## Your role

You own the official Release scope, Build baseline, team assignments, publication of Manual results to the dashboard, dashboard integrity checks, and Team UAT governance.

Manual Testers execute and record their test results. They should not independently change Release scope or publish canonical dashboard data during the initial UAT cycle.

## 1. Define the active Release baseline

Confirm with the delivery/product team:

- Release Stream
- Release
- current Build
- Jira Release Items included in scope
- applicable environments for each Feature / Manual Test

Example:

```text
Release Stream: Agent Runtime
Release: Release 2.9
Build: 2.9.1
```

For a brand-new Release, create the durable bundle:

```cmd
python .\tools\create_release_bundle.py --stream-id agent-runtime --stream-name "Agent Runtime" --release-id runtime-2.9 --release-name "Release 2.9" --build 2.9.1 --output input/runtime-2.9
```

## 2. Maintain Release scope

The Test Lead owns `release_scope.json` inside the active bundle.

When Release Items are added or removed, update the active bundle scope only after confirming the change with the release/delivery owner.

Do not delete historical Manual executions when an item is removed from current scope.

After a scope update, validate before publishing:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
```

## 3. Confirm Manual Test Definitions are ready

Each in-scope Feature must reference a valid Manual Test Definition before execution starts.

Testers may prepare or propose the definitions for their assigned items. The Test Lead reviews the mapping and confirms:

```text
Release Item -> Feature -> Scenario -> Manual Test Definition -> applicable environments
```

## 4. Start-of-day checks

After pulling the latest repository state, restore durable bundles if required:

```cmd
python .\tools\rebuild_from_bundles.py --apply
```

Run preflight:

```cmd
python .\tools\operator_preflight.py --bundle input\runtime-2.9
```

Review current UAT status:

```cmd
python .\tools\team_uat_status.py input\runtime-2.9
```

Expected dashboard publish state:

```text
dashboard publish state: PUBLISHED
```

Tell the testers the active Release / Build baseline and their assigned Release Items.

## 5. During testing

Manual Testers execute their assigned tests and record each real execution using `record_manual_execution.py`.

A retest is always a new execution. Historical real results must not be changed to represent a later run.

Application/product defects remain normal Jira defects.

Dashboard/process problems are Team UAT findings, not product defects.

## 6. Review before dashboard publication

Inspect all results recorded in the active bundle:

```cmd
python .\tools\show_bundle_status.py input\runtime-2.9
```

Check especially:

- correct Manual Test IDs
- correct environment
- unexpected FAILED / BLOCKED results
- outstanding applicable gates
- scope changes since the previous publish

Then dry-run:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --dry-run
```

## 7. Publish the official dashboard state

When the bundle is correct:

```cmd
python .\tools\publish_release_bundle.py input\runtime-2.9 --apply
```

Then verify:

```cmd
python .\tools\team_uat_status.py input\runtime-2.9
```

Finally refresh the browser and reconcile:

```text
Release Bundle = team_uat_status.py = Dashboard
```

If these disagree, stop publication/reporting and investigate before using the dashboard as the official status.

## 8. Handle Team UAT findings

Record dashboard/process issues with:

```cmd
python .\tools\record_uat_feedback.py ...
```

Review findings:

```cmd
python .\tools\show_uat_feedback.py
```

After a fix and successful retest, close the finding with:

```cmd
python .\tools\close_uat_feedback.py UAT-001 --retested-by "<name>" --retest-result PASSED --resolution "<resolution>" --fix-version v0.9
```

Do not close a failed retest.

## 9. End-of-day checks

Run:

```cmd
python .\tools\team_uat_status.py input\runtime-2.9
python .\tools\show_uat_feedback.py
python .\tools\run_uat_checks.py
```

Confirm the browser matches the command-line status and summarize for the team:

- execution progress
- pass / fail / blocked / not executed
- environments behind plan
- release-impacting defects
- current blockers
- scope changes
- open dashboard/process UAT findings

## Operating rules

1. Test Lead owns Release scope and publication.
2. Manual Testers own execution of assigned tests and recording their results.
3. Do not edit previous real execution records to represent a retest.
4. Do not change canonical `data` JSON directly as a normal operating workaround.
5. Keep Release/product defects separate from dashboard/process UAT findings.
6. The durable bundle under `input` is the operator source; canonical `data` is the published dashboard state.
