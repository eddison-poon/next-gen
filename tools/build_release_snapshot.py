from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "generated"
ENVIRONMENTS = ["DEV", "SIT", "UAT", "PPD", "PROD"]
DONE = {"PASSED", "FAILED", "BLOCKED"}

def load_path(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load(name: str):
    return load_path(DATA / name)

def pct(a: int, b: int) -> float:
    return round((a / b) * 100, 1) if b else 0.0

def latest_by_test_env(executions):
    latest = {}
    for x in executions:
        key = (x["manual_test_id"], x["environment"])
        current = latest.get(key)
        if current is None or datetime.fromisoformat(x["executed_at"]) > datetime.fromisoformat(current["executed_at"]):
            latest[key] = x
    return latest

def status_for(feature, env, latest):
    if env not in feature["applicable_environments"]:
        return "N/A"
    row = latest.get((feature["manual_test_id"], env))
    return row["status"] if row else "NOT_EXECUTED"

def build_release_snapshot(manifest, build, definitions, executions):
    stream = manifest["stream"]
    release = manifest["release"]
    items = manifest.get("scope", {}).get("release_items", [])
    scoped_execs = [
        x for x in executions
        if x["stream_id"] == stream["id"]
        and x["release_id"] == release["id"]
        and x["build"] == build
    ]
    latest = latest_by_test_env(scoped_execs)
    def_by_id = {x["manual_test_id"]: x for x in definitions}

    pairs=[]
    release_items=[]
    env_pairs={e:[] for e in ENVIRONMENTS}

    for item in items:
        feature_views=[]
        item_statuses=[]
        item_envs={}

        for feature in item["features"]:
            d=def_by_id[feature["manual_test_id"]]
            env_statuses={}
            for env in ENVIRONMENTS:
                status=status_for(feature,env,latest)
                env_statuses[env]=status
                if status!="N/A":
                    row={
                        "jira_key":item["jira_key"],
                        "feature_id":feature["id"],
                        "scenario_id":feature["scenario_id"],
                        "manual_test_id":feature["manual_test_id"],
                        "environment":env,
                        "status":status,
                    }
                    pairs.append(row)
                    env_pairs[env].append(row)
                    item_statuses.append(status)

            feature_views.append({
                "id":feature["id"],
                "name":feature["name"],
                "scenario":{
                    "id":feature["scenario_id"],
                    "title":d["title"],
                    "manual_test_id":feature["manual_test_id"],
                    "jira_key":d["jira_key"],
                },
                "applicable_environments":feature["applicable_environments"],
                "environment_status":env_statuses,
            })

        for env in ENVIRONMENTS:
            statuses=[
                status_for(f,env,latest)
                for f in item["features"]
                if env in f["applicable_environments"]
            ]
            if not statuses:item_envs[env]="N/A"
            elif all(s=="PASSED" for s in statuses):item_envs[env]="PASSED"
            elif any(s=="FAILED" for s in statuses):item_envs[env]="FAILED"
            elif any(s=="BLOCKED" for s in statuses):item_envs[env]="BLOCKED"
            else:item_envs[env]="NOT_EXECUTED"

        if not item_statuses or all(s=="NOT_EXECUTED" for s in item_statuses):health="GREY"
        elif any(s=="FAILED" for s in item_statuses):health="RED"
        elif any(s in {"BLOCKED","NOT_EXECUTED"} for s in item_statuses):health="AMBER"
        else:health="GREEN"

        release_items.append({
            "jira_key":item["jira_key"],
            "summary":item["summary"],
            "issue_type":item["issue_type"],
            "jira_url":item["jira_url"],
            "health":health,
            "environment_gate":item_envs,
            "features":feature_views,
        })

    executed=[x for x in pairs if x["status"] in DONE]
    passed=[x for x in pairs if x["status"]=="PASSED"]
    failed=[x for x in pairs if x["status"]=="FAILED"]
    blocked=[x for x in pairs if x["status"]=="BLOCKED"]
    not_executed=[x for x in pairs if x["status"]=="NOT_EXECUTED"]

    environment_health=[]
    for env in ENVIRONMENTS:
        rows=env_pairs[env]
        done=[x for x in rows if x["status"] in DONE]
        p=[x for x in done if x["status"]=="PASSED"]
        f=[x for x in done if x["status"]=="FAILED"]
        b=[x for x in done if x["status"]=="BLOCKED"]
        pass_fail=len(p)+len(f)
        environment_health.append({
            "environment":env,
            "applicable":len(rows),
            "executed":len(done),
            "passed":len(p),
            "failed":len(f),
            "blocked":len(b),
            "not_executed":len(rows)-len(done),
            "pass_rate":pct(len(p),pass_fail) if pass_fail else None,
            "readiness":"N/A" if not rows else "READY" if all(x["status"]=="PASSED" for x in rows) else "IN_PROGRESS" if done else "NOT_STARTED",
        })

    item_healths=[x["health"] for x in release_items]
    overall="RED" if "RED" in item_healths else "AMBER" if "AMBER" in item_healths else "GREEN" if item_healths else "NOT_AVAILABLE"

    return {
        "scope":{
            "version":manifest["scope_version"],
            "effective_at":manifest["effective_at"],
        },
        "stream":{"id":stream["id"],"name":stream["name"]},
        "release":{
            "id":release["id"],
            "name":release["name"],
            "build":build,
            "available_builds":release["builds"],
            "release_item_count":len(items),
        },
        "kpis":{
            "overall_health":overall,
            "release_test_coverage":pct(len(executed),len(pairs)),
            "execution_progress":pct(len(executed),len(pairs)),
            "pass_rate":pct(len(passed),len(passed)+len(failed)) if (passed or failed) else None,
            "executed":len(executed),
            "passed":len(passed),
            "failed":len(failed),
            "blocked":len(blocked),
            "not_executed":len(not_executed),
            "total_applicable_gates":len(pairs),
        },
        "environment_health":environment_health,
        "release_items":release_items,
    }

def main():
    registry=load("release_registry.json")
    definitions=load("manual_test_definitions.json")["definitions"]
    executions=load("manual_executions.json")["executions"]

    snapshots=[]
    first_selected=None

    for stream in registry["streams"]:
        for release_ref in stream["releases"]:
            ref=release_ref["manifest"]
            manifest=load_path(ROOT/ref)
            if first_selected is None:
                first_selected={
                    "stream_id":manifest["stream"]["id"],
                    "release_id":manifest["release"]["id"],
                    "build":manifest["release"]["current_build"],
                }
            for build in manifest["release"]["builds"]:
                snapshots.append(build_release_snapshot(manifest,build,definitions,executions))

    payload={
        "schema_version":"ng-release-focus-snapshot-0.4",
        "generated_at":registry["generated_at"],
        "selected":first_selected,
        "snapshots":snapshots,
    }
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/"release_focus_snapshot.json"
    target.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(f"Generated: {target.relative_to(ROOT)}")
    print(f"Release/build snapshots: {len(snapshots)}")

if __name__=="__main__":
    main()
