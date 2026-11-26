import { test } from 'node:test';
import assert from 'node:assert/strict';
import { callProvider, generate, openAIText } from '../providers.mjs';

const config = { llamaModel: 'llama3', geminiModel: 'gemini-example', openaiModel: 'gpt-example', geminiKey: 'gemini-test-key', openaiKey: 'openai-test-key' };

test('all perspectives begin concurrently and Llama synthesizes both cloud answers', async () => {
  const started = [], releases = [];
  const caller = async (id, prompt) => {
    if (prompt.includes('REFERENCE RESPONSES')) {
      assert.equal(id, 'llama');
      assert.match(prompt, /gemini answer/);
      assert.match(prompt, /openai answer/);
      return 'combined answer';
    }
    started.push(id);
    return new Promise(resolve => releases.push(() => resolve(`${id} answer`)));
  };
  const pending = generate({ prompt: 'Design a message queue', mode: 'fusion', providers: ['gemini', 'openai'] }, config, { caller });
  assert.deepEqual(started, ['llama', 'gemini', 'openai']);
  releases.forEach(resolve => resolve());
  const result = await pending;
  assert.equal(result.output, 'combined answer');
  assert.equal(result.synthesized, true);
  assert.equal(result.partial, false);
});

test('one unavailable provider is reported and other responses still synthesize', async () => {
  const result = await generate({ prompt: 'hello', providers: ['gemini', 'openai'] }, config, { caller: async id => { if (id === 'gemini') throw new Error('quota exceeded'); return `${id} answer`; } });
  assert.equal(result.partial, true);
  assert.equal(result.synthesized, true);
  assert.equal(result.results.find(r => r.id === 'gemini').error, 'quota exceeded');
});

test('missing Llama never claims successful fusion', async () => {
  const result = await generate({ prompt: 'hello', providers: ['gemini', 'openai'] }, config, { caller: async id => { if (id === 'llama') throw new Error('offline'); return `${id} answer`; } });
  assert.equal(result.synthesized, false);
  assert.match(result.warning, /fusion did not complete/);
});

test('no provider answer yields an explicit error rather than invented output', async () => {
  const result = await generate({ prompt: 'hello', providers: ['gemini'] }, config, { caller: async () => { throw new Error('offline'); } });
  assert.equal(result.ok, false); assert.equal(result.output, '');
});

test('single-provider selection never contacts another provider', async () => {
  const calls = [];
  await generate({ prompt: 'hello', mode: 'llama', providers: ['gemini', 'openai'] }, config, { caller: async id => { calls.push(id); return 'answer'; } });
  assert.deepEqual(calls, ['llama']);
});

test('provider adapters send expected REST bodies and parse returned text', async () => {
  for (const id of ['llama', 'gemini', 'openai']) {
    const text = await callProvider(id, 'hello', config, { fetcher: async (url, request) => {
      const payload = JSON.parse(request.body);
      assert.equal(request.method, 'POST');
      if (id === 'openai') { assert.equal(payload.store, false); assert.equal(payload.input, 'hello'); assert.equal(request.headers.Authorization, 'Bearer openai-test-key'); assert.match(url, /\/v1\/responses$/); }
      if (id === 'gemini') { assert.equal(payload.contents[0].parts[0].text, 'hello'); assert.equal(request.headers['x-goog-api-key'], 'gemini-test-key'); }
      if (id === 'llama') { assert.equal(payload.stream, false); assert.equal(payload.model, 'llama3'); }
      return { ok: true, json: async () => ({ message: { content: 'answer' }, candidates: [{ content: { parts: [{ thought: true, text: 'hidden reasoning' }, { text: 'answer' }] } }], output: [{ type: 'reasoning' }, { type: 'message', content: [{ type: 'output_text', text: 'answer' }] }] }) };
    } });
    assert.equal(text, 'answer');
  }
});

test('API secrets are redacted from provider errors', async () => {
  await assert.rejects(callProvider('openai', 'hello', config, { fetcher: async () => ({ ok: false, status: 401, json: async () => ({ error: { message: 'invalid openai-test-key' } }) }) }), /\[redacted\]/);
});

test('empty prompts and missing keys fail before an external request', async () => {
  await assert.rejects(generate({ prompt: ' ' }, config), /Enter a prompt/);
  await assert.rejects(callProvider('gemini', 'hello', {}), /API key/);
  assert.equal(openAIText({ output: [{ type: 'message', content: [{ type: 'refusal', refusal: 'No' }] }] }), '');
});
