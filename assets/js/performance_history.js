(() => {
  "use strict";

  let performanceData=null;
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));

  document.addEventListener("DOMContentLoaded",()=>{
    ["perfStreamSelect","perfReleaseSelect","perfBuildSelect"].forEach(id=>$(id)?.addEventListener("change",()=>queueMicrotask(renderPerformanceHistory)));
    $("refreshButton")?.addEventListener("click",()=>loadPerformanceHistory());
    loadPerformanceHistory();
  });

  async function loadPerformanceHistory(){
    try{
      const r=await fetch(`data/performance_results.json?ts=${Date.now()}`,{cache:"no-store"});
      if(!r.ok)throw new Error(`performance data: HTTP ${r.status}`);
      performanceData=await r.json();
      if(performanceData.schema_version!=="ng-performance-0.6")return;
      queueMicrotask(renderPerformanceHistory);
    }catch(err){console.error(err);}
  }

  function renderPerformanceHistory(){
    if(!performanceData||!$("performanceDetail"))return;
    const sid=$("perfStreamSelect")?.value;
    const rid=$("perfReleaseSelect")?.value;
    const build=$("perfBuildSelect")?.value;
    if(!sid||!rid||!build)return;

    const definitions=new Map((performanceData.definitions||[]).map(x=>[String(x.performance_test_id),x]));
    const runs=(performanceData.executions||[])
      .filter(x=>String(x.stream_id)===String(sid)&&String(x.release_id)===String(rid)&&String(x.build)===String(build))
      .sort((a,b)=>String(b.executed_at).localeCompare(String(a.executed_at)));

    $("perfRun").textContent=runs.length?`${runs.length} execution${runs.length===1?"":"s"}`:"No executions";
    if(!runs.length){
      $("performanceDetail").innerHTML='<div class="performance-empty"><p class="eyebrow dark">Performance executions</p><h3>No performance executions</h3><p class="muted">No performance test result is available for the selected Release / Build.</p></div>';
      return;
    }

    const passed=runs.filter(x=>x.assessment==="PASSED").length;
    const failed=runs.filter(x=>x.assessment==="FAILED").length;
    const partial=runs.length-passed-failed;
    $("performanceDetail").innerHTML=`
      <section class="performance-history-head">
        <div><p class="eyebrow dark">Performance Testing</p><h3>Execution History</h3><p class="muted">Newest execution first · all recorded runs for the selected Release / Build</p></div>
        <div class="performance-history-summary">
          ${summary("Executions",runs.length,"")}${summary("Passed",passed,"pass")}${summary("Failed",failed,"fail")}${partial?summary("Partial / Other",partial,"amber"):""}
        </div>
      </section>
      <div class="performance-execution-list">${runs.map((run,index)=>executionCard(run,definitions.get(String(run.performance_test_id)),index<2)).join("")}</div>`;
  }

  function summary(label,value,cls){return `<div class="performance-summary-chip ${cls}"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;}

  function executionCard(run,definition,open){
    const assessment=(run.assessment||"UNKNOWN").toUpperCase();
    const cls=assessment==="PASSED"?"pass":assessment==="FAILED"?"fail":"amber";
    const title=definition?.title||run.performance_test_id;
    const objective=definition?.objective||"";
    const scenario=definition?.performance_scenario_id||"—";
    const jira=definition?.jira_key||"—";
    return `<details class="performance-execution-card ${cls}" ${open?"open":""}>
      <summary class="performance-execution-summary">
        <span class="performance-status ${cls}">${esc(assessment)} ${assessment==="PASSED"?"✓":assessment==="FAILED"?"✕":""}</span>
        <span class="performance-run-id">${esc(run.performance_execution_id)}</span><span class="performance-run-title">${esc(title)}</span>
        <span class="performance-run-date">${formatDate(run.executed_at)}</span><span class="performance-toggle">Details</span>
      </summary>
      <div class="performance-execution-body">
        <section class="performance-card-section performance-definition-section"><span class="performance-section-label">Test Definition</span><strong>${esc(title)}</strong><small>${esc(run.performance_test_id)} · ${esc(scenario)}</small><p>${esc(objective)}</p><span class="performance-jira">Jira: ${esc(jira)}</span><span class="performance-by">Executed by ${esc(run.executed_by||"—")}</span></section>
        ${metricSection("Workload",run.workload||{},false,run)}
        ${metricSection("Results",run.results||{},true,run)}
        ${environmentSection(run.environment||{})}${hardwareSection(run.hardware_utilization||[],run)}
        <section class="performance-card-section performance-notes-section"><span class="performance-section-label">Notes</span><p>${esc(run.notes||"—")}</p></section>
      </div>
    </details>`;
  }

  function metricSection(label,data,showStatus,run){
    if(Array.isArray(data)){
      return `<section class="performance-card-section"><span class="performance-section-label">${esc(label)}</span>${data.length?data.map(x=>metricRow(x.name,x.value,x.target,x.status,showStatus)).join(""):'<p class="muted">Not recorded</p>'}</section>`;
    }
    if(data&&typeof data==="object"){
      const rows=Object.entries(data);
      return `<section class="performance-card-section"><span class="performance-section-label">${esc(label)}</span>${rows.length?rows.map(([k,v])=>metricRow(pretty(k),formatMetricValue(k,v),null,inferMetricStatus(k,v,run),showStatus)).join(""):'<p class="muted">Not recorded</p>'}</section>`;
    }
    return `<section class="performance-card-section"><span class="performance-section-label">${esc(label)}</span><p class="muted">Not recorded</p></section>`;
  }

  function metricRow(name,value,target,status,showStatus){
    const cls=showStatus&&status==="FAILED"?"value-fail":showStatus&&status==="PASSED"?"value-pass":"";
    return `<div class="performance-data-row"><span>${esc(name)}</span><strong class="${cls}">${esc(value)}</strong>${target?`<small>Target ${esc(target)}</small>`:""}</div>`;
  }

  function inferMetricStatus(key,value,run){
    const results=run?.results;
    if(!results||Array.isArray(results)||typeof results!=="object")return null;
    const failed=Number(results.failed_transactions||0);
    const target=Number(run?.workload?.target_transactions||0);
    const attempted=Number(results.attempted_transactions||0);
    if(key==="failed_transactions"||key==="transaction_failure_rate_percent")return Number(value)>0?"FAILED":"PASSED";
    if(key==="transaction_pass_rate_percent")return Number(value)>=100?"PASSED":"FAILED";
    if(key==="passed_transactions")return failed===0&&Number(value)>0?"PASSED":failed>0?"FAILED":null;
    if(key==="attempted_transactions")return target>0&&attempted>=target?"PASSED":null;
    return null;
  }

  function formatMetricValue(key,value){
    if(value===null||value===undefined)return"—";
    if(key.endsWith("_percent"))return `${value}%`;
    if(key==="concurrent_users")return String(value);
    if(key==="target_transactions"||key==="attempted_transactions"||key==="passed_transactions"||key==="failed_transactions")return Number(value).toLocaleString("en-US");
    return String(value);
  }

  function environmentSection(env){
    const rows=Object.entries(env);
    return `<section class="performance-card-section"><span class="performance-section-label">Environment</span>${rows.length?rows.map(([k,v])=>`<div class="performance-data-row"><span>${esc(pretty(k))}</span><strong>${esc(v)}</strong></div>`).join(""):'<p class="muted">Not recorded</p>'}</section>`;
  }

  function hardwareSection(components,run){
    if(!components.length)return `<section class="performance-card-section performance-hardware-section"><span class="performance-section-label">Hardware Utilization</span><p class="muted">Not recorded</p></section>`;
    const visible=components.slice(0,2).map(c=>hardwareComponent(c,run)).join("");
    const extra=components.slice(2);
    const more=extra.length?`<details class="hardware-more"><summary>+ ${extra.length} more component${extra.length===1?"":"s"}</summary>${extra.map(c=>hardwareComponent(c,run)).join("")}</details>`:"";
    return `<section class="performance-card-section performance-hardware-section"><span class="performance-section-label">Hardware Utilization</span>${visible}${more}</section>`;
  }

  function hardwareComponent(component,run){
    const metrics=component?.metrics; let rows="";
    if(Array.isArray(metrics)){
      rows=metrics.map(m=>`<div class="performance-data-row"><span>${esc(m.name)}</span><strong class="${m.status==="FAILED"?"value-fail":m.status==="PASSED"?"value-pass":""}">${esc(m.value)}</strong></div>`).join("");
    }else if(metrics&&typeof metrics==="object"){
      rows=Object.entries(metrics).map(([k,v])=>{
        const status=inferHardwareStatus(k,v,run);
        return `<div class="performance-data-row"><span>${esc(pretty(k))}</span><strong class="${status==="FAILED"?"value-fail":status==="PASSED"?"value-pass":""}">${esc(formatMetricValue(k,v))}</strong></div>`;
      }).join("");
    }
    return `<div class="hardware-component"><strong>${esc(component?.component||"Component")}</strong>${rows||'<p class="muted">Not recorded</p>'}</div>`;
  }

  function inferHardwareStatus(key,value,run){
    if(!String(key).toLowerCase().includes("cpu"))return null;
    const n=Number(value);
    if(!Number.isFinite(n))return null;
    if(n>=90)return"FAILED";
    return null;
  }

  function pretty(v){return String(v).replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}
  function formatDate(v){if(!v)return"—";const d=new Date(v);if(Number.isNaN(d.getTime()))return esc(v);return new Intl.DateTimeFormat("en",{year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit",hour12:false}).format(d);}
})();
