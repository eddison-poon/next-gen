# Real Data Onboarding Input

Starting in v0.7, internal teams should prepare data in an input bundle instead of editing dashboard UI files or canonical `data/` files directly.

## Recommended flow

1. Create a starter bundle:

```bash
python tools/create_release_bundle.py --stream-id agent-runtime --stream-name "Agent Runtime" --release-id runtime-2.9 --release-name "Release 2.9" --build 2.9.1 --output input/runtime-2.9
```

2. Edit the generated JSON files.
3. Validate without changing canonical data:

```bash
python tools/import_data_bundle.py input/runtime-2.9 --dry-run
```

4. Apply when validation is clean:

```bash
python tools/import_data_bundle.py input/runtime-2.9 --apply
```

5. Run:

```bash
python tools/run_uat_checks.py
python -m http.server 8000
```

The importer updates the registry/current release scope, upserts Manual Test Definitions and executions, and optionally imports Automation and Performance snapshots. The UI does not need code changes for a new release.
