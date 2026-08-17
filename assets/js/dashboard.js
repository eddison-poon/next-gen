(() => {
  "use strict";
  const ENVIRONMENTS=["DEV","SIT","UAT","PPD","PROD"];
  const state={payload:null,snapshot:null,selectedItem:null,selectedFeature:null,search:"",automation:null,selectedCapability:null,performance:null,perfSnapshot:null};
  const $=id=>document.getElementById(id);

  document.addEventListener("DOMContentLoaded",()=>{bindTabs();bindEvents();loadData();loadAutomation();loadPerformance();});
  function bindTabs(){document.querySelectorAll(".rail-link").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".rail-link").forEach(x=>x.classList.toggle("active",x===btn));document.querySelectorAll(".tab-panel").forEach(x=>x.classList.remove("active"));$(btn.dataset.tab+"Tab").classList.add("active");}));}
  function bindEvents(){
    $("streamSelect").addEventListener("change",()=>selectFromControls("stream"));
    $("releaseSelect").addEventListener("change",()=>selectFromControls("release"));
    $("buildSelect").addEventListener("change",()=>selectFromControls("build"));
    $("releaseSearch").addEventListener("input",e=>{state.search=e.target.value.trim().toLowerCase();renderItems();});
    $("refreshButton").addEventListener("click",()=>{loadData();loadAutomation();loadPerformance();});
    $("perfStreamSelect").addEventListener("change",()=>selectPerformance("stream"));
    $("perfReleaseSelect").addEventListener("change",()=>selectPerformance("release"));
    $("perfBuildSelect").addEventListener("change",()=>selectPerformance("build"));
  }

  async function loadData(){
    try{
      const r=await fetch(`data/generated/release_focus_snapshot.json?ts=${Date.now()}`,{cache:"no-store"});
      if(!r.ok)throw new Error(`snapshot: HTTP ${r.status}`);
      state.payload=await r.json();
      const s=state.payload.selected;
      state.snapshot=findSnapshot(s.stream_id,s.release_id,s.build)||state.payload.snapshots[0];
      selectFirstItem();render();
    }catch(err){
      console.error(err);
      $("releaseDetail").innerHTML=`<div class="muted">Unable to load generated Release Focus snapshot: ${esc(err.message)}</div>`;
    }
  }
  function findSnapshot(streamId,releaseId,build){return state.payload.snapshots.find(x=>x.stream.id===streamId&&x.release.id===releaseId&&x.release.build===build)}
  function streams(){return [...new Map(state.payload.snapshots.map(x=>[x.stream.id,x.stream])).values()]}
  function releasesFor(streamId){return [...new Map(state.payload.snapshots.filter(x=>x.stream.id===streamId).map(x=>[x.release.id,{id:x.release.id,name:x.release.name}])).values()]}
  function buildsFor(streamId,releaseId){return state.payload.snapshots.filter(x=>x.stream.id===streamId&&x.release.id===releaseId).map(x=>x.release.build)}
  function selectFirstItem(){state.selectedItem=state.snapshot.release_items[0]||null;state.selectedFeature=state.selectedItem?.features[0]||null}
  function selectFromControls(changed){
    let streamId=$("streamSelect").value,releaseId=$("releaseSelect").value,build=$("buildSelect").value;
    if(changed==="stream"){releaseId=releasesFor(streamId)[0]?.id;build=buildsFor(streamId,releaseId)[0]}
    if(changed==="release"){build=buildsFor(streamId,releaseId)[0]}
    state.snapshot=findSnapshot(streamId,releaseId,build)||state.payload.snapshots[0];
    selectFirstItem();render();
  }

  function render(){renderContext();renderKPIs();renderExecution();renderEnvironments();renderItems();renderDetail()}
  function renderContext(){
    $("snapshotChip").textContent=`Snapshot ${formatDate(state.payload.generated_at)}`;
    const streamId=state.snapshot.stream.id,releaseId=state.snapshot.release.id,build=state.snapshot.release.build;
    $("streamSelect").innerHTML=streams().map(x=>`<option value="${x.id}" ${x.id===streamId?"selected":""}>${esc(x.name)}</option>`).join("");
    $("releaseSelect").innerHTML=releasesFor(streamId).map(x=>`<option value="${x.id}" ${x.id===releaseId?"selected":""}>${esc(x.name)}</option>`).join("");
    $("buildSelect").innerHTML=buildsFor(streamId,releaseId).map(x=>`<option ${x===build?"selected":""}>${esc(x)}</option>`).join("");
    $("scopeCount").textContent=`${state.snapshot.release.release_item_count} Release Items`;
  }

  function renderKPIs(){
    const k=state.snapshot.kpis;
    const health=(k.overall_health||"Not Available").toLowerCase().replace("_"," ");
    const cards=[
      ["Overall Health",title(k.overall_health),health,"Manual release-governing signal"],
      ["Release Test Coverage",`${k.release_test_coverage}%`,"",`${k.executed} / ${k.total_applicable_gates} applicable scenario-environment gates`],
      ["Execution Progress",`${k.execution_progress}%`,"",`${k.executed} / ${k.total_applicable_gates} Manual scenario-environment executions`],
      ["Pass Rate",k.pass_rate==null?"—":`${k.pass_rate}%`,k.pass_rate>=80?"green":k.pass_rate>=50?"amber":"red",`${k.passed} passed / ${k.passed+k.failed} completed Pass/Fail`],
      ["Executed",k.executed,"","Manual scenario-environment results"],
      ["Passed",k.passed,"green","Manual scenario-environment results"],
      ["Failed",k.failed,k.failed?"red":"green","Manual scenario-environment results"],
      ["Blocked",k.blocked,k.blocked?"amber":"","Manual scenario-environment results"],
      ["Not Executed",k.not_executed,"","Manual scenario-environment results"]
    ];
    $("kpiGrid").innerHTML=cards.map(([l,v,h,d])=>`<article class="kpi-card ${h?`health-${h}`:""}"><span class="label">${esc(l)}</span><strong>${esc(String(v))}</strong><small>${esc(d)}</small></article>`).join("");
  }

  function renderExecution(){
    const k=state.snapshot.kpis;
    $("executionProgress").innerHTML=`<div class="progress-head"><div><p class="eyebrow dark">Manual execution</p><h3>Test Execution Progress</h3></div><span class="muted">${k.execution_progress}% complete · ${k.pass_rate??"—"}% pass rate</span></div><div class="bar"><div class="bar-fill" style="width:${k.execution_progress}%"></div></div><div class="status-row">${[["Executed",k.executed],["Passed",k.passed],["Failed",k.failed],["Blocked",k.blocked],["Not Executed",k.not_executed]].map(([l,v])=>`<div class="status-cell"><span>${l}</span><strong>${v}</strong></div>`).join("")}</div>`;
  }

  function renderEnvironments(){
    $("environmentGrid").innerHTML=state.snapshot.environment_health.map(e=>{
      const cls=e.executed===0?"grey":(e.pass_rate??0)>=80?"green":(e.pass_rate??0)>=50?"amber":"red";
      const readiness=e.readiness==="READY"?"ready":e.readiness==="IN_PROGRESS"?"partial":"not-started";
      return`<div class="env-box"><div class="env-top"><span class="env-name">${e.environment}</span><strong class="env-rate ${cls}">${e.pass_rate==null?"—":e.pass_rate+"%"}</strong></div><div class="env-stats"><div><span>Executed</span><strong>${e.executed}</strong></div><div><span>Passed</span><strong>${e.passed}</strong></div><div><span>Failed / Blocked</span><strong>${e.failed} / ${e.blocked}</strong></div></div><span class="readiness ${readiness}">${title(e.readiness)}</span></div>`;
    }).join("");
  }

  function renderItems(){
    const term=state.search,items=state.snapshot.release_items.filter(x=>!term||`${x.jira_key} ${x.summary}`.toLowerCase().includes(term));
    $("releaseItemCount").textContent=state.snapshot.release_items.length;
    $("releaseItems").innerHTML=items.length?items.map(i=>`<button class="release-item ${i===state.selectedItem?"active":""}" data-key="${i.jira_key}"><span><span class="release-key">${esc(i.jira_key)}</span><span class="release-summary">${esc(i.summary)}</span><span class="release-meta">${i.features.length} feature${i.features.length===1?"":"s"} · ${esc(i.issue_type)}</span></span><i class="item-state ${healthClass(i.health)}"></i></button>`).join(""):`<div class="muted" style="padding:18px">No matching release items.</div>`;
    document.querySelectorAll(".release-item").forEach(b=>b.addEventListener("click",()=>{state.selectedItem=state.snapshot.release_items.find(x=>x.jira_key===b.dataset.key);state.selectedFeature=state.selectedItem.features[0]||null;renderItems();renderDetail()}));
  }

  function mark(status){if(status==="N/A")return["N/A","na"];if(status==="PASSED")return["✓","pass"];if(status==="FAILED")return["✕","fail"];if(status==="BLOCKED")return["!","blocked"];return["—","none"]}
  function renderDetail(){
    const item=state.selectedItem;if(!item){$("releaseDetail").innerHTML=`<div class="muted">No release item selected.</div>`;return}
    const rows=item.features.map(f=>`<div class="feature-row ${f===state.selectedFeature?"active":""}" data-feature="${f.id}"><div class="feature-name"><strong>${esc(f.name)}</strong><small>${esc(f.scenario.title)}</small></div>${ENVIRONMENTS.map(e=>{const[m,c]=mark(f.environment_status[e]);return`<span class="env-mark ${c}">${m}</span>`}).join("")}</div>`).join("");
    $("releaseDetail").innerHTML=`<div class="item-overview"><div><p class="eyebrow dark">Selected Release Item</p><h3 class="detail-title">${esc(item.summary)}</h3><div class="issue-meta"><span>${esc(item.issue_type)}</span><span>${item.features.length} features</span></div></div><a class="jira-link" href="${escAttr(item.jira_url)}" target="_blank" rel="noopener">${esc(item.jira_key)} ↗</a></div><div class="feature-list"><div class="feature-header"><span>Feature</span>${ENVIRONMENTS.map(e=>`<span>${e}</span>`).join("")}</div>${rows}</div><div id="selectedFeatureArea"></div>`;
    document.querySelectorAll(".feature-row").forEach(r=>r.addEventListener("click",()=>{state.selectedFeature=item.features.find(x=>x.id===r.dataset.feature);renderDetail()}));
    renderSelectedFeature();
  }
  function renderSelectedFeature(){
    const f=state.selectedFeature;if(!f)return;
    $("selectedFeatureArea").innerHTML=`<section class="selected-feature"><p class="eyebrow dark">Selected Feature</p><h4>${esc(f.name)}</h4><table class="scenario-table"><thead><tr><th>Scenario / Manual Test</th>${ENVIRONMENTS.map(e=>`<th>${e}</th>`).join("")}<th>Jira</th></tr></thead><tbody><tr><td><span class="scenario-name">${esc(f.scenario.title)}</span><span class="scenario-id">${esc(f.scenario.id)} · ${esc(f.scenario.manual_test_id)}</span></td>${ENVIRONMENTS.map(e=>{const[m,c]=mark(f.environment_status[e]);return`<td><span class="env-mark ${c}">${m}</span></td>`}).join("")}<td><a class="jira-link" href="${escAttr(state.selectedItem.jira_url)}">${esc(state.selectedItem.jira_key)}</a></td></tr></tbody></table><div class="legend"><span><b>✓</b> Passed</span><span><b>✕</b> Failed</span><span><b>!</b> Blocked</span><span><b>—</b> Not Executed</span><span><b>N/A</b> Not Applicable</span></div></section>`;
  }


  async function loadAutomation(){
    const r=await fetch(`data/automation_regression.json?ts=${Date.now()}`,{cache:"no-store"});if(!r.ok)return;
    state.automation=await r.json();state.selectedCapability=state.automation.capabilities[0]||null;renderAutomation();
  }
  function automationScenarios(){return state.automation?.capabilities.flatMap(c=>c.features.flatMap(f=>f.scenarios.map(s=>({c,f,s}))))||[]}
  function autoStatus(s,e){return s.applicable_environments.includes(e)?(s.results[e]||"NOT_EXECUTED"):"N/A"}
  function autoCoverage(rows){const a=rows.flatMap(x=>ENVIRONMENTS.filter(e=>autoStatus(x.s,e)!=="N/A").map(e=>autoStatus(x.s,e)));const ex=a.filter(x=>x!=="NOT_EXECUTED");return{applicable:a.length,executed:ex.length,coverage:a.length?Math.round(ex.length/a.length*1000)/10:0,passed:ex.filter(x=>x==="PASSED").length,failed:ex.filter(x=>x==="FAILED").length,blocked:ex.filter(x=>x==="BLOCKED").length}}
  function featureAutoMark(f,e){const s=f.scenarios.map(x=>autoStatus(x,e)).filter(x=>x!=="N/A");if(!s.length)return["N/A","na"];if(s.every(x=>x==="PASSED"))return["✓","pass"];if(s.some(x=>x==="FAILED"))return["✕","fail"];if(s.some(x=>x==="BLOCKED"))return["!","blocked"];return["—","none"]}
  function renderAutomation(){
    if(!state.automation)return;const rows=automationScenarios(),s=autoCoverage(rows);
    $("automationSummary").innerHTML=[["Automation Coverage",`${s.coverage}%`,`${s.executed} / ${s.applicable} applicable gates`],["Automated Scenarios",rows.length,"Regression scenarios"],["Passed Results",s.passed,"Latest environment results"],["Failed / Blocked",`${s.failed} / ${s.blocked}`,"Supporting signal"]].map(x=>`<div class="automation-card"><span>${x[0]}</span><strong>${x[1]}</strong><small>${x[2]}</small></div>`).join("");
    $("automationEnvironmentGrid").innerHTML=ENVIRONMENTS.map(e=>{const a=rows.filter(x=>autoStatus(x.s,e)!=="N/A"),ex=a.filter(x=>autoStatus(x.s,e)!=="NOT_EXECUTED"),cv=a.length?Math.round(ex.length/a.length*1000)/10:0;return`<div class="env-box"><div class="env-top"><span class="env-name">${e}</span><strong class="env-rate">${a.length?cv+"%":"—"}</strong></div><div class="env-stats"><div><span>Applicable</span><strong>${a.length}</strong></div><div><span>Executed</span><strong>${ex.length}</strong></div><div><span>Coverage</span><strong>${a.length?cv+"%":"N/A"}</strong></div></div><span class="readiness ${cv===100?"ready":ex.length?"partial":"not-started"}">${!a.length?"N/A":cv===100?"Covered":ex.length?"Partial":"Not Started"}</span></div>`}).join("");
    $("capabilityCount").textContent=state.automation.capabilities.length;
    $("capabilityItems").innerHTML=state.automation.capabilities.map(c=>{const cs=autoCoverage(c.features.flatMap(f=>f.scenarios.map(s=>({c,f,s}))));return`<button class="release-item ${c===state.selectedCapability?"active":""}" data-cap="${c.id}"><span><span class="release-key">${esc(c.name)}</span><span class="release-summary">${c.features.length} features</span><span class="release-meta">${cs.coverage}% automation coverage</span></span><i class="item-state ${cs.failed?"red":cs.blocked?"amber":cs.coverage===100?"green":"amber"}"></i></button>`}).join("");
    document.querySelectorAll("[data-cap]").forEach(b=>b.addEventListener("click",()=>{state.selectedCapability=state.automation.capabilities.find(c=>c.id===b.dataset.cap);renderAutomation()}));
    renderCapabilityDetail();
  }
  function renderCapabilityDetail(){
    const c=state.selectedCapability;if(!c){$("capabilityDetail").innerHTML='<div class="muted">No capability selected.</div>';return}
    $("capabilityDetail").innerHTML=`<div class="item-overview"><div><p class="eyebrow dark">Selected Capability</p><h3 class="detail-title">${esc(c.name)}</h3><p class="capability-description">${esc(c.description)}</p></div></div>${c.features.map(f=>`<section class="capability-feature"><div class="capability-feature-head"><strong>${esc(f.name)}</strong>${ENVIRONMENTS.map(e=>{const[m,cl]=featureAutoMark(f,e);return`<span class="env-mark ${cl}">${m}</span>`}).join("")}</div><table class="auto-scenario-table"><thead><tr><th>Automated Scenario</th>${ENVIRONMENTS.map(e=>`<th>${e}</th>`).join("")}</tr></thead><tbody>${f.scenarios.map(s=>`<tr><td><strong>${esc(s.name)}</strong><br><span class="muted">${esc(s.automation_test_id)}</span></td>${ENVIRONMENTS.map(e=>{const[m,cl]=mark(autoStatus(s,e));return`<td><span class="env-mark ${cl}">${m}</span></td>`}).join("")}</tr>`).join("")}</tbody></table></section>`).join("")}`;
  }

  async function loadPerformance(){
    const r=await fetch(`data/performance_results.json?ts=${Date.now()}`,{cache:"no-store"});if(!r.ok)return;
    state.performance=await r.json();renderPerformanceControls();
  }
  function selectPerformance(changed){
    let sid=$("perfStreamSelect").value,rid=$("perfReleaseSelect").value,b=$("perfBuildSelect").value;
    const all=state.payload.snapshots;
    if(changed==="stream"){const x=all.find(x=>x.stream.id===sid);rid=x?.release.id;b=x?.release.build}
    if(changed==="release"){const x=all.find(x=>x.stream.id===sid&&x.release.id===rid);b=x?.release.build}
    state.perfSnapshot=all.find(x=>x.stream.id===sid&&x.release.id===rid&&x.release.build===b)||all[0];renderPerformanceControls();
  }
  function renderPerformanceControls(){
    if(!state.performance||!state.payload)return;if(!state.perfSnapshot)state.perfSnapshot=state.snapshot;
    const sid=state.perfSnapshot.stream.id,rid=state.perfSnapshot.release.id,b=state.perfSnapshot.release.build;
    $("perfStreamSelect").innerHTML=streams().map(x=>`<option value="${x.id}" ${x.id===sid?"selected":""}>${esc(x.name)}</option>`).join("");
    $("perfReleaseSelect").innerHTML=releasesFor(sid).map(x=>`<option value="${x.id}" ${x.id===rid?"selected":""}>${esc(x.name)}</option>`).join("");
    $("perfBuildSelect").innerHTML=buildsFor(sid,rid).map(x=>`<option ${x===b?"selected":""}>${esc(x)}</option>`).join("");
    const r=state.performance.results.find(x=>x.stream_id===sid&&x.release_id===rid&&x.build===b);$("perfRun").textContent=r?.test_run||"No result";
    if(!r){$("performanceDetail").innerHTML='<div class="muted">No performance test result is available for the selected Release / Build.</div>';return}
    $("performanceDetail").innerHTML=`<div class="performance-head"><div><p class="eyebrow dark">Latest Performance Result</p><h3>${esc(r.test_run)}</h3><p class="muted">${esc(r.summary)}</p></div><span class="performance-assessment ${r.assessment.toLowerCase()}">${esc(r.assessment)}</span></div><div class="performance-metrics">${r.metrics.map(m=>`<div class="performance-metric"><span>${esc(m.name)}</span><strong>${esc(m.value)}</strong><small>Target: ${esc(m.target)}</small><div class="metric-status ${m.status==="PASSED"?"pass":"fail"}">${m.status==="PASSED"?"✓ Passed":"✕ Failed"}</div></div>`).join("")}</div>`;
  }

  function healthClass(v){return v==="RED"?"red":v==="AMBER"?"amber":v==="GREEN"?"green":"grey"}
  function title(v){return String(v??"").toLowerCase().replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())}
  function formatDate(v){const d=new Date(v);return new Intl.DateTimeFormat("en",{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit",hour12:false}).format(d)}
  function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}
  function escAttr(v){return esc(v)}
})();