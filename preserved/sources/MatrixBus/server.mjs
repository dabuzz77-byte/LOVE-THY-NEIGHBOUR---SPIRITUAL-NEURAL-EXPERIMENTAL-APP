import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { createInterface } from 'node:readline';
import { processMetrics, rate } from './metrics.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.MATRIX_PORT || 4317);
const HOST = '127.0.0.1';
const ORIGIN = `http://${HOST}:${PORT}`;
const TOKEN = randomBytes(32).toString('hex');
const powershell = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
const cores = os.cpus().length || 1;
const streams = new Set();
const jobs = new Map();
const history = [];
let sampler, restartTimer, prior, latest = null, lastSample = 0, stopping = false, sequence = 0;
let collectorError = null;
let cpuPrevious = os.cpus();
let systemCpu = 0;

function cpuSample() {
  const now = os.cpus();
  let idle = 0, total = 0;
  now.forEach((cpu, i) => {
    const old = cpuPrevious[i];
    if (!old) return;
    idle += cpu.times.idle - old.times.idle;
    for (const key of Object.keys(cpu.times)) total += cpu.times[key] - old.times[key];
  });
  cpuPrevious = now;
  systemCpu = total > 0 ? Math.max(0, Math.min(100, 100 * (1 - idle / total))) : 0;
}
const cpuTimer = setInterval(cpuSample, 1000);

function send(res, event, payload) {
  if (!res.destroyed && res.writableLength < 1024 * 1024) res.write(`event: ${event}\ndata: ${JSON.stringify(payload)}\n\n`);
  else { res.destroy(); streams.delete(res); }
}
function broadcast(event, payload) { for (const res of streams) send(res, event, payload); }
function event(kind, message) {
  const item = { id: ++sequence, at: Date.now(), kind, message };
  history.push(item); if (history.length > 80) history.shift();
  broadcast('activity', item);
}
function acceptSample(sample) {
  if (!Array.isArray(sample.processes) || !Number.isFinite(sample.timestamp)) return;
  const processes = processMetrics(sample, prior, cores);
  const seconds = prior ? (sample.timestamp - prior.timestamp) / 1000 : 0;
  const oldPids = new Map((prior?.processes || []).map(p => [p.pid, p]));
  const newPids = new Set(processes.map(p => p.pid));
  for (const p of processes) if (!oldPids.has(p.pid) || oldPids.get(p.pid).started !== p.started) event(p.runtime, `${p.label} connected · PID ${p.pid}`);
  for (const p of oldPids.values()) if (!newPids.has(p.pid)) event('exit', `${p.label} disconnected · PID ${p.pid}`);
  const memoryTotal = os.totalmem();
  const sum = field => processes.some(p=>p[field]===null) ? null : processes.reduce((n,p)=>n+(p[field]||0),0);
  latest = {
    timestamp: sample.timestamp, processes, warnings: sample.warnings || [],
    system: { cpu: systemCpu, cores, cpuModel: os.cpus()[0]?.model || 'Processor',
      memoryTotal, memoryUsed: memoryTotal - os.freemem(), uptime: os.uptime(),
      hostname: os.hostname(), platform: `Windows ${os.release()}`, totalProcesses: sample.totalProcesses,
      networkRx: sample.net?.available && prior?.net?.available ? rate(sample.net.received, prior.net.received, seconds) : null,
      networkTx: sample.net?.available && prior?.net?.available ? rate(sample.net.sent, prior.net.sent, seconds) : null,
      disk: sample.disk },
    totals: { cpu: sum('cpu'), memory: sum('memoryBytes'), io: sum('ioRate'),
      python: processes.filter(p=>p.runtime==='python').length, java: processes.filter(p=>p.runtime==='java').length }
  };
  prior = sample; lastSample = Date.now(); collectorError = null;
  broadcast('snapshot', latest);
}
function startSampler() {
  if (stopping) return;
  sampler = spawn(powershell, ['-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',path.join(ROOT,'sampler.ps1')], { windowsHide:true, cwd:ROOT, stdio:['ignore','pipe','pipe'] });
  createInterface({input:sampler.stdout}).on('line', line => {
    try { acceptSample(JSON.parse(line.replace(/^\uFEFF/,''))); } catch { /* Ignore incomplete diagnostic output. */ }
  });
  let errorText = '';
  sampler.stderr.on('data', data => { errorText = (errorText + data).slice(-3000); });
  sampler.on('error', error => { collectorError = error.message; });
  sampler.on('close', () => {
    if (stopping) return;
    collectorError ||= errorText || 'Collector stopped. Reconnecting…';
    broadcast('status', {connected:false, message:collectorError});
    prior = null;
    restartTimer = setTimeout(startSampler, 3000);
  });
}

