"""Microcosmic console: live CPU matrix, local buffer, and three-provider inference.

Requires pywebview. psutil supplies per-logical-CPU readings when installed;
Windows also has a dependency-free, system-wide CPU sampler.
Inference uses Python's standard library, with cloud keys held only in memory.
"""
import ctypes
import json
import math
import os
import re
from neural_app import section_threads as threading
import time
from collections import deque
from urllib import error as urlerror, parse as urlparse, request as urlrequest
try:
    import psutil
except ImportError:
    psutil = None
CARRIER_FREQUENCY = 7.83
TELEMETRY_INTERVAL = 0.5
BUFFER_CAPACITY = 1024
MAX_ORDER = 1000000
INFERENCE_TIMEOUT = 60
HTML_LAYOUT = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Microcosmic Charge Injector Core</title>\n<style>\n:root { color-scheme: dark; --bg:#030508; --panel:#080d17; --line:#1d2c42; --muted:#8597ae; --blue:#65a9ff; --ice:#dceeff; --cyan:#72deeb; }\n* { box-sizing:border-box; margin:0; padding:0; }\nbody { background:var(--bg); color:#d5e1f1; font:13px \'Cascadia Code\',Consolas,monospace; min-width:360px; }\nbutton,input,textarea { font:inherit; }\nbutton { cursor:pointer; }\nbutton:disabled { cursor:wait; opacity:.45; }\nbutton:focus-visible { outline:2px solid var(--cyan); outline-offset:3px; }\n::selection { background:#234b7e; color:white; }\n::-webkit-scrollbar { width:7px; height:7px; }\n::-webkit-scrollbar-thumb { background:#263c57; border-radius:4px; }\n.master-container { display:grid; grid-template-columns:minmax(0,1.12fr) minmax(400px,1fr); grid-template-rows:auto minmax(660px,1fr) auto 192px; gap:14px; padding:20px; min-height:100vh; }\n.masthead { grid-column:1/-1; display:flex; align-items:center; justify-content:space-between; gap:16px; padding:1px 2px 7px; }\n.eyebrow { color:var(--blue); font-size:10px; letter-spacing:.23em; margin-bottom:6px; }\nh1 { font-size:20px; font-weight:500; letter-spacing:.035em; color:#e7f1ff; }\n.version { font-size:11px; color:var(--muted); margin-left:10px; }\n.badge { font-size:10px; letter-spacing:.1em; color:var(--muted); white-space:nowrap; display:flex; align-items:center; gap:8px; }\n.dot { width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 10px currentColor; }\n.badge.live { color:var(--cyan); }\n.badge.stale { color:#efbf77; }\n.panel { min-width:0; border:1px solid var(--line); border-radius:5px; background:linear-gradient(135deg,#0a1220,#060a12 75%); display:flex; flex-direction:column; overflow:hidden; }\n.panel-header { min-height:43px; border-bottom:1px solid var(--line); padding:12px 16px; display:flex; align-items:center; justify-content:space-between; gap:12px; }\nh2 { font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:.15em; color:#a2b4cc; }\n.index { color:var(--blue); margin-right:10px; }\n.tag { color:#6685ab; font-size:10px; white-space:nowrap; }\n.telemetry-strip { display:grid; grid-template-columns:1.2fr 1fr 1fr; padding:19px 20px 13px; gap:10px; }\n.metric-label { color:var(--muted); text-transform:uppercase; letter-spacing:.09em; font-size:10px; }\n.metric-value { display:block; color:var(--ice); font-size:27px; margin-top:7px; font-variant-numeric:tabular-nums; }\n.metric-value.primary { color:var(--blue); }\n.metric-value small { font-size:12px; color:var(--muted); }\n.canvas-wrapper { min-height:365px; flex:1; position:relative; margin:0 12px; }\ncanvas { width:100%; height:100%; display:block; position:absolute; inset:0; }\n.matrix-caption { display:flex; justify-content:space-between; align-items:center; gap:14px; padding:12px 18px; border-top:1px solid #142235; color:var(--muted); font-size:10px; line-height:1.5; }\n.quiet-button { color:#9ab7db; border:1px solid #2a405d; background:#0a1525; border-radius:3px; padding:8px 11px; font-size:10px; white-space:nowrap; }\n.quiet-button:hover { border-color:#5a94d8; background:#10243d; color:#e4f1ff; }\n.workspace-panel { display:flex; flex-direction:column; gap:19px; padding:22px; flex:1; min-height:0; overflow:auto; }\n.input-group { display:flex; flex-direction:column; gap:9px; }\n.label-row { display:flex; justify-content:space-between; align-items:center; gap:10px; }\nlabel { color:#bdcce0; font-size:11px; text-transform:uppercase; letter-spacing:.07em; }\n.counter { color:var(--muted); font-size:10px; white-space:nowrap; }\ntextarea,input[type=number] { background:#03070d; border:1px solid #304661; color:#e8f2ff; padding:15px 16px; border-radius:4px; outline:none; width:100%; transition:border-color .15s,box-shadow .15s; }\ntextarea { min-height:158px; height:158px; resize:vertical; font-size:16px; line-height:1.65; }\ninput[type=number] { min-height:57px; font-size:22px; font-variant-numeric:tabular-nums; }\ntextarea:focus,input:focus { border-color:#589deb; box-shadow:0 0 0 3px #285da822; }\n[aria-invalid=true] { border-color:#ec9d83 !important; }\n.hint { font-size:10px; color:var(--muted); line-height:1.55; }\n.inject-btn { background:linear-gradient(100deg,#153867,#10284b); border:1px solid #4386d9; color:#b7d8ff; min-height:51px; padding:14px; font-size:11px; font-weight:bold; border-radius:3px; letter-spacing:.08em; text-transform:uppercase; width:100%; box-shadow:inset 0 1px #80b9ff16; }\n.inject-btn:hover:enabled { background:linear-gradient(100deg,#1c4d88,#163965); box-shadow:0 0 22px #387acc18; }\n.action-row { display:flex; gap:12px; align-items:center; }\n.shortcut { font-size:10px; color:var(--muted); white-space:nowrap; }\n.feedback { min-height:17px; color:var(--cyan); font-size:11px; line-height:1.5; overflow-wrap:anywhere; }\n.feedback.error,.counter.error { color:#f3ad93; }\n.buffer-card { border-top:1px solid var(--line); padding-top:16px; margin-top:auto; }\n.buffer-top { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px; }\n.buffer-stats { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }\n.buffer-value { display:block; margin-top:7px; font-size:16px; color:#c2d8f2; overflow-wrap:anywhere; }\n.meter { height:3px; background:#12233a; margin:15px 0 10px; }\n.meter-fill { height:100%; background:var(--blue); width:0; transition:width .2s; box-shadow:0 0 9px #518ee866; }\n.hex-preview { color:#6d8fb8; font-size:10px; line-height:1.7; overflow-wrap:anywhere; white-space:pre-wrap; min-height:34px; }\n.ledger-panel { grid-column:1/-1; background:#04080e; }\n.ledger-tools { display:flex; align-items:center; gap:14px; }\n.ledger { overflow:auto; padding:12px 16px; font-size:11px; line-height:1.85; flex:1; min-height:0; }\n.log-line { display:grid; grid-template-columns:74px 85px 1fr; gap:12px; }\n.log-time { color:#607897; }\n.log-kind { color:#7daef0; }\n.log-message { color:#a7bdd8; white-space:pre-wrap; overflow-wrap:anywhere; }\n.log-line.error .log-message { color:#e9a58c; }\n.network-panel { grid-column:1/-1; }\n.network-body { padding:20px; }\n.network-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }\n.provider { border:1px solid #23374f; background:#050b14; padding:16px; border-radius:4px; min-width:0; }\n.provider-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:18px; }\n.provider-head label { color:#c7defb; font-size:13px; }\n.provider-head input { accent-color:#6cb5ff; margin-right:8px; }\n.provider-settings { border:0; display:flex; flex-direction:column; gap:10px; min-width:0; }\n.provider-settings label { font-size:10px; }\n.provider-settings input[type=text],.provider-settings input[type=password],.provider-settings input[type=url] { background:#02060b; border:1px solid #304661; color:#e8f2ff; padding:13px; border-radius:4px; width:100%; min-height:46px; font-size:14px; }\n.provider-status { font-size:10px; color:#92aac7; }\n.provider-status.active { color:var(--cyan); }\n.provider-status.error { color:#efad92; }\n.provider-meta { font-size:10px; color:#718eae; margin:14px 0 8px; min-height:15px; }\n.provider-output { white-space:pre-wrap; overflow-wrap:anywhere; color:#b8cfe9; line-height:1.7; font:12px/1.7 Consolas,monospace; border-top:1px solid #1a2c43; padding-top:10px; min-height:100px; max-height:300px; overflow:auto; user-select:text; }\n.network-actions { display:flex; align-items:center; flex-wrap:wrap; gap:12px; margin-top:18px; }\n.network-actions .inject-btn { width:auto; min-width:240px; }\n.network-actions input[type=number] { width:120px; min-height:46px; font-size:16px; padding:10px; }\n.network-feedback { margin-top:12px; }\n.network-note { margin-bottom:16px; }\n@media(min-height:930px) { .master-container { grid-template-rows:auto minmax(710px,1fr) auto 192px; } textarea { min-height:186px; height:186px; } }\n@media(max-width:920px) { .master-container { grid-template-columns:minmax(0,1fr); padding:12px; grid-template-rows:auto 590px auto auto 192px; } .masthead { align-items:flex-start; } .panel-header { padding:12px; } h1 { font-size:16px; } .version { display:none; } .workspace-panel { padding:18px; overflow:visible; } .network-grid { grid-template-columns:minmax(0,1fr); } }\n@media(prefers-reduced-motion:reduce) { * { transition:none !important; } }\n</style>\n</head>\n<body>\n<main class="master-container">\n  <header class="masthead">\n    <div><div class="eyebrow">HARDWARE ACTIVITY / INTENT WORKSPACE</div><h1>Microcosmic Charge Injector<span class="version">CORE / 02</span></h1></div>\n    <div id="connectionStatus" class="badge" role="status"><span class="dot"></span><span id="connectionText">CONNECTING</span></div>\n  </header>\n  <section class="panel" aria-labelledby="matrixTitle">\n    <div class="panel-header"><h2 id="matrixTitle"><span class="index">01 //</span>Active flux matrix</h2><span class="tag">CPU TELEMETRY · 500 MS</span></div>\n    <div class="telemetry-strip">\n      <div><span class="metric-label">System CPU</span><span class="metric-value primary" id="cpuValue">—</span></div>\n      <div><span class="metric-label">System RAM</span><span class="metric-value" id="ramValue">—</span></div>\n      <div><span class="metric-label">Logical CPUs</span><span class="metric-value" id="coreValue">—</span></div>\n    </div>\n    <div class="canvas-wrapper"><canvas id="fluxCanvas" role="img" aria-label="Live CPU matrix. Column activity follows measured CPU utilization; the orbit and history show total CPU usage."></canvas></div>\n    <div class="matrix-caption"><span id="matrixSource">Waiting for the local CPU sampler.</span><button class="quiet-button" id="motionButton" type="button" aria-pressed="false">Pause motion</button></div>\n  </section>\n  <section class="panel" aria-labelledby="bufferTitle">\n    <div class="panel-header"><h2 id="bufferTitle"><span class="index">02 //</span>Intent injection buffer</h2><span class="tag" id="engineState">STANDBY</span></div>\n    <form id="injectionForm" class="workspace-panel" novalidate>\n      <div class="input-group">\n        <div class="label-row"><label for="intentInput">Target identity / intent string</label><span class="counter" id="byteCounter">0 / 1,024 B</span></div>\n        <textarea id="intentInput" spellcheck="false" aria-describedby="intentHint byteCounter">INTELLIGENCE_MUTATION_ALIGNMENT_INVARIANT</textarea>\n        <p class="hint" id="intentHint">Multiline input · up to 1,024 UTF-8 bytes · preserves your full text</p>\n      </div>\n      <div class="input-group">\n        <label for="orderInput">Elevation order / multiplier</label>\n        <input type="number" id="orderInput" value="10" step="any" min="-1000000" max="1000000" required aria-describedby="orderHint">\n        <p class="hint" id="orderHint">Yield = order × 7.83 · byte transform uses the whole-number part</p>\n      </div>\n      <div>\n        <button class="inject-btn" id="injectButton" type="submit" disabled>Fire heightened charge vector ↗</button>\n        <div class="action-row" style="margin-top:10px"><p class="feedback" id="feedback" role="status" style="flex:1">Connecting to the local engine…</p><span class="shortcut">CTRL + ENTER</span></div>\n      </div>\n      <div class="buffer-card">\n        <div class="buffer-top"><span class="metric-label">Local buffer / live state</span><button type="button" class="quiet-button" id="resetButton" disabled>Reset buffer</button></div>\n        <div class="buffer-stats">\n          <div><span class="metric-label">Written</span><span class="buffer-value" id="bytesValue">0 B</span></div>\n          <div><span class="metric-label">Yield</span><span class="buffer-value" id="yieldValue">0.00</span></div>\n          <div><span class="metric-label">Dispatches</span><span class="buffer-value" id="dispatchValue">0</span></div>\n        </div>\n        <div class="meter"><div class="meter-fill" id="bufferMeter"></div></div>\n        <div class="hex-preview" id="hexPreview">BUFFER EMPTY // AWAITING DISPATCH</div>\n        <p class="hint" style="margin-top:8px">Writes to this app\'s memory buffer. The matrix independently monitors actual system CPU activity.</p>\n      </div>\n    </form>\n  </section>\n  <section class="panel network-panel" aria-labelledby="networkTitle">\n    <div class="panel-header"><h2 id="networkTitle"><span class="index">03 //</span>Llama + Gemini + ChatGPT / inference network</h2><span class="tag" id="networkFlag">ACTIVE = FALSE</span></div>\n    <div class="network-body">\n      <p class="hint network-note">Run sends the current intent above to each selected provider. Each reply appears below. Active reflects successful replies from all three in the last run; cloud API usage is billed by the provider.</p>\n      <div class="network-grid">\n        <article class="provider">\n          <div class="provider-head"><label><input type="checkbox" id="llamaEnabled" checked>Llama / local</label><span class="provider-status" id="llamaStatus">NOT TESTED</span></div>\n          <fieldset class="provider-settings" id="llamaSettings">\n            <label for="llamaModel">Ollama model</label><input id="llamaModel" type="text" value="llama3.2" spellcheck="false">\n            <label for="llamaEndpoint">Local Ollama address</label><input id="llamaEndpoint" type="url" value="http://127.0.0.1:11434" spellcheck="false">\n            <p class="hint">Use a Llama model already installed in Ollama.</p>\n          </fieldset>\n          <div class="provider-meta" id="llamaMeta">Awaiting first request</div><pre class="provider-output" id="llamaOutput">Your Llama reply will appear here.</pre>\n        </article>\n        <article class="provider">\n          <div class="provider-head"><label><input type="checkbox" id="geminiEnabled" checked>Google Gemini</label><span class="provider-status" id="geminiStatus">NEEDS KEY</span></div>\n          <fieldset class="provider-settings" id="geminiSettings">\n            <label for="geminiModel">Gemini model</label><input id="geminiModel" type="text" value="gemini-3.8-flash" spellcheck="false">\n            <label for="geminiKey">Gemini API key</label><input id="geminiKey" type="password" autocomplete="off" spellcheck="false" placeholder="Enter locally / session only">\n            <p class="hint" id="geminiKeyHint">Or set GEMINI_API_KEY before launch.</p>\n          </fieldset>\n          <div class="provider-meta" id="geminiMeta">Awaiting first request</div><pre class="provider-output" id="geminiOutput">Your Gemini reply will appear here.</pre>\n        </article>\n        <article class="provider">\n          <div class="provider-head"><label><input type="checkbox" id="openaiEnabled" checked>ChatGPT / OpenAI</label><span class="provider-status" id="openaiStatus">NEEDS KEY</span></div>\n          <fieldset class="provider-settings" id="openaiSettings">\n            <label for="openaiModel">OpenAI API model</label><input id="openaiModel" type="text" value="gpt-6-astra" spellcheck="false">\n            <label for="openaiKey">OpenAI API key</label><input id="openaiKey" type="password" autocomplete="off" spellcheck="false" placeholder="Enter locally / session only">\n            <p class="hint" id="openaiKeyHint">Or set OPENAI_API_KEY before launch.</p>\n          </fieldset>\n          <div class="provider-meta" id="openaiMeta">Awaiting first request</div><pre class="provider-output" id="openaiOutput">Your OpenAI reply will appear here.</pre>\n        </article>\n      </div>\n      <div class="network-actions">\n        <button class="inject-btn" id="runNetworkButton" type="button" disabled>Run current intent ↗</button>\n        <label for="networkTokens">Output token limit</label><input id="networkTokens" type="number" min="128" max="8192" step="1" value="4096">\n        <button class="quiet-button" id="forgetKeysButton" type="button" disabled>Forget cloud keys</button>\n      </div>\n      <p class="feedback network-feedback" id="networkFeedback" role="status">Configure the providers, then run your current intent. Keys stay in memory for this session.</p>\n    </div>\n  </section>\n  <section class="panel ledger-panel" aria-labelledby="ledgerTitle">\n    <div class="panel-header"><h2 id="ledgerTitle"><span class="index">04 //</span>Machine activity ledger</h2><div class="ledger-tools"><span class="tag">SESSION / LAST 120 EVENTS</span><button class="quiet-button" id="clearLogButton" type="button">Clear log</button></div></div>\n    <div class="ledger" id="assemblyTerminal" role="log" aria-live="polite" aria-relevant="additions"></div>\n  </section>\n</main>\n<script>\n\'use strict\';\nconst $ = id => document.getElementById(id);\nconst canvas = $(\'fluxCanvas\'), ctx = canvas.getContext(\'2d\');\nconst terminal = $(\'assemblyTerminal\'), intentIn = $(\'intentInput\'), orderIn = $(\'orderInput\');\nconst encoder = new TextEncoder();\nconst reducedMotion = window.matchMedia(\'(prefers-reduced-motion: reduce)\');\nlet paused = reducedMotion.matches, bridgeReady = false, busy = false;\nlet latest = null, lastReceived = 0, lastEvent = 0, lastRevision = -1;\nlet history = [], smoothedCPU = 0, smoothedCores = [], phase = 0, writeFlash = 0;\nlet viewWidth = 0, viewHeight = 0, lastFrame = 0, staleState = \'\';\nconst providerIds = [\'llama\',\'gemini\',\'openai\'];\nlet networkVersion = -1, networkBusy = false, networkHydrated = false;\nlet networkRequestPending = false, networkRunning = false;\n\nfunction networkFeedback(message,error=false) { $(\'networkFeedback\').textContent=message; $(\'networkFeedback\').classList.toggle(\'error\',error); }\nfunction lockNetwork(locked) {\n  networkBusy=locked || networkRequestPending;\n  $(\'runNetworkButton\').disabled=!bridgeReady || networkBusy;\n  $(\'forgetKeysButton\').disabled=!bridgeReady || networkBusy;\n  $(\'networkTokens\').disabled=networkBusy;\n  for(const id of providerIds) {$(id+\'Settings\').disabled=networkBusy;$(id+\'Enabled\').disabled=networkBusy;}\n}\nfunction applyNetwork(data) {\n  if(!data || data.version <= networkVersion) return;\n  networkVersion=data.version;\n  if(!networkHydrated) {\n    for(const id of providerIds) {$(id+\'Model\').value=data.providers[id].model;$(id+\'Enabled\').checked=data.providers[id].enabled;}\n    $(\'llamaEndpoint\').value=data.providers.llama.endpoint;networkHydrated=true;\n  }\n  $(\'networkFlag\').textContent=(data.running?\'RUNNING / \':\'LAST RUN / \')+\'ACTIVE = \'+(data.active?\'TRUE\':\'FALSE\');\n  networkRunning=data.running;lockNetwork(networkRunning);\n  for(const id of providerIds) {\n    const provider=data.providers[id],status=$(id+\'Status\');\n    status.textContent=provider.status.replaceAll(\'_\',\' \').toUpperCase();status.className=\'provider-status \'+provider.status;\n    if(provider.output || provider.error) $(id+\'Output\').textContent=provider.output || provider.error;\n    else $(id+\'Output\').textContent=provider.status===\'running\'?\'Waiting for the provider reply…\':\'Awaiting a request.\';\n    $(id+\'Meta\').textContent=provider.latency_ms!==null?`${(provider.latency_ms/1000).toFixed(2)} s · ${provider.model}`:`${provider.model} · ${provider.status.replaceAll(\'_\',\' \')}`;\n    if(id!==\'llama\') $(id+\'KeyHint\').textContent=provider.key_configured?\'Key configured for this session. Leave blank to keep it.\':`Enter an API key, or set ${id===\'openai\'?\'OPENAI_API_KEY\':\'GEMINI_API_KEY\'} before launch.`;\n  }\n  if(!data.running && data.run_id>0) {\n    const succeeded=providerIds.filter(id=>data.providers[id].status===\'active\').length;\n    networkFeedback(`${succeeded} of ${data.selected_count} selected providers returned complete replies.`,succeeded<data.selected_count);\n  }\n}\n$(\'runNetworkButton\').addEventListener(\'click\',async()=>{\n  if(!bridgeReady || networkBusy) return;\n  if(!intentIn.value.trim()) {networkFeedback(\'Enter an intent above before running inference.\',true);intentIn.focus();return;}\n  const tokens=Number($(\'networkTokens\').value);\n  if(!Number.isInteger(tokens)||tokens<128||tokens>8192) {networkFeedback(\'Choose an output limit from 128 to 8,192 tokens.\',true);return;}\n  const settings={};\n  for(const id of providerIds) settings[id]={enabled:$(id+\'Enabled\').checked,model:$(id+\'Model\').value,api_key:id===\'llama\'?\'\':$(id+\'Key\').value};\n  settings.llama.endpoint=$(\'llamaEndpoint\').value;\n  networkRequestPending=true;lockNetwork(true);networkFeedback(\'Dispatching the current intent to the selected providers…\');\n  try {\n    const result=await window.pywebview.api.run_inference_network(intentIn.value,settings,tokens);\n    applyNetwork(result.network);\n    networkFeedback(result.message,!result.ok);\n    if(result.ok) { $(\'geminiKey\').value=\'\';$(\'openaiKey\').value=\'\'; }\n  } catch(error) {networkFeedback(\'The local engine could not start the inference request.\',true);}\n  finally {networkRequestPending=false;lockNetwork(networkRunning);}\n});\n$(\'forgetKeysButton\').addEventListener(\'click\',async()=>{\n  if(!bridgeReady || networkBusy) return;networkRequestPending=true;lockNetwork(true);\n  try {const result=await window.pywebview.api.forget_inference_keys();applyNetwork(result.network);$(\'geminiKey\').value=\'\';$(\'openaiKey\').value=\'\';networkFeedback(result.message,!result.ok);}\n  catch(error) {networkFeedback(\'The local engine did not confirm key removal.\',true);}\n  finally {networkRequestPending=false;lockNetwork(networkRunning);}\n});\n\nfunction appendLog(kind, message, timestamp, error=false) {\n  const atBottom = terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 28;\n  const row = document.createElement(\'div\'); row.className = \'log-line\' + (error ? \' error\' : \'\');\n  const clock = document.createElement(\'span\'); clock.className = \'log-time\';\n  clock.textContent = new Date(timestamp || Date.now()).toLocaleTimeString(\'en-GB\', {hour12:false});\n  const label = document.createElement(\'span\'); label.className = \'log-kind\'; label.textContent = kind;\n  const text = document.createElement(\'span\'); text.className = \'log-message\'; text.textContent = message;\n  row.append(clock,label,text); terminal.appendChild(row);\n  while (terminal.children.length > 120) terminal.firstChild.remove();\n  if (atBottom) terminal.scrollTop = terminal.scrollHeight;\n}\nfunction feedback(message, error=false) { $(\'feedback\').textContent = message; $(\'feedback\').classList.toggle(\'error\',error); }\nfunction countBytes() {\n  const count = encoder.encode(intentIn.value).length;\n  $(\'byteCounter\').textContent = `${count.toLocaleString()} / 1,024 B`;\n  $(\'byteCounter\').classList.toggle(\'error\',count > 1024);\n  intentIn.setAttribute(\'aria-invalid\',String(count > 1024)); return count;\n}\nintentIn.addEventListener(\'input\',countBytes); countBytes();\norderIn.addEventListener(\'input\',() => orderIn.setAttribute(\'aria-invalid\',\'false\'));\nfunction setBusy(value) { busy = value; $(\'injectButton\').disabled = !bridgeReady || busy; $(\'resetButton\').disabled = !bridgeReady || busy; }\nfunction applyState(state) {\n  if (!state || state.revision < lastRevision) return;\n  if (lastRevision >= 0 && state.revision > lastRevision && state.bytes_written > 0) writeFlash = 1;\n  lastRevision = state.revision;\n  applyNetwork(state.network);\n  $(\'engineState\').textContent = state.engine_state;\n  $(\'bytesValue\').textContent = `${state.bytes_written.toLocaleString()} B`;\n  $(\'yieldValue\').textContent = Number(state.calculated_yield).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});\n  $(\'dispatchValue\').textContent = state.dispatch_count;\n  $(\'bufferMeter\').style.width = `${state.bytes_written / 1024 * 100}%`;\n  $(\'hexPreview\').textContent = state.bytes_written ? `HEX / ${state.hex_preview}\\nBUFFER / ${state.memory_address}` : \'BUFFER EMPTY // AWAITING DISPATCH\';\n  for (const event of state.events || []) {\n    if (event.id <= lastEvent) continue;\n    appendLog(event.kind,event.message,event.timestamp,event.kind === \'BLOCKED\'); lastEvent = event.id;\n  }\n}\nfunction updateMachineLogStream(data) {\n  if (typeof data === \'string\') data = JSON.parse(data);\n  latest = data; lastReceived = performance.now();\n  const cpu = data.cpu;\n  $(\'cpuValue\').textContent = cpu.available ? `${cpu.total.toFixed(1)}%` : \'—\';\n  $(\'ramValue\').textContent = Number.isFinite(cpu.memory_percent) ? `${cpu.memory_percent.toFixed(1)}%` : \'—\';\n  $(\'coreValue\').textContent = cpu.logical_cpus || \'—\';\n  $(\'matrixSource\').textContent = cpu.available ? `${cpu.per_core.length ? \'Columns follow logical CPU load\' : \'Columns follow total CPU load\'} · ${cpu.source}` : (cpu.error || \'CPU telemetry unavailable\');\n  const now = performance.now();\n  history.push({time:now,value:cpu.available ? cpu.total : null});\n  history = history.filter(point => now - point.time <= 60000).slice(-121);\n  applyState(data.state); updateConnection();\n}\nwindow.updateMachineLogStream = updateMachineLogStream;\nfunction updateConnection() {\n  const stale = lastReceived && performance.now() - lastReceived > 2500;\n  const available = latest && latest.cpu.available;\n  const next = !lastReceived ? \'CONNECTING\' : stale ? \'SIGNAL LOST\' : available ? \'LIVE / LOCAL\' : \'CPU UNAVAILABLE\';\n  if (next === staleState) return;\n  staleState = next; $(\'connectionText\').textContent = next;\n  $(\'connectionStatus\').className = \'badge \' + (next === \'LIVE / LOCAL\' ? \'live\' : \'stale\');\n  if (stale || (latest && !available)) { $(\'cpuValue\').textContent = \'—\'; $(\'ramValue\').textContent = \'—\'; }\n  if (stale) appendLog(\'TELEMETRY\',\'CPU signal lost; awaiting fresh measurements.\');\n}\nfunction onBridgeReady() {\n  if (bridgeReady || !window.pywebview || !window.pywebview.api) return;\n  bridgeReady = true; setBusy(false); feedback(\'Ready for local buffer dispatch.\');\n  lockNetwork(networkBusy);\n}\nwindow.addEventListener(\'pywebviewready\',onBridgeReady); onBridgeReady();\nsetTimeout(() => { if (!bridgeReady) feedback(\'Waiting for the desktop engine. Open this interface through the Python app.\'); },5000);\nasync function executeHeightenedChargeInjection() {\n  if (!bridgeReady || busy) return;\n  const byteCount = countBytes(), factor = Number(orderIn.value);\n  if (!intentIn.value.trim() || byteCount > 1024) {\n    intentIn.setAttribute(\'aria-invalid\',\'true\'); intentIn.focus();\n    feedback(byteCount > 1024 ? \'Intent exceeds 1,024 UTF-8 bytes. Shorten the text to continue.\' : \'Enter an intent before dispatching.\',true); return;\n  }\n  if (!orderIn.value.trim() || !Number.isFinite(factor) || Math.abs(factor) > 1000000) {\n    orderIn.setAttribute(\'aria-invalid\',\'true\'); orderIn.focus(); feedback(\'Enter a finite multiplier between −1,000,000 and 1,000,000.\',true); return;\n  }\n  setBusy(true); feedback(\'Writing local buffer…\');\n  try {\n    const result = await window.pywebview.api.inject_heightened_charge_substrate(intentIn.value,orderIn.value);\n    applyState(result.state); feedback(result.message,!result.ok);\n  } catch (error) { feedback(\'Dispatch failed. The local engine is unavailable.\',true); appendLog(\'BRIDGE\',\'Dispatch could not reach the local engine.\',null,true); }\n  finally { setBusy(false); }\n}\n$(\'injectionForm\').addEventListener(\'submit\',event => {event.preventDefault(); executeHeightenedChargeInjection();});\ndocument.addEventListener(\'keydown\',event => { if ((event.ctrlKey || event.metaKey) && event.key === \'Enter\') { event.preventDefault(); executeHeightenedChargeInjection(); } });\n$(\'resetButton\').addEventListener(\'click\',async () => {\n  if (busy || !bridgeReady) return; setBusy(true);\n  try { const result = await window.pywebview.api.reset_buffer(); applyState(result.state); feedback(result.message); }\n  catch (error) { feedback(\'Reset failed. The local engine is unavailable.\',true); }\n  finally { setBusy(false); }\n});\n$(\'clearLogButton\').addEventListener(\'click\',() => {terminal.replaceChildren(); appendLog(\'LEDGER\',\'Visible log cleared. New events will appear here.\');});\nfunction syncMotionButton() { $(\'motionButton\').textContent = paused ? \'Resume motion\' : \'Pause motion\'; $(\'motionButton\').setAttribute(\'aria-pressed\',String(paused)); }\n$(\'motionButton\').addEventListener(\'click\',() => {paused = !paused; syncMotionButton();}); syncMotionButton();\nfunction resize() {\n  const bounds = canvas.parentElement.getBoundingClientRect();\n  viewWidth = bounds.width; viewHeight = bounds.height;\n  const dpr = Math.min(window.devicePixelRatio || 1,2);\n  canvas.width = Math.round(viewWidth*dpr); canvas.height = Math.round(viewHeight*dpr);\n  ctx.setTransform(dpr,0,0,dpr,0,0);\n}\nnew ResizeObserver(resize).observe(canvas.parentElement); window.addEventListener(\'resize\',resize);\nfunction text(value,x,y,color=\'#6d88aa\',size=10,align=\'left\') { ctx.fillStyle=color; ctx.font=`${size}px Consolas, monospace`; ctx.textAlign=align; ctx.fillText(value,x,y); }\nfunction line(x1,y1,x2,y2,color,width=1) {ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}\nfunction renderSystemMatrix(now) {\n  requestAnimationFrame(renderSystemMatrix);\n  if (document.hidden || now-lastFrame < (paused ? 180 : 32)) return;\n  const dt = Math.min((now-lastFrame)/1000,.2); lastFrame=now; updateConnection();\n  const w=viewWidth,h=viewHeight; if (!w || !h) return;\n  const live=latest && latest.cpu.available && now-lastReceived <= 2500;\n  const target=live ? latest.cpu.total/100 : 0;\n  const blend=paused ? 1 : 1-Math.exp(-dt*7);\n  smoothedCPU += (target-smoothedCPU)*blend;\n  const measured = live ? (latest.cpu.per_core.length ? latest.cpu.per_core : [latest.cpu.total]) : [0];\n  const cols=Math.max(1,Math.min(measured.length===1 ? 16 : measured.length,Math.floor((w-34)/18),32));\n  const groups=Array.from({length:cols},(_,c) => {\n    if (measured.length===1) return measured[0]/100;\n    const start=Math.floor(c*measured.length/cols),end=Math.floor((c+1)*measured.length/cols);\n    return measured.slice(start,end).reduce((a,b)=>a+b,0)/(end-start)/100;\n  });\n  smoothedCores=groups.map((load,i) => (smoothedCores[i] || 0)+(load-(smoothedCores[i] || 0))*blend);\n  if (!paused && live) phase += dt*(.08+smoothedCPU*2.8);\n  writeFlash=Math.max(0,writeFlash-dt*1.5);\n  ctx.clearRect(0,0,w,h);\n  const glow=ctx.createRadialGradient(w/2,h*.54,0,w/2,h*.54,w*.65);\n  glow.addColorStop(0,`rgba(25,74,130,${.08+smoothedCPU*.18})`);glow.addColorStop(1,\'rgba(4,8,14,0)\');ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);\n  for(let x=10;x<w;x+=24) line(x,0,x,h,\'#17294133\');\n  for(let y=8;y<h;y+=24) line(0,y,w,y,\'#17294133\');\n  text(live ? (measured.length>cols ? \'LOGICAL CPU GROUPS / AVERAGE LOAD\' : measured.length===1 ? \'SYSTEM LOAD / ACTIVITY MATRIX\' : \'LOGICAL CPU / ACTIVITY MATRIX\') : \'CPU MATRIX / WAITING FOR SIGNAL\',12,15);\n  const gridTop=37,gridHeight=Math.min(132,h*.29),rows=9,step=(w-30)/cols;\n  for(let c=0;c<cols;c++) {\n    const activity=smoothedCores[c],x=16+(c+.5)*step;\n    for(let r=0;r<rows;r++) {\n      const threshold=(rows-r-.5)/rows,lit=live && activity>=threshold;\n      const bit=lit ? ((c*7+r*3+Math.floor(phase*(1+activity*4)))%2 ? \'1\':\'0\') : \'0\';\n      text(bit,x,gridTop+r*(gridHeight/rows),lit ? `rgba(167,211,255,${.5+activity*.5})` : \'#244263\',Math.min(12,step*.62),\'center\');\n    }\n    ctx.fillStyle=live?\'#4d9cf0\':\'#254361\';ctx.fillRect(x-step*.27,gridTop+gridHeight+2,step*.54,2+activity*5);\n    if (cols<=20 || c%2===0) text(measured.length===1 ? \'\' : String(c+1).padStart(2,\'0\'),x,gridTop+gridHeight+22,\'#6882a2\',8,\'center\');\n  }\n  const historyTop=h-67, orbitTop=gridTop+gridHeight+37;\n  const cy=(orbitTop+historyTop)/2, cx=w/2, radius=Math.max(30,Math.min(64,(historyTop-orbitTop)/2-13,w*.16));\n  ctx.beginPath();ctx.arc(cx,cy,radius+13,0,Math.PI*2);ctx.strokeStyle=\'#203b5c\';ctx.lineWidth=1;ctx.stroke();\n  for(let i=0;i<48;i++) {\n    const a=i/48*Math.PI*2-Math.PI/2;\n    line(cx+Math.cos(a)*(radius+18),cy+Math.sin(a)*(radius+18),cx+Math.cos(a)*(radius+22),cy+Math.sin(a)*(radius+22),live && i/48<smoothedCPU?\'#8dccff\':\'#1a304c\',1.5);\n  }\n  ctx.beginPath();ctx.arc(cx,cy,radius,-Math.PI/2,Math.PI*2-Math.PI/2);ctx.strokeStyle=\'#1c3c62\';ctx.lineWidth=2;ctx.stroke();\n  if(live && smoothedCPU>0) {ctx.beginPath();ctx.arc(cx,cy,radius,-Math.PI/2,smoothedCPU*Math.PI*2-Math.PI/2);ctx.strokeStyle=\'#6eb9ff\';ctx.shadowColor=\'#4b9ef4\';ctx.shadowBlur=10;ctx.lineWidth=2.5;ctx.stroke();ctx.shadowBlur=0;}\n  for(let i=0;i<4;i++) {\n    const a=i/4*Math.PI*2+phase,x=cx+Math.cos(a)*radius,y=cy+Math.sin(a)*radius;\n    ctx.beginPath();ctx.arc(x,y,2+smoothedCPU*2.5,0,Math.PI*2);ctx.fillStyle=live?(i%2?\'#66aaf7\':\'#d7ecff\'):\'#34516f\';ctx.fill();\n  }\n  if(writeFlash>0 && !paused) {ctx.beginPath();ctx.arc(cx,cy,radius+24+(1-writeFlash)*13,0,Math.PI*2);ctx.strokeStyle=`rgba(114,222,235,${writeFlash*.65})`;ctx.lineWidth=1;ctx.stroke();}\n  text(live ? `${latest.cpu.total.toFixed(1)}%` : \'—\',cx,cy+3,\'#d6eaff\',Math.max(18,radius*.37),\'center\');\n  text(\'CPU LOAD\',cx,cy+19,\'#7698c0\',8,\'center\');\n  if(w>460) {\n    text(\'MICROCOSMIC\',22,cy-9,\'#6582a5\',9);text(\'ORBIT / 01\',22,cy+7,\'#96b7de\',10);\n    text(\'FLUX RESPONSE\',w-22,cy-9,\'#6582a5\',9,\'right\');text(paused?\'MOTION PAUSED\':live?\'LIVE CPU\':\'NO SIGNAL\',w-22,cy+7,\'#96b7de\',10,\'right\');\n  }\n  line(12,historyTop-7,w-12,historyTop-7,\'#1b304a\');\n  text(\'CPU HISTORY / 60 SEC\',12,historyTop+8,\'#6d88aa\',9);\n  text(\'100%\',w-12,historyTop+8,\'#587390\',8,\'right\');\n  const chartTop=historyTop+18,chartBottom=h-8,chartW=w-26;\n  line(13,chartBottom,w-13,chartBottom,\'#1c3554\');\n  ctx.beginPath(); let connected=false,lastTime=0;\n  for(const point of history) {\n    if(now-point.time>60000) continue;\n    if(point.value===null) {connected=false;continue;}\n    const x=13+chartW*(1-(now-point.time)/60000),y=chartBottom-point.value/100*(chartBottom-chartTop);\n    if(connected && point.time-lastTime<1600) ctx.lineTo(x,y); else ctx.moveTo(x,y);\n    connected=true;lastTime=point.time;\n  }\n  ctx.strokeStyle=\'#5ea9ff\';ctx.lineWidth=1.5;ctx.stroke();\n}\nappendLog(\'SYSTEM\',\'Initializing local memory buffer and live CPU telemetry.\');\nresize();requestAnimationFrame(renderSystemMatrix);\n</script>\n</body>\n</html>'

class WindowsCPUCounter:
    """System CPU from Windows' cumulative idle/kernel/user counters.

    GetSystemTimes includes idle time in kernel time. Two samples are required.
    This fallback deliberately reports aggregate load, never invented per-core data.
    """

    def __init__(self):
        from ctypes import wintypes
        self.filetime = wintypes.FILETIME
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel32.GetSystemTimes.argtypes = [ctypes.POINTER(self.filetime)] * 3
        self.kernel32.GetSystemTimes.restype = wintypes.BOOL
        self.previous = self._read()

    def _read(self):
        idle, kernel, user = (self.filetime(), self.filetime(), self.filetime())
        if not self.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            raise ctypes.WinError(ctypes.get_last_error())
        return tuple((v.dwHighDateTime << 32 | v.dwLowDateTime for v in (idle, kernel, user)))

    def sample(self):
        current = self._read()
        idle, kernel, user = (now - before for now, before in zip(current, self.previous))
        self.previous = current
        total = kernel + user
        if total <= 0 or min(idle, kernel, user) < 0:
            raise RuntimeError('CPU counters have not advanced; waiting for another sample.')
        return round(max(0.0, min(100.0, 100.0 * (total - idle) / total)), 1)

class CPUSampler:
    """Created and sampled on the same worker thread so psutil deltas are valid."""

    def __init__(self):
        self.logical_cpus = os.cpu_count() or 1
        self.native = None
        self.error = None
        self.use_psutil = False
        if psutil is not None:
            try:
                psutil.cpu_percent(interval=None)
                psutil.cpu_percent(interval=None, percpu=True)
                self.use_psutil = True
            except (OSError, RuntimeError):
                pass
        if not self.use_psutil:
            try:
                if os.name != 'nt':
                    raise RuntimeError('Install psutil to enable CPU telemetry on this platform.')
                self.native = WindowsCPUCounter()
            except (OSError, RuntimeError) as error:
                self.error = str(error)

    def sample(self):
        result = {'available': False, 'total': None, 'per_core': [], 'logical_cpus': self.logical_cpus, 'memory_percent': None, 'source': 'psutil' if self.use_psutil else 'Windows CPU counters'}
        try:
            if self.use_psutil:
                result['total'] = psutil.cpu_percent(interval=None)
                result['per_core'] = psutil.cpu_percent(interval=None, percpu=True)
                result['logical_cpus'] = len(result['per_core']) or self.logical_cpus
                try:
                    result['memory_percent'] = psutil.virtual_memory().percent
                except (OSError, RuntimeError):
                    pass
            elif self.native is not None:
                result['total'] = self.native.sample()
            else:
                raise RuntimeError(self.error or 'CPU telemetry unavailable.')
            values = [result['total'], *result['per_core']]
            if not all((math.isfinite(value) and 0 <= value <= 100 for value in values)):
                raise RuntimeError('CPU sampler returned an invalid reading.')
            result['available'] = True
        except (OSError, RuntimeError, ValueError) as error:
            result.update(total=None, per_core=[], error=str(error))
        return result

class NoProviderRedirects(urlrequest.HTTPRedirectHandler):
    """Never forward prompts or authentication headers to a redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class InferenceNetwork:
    """Three independent provider requests, with session-only credentials.

    API contracts: developers.openai.com/api/docs/guides/text,
    ai.google.dev/api/generate-content, docs.ollama.com/api/chat.
    'active' describes complete replies from all three in the latest run.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._closed = False
        self._version = 0
        self._run_id = 0
        self._remaining = 0
        self._selected_count = 0
        self._config = {'llama': {'enabled': True, 'model': os.getenv('OLLAMA_MODEL', 'llama3.2'), 'endpoint': os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434'), 'api_key': ''}, 'gemini': {'enabled': True, 'model': os.getenv('GEMINI_MODEL', 'gemini-3.8-flash'), 'api_key': os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY', '')}, 'openai': {'enabled': True, 'model': os.getenv('OPENAI_MODEL', 'gpt-6-astra'), 'api_key': os.getenv('OPENAI_API_KEY', '')}}
        self._results = {name: self._empty_result(name) for name in self._config}

    def _empty_result(self, name):
        config = self._config[name]
        return {'status': 'not_tested' if name == 'llama' or config['api_key'] else 'needs_key', 'output': '', 'error': '', 'latency_ms': None}

    def _snapshot(self):
        with self._lock:
            providers = {}
            for name, config in self._config.items():
                providers[name] = {key: value for key, value in config.items() if key != 'api_key'}
                providers[name].update(self._results[name])
                providers[name]['key_configured'] = bool(config['api_key'])
            return {'version': self._version, 'run_id': self._run_id, 'running': self._remaining > 0, 'selected_count': self._selected_count, 'active': self._run_id > 0 and self._remaining == 0 and all((p['enabled'] and p['status'] == 'active' for p in providers.values())), 'providers': providers}

    def _reply(self, ok, message):
        return {'ok': ok, 'message': message, 'network': self._snapshot()}

    @staticmethod
    def _local_endpoint(value):
        if not isinstance(value, str):
            raise ValueError('Enter a local Ollama address.')
        try:
            parsed = urlparse.urlsplit(value.strip())
            _ = parsed.port
        except ValueError:
            raise ValueError('Check the local Ollama address and port.') from None
        if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password or parsed.query or parsed.fragment or (parsed.path not in ('', '/')):
            raise ValueError('Use a local Ollama address such as http://127.0.0.1:11434.')
        return value.strip().rstrip('/')

    def run(self, prompt, settings, max_tokens):
        with self._lock:
            if self._closed:
                return self._reply(False, 'The inference engine is closing.')
            if self._remaining:
                return self._reply(False, 'A network run is already in progress.')
            try:
                if not isinstance(prompt, str) or not prompt.strip():
                    raise ValueError('Enter a non-empty intent to run inference.')
                if len(prompt.encode('utf-8')) > 32768:
                    raise ValueError('Inference prompts are limited to 32,768 UTF-8 bytes.')
                if type(max_tokens) is not int or not 128 <= max_tokens <= 8192:
                    raise ValueError('Choose an output limit from 128 to 8,192 tokens.')
                if not isinstance(settings, dict):
                    raise ValueError('Provider settings must be an object.')
                staged = {}
                for name, previous in self._config.items():
                    raw = settings.get(name, previous)
                    if not isinstance(raw, dict) or type(raw.get('enabled', True)) is not bool:
                        raise ValueError('Each provider needs valid settings and an enabled checkbox.')
                    model = raw.get('model', previous['model'])
                    if not isinstance(model, str):
                        raise ValueError('Model names must be text.')
                    model = model.strip()
                    if raw.get('enabled', True) and (not model or not re.fullmatch('[A-Za-z0-9_.:/-]{1,200}', model)):
                        raise ValueError(f'Enter a valid model name for {name}.')
                    key = raw.get('api_key', '')
                    if not isinstance(key, str) or len(key) > 4096 or any((ord(char) < 32 for char in key)):
                        raise ValueError('API keys must be single-line text.')
                    staged[name] = {'enabled': raw.get('enabled', True), 'model': model, 'api_key': key.strip() or previous['api_key']}
                    if name == 'llama':
                        endpoint = raw.get('endpoint', previous['endpoint'])
                        staged[name]['endpoint'] = self._local_endpoint(endpoint) if staged[name]['enabled'] else previous['endpoint']
                if not any((p['enabled'] for p in staged.values())):
                    raise ValueError('Select at least one inference provider.')
            except UnicodeError:
                return self._reply(False, 'The prompt contains an invalid Unicode sequence.')
            except (TypeError, ValueError) as exception:
                return self._reply(False, str(exception))
            self._config = staged
            self._run_id += 1
            self._version += 1
            run_id = self._run_id
            self._selected_count = sum((p['enabled'] for p in staged.values()))
            ready = []
            for name, config in staged.items():
                self._results[name] = self._empty_result(name)
                if not config['enabled']:
                    self._results[name]['status'] = 'disabled'
                elif name != 'llama' and (not config['api_key']):
                    self._results[name].update(status='needs_key', error="Add this provider's API key, then run again.")
                else:
                    self._results[name]['status'] = 'running'
                    ready.append((name, dict(config)))
            self._remaining = len(ready)
            for name, config in ready:
                worker = threading.Thread(target=self._run_provider, args=(run_id, name, config, prompt, max_tokens), daemon=True)
                try:
                    worker.start()
                except RuntimeError:
                    self._remaining -= 1
                    self._results[name].update(status='error', error='The local request worker could not start.')
            if not ready:
                return self._reply(False, 'Add an API key for at least one selected cloud provider.')
            if not self._remaining:
                return self._reply(False, 'The local request workers could not start. Please restart the app.')
            return self._reply(True, f'Started {len(ready)} provider request(s). Missing keys are shown on their cards.')

    @staticmethod
    def _request_json(url, body, headers, local=False):
        handlers = [NoProviderRedirects()]
        if local:
            handlers.append(urlrequest.ProxyHandler({}))
        opener = urlrequest.build_opener(*handlers)
        request = urlrequest.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json', **headers}, method='POST')
        with opener.open(request, timeout=INFERENCE_TIMEOUT) as response:
            content = response.read(2000001)
        if len(content) > 2000000:
            raise ValueError('Response too large.')
        data = json.loads(content.decode('utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Expected an object response.')
        return data

    def _infer(self, name, config, prompt, max_tokens):
        model, key = (config['model'], config['api_key'])
        complete = True
        if name == 'llama':
            data = self._request_json(config['endpoint'] + '/api/chat', {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'stream': False, 'options': {'num_predict': max_tokens}}, {}, local=True)
            text = data.get('message', {}).get('content', '')
            complete = data.get('done', False) and data.get('done_reason') != 'length'
        elif name == 'gemini':
            model_path = urlparse.quote(model.removeprefix('models/'), safe='')
            data = self._request_json(f'https://generativelanguage.googleapis.com/v1beta/models/{model_path}:generateContent', {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}], 'generationConfig': {'maxOutputTokens': max_tokens}}, {'x-goog-api-key': key})
            candidates = data.get('candidates') or []
            candidate = candidates[0] if candidates else {}
            text = '\n'.join((part['text'] for part in candidate.get('content', {}).get('parts', []) if isinstance(part.get('text'), str) and (not part.get('thought', False))))
            complete = candidate.get('finishReason') == 'STOP'
        else:
            data = self._request_json('https://api.openai.com/v1/responses', {'model': model, 'input': prompt, 'max_output_tokens': max_tokens, 'store': False}, {'Authorization': 'Bearer ' + key})
            chunks = []
            for item in data.get('output', []):
                if item.get('type') != 'message':
                    continue
                for part in item.get('content', []):
                    if part.get('type') == 'output_text' and isinstance(part.get('text'), str):
                        chunks.append(part['text'])
                    elif part.get('type') == 'refusal' and isinstance(part.get('refusal'), str):
                        chunks.append(part['refusal'])
            text = '\n'.join(chunks)
            complete = data.get('status') == 'completed'
        if not isinstance(text, str) or not text.strip():
            return {'status': 'error', 'output': '', 'error': 'The provider returned no displayable text. Check the model, output limit, or provider restrictions.'}
        if len(text) > 32000:
            text = text[:32000] + '\n[Display limited to 32,000 characters.]'
        if not complete:
            text += '\n\n[Partial response. Try a larger output limit or check the provider.]'
        return {'status': 'active' if complete else 'partial', 'output': text, 'error': ''}

    def _run_provider(self, run_id, name, config, prompt, max_tokens):
        started = time.perf_counter()
        try:
            result = self._infer(name, config, prompt, max_tokens)
        except urlerror.HTTPError as error:
            messages = {400: 'Request rejected. Check the model and output settings.', 401: 'API key rejected. Check the key for this provider.', 403: 'Access denied. Check the key and model permissions.', 404: 'Model or endpoint not found. For Llama, check the installed Ollama model.', 429: 'Provider quota or rate limit reached. Check usage and retry later.'}
            result = {'status': 'error', 'output': '', 'error': messages.get(error.code, f'Provider returned HTTP {error.code}. Please retry later.')}
            error.close()
        except (TimeoutError, urlerror.URLError, OSError):
            result = {'status': 'error', 'output': '', 'error': 'No response within the connection limit. Check Ollama or your network connection.'}
        except Exception:
            result = {'status': 'error', 'output': '', 'error': 'The provider returned an unexpected response.'}
        result['latency_ms'] = round((time.perf_counter() - started) * 1000)
        with self._lock:
            if self._closed or run_id != self._run_id:
                return
            self._results[name] = result
            self._remaining -= 1
            self._version += 1

    def forget_keys(self):
        with self._lock:
            if self._remaining:
                return self._reply(False, 'Wait for the current requests to finish before clearing keys.')
            for name in ('gemini', 'openai'):
                self._config[name]['api_key'] = ''
                self._results[name] = self._empty_result(name)
            self._version += 1
            return self._reply(True, 'Cloud keys removed from this app session. Environment variables were not changed.')

    def close(self):
        with self._lock:
            self._closed = True
            for config in self._config.values():
                config['api_key'] = ''
            self._remaining = 0

