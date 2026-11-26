import {makeCharge,birthParticles,particlePhase} from './intent_particles.js';
const HTML="<style>\n:host {\n  color-scheme: dark;\n  --bg: #070b12; --panel: rgba(14,22,34,.88); --line: rgba(136,173,204,.16);\n  --muted: #8193a7; --text: #e5f0f6; --cyan: #70e1dc; --blue: #72aaff;\n  --green: #82e6b4; --red: #ff898f;\n  font-family: Inter, \"Segoe UI\", system-ui, sans-serif;\n}\n* { box-sizing: border-box; }\nbody { margin: 0; min-width: 320px; min-height: 100vh; color: var(--text);\n  background: radial-gradient(ellipse at 18% 0%, #122638 0, transparent 38%),\n  radial-gradient(ellipse at 100% 80%, #101e32 0, transparent 34%), var(--bg); }\nbutton, input, textarea { font: inherit; }\n.app { min-height: 100vh; padding: 22px; display: flex; flex-direction: column; gap: 16px; }\n.topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; }\n.brand { display: flex; align-items: center; gap: 13px; min-width: 0; }\n.brand-mark { width: 40px; height: 40px; display: grid; place-items: center; flex: 0 0 auto;\n  border: 1px solid rgba(112,225,220,.42); border-radius: 13px; color: var(--cyan);\n  background: linear-gradient(145deg, rgba(112,225,220,.17), rgba(114,170,255,.06)); box-shadow: 0 0 24px rgba(112,225,220,.10); }\n.brand-mark svg { width: 23px; height: 23px; }\n.eyebrow { color: var(--cyan); text-transform: uppercase; letter-spacing: .19em; font-size: 10px; font-weight: 700; }\nh1 { margin: 3px 0 0; font-size: clamp(18px, 2vw, 23px); letter-spacing: -.025em; font-weight: 650; }\n.link-badge { display: inline-flex; align-items: center; gap: 9px; border: 1px solid var(--line); border-radius: 999px;\n  padding: 9px 13px; color: #b7c8d7; background: rgba(10,17,27,.75); font-size: 11px; white-space: nowrap; }\n.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 12px currentColor; }\n.link-badge[data-state=\"ok\"] .dot { background: var(--green); }\n.link-badge[data-state=\"error\"] .dot { background: var(--red); }\n.layout { flex: 1; min-height: 620px; display: grid; grid-template-columns: minmax(0,1.32fr) minmax(360px,.88fr);\n  grid-template-rows: minmax(340px,1fr) 178px; gap: 16px; }\n.panel { min-width: 0; border: 1px solid var(--line); border-radius: 16px; overflow: hidden;\n  background: linear-gradient(145deg, rgba(16,26,40,.92), rgba(8,14,23,.94)); box-shadow: 0 18px 48px rgba(0,0,0,.19); }\n.field-panel { display: flex; flex-direction: column; position: relative; }\n.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 17px 19px 13px; border-bottom: 1px solid var(--line); }\n.panel-title { font-size: 12px; font-weight: 650; }\n.panel-subtitle { margin-top: 4px; color: var(--muted); font-size: 10px; }\n.chip { border: 1px solid rgba(112,225,220,.23); border-radius: 999px; padding: 6px 9px; color: var(--cyan); font-size: 9px; letter-spacing: .12em; text-transform: uppercase; white-space: nowrap; }\n.canvas-wrap { flex: 1; min-height: 245px; position: relative; }\n#fieldCanvas { width: 100%; height: 100%; display: block; }\n.field-caption { position: absolute; left: 20px; bottom: 15px; color: #7891a4; font-size: 10px; letter-spacing: .04em; }\n.field-legend { position: absolute; top: 16px; right: 18px; display: flex; gap: 13px; color: #8ba0b1; font-size: 9px; }\n.legend-item { display: flex; align-items: center; gap: 6px; }\n.legend-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--cyan); }\n.legend-dot.blue { background: var(--blue); }\n.instrument-row { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 9px; padding: 0 16px 16px; }\n.metric { min-width: 0; border: 1px solid rgba(136,173,204,.12); border-radius: 11px; padding: 11px 12px; background: rgba(5,11,19,.46); }\n.metric-label { display: flex; justify-content: space-between; gap: 5px; color: var(--muted); font-size: 9px; text-transform: uppercase; letter-spacing: .12em; }\n.metric-value { margin-top: 7px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18px; font-variant-numeric: tabular-nums; }\n.metric-detail { margin-top: 4px; min-height: 12px; color: #8296a7; font-size: 9px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.controls { display: flex; flex-direction: column; }\n.controls-body { padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 13px; }\n.field-group { display: flex; flex-direction: column; gap: 7px; }\n.label-row { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }\nlabel { color: #a8bac8; font-size: 10px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }\n.micro { color: #71869a; font-size: 9px; }\ninput[type=\"url\"], textarea { width: 100%; border: 1px solid rgba(136,173,204,.21); border-radius: 9px; outline: none;\n  color: #deebf2; background: rgba(3,8,14,.62); padding: 10px 11px; font-size: 11px; transition: border-color .16s, box-shadow .16s; }\ntextarea { min-height: 83px; resize: vertical; line-height: 1.5; }\ninput[type=\"url\"]:focus, textarea:focus { border-color: rgba(112,225,220,.63); box-shadow: 0 0 0 3px rgba(112,225,220,.08); }\ninput::placeholder, textarea::placeholder { color: #536779; }\n.tuner { display: flex; align-items: center; gap: 11px; }\ninput[type=\"range\"] { flex: 1; accent-color: var(--cyan); }\n.tuner-value { width: 42px; color: var(--cyan); text-align: right; font-size: 12px; font-variant-numeric: tabular-nums; }\n.actions { display: grid; grid-template-columns: 1fr 1.35fr; gap: 9px; margin-top: 2px; }\nbutton { min-height: 38px; border-radius: 9px; cursor: pointer; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; transition: transform .15s, background .15s, border-color .15s; }\nbutton:hover { transform: translateY(-1px); }\nbutton:disabled { opacity: .55; cursor: wait; transform: none; }\n.secondary { border: 1px solid rgba(136,173,204,.22); background: rgba(18,30,43,.8); color: #bad0dd; }\n.primary { border: 1px solid rgba(112,225,220,.48); background: linear-gradient(110deg, rgba(49,154,155,.34), rgba(69,115,175,.28)); color: #b5ffef; box-shadow: inset 0 1px rgba(255,255,255,.07); }\n.primary:hover { background: linear-gradient(110deg, rgba(49,154,155,.5), rgba(69,115,175,.4)); }\n.disclosure { color: #71879a; font-size: 9px; line-height: 1.5; }\n.status-line { min-height: 28px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--line); padding: 9px 16px; color: #8ca0b1; font-size: 10px; }\n.status-line[data-kind=\"ok\"] { color: var(--green); }\n.status-line[data-kind=\"error\"] { color: var(--red); }\n.activity { grid-column: 1 / -1; display: flex; flex-direction: column; }\n.activity-body { flex: 1; overflow: auto; padding: 10px 16px 13px; }\n.event-list { display: flex; flex-direction: column; gap: 7px; }\n.event { display: grid; grid-template-columns: 72px 69px minmax(0,1fr); gap: 9px; align-items: baseline; color: #9aafbd; font-size: 10px; line-height: 1.45; }\n.event-time { color: #627a8e; font-variant-numeric: tabular-nums; }\n.event-tag { color: var(--cyan); text-transform: uppercase; letter-spacing: .08em; font-size: 9px; }\n.event-tag.error { color: var(--red); }\n.event-message { overflow-wrap: anywhere; }\n.footer { display: flex; justify-content: space-between; gap: 12px; color: #677d90; font-size: 9px; }\n@media (max-width: 900px) { .app { padding: 14px; } .layout { grid-template-columns: minmax(0,1fr); grid-template-rows: 390px auto 170px; min-height: 0; } .activity { grid-column: 1; } .controls { min-height: 410px; } }\n@media (max-width: 540px) { .topbar { align-items: flex-start; } .link-badge { padding: 8px; font-size: 9px; } .layout { grid-template-rows: 375px auto 160px; } .instrument-row { grid-template-columns: repeat(2,minmax(0,1fr)); } .controls { min-height: 440px; } .footer { flex-direction: column; } .event { grid-template-columns: 54px 57px minmax(0,1fr); } }\n\n/* Additive overlays: all original panels, text, spacing and field drawing stay intact. */\n.metric { position: relative; }\n.reactive-trail { position: absolute; left: 10px; right: 10px; bottom: 0; height: 2px;\n  overflow: hidden; border-radius: 2px; pointer-events: none; background: rgba(112,225,220,.035); }\n.reactive-trail-fill { width: 100%; height: 100%; transform: scaleX(0); transform-origin: left;\n  background: var(--cyan); opacity: .5; box-shadow: 0 0 9px currentColor; }\n.reactive-trail[data-signal=\"rx_rate\"] .reactive-trail-fill,\n.reactive-trail[data-signal=\"tx_rate\"] .reactive-trail-fill { background: var(--blue); }\n#reactiveCanvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }\n.audio-readout { position: absolute; top: 16px; left: 20px; width: clamp(134px,32%,190px);\n  color: #8ba0b1; pointer-events: auto; }\n.audio-readout-head { display: flex; align-items: baseline; justify-content: space-between;\n  gap: 8px; font-size: 9px; letter-spacing: .04em; }\n.audio-readout-label { color: var(--cyan); }\n.audio-readout-value { font-size: 8px; font-variant-numeric: tabular-nums; white-space: nowrap; }\n.audio-history { display: block; width: 100%; height: 30px; margin-top: 5px; overflow: hidden; }\n.audio-history-baseline { stroke: rgba(112,225,220,.12); stroke-width: 1; }\n.audio-history-fill { fill: rgba(112,225,220,.055); }\n.audio-history-line { fill: none; stroke: rgba(112,225,220,.65); stroke-width: 1;\n  stroke-linejoin: round; stroke-linecap: round; }\n.audio-readout[data-state=\"unavailable\"] .audio-readout-label { color: var(--muted); }\n\n:host{display:block;min-width:0}.app{min-height:0;padding:16px}.layout{min-height:620px}@media(max-width:950px){.layout{display:flex;flex-direction:column}.canvas-wrap{min-height:380px}}</style>\n<div class=\"app\">\n  <header class=\"topbar\">\n    <div class=\"brand\"><div class=\"brand-mark\" aria-hidden=\"true\"><svg viewBox=\"0 0 24 24\" fill=\"none\"><path d=\"M3 12h3l2.1-6 4.1 12 2.2-7 1.2 3H21\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/><circle cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" stroke-opacity=\".35\"/></svg></div>\n      <div><div class=\"eyebrow\">Ambient Field Workbench</div><h1>Host telemetry &amp; message transport</h1></div></div>\n    <div id=\"linkBadge\" class=\"link-badge\" data-state=\"idle\"><span class=\"dot\"></span><span id=\"linkBadgeText\">NETWORK READY · SEND MANUALLY</span></div>\n  </header>\n  <main class=\"layout\">\n    <section class=\"panel field-panel\">\n      <div class=\"panel-head\"><div><div class=\"panel-title\">Live system field</div><div class=\"panel-subtitle\">Animated from local CPU and interface telemetry</div></div><div class=\"chip\">Local metrics · 1 s</div></div>\n      <div class=\"canvas-wrap\" id=\"canvasWrap\"><canvas id=\"fieldCanvas\"></canvas>\n        <div class=\"field-legend\"><span class=\"legend-item\"><i class=\"legend-dot\"></i>CPU</span><span class=\"legend-item\"><i class=\"legend-dot blue\"></i>Network I/O</span></div>\n        <div class=\"field-caption\">VISUAL REFERENCE · 7.83 Hz IS NOT AN RF TRANSMISSION</div>\n      </div>\n      <div class=\"instrument-row\">\n        <div class=\"metric\"><div class=\"metric-label\"><span>CPU load</span><span>HOST</span></div><div class=\"metric-value\" id=\"cpuValue\">—</div><div class=\"metric-detail\" id=\"cpuDetail\">Waiting for sample</div></div>\n        <div class=\"metric\"><div class=\"metric-label\"><span>Memory</span><span>HOST</span></div><div class=\"metric-value\" id=\"memoryValue\">—</div><div class=\"metric-detail\" id=\"memoryDetail\">Waiting for sample</div></div>\n        <div class=\"metric\"><div class=\"metric-label\"><span>Download</span><span>INTERFACES</span></div><div class=\"metric-value\" id=\"rxValue\">—</div><div class=\"metric-detail\" id=\"rxDetail\">Waiting for sample</div></div>\n        <div class=\"metric\"><div class=\"metric-label\"><span>Upload</span><span>INTERFACES</span></div><div class=\"metric-value\" id=\"txValue\">—</div><div class=\"metric-detail\" id=\"txDetail\">Waiting for sample</div></div>\n      </div>\n    </section>\n    <section class=\"panel controls\">\n      <div class=\"panel-head\"><div><div class=\"panel-title\">Send a JSON message</div><div class=\"panel-subtitle\">One request, only when you press Send</div></div><div class=\"chip\">HTTPS</div></div>\n      <div class=\"controls-body\">\n        <div class=\"field-group\"><div class=\"label-row\"><label for=\"endpointInput\">Destination URL</label><span class=\"micro\">No default destination</span></div><input type=\"url\" id=\"endpointInput\" placeholder=\"https://your-service.example/api/ingest\" autocomplete=\"url\" spellcheck=\"false\"></div>\n        <div class=\"field-group\"><div class=\"label-row\"><label for=\"payloadInput\">Message payload</label><span class=\"micro\">Up to 16 KB</span></div><textarea id=\"payloadInput\" maxlength=\"16384\" placeholder=\"Enter the text you want to send…\">Ambient field status request</textarea></div>\n        <div class=\"field-group\"><div class=\"label-row\"><label for=\"tunerInput\">Tuning factor</label><span class=\"micro\">Sent as JSON metadata · 0.1–10</span></div><div class=\"tuner\"><input type=\"range\" min=\"0.1\" max=\"10\" step=\"0.1\" value=\"1\" id=\"tunerInput\"><span class=\"tuner-value\" id=\"tunerValue\">1.0×</span></div></div>\n        <div class=\"actions\"><button class=\"secondary\" id=\"previewButton\" type=\"button\">Preview locally</button><button class=\"primary\" id=\"sendButton\" type=\"button\">Send once</button></div>\n        <div class=\"disclosure\">The request contains your message, tuning factor, SHA-256 digest, and send time. HTTPS is required. HTTP is allowed only for localhost. Redirects are not followed.</div>\n      </div>\n      <div class=\"status-line\" id=\"sendStatus\" data-kind=\"idle\"><span class=\"dot\"></span><span id=\"sendStatusText\">No request sent this session.</span></div>\n    </section>\n    <section class=\"panel activity\">\n      <div class=\"panel-head\"><div><div class=\"panel-title\">Activity ledger</div><div class=\"panel-subtitle\" id=\"hostDetail\">Waiting for local machine details…</div></div><div class=\"chip\" id=\"sampleTime\">Waiting for telemetry</div></div>\n      <div class=\"activity-body\"><div class=\"event-list\" id=\"eventList\" aria-live=\"polite\"></div></div>\n    </section>\n  </main>\n  <footer class=\"footer\"><span>Telemetry is read from this computer with psutil. Nothing is transmitted automatically.</span><span>Payload preview computes size and digest locally.</span></footer>\n</div>\n";
export function mountAmbient2(host,api,onInput,onFieldFrame=()=>{}){
 let chargeParticles=[],chargeSequence=0;let dead=false,busy=false,lastSendStatus='';const fieldInput={sound:0,emf:0,emfValue:null};let lastFieldFeedback=0;const frames=new Set(),observers=[],listeners=[];
 const shadow=host.attachShadow({mode:'open'});
 shadow.innerHTML=HTML;
 const palette=globalThis.document.createElement('style');palette.textContent=`:host{color-scheme:light;--text:#233e50;--muted:#587082;--cyan:#47768f;--blue:#688ca9;--line:#a9becd88}.app{min-height:0;padding:12px;background:linear-gradient(135deg,#f1f5f8,#cedae3);color:var(--text)}.panel{background:linear-gradient(145deg,#f6f8fa,#dce5ec);box-shadow:none}.link-badge,input,textarea,select,.metric,.disclosure{background:#e8eff4!important;color:#29485d!important}button{background:#365e79!important;color:#fff!important}.layout{grid-template-columns:minmax(0,1.2fr) minmax(260px,.8fr)}@media(max-width:850px){.layout{display:flex;flex-direction:column}.canvas-wrap{height:360px}}`;shadow.append(palette);
 const document={getElementById:id=>shadow.getElementById(id),querySelectorAll:s=>shadow.querySelectorAll(s),createElement:tag=>globalThis.document.createElement(tag)};
 const window={devicePixelRatio:globalThis.devicePixelRatio,matchMedia:globalThis.matchMedia.bind(globalThis),addEventListener:(type,fn)=>{globalThis.addEventListener(type,fn);listeners.push([type,fn]);},pywebview:{api:{preview_payload:(payload,tuning_factor)=>api('ambient2/preview',{payload,tuning_factor}),transmit_payload:(payload,tuning_factor,endpoint)=>api('ambient2/send',{payload,tuning_factor,endpoint})}}};
 const ResizeObserver=class extends globalThis.ResizeObserver{constructor(fn){super(fn);observers.push(this);}};
 const requestAnimationFrame=fn=>{if(dead)return 0;const id=globalThis.requestAnimationFrame(now=>{frames.delete(id);if(dead)return;if(globalThis.document.hidden){requestAnimationFrame(fn);return;}fn(now);});frames.add(id);return id;};
 async function processInput(){if(busy)throw Error('Input is already being processed.');busy=true;const status=document.getElementById('flowStatus');try{status.textContent='Input → Unified Flux → stochastic particles…';const input=document.getElementById('payloadInput').value,factor=Number(document.getElementById('tunerInput').value);if(!chargeParticles.length)chargeParticles=birthParticles(makeCharge(input.slice(0,256),factor),performance.now());const result=await onInput(input,factor);if(!dead)status.textContent='Complete · '+JSON.stringify(result);return result;}catch(e){if(!dead)status.textContent=e.message;throw e;}finally{busy=false;}}

(() => {
  const canvas = document.getElementById('fieldCanvas');
  const ctx = canvas.getContext('2d');
  const badge = document.getElementById('linkBadge');
  const badgeText = document.getElementById('linkBadgeText');
  const statusLine = document.getElementById('sendStatus');
  const statusText = document.getElementById('sendStatusText');
  const eventList = document.getElementById('eventList');
  const payloadInput = document.getElementById('payloadInput');
  const endpointInput = document.getElementById('endpointInput');
  const tunerInput = document.getElementById('tunerInput');
  const sendButton = document.getElementById('sendButton');
  const tunerValue = document.getElementById('tunerValue');
  let metrics = {cpu_percent: 0, rx_rate: 0, tx_rate: 0, memory_percent: 0};
  let fieldTime = 0, lastFrame = performance.now(), size = {width: 0, height: 0};

  function fitCanvas() {
    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    size = {width: rect.width, height: rect.height};
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  new ResizeObserver(fitCanvas).observe(canvas);
  window.addEventListener('resize', fitCanvas);
  fitCanvas();

  function formatBytes(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—';
    const n = Math.max(0, Number(value));
    if (n < 1024) return `${Math.round(n)} B`;
    const units = ['KB', 'MB', 'GB', 'TB'];
    let amount = n / 1024, i = 0;
    while (amount >= 1024 && i < units.length - 1) { amount /= 1024; i++; }
    return `${amount.toFixed(amount >= 100 ? 0 : 1)} ${units[i]}`;
  }
  function formatRate(value) { return `${formatBytes(value)}/s`; }
  function addEvent(tag, message, kind = 'ok') {
    const row = document.createElement('div'); row.className = 'event';
    const time = document.createElement('span'); time.className = 'event-time'; time.textContent = new Date().toLocaleTimeString();
    const label = document.createElement('span'); label.className = `event-tag${kind === 'error' ? ' error' : ''}`; label.textContent = tag;
    const detail = document.createElement('span'); detail.className = 'event-message'; detail.textContent = message;
    row.append(time, label, detail); eventList.prepend(row);
    while (eventList.children.length > 30) eventList.lastElementChild.remove();
  }
  function setSendStatus(message, kind = 'idle') { statusLine.dataset.kind = kind; statusText.textContent = message; }
  function setBadge(text, state = 'idle') { badge.dataset.state = state; badgeText.textContent = text; }

  function updateTelemetry(data) {
    metrics = data;
    document.getElementById('cpuValue').textContent = Number.isFinite(data.cpu_percent) ? `${data.cpu_percent.toFixed(1)}%` : '—';
    document.getElementById('cpuDetail').textContent = `Process ${formatBytes(data.process_rss)} resident`;
    document.getElementById('memoryValue').textContent = Number.isFinite(data.memory_percent) ? `${data.memory_percent.toFixed(1)}%` : '—';
    document.getElementById('memoryDetail').textContent = `${formatBytes(data.memory_used)} of ${formatBytes(data.memory_total)}`;
    document.getElementById('rxValue').textContent = formatRate(data.rx_rate);
    document.getElementById('rxDetail').textContent = `Total ${formatBytes(data.rx_total)}`;
    document.getElementById('txValue').textContent = formatRate(data.tx_rate);
    document.getElementById('txDetail').textContent = `Total ${formatBytes(data.tx_total)}`;
    const names = Array.isArray(data.interface_names) ? data.interface_names.join(', ') : '';
    document.getElementById('hostDetail').textContent = `${data.hostname} · ${data.platform} · ${data.active_interfaces} active interface(s)${names ? ` · ${names}` : ''}`;
    document.getElementById('sampleTime').textContent = `Sampled ${new Date(data.sampled_at).toLocaleTimeString()}`;
    if (!window._firstTelemetry) { window._firstTelemetry = true; addEvent('SYSTEM', 'Live CPU, memory, process, and interface counters are connected.'); }
  }
  window.updateTelemetry = updateTelemetry;

  function setTransmissionResult(result) {
    sendButton.disabled = false; sendButton.textContent = 'Send once';
    if (result.ok) {
      setSendStatus(result.message, 'ok'); setBadge('HTTP RESPONSE RECEIVED', 'ok');
      addEvent('NETWORK', `${result.message} · ${result.sha256}`, 'ok');
    } else {
      setSendStatus(result.message, 'error'); setBadge('REQUEST FAILED', 'error');
      addEvent('NETWORK', result.message, 'error');
    }
  }
  window.setTransmissionResult = setTransmissionResult;

  document.getElementById('previewButton').addEventListener('click', async () => {
    try {
      const result = await window.pywebview.api.preview_payload(payloadInput.value, Number(tunerInput.value));
      if (result.ok) {
        setSendStatus(`Local preview · ${result.bytes} bytes · SHA-256 ${result.sha256}`, 'ok');
        addEvent('PREVIEW', `${result.bytes} UTF-8 bytes · SHA-256 ${result.sha256}`);
      } else {
        setSendStatus(result.message, 'error'); addEvent('PREVIEW', result.message, 'error');
      }
    } catch (err) { setSendStatus(String(err), 'error'); }
  });
  sendButton.addEventListener('click', async () => {
    sendButton.disabled = true; sendButton.textContent = 'Sending…';
    setSendStatus('Preparing one request…'); setBadge('REQUEST IN PROGRESS');
    try {
      await processInput();
      const result = await window.pywebview.api.transmit_payload(payloadInput.value, Number(tunerInput.value), endpointInput.value.trim());
      if (!result.ok || result.status !== 'sending') setTransmissionResult(result);
      else { setSendStatus('One request is in progress.'); addEvent('NETWORK', `POST queued to ${result.host} · ${result.sha256}`); }
    } catch (err) { setTransmissionResult({ok: false, message: String(err)}); }
  });
  tunerInput.addEventListener('input', () => { tunerValue.textContent = `${Number(tunerInput.value).toFixed(1)}×`; });

  const particles = Array.from({length: 78}, (_, i) => ({
    angle: Math.random() * Math.PI * 2, radius: .18 + Math.random() * .39,
    drift: .00008 + Math.random() * .00022, phase: Math.random() * Math.PI * 2,
    size: .8 + Math.random() * 1.6, color: i % 4 === 0 ? 'blue' : 'cyan'
  }));
  function draw(now) {
    const dt = Math.min(.05, (now - lastFrame) / 1000); lastFrame = now; fieldTime += dt;
    const w = size.width, h = size.height;
    if (w > 0 && h > 0) {
      ctx.clearRect(0, 0, w, h);
      const cx = w * .5, cy = h * .49, base = Math.min(w, h) * .24;
      const cpu = Math.max(0, Math.min(100, Number(metrics.cpu_percent) || 0));
      const io = Math.log10(1 + Math.max(0, Number(metrics.rx_rate) + Number(metrics.tx_rate)));
      const glow = ctx.createRadialGradient(cx, cy, 5, cx, cy, base * 2.8);
      glow.addColorStop(0, 'rgba(72,196,190,.14)'); glow.addColorStop(.55, 'rgba(56,121,160,.035)'); glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow; ctx.fillRect(0, 0, w, h);
      for (let ring = 1; ring <= 4; ring++) {
        ctx.beginPath(); ctx.ellipse(cx, cy, base * ring * .65, base * ring * .48, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(116,177,194,${.065 - ring * .008})`; ctx.lineWidth = 1; ctx.stroke();
      }
      const waveHeight = 5 + cpu * .18 + fieldInput.sound*24 + fieldInput.emf*12 + (fieldInput.tone||0)*20;
      ctx.beginPath();
      for (let x = 0; x <= w; x += 3) {
        const y = cy + Math.sin(x * .018 - fieldTime * (1 + io * .04)) * waveHeight + Math.sin(x * .006 + fieldTime * .7) * 4;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(112,225,220,.24)'; ctx.lineWidth = 1; ctx.stroke();
      const positions = particles.map(p => {
        p.angle += p.drift * (1 + io * .08 + fieldInput.sound*3 + fieldInput.emf) * (dt * 60);
        return {x: cx + Math.cos(p.angle) * base * (1 + .12 * Math.sin(fieldTime + p.phase)), y: cy + Math.sin(p.angle) * base * .67 * (1 + .12 * Math.cos(fieldTime * .8 + p.phase)), p};
      });
      chargeParticles=chargeParticles.filter(p=>particlePhase(p,now).alive);
      for(const p of chargeParticles){const f=particlePhase(p,now),r=base*(.15+f.age*1.65),a=p.angle+f.age*2;ctx.globalAlpha=f.alpha;ctx.fillStyle='#315e7e';ctx.beginPath();ctx.arc(cx+Math.cos(a)*r,cy+Math.sin(a)*r*.67,1.5+(p.byte%4)*.5,0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;
      if(now-lastFieldFeedback>250){lastFieldFeedback=now;onFieldFrame({charge_sequence:chargeSequence,charge_particles:chargeParticles.map(p=>({byte:p.byte,index:p.index,...particlePhase(p,now)})),time:fieldTime,sound_rms:fieldInput.sound,magnetic_nt:fieldInput.emfValue,magnetic_mode:fieldInput.magnetic_mode||'off',audio_mode:fieldInput.audio_mode||'off',positions:positions.map(p=>[Number(p.x.toFixed(3)),Number(p.y.toFixed(3))])});}
      positions.forEach((a, i) => {
        for (let j = i + 1; j < positions.length; j++) {
          const b = positions[j], dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy);
          if (d < 38) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.strokeStyle = `rgba(104,188,205,${(1 - d / 38) * .13})`; ctx.lineWidth = .7; ctx.stroke(); }
        }
      });
      positions.forEach(({x, y, p}) => {
        const color = p.color === 'blue' ? '114,170,255' : '112,225,220';
        ctx.beginPath(); ctx.arc(x, y, p.size + (p.color === 'blue' ? Math.min(1.8, io * .12) : 0), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${color},${p.color === 'blue' ? .62 : .47})`; ctx.fill();
      });
      const pulseRadius = base * (.18 + ((fieldTime * (.12 + io * .006)) % .76));
      ctx.beginPath(); ctx.arc(cx, cy, pulseRadius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(114,170,255,${.32 * (1 - pulseRadius / (base * .95))})`; ctx.lineWidth = 1.2; ctx.stroke();
      const center = ctx.createRadialGradient(cx, cy, 0, cx, cy, 34);
      center.addColorStop(0, 'rgba(112,225,220,.25)'); center.addColorStop(1, 'rgba(112,225,220,0)');
      ctx.fillStyle = center; ctx.beginPath(); ctx.arc(cx, cy, 34, 0, Math.PI * 2); ctx.fill();
      ctx.textAlign = 'center'; ctx.fillStyle = '#d2e8ed'; ctx.font = '600 10px Segoe UI, sans-serif'; ctx.save();ctx.globalAlpha=.65;ctx.shadowColor='#d9f2ff';ctx.shadowBlur=8;ctx.beginPath();ctx.moveTo(cx,cy-7);ctx.lineTo(cx+1.8,cy-1.8);ctx.lineTo(cx+7,cy);ctx.lineTo(cx+1.8,cy+1.8);ctx.lineTo(cx,cy+7);ctx.lineTo(cx-1.8,cy+1.8);ctx.lineTo(cx-7,cy);ctx.lineTo(cx-1.8,cy-1.8);ctx.closePath();ctx.fillStyle='#e5f3fa';ctx.fill();ctx.restore();ctx.fillText('AMBIENT FIELD', cx, cy + 26);
      ctx.fillStyle = '#7896a8'; ctx.font = '9px Segoe UI, sans-serif'; ctx.fillText(`CPU ${cpu.toFixed(1)}% · I/O ${formatRate(metrics.rx_rate + metrics.tx_rate)}`, cx, cy + 42);
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();


// A separate layer keeps the existing field animation and controls unchanged.
(() => {
  const wrap = document.getElementById('canvasWrap');
  const layer = document.createElement('canvas'); layer.id = 'reactiveCanvas';
  layer.setAttribute('aria-hidden', 'true'); wrap.append(layer);
  const ctx = layer.getContext('2d');
  const readout = document.createElement('div'); readout.className = 'audio-readout';
  readout.dataset.state = 'connecting';
  readout.setAttribute('role', 'img');
  readout.innerHTML = `<div class="audio-readout-head"><span class="audio-readout-label">SYSTEM AUDIO</span><span class="audio-readout-value">Connecting</span></div>
    <svg class="audio-history" viewBox="0 0 190 30" preserveAspectRatio="none" aria-hidden="true"><path class="audio-history-baseline" d="M0 15H190"/><path class="audio-history-fill"/><path class="audio-history-line"/></svg>`;
  wrap.append(readout);
  const value = readout.querySelector('.audio-readout-value');
  const historyLine = readout.querySelector('.audio-history-line');
  const historyFill = readout.querySelector('.audio-history-fill');
  const signalKeys = ['cpu_percent', 'memory_percent', 'rx_rate', 'tx_rate'];
  const cards = [...document.querySelectorAll('.instrument-row .metric')];
  const trails = cards.map((card, i) => {
    const trail = document.createElement('div'); trail.className = 'reactive-trail';
    trail.dataset.signal = signalKeys[i]; trail.setAttribute('aria-hidden', 'true');
    const fill = document.createElement('div'); fill.className = 'reactive-trail-fill';
    trail.append(fill); card.append(trail); return fill;
  });
  const clamp = v => Math.max(0, Math.min(1, Number(v) || 0));
  const levelScale = v => v > .001 ? clamp((20 * Math.log10(v) + 60) / 60) : 0;
  const rateScale = v => clamp(Math.log10(1 + Math.max(0, Number(v) || 0)) / 8);
  const history = Array(64).fill(0);
  let audio = {available: false, peak: 0}, receivedAudio = 0, receivedTelemetry = 0;
  let targets = [0, 0, 0, 0], levels = [0, 0, 0, 0], smoothAudio = 0;
  let width = 0, height = 0, last = performance.now(), activityPhase = 0;
  let historyElapsed = 0, lastStatus = '', lastAriaStatus = '';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const originalTelemetry = window.updateTelemetry;
  window.updateTelemetry = data => {
    originalTelemetry(data);
    receivedTelemetry = performance.now();
    targets = [clamp(data.cpu_percent / 100), clamp(data.memory_percent / 100),
      rateScale(data.rx_rate), rateScale(data.tx_rate)];
  };
  window.updateAudio = data => {
    const changedDevice = audio.device_id !== data.device_id;
    audio = {...data, peak: clamp(data.peak)}; receivedAudio = performance.now();
    if (!audio.available || changedDevice) history.fill(0);
  };
  function resize() {
    const bounds = wrap.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = bounds.width; height = bounds.height;
    layer.width = Math.max(1, Math.round(width * dpr)); layer.height = Math.max(1, Math.round(height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  new ResizeObserver(resize).observe(wrap); resize();
  function frame(now) {
    const dt = Math.min(.05, Math.max(0, (now - last) / 1000)); last = now;
    const fresh = receivedAudio > 0 && now - receivedAudio < 1800;
    const available = fresh && audio.available;
    const peak = available ? audio.peak : 0, targetAudio = levelScale(peak);
    smoothAudio += (targetAudio - smoothAudio) * (1 - Math.exp(-dt * (targetAudio > smoothAudio ? 24 : 7)));
    const status = !fresh ? (receivedAudio ? 'Reconnecting' : 'Connecting') :
      !audio.available ? 'Unavailable' : peak < .001 ? 'Quiet' : `${(20 * Math.log10(peak)).toFixed(1)} dBFS`;
    if (status !== lastStatus) { value.textContent = status; lastStatus = status; }
    const state = available ? 'live' : !fresh ? 'connecting' : 'unavailable';
    readout.dataset.state = state;
    readout.title = available ? 'Default playback output · peak level history · before master volume. Audio is not recorded.' :
      audio.message || 'Connecting to the default playback output.';
    // Accessibility descriptions change with connection state, not every audio sample.
    const ariaStatus = `System audio: ${state}. ${readout.title}`;
    if (ariaStatus !== lastAriaStatus) { readout.setAttribute('aria-label', ariaStatus); lastAriaStatus = ariaStatus; }
    if (!fresh) history.fill(0);
    historyElapsed += dt;
    if (historyElapsed >= .05) {
      historyElapsed %= .05; history.shift(); history.push(targetAudio);
      if (!reducedMotion.matches) {
        const upper = history.map((v, i) => `${(i * 190 / 63).toFixed(1)},${(15 - v * 13).toFixed(1)}`);
        const lower = history.map((v, i) => `${(i * 190 / 63).toFixed(1)},${(15 + v * 13).toFixed(1)}`).reverse();
        historyLine.setAttribute('d', `M${upper.join(' L')}`);
        historyFill.setAttribute('d', `M${upper.join(' L')} L${lower.join(' L')} Z`);
      } else { historyLine.setAttribute('d', ''); historyFill.setAttribute('d', ''); }
    }
    const telemetryFresh = receivedTelemetry > 0 && now - receivedTelemetry < 3500;
    levels = levels.map((v, i) => v + ((telemetryFresh ? targets[i] : 0) - v) * (1 - Math.exp(-dt * 5)));
    trails.forEach((trail, i) => {
      trail.style.transform = `scaleX(${reducedMotion.matches ? (telemetryFresh ? targets[i] : 0) : levels[i]})`;
    });
    ctx.clearRect(0, 0, width, height);
    if (!reducedMotion.matches && width > 0 && height > 0) {
      const cx = width * .5, cy = height * .49, base = Math.min(width, height) * .24;
      activityPhase += dt * (.12 + levels[0] * .55 + (levels[2] + levels[3]) * .35);
      // A breathing halo follows the measured output amplitude; silence has no halo.
      if (smoothAudio > .003) {
        for (let ring = 0; ring < 2; ring++) {
          ctx.beginPath(); ctx.ellipse(cx, cy, base * (1.24 + ring * .13 + smoothAudio * .13),
            base * (.86 + ring * .1 + smoothAudio * .09), 0, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(112,225,220,${smoothAudio * (ring ? .12 : .34)})`;
          ctx.lineWidth = 1 + smoothAudio * .7; ctx.stroke();
        }
      }
      // Short orbital traces follow CPU/memory load and actual inbound/outbound traffic.
      levels.forEach((level, i) => {
        if (level < .003) return;
        const angle = activityPhase * (i % 2 ? -1 : 1) + i * Math.PI / 2;
        const rx = base * (1.58 + i * .16), ry = rx * .72;
        ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, angle, angle + .08 + level * .72);
        ctx.strokeStyle = `rgba(${i < 2 ? '112,225,220' : '114,170,255'},${.06 + level * .26})`;
        ctx.lineWidth = 1; ctx.stroke();
        const end = angle + .08 + level * .72;
        ctx.beginPath(); ctx.arc(cx + Math.cos(end) * rx, cy + Math.sin(end) * ry, 1 + level, 0, Math.PI * 2);
        ctx.fillStyle = ctx.strokeStyle; ctx.fill();
      });
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();

 const block=globalThis.document.createElement('div');block.className='disclosure';block.innerHTML='<button id="processFlow" type="button">Process locally: Unified Flux → particles</button><p id="flowStatus" role="status">The input enters Unified Flux first. Local processing does not send the message to the destination URL.</p><a href="#beacon" id="ambientBeacon">Filtered star ↔ inference beacon</a>';
 shadow.querySelector('.controls-body').append(block);document.getElementById('processFlow').onclick=()=>processInput().catch(()=>{});document.getElementById('ambientBeacon').onclick=ev=>{ev.preventDefault();globalThis.location.hash='beacon';};
 async function telemetry(){if(dead||globalThis.document.hidden)return;try{const value=await api('ambient2/telemetry');if(dead)return;window.updateTelemetry(value);window.updateAudio(value.audio||{available:false,peak:0});const send=value.last_send;if(send&&send.status!=='sending'&&send.status!=='idle'&&JSON.stringify(send)!==lastSendStatus){lastSendStatus=JSON.stringify(send);window.setTransmissionResult(send);}}catch(e){if(!dead)window.updateAudio({available:false,peak:0,message:e.message});}}

 const earth=globalThis.document.createElement('section');earth.className='panel';earth.style.padding='16px';earth.innerHTML=`<h2 style="font-size:18px">Real Earth inputs · sound and magnetic field</h2><label><input id="earthEnabled" type="checkbox"> Enable real source inputs</label><label>Audio source<select id="earthMode"><option value="recording">BAS Halley VLF recording · offline fallback</option><option value="live">Live Locus Sonus environmental sound</option></select></label><label><input id="earthTerms" type="checkbox"> I have read and accept the live source’s terms</label><a href="https://locusonus.org/soundmap/" target="_blank" rel="noopener noreferrer">Locus Sonus source and terms ↗</a><label>Available live station<select id="earthStation"></select></label><button id="earthRefresh">Refresh live stations</button><label><input id="earthAudible" type="checkbox"> Hear the audio (analysis also works silently)</label><p id="earthAudioStatus">Audio input OFF</p><p id="earthMagStatus">Magnetometer input OFF</p><p>Environmental sound comes from public microphones. The BAS fallback is a recorded Antarctic VLF receiver signal converted to sound. NOAA supplies recent GOES magnetic measurements in nT; this is numerical magnetic data, not a live RF waveform. Source-driven particle motion returns through Unified Flux into the particles above.</p><p><a href="https://www.bas.ac.uk/project/sounds-of-space/" target="_blank" rel="noopener noreferrer">BAS recording and attribution ↗</a> · <a href="https://www.swpc.noaa.gov/products/goes-magnetometer" target="_blank" rel="noopener noreferrer">NOAA GOES magnetometer ↗</a></p><small>Primary → secondary → dated cache for magnetic data; live audio → bundled BAS recording for audio. Nothing cached is labelled live. Providers may change or end their services.</small>`;
 shadow.querySelector('.layout').after(earth);
 const eq=id=>document.getElementById(id);let soundContext=null,soundSource=null,analyser=null,gain=null,audio=null,magTimer=null,earthGeneration=0,audioKind='off';
 async function stations(){try{const result=await api('ambient2/stations');if(dead)return;eq('earthStation').replaceChildren(...result.stations.map(item=>{const option=globalThis.document.createElement('option');option.value=item.id;option.textContent=item.name;return option;}));eq('earthAudioStatus').textContent=result.stations.length+' live stations listed; select live mode and enable inputs to listen.';}catch(e){if(!dead)eq('earthAudioStatus').textContent='Live catalogue unavailable · bundled BAS recording remains available.';}}
 async function magnetic(){if(dead||!eq('earthEnabled').checked)return;const generation=earthGeneration;try{const value=await api('ambient2/geomagnetic');if(dead||generation!==earthGeneration)return;const total=Number(value.sample?.total),stamp=value.sample?.time_tag;fieldInput.emfValue=value.sample&&Number.isFinite(total)?total:null;fieldInput.emf=fieldInput.emfValue===null?0:Math.min(1,Math.abs(total)/500);fieldInput.magnetic_mode=value.mode;eq('earthMagStatus').textContent=fieldInput.emfValue===null?'NOAA unavailable · no magnetic input':`NOAA ${value.mode.toUpperCase()} · ${total.toFixed(2)} nT · sample ${stamp} · ${value.fallback?'secondary feed':'primary feed'}`;}catch(e){if(!dead&&generation===earthGeneration){fieldInput.emf=0;fieldInput.emfValue=null;eq('earthMagStatus').textContent='NOAA unavailable · '+e.message;}}}
 function stopEarth(){earthGeneration++;if(magTimer)clearInterval(magTimer);magTimer=null;if(audio){audio.pause();audio.removeAttribute('src');audio.load();}fieldInput.sound=0;fieldInput.emf=0;fieldInput.emfValue=null;if(soundContext)soundContext.suspend();}
 async function startAudio(fallback=false){if(dead||!eq('earthEnabled').checked)return;const generation=earthGeneration;const live=eq('earthMode').value==='live'&&!fallback;if(live&&!eq('earthTerms').checked){eq('earthAudioStatus').textContent='Live audio waiting for your acceptance of the source terms. NOAA can operate independently.';return;}if(live&&!eq('earthStation').value){await stations();if(!eq('earthStation').value)return;}
  if(!soundContext){const AudioContext=globalThis.AudioContext||globalThis.webkitAudioContext;soundContext=new AudioContext();audio=globalThis.document.createElement('audio');audio.preload='none';audio.crossOrigin='anonymous';soundSource=soundContext.createMediaElementSource(audio);analyser=soundContext.createAnalyser();analyser.fftSize=1024;gain=soundContext.createGain();gain.gain.value=0;soundSource.connect(analyser);analyser.connect(gain);gain.connect(soundContext.destination);
   audio.onerror=()=>{if(dead||!eq('earthEnabled').checked)return;if(audioKind==='live'){eq('earthAudioStatus').textContent='Live stream failed · switching to the recorded BAS fallback.';startAudio(true).catch(e=>eq('earthAudioStatus').textContent=e.message);}else eq('earthAudioStatus').textContent='Recording could not be played.';};
   audio.onended=()=>{if(audioKind==='live'&&eq('earthEnabled').checked)startAudio().catch(()=>{});};
   const wave=new Float32Array(analyser.fftSize);let lastLevel=0;function sample(now){if(dead)return;if(eq('earthEnabled').checked&&!audio.paused&&now-lastLevel>=100){analyser.getFloatTimeDomainData(wave);fieldInput.sound=Math.sqrt(wave.reduce((sum,v)=>sum+v*v,0)/wave.length);fieldInput.audio_mode=audioKind;eq('earthAudioStatus').textContent=`${audioKind==='live'?'LIVE ENVIRONMENTAL AUDIO':'RECORDED BAS VLF · loop'} · RMS ${fieldInput.sound.toFixed(4)}`;lastLevel=now;}requestAnimationFrame(sample);}requestAnimationFrame(sample);
  }
  gain.gain.value=eq('earthAudible').checked?.25:0;audioKind=live?'live':'recording';audio.loop=!live;audio.src=live?'/api/ambient2/audio?station='+encodeURIComponent(eq('earthStation').value)+'&key='+encodeURIComponent(globalThis.NEURAL_TOKEN||''):'/assets/halley-whistlers.wav';await soundContext.resume();if(dead||generation!==earthGeneration)return;await audio.play();
 }
 eq('earthEnabled').onchange=()=>{stopEarth();if(eq('earthEnabled').checked){magnetic();magTimer=setInterval(magnetic,60000);startAudio().catch(e=>eq('earthAudioStatus').textContent=e.message);}else{eq('earthAudioStatus').textContent='Audio input OFF';eq('earthMagStatus').textContent='Magnetometer input OFF';}};
 eq('earthRefresh').onclick=stations;eq('earthMode').onchange=eq('earthStation').onchange=()=>{if(audio)audio.pause();if(eq('earthEnabled').checked)startAudio().catch(e=>eq('earthAudioStatus').textContent=e.message);};eq('earthAudible').onchange=()=>{if(gain)gain.gain.value=eq('earthAudible').checked?.25:0;};

 const injector=globalThis.document.createElement('section');injector.className='panel';injector.style.padding='18px';injector.innerHTML=`<h2>Microcosmic Injector</h2><p>Input → charge particles in Ambient Field → Unified Flux → stochastic particles → filter and shared processing.</p><label>Intent<textarea id="mcIntent" rows="4">INTELLIGENCE_MUTATION_ALIGNMENT_INVARIANT</textarea></label><label>Order multiplier<input id="mcOrder" type="number" value="10" min="-1000000" max="1000000"></label><button id="mcFire">Fire heightened charge vector ↗</button><p id="mcStatus" role="status">Ready · materialize → animate and transmit → dematerialize.</p><small>Original transformation: UTF-8 bytes XOR integer order; calculated yield = order × 7.83. Up to 128 visual particles represent the payload; the complete transformed bytes enter the processing chain.</small>`;earth.after(injector);
 eq('mcFire').onclick=async()=>{const button=eq('mcFire');button.disabled=true;try{const charge=makeCharge(eq('mcIntent').value,Number(eq('mcOrder').value));chargeSequence++;chargeParticles=birthParticles(charge,performance.now());const payload=JSON.stringify({source:'microcosmic-injector',sequence:chargeSequence,...charge});eq('payloadInput').value=payload;eq('tunerInput').value=String(Math.max(.1,Math.min(10,Math.abs(charge.order))));eq('mcStatus').textContent='Materializing · '+charge.bytes.length+' bytes · yield '+charge.yield;const result=await processInput();eq('mcStatus').textContent='Charge passed through Ambient Field → Unified Flux → particles · '+JSON.stringify(result);}catch(e){eq('mcStatus').textContent=e.message;}finally{button.disabled=false;}};
 telemetry();const timer=setInterval(telemetry,1000);const dispose=()=>{stopEarth();if(soundContext)soundContext.close();dead=true;clearInterval(timer);frames.forEach(globalThis.cancelAnimationFrame);observers.forEach(o=>o.disconnect());listeners.forEach(([type,fn])=>globalThis.removeEventListener(type,fn));};dispose.receiveWave=value=>{fieldInput.tone=Math.max(0,Math.min(1,Number(value)||0));};return dispose;
}
