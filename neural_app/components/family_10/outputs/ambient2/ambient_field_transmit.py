"""Ambient Field Workbench: live host telemetry and explicit HTTP JSON sends.

The field animation is a visual reference, not an RF transmitter or measurement.
Network requests are sent only after the user enters a destination and clicks Send.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import platform
from neural_app import section_threads as threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any
try:
    import webview
except ImportError:
    print('[ERROR] pywebview is required. Install: python -m pip install pywebview')
    raise SystemExit(1)
try:
    import psutil
except ImportError:
    print('[ERROR] psutil is required for live host telemetry. Install: python -m pip install psutil')
    raise SystemExit(1)
TELEMETRY_INTERVAL = 1.0
MAX_PAYLOAD_BYTES = 16 * 1024
HTTP_TIMEOUT_SECONDS = 8
HTML_LAYOUT = '\n<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Ambient Field Workbench</title>\n<style>\n:root {\n  color-scheme: dark;\n  --bg: #070b12; --panel: rgba(14,22,34,.88); --line: rgba(136,173,204,.16);\n  --muted: #8193a7; --text: #e5f0f6; --cyan: #70e1dc; --blue: #72aaff;\n  --green: #82e6b4; --red: #ff898f;\n  font-family: Inter, "Segoe UI", system-ui, sans-serif;\n}\n* { box-sizing: border-box; }\nbody { margin: 0; min-width: 320px; min-height: 100vh; color: var(--text);\n  background: radial-gradient(ellipse at 18% 0%, #122638 0, transparent 38%),\n  radial-gradient(ellipse at 100% 80%, #101e32 0, transparent 34%), var(--bg); }\nbutton, input, textarea { font: inherit; }\n.app { min-height: 100vh; padding: 22px; display: flex; flex-direction: column; gap: 16px; }\n.topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; }\n.brand { display: flex; align-items: center; gap: 13px; min-width: 0; }\n.brand-mark { width: 40px; height: 40px; display: grid; place-items: center; flex: 0 0 auto;\n  border: 1px solid rgba(112,225,220,.42); border-radius: 13px; color: var(--cyan);\n  background: linear-gradient(145deg, rgba(112,225,220,.17), rgba(114,170,255,.06)); box-shadow: 0 0 24px rgba(112,225,220,.10); }\n.brand-mark svg { width: 23px; height: 23px; }\n.eyebrow { color: var(--cyan); text-transform: uppercase; letter-spacing: .19em; font-size: 10px; font-weight: 700; }\nh1 { margin: 3px 0 0; font-size: clamp(18px, 2vw, 23px); letter-spacing: -.025em; font-weight: 650; }\n.link-badge { display: inline-flex; align-items: center; gap: 9px; border: 1px solid var(--line); border-radius: 999px;\n  padding: 9px 13px; color: #b7c8d7; background: rgba(10,17,27,.75); font-size: 11px; white-space: nowrap; }\n.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 12px currentColor; }\n.link-badge[data-state="ok"] .dot { background: var(--green); }\n.link-badge[data-state="error"] .dot { background: var(--red); }\n.layout { flex: 1; min-height: 620px; display: grid; grid-template-columns: minmax(0,1.32fr) minmax(360px,.88fr);\n  grid-template-rows: minmax(340px,1fr) 178px; gap: 16px; }\n.panel { min-width: 0; border: 1px solid var(--line); border-radius: 16px; overflow: hidden;\n  background: linear-gradient(145deg, rgba(16,26,40,.92), rgba(8,14,23,.94)); box-shadow: 0 18px 48px rgba(0,0,0,.19); }\n.field-panel { display: flex; flex-direction: column; position: relative; }\n.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 17px 19px 13px; border-bottom: 1px solid var(--line); }\n.panel-title { font-size: 12px; font-weight: 650; }\n.panel-subtitle { margin-top: 4px; color: var(--muted); font-size: 10px; }\n.chip { border: 1px solid rgba(112,225,220,.23); border-radius: 999px; padding: 6px 9px; color: var(--cyan); font-size: 9px; letter-spacing: .12em; text-transform: uppercase; white-space: nowrap; }\n.canvas-wrap { flex: 1; min-height: 245px; position: relative; }\n#fieldCanvas { width: 100%; height: 100%; display: block; }\n.field-caption { position: absolute; left: 20px; bottom: 15px; color: #7891a4; font-size: 10px; letter-spacing: .04em; }\n.field-legend { position: absolute; top: 16px; right: 18px; display: flex; gap: 13px; color: #8ba0b1; font-size: 9px; }\n.legend-item { display: flex; align-items: center; gap: 6px; }\n.legend-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--cyan); }\n.legend-dot.blue { background: var(--blue); }\n.instrument-row { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 9px; padding: 0 16px 16px; }\n.metric { min-width: 0; border: 1px solid rgba(136,173,204,.12); border-radius: 11px; padding: 11px 12px; background: rgba(5,11,19,.46); }\n.metric-label { display: flex; justify-content: space-between; gap: 5px; color: var(--muted); font-size: 9px; text-transform: uppercase; letter-spacing: .12em; }\n.metric-value { margin-top: 7px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18px; font-variant-numeric: tabular-nums; }\n.metric-detail { margin-top: 4px; min-height: 12px; color: #8296a7; font-size: 9px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.controls { display: flex; flex-direction: column; }\n.controls-body { padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 13px; }\n.field-group { display: flex; flex-direction: column; gap: 7px; }\n.label-row { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }\nlabel { color: #a8bac8; font-size: 10px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }\n.micro { color: #71869a; font-size: 9px; }\ninput[type="url"], textarea { width: 100%; border: 1px solid rgba(136,173,204,.21); border-radius: 9px; outline: none;\n  color: #deebf2; background: rgba(3,8,14,.62); padding: 10px 11px; font-size: 11px; transition: border-color .16s, box-shadow .16s; }\ntextarea { min-height: 83px; resize: vertical; line-height: 1.5; }\ninput[type="url"]:focus, textarea:focus { border-color: rgba(112,225,220,.63); box-shadow: 0 0 0 3px rgba(112,225,220,.08); }\ninput::placeholder, textarea::placeholder { color: #536779; }\n.tuner { display: flex; align-items: center; gap: 11px; }\ninput[type="range"] { flex: 1; accent-color: var(--cyan); }\n.tuner-value { width: 42px; color: var(--cyan); text-align: right; font-size: 12px; font-variant-numeric: tabular-nums; }\n.actions { display: grid; grid-template-columns: 1fr 1.35fr; gap: 9px; margin-top: 2px; }\nbutton { min-height: 38px; border-radius: 9px; cursor: pointer; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; transition: transform .15s, background .15s, border-color .15s; }\nbutton:hover { transform: translateY(-1px); }\nbutton:disabled { opacity: .55; cursor: wait; transform: none; }\n.secondary { border: 1px solid rgba(136,173,204,.22); background: rgba(18,30,43,.8); color: #bad0dd; }\n.primary { border: 1px solid rgba(112,225,220,.48); background: linear-gradient(110deg, rgba(49,154,155,.34), rgba(69,115,175,.28)); color: #b5ffef; box-shadow: inset 0 1px rgba(255,255,255,.07); }\n.primary:hover { background: linear-gradient(110deg, rgba(49,154,155,.5), rgba(69,115,175,.4)); }\n.disclosure { color: #71879a; font-size: 9px; line-height: 1.5; }\n.status-line { min-height: 28px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--line); padding: 9px 16px; color: #8ca0b1; font-size: 10px; }\n.status-line[data-kind="ok"] { color: var(--green); }\n.status-line[data-kind="error"] { color: var(--red); }\n.activity { grid-column: 1 / -1; display: flex; flex-direction: column; }\n.activity-body { flex: 1; overflow: auto; padding: 10px 16px 13px; }\n.event-list { display: flex; flex-direction: column; gap: 7px; }\n.event { display: grid; grid-template-columns: 72px 69px minmax(0,1fr); gap: 9px; align-items: baseline; color: #9aafbd; font-size: 10px; line-height: 1.45; }\n.event-time { color: #627a8e; font-variant-numeric: tabular-nums; }\n.event-tag { color: var(--cyan); text-transform: uppercase; letter-spacing: .08em; font-size: 9px; }\n.event-tag.error { color: var(--red); }\n.event-message { overflow-wrap: anywhere; }\n.footer { display: flex; justify-content: space-between; gap: 12px; color: #677d90; font-size: 9px; }\n@media (max-width: 900px) { .app { padding: 14px; } .layout { grid-template-columns: minmax(0,1fr); grid-template-rows: 390px auto 170px; min-height: 0; } .activity { grid-column: 1; } .controls { min-height: 410px; } }\n@media (max-width: 540px) { .topbar { align-items: flex-start; } .link-badge { padding: 8px; font-size: 9px; } .layout { grid-template-rows: 375px auto 160px; } .instrument-row { grid-template-columns: repeat(2,minmax(0,1fr)); } .controls { min-height: 440px; } .footer { flex-direction: column; } .event { grid-template-columns: 54px 57px minmax(0,1fr); } }\n\n/* Additive overlays: all original panels, text, spacing and field drawing stay intact. */\n.metric { position: relative; }\n.reactive-trail { position: absolute; left: 10px; right: 10px; bottom: 0; height: 2px;\n  overflow: hidden; border-radius: 2px; pointer-events: none; background: rgba(112,225,220,.035); }\n.reactive-trail-fill { width: 100%; height: 100%; transform: scaleX(0); transform-origin: left;\n  background: var(--cyan); opacity: .5; box-shadow: 0 0 9px currentColor; }\n.reactive-trail[data-signal="rx_rate"] .reactive-trail-fill,\n.reactive-trail[data-signal="tx_rate"] .reactive-trail-fill { background: var(--blue); }\n#reactiveCanvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }\n.audio-readout { position: absolute; top: 16px; left: 20px; width: clamp(134px,32%,190px);\n  color: #8ba0b1; pointer-events: auto; }\n.audio-readout-head { display: flex; align-items: baseline; justify-content: space-between;\n  gap: 8px; font-size: 9px; letter-spacing: .04em; }\n.audio-readout-label { color: var(--cyan); }\n.audio-readout-value { font-size: 8px; font-variant-numeric: tabular-nums; white-space: nowrap; }\n.audio-history { display: block; width: 100%; height: 30px; margin-top: 5px; overflow: hidden; }\n.audio-history-baseline { stroke: rgba(112,225,220,.12); stroke-width: 1; }\n.audio-history-fill { fill: rgba(112,225,220,.055); }\n.audio-history-line { fill: none; stroke: rgba(112,225,220,.65); stroke-width: 1;\n  stroke-linejoin: round; stroke-linecap: round; }\n.audio-readout[data-state="unavailable"] .audio-readout-label { color: var(--muted); }\n</style>\n</head>\n<body>\n<div class="app">\n  <header class="topbar">\n    <div class="brand"><div class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M3 12h3l2.1-6 4.1 12 2.2-7 1.2 3H21" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity=".35"/></svg></div>\n      <div><div class="eyebrow">Ambient Field Workbench</div><h1>Host telemetry &amp; message transport</h1></div></div>\n    <div id="linkBadge" class="link-badge" data-state="idle"><span class="dot"></span><span id="linkBadgeText">NETWORK READY · SEND MANUALLY</span></div>\n  </header>\n  <main class="layout">\n    <section class="panel field-panel">\n      <div class="panel-head"><div><div class="panel-title">Live system field</div><div class="panel-subtitle">Animated from local CPU and interface telemetry</div></div><div class="chip">Local metrics · 1 s</div></div>\n      <div class="canvas-wrap" id="canvasWrap"><canvas id="fieldCanvas"></canvas>\n        <div class="field-legend"><span class="legend-item"><i class="legend-dot"></i>CPU</span><span class="legend-item"><i class="legend-dot blue"></i>Network I/O</span></div>\n        <div class="field-caption">VISUAL REFERENCE · 7.83 Hz IS NOT AN RF TRANSMISSION</div>\n      </div>\n      <div class="instrument-row">\n        <div class="metric"><div class="metric-label"><span>CPU load</span><span>HOST</span></div><div class="metric-value" id="cpuValue">—</div><div class="metric-detail" id="cpuDetail">Waiting for sample</div></div>\n        <div class="metric"><div class="metric-label"><span>Memory</span><span>HOST</span></div><div class="metric-value" id="memoryValue">—</div><div class="metric-detail" id="memoryDetail">Waiting for sample</div></div>\n        <div class="metric"><div class="metric-label"><span>Download</span><span>INTERFACES</span></div><div class="metric-value" id="rxValue">—</div><div class="metric-detail" id="rxDetail">Waiting for sample</div></div>\n        <div class="metric"><div class="metric-label"><span>Upload</span><span>INTERFACES</span></div><div class="metric-value" id="txValue">—</div><div class="metric-detail" id="txDetail">Waiting for sample</div></div>\n      </div>\n    </section>\n    <section class="panel controls">\n      <div class="panel-head"><div><div class="panel-title">Send a JSON message</div><div class="panel-subtitle">One request, only when you press Send</div></div><div class="chip">HTTPS</div></div>\n      <div class="controls-body">\n        <div class="field-group"><div class="label-row"><label for="endpointInput">Destination URL</label><span class="micro">No default destination</span></div><input type="url" id="endpointInput" placeholder="https://your-service.example/api/ingest" autocomplete="url" spellcheck="false"></div>\n        <div class="field-group"><div class="label-row"><label for="payloadInput">Message payload</label><span class="micro">Up to 16 KB</span></div><textarea id="payloadInput" maxlength="16384" placeholder="Enter the text you want to send…">Ambient field status request</textarea></div>\n        <div class="field-group"><div class="label-row"><label for="tunerInput">Tuning factor</label><span class="micro">Sent as JSON metadata · 0.1–10</span></div><div class="tuner"><input type="range" min="0.1" max="10" step="0.1" value="1" id="tunerInput"><span class="tuner-value" id="tunerValue">1.0×</span></div></div>\n        <div class="actions"><button class="secondary" id="previewButton" type="button">Preview locally</button><button class="primary" id="sendButton" type="button">Send once</button></div>\n        <div class="disclosure">The request contains your message, tuning factor, SHA-256 digest, and send time. HTTPS is required. HTTP is allowed only for localhost. Redirects are not followed.</div>\n      </div>\n      <div class="status-line" id="sendStatus" data-kind="idle"><span class="dot"></span><span id="sendStatusText">No request sent this session.</span></div>\n    </section>\n    <section class="panel activity">\n      <div class="panel-head"><div><div class="panel-title">Activity ledger</div><div class="panel-subtitle" id="hostDetail">Waiting for local machine details…</div></div><div class="chip" id="sampleTime">Waiting for telemetry</div></div>\n      <div class="activity-body"><div class="event-list" id="eventList" aria-live="polite"></div></div>\n    </section>\n  </main>\n  <footer class="footer"><span>Telemetry is read from this computer with psutil. Nothing is transmitted automatically.</span><span>Payload preview computes size and digest locally.</span></footer>\n</div>\n<script>\n(() => {\n  const canvas = document.getElementById(\'fieldCanvas\');\n  const ctx = canvas.getContext(\'2d\');\n  const badge = document.getElementById(\'linkBadge\');\n  const badgeText = document.getElementById(\'linkBadgeText\');\n  const statusLine = document.getElementById(\'sendStatus\');\n  const statusText = document.getElementById(\'sendStatusText\');\n  const eventList = document.getElementById(\'eventList\');\n  const payloadInput = document.getElementById(\'payloadInput\');\n  const endpointInput = document.getElementById(\'endpointInput\');\n  const tunerInput = document.getElementById(\'tunerInput\');\n  const sendButton = document.getElementById(\'sendButton\');\n  const tunerValue = document.getElementById(\'tunerValue\');\n  let metrics = {cpu_percent: 0, rx_rate: 0, tx_rate: 0, memory_percent: 0};\n  let fieldTime = 0, lastFrame = performance.now(), size = {width: 0, height: 0};\n\n  function fitCanvas() {\n    const rect = canvas.getBoundingClientRect();\n    const dpr = Math.min(window.devicePixelRatio || 1, 2);\n    size = {width: rect.width, height: rect.height};\n    canvas.width = Math.max(1, Math.round(rect.width * dpr));\n    canvas.height = Math.max(1, Math.round(rect.height * dpr));\n    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);\n  }\n  new ResizeObserver(fitCanvas).observe(canvas);\n  window.addEventListener(\'resize\', fitCanvas);\n  fitCanvas();\n\n  function formatBytes(value) {\n    if (value === null || value === undefined || !Number.isFinite(Number(value))) return \'—\';\n    const n = Math.max(0, Number(value));\n    if (n < 1024) return `${Math.round(n)} B`;\n    const units = [\'KB\', \'MB\', \'GB\', \'TB\'];\n    let amount = n / 1024, i = 0;\n    while (amount >= 1024 && i < units.length - 1) { amount /= 1024; i++; }\n    return `${amount.toFixed(amount >= 100 ? 0 : 1)} ${units[i]}`;\n  }\n  function formatRate(value) { return `${formatBytes(value)}/s`; }\n  function addEvent(tag, message, kind = \'ok\') {\n    const row = document.createElement(\'div\'); row.className = \'event\';\n    const time = document.createElement(\'span\'); time.className = \'event-time\'; time.textContent = new Date().toLocaleTimeString();\n    const label = document.createElement(\'span\'); label.className = `event-tag${kind === \'error\' ? \' error\' : \'\'}`; label.textContent = tag;\n    const detail = document.createElement(\'span\'); detail.className = \'event-message\'; detail.textContent = message;\n    row.append(time, label, detail); eventList.prepend(row);\n    while (eventList.children.length > 30) eventList.lastElementChild.remove();\n  }\n  function setSendStatus(message, kind = \'idle\') { statusLine.dataset.kind = kind; statusText.textContent = message; }\n  function setBadge(text, state = \'idle\') { badge.dataset.state = state; badgeText.textContent = text; }\n\n  function updateTelemetry(data) {\n    metrics = data;\n    document.getElementById(\'cpuValue\').textContent = Number.isFinite(data.cpu_percent) ? `${data.cpu_percent.toFixed(1)}%` : \'—\';\n    document.getElementById(\'cpuDetail\').textContent = `Process ${formatBytes(data.process_rss)} resident`;\n    document.getElementById(\'memoryValue\').textContent = Number.isFinite(data.memory_percent) ? `${data.memory_percent.toFixed(1)}%` : \'—\';\n    document.getElementById(\'memoryDetail\').textContent = `${formatBytes(data.memory_used)} of ${formatBytes(data.memory_total)}`;\n    document.getElementById(\'rxValue\').textContent = formatRate(data.rx_rate);\n    document.getElementById(\'rxDetail\').textContent = `Total ${formatBytes(data.rx_total)}`;\n    document.getElementById(\'txValue\').textContent = formatRate(data.tx_rate);\n    document.getElementById(\'txDetail\').textContent = `Total ${formatBytes(data.tx_total)}`;\n    const names = Array.isArray(data.interface_names) ? data.interface_names.join(\', \') : \'\';\n    document.getElementById(\'hostDetail\').textContent = `${data.hostname} · ${data.platform} · ${data.active_interfaces} active interface(s)${names ? ` · ${names}` : \'\'}`;\n    document.getElementById(\'sampleTime\').textContent = `Sampled ${new Date(data.sampled_at).toLocaleTimeString()}`;\n    if (!window._firstTelemetry) { window._firstTelemetry = true; addEvent(\'SYSTEM\', \'Live CPU, memory, process, and interface counters are connected.\'); }\n  }\n  window.updateTelemetry = updateTelemetry;\n\n  function setTransmissionResult(result) {\n    sendButton.disabled = false; sendButton.textContent = \'Send once\';\n    if (result.ok) {\n      setSendStatus(result.message, \'ok\'); setBadge(\'HTTP RESPONSE RECEIVED\', \'ok\');\n      addEvent(\'NETWORK\', `${result.message} · ${result.sha256}`, \'ok\');\n    } else {\n      setSendStatus(result.message, \'error\'); setBadge(\'REQUEST FAILED\', \'error\');\n      addEvent(\'NETWORK\', result.message, \'error\');\n    }\n  }\n  window.setTransmissionResult = setTransmissionResult;\n\n  document.getElementById(\'previewButton\').addEventListener(\'click\', async () => {\n    try {\n      const result = await window.pywebview.api.preview_payload(payloadInput.value, Number(tunerInput.value));\n      if (result.ok) {\n        setSendStatus(`Local preview · ${result.bytes} bytes · SHA-256 ${result.sha256}`, \'ok\');\n        addEvent(\'PREVIEW\', `${result.bytes} UTF-8 bytes · SHA-256 ${result.sha256}`);\n      } else {\n        setSendStatus(result.message, \'error\'); addEvent(\'PREVIEW\', result.message, \'error\');\n      }\n    } catch (err) { setSendStatus(String(err), \'error\'); }\n  });\n  sendButton.addEventListener(\'click\', async () => {\n    sendButton.disabled = true; sendButton.textContent = \'Sending…\';\n    setSendStatus(\'Preparing one request…\'); setBadge(\'REQUEST IN PROGRESS\');\n    try {\n      const result = await window.pywebview.api.transmit_payload(payloadInput.value, Number(tunerInput.value), endpointInput.value.trim());\n      if (!result.ok || result.status !== \'sending\') setTransmissionResult(result);\n      else { setSendStatus(\'One request is in progress.\'); addEvent(\'NETWORK\', `POST queued to ${result.host} · ${result.sha256}`); }\n    } catch (err) { setTransmissionResult({ok: false, message: String(err)}); }\n  });\n  tunerInput.addEventListener(\'input\', () => { tunerValue.textContent = `${Number(tunerInput.value).toFixed(1)}×`; });\n\n  const particles = Array.from({length: 78}, (_, i) => ({\n    angle: Math.random() * Math.PI * 2, radius: .18 + Math.random() * .39,\n    drift: .00008 + Math.random() * .00022, phase: Math.random() * Math.PI * 2,\n    size: .8 + Math.random() * 1.6, color: i % 4 === 0 ? \'blue\' : \'cyan\'\n  }));\n  function draw(now) {\n    const dt = Math.min(.05, (now - lastFrame) / 1000); lastFrame = now; fieldTime += dt;\n    const w = size.width, h = size.height;\n    if (w > 0 && h > 0) {\n      ctx.clearRect(0, 0, w, h);\n      const cx = w * .5, cy = h * .49, base = Math.min(w, h) * .24;\n      const cpu = Math.max(0, Math.min(100, Number(metrics.cpu_percent) || 0));\n      const io = Math.log10(1 + Math.max(0, Number(metrics.rx_rate) + Number(metrics.tx_rate)));\n      const glow = ctx.createRadialGradient(cx, cy, 5, cx, cy, base * 2.8);\n      glow.addColorStop(0, \'rgba(72,196,190,.14)\'); glow.addColorStop(.55, \'rgba(56,121,160,.035)\'); glow.addColorStop(1, \'rgba(0,0,0,0)\');\n      ctx.fillStyle = glow; ctx.fillRect(0, 0, w, h);\n      for (let ring = 1; ring <= 4; ring++) {\n        ctx.beginPath(); ctx.ellipse(cx, cy, base * ring * .65, base * ring * .48, 0, 0, Math.PI * 2);\n        ctx.strokeStyle = `rgba(116,177,194,${.065 - ring * .008})`; ctx.lineWidth = 1; ctx.stroke();\n      }\n      const waveHeight = 5 + cpu * .18;\n      ctx.beginPath();\n      for (let x = 0; x <= w; x += 3) {\n        const y = cy + Math.sin(x * .018 - fieldTime * (1 + io * .04)) * waveHeight + Math.sin(x * .006 + fieldTime * .7) * 4;\n        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);\n      }\n      ctx.strokeStyle = \'rgba(112,225,220,.24)\'; ctx.lineWidth = 1; ctx.stroke();\n      const positions = particles.map(p => {\n        p.angle += p.drift * (1 + io * .08) * (dt * 60);\n        return {x: cx + Math.cos(p.angle) * base * (1 + .12 * Math.sin(fieldTime + p.phase)), y: cy + Math.sin(p.angle) * base * .67 * (1 + .12 * Math.cos(fieldTime * .8 + p.phase)), p};\n      });\n      positions.forEach((a, i) => {\n        for (let j = i + 1; j < positions.length; j++) {\n          const b = positions[j], dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy);\n          if (d < 38) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.strokeStyle = `rgba(104,188,205,${(1 - d / 38) * .13})`; ctx.lineWidth = .7; ctx.stroke(); }\n        }\n      });\n      positions.forEach(({x, y, p}) => {\n        const color = p.color === \'blue\' ? \'114,170,255\' : \'112,225,220\';\n        ctx.beginPath(); ctx.arc(x, y, p.size + (p.color === \'blue\' ? Math.min(1.8, io * .12) : 0), 0, Math.PI * 2);\n        ctx.fillStyle = `rgba(${color},${p.color === \'blue\' ? .62 : .47})`; ctx.fill();\n      });\n      const pulseRadius = base * (.18 + ((fieldTime * (.12 + io * .006)) % .76));\n      ctx.beginPath(); ctx.arc(cx, cy, pulseRadius, 0, Math.PI * 2);\n      ctx.strokeStyle = `rgba(114,170,255,${.32 * (1 - pulseRadius / (base * .95))})`; ctx.lineWidth = 1.2; ctx.stroke();\n      const center = ctx.createRadialGradient(cx, cy, 0, cx, cy, 34);\n      center.addColorStop(0, \'rgba(112,225,220,.25)\'); center.addColorStop(1, \'rgba(112,225,220,0)\');\n      ctx.fillStyle = center; ctx.beginPath(); ctx.arc(cx, cy, 34, 0, Math.PI * 2); ctx.fill();\n      ctx.textAlign = \'center\'; ctx.fillStyle = \'#d2e8ed\'; ctx.font = \'600 10px Segoe UI, sans-serif\'; ctx.fillText(\'AMBIENT FIELD\', cx, cy - 3);\n      ctx.fillStyle = \'#7896a8\'; ctx.font = \'9px Segoe UI, sans-serif\'; ctx.fillText(`CPU ${cpu.toFixed(1)}% · I/O ${formatRate(metrics.rx_rate + metrics.tx_rate)}`, cx, cy + 13);\n    }\n    requestAnimationFrame(draw);\n  }\n  requestAnimationFrame(draw);\n})();\n</script>\n\n<script>\n// A separate layer keeps the existing field animation and controls unchanged.\n(() => {\n  const wrap = document.getElementById(\'canvasWrap\');\n  const layer = document.createElement(\'canvas\'); layer.id = \'reactiveCanvas\';\n  layer.setAttribute(\'aria-hidden\', \'true\'); wrap.append(layer);\n  const ctx = layer.getContext(\'2d\');\n  const readout = document.createElement(\'div\'); readout.className = \'audio-readout\';\n  readout.dataset.state = \'connecting\';\n  readout.setAttribute(\'role\', \'img\');\n  readout.innerHTML = `<div class="audio-readout-head"><span class="audio-readout-label">SYSTEM AUDIO</span><span class="audio-readout-value">Connecting</span></div>\n    <svg class="audio-history" viewBox="0 0 190 30" preserveAspectRatio="none" aria-hidden="true"><path class="audio-history-baseline" d="M0 15H190"/><path class="audio-history-fill"/><path class="audio-history-line"/></svg>`;\n  wrap.append(readout);\n  const value = readout.querySelector(\'.audio-readout-value\');\n  const historyLine = readout.querySelector(\'.audio-history-line\');\n  const historyFill = readout.querySelector(\'.audio-history-fill\');\n  const signalKeys = [\'cpu_percent\', \'memory_percent\', \'rx_rate\', \'tx_rate\'];\n  const cards = [...document.querySelectorAll(\'.instrument-row .metric\')];\n  const trails = cards.map((card, i) => {\n    const trail = document.createElement(\'div\'); trail.className = \'reactive-trail\';\n    trail.dataset.signal = signalKeys[i]; trail.setAttribute(\'aria-hidden\', \'true\');\n    const fill = document.createElement(\'div\'); fill.className = \'reactive-trail-fill\';\n    trail.append(fill); card.append(trail); return fill;\n  });\n  const clamp = v => Math.max(0, Math.min(1, Number(v) || 0));\n  const levelScale = v => v > .001 ? clamp((20 * Math.log10(v) + 60) / 60) : 0;\n  const rateScale = v => clamp(Math.log10(1 + Math.max(0, Number(v) || 0)) / 8);\n  const history = Array(64).fill(0);\n  let audio = {available: false, peak: 0}, receivedAudio = 0, receivedTelemetry = 0;\n  let targets = [0, 0, 0, 0], levels = [0, 0, 0, 0], smoothAudio = 0;\n  let width = 0, height = 0, last = performance.now(), activityPhase = 0;\n  let historyElapsed = 0, lastStatus = \'\', lastAriaStatus = \'\';\n  const reducedMotion = window.matchMedia(\'(prefers-reduced-motion: reduce)\');\n  const originalTelemetry = window.updateTelemetry;\n  window.updateTelemetry = data => {\n    originalTelemetry(data);\n    receivedTelemetry = performance.now();\n    targets = [clamp(data.cpu_percent / 100), clamp(data.memory_percent / 100),\n      rateScale(data.rx_rate), rateScale(data.tx_rate)];\n  };\n  window.updateAudio = data => {\n    const changedDevice = audio.device_id !== data.device_id;\n    audio = {...data, peak: clamp(data.peak)}; receivedAudio = performance.now();\n    if (!audio.available || changedDevice) history.fill(0);\n  };\n  function resize() {\n    const bounds = wrap.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);\n    width = bounds.width; height = bounds.height;\n    layer.width = Math.max(1, Math.round(width * dpr)); layer.height = Math.max(1, Math.round(height * dpr));\n    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);\n  }\n  new ResizeObserver(resize).observe(wrap); resize();\n  function frame(now) {\n    const dt = Math.min(.05, Math.max(0, (now - last) / 1000)); last = now;\n    const fresh = receivedAudio > 0 && now - receivedAudio < 1800;\n    const available = fresh && audio.available;\n    const peak = available ? audio.peak : 0, targetAudio = levelScale(peak);\n    smoothAudio += (targetAudio - smoothAudio) * (1 - Math.exp(-dt * (targetAudio > smoothAudio ? 24 : 7)));\n    const status = !fresh ? (receivedAudio ? \'Reconnecting\' : \'Connecting\') :\n      !audio.available ? \'Unavailable\' : peak < .001 ? \'Quiet\' : `${(20 * Math.log10(peak)).toFixed(1)} dBFS`;\n    if (status !== lastStatus) { value.textContent = status; lastStatus = status; }\n    const state = available ? \'live\' : !fresh ? \'connecting\' : \'unavailable\';\n    readout.dataset.state = state;\n    readout.title = available ? \'Default playback output · peak level history · before master volume. Audio is not recorded.\' :\n      audio.message || \'Connecting to the default playback output.\';\n    // Accessibility descriptions change with connection state, not every audio sample.\n    const ariaStatus = `System audio: ${state}. ${readout.title}`;\n    if (ariaStatus !== lastAriaStatus) { readout.setAttribute(\'aria-label\', ariaStatus); lastAriaStatus = ariaStatus; }\n    if (!fresh) history.fill(0);\n    historyElapsed += dt;\n    if (historyElapsed >= .05) {\n      historyElapsed %= .05; history.shift(); history.push(targetAudio);\n      if (!reducedMotion.matches) {\n        const upper = history.map((v, i) => `${(i * 190 / 63).toFixed(1)},${(15 - v * 13).toFixed(1)}`);\n        const lower = history.map((v, i) => `${(i * 190 / 63).toFixed(1)},${(15 + v * 13).toFixed(1)}`).reverse();\n        historyLine.setAttribute(\'d\', `M${upper.join(\' L\')}`);\n        historyFill.setAttribute(\'d\', `M${upper.join(\' L\')} L${lower.join(\' L\')} Z`);\n      } else { historyLine.setAttribute(\'d\', \'\'); historyFill.setAttribute(\'d\', \'\'); }\n    }\n    const telemetryFresh = receivedTelemetry > 0 && now - receivedTelemetry < 3500;\n    levels = levels.map((v, i) => v + ((telemetryFresh ? targets[i] : 0) - v) * (1 - Math.exp(-dt * 5)));\n    trails.forEach((trail, i) => {\n      trail.style.transform = `scaleX(${reducedMotion.matches ? (telemetryFresh ? targets[i] : 0) : levels[i]})`;\n    });\n    ctx.clearRect(0, 0, width, height);\n    if (!reducedMotion.matches && width > 0 && height > 0) {\n      const cx = width * .5, cy = height * .49, base = Math.min(width, height) * .24;\n      activityPhase += dt * (.12 + levels[0] * .55 + (levels[2] + levels[3]) * .35);\n      // A breathing halo follows the measured output amplitude; silence has no halo.\n      if (smoothAudio > .003) {\n        for (let ring = 0; ring < 2; ring++) {\n          ctx.beginPath(); ctx.ellipse(cx, cy, base * (1.24 + ring * .13 + smoothAudio * .13),\n            base * (.86 + ring * .1 + smoothAudio * .09), 0, 0, Math.PI * 2);\n          ctx.strokeStyle = `rgba(112,225,220,${smoothAudio * (ring ? .12 : .34)})`;\n          ctx.lineWidth = 1 + smoothAudio * .7; ctx.stroke();\n        }\n      }\n      // Short orbital traces follow CPU/memory load and actual inbound/outbound traffic.\n      levels.forEach((level, i) => {\n        if (level < .003) return;\n        const angle = activityPhase * (i % 2 ? -1 : 1) + i * Math.PI / 2;\n        const rx = base * (1.58 + i * .16), ry = rx * .72;\n        ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, angle, angle + .08 + level * .72);\n        ctx.strokeStyle = `rgba(${i < 2 ? \'112,225,220\' : \'114,170,255\'},${.06 + level * .26})`;\n        ctx.lineWidth = 1; ctx.stroke();\n        const end = angle + .08 + level * .72;\n        ctx.beginPath(); ctx.arc(cx + Math.cos(end) * rx, cy + Math.sin(end) * ry, 1 + level, 0, Math.PI * 2);\n        ctx.fillStyle = ctx.strokeStyle; ctx.fill();\n      });\n    }\n    requestAnimationFrame(frame);\n  }\n  requestAnimationFrame(frame);\n})();\n</script>\n</body>\n</html>\n'

class _WindowsOutputMeter:
    """Read Windows' default playback peak meter without recording audio.

    COM pointers are created, read, and released on the audio worker thread.
    The meter is before master-volume attenuation (Windows Core Audio behavior).
    No third-party audio package, microphone, or loopback recording is needed.
    """

    def __init__(self) -> None:
        if os.name != 'nt':
            raise OSError('System audio metering is available on Windows.')
        import ctypes
        import uuid
        self._ct = ctypes
        self._com_initialized = False
        self._enumerator = ctypes.c_void_p()
        self._meter = ctypes.c_void_p()
        self._device_id = ''
        self._next_device_check = 0.0

        class GUID(ctypes.Structure):
            _fields_ = [('data1', ctypes.c_uint32), ('data2', ctypes.c_uint16), ('data3', ctypes.c_uint16), ('data4', ctypes.c_ubyte * 8)]
        self._guid_type = GUID
        self._meter_iid = GUID.from_buffer_copy(uuid.UUID('C02216F6-8C67-4B5B-9D00-D008E73E0064').bytes_le)
        clsid = GUID.from_buffer_copy(uuid.UUID('BCDE0395-E52F-467C-8E3D-C4579291692E').bytes_le)
        iid = GUID.from_buffer_copy(uuid.UUID('A95664D2-9614-4F35-A746-DE8DB63617E6').bytes_le)
        self._ole = ctypes.OleDLL('ole32')
        self._ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self._ole.CoInitializeEx.restype = ctypes.c_long
        self._ole.CoCreateInstance.argtypes = [ctypes.POINTER(GUID), ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
        self._ole.CoCreateInstance.restype = ctypes.c_long
        self._ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        self._ole.CoTaskMemFree.restype = None
        self._ole.CoUninitialize.argtypes = []
        self._ole.CoUninitialize.restype = None
        try:
            self._check(self._ole.CoInitializeEx(None, 0))
            self._com_initialized = True
            self._check(self._ole.CoCreateInstance(ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(self._enumerator)))
            self._refresh_device()
        except Exception:
            self.close()
            raise

    @staticmethod
    def _check(result: int) -> None:
        if result < 0:
            raise OSError(f'Windows audio meter error 0x{result & 4294967295:08X}')

    def _method(self, pointer, slot, argtypes, *args):
        ct = self._ct
        table = ct.cast(pointer, ct.POINTER(ct.POINTER(ct.c_void_p))).contents
        function = ct.WINFUNCTYPE(ct.c_long, ct.c_void_p, *argtypes)(table[slot])
        return function(pointer, *args)

    def _release(self, pointer) -> None:
        if pointer:
            self._method(pointer, 2, [])
            pointer.value = None

    def _refresh_device(self) -> None:
        ct = self._ct
        device, device_id, new_meter = (ct.c_void_p(), ct.c_void_p(), ct.c_void_p())
        try:
            self._check(self._method(self._enumerator, 4, [ct.c_int, ct.c_int, ct.POINTER(ct.c_void_p)], 0, 1, ct.byref(device)))
            self._check(self._method(device, 5, [ct.POINTER(ct.c_void_p)], ct.byref(device_id)))
            identifier = ct.wstring_at(device_id)
            if identifier != self._device_id or not self._meter:
                self._check(self._method(device, 3, [ct.POINTER(self._guid_type), ct.c_uint32, ct.c_void_p, ct.POINTER(ct.c_void_p)], ct.byref(self._meter_iid), 23, None, ct.byref(new_meter)))
                self._release(self._meter)
                self._meter, new_meter = (new_meter, ct.c_void_p())
                self._device_id = identifier
        finally:
            if device_id:
                self._ole.CoTaskMemFree(device_id)
            self._release(new_meter)
            self._release(device)
        self._next_device_check = time.monotonic() + 1.0

    def read(self) -> dict[str, Any]:
        if time.monotonic() >= self._next_device_check:
            self._refresh_device()
        peak = self._ct.c_float()
        self._check(self._method(self._meter, 3, [self._ct.POINTER(self._ct.c_float)], self._ct.byref(peak)))
        return {'available': True, 'peak': round(max(0.0, min(1.0, peak.value)), 6), 'device_id': self._device_id}

    def close(self) -> None:
        self._release(self._meter)
        self._release(self._enumerator)
        if self._com_initialized:
            self._ole.CoUninitialize()
            self._com_initialized = False

def audio_broadcast_loop(window: Any, stop_event: threading.Event) -> None:
    """Read the playback meter at 20 Hz; reconnect after device/service changes."""
    meter = None
    try:
        while not stop_event.is_set():
            tick = time.monotonic()
            try:
                if meter is None:
                    meter = _WindowsOutputMeter()
                sample = meter.read()
            except Exception as exc:
                if meter is not None:
                    meter.close()
                    meter = None
                sample = {'available': False, 'peak': 0, 'message': f'Playback meter unavailable; retrying. {str(exc)[:160]}'}
            try:
                window.evaluate_js(f'window.updateAudio({json.dumps(sample, ensure_ascii=True)})')
            except Exception:
                break
            delay = 0.05 if sample['available'] else 2.0
            stop_event.wait(max(0.0, delay - (time.monotonic() - tick)))
    finally:
        if meter is not None:
            meter.close()

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Keep a POST tied to the destination the user entered."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class AmbientFieldEngine:
    """Collect live host counters and send a user-authored JSON payload on demand."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._window = None
        self._send_in_progress = False
        self._last_send: dict[str, Any] = {'status': 'idle'}
        self._payload_buffer = bytearray(MAX_PAYLOAD_BYTES)

    def attach_window(self, window: Any) -> None:
        self._window = window

    def _prepare_payload(self, payload: Any, tuning_factor: Any) -> tuple[dict[str, Any] | None, str | None]:
        if not isinstance(payload, str) or not payload.strip():
            return (None, 'Enter a message before previewing or sending.')
        encoded = payload.encode('utf-8')
        if len(encoded) > MAX_PAYLOAD_BYTES:
            return (None, f'The UTF-8 payload exceeds the {MAX_PAYLOAD_BYTES:,}-byte limit.')
        try:
            factor = float(tuning_factor)
        except (TypeError, ValueError):
            return (None, 'Tuning factor must be a number from 0.1 to 10.0.')
        if not math.isfinite(factor) or not 0.1 <= factor <= 10.0:
            return (None, 'Tuning factor must be between 0.1 and 10.0.')
        digest = hashlib.sha256(encoded).hexdigest()
        with self._lock:
            self._payload_buffer[:] = b'\x00' * len(self._payload_buffer)
            self._payload_buffer[:len(encoded)] = encoded
        return ({'payload': payload, 'payload_bytes': len(encoded), 'tuning_factor': factor, 'sha256': digest}, None)

    def preview_payload(self, payload: str, tuning_factor: float) -> dict[str, Any]:
        prepared, error = self._prepare_payload(payload, tuning_factor)
        if error:
            return {'ok': False, 'message': error}
        assert prepared is not None
        return {'ok': True, 'bytes': prepared['payload_bytes'], 'sha256': prepared['sha256'], 'message': 'Payload previewed locally; nothing was transmitted.'}

    @staticmethod
    def _validate_endpoint(endpoint: str) -> tuple[str | None, str | None]:
        if not isinstance(endpoint, str) or not endpoint.strip():
            return (None, 'Enter the HTTPS endpoint that should receive this message.')
        try:
            parsed = urllib.parse.urlsplit(endpoint.strip())
            hostname = parsed.hostname
        except ValueError:
            return (None, 'The destination URL is not valid.')
        if not parsed.scheme or not hostname or parsed.username or parsed.password or parsed.fragment:
            return (None, 'Enter a complete URL without credentials or a fragment.')
        scheme = parsed.scheme.lower()
        if scheme == 'https' or (scheme == 'http' and hostname.lower() in {'localhost', '127.0.0.1', '::1'}):
            return (endpoint.strip(), None)
        return (None, 'Use HTTPS. HTTP is allowed only for localhost, 127.0.0.1, or ::1.')

    def transmit_payload(self, payload: str, tuning_factor: float, endpoint: str) -> dict[str, Any]:
        prepared, error = self._prepare_payload(payload, tuning_factor)
        if error:
            return {'ok': False, 'message': error}
        valid_endpoint, error = self._validate_endpoint(endpoint)
        if error:
            return {'ok': False, 'message': error}
        assert prepared is not None and valid_endpoint is not None
        with self._lock:
            if self._send_in_progress:
                return {'ok': False, 'message': 'A request is already in progress; wait for its response.'}
            self._send_in_progress = True
            self._last_send = {'status': 'sending', 'sha256': prepared['sha256']}
        body = json.dumps({'payload': prepared['payload'], 'tuning_factor': prepared['tuning_factor'], 'sha256': prepared['sha256'], 'sent_at': datetime.now(timezone.utc).isoformat()}, ensure_ascii=False).encode('utf-8')
        try:
            worker = threading.Thread(target=self._send_request, args=(valid_endpoint, body, prepared['sha256']), name='ambient-field-http-send', daemon=True)
            worker.start()
        except Exception as exc:
            with self._lock:
                self._send_in_progress = False
            return {'ok': False, 'message': f'Could not start the network request: {exc}'}
        host = urllib.parse.urlsplit(valid_endpoint).hostname or 'destination'
        return {'ok': True, 'status': 'sending', 'host': host, 'sha256': prepared['sha256']}

    def _send_request(self, endpoint: str, body: bytes, digest: str) -> None:
        request = urllib.request.Request(endpoint, data=body, headers={'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json, text/plain, */*'}, method='POST')
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                response.read(2048)
                status = int(response.status)
                result = {'ok': 200 <= status < 300, 'message': f'HTTP {status} · {urllib.parse.urlsplit(endpoint).hostname}', 'sha256': digest}
        except urllib.error.HTTPError as exc:
            result = {'ok': False, 'message': f'HTTP {exc.code} · {urllib.parse.urlsplit(endpoint).hostname}', 'sha256': digest}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, 'reason', exc)
            result = {'ok': False, 'message': f'Request failed: {str(reason)[:220]}', 'sha256': digest}
        except Exception as exc:
            result = {'ok': False, 'message': f'Request failed: {str(exc)[:220]}', 'sha256': digest}
        with self._lock:
            self._send_in_progress = False
            self._last_send = {'status': 'ok' if result['ok'] else 'error', **result}
            window = self._window
        if window is not None:
            try:
                payload_json = json.dumps(result, ensure_ascii=True)
                window.evaluate_js(f'window.setTransmissionResult({payload_json})')
            except Exception:
                pass

    def live_telemetry(self, elapsed: float, previous_rx: int | None, previous_tx: int | None) -> dict[str, Any]:
        sampled = datetime.now(timezone.utc).isoformat()
        try:
            cpu_percent = float(psutil.cpu_percent(interval=None))
            memory = psutil.virtual_memory()
            process_rss = int(psutil.Process(os.getpid()).memory_info().rss)
            pernic = psutil.net_io_counters(pernic=True) or {}
            interface_stats = psutil.net_if_stats() or {}
            active_names = [name for name in pernic if name in interface_stats and interface_stats[name].isup]
            if not active_names:
                active_names = list(pernic)
            rx_total = sum((int(pernic[name].bytes_recv) for name in active_names))
            tx_total = sum((int(pernic[name].bytes_sent) for name in active_names))
            elapsed = max(elapsed, 0.001)
            rx_rate = 0.0 if previous_rx is None else max(0.0, (rx_total - previous_rx) / elapsed)
            tx_rate = 0.0 if previous_tx is None else max(0.0, (tx_total - previous_tx) / elapsed)
            with self._lock:
                send_state = self._last_send.copy()
            return {'cpu_percent': cpu_percent, 'memory_percent': float(memory.percent), 'memory_used': int(memory.used), 'memory_total': int(memory.total), 'process_rss': process_rss, 'rx_total': rx_total, 'tx_total': tx_total, 'rx_rate': rx_rate, 'tx_rate': tx_rate, 'active_interfaces': len(active_names), 'interface_names': active_names[:6], 'hostname': platform.node() or 'This computer', 'platform': f'{platform.system()} {platform.release()}', 'sampled_at': sampled, 'last_send': send_state}
        except Exception as exc:
            return {'cpu_percent': None, 'memory_percent': None, 'memory_used': None, 'memory_total': None, 'process_rss': None, 'rx_total': None, 'tx_total': None, 'rx_rate': None, 'tx_rate': None, 'active_interfaces': 0, 'interface_names': [], 'hostname': platform.node() or 'This computer', 'platform': f'{platform.system()} {platform.release()}', 'sampled_at': sampled, 'telemetry_error': str(exc)[:180]}
