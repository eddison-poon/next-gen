# Next Generation Dashboard — v0.6 UAT Candidate 2

v0.6 is a bundled UAT-hardening package. The three-tab architecture is unchanged.

## Included

### Release Focus hardening
- Agent Runtime 2.8 remains the reference release.
- Agent Hub UI 4.2 now contains a realistic second release scope.
- Mixed Passed / Failed / Blocked / Not Executed / N/A conditions.
- Multi-release switching can now be exercised with populated data.

### Regression / Automation hardening
- Added Ark Sandbox automation capability.
- Added blocked, partial, not-executed, and N/A regression states.
- Stronger duplicate-ID and result-matrix validation.

### Performance hardening
- Added Agent Hub UI 4.2.1 performance result.
- Performance results remain isolated by Release Stream → Release → Build.
- Existing no-result handling remains available for builds without a run.

### Calculation regression tests
`tests/test_release_reporting.py` locks the agreed Release Focus calculations and environment-gate rules.

### Company-network friendly UAT runner
No pytest dependency is required:

```bash
python tools/run_uat_checks.py
```

This rebuilds the generated snapshot, validates all data contracts, and runs lightweight reporting regression checks.

## Recommended internal UAT

```bash
python tools/run_uat_checks.py
python -m http.server 8000
```

Open `http://localhost:8000`.

Suggested checks:
1. Runtime 2.8 / Build 2.8.4 Release Focus.
2. Drill ETIVAI-12442 and locate the UAT failure.
3. Switch to Agent Hub UI 4.2 / Build 4.2.1.
4. Confirm mixed Manual states and N/A handling.
5. Regression / Automation: locate Failed, Blocked and Not Executed scenarios.
6. Confirm automation does not alter Release Focus health.
7. Performance: switch between Runtime and UI releases/builds.
8. Confirm release/build isolation and clean empty-result behavior.

If v0.6 passes, the next step should be production-data onboarding and UAT feedback fixes rather than another structural dashboard redesign.
