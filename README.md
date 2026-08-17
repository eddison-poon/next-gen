# Next Generation Dashboard — v0.5 UAT Candidate 1

This is the first bundled UAT-oriented package after v0.4.

## Included

### Release Focus
- Release Stream → Release → Build
- Dynamic release scope
- Jira Release Item navigator
- Manual release-governing testing
- Release Test Coverage
- Execution Progress
- Pass Rate
- Environment Health
- Feature / Scenario per-environment status
- N/A handling

### Regression / Automation
The placeholder is replaced by a working Capability Explorer.

- left navigator = Capabilities
- Capability → Feature → Automated Scenario
- DEV / SIT / UAT / PPD / PROD status
- overall automation coverage
- per-environment automation coverage
- ✓ / ✕ / ! / — / N/A
- automation is a supporting regression signal and does not gate release readiness

### Performance Testing
The placeholder is replaced by a release-aware foundation.

- Release Stream → Release → Build
- latest result for the selected release/build
- overall assessment
- Peak Users
- Throughput / QPM
- P95 Response Time
- Error Rate
- clean empty-state when no result exists

## Validation

From `next_gen_preview`:

```bash
python tools/build_release_snapshot.py
python tools/validate_release_data.py
python tools/validate_uat_candidate.py
python -m http.server 8000
```

Then open `http://localhost:8000`.

## UAT focus

1. Can a tester understand selected Release progress and drill into a failing Manual scenario?
2. Can a tester understand regression automation coverage and identify missing/failed automated scenarios?
3. Does Performance selection by Release/Build feel natural?
4. Do all three tabs feel like the same dashboard product?
