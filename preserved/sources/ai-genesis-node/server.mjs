import http from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { generate } from './providers.mjs';
import { scanProcesses } from './processes.mjs';

const root = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(root, 'data');
await mkdir(dataDir, { recursive: true });
const tokenPath = path.join(dataDir, 'connector-token');
const connectorToken = existsSync(tokenPath) ? (await readFile(tokenPath, 'utf8')).trim() : randomBytes(32).toString('hex');
await writeFile(tokenPath, connectorToken, { mode: 0o600 });
const uiToken = randomBytes(32).toString('hex');
const port = Number(process.env.GENESIS_PORT || 7860);
let preferences = {};
try { preferences = JSON.parse(await readFile(path.join(dataDir, 'settings.json'), 'utf8')); } catch {}
const config = { llamaModel: preferences.llamaModel || 'llama3', geminiModel: preferences.geminiModel || 'gemini-3.8-flash', openaiModel: preferences.openaiModel || 'gpt-6-astra', openaiKey: process.env.OPENAI_API_KEY || '', geminiKey: process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || '' };
const programs = new Map();
const pendingMessages = new Map();
let generationActive = false;

const equal = (a, b) => typeof a === 'string' && a.length === b.length && timingSafeEqual(Buffer.from(a), Buffer.from(b));
function send(res, status, value, contentType = 'application/json; charset=utf-8') {
  if (res.destroyed || res.writableEnded) return;
  res.writeHead(status, { 'Content-Type': contentType, 'Cache-Control': 'no-store' });
  res.end(contentType.startsWith('application/json') ? JSON.stringify(value) : value);
}
async function body(req, max = 100000) {
  const chunks = []; let size = 0;
  for await (const chunk of req) { size += chunk.length; if (size > max) throw Object.assign(new Error('Message is too large.'), { status: 413 }); chunks.push(chunk); }
  return Buffer.concat(chunks).toString('utf8');
}
async function json(req) { try { return JSON.parse(await body(req)); } catch (e) { if (e.status) throw e; throw Object.assign(new Error('Invalid JSON.'), { status: 400 }); } }
function publicSettings() { return { llamaModel: config.llamaModel, geminiModel: config.geminiModel, openaiModel: config.openaiModel, openaiConfigured: !!config.openaiKey, geminiConfigured: !!config.geminiKey }; }
async function modelStatus() {
  try {
    const response = await fetch('http://127.0.0.1:11434/api/tags', { signal: AbortSignal.timeout(3000) });
    if (!response.ok) throw new Error();
    const data = await response.json();
    const models = (data.models || []).map(m => m.name);
    const target = config.llamaModel.includes(':') ? config.llamaModel : `${config.llamaModel}:latest`;
    return { running: true, ready: models.includes(target) || models.includes(config.llamaModel), models };
  } catch { return { running: false, ready: false, models: [] }; }
}
function connections() {
  const now = Date.now();
  return [...programs.values()].map(p => ({ id: p.id, name: p.name, language: p.language, pid: p.pid, lastSeen: p.lastSeen, connected: now - p.lastSeen < 15000 }));
}

