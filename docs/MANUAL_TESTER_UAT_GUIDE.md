# Manual Tester UAT Guide — v0.9

This is the day-to-day guide for Manual Testers using the Functional Testing Dashboard during internal UAT.

## Your role

You own execution of your assigned Manual Tests and recording the result of each real execution.

The Test Lead owns Release scope, publication to the dashboard, and final status reporting.

## 1. Confirm your assignment before testing

Before starting a test, confirm with the Test Lead:

- active Release Stream
- Release
- Build
- assigned Jira Release Item
- Manual Test ID
- environment to test

Example:

```text
Release Stream: Agent Runtime
Release: Release 2.9
Build: 2.9.1
Release Item: ETIVAI-12920
Manual Test: M-12920-01
Environment: UAT
```

Do not add or remove Release Items yourself. Raise any scope question to the Test Lead.

## 2. Review the Manual Test Definition

Before execution, confirm the Manual Test Definition is complete and understandable.

The definition describes what should be tested and the expected behavior.

If the definition is missing or unclear, stop and clarify it before recording an execution result.

## 3. Execute the test

Perform the test against the assigned environment using the agreed Manual Test Definition.

Determine the result:

- `PASSED` — expected behavior is met.
- `FAILED` — test executed but expected behavior is not met.
- `BLOCKED` — test cannot be completed because of an external blocker/dependency.

## 4. Record the result immediately after the test

Use the active Release bundle supplied by the Test Lead.

PASSED example:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-12920-01 --environment UAT --status PASSED
```

FAILED example:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-12920-01 --environment UAT --status FAILED
```

BLOCKED example:

```cmd
python .\tools\record_manual_execution.py input\runtime-2.9 --manual-test-id M-12920-01 --environment UAT --status BLOCKED
```

The command automatically creates the execution ID and timestamp.

## 5. Retesting rule

Every real retest must create a new execution.

Correct history:

```text
Execution 001 -> FAILED
Execution 002 -> PASSED
```

Do not edit Execution 001 from FAILED to PASSED to represent the retest.

The dashboard uses the latest execution for the current Release + Build + Manual Test + Environment while retaining older execution history.

## 6. If the application test fails

If the failure is a product/application problem:

1. Record the Manual execution as `FAILED`.
2. Raise or update the normal Jira product defect according to the team's QA process.
3. Keep the relevant evidence.
4. Inform the Test Lead if it affects release readiness or blocks further testing.

Product defects are separate from dashboard UAT findings.

## 7. If you cannot execute the test

If testing cannot continue because of environment, dependency, access, test data, or another blocker:

1. Record the result as `BLOCKED` when appropriate.
2. Record/raise the blocker using the normal project process.
3. Inform the Test Lead.

Do not mark a blocked test as PASSED or NOT_EXECUTED merely to avoid reporting the blocker.

## 8. If the dashboard/process looks wrong

Examples:

- you recorded PASSED but the dashboard shows FAILED;
- the Release or environment is missing;
- the wrong test result appears under another environment;
- a dashboard calculation looks incorrect.

Do not edit canonical `data` JSON to fix it yourself.

Capture:

- command used
- command output
- Release / Build
- Manual Test ID
- environment
- screenshot if useful

Then notify the Test Lead. The Test Lead will determine whether to record a Team UAT finding.

## 9. What you normally do NOT need to run

During initial Team UAT, Manual Testers normally do not need to run:

```text
publish_release_bundle.py
rebuild_from_bundles.py
operator_preflight.py
team_uat_status.py
publish_automation_status.py
```

These are Test Lead / operator controls unless the Test Lead specifically assigns them to you.

## Daily tester checklist

Before testing:

- confirm Release / Build
- confirm assigned Release Item
- confirm Manual Test ID
- confirm environment
- review Manual Test Definition

After each test:

- record PASSED / FAILED / BLOCKED with `record_manual_execution.py`
- raise/update Jira defect if it is a product failure
- inform Test Lead of release-impacting blockers or unusual results

At end of your testing session:

- confirm all tests you actually executed were recorded
- tell the Test Lead which assigned items are complete, failed, blocked, or still outstanding

## Golden rule

**Execute the defined test, record what actually happened, preserve execution history, and let the Test Lead control the official dashboard publication.**
