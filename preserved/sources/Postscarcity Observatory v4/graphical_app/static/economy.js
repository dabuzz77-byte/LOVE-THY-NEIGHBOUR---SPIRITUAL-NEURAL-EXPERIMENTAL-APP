'use strict';
titleMap.economy='Economic engines';
const economySection=document.createElement('section');
economySection.id='economy';economySection.className='view';
economySection.innerHTML=v3Heading('THREE ENGINES · ONE WORKSPACE','Economic engines','Benefits, central banking and restitution — original rules with shared controls and recorded results.')+`
<article class="panel economy-toolbar"><div><strong>Local calculations · generated metrics</strong><p>Target names are scenario labels. These engines do not connect to banks, benefits services or gambling accounts.</p></div><div class="button-row"><button class="button primary" data-economy-all="run">Run all once</button><button class="button" data-economy-all="start">Loop all</button><button class="button" data-economy-all="pause">Pause all</button><button class="button" id="economy-export">Export results</button></div><p id="economy-global" role="status"></p></article>
<div id="economy-cards" class="economy-cards"></div><p id="economy-log-path" class="muted"></p>`;
$('main footer').before(economySection);
const economyNav=document.createElement('button');economyNav.dataset.view='economy';economyNav.innerHTML='<span>▥</span> Economic engines';
$('nav').append(economyNav);economyNav.onclick=()=>{showView('economy');economyRefresh().catch(e=>toast(e.message));};
let economyData=null,economyLoading=false,economyAction=false;

function economyCard(row){
 const article=document.createElement('article');article.className='panel economy-card';article.id='economy-'+row.id;
 article.innerHTML=`<header><div class="eyebrow">${escapeHTML(row.module)}</div><h2>${escapeHTML(row.title)}</h2><span class="economy-status" role="status">Ready</span></header>
 <label>Scenario target<input class="economy-target" list="economy-options-${row.id}" maxlength="300"><datalist id="economy-options-${row.id}">${row.targets.map(t=>`<option value="${escapeHTML(t)}">`).join('')}</datalist></label>
 <label>Text input<textarea class="economy-payload" rows="6" maxlength="12000" spellcheck="false"></textarea></label>
 <div class="button-row"><button class="button primary" data-action="run">Run once</button><button class="button" data-action="start">Start loop</button><button class="button" data-action="pause">Pause</button><button class="button" data-action="reset">Reset</button></div>
 <div class="economy-rails"><label>Track A · progression</label><div class="economy-bits" data-rail="rail_a"></div><label>Track B · refinery</label><div class="economy-bits" data-rail="rail_b"></div></div>
 <div class="economy-metrics"></div><canvas class="economy-chart" width="460" height="110" aria-label="Recent generated metric history"></canvas>
 <details><summary>Result and original source trace</summary><pre class="bb-output economy-output" tabindex="0">Run a cycle to record results.</pre></details>
 <details><summary>Edit starting state / reproducible seed</summary><p>Use an integer seed to repeat generated draws, or null for the original random behavior. Save while paused between cycles.</p><textarea class="economy-state" rows="8" spellcheck="false" aria-label="Starting state JSON"></textarea><button class="button" data-action="state">Save starting state</button></details>
 <div class="button-row"><button class="button" data-action="source">Read full module</button><button class="button" data-action="export">Export this engine</button></div><p class="economy-error" role="alert"></p>`;
 $('.economy-target',article).value=row.inputs.target;$('.economy-payload',article).value=row.inputs.payload;
 const state={...row.inputs};delete state.target;delete state.payload;$('.economy-state',article).value=JSON.stringify(state,null,2);
 article.addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(b)economyPerform(row.id,b.dataset.action).catch(err=>toast(err.message));});
 return article;
}