function json(res, code, body) { res.writeHead(code, {'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify(body)); }
async function body(req) {
  let size = 0, chunks = [];
  for await (const chunk of req) { size += chunk.length; if (size > 16384) throw new Error('Request too large'); chunks.push(chunk); }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}
function validToken(req) {
  const value = req.headers['x-matrix-token'];
  return typeof value === 'string' && value.length === TOKEN.length && timingSafeEqual(Buffer.from(value), Buffer.from(TOKEN));
}
function killTree(child) {
  if (!child?.pid || child.exitCode !== null) return;
  const killer = spawn('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], {windowsHide:true, stdio:'ignore'});
  killer.on('error', () => child.kill());
  killer.on('close', code => { if (code !== 0 && child.exitCode === null) child.kill(); });
}
function runCommand(command) {
  const id = randomUUID();
  // stdin is closed: this is a command runner, not an interactive console or PTY.
  const script = `[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n$ErrorActionPreference = 'Stop'\ntry {\n${command}\nif (-not $?) { exit 1 }; if ($null -ne $LASTEXITCODE) { exit $LASTEXITCODE }\n} catch { [Console]::Error.WriteLine($_.ToString()); exit 1 }`;
  const encoded = Buffer.from(script, 'utf16le').toString('base64');
  const child = spawn(powershell, ['-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',encoded], {cwd:ROOT,windowsHide:true,stdio:['ignore','pipe','pipe']});
  const job = {id, child, command, bytes:0};
  jobs.set(id, job);
  broadcast('command', {id, state:'start', command});
  for (const [stream, type] of [[child.stdout,'stdout'],[child.stderr,'stderr']]) {
    stream.setEncoding('utf8');
    stream.on('data', chunk => {
      job.bytes += Buffer.byteLength(chunk);
      if (job.bytes > 1024*1024) { broadcast('command', {id,state:'output',type:'stderr',text:'\nOutput limit reached; stopping command.\n'}); killTree(child); return; }
      broadcast('command', {id,state:'output',type,text:chunk});
    });
  }
  const timeout = setTimeout(() => { broadcast('command',{id,state:'output',type:'stderr',text:'\nTwo-minute limit reached; stopping command.\n'}); killTree(child); },120000);
  child.on('error', error => broadcast('command',{id,state:'output',type:'stderr',text:error.message}));
  child.on('close', code => { clearTimeout(timeout); jobs.delete(id); broadcast('command',{id,state:'end',code}); });
  return id;
}

const staticFiles = new Map([['/','index.html'],['/app.js','app.js'],['/styles.css','styles.css'],['/icon.svg','icon.svg']]);
const server = http.createServer(async (req, res) => {
  res.setHeader('Cache-Control','no-store');
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('X-Frame-Options','DENY');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
  // Loopback binding + exact Host/Origin checks prevent remote websites and DNS rebinding.
  if (req.headers.host !== `${HOST}:${PORT}`) return json(res,403,{error:'Use the local Matrix Bus URL.'});
  if (req.headers.origin && req.headers.origin !== ORIGIN) return json(res,403,{error:'Origin rejected.'});
  if (req.headers['sec-fetch-site'] && !['same-origin','none'].includes(req.headers['sec-fetch-site'])) return json(res,403,{error:'Cross-site request rejected.'});
  const url = new URL(req.url, ORIGIN);
  try {
    if (req.method === 'GET' && url.pathname === '/api/session') return json(res,200,{token:TOKEN,cwd:ROOT,shell:'Windows PowerShell',commandsTimeout:120});
    if (req.method === 'GET' && url.pathname === '/api/snapshot') return json(res,200,{snapshot:latest,connected:Date.now()-lastSample<5000,error:collectorError});
    if (req.method === 'GET' && url.pathname === '/api/events') {
      res.writeHead(200,{'Content-Type':'text/event-stream','Connection':'keep-alive'});
      res.write('retry: 2000\n\n');
      streams.add(res);
      send(res,'session',{token:TOKEN,cwd:ROOT,shell:'Windows PowerShell',activeCommand:[...jobs.values()].map(j=>({id:j.id,command:j.command}))[0]||null});
      if (latest) send(res,'snapshot',latest);
      send(res,'history',history);
      send(res,'status',{connected:Date.now()-lastSample<5000,message:collectorError});
      req.on('close',()=>streams.delete(res));
      return;
    }
    if (req.method === 'POST' && url.pathname.startsWith('/api/')) {
      if (!validToken(req) || req.headers.origin !== ORIGIN || !req.headers['content-type']?.startsWith('application/json')) return json(res,403,{error:'Invalid local session.'});
      const data = await body(req);
      if (url.pathname === '/api/command') {
        if (typeof data.command !== 'string' || !data.command.trim() || data.command.length>8000) return json(res,400,{error:'Enter a command (maximum 8,000 characters).'});
        if (jobs.size) return json(res,409,{error:'A command is already running. Stop it before starting another.'});
        return json(res,202,{id:runCommand(data.command.trim())});
      }
      if (url.pathname === '/api/cancel') {
        const job = jobs.get(data.id); if (!job) return json(res,404,{error:'Command has already finished.'});
        killTree(job.child); return json(res,200,{ok:true});
      }
      if (url.pathname === '/api/shutdown') { json(res,200,{ok:true}); setTimeout(shutdown,100); return; }
    }
    if (req.method === 'GET' && staticFiles.has(url.pathname)) {
      const file = staticFiles.get(url.pathname);
      const content = await readFile(path.join(ROOT,'public',file));
      const mime = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml'};
      res.writeHead(200,{'Content-Type':`${mime[path.extname(file)]}; charset=utf-8`}); return res.end(content);
    }
    json(res,404,{error:'Not found'});
  } catch (error) { json(res,400,{error:error.message || 'Request failed'}); }
});

const heartbeat = setInterval(() => {
  broadcast('status',{connected:Date.now()-lastSample<5000,message:collectorError});
},3000);
function shutdown() {
  if (stopping) return; stopping=true;
  clearTimeout(restartTimer); clearInterval(heartbeat); clearInterval(cpuTimer);
  sampler?.kill();
  for (const job of jobs.values()) killTree(job.child);
  for (const res of streams) res.end();
  server.close(()=>process.exit(0)); setTimeout(()=>process.exit(0),1500).unref();
}
process.on('SIGINT',shutdown); process.on('SIGTERM',shutdown);
server.on('error', error => { console.error(error.code === 'EADDRINUSE' ? `Port ${PORT} is already in use. Open ${ORIGIN} or set MATRIX_PORT to another port.` : error.message); shutdown(); process.exitCode=1; });
server.listen(PORT,HOST,()=>{ console.log(`Matrix Bus is running at ${ORIGIN}`); startSampler(); });
