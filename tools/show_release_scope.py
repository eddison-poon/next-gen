from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"data"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

registry=load(DATA/"release_registry.json")
for stream in registry["streams"]:
    for ref in stream["releases"]:
        manifest=load(ROOT/ref["manifest"])
        items=manifest["scope"]["release_items"]
        features=sum(len(x["features"]) for x in items)
        gates=sum(len(f["applicable_environments"]) for x in items for f in x["features"])
        print(f"{manifest['stream']['name']} | {manifest['release']['name']} | build {manifest['release']['current_build']}")
        print(f"  scope version: {manifest['scope_version']}")
        print(f"  release items: {len(items)}")
        print(f"  features/scenarios: {features}")
        print(f"  applicable manual gates: {gates}")
