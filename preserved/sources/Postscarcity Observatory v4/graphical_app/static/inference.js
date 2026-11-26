'use strict';
titleMap.inference='Inference engine';
const inferenceSection=document.createElement('section');inferenceSection.id='inference';inferenceSection.className='view';
inferenceSection.innerHTML=v3Heading('REAL MODEL EXECUTION · SAVED RECEIPTS','Inference engine','Ask the model to reason over your request, the shared neural rules, live system state and selected evidence.')+`
<div class="v3-grid"><form id="inference-form" class="panel extension-form"><h2>Input</h2><label>Model<select name="provider"><option value="llama">Llama 3 · local</option><option value="gemini">Gemini · configured account</option><option value="chatgpt">ChatGPT · configured account</option></select></label><p id="inference-model-state" role="status"></p><label>Request<textarea name="prompt" maxlength="4000" required placeholder="What can we do with the available evidence and resources to raise the human and ecological floor?"></textarea></label><label>Evidence sources<select id="inference-sources" multiple size="5"></select></label><small>Choose up to three sources in total, including latest research when selected.</small><label class="check"><input name="latest_research" type="checkbox"> Include the latest Internet watch report</label>${v3Button('Run inference')}<p>Local Llama runs on this computer. A selected cloud model receives your request and chosen evidence through your Windows/VPN network route; configure its key in its model panel first.</p><p>All shared rules and all module identities remain in context. Neural activations and weights inform the request; they do not replace the model’s trained parameters. This control produces an answer, not an external action.</p></form><article class="panel extension-form"><h2>Output</h2><div id="inference-status" role="status">No inference yet.</div><pre id="inference-answer" class="v3-output"></pre><div class="button-row"><button id="inference-export" class="button" disabled>Download answer & receipt</button></div><details><summary>Model and evidence receipt</summary><pre id="inference-receipt" class="v3-output"></pre></details></article></div><article class="panel extension-form"><h2>Saved runs</h2><div id="inference-history"></div></article>`;
$('main footer').before(inferenceSection);
const inferenceNav=document.createElement('button');inferenceNav.dataset.view='inference';inferenceNav.title=titleMap.inference;inferenceNav.innerHTML='<span>◉</span> Inference engine';$('nav [data-view=models]').after(inferenceNav);
let inferenceState=null,inferenceSelected=null,inferenceSourcesReady=false;
inferenceNav.addEventListener('click',()=>{inferenceSourcesReady=false;showView('inference');refreshInference().catch(e=>toast(e.message));});
async function refreshInference(){
 if(activeView!=='inference')return;
 inferenceState=await api('/api/inference');
 if(!inferenceSourcesReady){const sources=await api('/api/sources');$('#inference-sources').innerHTML=sources.filter(s=>s.status==='ready').map(s=>`<option value="${escapeHTML(s.id)}">${escapeHTML(s.title)}</option>`).join('');inferenceSourcesReady=true;}
 const provider=$('#inference-form [name=provider]').value,p=inferenceState.providers[provider];
 $('#inference-model-state').textContent=`${p.model} · ${p.configured?p.status:'Needs account configuration'}`;
 $('#inference-form [type=submit]').disabled=inferenceState.busy;
 const latest=inferenceState.jobs.at(-1);if(latest&&!inferenceSelected)inferenceSelected=latest.id;
 const job=inferenceState.jobs.find(j=>j.id===inferenceSelected)||latest;
 if(job){
  $('#inference-status').textContent=`${job.status.toUpperCase()} · ${job.model}${job.duration_ms!==undefined?' · '+(job.duration_ms/1000).toFixed(1)+' seconds':''}`;
  const text=job.answer||job.error||'The model is working…',el=$('#inference-answer');
  if(el.textContent!==text){const top=el.scrollTop;el.textContent=text;el.scrollTop=top;}
  const {answer,prompt,...receipt}=job;$('#inference-receipt').textContent=JSON.stringify(receipt,null,2);$('#inference-export').disabled=false;
 }
 rwReplace('inference-history',inferenceState.jobs.slice().reverse().map(j=>`<button class="button" data-inference="${j.id}">${escapeHTML(j.created)} · ${escapeHTML(j.provider)} · ${escapeHTML(j.status)} · ${escapeHTML(j.prompt.slice(0,70))}</button>`).join(' ')||'<p>No saved runs.</p>');
}
$('#inference-form').addEventListener('submit',guarded(async e=>{e.preventDefault();const f=e.target;const result=await api('/api/inference/run',{provider:f.elements.provider.value,prompt:f.elements.prompt.value,source_ids:[...$('#inference-sources').selectedOptions].map(o=>o.value),latest_research:f.elements.latest_research.checked});inferenceSelected=result.id;await refreshInference();}));
$('#inference-form [name=provider]').addEventListener('change',guarded(refreshInference));
$('#inference-history').addEventListener('click',guarded(async e=>{const b=e.target.closest('[data-inference]');if(b){inferenceSelected=b.dataset.inference;await refreshInference();}}));
$('#inference-export').addEventListener('click',guarded(async()=>{const job=inferenceState.jobs.find(j=>j.id===inferenceSelected)||inferenceState.jobs.at(-1);if(job)rwDownload('inference-'+job.id+'.json',job);}));
setInterval(()=>{if(activeView==='inference')refreshInference().catch(()=>{});},2000);
if(location.hash==='#inference'){showView('inference');refreshInference().catch(()=>{});}
