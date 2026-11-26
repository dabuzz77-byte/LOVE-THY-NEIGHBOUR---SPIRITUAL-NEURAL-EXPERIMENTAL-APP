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
import threading
import time
from collections import deque
from urllib import error as urlerror, parse as urlparse, request as urlrequest

try:
    import psutil
except ImportError:
    psutil = None

CARRIER_FREQUENCY = 7.83  # Preserved arithmetic coefficient; not a hardware clock.
TELEMETRY_INTERVAL = 0.5
BUFFER_CAPACITY = 1024
MAX_ORDER = 1_000_000
INFERENCE_TIMEOUT = 60

HTML_LAYOUT = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Microcosmic Charge Injector Core</title>
<style>
:root { color-scheme: dark; --bg:#030508; --panel:#080d17; --line:#1d2c42; --muted:#8597ae; --blue:#65a9ff; --ice:#dceeff; --cyan:#72deeb; }
* { box-sizing:border-box; margin:0; padding:0; }
body { background:var(--bg); color:#d5e1f1; font:13px 'Cascadia Code',Consolas,monospace; min-width:360px; }
button,input,textarea { font:inherit; }
button { cursor:pointer; }
button:disabled { cursor:wait; opacity:.45; }
button:focus-visible { outline:2px solid var(--cyan); outline-offset:3px; }
::selection { background:#234b7e; color:white; }
::-webkit-scrollbar { width:7px; height:7px; }
::-webkit-scrollbar-thumb { background:#263c57; border-radius:4px; }
.master-container { display:grid; grid-template-columns:minmax(0,1.12fr) minmax(400px,1fr); grid-template-rows:auto minmax(660px,1fr) auto 192px; gap:14px; padding:20px; min-height:100vh; }
.masthead { grid-column:1/-1; display:flex; align-items:center; justify-content:space-between; gap:16px; padding:1px 2px 7px; }
.eyebrow { color:var(--blue); font-size:10px; letter-spacing:.23em; margin-bottom:6px; }
h1 { font-size:20px; font-weight:500; letter-spacing:.035em; color:#e7f1ff; }
.version { font-size:11px; color:var(--muted); margin-left:10px; }
.badge { font-size:10px; letter-spacing:.1em; color:var(--muted); white-space:nowrap; display:flex; align-items:center; gap:8px; }
.dot { width:6px; height:6px; border-radius:50%; background:currentColor; box-shadow:0 0 10px currentColor; }
.badge.live { color:var(--cyan); }
.badge.stale { color:#efbf77; }
.panel { min-width:0; border:1px solid var(--line); border-radius:5px; background:linear-gradient(135deg,#0a1220,#060a12 75%); display:flex; flex-direction:column; overflow:hidden; }
.panel-header { min-height:43px; border-bottom:1px solid var(--line); padding:12px 16px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
h2 { font-size:10px; font-weight:500; text-transform:uppercase; letter-spacing:.15em; color:#a2b4cc; }
.index { color:var(--blue); margin-right:10px; }
.tag { color:#6685ab; font-size:10px; white-space:nowrap; }
.telemetry-strip { display:grid; grid-template-columns:1.2fr 1fr 1fr; padding:19px 20px 13px; gap:10px; }
.metric-label { color:var(--muted); text-transform:uppercase; letter-spacing:.09em; font-size:10px; }
.metric-value { display:block; color:var(--ice); font-size:27px; margin-top:7px; font-variant-numeric:tabular-nums; }
.metric-value.primary { color:var(--blue); }
.metric-value small { font-size:12px; color:var(--muted); }
.canvas-wrapper { min-height:365px; flex:1; position:relative; margin:0 12px; }
canvas { width:100%; height:100%; display:block; position:absolute; inset:0; }
.matrix-caption { display:flex; justify-content:space-between; align-items:center; gap:14px; padding:12px 18px; border-top:1px solid #142235; color:var(--muted); font-size:10px; line-height:1.5; }
.quiet-button { color:#9ab7db; border:1px solid #2a405d; background:#0a1525; border-radius:3px; padding:8px 11px; font-size:10px; white-space:nowrap; }
.quiet-button:hover { border-color:#5a94d8; background:#10243d; color:#e4f1ff; }
.workspace-panel { display:flex; flex-direction:column; gap:19px; padding:22px; flex:1; min-height:0; overflow:auto; }
.input-group { display:flex; flex-direction:column; gap:9px; }
.label-row { display:flex; justify-content:space-between; align-items:center; gap:10px; }
label { color:#bdcce0; font-size:11px; text-transform:uppercase; letter-spacing:.07em; }
.counter { color:var(--muted); font-size:10px; white-space:nowrap; }
textarea,input[type=number] { background:#03070d; border:1px solid #304661; color:#e8f2ff; padding:15px 16px; border-radius:4px; outline:none; width:100%; transition:border-color .15s,box-shadow .15s; }
textarea { min-height:158px; height:158px; resize:vertical; font-size:16px; line-height:1.65; }
input[type=number] { min-height:57px; font-size:22px; font-variant-numeric:tabular-nums; }
textarea:focus,input:focus { border-color:#589deb; box-shadow:0 0 0 3px #285da822; }
[aria-invalid=true] { border-color:#ec9d83 !important; }
.hint { font-size:10px; color:var(--muted); line-height:1.55; }
.inject-btn { background:linear-gradient(100deg,#153867,#10284b); border:1px solid #4386d9; color:#b7d8ff; min-height:51px; padding:14px; font-size:11px; font-weight:bold; border-radius:3px; letter-spacing:.08em; text-transform:uppercase; width:100%; box-shadow:inset 0 1px #80b9ff16; }
.inject-btn:hover:enabled { background:linear-gradient(100deg,#1c4d88,#163965); box-shadow:0 0 22px #387acc18; }
.action-row { display:flex; gap:12px; align-items:center; }
.shortcut { font-size:10px; color:var(--muted); white-space:nowrap; }
.feedback { min-height:17px; color:var(--cyan); font-size:11px; line-height:1.5; overflow-wrap:anywhere; }
.feedback.error,.counter.error { color:#f3ad93; }
.buffer-card { border-top:1px solid var(--line); padding-top:16px; margin-top:auto; }
.buffer-top { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px; }
.buffer-stats { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }
.buffer-value { display:block; margin-top:7px; font-size:16px; color:#c2d8f2; overflow-wrap:anywhere; }
.meter { height:3px; background:#12233a; margin:15px 0 10px; }
.meter-fill { height:100%; background:var(--blue); width:0; transition:width .2s; box-shadow:0 0 9px #518ee866; }
.hex-preview { color:#6d8fb8; font-size:10px; line-height:1.7; overflow-wrap:anywhere; white-space:pre-wrap; min-height:34px; }
.ledger-panel { grid-column:1/-1; background:#04080e; }
.ledger-tools { display:flex; align-items:center; gap:14px; }
.ledger { overflow:auto; padding:12px 16px; font-size:11px; line-height:1.85; flex:1; min-height:0; }
.log-line { display:grid; grid-template-columns:74px 85px 1fr; gap:12px; }
.log-time { color:#607897; }
.log-kind { color:#7daef0; }
.log-message { color:#a7bdd8; white-space:pre-wrap; overflow-wrap:anywhere; }
.log-line.error .log-message { color:#e9a58c; }
.network-panel { grid-column:1/-1; }
.network-body { padding:20px; }
.network-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }
.provider { border:1px solid #23374f; background:#050b14; padding:16px; border-radius:4px; min-width:0; }
.provider-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:18px; }
.provider-head label { color:#c7defb; font-size:13px; }
.provider-head input { accent-color:#6cb5ff; margin-right:8px; }
.provider-settings { border:0; display:flex; flex-direction:column; gap:10px; min-width:0; }
.provider-settings label { font-size:10px; }
.provider-settings input[type=text],.provider-settings input[type=password],.provider-settings input[type=url] { background:#02060b; border:1px solid #304661; color:#e8f2ff; padding:13px; border-radius:4px; width:100%; min-height:46px; font-size:14px; }
.provider-status { font-size:10px; color:#92aac7; }
.provider-status.active { color:var(--cyan); }
.provider-status.error { color:#efad92; }
.provider-meta { font-size:10px; color:#718eae; margin:14px 0 8px; min-height:15px; }
.provider-output { white-space:pre-wrap; overflow-wrap:anywhere; color:#b8cfe9; line-height:1.7; font:12px/1.7 Consolas,monospace; border-top:1px solid #1a2c43; padding-top:10px; min-height:100px; max-height:300px; overflow:auto; user-select:text; }
.network-actions { display:flex; align-items:center; flex-wrap:wrap; gap:12px; margin-top:18px; }
.network-actions .inject-btn { width:auto; min-width:240px; }
.network-actions input[type=number] { width:120px; min-height:46px; font-size:16px; padding:10px; }
.network-feedback { margin-top:12px; }
.network-note { margin-bottom:16px; }
@media(min-height:930px) { .master-container { grid-template-rows:auto minmax(710px,1fr) auto 192px; } textarea { min-height:186px; height:186px; } }
@media(max-width:920px) { .master-container { grid-template-columns:minmax(0,1fr); padding:12px; grid-template-rows:auto 590px auto auto 192px; } .masthead { align-items:flex-start; } .panel-header { padding:12px; } h1 { font-size:16px; } .version { display:none; } .workspace-panel { padding:18px; overflow:visible; } .network-grid { grid-template-columns:minmax(0,1fr); } }
@media(prefers-reduced-motion:reduce) { * { transition:none !important; } }
</style>
</head>
<body>
<main class="master-container">
  <header class="masthead">
    <div><div class="eyebrow">HARDWARE ACTIVITY / INTENT WORKSPACE</div><h1>Microcosmic Charge Injector<span class="version">CORE / 02</span></h1></div>
    <div id="connectionStatus" class="badge" role="status"><span class="dot"></span><span id="connectionText">CONNECTING</span></div>
  </header>
  <section class="panel" aria-labelledby="matrixTitle">
    <div class="panel-header"><h2 id="matrixTitle"><span class="index">01 //</span>Active flux matrix</h2><span class="tag">CPU TELEMETRY · 500 MS</span></div>
    <div class="telemetry-strip">
      <div><span class="metric-label">System CPU</span><span class="metric-value primary" id="cpuValue">—</span></div>
      <div><span class="metric-label">System RAM</span><span class="metric-value" id="ramValue">—</span></div>
      <div><span class="metric-label">Logical CPUs</span><span class="metric-value" id="coreValue">—</span></div>
    </div>
    <div class="canvas-wrapper"><canvas id="fluxCanvas" role="img" aria-label="Live CPU matrix. Column activity follows measured CPU utilization; the orbit and history show total CPU usage."></canvas></div>
    <div class="matrix-caption"><span id="matrixSource">Waiting for the local CPU sampler.</span><button class="quiet-button" id="motionButton" type="button" aria-pressed="false">Pause motion</button></div>
  </section>
  <section class="panel" aria-labelledby="bufferTitle">
    <div class="panel-header"><h2 id="bufferTitle"><span class="index">02 //</span>Intent injection buffer</h2><span class="tag" id="engineState">STANDBY</span></div>
    <form id="injectionForm" class="workspace-panel" novalidate>
      <div class="input-group">
        <div class="label-row"><label for="intentInput">Target identity / intent string</label><span class="counter" id="byteCounter">0 / 1,024 B</span></div>
        <textarea id="intentInput" spellcheck="false" aria-describedby="intentHint byteCounter">INTELLIGENCE_MUTATION_ALIGNMENT_INVARIANT</textarea>
        <p class="hint" id="intentHint">Multiline input · up to 1,024 UTF-8 bytes · preserves your full text</p>
      </div>
      <div class="input-group">
        <label for="orderInput">Elevation order / multiplier</label>
        <input type="number" id="orderInput" value="10" step="any" min="-1000000" max="1000000" required aria-describedby="orderHint">
        <p class="hint" id="orderHint">Yield = order × 7.83 · byte transform uses the whole-number part</p>
      </div>
      <div>
        <button class="inject-btn" id="injectButton" type="submit" disabled>Fire heightened charge vector ↗</button>
        <div class="action-row" style="margin-top:10px"><p class="feedback" id="feedback" role="status" style="flex:1">Connecting to the local engine…</p><span class="shortcut">CTRL + ENTER</span></div>
      </div>
      <div class="buffer-card">
        <div class="buffer-top"><span class="metric-label">Local buffer / live state</span><button type="button" class="quiet-button" id="resetButton" disabled>Reset buffer</button></div>
        <div class="buffer-stats">
          <div><span class="metric-label">Written</span><span class="buffer-value" id="bytesValue">0 B</span></div>
          <div><span class="metric-label">Yield</span><span class="buffer-value" id="yieldValue">0.00</span></div>
          <div><span class="metric-label">Dispatches</span><span class="buffer-value" id="dispatchValue">0</span></div>
        </div>
        <div class="meter"><div class="meter-fill" id="bufferMeter"></div></div>
        <div class="hex-preview" id="hexPreview">BUFFER EMPTY // AWAITING DISPATCH</div>
        <p class="hint" style="margin-top:8px">Writes to this app's memory buffer. The matrix independently monitors actual system CPU activity.</p>
      </div>
    </form>
  </section>
  <section class="panel network-panel" aria-labelledby="networkTitle">
    <div class="panel-header"><h2 id="networkTitle"><span class="index">03 //</span>Llama + Gemini + ChatGPT / inference network</h2><span class="tag" id="networkFlag">ACTIVE = FALSE</span></div>
    <div class="network-body">
      <p class="hint network-note">Run sends the current intent above to each selected provider. Each reply appears below. Active reflects successful replies from all three in the last run; cloud API usage is billed by the provider.</p>
      <div class="network-grid">
        <article class="provider">
          <div class="provider-head"><label><input type="checkbox" id="llamaEnabled" checked>Llama / local</label><span class="provider-status" id="llamaStatus">NOT TESTED</span></div>
          <fieldset class="provider-settings" id="llamaSettings">
            <label for="llamaModel">Ollama model</label><input id="llamaModel" type="text" value="llama3.2" spellcheck="false">
            <label for="llamaEndpoint">Local Ollama address</label><input id="llamaEndpoint" type="url" value="http://127.0.0.1:11434" spellcheck="false">
            <p class="hint">Use a Llama model already installed in Ollama.</p>
          </fieldset>
          <div class="provider-meta" id="llamaMeta">Awaiting first request</div><pre class="provider-output" id="llamaOutput">Your Llama reply will appear here.</pre>
        </article>
        <article class="provider">
          <div class="provider-head"><label><input type="checkbox" id="geminiEnabled" checked>Google Gemini</label><span class="provider-status" id="geminiStatus">NEEDS KEY</span></div>
          <fieldset class="provider-settings" id="geminiSettings">
            <label for="geminiModel">Gemini model</label><input id="geminiModel" type="text" value="gemini-3.8-flash" spellcheck="false">
            <label for="geminiKey">Gemini API key</label><input id="geminiKey" type="password" autocomplete="off" spellcheck="false" placeholder="Enter locally / session only">
            <p class="hint" id="geminiKeyHint">Or set GEMINI_API_KEY before launch.</p>
          </fieldset>
          <div class="provider-meta" id="geminiMeta">Awaiting first request</div><pre class="provider-output" id="geminiOutput">Your Gemini reply will appear here.</pre>
        </article>
        <article class="provider">
          <div class="provider-head"><label><input type="checkbox" id="openaiEnabled" checked>ChatGPT / OpenAI</label><span class="provider-status" id="openaiStatus">NEEDS KEY</span></div>
          <fieldset class="provider-settings" id="openaiSettings">
            <label for="openaiModel">OpenAI API model</label><input id="openaiModel" type="text" value="gpt-6-astra" spellcheck="false">
            <label for="openaiKey">OpenAI API key</label><input id="openaiKey" type="password" autocomplete="off" spellcheck="false" placeholder="Enter locally / session only">
            <p class="hint" id="openaiKeyHint">Or set OPENAI_API_KEY before launch.</p>
          </fieldset>
          <div class="provider-meta" id="openaiMeta">Awaiting first request</div><pre class="provider-output" id="openaiOutput">Your OpenAI reply will appear here.</pre>
        </article>
      </div>
      <div class="network-actions">
        <button class="inject-btn" id="runNetworkButton" type="button" disabled>Run current intent ↗</button>
        <label for="networkTokens">Output token limit</label><input id="networkTokens" type="number" min="128" max="8192" step="1" value="4096">
        <button class="quiet-button" id="forgetKeysButton" type="button" disabled>Forget cloud keys</button>
      </div>
      <p class="feedback network-feedback" id="networkFeedback" role="status">Configure the providers, then run your current intent. Keys stay in memory for this session.</p>
    </div>
  </section>
  <section class="panel ledger-panel" aria-labelledby="ledgerTitle">
    <div class="panel-header"><h2 id="ledgerTitle"><span class="index">04 //</span>Machine activity ledger</h2><div class="ledger-tools"><span class="tag">SESSION / LAST 120 EVENTS</span><button class="quiet-button" id="clearLogButton" type="button">Clear log</button></div></div>
    <div class="ledger" id="assemblyTerminal" role="log" aria-live="polite" aria-relevant="additions"></div>
  </section>
</main>
<script>
'use strict';
const $ = id => document.getElementById(id);
const canvas = $('fluxCanvas'), ctx = canvas.getContext('2d');
const terminal = $('assemblyTerminal'), intentIn = $('intentInput'), orderIn = $('orderInput');
const encoder = new TextEncoder();
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let paused = reducedMotion.matches, bridgeReady = false, busy = false;
let latest = null, lastReceived = 0, lastEvent = 0, lastRevision = -1;
let history = [], smoothedCPU = 0, smoothedCores = [], phase = 0, writeFlash = 0;
let viewWidth = 0, viewHeight = 0, lastFrame = 0, staleState = '';
const providerIds = ['llama','gemini','openai'];
let networkVersion = -1, networkBusy = false, networkHydrated = false;
let networkRequestPending = false, networkRunning = false;

function networkFeedback(message,error=false) { $('networkFeedback').textContent=message; $('networkFeedback').classList.toggle('error',error); }
function lockNetwork(locked) {
  networkBusy=locked || networkRequestPending;
  $('runNetworkButton').disabled=!bridgeReady || networkBusy;
  $('forgetKeysButton').disabled=!bridgeReady || networkBusy;
  $('networkTokens').disabled=networkBusy;
  for(const id of providerIds) {$(id+'Settings').disabled=networkBusy;$(id+'Enabled').disabled=networkBusy;}
}
function applyNetwork(data) {
  if(!data || data.version <= networkVersion) return;
  networkVersion=data.version;
  if(!networkHydrated) {
    for(const id of providerIds) {$(id+'Model').value=data.providers[id].model;$(id+'Enabled').checked=data.providers[id].enabled;}
    $('llamaEndpoint').value=data.providers.llama.endpoint;networkHydrated=true;
  }
  $('networkFlag').textContent=(data.running?'RUNNING / ':'LAST RUN / ')+'ACTIVE = '+(data.active?'TRUE':'FALSE');
  networkRunning=data.running;lockNetwork(networkRunning);
  for(const id of providerIds) {
    const provider=data.providers[id],status=$(id+'Status');
    status.textContent=provider.status.replaceAll('_',' ').toUpperCase();status.className='provider-status '+provider.status;
    if(provider.output || provider.error) $(id+'Output').textContent=provider.output || provider.error;
    else $(id+'Output').textContent=provider.status==='running'?'Waiting for the provider reply…':'Awaiting a request.';
    $(id+'Meta').textContent=provider.latency_ms!==null?`${(provider.latency_ms/1000).toFixed(2)} s · ${provider.model}`:`${provider.model} · ${provider.status.replaceAll('_',' ')}`;
    if(id!=='llama') $(id+'KeyHint').textContent=provider.key_configured?'Key configured for this session. Leave blank to keep it.':`Enter an API key, or set ${id==='openai'?'OPENAI_API_KEY':'GEMINI_API_KEY'} before launch.`;
  }
  if(!data.running && data.run_id>0) {
    const succeeded=providerIds.filter(id=>data.providers[id].status==='active').length;
    networkFeedback(`${succeeded} of ${data.selected_count} selected providers returned complete replies.`,succeeded<data.selected_count);
  }
}
$('runNetworkButton').addEventListener('click',async()=>{
  if(!bridgeReady || networkBusy) return;
  if(!intentIn.value.trim()) {networkFeedback('Enter an intent above before running inference.',true);intentIn.focus();return;}
  const tokens=Number($('networkTokens').value);
  if(!Number.isInteger(tokens)||tokens<128||tokens>8192) {networkFeedback('Choose an output limit from 128 to 8,192 tokens.',true);return;}
  const settings={};
  for(const id of providerIds) settings[id]={enabled:$(id+'Enabled').checked,model:$(id+'Model').value,api_key:id==='llama'?'':$(id+'Key').value};
  settings.llama.endpoint=$('llamaEndpoint').value;
  networkRequestPending=true;lockNetwork(true);networkFeedback('Dispatching the current intent to the selected providers…');
  try {
    const result=await window.pywebview.api.run_inference_network(intentIn.value,settings,tokens);
    applyNetwork(result.network);
    networkFeedback(result.message,!result.ok);
    if(result.ok) { $('geminiKey').value='';$('openaiKey').value=''; }
  } catch(error) {networkFeedback('The local engine could not start the inference request.',true);}
  finally {networkRequestPending=false;lockNetwork(networkRunning);}
});
$('forgetKeysButton').addEventListener('click',async()=>{
  if(!bridgeReady || networkBusy) return;networkRequestPending=true;lockNetwork(true);
  try {const result=await window.pywebview.api.forget_inference_keys();applyNetwork(result.network);$('geminiKey').value='';$('openaiKey').value='';networkFeedback(result.message,!result.ok);}
  catch(error) {networkFeedback('The local engine did not confirm key removal.',true);}
  finally {networkRequestPending=false;lockNetwork(networkRunning);}
});

function appendLog(kind, message, timestamp, error=false) {
  const atBottom = terminal.scrollHeight - terminal.scrollTop - terminal.clientHeight < 28;
  const row = document.createElement('div'); row.className = 'log-line' + (error ? ' error' : '');
  const clock = document.createElement('span'); clock.className = 'log-time';
  clock.textContent = new Date(timestamp || Date.now()).toLocaleTimeString('en-GB', {hour12:false});
  const label = document.createElement('span'); label.className = 'log-kind'; label.textContent = kind;
  const text = document.createElement('span'); text.className = 'log-message'; text.textContent = message;
  row.append(clock,label,text); terminal.appendChild(row);
  while (terminal.children.length > 120) terminal.firstChild.remove();
  if (atBottom) terminal.scrollTop = terminal.scrollHeight;
}
function feedback(message, error=false) { $('feedback').textContent = message; $('feedback').classList.toggle('error',error); }
function countBytes() {
  const count = encoder.encode(intentIn.value).length;
  $('byteCounter').textContent = `${count.toLocaleString()} / 1,024 B`;
  $('byteCounter').classList.toggle('error',count > 1024);
  intentIn.setAttribute('aria-invalid',String(count > 1024)); return count;
}
intentIn.addEventListener('input',countBytes); countBytes();
orderIn.addEventListener('input',() => orderIn.setAttribute('aria-invalid','false'));
function setBusy(value) { busy = value; $('injectButton').disabled = !bridgeReady || busy; $('resetButton').disabled = !bridgeReady || busy; }
function applyState(state) {
  if (!state || state.revision < lastRevision) return;
  if (lastRevision >= 0 && state.revision > lastRevision && state.bytes_written > 0) writeFlash = 1;
  lastRevision = state.revision;
  applyNetwork(state.network);
  $('engineState').textContent = state.engine_state;
  $('bytesValue').textContent = `${state.bytes_written.toLocaleString()} B`;
  $('yieldValue').textContent = Number(state.calculated_yield).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});
  $('dispatchValue').textContent = state.dispatch_count;
  $('bufferMeter').style.width = `${state.bytes_written / 1024 * 100}%`;
  $('hexPreview').textContent = state.bytes_written ? `HEX / ${state.hex_preview}\nBUFFER / ${state.memory_address}` : 'BUFFER EMPTY // AWAITING DISPATCH';
  for (const event of state.events || []) {
    if (event.id <= lastEvent) continue;
    appendLog(event.kind,event.message,event.timestamp,event.kind === 'BLOCKED'); lastEvent = event.id;
  }
}
function updateMachineLogStream(data) {
  if (typeof data === 'string') data = JSON.parse(data);
  latest = data; lastReceived = performance.now();
  const cpu = data.cpu;
  $('cpuValue').textContent = cpu.available ? `${cpu.total.toFixed(1)}%` : '—';
  $('ramValue').textContent = Number.isFinite(cpu.memory_percent) ? `${cpu.memory_percent.toFixed(1)}%` : '—';
  $('coreValue').textContent = cpu.logical_cpus || '—';
  $('matrixSource').textContent = cpu.available ? `${cpu.per_core.length ? 'Columns follow logical CPU load' : 'Columns follow total CPU load'} · ${cpu.source}` : (cpu.error || 'CPU telemetry unavailable');
  const now = performance.now();
  history.push({time:now,value:cpu.available ? cpu.total : null});
  history = history.filter(point => now - point.time <= 60000).slice(-121);
  applyState(data.state); updateConnection();
}
window.updateMachineLogStream = updateMachineLogStream;
function updateConnection() {
  const stale = lastReceived && performance.now() - lastReceived > 2500;
  const available = latest && latest.cpu.available;
  const next = !lastReceived ? 'CONNECTING' : stale ? 'SIGNAL LOST' : available ? 'LIVE / LOCAL' : 'CPU UNAVAILABLE';
  if (next === staleState) return;
  staleState = next; $('connectionText').textContent = next;
  $('connectionStatus').className = 'badge ' + (next === 'LIVE / LOCAL' ? 'live' : 'stale');
  if (stale || (latest && !available)) { $('cpuValue').textContent = '—'; $('ramValue').textContent = '—'; }
  if (stale) appendLog('TELEMETRY','CPU signal lost; awaiting fresh measurements.');
}
function onBridgeReady() {
  if (bridgeReady || !window.pywebview || !window.pywebview.api) return;
  bridgeReady = true; setBusy(false); feedback('Ready for local buffer dispatch.');
  lockNetwork(networkBusy);
}
window.addEventListener('pywebviewready',onBridgeReady); onBridgeReady();
setTimeout(() => { if (!bridgeReady) feedback('Waiting for the desktop engine. Open this interface through the Python app.'); },5000);
async function executeHeightenedChargeInjection() {
  if (!bridgeReady || busy) return;
  const byteCount = countBytes(), factor = Number(orderIn.value);
  if (!intentIn.value.trim() || byteCount > 1024) {
    intentIn.setAttribute('aria-invalid','true'); intentIn.focus();
    feedback(byteCount > 1024 ? 'Intent exceeds 1,024 UTF-8 bytes. Shorten the text to continue.' : 'Enter an intent before dispatching.',true); return;
  }
  if (!orderIn.value.trim() || !Number.isFinite(factor) || Math.abs(factor) > 1000000) {
    orderIn.setAttribute('aria-invalid','true'); orderIn.focus(); feedback('Enter a finite multiplier between −1,000,000 and 1,000,000.',true); return;
  }
  setBusy(true); feedback('Writing local buffer…');
  try {
    const result = await window.pywebview.api.inject_heightened_charge_substrate(intentIn.value,orderIn.value);
    applyState(result.state); feedback(result.message,!result.ok);
  } catch (error) { feedback('Dispatch failed. The local engine is unavailable.',true); appendLog('BRIDGE','Dispatch could not reach the local engine.',null,true); }
  finally { setBusy(false); }
}
$('injectionForm').addEventListener('submit',event => {event.preventDefault(); executeHeightenedChargeInjection();});
document.addEventListener('keydown',event => { if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') { event.preventDefault(); executeHeightenedChargeInjection(); } });
$('resetButton').addEventListener('click',async () => {
  if (busy || !bridgeReady) return; setBusy(true);
  try { const result = await window.pywebview.api.reset_buffer(); applyState(result.state); feedback(result.message); }
  catch (error) { feedback('Reset failed. The local engine is unavailable.',true); }
  finally { setBusy(false); }
});
$('clearLogButton').addEventListener('click',() => {terminal.replaceChildren(); appendLog('LEDGER','Visible log cleared. New events will appear here.');});
function syncMotionButton() { $('motionButton').textContent = paused ? 'Resume motion' : 'Pause motion'; $('motionButton').setAttribute('aria-pressed',String(paused)); }
$('motionButton').addEventListener('click',() => {paused = !paused; syncMotionButton();}); syncMotionButton();
function resize() {
  const bounds = canvas.parentElement.getBoundingClientRect();
  viewWidth = bounds.width; viewHeight = bounds.height;
  const dpr = Math.min(window.devicePixelRatio || 1,2);
  canvas.width = Math.round(viewWidth*dpr); canvas.height = Math.round(viewHeight*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
new ResizeObserver(resize).observe(canvas.parentElement); window.addEventListener('resize',resize);
function text(value,x,y,color='#6d88aa',size=10,align='left') { ctx.fillStyle=color; ctx.font=`${size}px Consolas, monospace`; ctx.textAlign=align; ctx.fillText(value,x,y); }
function line(x1,y1,x2,y2,color,width=1) {ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}
function renderSystemMatrix(now) {
  requestAnimationFrame(renderSystemMatrix);
  if (document.hidden || now-lastFrame < (paused ? 180 : 32)) return;
  const dt = Math.min((now-lastFrame)/1000,.2); lastFrame=now; updateConnection();
  const w=viewWidth,h=viewHeight; if (!w || !h) return;
  const live=latest && latest.cpu.available && now-lastReceived <= 2500;
  const target=live ? latest.cpu.total/100 : 0;
  const blend=paused ? 1 : 1-Math.exp(-dt*7);
  smoothedCPU += (target-smoothedCPU)*blend;
  const measured = live ? (latest.cpu.per_core.length ? latest.cpu.per_core : [latest.cpu.total]) : [0];
  const cols=Math.max(1,Math.min(measured.length===1 ? 16 : measured.length,Math.floor((w-34)/18),32));
  const groups=Array.from({length:cols},(_,c) => {
    if (measured.length===1) return measured[0]/100;
    const start=Math.floor(c*measured.length/cols),end=Math.floor((c+1)*measured.length/cols);
    return measured.slice(start,end).reduce((a,b)=>a+b,0)/(end-start)/100;
  });
  smoothedCores=groups.map((load,i) => (smoothedCores[i] || 0)+(load-(smoothedCores[i] || 0))*blend);
  if (!paused && live) phase += dt*(.08+smoothedCPU*2.8);
  writeFlash=Math.max(0,writeFlash-dt*1.5);
  ctx.clearRect(0,0,w,h);
  const glow=ctx.createRadialGradient(w/2,h*.54,0,w/2,h*.54,w*.65);
  glow.addColorStop(0,`rgba(25,74,130,${.08+smoothedCPU*.18})`);glow.addColorStop(1,'rgba(4,8,14,0)');ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);
  for(let x=10;x<w;x+=24) line(x,0,x,h,'#17294133');
  for(let y=8;y<h;y+=24) line(0,y,w,y,'#17294133');
  text(live ? (measured.length>cols ? 'LOGICAL CPU GROUPS / AVERAGE LOAD' : measured.length===1 ? 'SYSTEM LOAD / ACTIVITY MATRIX' : 'LOGICAL CPU / ACTIVITY MATRIX') : 'CPU MATRIX / WAITING FOR SIGNAL',12,15);
  const gridTop=37,gridHeight=Math.min(132,h*.29),rows=9,step=(w-30)/cols;
  for(let c=0;c<cols;c++) {
    const activity=smoothedCores[c],x=16+(c+.5)*step;
    for(let r=0;r<rows;r++) {
      const threshold=(rows-r-.5)/rows,lit=live && activity>=threshold;
      const bit=lit ? ((c*7+r*3+Math.floor(phase*(1+activity*4)))%2 ? '1':'0') : '0';
      text(bit,x,gridTop+r*(gridHeight/rows),lit ? `rgba(167,211,255,${.5+activity*.5})` : '#244263',Math.min(12,step*.62),'center');
    }
    ctx.fillStyle=live?'#4d9cf0':'#254361';ctx.fillRect(x-step*.27,gridTop+gridHeight+2,step*.54,2+activity*5);
    if (cols<=20 || c%2===0) text(measured.length===1 ? '' : String(c+1).padStart(2,'0'),x,gridTop+gridHeight+22,'#6882a2',8,'center');
  }
  const historyTop=h-67, orbitTop=gridTop+gridHeight+37;
  const cy=(orbitTop+historyTop)/2, cx=w/2, radius=Math.max(30,Math.min(64,(historyTop-orbitTop)/2-13,w*.16));
  ctx.beginPath();ctx.arc(cx,cy,radius+13,0,Math.PI*2);ctx.strokeStyle='#203b5c';ctx.lineWidth=1;ctx.stroke();
  for(let i=0;i<48;i++) {
    const a=i/48*Math.PI*2-Math.PI/2;
    line(cx+Math.cos(a)*(radius+18),cy+Math.sin(a)*(radius+18),cx+Math.cos(a)*(radius+22),cy+Math.sin(a)*(radius+22),live && i/48<smoothedCPU?'#8dccff':'#1a304c',1.5);
  }
  ctx.beginPath();ctx.arc(cx,cy,radius,-Math.PI/2,Math.PI*2-Math.PI/2);ctx.strokeStyle='#1c3c62';ctx.lineWidth=2;ctx.stroke();
  if(live && smoothedCPU>0) {ctx.beginPath();ctx.arc(cx,cy,radius,-Math.PI/2,smoothedCPU*Math.PI*2-Math.PI/2);ctx.strokeStyle='#6eb9ff';ctx.shadowColor='#4b9ef4';ctx.shadowBlur=10;ctx.lineWidth=2.5;ctx.stroke();ctx.shadowBlur=0;}
  for(let i=0;i<4;i++) {
    const a=i/4*Math.PI*2+phase,x=cx+Math.cos(a)*radius,y=cy+Math.sin(a)*radius;
    ctx.beginPath();ctx.arc(x,y,2+smoothedCPU*2.5,0,Math.PI*2);ctx.fillStyle=live?(i%2?'#66aaf7':'#d7ecff'):'#34516f';ctx.fill();
  }
  if(writeFlash>0 && !paused) {ctx.beginPath();ctx.arc(cx,cy,radius+24+(1-writeFlash)*13,0,Math.PI*2);ctx.strokeStyle=`rgba(114,222,235,${writeFlash*.65})`;ctx.lineWidth=1;ctx.stroke();}
  text(live ? `${latest.cpu.total.toFixed(1)}%` : '—',cx,cy+3,'#d6eaff',Math.max(18,radius*.37),'center');
  text('CPU LOAD',cx,cy+19,'#7698c0',8,'center');
  if(w>460) {
    text('MICROCOSMIC',22,cy-9,'#6582a5',9);text('ORBIT / 01',22,cy+7,'#96b7de',10);
    text('FLUX RESPONSE',w-22,cy-9,'#6582a5',9,'right');text(paused?'MOTION PAUSED':live?'LIVE CPU':'NO SIGNAL',w-22,cy+7,'#96b7de',10,'right');
  }
  line(12,historyTop-7,w-12,historyTop-7,'#1b304a');
  text('CPU HISTORY / 60 SEC',12,historyTop+8,'#6d88aa',9);
  text('100%',w-12,historyTop+8,'#587390',8,'right');
  const chartTop=historyTop+18,chartBottom=h-8,chartW=w-26;
  line(13,chartBottom,w-13,chartBottom,'#1c3554');
  ctx.beginPath(); let connected=false,lastTime=0;
  for(const point of history) {
    if(now-point.time>60000) continue;
    if(point.value===null) {connected=false;continue;}
    const x=13+chartW*(1-(now-point.time)/60000),y=chartBottom-point.value/100*(chartBottom-chartTop);
    if(connected && point.time-lastTime<1600) ctx.lineTo(x,y); else ctx.moveTo(x,y);
    connected=true;lastTime=point.time;
  }
  ctx.strokeStyle='#5ea9ff';ctx.lineWidth=1.5;ctx.stroke();
}
appendLog('SYSTEM','Initializing local memory buffer and live CPU telemetry.');
resize();requestAnimationFrame(renderSystemMatrix);
</script>
</body>
</html>"""


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
        idle, kernel, user = self.filetime(), self.filetime(), self.filetime()
        if not self.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            raise ctypes.WinError(ctypes.get_last_error())
        return tuple((v.dwHighDateTime << 32) | v.dwLowDateTime for v in (idle, kernel, user))

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
        result = {'available': False, 'total': None, 'per_core': [],
                  'logical_cpus': self.logical_cpus, 'memory_percent': None,
                  'source': 'psutil' if self.use_psutil else 'Windows CPU counters'}
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
            if not all(math.isfinite(value) and 0 <= value <= 100 for value in values):
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
        self._config = {
            'llama': {'enabled': True, 'model': os.getenv('OLLAMA_MODEL', 'llama3.2'),
                      'endpoint': os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434'), 'api_key': ''},
            'gemini': {'enabled': True, 'model': os.getenv('GEMINI_MODEL', 'gemini-3.8-flash'),
                       'api_key': os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY', '')},
            'openai': {'enabled': True, 'model': os.getenv('OPENAI_MODEL', 'gpt-6-astra'),
                       'api_key': os.getenv('OPENAI_API_KEY', '')},
        }
        self._results = {name: self._empty_result(name) for name in self._config}

    def _empty_result(self, name):
        config = self._config[name]
        return {'status': 'not_tested' if name == 'llama' or config['api_key'] else 'needs_key',
                'output': '', 'error': '', 'latency_ms': None}

    def _snapshot(self):
        with self._lock:
            providers = {}
            for name, config in self._config.items():
                providers[name] = {key: value for key, value in config.items() if key != 'api_key'}
                providers[name].update(self._results[name])
                providers[name]['key_configured'] = bool(config['api_key'])
            return {'version': self._version, 'run_id': self._run_id,
                    'running': self._remaining > 0, 'selected_count': self._selected_count,
                    'active': self._run_id > 0 and self._remaining == 0 and
                              all(p['enabled'] and p['status'] == 'active' for p in providers.values()),
                    'providers': providers}

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
        if (parsed.scheme not in ('http', 'https') or
                parsed.hostname not in ('localhost', '127.0.0.1', '::1') or
                parsed.username or parsed.password or parsed.query or parsed.fragment or
                parsed.path not in ('', '/')):
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
                    if raw.get('enabled', True) and (not model or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,200}', model)):
                        raise ValueError(f'Enter a valid model name for {name}.')
                    key = raw.get('api_key', '')
                    if not isinstance(key, str) or len(key) > 4096 or any(ord(char) < 32 for char in key):
                        raise ValueError('API keys must be single-line text.')
                    staged[name] = {'enabled': raw.get('enabled', True), 'model': model,
                                    'api_key': key.strip() or previous['api_key']}
                    if name == 'llama':
                        endpoint = raw.get('endpoint', previous['endpoint'])
                        staged[name]['endpoint'] = self._local_endpoint(endpoint) if staged[name]['enabled'] else previous['endpoint']
                if not any(p['enabled'] for p in staged.values()):
                    raise ValueError('Select at least one inference provider.')
            except UnicodeError:
                return self._reply(False, 'The prompt contains an invalid Unicode sequence.')
            except (TypeError, ValueError) as exception:
                return self._reply(False, str(exception))
            self._config = staged
            self._run_id += 1
            self._version += 1
            run_id = self._run_id
            self._selected_count = sum(p['enabled'] for p in staged.values())
            ready = []
            for name, config in staged.items():
                self._results[name] = self._empty_result(name)
                if not config['enabled']:
                    self._results[name]['status'] = 'disabled'
                elif name != 'llama' and not config['api_key']:
                    self._results[name].update(status='needs_key', error='Add this provider\'s API key, then run again.')
                else:
                    self._results[name]['status'] = 'running'
                    ready.append((name, dict(config)))
            self._remaining = len(ready)
            for name, config in ready:
                worker = threading.Thread(target=self._run_provider,
                                          args=(run_id, name, config, prompt, max_tokens), daemon=True)
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
        request = urlrequest.Request(url, data=json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json', **headers}, method='POST')
        with opener.open(request, timeout=INFERENCE_TIMEOUT) as response:
            content = response.read(2_000_001)
        if len(content) > 2_000_000:
            raise ValueError('Response too large.')
        data = json.loads(content.decode('utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Expected an object response.')
        return data

    def _infer(self, name, config, prompt, max_tokens):
        model, key = config['model'], config['api_key']
        complete = True
        if name == 'llama':
            data = self._request_json(config['endpoint'] + '/api/chat',
                                      {'model': model, 'messages': [{'role': 'user', 'content': prompt}],
                                       'stream': False, 'options': {'num_predict': max_tokens}}, {}, local=True)
            text = data.get('message', {}).get('content', '')
            complete = data.get('done', False) and data.get('done_reason') != 'length'
        elif name == 'gemini':
            model_path = urlparse.quote(model.removeprefix('models/'), safe='')
            data = self._request_json(f'https://generativelanguage.googleapis.com/v1beta/models/{model_path}:generateContent',
                                      {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                                       'generationConfig': {'maxOutputTokens': max_tokens}}, {'x-goog-api-key': key})
            candidates = data.get('candidates') or []
            candidate = candidates[0] if candidates else {}
            text = '\n'.join(part['text'] for part in candidate.get('content', {}).get('parts', [])
                             if isinstance(part.get('text'), str) and not part.get('thought', False))
            complete = candidate.get('finishReason') == 'STOP'
        else:
            data = self._request_json('https://api.openai.com/v1/responses',
                                      {'model': model, 'input': prompt, 'max_output_tokens': max_tokens,
                                       'store': False}, {'Authorization': 'Bearer ' + key})
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
            return {'status': 'error', 'output': '',
                    'error': 'The provider returned no displayable text. Check the model, output limit, or provider restrictions.'}
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
            messages = {400: 'Request rejected. Check the model and output settings.',
                        401: 'API key rejected. Check the key for this provider.',
                        403: 'Access denied. Check the key and model permissions.',
                        404: 'Model or endpoint not found. For Llama, check the installed Ollama model.',
                        429: 'Provider quota or rate limit reached. Check usage and retry later.'}
            result = {'status': 'error', 'output': '',
                      'error': messages.get(error.code, f'Provider returned HTTP {error.code}. Please retry later.')}
            error.close()
        except (TimeoutError, urlerror.URLError, OSError):
            result = {'status': 'error', 'output': '',
                      'error': 'No response within the connection limit. Check Ollama or your network connection.'}
        except Exception:
            # Never put raw provider exceptions/HTTP bodies (which may echo keys)
            # into the HTML bridge or the activity log.
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
        self._events.append({'id': self._event_id, 'kind': kind,
                             'message': message, 'timestamp': int(time.time() * 1000)})

    def _snapshot(self):
        with self._lock:
            address = ctypes.addressof(ctypes.c_ubyte.from_buffer(self._buffer))
            return {'revision': self._revision, 'engine_state': self._engine_state,
                    'bytes_written': self._bytes_written, 'capacity': BUFFER_CAPACITY,
                    'calculated_yield': self._yield, 'dispatch_count': self._dispatch_count,
                    'memory_address': f'0x{address:X}',
                    'hex_preview': self._buffer[:min(self._bytes_written, 32)].hex(' ').upper(),
                    'events': list(self._events), 'network': self._network._snapshot()}

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
                mask = int(order) & 0xFF
                transformed = bytes(value ^ mask for value in encoded)
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
    while not ready_event.wait(0.1):
        if stop_event.is_set():
            return
    sampler = CPUSampler()
    while not stop_event.wait(TELEMETRY_INTERVAL):
        payload = {'cpu': sampler.sample(), 'state': api._snapshot()}
        # Pass a JSON object, avoiding nested quoting of user-controlled content.
        script = 'window.updateMachineLogStream(' + json.dumps(payload, ensure_ascii=True, allow_nan=False) + ');'
        try:
            window.evaluate_js(script)
        except Exception:
            if stop_event.is_set():
                break
            # A page reload may temporarily remove its JS handler. Retry next tick.


def main():
    try:
        import webview
    except ImportError:
        raise SystemExit("[ERROR] Missing pywebview. Install with: python -m pip install pywebview")
    api = MetaphysicalChargeInjectorAPI()
    stop_event, ready_event = threading.Event(), threading.Event()
    window = webview.create_window(
        'Microcosmic Charge Injector Core / Live CPU', html=HTML_LAYOUT,
        width=1440, height=960, min_size=(760, 680), background_color='#030508', js_api=api,
    )
    window.events.loaded += ready_event.set
    window.events.closed += stop_event.set
    try:
        webview.start(schumann_carrier_broadcast_loop, (window, api, stop_event, ready_event))
    finally:
        stop_event.set()
        api._network.close()


if __name__ == '__main__':
    main()
