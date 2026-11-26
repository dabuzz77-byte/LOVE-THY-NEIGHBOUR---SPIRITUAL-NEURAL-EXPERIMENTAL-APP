const $ = id => document.getElementById(id);
let token, state, filter = 'all', refreshing = false, controller, ticker, selectedProgram, lastProgramOutput = '', toastTimer;
const names = { llama: 'Llama 3', gemini: 'Google Gemini', openai: 'OpenAI' };
async function api(path, data, signal) {
  const response = await fetch(path, { method: data === undefined ? 'GET' : 'POST', headers: { Authorization: `Bearer ${token}`, ...(data === undefined ? {} : { 'Content-Type': 'application/json' }) }, ...(data === undefined ? {} : { body: JSON.stringify(data) }), signal });
  const result = await response.json();
  if (!response.ok && !result.results) throw new Error(result.error || 'The request failed.');
  return result;
}
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 3500); }
function showError(message) { $('alert').textContent = message; $('alert').hidden = !message; }
async function refresh() {
  if (refreshing || !token) return;
  refreshing = true;
  try {
    state = await api('/api/status', undefined, AbortSignal.timeout(18000));
    $('node-status').textContent = 'Node active'; $('node-status').className = 'status online';
    $('active-formula').textContent = 'AI GENESIS NODE ACTIVE = TRUE = 1';
    $('llama-state').textContent = state.ollama.ready ? `${state.settings.llamaModel} · Ready` : state.ollama.running ? 'Model not installed' : 'Open Ollama to connect';
    $('llama-state').className = `provider-state ${state.ollama.ready ? 'ready' : ''}`;
    $('gemini-state').textContent = state.settings.geminiConfigured ? 'Key configured' : 'Add API key';
    $('openai-state').textContent = state.settings.openaiConfigured ? 'Key configured' : 'Add API key';
    for (const id of ['gemini', 'openai']) {
      $(`use-${id}`).disabled = !state.settings[`${id}Configured`] || !!controller;
      if (!state.settings[`${id}Configured`]) $(`use-${id}`).checked = false;
    }
    $('last-scan').textContent = new Date(state.checkedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    renderPrograms(); privacy();
  } catch (error) {
    $('node-status').textContent = 'Disconnected'; $('node-status').className = 'status offline';
    $('active-formula').textContent = 'AI GENESIS NODE ACTIVE = FALSE = 0';
    $('llama-state').textContent = 'Status unavailable';
    $('fusion-state').textContent = 'LOCAL CONTROLLER · DISCONNECTED';
    $('process-list').replaceChildren(Object.assign(document.createElement('div'), { className: 'empty-programs', textContent: 'Controller disconnected. Start AI Genesis Node and refresh this page.' }));
  } finally { refreshing = false; }
}
function renderPrograms() {
  const list = $('process-list'); list.replaceChildren();
  const connections = state.connections || [];
  const rows = state.processes.map(p => ({ ...p, bridge: connections.find(c => c.pid === p.pid && c.language === p.language && c.connected) }));
  for (const c of connections.filter(c => c.connected && !rows.some(p => p.pid === c.pid && p.language === c.language))) rows.push({ pid: c.pid, name: c.name, language: c.language, source: c.name, bridge: c });
  rows.sort((a, b) => Number(!!b.bridge) - Number(!!a.bridge) || a.pid - b.pid);
  $('process-count').textContent = rows.length;
  if (state.error) list.append(Object.assign(document.createElement('div'), { className: 'notice', textContent: state.error }));
  const shown = rows.filter(p => filter === 'all' || p.language === filter);
  if (!shown.length) list.append(Object.assign(document.createElement('div'), { className: 'empty-programs', textContent: `No ${filter === 'all' ? 'Python or Java' : filter === 'python' ? 'Python' : 'Java'} programs detected. Start a program to see it here.` }));
  for (const p of shown) {
    const row = document.createElement('button'); row.className = 'process-item';
    const icon = document.createElement('span'); icon.className = `language-badge ${p.language}`; icon.textContent = p.language === 'java' ? 'JV' : 'PY';
    const info = document.createElement('span'); info.className = 'process-info';
    const title = document.createElement('span'); title.className = 'process-name'; title.textContent = p.bridge?.name || p.source || p.name;
    const meta = document.createElement('span'); meta.className = 'process-meta'; meta.textContent = `PID ${p.pid}${p.memoryMB ? ` · ${p.memoryMB} MB` : ''}`;
    const ready = document.createElement('span'); ready.className = `process-meta ${p.bridge ? 'io-ready' : ''}`; ready.textContent = p.bridge ? 'I/O ready' : 'Monitored · connector needed';
    info.append(title, meta, ready); row.append(icon, info); row.onclick = () => p.bridge ? openProgram(p.bridge) : $('guide-dialog').showModal(); list.append(row);
  }
}
function privacy() {
  const mode = $('mode').value;
  const cloud = mode === 'fusion' ? ['gemini', 'openai'].filter(id => $(`use-${id}`).checked).map(id => names[id]) : ['gemini', 'openai'].includes(mode) ? [names[mode]] : [];
  $('privacy-note').textContent = cloud.length ? `Your prompt will also be sent to ${cloud.join(' and ')}. API usage may incur charges.` : 'Your prompt stays on this computer with Llama 3.';
  $('fusion-state').textContent = mode === 'fusion' && cloud.length ? `FUSION · LLAMA 3 + ${cloud.join(' + ').toUpperCase()}` : `${mode === 'fusion' || mode === 'llama' ? 'LLAMA 3' : names[mode].toUpperCase()} · SINGLE MODEL`;
}
async function run() {
  if (controller) return;
  const prompt = $('prompt').value.trim();
  if (!prompt) { $('prompt').focus(); return showError('Enter a prompt to begin.'); }
  showError(''); controller = new AbortController();
  $('generate').hidden = true; $('cancel').hidden = false; $('mode').disabled = true; $('use-gemini').disabled = true; $('use-openai').disabled = true;
  $('output-empty').hidden = true; $('output-content').hidden = true; $('progress').hidden = false; $('perspectives').hidden = true; $('copy-output').disabled = true;
  $('result-label').textContent = 'Working'; $('progress-text').textContent = $('mode').value === 'fusion' ? 'Gathering perspectives, then synthesizing with Llama 3…' : `Waiting for ${names[$('mode').value]}…`;
  const start = Date.now(); $('elapsed').textContent = '0s'; ticker = setInterval(() => $('elapsed').textContent = `${Math.floor((Date.now() - start) / 1000)}s`, 1000);
  try {
    const result = await api('/api/generate', { prompt, mode: $('mode').value, providers: ['llama', ...['gemini', 'openai'].filter(id => $(`use-${id}`).checked)] }, controller.signal);
    $('output').textContent = result.output || result.error;
    $('result-warning').textContent = result.warning || ''; $('result-warning').hidden = !result.warning;
    $('output-content').hidden = false; $('copy-output').disabled = !result.output;
    $('result-label').textContent = !result.ok ? 'Needs attention' : result.synthesized ? 'Synthesized by Llama 3' : 'Individual response';
    $('run-summary').textContent = `${result.results.filter(r => r.ok).length}/${result.results.length} models · ${(result.elapsedMs / 1000).toFixed(1)}s`;
    const list = $('perspective-list'); list.replaceChildren();
    for (const r of result.results) {
      const item = document.createElement('details'), summary = document.createElement('summary'), meta = document.createElement('span'), pre = document.createElement('pre');
      summary.textContent = names[r.id]; meta.textContent = `${r.ok ? 'Answered' : 'Unavailable'} · ${(r.elapsedMs / 1000).toFixed(1)}s`; summary.append(meta); pre.textContent = r.ok ? r.text : r.error; item.append(summary, pre); list.append(item);
    }
    $('perspectives').hidden = false;
    if (!result.ok) showError(result.error);
  } catch (e) {
    const cancelled = e.name === 'AbortError'; $('output').textContent = cancelled ? 'Generation cancelled.' : e.message; $('result-warning').hidden = true; $('output-content').hidden = false; $('result-label').textContent = cancelled ? 'Cancelled' : 'Connection error'; $('run-summary').textContent = cancelled ? 'Cancelled by you' : 'No answer received'; if (!cancelled) showError(e.message);
  } finally {
    clearInterval(ticker); controller = null; $('progress').hidden = true; $('generate').hidden = false; $('cancel').hidden = true; $('mode').disabled = false; refresh();
  }
}
function openSettings() {
  if (state) {
    for (const id of ['llama', 'gemini', 'openai']) $(`${id}-model`).value = state.settings[`${id}Model`];
    $('ollama-detail').textContent = state.ollama.ready ? `Ready · Installed: ${state.ollama.models.join(', ')}` : state.ollama.running ? 'This model is not installed. Run ollama pull llama3, then refresh.' : 'Start Ollama on this computer to enable Llama 3.';
    for (const id of ['gemini', 'openai']) { $(`${id}-key`).value = ''; $(`${id}-key`).placeholder = state.settings[`${id}Configured`] ? 'Configured · leave blank to keep' : `Enter your ${names[id]} API key`; $(`clear-${id}`).checked = false; }
  }
  $('settings-message').textContent = ''; $('settings-dialog').showModal();
}
function openProgram(p) { selectedProgram = p; lastProgramOutput = ''; $('program-title').textContent = p.name; $('program-info').textContent = `${p.language === 'java' ? 'Java' : 'Python'} · PID ${p.pid} · Messages go directly to this program.`; $('program-input').value = ''; $('program-output').textContent = 'Waiting for a message.'; $('use-program-output').disabled = true; $('program-dialog').showModal(); }
$('program-send').onclick = async () => {
  const p = selectedProgram, text = $('program-input').value.trim(); if (!text) return $('program-input').focus();
  $('program-send').disabled = true; $('program-output').textContent = 'Waiting for the program…'; $('use-program-output').disabled = true; lastProgramOutput = '';
  try { const result = await api('/api/program/send', { id: p.id, text }); if (selectedProgram?.id === p.id) { lastProgramOutput = result.output; $('program-output').textContent = result.output || '(Program returned an empty response.)'; $('use-program-output').disabled = !result.output; } }
  catch (e) { $('program-output').textContent = e.message; } finally { $('program-send').disabled = false; }
};
$('use-program-output').onclick = () => { $('prompt').value = `Help me interpret this output from ${selectedProgram.name}:\n\n${lastProgramOutput}`.slice(0, 24000); $('prompt').dispatchEvent(new Event('input')); $('program-dialog').close(); $('prompt').focus(); };
$('settings-form').onsubmit = async e => {
  e.preventDefault(); const button = e.submitter; button.disabled = true;
  try {
    await api('/api/settings', { llamaModel: $('llama-model').value.trim(), geminiModel: $('gemini-model').value.trim(), openaiModel: $('openai-model').value.trim(), geminiKey: $('gemini-key').value.trim(), openaiKey: $('openai-key').value.trim(), clear_geminiKey: $('clear-gemini').checked, clear_openaiKey: $('clear-openai').checked });
    $('gemini-key').value = ''; $('openai-key').value = ''; $('settings-dialog').close(); await refresh(); toast('Connections saved. Select cloud models to include them.');
  } catch (e) { $('settings-message').textContent = e.message; } finally { button.disabled = false; }
};
$('generate').onclick = run; $('cancel').onclick = () => controller?.abort(); $('settings-open').onclick = openSettings; $('guide-open').onclick = () => $('guide-dialog').showModal(); $('refresh').onclick = refresh;
$('prompt').addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); } });
$('prompt').addEventListener('input', () => $('char-count').textContent = $('prompt').value.length.toLocaleString());
$('copy-output').onclick = async () => { try { await navigator.clipboard.writeText($('output').textContent); toast('Output copied.'); } catch { toast('Select the output text and copy it manually.'); } };
for (const id of ['mode', 'use-gemini', 'use-openai']) $(id).addEventListener('change', privacy);
document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => $(b.dataset.close).close());
document.querySelectorAll('[data-filter]').forEach(b => b.onclick = () => { filter = b.dataset.filter; document.querySelectorAll('[data-filter]').forEach(x => x.classList.toggle('selected', x === b)); if (state) renderPrograms(); });
document.querySelectorAll('[data-prompt]').forEach(b => b.onclick = () => { $('prompt').value = b.dataset.prompt; $('prompt').dispatchEvent(new Event('input')); $('prompt').focus(); });
try { const response = await fetch('/api/session'); const session = await response.json(); if (!response.ok) throw new Error(session.error); token = session.token; await refresh(); }
catch { showError('Cannot connect to the local controller. Start AI Genesis Node, then refresh.'); }
setInterval(refresh, 5000);