const server = http.createServer(async (req, res) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
  const allowedHosts = [`127.0.0.1:${port}`, `localhost:${port}`];
  if (!allowedHosts.includes(req.headers.host)) return send(res, 403, { error: 'Invalid host.' });
  if (req.headers.origin && !allowedHosts.map(h => `http://${h}`).includes(req.headers.origin)) return send(res, 403, { error: 'Cross-origin access is disabled.' });
  if (req.headers['sec-fetch-site'] && !['same-origin', 'none'].includes(req.headers['sec-fetch-site'])) return send(res, 403, { error: 'Open Genesis directly on this computer.' });
  const url = new URL(req.url, `http://127.0.0.1:${port}`);
  try {
    if (url.pathname === '/api/session' && req.method === 'GET') {
      // Reject cross-site requests before issuing the local UI session token.
      return send(res, 200, { token: uiToken, name: 'AI Genesis Node' });
    }
    if (url.pathname.startsWith('/api/')) {
      const supplied = (req.headers.authorization || '').replace(/^Bearer /, '');
      const bridge = url.pathname.startsWith('/api/bridge/');
      if (!equal(supplied, bridge ? connectorToken : uiToken)) return send(res, 401, { error: 'Connection expired. Refresh the app or check the connector token.' });
      if (req.method === 'POST' && !bridge && !String(req.headers['content-type']).startsWith('application/json')) return send(res, 415, { error: 'Use JSON.' });
      if (url.pathname === '/api/status' && req.method === 'GET') {
        const [ollama, scan] = await Promise.all([modelStatus(), scanProcesses()]);
        return send(res, 200, { active: true, settings: publicSettings(), ollama, ...scan, connections: connections() });
      }
      if (url.pathname === '/api/shutdown' && req.method === 'POST') {
        send(res, 200, { ok: true });
        server.close();
        setTimeout(() => process.exit(0), 200).unref();
        return;
      }
      if (url.pathname === '/api/settings' && req.method === 'POST') {
        const input = await json(req);
        const updated = { ...config };
        for (const key of ['llamaModel', 'geminiModel', 'openaiModel']) {
          if (input[key] !== undefined) {
            if (typeof input[key] !== 'string' || !/^[a-zA-Z0-9_.:/-]{1,100}$/.test(input[key])) throw new Error('Enter a valid model name.');
            updated[key] = input[key];
          }
        }
        for (const key of ['openaiKey', 'geminiKey']) {
          if (input[key] !== undefined && (typeof input[key] !== 'string' || input[key].length > 500 || /\s/.test(input[key]))) throw new Error('Invalid API key.');
          if (input[key]) updated[key] = input[key];
          if (input[`clear_${key}`]) updated[key] = '';
        }
        const safe = { llamaModel: updated.llamaModel, geminiModel: updated.geminiModel, openaiModel: updated.openaiModel };
        await writeFile(path.join(dataDir, 'settings.json'), JSON.stringify(safe, null, 2));
        Object.assign(config, updated);
        return send(res, 200, publicSettings());
      }
      if (url.pathname === '/api/generate' && req.method === 'POST') {
        if (generationActive) return send(res, 409, { error: 'A generation is already running. Wait or cancel it.' });
        const input = await json(req);
        generationActive = true;
        const controller = new AbortController();
        res.once('close', () => { if (!res.writableEnded) controller.abort(); });
        try { const result = await generate(input, { ...config }, { signal: controller.signal }); return send(res, result.ok ? 200 : 502, result); }
        finally { generationActive = false; }
      }
      if (url.pathname === '/api/program/send' && req.method === 'POST') {
        const input = await json(req), program = programs.get(input.id);
        if (!program || Date.now() - program.lastSeen >= 15000) return send(res, 409, { error: 'Program is disconnected. Start its connector and retry.' });
        if (typeof input.text !== 'string' || !input.text.trim() || input.text.length > 24000) throw new Error('Enter a program message between 1 and 24,000 characters.');
        if (program.queue.length >= 5 || [...pendingMessages.values()].filter(p => p.programId === program.id).length >= 5) throw new Error('This program already has five pending messages.');
        const id = randomUUID();
        const result = await new Promise(resolve => {
          const timer = setTimeout(() => { pendingMessages.delete(id); program.queue = program.queue.filter(m => m.id !== id); resolve({ ok: false, error: 'The program did not reply within 60 seconds. Its work may still be running.' }); }, 60000);
          pendingMessages.set(id, { programId: program.id, resolve, timer });
          program.queue.push({ id, text: input.text });
        });
        return send(res, result.ok ? 200 : 504, result);
      }
      if (url.pathname === '/api/bridge/register' && req.method === 'POST') {
        const input = await json(req);
        if (!['python', 'java'].includes(input.language) || !Number.isInteger(input.pid) || input.pid < 1 || typeof input.name !== 'string' || !input.name.trim() || input.name.length > 100) throw new Error('Invalid program registration.');
        const old = [...programs.values()].find(p => p.pid === input.pid && p.language === input.language);
        if (!old && programs.size >= 500) throw new Error('Too many registered programs. Restart Genesis to clear inactive connections.');
        const id = old?.id || randomUUID();
        programs.set(id, { id, name: input.name, language: input.language, pid: input.pid, lastSeen: Date.now(), queue: old?.queue || [] });
        return send(res, 200, { id });
      }
      if (url.pathname === '/api/bridge/next' && req.method === 'GET') {
        const p = programs.get(url.searchParams.get('id'));
        if (!p) return send(res, 404, { error: 'Register again.' });
        p.lastSeen = Date.now();
        const item = p.queue.shift();
        if (!item) { res.writeHead(204); return res.end(); }
        res.setHeader('X-Genesis-Request-Id', item.id);
        return send(res, 200, item.text, 'text/plain; charset=utf-8');
      }
      if (url.pathname === '/api/bridge/reply' && req.method === 'POST') {
        const id = url.searchParams.get('request'), p = programs.get(url.searchParams.get('id')), item = pendingMessages.get(id);
        if (!p || !item || item.programId !== p.id) return send(res, 404, { error: 'Message is no longer pending.' });
        const output = await body(req);
        p.lastSeen = Date.now();
        clearTimeout(item.timer); pendingMessages.delete(id);
        item.resolve({ ok: true, output, name: p.name });
        return send(res, 200, { ok: true });
      }
      return send(res, 404, { error: 'Unknown endpoint.' });
    }
    if (req.method !== 'GET') return send(res, 405, { error: 'Method not allowed.' });
    const files = { '/': ['index.html', 'text/html; charset=utf-8'], '/app.js': ['app.js', 'text/javascript; charset=utf-8'], '/styles.css': ['styles.css', 'text/css; charset=utf-8'], '/favicon.svg': ['favicon.svg', 'image/svg+xml'] };
    const entry = files[url.pathname];
    if (!entry) return send(res, 404, 'Not found', 'text/plain');
    return send(res, 200, await readFile(path.join(root, 'public', entry[0])), entry[1]);
  } catch (error) { return send(res, error.status || 400, { error: error.message || 'Request failed.' }); }
});
server.requestTimeout = 400000;
server.on('error', error => { console.error(error.code === 'EADDRINUSE' ? `Port ${port} is in use. Open http://127.0.0.1:${port} or set GENESIS_PORT.` : error.message); process.exitCode = 1; });
server.listen(port, '127.0.0.1', () => console.log(`AI Genesis Node is running at http://127.0.0.1:${port}`));
