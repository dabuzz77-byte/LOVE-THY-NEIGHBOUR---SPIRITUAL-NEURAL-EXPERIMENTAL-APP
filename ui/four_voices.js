import {mountMatterSpirit} from '/matter_spirit.js';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function mountFourVoices(host,api){
 let disposed=false,timer=null,busy=false,presets=null,source=null;
 const q=s=>host.querySelector(s);
 const base=mountMatterSpirit(host,api,{catalogue:'four-voices',section:'gnostic_four',research:'gnostic_four',afterMount:async()=>{
  if(disposed)return;
  q('.ms-page').insertAdjacentHTML('beforeend',`<section class="panel pad" id="fourTools"><h2>Source library and continuous ingestion</h2><p>Read the selected public-domain editions, including surviving gaps. Every character is divided into checked UTF-8 chunks for resumable processing through shared engines. You can pause or resume without opening another app.</p><p id="fourProgress" role="status">Loading library…</p><div class="actions"><button id="fourStart">Keep source learning active</button><button id="fourPause">Pause source ingestion</button></div><label class="field">Read a source<select id="fourSource"><option value="john">Apocryphon of John · long recension</option><option value="mary">Gospel of Mary</option><option value="thomas">Gospel of Thomas</option><option value="dialogue">Dialogue of the Savior</option><option value="bushido">Additional study · Nitobe’s Bushido</option><option value="iching">Additional study · Legge’s complete I Ching</option></select></label><label class="field">Find words in the source<input id="fourQuery" maxlength="160" placeholder="light, knowledge, love…"></label><button id="fourRead">Open full local text / search</button><p id="fourAttribution"></p><div id="fourHits"></div><details><summary>Complete surviving text of this edition</summary><pre id="fourText"></pre></details></section>
  <section class="panel pad" id="fourEngine"><h2>Choose good / life · action engine</h2><p>These are declared assessments of hypothetical proposals. All seven checks must pass. Unknown is represented separately and waits for review. A large claimed benefit cannot overrule a failed check.</p><label class="field">World-system example<select id="fourScenario"></select></label><label class="field">Available resource budget<input id="fourBudget" type="number" min="0" max="10000" step=".5" value="3"></label><div id="fourCandidates"></div><button id="fourRun" class="primary">Compute decision bits and pass through neural system</button><p id="fourStatus" role="status">Ready.</p><div id="fourDecision"></div><details><summary>Exact decision, counterfactuals and shared receipt</summary><pre id="fourTrace"></pre></details></section>`);
  q('.ms-page > section:first-of-type').insertAdjacentHTML('beforeend','<div class="actions"><button id="fourGoLibrary">Read full texts & ingestion status</button><button id="fourGoEngine">Open good-action engine</button></div>');
  q('#fourGoLibrary').onclick=()=>q('#fourTools').scrollIntoView({behavior:'smooth'});q('#fourGoEngine').onclick=()=>q('#fourEngine').scrollIntoView({behavior:'smooth'});
  try{
   presets=await api('four-texts/presets');if(disposed)return;
   q('#fourScenario').innerHTML=Object.entries(presets).map(([id,v])=>`<option value="${id}">${esc(v.title)}</option>`).join('');
   function render(){const rows=presets[q('#fourScenario').value].candidates;q('#fourCandidates').innerHTML=rows.map((row,i)=>`<details ${i===0?'open':''} class="ms-source"><summary>${esc(row.label)}</summary><div class="ms-two">${Object.entries(row.checks).map(([key,value])=>`<label class="field">${esc(key.replaceAll('_',' '))}<select data-check="${key}" data-row="${i}"><option value="true" ${value===true?'selected':''}>Pass</option><option value="false" ${value===false?'selected':''}>Fail</option><option value="unknown" ${value===null?'selected':''}>Unknown / review</option></select></label>`).join('')}${['benefit','need','confidence','cost'].map(k=>`<label class="field">${k}<input data-metric="${k}" data-row="${i}" type="number" min="0" max="${k==='cost'?10000:1}" step=".05" value="${row[k]}"></label>`).join('')}</div></details>`).join('')}
   q('#fourScenario').onchange=render;render();
   async function progress(){try{const v=await api('four-texts');if(!disposed)q('#fourProgress').textContent=`${v.processed_chunks} / ${v.total_chunks} source chunks processed · ${v.enabled?'active':'paused'}${v.error?' · '+v.error:''}`}catch(e){if(!disposed)q('#fourProgress').textContent=e.message}}
   q('#fourStart').onclick=async()=>{await api('four-texts/configure',{enabled:true});if(!disposed)progress()};q('#fourPause').onclick=async()=>{await api('four-texts/configure',{enabled:false});if(!disposed)progress()};
   q('#fourRead').onclick=async()=>{try{const v=await api('four-texts/source?id='+q('#fourSource').value+'&q='+encodeURIComponent(q('#fourQuery').value));if(disposed)return;source=v;q('#fourText').textContent=v.text;q('#fourText').closest('details').open=true;q('#fourAttribution').textContent=v.source.translator+' · SHA-256 '+v.source.sha256;q('#fourHits').innerHTML=v.hits.map(h=>'<p>'+esc(h.excerpt)+'</p>').join('')||(q('#fourQuery').value?'No matches.':'Full text opened below.')}catch(e){if(!disposed)q('#fourAttribution').textContent=e.message}};
   q('#fourRun').onclick=async()=>{
    if(busy)return;busy=true;q('#fourRun').disabled=true;
    try{
     const rows=JSON.parse(JSON.stringify(presets[q('#fourScenario').value].candidates));
     host.querySelectorAll('[data-check]').forEach(el=>rows[Number(el.dataset.row)].checks[el.dataset.check]=el.value==='unknown'?null:el.value==='true');
     host.querySelectorAll('[data-metric]').forEach(el=>rows[Number(el.dataset.row)][el.dataset.metric]=Number(el.value));
     const job=await api('run',{section:'pipeline',input:{text:'Four voices: evaluate declared action proposals by truth, care, consent and repair.',sections:['gnostic_four','virtue_text','reference','inference'],section_inputs:{gnostic_four:{lesson:'engine',candidates:rows,budget:Number(q('#fourBudget').value)}}}});
     if(disposed)return;q('#fourStatus').textContent='Processing source-based teaching, checks and exact decision bits…';
     for(let i=0;i<240&&!disposed;i++){
      await new Promise(r=>setTimeout(r,250));if(disposed)return;const v=await api('job?id='+job.id);if(disposed)return;
      if(v.status==='error')throw Error(v.error);
      if(v.status==='complete'){
       const d=v.result.stages.gnostic_four.decision;q('#fourStatus').textContent=`Receipt ${v.receipt} · ${d.selected?'selected '+d.selected:'No candidate qualifies; review required'} · ${v.result.learning.updates} shared learning updates`;
       q('#fourDecision').innerHTML=`<p><b>Eligibility:</b> ${esc(d.eligibility_bits)} · <b>Selection:</b> ${esc(d.selection_bits)} · exact round trip ${d.round_trip?'passed':'failed'}</p><p>Check order: ${esc(d.checks.join(' · '))}</p>`+d.actions.map(a=>`<div class="ms-source"><h3>${esc(a.label)}</h3><p>Pass bits: <b>${a.check_bits}</b> · Known bits: <b>${a.known_bits}</b></p><p>${a.eligible?'Eligible; score '+a.score:esc(a.reasons.join('; '))}</p></div>`).join('')+`<p>${d.counterfactual_changes.length} single-check changes would change the selected action.</p><p>${esc(d.scope)}</p>`;
       q('#fourTrace').textContent=JSON.stringify(v,null,2);return;
      }
     }
     if(!disposed)q('#fourStatus').textContent='Still queued; inspect Results & feedback.';
    }catch(e){if(!disposed)q('#fourStatus').textContent=e.message}finally{busy=false;if(!disposed)q('#fourRun').disabled=false}
   };
   progress();timer=setInterval(()=>{if(!document.hidden)progress()},2000);
  }catch(e){if(!disposed)q('#fourProgress').textContent=e.message}
 }});
 return()=>{disposed=true;clearInterval(timer);base()};
}
