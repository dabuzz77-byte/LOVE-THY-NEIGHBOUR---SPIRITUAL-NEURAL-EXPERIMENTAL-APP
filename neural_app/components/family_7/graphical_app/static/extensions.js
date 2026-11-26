'use strict';
let sourceLibrary=[],workState=null,extensionRefresh=false,recognizer=null,recognitionButton=null;
let speechGeneration=0,speechUtterance=null,availableVoices=[];
let localAudio=null,localAudioURL=null;
const heardReplies={};
window.selectedSources=id=>[...document.getElementById(id).selectedOptions].map(option=>option.value).filter(Boolean);
function voiceStatus(text){$('#voice-status').textContent=text;}
function stopSpeaking(){speechGeneration++;window.speechSynthesis?.cancel();speechUtterance=null;if(localAudio){localAudio.pause();localAudio=null;}if(localAudioURL){URL.revokeObjectURL(localAudioURL);localAudioURL=null;}voiceStatus('Speech stopped.');}
async function speakText(text){
  if(recognizer){recognizer.abort();recognizer=null;}
  stopSpeaking();const generation=speechGeneration;
  const clean=String(text).replace(/```[\s\S]*?```/g,' Code block omitted from speech. ').replace(/https?:\/\/\S+/g,' link ').replace(/[#*_`]/g,'').trim();
  if(!clean){voiceStatus('There is no readable text to speak.');return;}
  if($('#voice-choice').value==='windows'){
    if(clean.length>6000){voiceStatus('Choose a browser voice for text longer than 6,000 characters.');return;}
    voiceStatus('Creating speech on this computer…');
    try{
      const response=await fetch('/api/speech',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:clean,rate:Number($('#voice-rate').value)||1})});
      if(!response.ok){const result=await response.json();throw Error(result.error||'Speech could not be generated');}
      const blob=await response.blob();if(generation!==speechGeneration)return;
      localAudioURL=URL.createObjectURL(blob);localAudio=new Audio(localAudioURL);
      localAudio.onended=()=>{if(generation===speechGeneration){stopSpeaking();voiceStatus('Finished speaking.');}};
      localAudio.onerror=()=>{if(generation===speechGeneration){stopSpeaking();voiceStatus('Audio playback failed. Try a browser voice.');}};
      await localAudio.play();if(generation===speechGeneration)voiceStatus('Speaking AI-generated text with the local Windows voice…');
    }catch(error){if(generation===speechGeneration){stopSpeaking();voiceStatus(error.name==='NotAllowedError'?'Your browser paused audio. Click Read reply or Test voice to play it.':error.message);}}
    return;
  }
  if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window)){voiceStatus('Browser speech is unavailable. Choose the local Windows voice.');return;}
  const chunks=clean.match(/.{1,220}(?:\s|$)|\S{1,220}/gs)||[];
  let position=0;
  const next=()=>{if(generation!==speechGeneration)return;if(position>=chunks.length){speechUtterance=null;voiceStatus('Finished speaking.');return;}
    const utterance=new SpeechSynthesisUtterance(chunks[position++]);speechUtterance=utterance;
    utterance.voice=availableVoices.find(v=>v.voiceURI===$('#voice-choice').value)||null;
    utterance.lang=utterance.voice?.lang||'en-GB';utterance.rate=Number($('#voice-rate').value)||1;
    utterance.onend=next;utterance.onerror=event=>{if(generation===speechGeneration&&event.error!=='canceled'&&event.error!=='interrupted')voiceStatus('Speech unavailable: '+event.error+'. Try another voice or browser.');};
    voiceStatus('Speaking AI-generated text…');speechSynthesis.speak(utterance);
  };next();
}
function loadVoices(){
  availableVoices=window.speechSynthesis?.getVoices()||[];const chosen=localStorage.getItem('postscarcity-voice')??'windows';
  $('#voice-choice').innerHTML='<option value="windows">Windows voice · local</option><option value="">Browser default</option>'+availableVoices.map(v=>`<option value="${escapeHTML(v.voiceURI)}">${escapeHTML(v.name)} · ${escapeHTML(v.lang)}</option>`).join('');
  if(chosen==='windows'||chosen===''||availableVoices.some(v=>v.voiceURI===chosen))$('#voice-choice').value=chosen;
}
function dictate(target,button){
  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!Recognition){toast('Dictation is unavailable here. You can type or use your operating system’s dictation.');return;}
  if(recognizer){recognizer.stop();return;}
  stopSpeaking();const input=typeof target==='string'?document.getElementById(target):target;
  const recognition=new Recognition();recognizer=recognition;recognitionButton=button;
  const oldLabel=button.textContent,initial=input.value;button.textContent='Stop listening';button.classList.add('listening');
  recognition.lang='en-GB';recognition.continuous=false;recognition.interimResults=false;
  voiceStatus('Listening. Your browser may use its online speech service.');
  recognition.onresult=event=>{
    const transcript=[...event.results].filter(r=>r.isFinal).map(r=>r[0].transcript).join(' ');
    const combined=(initial.trim()?initial.trim()+' ':'')+transcript;
    input.value=input.maxLength>0?combined.slice(0,input.maxLength):combined;
    input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();toast('Speech added. Review it, then send or save.');
  };
  recognition.onerror=event=>{toast(event.error==='not-allowed'?'Microphone permission was not granted. Enable it in your browser or type instead.':'Dictation: '+event.error+'. You can still type.');voiceStatus('Dictation stopped.');};
  recognition.onend=()=>{button.textContent=oldLabel;button.classList.remove('listening');if(recognizer===recognition)recognizer=null;recognitionButton=null;};
  try{recognition.start();}catch(error){recognition.onend();toast(error.message);}
}
$('#voice-auto').checked=localStorage.getItem('postscarcity-speak')==='true';
$('#voice-rate').value=localStorage.getItem('postscarcity-rate')||'1';
$('#voice-auto').addEventListener('change',()=>{localStorage.setItem('postscarcity-speak',String($('#voice-auto').checked));if(!$('#voice-auto').checked)stopSpeaking();else speakText('Spoken replies are on.');});
$('#voice-choice').addEventListener('change',()=>localStorage.setItem('postscarcity-voice',$('#voice-choice').value));
$('#voice-rate').addEventListener('change',()=>localStorage.setItem('postscarcity-rate',$('#voice-rate').value));
$('#voice-test').addEventListener('click',()=>speakText('The Postscarcity Observatory is ready. You can give me a task, add a source, or ask about the neural rules.'));
$('#voice-stop').addEventListener('click',stopSpeaking);
window.speechSynthesis?.addEventListener('voiceschanged',loadVoices);loadVoices();
$$('[data-dictate]').forEach(button=>button.addEventListener('click',()=>dictate(button.dataset.dictate,button)));
window.setupModelVoice=()=>{
  for(const panel of $$('.model-panel')){
    const controls=document.createElement('div');controls.className='model-voice-controls';
    controls.innerHTML='<button type="button" class="button model-dictate">Dictate</button><button type="button" class="button model-read">Read reply</button>';
    $('.model-compose',panel).prepend(controls);
    $('.model-dictate',panel).addEventListener('click',event=>dictate($('.model-input',panel),event.currentTarget));
    $('.model-read',panel).addEventListener('click',()=>{const reply=modelState?.[panel.dataset.provider]?.messages.filter(m=>m.role==='assistant').at(-1);if(reply)speakText(reply.content);else toast('Send a message first to receive a reply.');});
  }
};
window.voiceModels=models=>{
  for(const [provider,data] of Object.entries(models)){
    const latest=data.messages.at(-1);if(latest?.role!=='assistant')continue;
    const signature=data.messages.length+'|'+latest.content+'|'+data.context?.snapshot_time;
    if(heardReplies[provider]!==undefined&&heardReplies[provider]!==signature&&$('#voice-auto').checked)speakText(latest.content);
    heardReplies[provider]=signature;
  }
};
// Establish a baseline before the first response, so new replies can speak without reading old history on reload.
document.addEventListener('submit',event=>{const panel=event.target.closest('.model-panel');if(panel&&heardReplies[panel.dataset.provider]===undefined)heardReplies[panel.dataset.provider]='';},true);