class MetaphysicalChargeInjectorAPI:
    """Thread-safe intent transformations within the app's own fixed-size buffer."""

    def __init__(self):
        self._lock = threading.RLock()
        self._buffer = bytearray(BUFFER_CAPACITY)
        self._bytes_written = 0
        self._yield = 0.0
        self._dispatch_count = 0
        self._revision = 0
        self._event_id = 0
        self._events = deque(maxlen=120)
        self._engine_state = 'STANDBY'
        self._network = InferenceNetwork()
        self._log('ENGINE', 'Local 1,024-byte buffer ready. CPU telemetry is independent of dispatches.')

    def _log(self, kind, message):
        self._event_id += 1
        self._events.append({'id': self._event_id, 'kind': kind, 'message': message, 'timestamp': int(time.time() * 1000)})

    def _snapshot(self):
        with self._lock:
            address = ctypes.addressof(ctypes.c_ubyte.from_buffer(self._buffer))
            return {'revision': self._revision, 'engine_state': self._engine_state, 'bytes_written': self._bytes_written, 'capacity': BUFFER_CAPACITY, 'calculated_yield': self._yield, 'dispatch_count': self._dispatch_count, 'memory_address': f'0x{address:X}', 'hex_preview': self._buffer[:min(self._bytes_written, 32)].hex(' ').upper(), 'events': list(self._events), 'network': self._network._snapshot()}

    def run_inference_network(self, prompt, settings, max_tokens=4096):
        result = self._network.run(prompt, settings, max_tokens)
        with self._lock:
            self._log('INFERENCE', result['message'])
        return result

    def forget_inference_keys(self):
        return self._network.forget_keys()

    def inject_heightened_charge_substrate(self, intent_string, order_multiplier_string):
        """Validate first, then atomically replace the buffer; rejected input leaves it intact."""
        with self._lock:
            try:
                if not isinstance(intent_string, str) or not intent_string.strip():
                    raise ValueError('Enter a non-empty intent string.')
                encoded = intent_string.encode('utf-8')
                if len(encoded) > BUFFER_CAPACITY:
                    raise ValueError(f'Intent is {len(encoded):,} UTF-8 bytes; the limit is {BUFFER_CAPACITY:,}.')
                order = float(order_multiplier_string)
                if not math.isfinite(order) or abs(order) > MAX_ORDER:
                    raise ValueError('Multiplier must be finite and between -1,000,000 and 1,000,000.')
                mask = int(order) & 255
                transformed = bytes((value ^ mask for value in encoded))
            except (TypeError, ValueError, OverflowError) as error:
                message = str(error)
                self._log('BLOCKED', message)
                return {'ok': False, 'message': message, 'state': self._snapshot()}
            self._buffer[:] = transformed + bytes(BUFFER_CAPACITY - len(transformed))
            self._bytes_written = len(transformed)
            self._yield = order * CARRIER_FREQUENCY
            self._dispatch_count += 1
            self._revision += 1
            self._engine_state = 'BUFFER LOADED'
            message = f'Dispatch {self._dispatch_count:04d} complete · {len(transformed):,} bytes written · yield {self._yield:,.2f}'
            self._log('DISPATCH', f'{message} · XOR 0x{mask:02X}')
            return {'ok': True, 'message': message, 'state': self._snapshot()}

    def reset_buffer(self):
        with self._lock:
            self._buffer[:] = bytes(BUFFER_CAPACITY)
            self._bytes_written = 0
            self._yield = 0.0
            self._revision += 1
            self._engine_state = 'STANDBY'
            self._log('RESET', 'Buffer cleared. Session dispatch count retained.')
            return {'ok': True, 'message': 'Local buffer reset.', 'state': self._snapshot()}

