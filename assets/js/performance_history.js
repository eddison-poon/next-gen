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
    }catch(err){
      console.error(err);
    }
  }

  function renderPerformanceHistory(){
    if(!performanceData||!$("performanceDetail"))return;
    const sid=$("perfStreamSelect")?.value;
    const rid=$("perfReleaseSelect")?.value;
    const build=$("perfBuildSelect")?.value;
    if(!sid||!rid||!build)return;

    const definitions=new Map((performanceData.definitions||[]).map(x=>[x.performance_test_id,x]));
    const runs=(performanceData.executions||[])
      .filter(x=>x.stream_id===sid&&x.release_id===rid&&x.build===build)
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
          ${summary("Executions",runs.length,"")}
          ${summary("Passed",passed,"pass")}
          ${summary("Failed",failed,"fail")}
          ${partial?summary("Partial / Other",partial,"amber"):""}
        </div>
      </section>
      <div class="performance-execution-list">
        ${runs.map((run,index)=>executionCard(run,definitions.get(run.performance_test_id),index<2)).join("")}
      </div>`;
  }

  function summary(label,value,cls){
    return `<div class="performance-summary-chip ${cls}"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
  }

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
        <span class="performance-run-id">${esc(run.performance_execution_id)}</span>
        <span class="performance-run-title">${esc(title)}</span>
        <span class="performance-run-date">${formatDate(run.executed_at)}</span>
        <span class="performance-toggle">Details</span>
      </summary>
      <div class="performance-execution-body">
        <section class="performance-card-section performance-definition-section">
          <span class="performance-section-label">Test Definition</span>
          <strong>${esc(title)}</strong>
          <small>${esc(run.performance_test_id)} · ${esc(scenario)}</small>
          <p>${esc(objective)}</p>
          <span class="performance-jira">Jira: ${esc(jira)}</span>
          <span class="performance-by">Executed by ${esc(run.executed_by||"—")}</span>
        </section>
        ${metricSection("Workload",run.workload||[],false)}
        ${metricSection("Results",run.results||[],true)}
        ${environmentSection(run.environment||{})}
        ${hardwareSection(run.hardware_utilization||[])}
        <section class="performance-card-section performance-notes-section">
          <span class="performance-section-label">Notes</span>
          <p>${esc(run.notes||"—")}</p>
        </section>
      </div>
    </details>`;
  }

  function metricSection(label,rows,showStatus){
    return `<section class="performance-card-section"><span class="performance-section-label">${esc(label)}</span>${rows.length?rows.map(x=>`<div class="performance-data-row"><span>${esc(x.name)}</span><strong class="${showStatus&&x.status==="FAILED"?"value-fail":showStatus&&x.status==="PASSED"?"value-pass":""}">${esc(x.value)}</strong>${x.target?`<small>Target ${esc(x.target)}</small>`:""}</div>`).join(""):'<p class="muted">Not recorded</p>'}</section>`;
  }

  function environmentSection(env){
    const rows=Object.entries(env);
    return `<section class="performance-card-section"><span class="performance-section-label">Environment</span>${rows.length?rows.map(([k,v])=>`<div class="performance-data-row"><span>${esc(pretty(k))}</span><strong>${esc(v)}</strong></div>`).join(""):'<p class="muted">Not recorded</p>'}</section>`;
  }

  function hardwareSection(components){
    return `<section class="performance-card-section performance-hardware-section"><span class="performance-section-label">Hardware Utilization</span>${components.length?components.map(c=>`<div class="hardware-component"><strong>${esc(c.component)}</strong>${(c.metrics||[]).map(m=>`<div class="performance-data-row"><span>${esc(m.name)}</span><strong>${esc(m.value)}</strong></div>`).join("")}</div>`).join(""):'<p class="muted">Not recorded</p>'}</section>`;
  }

  function pretty(v){return String(v).replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}
  function formatDate(v){
    if(!v)return"—";
    const d=new Date(v);
    if(Number.isNaN(d.getTime()))return esc(v);
    return new Intl.DateTimeFormat("en",{year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit",hour12:false}).format(d);
  }
})();