function sourcePickers(){
  for(const select of $$('.source-picker')){
    if(document.activeElement===select)continue;
    const chosen=new Set([...select.selectedOptions].map(o=>o.value));
    const ready=sourceLibrary.filter(s=>s.text);
    select.innerHTML=ready.length?ready.map(s=>`<option value="${s.id}" ${chosen.has(s.id)?'selected':''}>${escapeHTML(s.title)}</option>`).join(''):'<option value="" disabled>Add website or text sources first</option>';
  }
}
function renderSourceLibrary(){
  const open=new Set($$('#source-library details[open]').map(d=>d.dataset.source));
  $('#source-count').textContent=sourceLibrary.length+' SOURCES';
  $('#source-library').innerHTML=sourceLibrary.length?sourceLibrary.slice().reverse().map(s=>`<article class="panel source-card"><header><span class="tiny-label">${s.kind==='website'?'WEBSITE':s.kind==='screen'?'APP / TAB CAPTURE':'PASTED TEXT'}</span><span class="tag ${s.status==='ready'?'mint':''}">${escapeHTML(s.status.toUpperCase())}</span></header><h2>${escapeHTML(s.title)}</h2>${s.url?`<a href="${escapeHTML(s.url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:''}<p class="muted">${s.retrieved?'Last captured '+escapeHTML(shortTime(s.retrieved)):'Waiting for retrieval'}${s.truncated?' · stored excerpt':''}</p>${s.error?`<p class="source-error">${escapeHTML(s.error)}</p>`:''}<details data-source="${s.id}" ${open.has(s.id)?'open':''}><summary>Read ingested text</summary><pre>${escapeHTML(s.text||'No text retrieved yet.')}</pre></details>${s.kind==='website'?`<div class="button-row"><button class="button" data-source-action="refresh" data-id="${s.id}">Refresh now</button><button class="button" data-source-action="toggle" data-id="${s.id}">${s.automatic?'Pause automatic refresh':'Enable automatic refresh'}</button></div>`:''}</article>`).join(''):'<div class="panel empty">Add a website or text above. Your source library will appear here.</div>';
}
function renderWork(){
  if(!workState)return;
  $('#work-folder').textContent=workState.folder;$('#work-complete').textContent=workState.outcomes.files_verified;$('#work-useful').textContent=workState.outcomes.useful;
  const filter=$('#work-filter').value,open=new Set($$('#work-tasks details[open]').map(d=>d.dataset.task));
  const tasks=workState.tasks.filter(t=>filter==='all'||t.status===filter||(filter==='failed'&&t.status==='interrupted')).reverse();
  $('#work-tasks').innerHTML=tasks.length?tasks.map(t=>`<article class="panel task-card"><header><span class="tiny-label">${escapeHTML(t.provider.toUpperCase())}</span><span class="tag ${t.status==='complete'?'mint':''}">${escapeHTML(t.status.toUpperCase())}</span></header><h2>${escapeHTML(t.title)}</h2><p>${escapeHTML(t.instruction)}</p><small>${escapeHTML(t.filename)} · ${escapeHTML(shortTime(t.updated))}</small>${t.error?`<p class="source-error">${escapeHTML(t.error)}</p>`:''}${t.status==='cancelled'&&workState.active===t.id?'<p class="muted">The current model request is finishing. Its output will not be saved.</p>':''}${t.output?`<details data-task="${t.id}" ${open.has(t.id)?'open':''}><summary>Preview saved file · ${t.output.bytes} bytes checked</summary><pre>${escapeHTML(t.output.preview)}</pre></details><div class="button-row"><a class="button" href="/api/work/file?id=${t.id}&download=1">Download file ↗</a><button class="button" data-work-action="read" data-id="${t.id}">Read aloud</button></div><div class="task-feedback"><span>Your review:</span><button class="button ${t.feedback==='useful'?'primary':''}" data-work-action="useful" data-id="${t.id}">Useful</button><button class="button ${t.feedback==='needs_revision'?'primary':''}" data-work-action="needs_revision" data-id="${t.id}">Needs revision</button></div>`:`<div class="button-row">${t.status==='running'?`<button class="button" data-work-action="cancel" data-id="${t.id}">Cancel task</button>`:`<button class="button primary" data-work-action="run" data-id="${t.id}" ${workState.active?'disabled':''}>Run task ↗</button>${t.status==='draft'?`<button class="button" data-work-action="cancel" data-id="${t.id}">Cancel</button>`:''}`}</div>`}</article>`).join(''):'<div class="panel empty">Your tasks will appear here with their progress and saved files.</div>';
}
window.refreshExtensions=async()=>{
  if(extensionRefresh)return;extensionRefresh=true;
  try{const results=await Promise.all([api('/api/sources'),api('/api/work')]);sourceLibrary=results[0];workState=results[1];sourcePickers();if(activeView==='sources')renderSourceLibrary();if(activeView==='work')renderWork();}
  catch(error){toast(error.message)}finally{extensionRefresh=false;}
};
$('#website-form').addEventListener('submit',guarded(async event=>{event.preventDefault();const button=$('button[type=submit]',event.target);button.disabled=true;try{await api('/api/sources/add',{kind:'website',url:$('#website-url').value,automatic:$('#website-auto').checked});$('#website-url').value='';toast('Website queued for ingestion');await refreshExtensions();}finally{button.disabled=false;}}));
$('#text-source-form').addEventListener('submit',guarded(async event=>{event.preventDefault();await api('/api/sources/add',{kind:'text',title:$('#source-title').value,text:$('#source-text').value});event.target.reset();toast('Text ingested and available to the models');await refreshExtensions();}));
$('#source-library').addEventListener('click',guarded(async event=>{const button=event.target.closest('[data-source-action]');if(!button)return;await api('/api/sources/control',{id:button.dataset.id,action:button.dataset.sourceAction});await refreshExtensions();}));
$('#work-form').addEventListener('submit',guarded(async event=>{event.preventDefault();const button=event.submitter;button.disabled=true;try{
  const provider=$('#work-provider').value;
  const task=await api('/api/work/create',{title:$('#work-title').value,instruction:$('#work-instruction').value,provider,filename:$('#work-filename').value,source_ids:selectedSources('work-sources')});
  event.target.reset();$('#work-provider').value=provider;
  if(button.value==='run'){await api('/api/work/start',{id:task.id});toast('Task started. Its file will appear here.');}else toast('Task saved to your work board');
}finally{button.disabled=false;await refreshExtensions();}}));
$('#work-filter').addEventListener('change',renderWork);
$('#work-tasks').addEventListener('click',guarded(async event=>{const button=event.target.closest('[data-work-action]');if(!button)return;const id=button.dataset.id,action=button.dataset.workAction;
  if(action==='read'){const file=await api('/api/work/file?id='+id);speakText(file.text);return;}
  button.disabled=true;try{if(action==='run')await api('/api/work/start',{id});else await api('/api/work/action',{id,action:action==='cancel'?'cancel':'feedback',value:action});await refreshExtensions();}finally{button.disabled=false;}
}));
setInterval(()=>{if(['work','sources','models'].includes(activeView))refreshExtensions();},3000);
window.addEventListener('beforeunload',()=>{recognizer?.abort();stopSpeaking();});

window.renderChiralText=()=>{
  const command=state?.chiral?.command,bus=state?.chiral?.binary_bus;
  $('#chiral-text-stage').textContent=command?'PASS '+number(command.generations):'AWAITING INPUT';
  $('#chiral-text-summary').textContent=command?`${command.byte_count} UTF-8 bytes · ${command.bit_count} bits · rotation ${command.rotations} / 4`:'Load text to see its bits move through both chirals.';
  $('#chiral-binary-input').textContent=command?.input_binary||'—';$('#chiral-binary-output').textContent=command?.output_binary||'—';
  $('#chiral-recovered-text').textContent=command?.recovered_text||'—';$('#chiral-recovery-status').textContent=command?(command.verified?'Verified: every input byte is recoverable.':'Recovery check failed.'):'No input yet.';
  $('#chiral-decoded-text').textContent=command?(command.output_text===null?'These transformed bytes do not currently form valid UTF-8 text. The binary above remains valid and reversible.':JSON.stringify(command.output_text)):'—';
  const left=command?.left_binary.split(' ')||[],right=command?.right_binary.split(' ')||[];
  $('#chiral-byte-grid').innerHTML=left.slice(0,8).map((bits,i)=>`<div class="chiral-byte"><small>BYTE ${i+1}</small><span class="left-bits">${bits.split('').map(bit=>`<b class="bit-${bit}">${bit}</b>`).join('')}</span><span class="binary-arrow">⇄</span><span class="right-bits">${right[i].split('').map(bit=>`<b class="bit-${bit}">${bit}</b>`).join('')}</span></div>`).join('')+(left.length>8?'<small>First 8 bytes animated · all bytes included in the binary output.</small>':'');
  if(!bus)return;
  $('#chiral-bus-status').textContent=state.settings.chiral_running?'PROCESSING EACH PULSE':'PAUSED · INPUTS QUEUING';
  $('#chiral-bus-bytes').textContent=number(bus.processed_bytes);$('#chiral-bus-frames').textContent=number(bus.completed_frames);$('#chiral-bus-pending').textContent=number(bus.pending_bytes);$('#chiral-bus-rejected').textContent=number(bus.rejected_frames);
  const latest=bus.latest;
  $('#chiral-bus-latest').textContent=bus.rejected_frames?bus.last_error:latest?`${latest.stream} · ${number(latest.bytes)} bytes · ${latest.reversible?'inverse verified':'recovery failed'}`:'Waiting for the first runtime frame.';
  $('#chiral-bus-preview').textContent=latest?`INPUT (first 32 bytes)\n${latest.input_binary_preview}\n\nOUTPUT (first 32 bytes)\n${latest.output_binary_preview}\n\nInput fingerprint: ${latest.input_sha256}\nOutput fingerprint: ${latest.output_sha256}`:'—';
  $('#chiral-streams').innerHTML=Object.entries(bus.streams).map(([name,counts])=>`<tr><td>${escapeHTML(name)}</td><td>${number(counts.accepted_bytes)}</td><td>${number(counts.processed_bytes)}</td></tr>`).join('');
};
$('#chiral-text-form').addEventListener('submit',guarded(async event=>{event.preventDefault();const button=$('button[type=submit]',event.target);button.disabled=true;try{const result=await api('/api/chiral',{action:'text',text:$('#chiral-text-input').value});state.chiral={...state.chiral,...result};renderAll();toast('Text encoded and passed through both chirals');}finally{button.disabled=false;}}));
$('#chiral-clear-text').addEventListener('click',guarded(async()=>{state.chiral={...state.chiral,...await api('/api/chiral',{action:'clear-text'})};$('#chiral-text-input').value='';renderAll();}));
for(const [id,key] of [['copy-chiral-binary','output_binary'],['copy-chiral-text','recovered_text']])$('#'+id).addEventListener('click',guarded(async()=>{const value=state?.chiral?.command?.[key];if(!value){toast('Load a text command first');return;}await navigator.clipboard.writeText(value);toast('Copied');}));

let passthroughSaving=false;
async function refreshCommands(){
  const result=await api('/api/commands');
  if(!passthroughSaving){$('#system-passthrough').checked=result.passthrough.enabled;$('#system-passthrough').disabled=false;}
  $('#passthrough-status').textContent=result.passthrough.enabled?'WINDOWS QUERIES ENABLED':'WINDOWS QUERIES BLOCKED';
  $('#command-history').innerHTML=result.plans.slice().reverse().map(item=>`<article class="panel task-card"><header><span class="tiny-label">${escapeHTML(item.basis)}</span><span class="tag">${escapeHTML(item.status.toUpperCase())}</span></header><h2>${escapeHTML(item.request.split('\n')[0])}</h2><pre class="access-output">${escapeHTML(item.preview)}</pre>${item.status==='ready'?`<button class="button primary" data-command-run="${item.id}">Run this command ↗</button>`:''}${item.output?`<details open><summary>Actual result${item.truncated?' · preview shortened':''}</summary><pre>${escapeHTML(item.output)}</pre></details>`:''}${item.error?`<p class="source-error">${escapeHTML(item.error)}</p>`:''}</article>`).join('')||'<div class="panel empty">Your interpreted commands and their actual results appear here.</div>';
}
$('#system-passthrough').addEventListener('change',guarded(async event=>{const toggle=event.target;passthroughSaving=true;toggle.disabled=true;try{await api('/api/settings',{system_passthrough:toggle.checked});}finally{passthroughSaving=false;await refreshCommands();}}));
$('nav [data-view=commands]').addEventListener('click',guarded(refreshCommands));
$('#command-form').addEventListener('submit',guarded(async event=>{event.preventDefault();const button=$('button[type=submit]',event.target);button.disabled=true;$('#command-status').textContent='Interpreting with the shared rule context…';try{await api('/api/commands/prepare',{text:$('#command-input').value,provider:$('#command-provider').value});await refreshCommands();$('#command-status').textContent='Plan ready. Review it, then Run this command.';}catch(error){$('#command-status').textContent=error.message;throw error;}finally{button.disabled=false;}}));
$('#command-history').addEventListener('click',guarded(async event=>{const button=event.target.closest('[data-command-run]');if(!button)return;button.disabled=true;button.textContent='Running…';try{await api('/api/commands/run',{id:button.dataset.commandRun});await refreshCommands();}finally{button.disabled=false;await refreshCommands();}}));
let selectedWindows=[];
function screenPayload(){return {handle:$('#screen-window').value,tab:$('#screen-tab').value,element:$('#screen-element').value,automatic:$('#screen-auto').checked,targets:screenTargets()};}
$('#screen-refresh').addEventListener('click',guarded(async()=>{const button=$('#screen-refresh');button.disabled=true;$('#screen-status').textContent='Reading available window titles…';try{selectedWindows=await api('/api/screen/windows');$('#screen-window').innerHTML='<option value="">Choose an application window</option>'+selectedWindows.map(w=>`<option value="${escapeHTML(w.handle)}">${escapeHTML(w.process+' · '+w.title)}</option>`).join('');$('#screen-tab').innerHTML='<option value="">Choose a window first</option>';$('#screen-element').innerHTML='<option value="">Readable content of the selected window or tab</option>';$('#screen-status').textContent=selectedWindows.length+' windows available.';}finally{button.disabled=false;}}));
$('#screen-window').addEventListener('change',guarded(async()=>{if(!$('#screen-window').value)return;$('#screen-status').textContent='Finding individual browser tabs…';$('#screen-element').innerHTML='<option value="">Readable content of the selected window or tab</option>';const rows=await api('/api/screen/inspect',{mode:'tabs',...screenPayload()});$('#screen-tab').innerHTML=rows.length?'<option value="">Choose one browser tab</option>'+rows.map(row=>`<option value="${escapeHTML(row.id)}">${escapeHTML(row.title)}${row.selected?' · active':''}</option>`).join(''):'<option value="">No browser tabs exposed by this window</option>';$('#screen-status').textContent=rows.length?'Choose a tab to ingest.':'Window selected. Choose an element if useful, then ingest.';}));
$('#screen-tab').addEventListener('change',()=>{$('#screen-element').innerHTML='<option value="">Readable content of the selected window or tab</option>';});
$('#screen-elements').addEventListener('click',guarded(async()=>{const button=$('#screen-elements');button.disabled=true;$('#screen-status').textContent='Reading accessible elements in your selection…';try{const rows=await api('/api/screen/inspect',{mode:'elements',...screenPayload()});$('#screen-element').innerHTML='<option value="">Readable content of the selected window or tab</option>'+rows.map(row=>`<option value="${escapeHTML(row.id)}">${escapeHTML(row.type.replace('ControlType.','')+' · '+row.title)}</option>`).join('');$('#screen-status').textContent=rows.length+' accessible elements available.';}finally{button.disabled=false;}}));
async function showScreenResult(result){if(!screenPicking)$('#screen-status').textContent=result.error||result.status;const c=result.command;const run=$('#screen-command-execute');run.hidden=!(c?.plan?.status==='ready');if(c?.plan)run.dataset.plan=c.plan.id;if(c){const out=$('#screen-command-output');const bottom=out.scrollHeight-out.scrollTop-out.clientHeight<30;const text=c.output||c.error||(c.busy?'Model is working on the selected text…':'No model reply available.');if(out.textContent!==text){const top=out.scrollTop;out.textContent=text;out.scrollTop=bottom?out.scrollHeight:top;}}if(result.source_id){await refreshExtensions();const source=sourceLibrary.find(s=>s.id===result.source_id);$('#screen-preview').textContent=source?.text||'Captured source is available in Website & text.';}}
$('#screen-form').addEventListener('submit',guarded(async event=>{event.preventDefault();const button=$('button[type=submit]',event.target);button.disabled=true;$('#screen-status').textContent='Ingesting the selected content…';try{await showScreenResult(await api('/api/screen/ingest',screenPayload()));toast('Selected app content ingested into the field');}catch(error){$('#screen-status').textContent=error.message;throw error;}finally{button.disabled=false;}}));
$('#screen-stop').addEventListener('click',guarded(async()=>{await showScreenResult(await api('/api/screen/stop',{}));$('#screen-auto').checked=false;}));
setInterval(()=>{if(activeView==='commands')refreshCommands().catch(error=>toast(error.message));if(activeView==='screen')api('/api/screen').then(showScreenResult).catch(error=>toast(error.message));},4000);

let fieldVoice=null,fieldVoiceSignature,fieldVoiceRenderingSignature;
async function refreshFieldVoice(){
  fieldVoice=await api('/api/field-voice');
  $('#field-voice-state').textContent=fieldVoice.busy?'THINKING':fieldVoice.error?'CHECK CONNECTION':'READY';
  $('#field-voice-form button[type=submit]').disabled=fieldVoice.busy;
  $('#field-voice-error').textContent=fieldVoice.error||'';
  const html=fieldVoice.messages.map(item=>`<div class="chat-message ${item.role}"><span>${item.role==='user'?'YOU':'WHOLE SYSTEM'}</span><p>${escapeHTML(item.content)}</p></div>`).join('')||'<p class="empty">Ask the assembled field a question or describe what you want to accomplish.</p>';
  const history=$('#field-voice-history'),renderingSignature=JSON.stringify(fieldVoice.messages);
  if(fieldVoiceRenderingSignature!==renderingSignature){
    const previousTop=history.scrollTop;
    const followLatest=fieldVoiceRenderingSignature===undefined||history.scrollHeight-previousTop-history.clientHeight<70;
    history.innerHTML=html;
    history.scrollTop=followLatest?history.scrollHeight:previousTop;
    fieldVoiceRenderingSignature=renderingSignature;
  }
  const last=fieldVoice.messages.at(-1);
  if(last?.role==='assistant'){
    const signature=fieldVoice.messages.length+'|'+last.content;
    if(fieldVoiceSignature!==undefined&&signature!==fieldVoiceSignature&&$('#voice-auto').checked)speakText(last.content);
    fieldVoiceSignature=signature;
  }
  if(fieldVoice.context){const c=fieldVoice.context;$('#field-voice-coverage').textContent=`${c.shared_rules} shared rules · ${c.module_summaries} module entries · ${c.node_count} weighted nodes · field ${c.field_output} · reply through ${c.provider}`;}
}
$('#field-voice-form').addEventListener('submit',guarded(async event=>{event.preventDefault();fieldVoiceSignature=fieldVoiceSignature??'';await api('/api/field-voice/send',{text:$('#field-voice-input').value,provider:$('#field-voice-provider').value,source_ids:selectedSources('field-voice-sources')});$('#field-voice-input').value='';await refreshFieldVoice();}));
$('#field-voice-read').addEventListener('click',()=>{const reply=fieldVoice?.messages.filter(item=>item.role==='assistant').at(-1);if(reply)speakText(reply.content);else toast('Ask the whole system a question first');});
$('#field-voice-clear').addEventListener('click',guarded(async()=>{await api('/api/field-voice/clear',{});fieldVoiceSignature=undefined;await refreshFieldVoice();}));
setInterval(()=>{if(activeView==='models')refreshFieldVoice().catch(error=>toast(error.message));},2000);

function fillScreenTargets(){
  if(!state?.modules)return;
  const group=$('#screen-group').value,chosen=new Set([...$('#screen-modules').selectedOptions].map(option=>option.value));
  $('#screen-group').innerHTML=[...new Set(state.modules.map(m=>m.family))].map(f=>`<option value="${f}">${f}</option>`).join('');
  if(group)$('#screen-group').value=group;
  $('#screen-modules').innerHTML=state.modules.map(m=>`<option value="${escapeHTML(m.id)}" ${chosen.has(m.id)?'selected':''}>${escapeHTML(m.title)}</option>`).join('');
}
function screenTargets(){
  if($('#screen-target-mode').value==='group')return state.modules.filter(m=>m.family===$('#screen-group').value).map(m=>m.id);
  if($('#screen-target-mode').value==='selected')return [...$('#screen-modules').selectedOptions].map(option=>option.value);
  return state?.modules.map(m=>m.id)||[];
}
$('#screen-refresh').addEventListener('click',fillScreenTargets);
$('#screen-target-mode').addEventListener('change',()=>{fillScreenTargets();$('#screen-group-label').hidden=$('#screen-target-mode').value!=='group';$('#screen-modules-label').hidden=$('#screen-target-mode').value!=='selected';$('#screen-target-caption').textContent='Selected modules receive this captured text as context, run their own rules and host measurements, and feed their results through the chirals.';});
let callDefinitionState=null,callDefinitionRefresh=false,callDefinitionTime=0;
window.renderCallDefinitions=async()=>{
  if(!callDefinitionState||Date.now()-callDefinitionTime>5000){
    if(callDefinitionRefresh)return;callDefinitionRefresh=true;
    try{callDefinitionState=await api('/api/call-definitions');callDefinitionTime=Date.now();}catch(error){toast(error.message);return;}finally{callDefinitionRefresh=false;}
  }
  if(definitionMode!=='calls')return;
  const data=callDefinitionState,query=$('#definition-search').value.toLowerCase();
  const sourceErrors=Object.entries(data.source_errors||{}).filter(([name,error])=>(name+' '+error).toLowerCase().includes(query));
  const rows=data.calls.filter(c=>(c.expression+' '+c.module+' '+c.qualified+' '+c.text).toLowerCase().includes(query));
  $('#ingest-caption').textContent=`${data.call_sites} call sites · ${data.local_or_documented} supplied definitions · ${data.web_pages_ready}/${data.web_pages_total} official pages retrieved · ${data.unresolved} unresolved names · ${data.automatic?'continuous ingestion on':'ingestion paused'} · showing ${Math.min(rows.length,60)} of ${rows.length} matches`;
  $('#definitions-grid').innerHTML=rows.slice(0,60).map(c=>`<article class="panel definition-card"><header><h2>${escapeHTML(c.expression)}</h2><span class="tag">${escapeHTML(c.web_status.toUpperCase())}</span></header><small>${escapeHTML(c.module)} · line ${c.line} · ${escapeHTML(c.resolution)}</small><p>${escapeHTML(c.text||c.error||'Official definition queued for retrieval.')}</p>${c.url?`<a href="${escapeHTML(c.url)}" target="_blank" rel="noopener noreferrer">Official reference ↗</a>`:''}<details><summary>Context sent back to the module</summary><pre>${escapeHTML(c.web_text||c.local_definition||'Waiting for the reference page.')}</pre></details><div class="module-chips"><button data-call-module="${escapeHTML(c.module)}">Open module ↗</button></div></article>`).join('');
  if(sourceErrors.length){
    $('#ingest-caption').textContent+=` · ${sourceErrors.length} source errors need repair`;
    $('#definitions-grid').insertAdjacentHTML('afterbegin',sourceErrors.map(([name,error])=>`<article class="panel definition-card"><header><h2>${escapeHTML(name)}</h2><span class="tag">SOURCE ERROR</span></header><p>${escapeHTML(error)}</p><p>Definitions for this file are unavailable until its source is repaired. Other modules continue loading.</p></article>`).join(''));
  }
  $$('[data-call-module]').forEach(button=>button.addEventListener('click',()=>openModule(button.dataset.callModule)));
};
setInterval(()=>{if(activeView==='definitions'&&definitionMode==='calls')renderCallDefinitions();},6000);

function fillLoopOptions(){
  if(!state?.modules)return;
  const chosen=new Set([...$('#loop-modules').selectedOptions].map(option=>option.value)),group=$('#loop-group').value,loops=state.settings.module_loops||{};
  $('#loop-modules').innerHTML=state.modules.map(m=>`<option value="${escapeHTML(m.id)}" ${chosen.has(m.id)?'selected':''}>${escapeHTML(m.title)} · ${loops[m.id]??state.settings.cycle_seconds}s${m.id in loops?' custom':''}</option>`).join('');
  $('#loop-group').innerHTML=[...new Set(state.modules.map(m=>m.family))].map(f=>`<option>${f}</option>`).join('');
  if(group)$('#loop-group').value=group;
  $('#loop-status').textContent=`${Object.keys(loops).length} custom loops configured. Normal interval: ${state.settings.cycle_seconds}s. Unselected modules keep their current schedules.`+(state.settings.running?'':' Module execution is currently paused in Settings.');
}
function loopModules(){const mode=$('#loop-mode').value;return mode==='all'?state.modules.map(m=>m.id):mode==='group'?state.modules.filter(m=>m.family===$('#loop-group').value).map(m=>m.id):[...$('#loop-modules').selectedOptions].map(option=>option.value);}
$('#module-loop-form').closest('details').addEventListener('toggle',fillLoopOptions);
$('#loop-mode').addEventListener('change',()=>{$('#loop-modules-label').hidden=$('#loop-mode').value!=='selected';$('#loop-group-label').hidden=$('#loop-mode').value!=='group';});
async function applyLoops(action){const selected=loopModules();if(!selected.length)throw Error('Choose at least one module');const result=await api('/api/loops',{modules:selected,action,interval:Number($('#loop-interval').value)});state.settings.module_loops=result.module_loops;fillLoopOptions();$('#loop-status').textContent=(action==='set'?`Custom loop applied to ${selected.length} modules. `:`Normal schedule restored for ${selected.length} modules. `)+`${Object.keys(result.module_loops).length} custom loops configured. Unselected modules keep their current schedules. Normal interval: ${result.default_seconds}s.`+(result.running?'':' Module execution is currently paused in Settings.');}
$('#module-loop-form').addEventListener('submit',guarded(async event=>{event.preventDefault();await applyLoops('set');}));
$('#loop-restore').addEventListener('click',guarded(async()=>{await applyLoops('restore');}));

let screenPicking=false;
async function pickScreenTarget(){
 const button=$('#screen-pick');button.disabled=true;screenPicking=true;fillScreenTargets();
 $('#screen-status').textContent='Click the window or tab you want. Escape cancels.';
 try {const r=await api('/api/screen/pick',{});if(r.cancelled){$('#screen-status').textContent='Selection cancelled.';return;}
 selectedWindows=selectedWindows.filter(w=>w.handle!==r.window.handle);selectedWindows.push(r.window);
 $('#screen-window').innerHTML='<option value="">Choose a window</option>'+selectedWindows.map(w=>`<option value="${escapeHTML(w.handle)}">${escapeHTML(w.process+' · '+w.title)}</option>`).join('');$('#screen-window').value=r.window.handle;
 $('#screen-tab').innerHTML='<option value="">'+(r.tabs.length?'Choose an individual tab':'No tabs exposed')+'</option>'+r.tabs.map(t=>`<option value="${escapeHTML(t.id)}">${escapeHTML(t.title)}</option>`).join('');$('#screen-tab').value=r.tab||'';
 $('#screen-element').innerHTML='<option value="">Readable content of the selected window or tab</option>';
 $('#screen-status').textContent='Selected: '+(r.tabs.find(t=>t.id===r.tab)?.title||r.window.title)+'. Enter a command or ingest this selection.';
 document.dispatchEvent(new CustomEvent('observatory-target-picked',{detail:r}));
 return r;
 }finally{screenPicking=false;button.disabled=false;}
}
$('#screen-pick').addEventListener('click',guarded(pickScreenTarget));
$('#screen-command-run').addEventListener('click',guarded(async()=>{const b=$('#screen-command-run');b.disabled=true;try{await showScreenResult(await api('/api/screen/command',{...screenPayload(),command:$('#screen-command').value,provider:$('#screen-command-provider').value,mode:$('#screen-command-mode').value}));}finally{b.disabled=false;}}));

$('#screen-command-execute').onclick=guarded(async()=>{const b=$('#screen-command-execute');b.disabled=true;try{await api('/api/commands/run',{id:b.dataset.plan});await showScreenResult(await api('/api/screen'));}finally{b.disabled=false;}});