def schumann_carrier_broadcast_loop(window, api, stop_event, ready_event):
    """Send real measurements at 2 Hz; wait for the page and stop when it closes."""
    for _shared_tick in range(1):
        if stop_event.is_set():
            return
    sampler = CPUSampler()
    for _shared_tick in range(1):
        payload = {'cpu': sampler.sample(), 'state': api._snapshot()}
        script = 'window.updateMachineLogStream(' + json.dumps(payload, ensure_ascii=True, allow_nan=False) + ');'
        try:
            window.evaluate_js(script)
        except Exception:
            if stop_event.is_set():
                break

def main():
    try:
        import webview
    except ImportError:
        raise SystemExit('[ERROR] Missing pywebview. Install with: python -m pip install pywebview')
    api = MetaphysicalChargeInjectorAPI()
    stop_event, ready_event = (threading.Event(), threading.Event())
    window = webview.create_window('Microcosmic Charge Injector Core / Live CPU', html=HTML_LAYOUT, width=1440, height=960, min_size=(760, 680), background_color='#030508', js_api=api)
    window.events.loaded += ready_event.set
    window.events.closed += stop_event.set
    try:
        webview.start(schumann_carrier_broadcast_loop, (window, api, stop_event, ready_event))
    finally:
        stop_event.set()
        api._network.close()