ENGINE = AmbientFieldEngine()

def telemetry_broadcast_loop(window: Any, stop_event: threading.Event) -> None:
    """Send real local telemetry to the UI once per second."""
    stop_event.wait(1.0)
    previous_rx: int | None = None
    previous_tx: int | None = None
    previous_time = time.perf_counter()
    next_tick = previous_time
    for _shared_tick in range(1):
        now = time.perf_counter()
        elapsed = max(now - previous_time, 0.001)
        telemetry = ENGINE.live_telemetry(elapsed, previous_rx, previous_tx)
        previous_time = now
        if telemetry.get('rx_total') is not None:
            previous_rx, previous_tx = (telemetry['rx_total'], telemetry['tx_total'])
        try:
            serialized = json.dumps(telemetry, ensure_ascii=True)
            window.evaluate_js(f'window.updateTelemetry({serialized})')
        except Exception:
            break
        next_tick += TELEMETRY_INTERVAL
        if next_tick < time.perf_counter():
            next_tick = time.perf_counter() + TELEMETRY_INTERVAL
        stop_event.wait(max(0, next_tick - time.perf_counter()))

def main() -> None:
    print('[SYSTEM] Starting Ambient Field Workbench.')
    print('[SYSTEM] Reading live local telemetry; network POSTs require a button press.')
    main_window = webview.create_window('Ambient Field Workbench', html=HTML_LAYOUT, width=1360, height=900, min_size=(760, 620), js_api=ENGINE)
    ENGINE.attach_window(main_window)
    stop_event = threading.Event()
    telemetry_thread = threading.Thread(target=telemetry_broadcast_loop, args=(main_window, stop_event), name='ambient-field-telemetry', daemon=True)
    audio_thread = threading.Thread(target=audio_broadcast_loop, args=(main_window, stop_event), name='ambient-field-audio', daemon=True)
    workers_started = threading.Event()

    def start_workers() -> None:
        if not workers_started.is_set() and (not stop_event.is_set()):
            workers_started.set()
            telemetry_thread.start()
            audio_thread.start()
    main_window.events.loaded += start_workers
    main_window.events.closed += stop_event.set
    try:
        webview.start()
    finally:
        stop_event.set()
        if telemetry_thread.ident is not None:
            telemetry_thread.join(timeout=2)
        if audio_thread.ident is not None:
            audio_thread.join(timeout=2)
