
from __future__ import annotations
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("builder",ROOT/"tools/build_release_snapshot.py")
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def manifest(stream, release): return load(ROOT/f"data/releases/{stream}/{release}.json")

def test_runtime_kpi_regression():
    defs=load(ROOT/"data/manual_test_definitions.json")["definitions"]
    ex=load(ROOT/"data/manual_executions.json")["executions"]
    snap=builder.build_release_snapshot(manifest("agent-runtime","runtime-2.8"),"2.8.4",defs,ex)
    assert snap["kpis"]["total_applicable_gates"]==24
    assert snap["kpis"]["executed"]==16
    assert snap["kpis"]["passed"]==14
    assert snap["kpis"]["failed"]==1
    assert snap["kpis"]["blocked"]==1
    assert snap["kpis"]["not_executed"]==8
    assert snap["kpis"]["release_test_coverage"]==66.7
    assert snap["kpis"]["pass_rate"]==93.3

def test_ui_release_scope():
    defs=load(ROOT/"data/manual_test_definitions.json")["definitions"]
    ex=load(ROOT/"data/manual_executions.json")["executions"]
    snap=builder.build_release_snapshot(manifest("agenthub-ui","ui-4.2"),"4.2.1",defs,ex)
    assert snap["release"]["release_item_count"]==3
    assert snap["kpis"]["total_applicable_gates"]==14
    assert snap["kpis"]["executed"]==10
    assert snap["kpis"]["passed"]==8
    assert snap["kpis"]["failed"]==1
    assert snap["kpis"]["blocked"]==1
    assert snap["kpis"]["not_executed"]==4

def test_release_item_environment_gate():
    defs=load(ROOT/"data/manual_test_definitions.json")["definitions"]
    ex=load(ROOT/"data/manual_executions.json")["executions"]
    snap=builder.build_release_snapshot(manifest("agent-runtime","runtime-2.8"),"2.8.4",defs,ex)
    item=next(x for x in snap["release_items"] if x["jira_key"]=="ETIVAI-12442")
    assert item["environment_gate"]["SIT"]=="PASSED"
    assert item["environment_gate"]["UAT"]=="FAILED"
    assert item["environment_gate"]["PPD"]=="NOT_EXECUTED"
