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
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

try:
    import webview
except ImportError:
    print("[ERROR] pywebview is required. Install: python -m pip install pywebview")
    raise SystemExit(1)

try:
    import psutil
except ImportError:
    print("[ERROR] psutil is required for live host telemetry. Install: python -m pip install psutil")
    raise SystemExit(1)

TELEMETRY_INTERVAL = 1.0
MAX_PAYLOAD_BYTES = 16 * 1024
HTTP_TIMEOUT_SECONDS = 8

HTML_LAYOUT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ambient Field Workbench</title>
<style>
:root {
  color-scheme: dark;
  --bg: #070b12; --panel: rgba(14,22,34,.88); --line: rgba(136,173,204,.16);
  --muted: #8193a7; --text: #e5f0f6; --cyan: #70e1dc; --blue: #72aaff;
  --green: #82e6b4; --red: #ff898f;
  font-family: Inter, "Segoe UI", system-ui, sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; min-height: 100vh; color: var(--text);
  background: radial-gradient(ellipse at 18% 0%, #122638 0, transparent 38%),
  radial-gradient(ellipse at 100% 80%, #101e32 0, transparent 34%), var(--bg); }
button, input, textarea { font: inherit; }
.app { min-height: 100vh; padding: 22px; display: flex; flex-direction: column; gap: 16px; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.brand { display: flex; align-items: center; gap: 13px; min-width: 0; }
.brand-mark { width: 40px; height: 40px; display: grid; place-items: center; flex: 0 0 auto;
  border: 1px solid rgba(112,225,220,.42); border-radius: 13px; color: var(--cyan);
  background: linear-gradient(145deg, rgba(112,225,220,.17), rgba(114,170,255,.06)); box-shadow: 0 0 24px rgba(112,225,220,.10); }
.brand-mark svg { width: 23px; height: 23px; }
.eyebrow { color: var(--cyan); text-transform: uppercase; letter-spacing: .19em; font-size: 10px; font-weight: 700; }
h1 { margin: 3px 0 0; font-size: clamp(18px, 2vw, 23px); letter-spacing: -.025em; font-weight: 650; }
.link-badge { display: inline-flex; align-items: center; gap: 9px; border: 1px solid var(--line); border-radius: 999px;
  padding: 9px 13px; color: #b7c8d7; background: rgba(10,17,27,.75); font-size: 11px; white-space: nowrap; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 12px currentColor; }
.link-badge[data-state="ok"] .dot { background: var(--green); }
.link-badge[data-state="error"] .dot { background: var(--red); }
.layout { flex: 1; min-height: 620px; display: grid; grid-template-columns: minmax(0,1.32fr) minmax(360px,.88fr);
  grid-template-rows: minmax(340px,1fr) 178px; gap: 16px; }
.panel { min-width: 0; border: 1px solid var(--line); border-radius: 16px; overflow: hidden;
  background: linear-gradient(145deg, rgba(16,26,40,.92), rgba(8,14,23,.94)); box-shadow: 0 18px 48px rgba(0,0,0,.19); }
.field-panel { display: flex; flex-direction: column; position: relative; }
.panel-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 17px 19px 13px; border-bottom: 1px solid var(--line); }
.panel-title { font-size: 12px; font-weight: 650; }
.panel-subtitle { margin-top: 4px; color: var(--muted); font-size: 10px; }
.chip { border: 1px solid rgba(112,225,220,.23); border-radius: 999px; padding: 6px 9px; color: var(--cyan); font-size: 9px; letter-spacing: .12em; text-transform: uppercase; white-space: nowrap; }
.canvas-wrap { flex: 1; min-height: 245px; position: relative; }
#fieldCanvas { width: 100%; height: 100%; display: block; }
.field-caption { position: absolute; left: 20px; bottom: 15px; color: #7891a4; font-size: 10px; letter-spacing: .04em; }
.field-legend { position: absolute; top: 16px; right: 18px; display: flex; gap: 13px; color: #8ba0b1; font-size: 9px; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--cyan); }
.legend-dot.blue { background: var(--blue); }
.instrument-row { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 9px; padding: 0 16px 16px; }
.metric { min-width: 0; border: 1px solid rgba(136,173,204,.12); border-radius: 11px; padding: 11px 12px; background: rgba(5,11,19,.46); }
.metric-label { display: flex; justify-content: space-between; gap: 5px; color: var(--muted); font-size: 9px; text-transform: uppercase; letter-spacing: .12em; }
.metric-value { margin-top: 7px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18px; font-variant-numeric: tabular-nums; }
.metric-detail { margin-top: 4px; min-height: 12px; color: #8296a7; font-size: 9px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.controls { display: flex; flex-direction: column; }
.controls-body { padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 13px; }
.field-group { display: flex; flex-direction: column; gap: 7px; }
.label-row { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
label { color: #a8bac8; font-size: 10px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
.micro { color: #71869a; font-size: 9px; }
input[type="url"], textarea { width: 100%; border: 1px solid rgba(136,173,204,.21); border-radius: 9px; outline: none;
  color: #deebf2; background: rgba(3,8,14,.62); padding: 10px 11px; font-size: 11px; transition: border-color .16s, box-shadow .16s; }
textarea { min-height: 83px; resize: vertical; line-height: 1.5; }
input[type="url"]:focus, textarea:focus { border-color: rgba(112,225,220,.63); box-shadow: 0 0 0 3px rgba(112,225,220,.08); }
input::placeholder, textarea::placeholder { color: #536779; }
.tuner { display: flex; align-items: center; gap: 11px; }
input[type="range"] { flex: 1; accent-color: var(--cyan); }
.tuner-value { width: 42px; color: var(--cyan); text-align: right; font-size: 12px; font-variant-numeric: tabular-nums; }
.actions { display: grid; grid-template-columns: 1fr 1.35fr; gap: 9px; margin-top: 2px; }
button { min-height: 38px; border-radius: 9px; cursor: pointer; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; transition: transform .15s, background .15s, border-color .15s; }
button:hover { transform: translateY(-1px); }
button:disabled { opacity: .55; cursor: wait; transform: none; }
.secondary { border: 1px solid rgba(136,173,204,.22); background: rgba(18,30,43,.8); color: #bad0dd; }
.primary { border: 1px solid rgba(112,225,220,.48); background: linear-gradient(110deg, rgba(49,154,155,.34), rgba(69,115,175,.28)); color: #b5ffef; box-shadow: inset 0 1px rgba(255,255,255,.07); }
.primary:hover { background: linear-gradient(110deg, rgba(49,154,155,.5), rgba(69,115,175,.4)); }
.disclosure { color: #71879a; font-size: 9px; line-height: 1.5; }
.status-line { min-height: 28px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--line); padding: 9px 16px; color: #8ca0b1; font-size: 10px; }
.status-line[data-kind="ok"] { color: var(--green); }
.status-line[data-kind="error"] { color: var(--red); }
.activity { grid-column: 1 / -1; display: flex; flex-direction: column; }
.activity-body { flex: 1; overflow: auto; padding: 10px 16px 13px; }
.event-list { display: flex; flex-direction: column; gap: 7px; }
.event { display: grid; grid-template-columns: 72px 69px minmax(0,1fr); gap: 9px; align-items: baseline; color: #9aafbd; font-size: 10px; line-height: 1.45; }
.event-time { color: #627a8e; font-variant-numeric: tabular-nums; }
.event-tag { color: var(--cyan); text-transform: uppercase; letter-spacing: .08em; font-size: 9px; }
.event-tag.error { color: var(--red); }
.event-message { overflow-wrap: anywhere; }
.footer { display: flex; justify-content: space-between; gap: 12px; color: #677d90; font-size: 9px; }
@media (max-width: 900px) { .app { padding: 14px; } .layout { grid-template-columns: minmax(0,1fr); grid-template-rows: 390px auto 170px; min-height: 0; } .activity { grid-column: 1; } .controls { min-height: 410px; } }
@media (max-width: 540px) { .topbar { align-items: flex-start; } .link-badge { padding: 8px; font-size: 9px; } .layout { grid-template-rows: 375px auto 160px; } .instrument-row { grid-template-columns: repeat(2,minmax(0,1fr)); } .controls { min-height: 440px; } .footer { flex-direction: column; } .event { grid-template-columns: 54px 57px minmax(0,1fr); } }
</style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand"><div class="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M3 12h3l2.1-6 4.1 12 2.2-7 1.2 3H21" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity=".35"/></svg></div>
      <div><div class="eyebrow">Ambient Field Workbench</div><h1>Host telemetry &amp; message transport</h1></div></div>
    <div id="linkBadge" class="link-badge" data-state="idle"><span class="dot"></span><span id="linkBadgeText">NETWORK READY · SEND MANUALLY</span></div>
  </header>
  <main class="layout">
    <section class="panel field-panel">
      <div class="panel-head"><div><div class="panel-title">Live system field</div><div class="panel-subtitle">Animated from local CPU and interface telemetry</div></div><div class="chip">Local metrics · 1 s</div></div>
      <div class="canvas-wrap" id="canvasWrap"><canvas id="fieldCanvas"></canvas>
        <div class="field-legend"><span class="legend-item"><i class="legend-dot"></i>CPU</span><span class="legend-item"><i class="legend-dot blue"></i>Network I/O</span></div>
        <div class="field-caption">VISUAL REFERENCE · 7.83 Hz IS NOT AN RF TRANSMISSION</div>
      </div>
      <div class="instrument-row">
        <div class="metric"><div class="metric-label"><span>CPU load</span><span>HOST</span></div><div class="metric-value" id="cpuValue">—</div><div class="metric-detail" id="cpuDetail">Waiting for sample</div></div>
        <div class="metric"><div class="metric-label"><span>Memory</span><span>HOST</span></div><div class="metric-value" id="memoryValue">—</div><div class="metric-detail" id="memoryDetail">Waiting for sample</div></div>
        <div class="metric"><div class="metric-label"><span>Download</span><span>INTERFACES</span></div><div class="metric-value" id="rxValue">—</div><div class="metric-detail" id="rxDetail">Waiting for sample</div></div>
        <div class="metric"><div class="metric-label"><span>Upload</span><span>INTERFACES</span></div><div class="metric-value" id="txValue">—</div><div class="metric-detail" id="txDetail">Waiting for sample</div></div>
      </div>
    </section>
    <section class="panel controls">
      <div class="panel-head"><div><div class="panel-title">Send a JSON message</div><div class="panel-subtitle">One request, only when you press Send</div></div><div class="chip">HTTPS</div></div>
      <div class="controls-body">
        <div class="field-group"><div class="label-row"><label for="endpointInput">Destination URL</label><span class="micro">No default destination</span></div><input type="url" id="endpointInput" placeholder="https://your-service.example/api/ingest" autocomplete="url" spellcheck="false"></div>
        <div class="field-group"><div class="label-row"><label for="payloadInput">Message payload</label><span class="micro">Up to 16 KB</span></div><textarea id="payloadInput" maxlength="16384" placeholder="Enter the text you want to send…">Ambient field status request</textarea></div>
        <div class="field-group"><div class="label-row"><label for="tunerInput">Tuning factor</label><span class="micro">Sent as JSON metadata · 0.1–10</span></div><div class="tuner"><input type="range" min="0.1" max="10" step="0.1" value="1" id="tunerInput"><span class="tuner-value" id="tunerValue">1.0×</span></div></div>
        <div class="actions"><button class="secondary" id="previewButton" type="button">Preview locally</button><button class="primary" id="sendButton" type="button">Send once</button></div>
        <div class="disclosure">The request contains your message, tuning factor, SHA-256 digest, and send time. HTTPS is required. HTTP is allowed only for localhost. Redirects are not followed.</div>
      </div>
      <div class="status-line" id="sendStatus" data-kind="idle"><span class="dot"></span><span id="sendStatusText">No request sent this session.</span></div>
    </section>
    <section class="panel activity">
      <div class="panel-head"><div><div class="panel-title">Activity ledger</div><div class="panel-subtitle" id="hostDetail">Waiting for local machine details…</div></div><div class="chip" id="sampleTime">Waiting for telemetry</div></div>
      <div class="activity-body"><div class="event-list" id="eventList" aria-live="polite"></div></div>
    </section>
  </main>
  <footer class="footer"><span>Telemetry is read from this computer with psutil. Nothing is transmitted automatically.</span><span>Payload preview computes size and digest locally.</span></footer>
</div>
<script>
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
      const waveHeight = 5 + cpu * .18;
      ctx.beginPath();
      for (let x = 0; x <= w; x += 3) {
        const y = cy + Math.sin(x * .018 - fieldTime * (1 + io * .04)) * waveHeight + Math.sin(x * .006 + fieldTime * .7) * 4;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(112,225,220,.24)'; ctx.lineWidth = 1; ctx.stroke();
      const positions = particles.map(p => {
        p.angle += p.drift * (1 + io * .08) * (dt * 60);
        return {x: cx + Math.cos(p.angle) * base * (1 + .12 * Math.sin(fieldTime + p.phase)), y: cy + Math.sin(p.angle) * base * .67 * (1 + .12 * Math.cos(fieldTime * .8 + p.phase)), p};
      });
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
      ctx.textAlign = 'center'; ctx.fillStyle = '#d2e8ed'; ctx.font = '600 10px Segoe UI, sans-serif'; ctx.fillText('AMBIENT FIELD', cx, cy - 3);
      ctx.fillStyle = '#7896a8'; ctx.font = '9px Segoe UI, sans-serif'; ctx.fillText(`CPU ${cpu.toFixed(1)}% · I/O ${formatRate(metrics.rx_rate + metrics.tx_rate)}`, cx, cy + 13);
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();
</script>
</body>
</html>
"""


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
        self._last_send: dict[str, Any] = {"status": "idle"}
        self._payload_buffer = bytearray(MAX_PAYLOAD_BYTES)

    def attach_window(self, window: Any) -> None:
        self._window = window

    def _prepare_payload(self, payload: Any, tuning_factor: Any) -> tuple[dict[str, Any] | None, str | None]:
        if not isinstance(payload, str) or not payload.strip():
            return None, "Enter a message before previewing or sending."
        encoded = payload.encode("utf-8")
        if len(encoded) > MAX_PAYLOAD_BYTES:
            return None, f"The UTF-8 payload exceeds the {MAX_PAYLOAD_BYTES:,}-byte limit."
        try:
            factor = float(tuning_factor)
        except (TypeError, ValueError):
            return None, "Tuning factor must be a number from 0.1 to 10.0."
        if not math.isfinite(factor) or not 0.1 <= factor <= 10.0:
            return None, "Tuning factor must be between 0.1 and 10.0."
        digest = hashlib.sha256(encoded).hexdigest()
        with self._lock:
            self._payload_buffer[:] = b"\0" * len(self._payload_buffer)
            self._payload_buffer[:len(encoded)] = encoded
        return {"payload": payload, "payload_bytes": len(encoded), "tuning_factor": factor, "sha256": digest}, None

    def preview_payload(self, payload: str, tuning_factor: float) -> dict[str, Any]:
        prepared, error = self._prepare_payload(payload, tuning_factor)
        if error:
            return {"ok": False, "message": error}
        assert prepared is not None
        return {"ok": True, "bytes": prepared["payload_bytes"], "sha256": prepared["sha256"],
                "message": "Payload previewed locally; nothing was transmitted."}

    @staticmethod
    def _validate_endpoint(endpoint: str) -> tuple[str | None, str | None]:
        if not isinstance(endpoint, str) or not endpoint.strip():
            return None, "Enter the HTTPS endpoint that should receive this message."
        try:
            parsed = urllib.parse.urlsplit(endpoint.strip())
            hostname = parsed.hostname
        except ValueError:
            return None, "The destination URL is not valid."
        if not parsed.scheme or not hostname or parsed.username or parsed.password or parsed.fragment:
            return None, "Enter a complete URL without credentials or a fragment."
        scheme = parsed.scheme.lower()
        if scheme == "https" or (scheme == "http" and hostname.lower() in {"localhost", "127.0.0.1", "::1"}):
            return endpoint.strip(), None
        return None, "Use HTTPS. HTTP is allowed only for localhost, 127.0.0.1, or ::1."

    def transmit_payload(self, payload: str, tuning_factor: float, endpoint: str) -> dict[str, Any]:
        prepared, error = self._prepare_payload(payload, tuning_factor)
        if error:
            return {"ok": False, "message": error}
        valid_endpoint, error = self._validate_endpoint(endpoint)
        if error:
            return {"ok": False, "message": error}
        assert prepared is not None and valid_endpoint is not None
        with self._lock:
            if self._send_in_progress:
                return {"ok": False, "message": "A request is already in progress; wait for its response."}
            self._send_in_progress = True
            self._last_send = {"status": "sending", "sha256": prepared["sha256"]}

        body = json.dumps({
            "payload": prepared["payload"],
            "tuning_factor": prepared["tuning_factor"],
            "sha256": prepared["sha256"],
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False).encode("utf-8")
        try:
            worker = threading.Thread(
                target=self._send_request,
                args=(valid_endpoint, body, prepared["sha256"]),
                name="ambient-field-http-send",
                daemon=True,
            )
            worker.start()
        except Exception as exc:
            with self._lock:
                self._send_in_progress = False
            return {"ok": False, "message": f"Could not start the network request: {exc}"}
        host = urllib.parse.urlsplit(valid_endpoint).hostname or "destination"
        return {"ok": True, "status": "sending", "host": host, "sha256": prepared["sha256"]}

    def _send_request(self, endpoint: str, body: bytes, digest: str) -> None:
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8", "Accept": "application/json, text/plain, */*"},
            method="POST",
        )
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                response.read(2048)
                status = int(response.status)
                result = {"ok": 200 <= status < 300,
                          "message": f"HTTP {status} · {urllib.parse.urlsplit(endpoint).hostname}",
                          "sha256": digest}
        except urllib.error.HTTPError as exc:
            result = {"ok": False, "message": f"HTTP {exc.code} · {urllib.parse.urlsplit(endpoint).hostname}", "sha256": digest}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            result = {"ok": False, "message": f"Request failed: {str(reason)[:220]}", "sha256": digest}
        except Exception as exc:
            result = {"ok": False, "message": f"Request failed: {str(exc)[:220]}", "sha256": digest}

        with self._lock:
            self._send_in_progress = False
            self._last_send = {"status": "ok" if result["ok"] else "error", **result}
            window = self._window
        if window is not None:
            try:
                payload_json = json.dumps(result, ensure_ascii=True)
                window.evaluate_js(f"window.setTransmissionResult({payload_json})")
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
            rx_total = sum(int(pernic[name].bytes_recv) for name in active_names)
            tx_total = sum(int(pernic[name].bytes_sent) for name in active_names)
            elapsed = max(elapsed, 0.001)
            rx_rate = 0.0 if previous_rx is None else max(0.0, (rx_total - previous_rx) / elapsed)
            tx_rate = 0.0 if previous_tx is None else max(0.0, (tx_total - previous_tx) / elapsed)
            with self._lock:
                send_state = self._last_send.copy()
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": float(memory.percent),
                "memory_used": int(memory.used), "memory_total": int(memory.total),
                "process_rss": process_rss,
                "rx_total": rx_total, "tx_total": tx_total, "rx_rate": rx_rate, "tx_rate": tx_rate,
                "active_interfaces": len(active_names), "interface_names": active_names[:6],
                "hostname": platform.node() or "This computer",
                "platform": f"{platform.system()} {platform.release()}",
                "sampled_at": sampled, "last_send": send_state,
            }
        except Exception as exc:
            return {
                "cpu_percent": None, "memory_percent": None, "memory_used": None, "memory_total": None,
                "process_rss": None, "rx_total": None, "tx_total": None, "rx_rate": None, "tx_rate": None,
                "active_interfaces": 0, "interface_names": [],
                "hostname": platform.node() or "This computer",
                "platform": f"{platform.system()} {platform.release()}",
                "sampled_at": sampled, "telemetry_error": str(exc)[:180],
            }


ENGINE = AmbientFieldEngine()


def telemetry_broadcast_loop(window: Any, stop_event: threading.Event) -> None:
    """Send real local telemetry to the UI once per second."""
    stop_event.wait(1.0)
    previous_rx: int | None = None
    previous_tx: int | None = None
    previous_time = time.perf_counter()
    next_tick = previous_time
    while not stop_event.is_set():
        now = time.perf_counter()
        elapsed = max(now - previous_time, 0.001)
        telemetry = ENGINE.live_telemetry(elapsed, previous_rx, previous_tx)
        previous_time = now
        if telemetry.get("rx_total") is not None:
            previous_rx, previous_tx = telemetry["rx_total"], telemetry["tx_total"]
        try:
            serialized = json.dumps(telemetry, ensure_ascii=True)
            window.evaluate_js(f"window.updateTelemetry({serialized})")
        except Exception:
            break
        next_tick += TELEMETRY_INTERVAL
        if next_tick < time.perf_counter():
            next_tick = time.perf_counter() + TELEMETRY_INTERVAL
        stop_event.wait(max(0, next_tick - time.perf_counter()))


def main() -> None:
    print("[SYSTEM] Starting Ambient Field Workbench.")
    print("[SYSTEM] Reading live local telemetry; network POSTs require a button press.")
    main_window = webview.create_window(
        "Ambient Field Workbench", html=HTML_LAYOUT, width=1360, height=900,
        min_size=(760, 620), js_api=ENGINE,
    )
    ENGINE.attach_window(main_window)
    stop_event = threading.Event()
    telemetry_thread = threading.Thread(
        target=telemetry_broadcast_loop,
        args=(main_window, stop_event),
        name="ambient-field-telemetry", daemon=True,
    )
    telemetry_thread.start()
    try:
        webview.start()
    finally:
        stop_event.set()
        telemetry_thread.join(timeout=2)


if __name__ == "__main__":
    main()