function economyDownload(value,filename){const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

async function economySave(id,advanced=false){
 const row=economyData.engines.find(r=>r.id===id),card=$('#economy-'+id);
 const inputs={...row.inputs,...(advanced?JSON.parse($('.economy-state',card).value):{}),target:$('.economy-target',card).value,payload:$('.economy-payload',card).value};
 economyData=await api('/api/economy',{engine:id,action:'save',inputs});
}

async function economyPerform(id,action){
 if(economyAction)return;
 const row=economyData?.engines.find(r=>r.id===id);if(!row)return;
 if(action==='source'){await openModule(row.module);return;}
 if(action==='export'){economyDownload(row,row.module+'-results.json');return;}
 economyAction=true;
 try{
  if(['run','start','state'].includes(action))await economySave(id,action==='state');
  if(action!=='state')economyData=await api('/api/economy',{engine:id,action});
  economyRender();
  if(action==='reset'||action==='state'){const state={...economyData.engines.find(r=>r.id===id).inputs};delete state.payload;delete state.target;$('#economy-'+id+' .economy-state').value=JSON.stringify(state,null,2);}
 }finally{economyAction=false;}
}

function economyRender(){
 if(!economyData)return;
 for(const row of economyData.engines){
  let card=$('#economy-'+row.id);if(!card){card=economyCard(row);$('#economy-cards').append(card);}
  $('.economy-status',card).textContent=(row.busy?'Computing':row.running?(economyData.global_running?'Loop active':'Loop waiting · global pause'):'Paused')+' · '+row.cycles+' recorded cycles';
  $('.economy-error',card).textContent=row.error||'';
  for(const key of ['rail_a','rail_b']){const rail=$('[data-rail="'+key+'"]',card);if(!rail.children.length)rail.innerHTML=Array.from({length:8},()=>'<span class="economy-bit">0</span>').join('');row.inputs[key].forEach((bit,i)=>{const cell=rail.children[i];cell.textContent=bit;cell.dataset.bit=bit;});}
  const result=row.last_result,m=result?.metrics||{};
  const pairs=row.id==='banking'?[['Phase',m.phase??row.inputs.phase],['Generated stability',(m.transition_stability??row.inputs.transition_stability).toFixed(1)+'%'],['Generated leverage',(m.elite_leverage??row.inputs.elite_leverage).toFixed(1)+'%'],['Generated abundance',(m.perimeter_abundance??row.inputs.perimeter_abundance).toFixed(1)]]:
    [['Rule state',result?.state||'Ready'],['Generated weight',m.generated_weight??'—'],[row.id==='benefits'?'Generated bps':'Generated outflow',m.generated_bps??m.generated_outflow??'—']];
  $('.economy-metrics',card).innerHTML=pairs.map(([k,v])=>`<div><small>${escapeHTML(k)}</small><strong>${escapeHTML(String(v))}</strong></div>`).join('');
  const output=$('.economy-output',card),next=JSON.stringify(result||{status:'Awaiting first cycle'},null,2);if(output.textContent!==next){const top=output.scrollTop,bottom=output.scrollHeight-output.clientHeight-top<12;output.textContent=next;output.scrollTop=bottom?output.scrollHeight:top;}
  $$('[data-action]',card).forEach(b=>{b.disabled=row.busy&&['run','start','reset','state'].includes(b.dataset.action);});
  const canvas=$('.economy-chart',card),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
  const values=row.history.map(h=>h.metrics[row.id==='banking'?'perimeter_abundance':row.id==='benefits'?'generated_bps':'generated_outflow']).filter(Number.isFinite).slice(-80);
  ctx.fillStyle='#8ba59e';ctx.font='12px sans-serif';ctx.fillText('Generated '+(row.id==='banking'?'abundance':row.id==='benefits'?'throughput':'outflow')+' · recent cycles',12,17);
  if(values.length){const max=Math.max(...values,1),min=Math.min(...values,0);ctx.strokeStyle='#75e3bd';ctx.lineWidth=2;ctx.beginPath();values.forEach((v,i)=>{const x=12+i/Math.max(1,values.length-1)*(canvas.width-24),y=canvas.height-12-(v-min)/(max-min)*(canvas.height-42);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}
 }
 $('#economy-global').textContent='Loops use the existing worker pool and primary cascade. '+(economyData.global_running?'Automatic scheduling is enabled.':'Global scheduling is paused; Run once remains available.');
 $('#economy-log-path').textContent='Recorded locally: '+economyData.log_path;
 $$('[data-economy-all]').forEach(b=>{b.disabled=b.dataset.economyAll!=='pause'&&economyData.engines.some(r=>r.busy);});
}

async function economyRefresh(){if(economyLoading||economyAction||activeView!=='economy')return;economyLoading=true;try{economyData=await api('/api/economy');economyRender();}finally{economyLoading=false;}}
$$('[data-economy-all]').forEach(b=>b.onclick=async()=>{if(economyAction||!economyData)return;economyAction=true;try{const action=b.dataset.economyAll;if(action!=='pause')for(const row of economyData.engines)await economySave(row.id);economyData=await api('/api/economy',{engine:'all',action});economyRender();}catch(e){toast(e.message);}finally{economyAction=false;}});
$('#economy-export').onclick=()=>{if(economyData)economyDownload(economyData,'economic-engines-results.json');};
setInterval(()=>economyRefresh().catch(e=>toast(e.message)),1200);
if(location.hash==='#economy'){showView('economy');economyRefresh().catch(e=>toast(e.message));}
