"""Direct Gemini and OpenAI clients; Windows-account encrypted credential storage."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
from ..source.ai_context import gemini_contents, fit_context

class KeyVault:

    def __init__(self, folder):
        self.folder = Path(folder)

    def _path(self, provider):
        if provider not in {'gemini', 'openai'}:
            raise ValueError('Unknown provider')
        return self.folder / (provider + '.key.dpapi')

    @staticmethod
    def _crypt(data, decrypt=False):
        if os.name != 'nt':
            raise OSError('Saved API keys use Windows account encryption')

        class Blob(ctypes.Structure):
            _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
        buffer = ctypes.create_string_buffer(data)
        source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
        result = Blob()
        crypt = ctypes.WinDLL('crypt32', use_last_error=True)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
        function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        function.restype = wintypes.BOOL
        if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(result.data, result.size)
        finally:
            kernel.LocalFree(result.data)

    def save(self, provider, key):
        if not key.strip():
            raise ValueError('Enter an API key first')
        encrypted = self._crypt(key.strip().encode('utf-8'))
        path = self._path(provider)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(encrypted)
        temporary.replace(path)

    def load(self, provider):
        path = self._path(provider)
        return self._crypt(path.read_bytes(), True).decode('utf-8') if path.exists() else ''

    def delete(self, provider):
        self._path(provider).unlink(missing_ok=True)

def redact(value, key):
    text = str(value)
    return text.replace(key, '[API key]') if key else text

def request_json(url, key, provider, body=None, timeout=90):
    if not key.strip():
        raise ValueError('Enter or load your API key')
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    headers['x-goog-api-key' if provider == 'gemini' else 'Authorization'] = key if provider == 'gemini' else 'Bearer ' + key
    request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            message = json.loads(error.read()).get('error', {}).get('message', str(error.reason))
        except (ValueError, AttributeError):
            message = str(error.reason)
        raise RuntimeError(f'HTTP {error.code}: {redact(message, key)}') from None
    except (OSError, ValueError) as error:
        raise RuntimeError(redact(error, key)) from None
    if not isinstance(result, dict):
        raise ValueError('The service returned an unexpected response')
    return result

def list_models(provider, key):
    if provider == 'gemini':
        names, token = ([], '')
        while True:
            url = 'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000'
            if token:
                url += '&pageToken=' + urllib.parse.quote(token, safe='')
            result = request_json(url, key, provider, timeout=30)
            names += [m['name'].removeprefix('models/') for m in result.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            token = result.get('nextPageToken')
            if not token:
                return sorted(set(names))
    result = request_json('https://api.openai.com/v1/models', key, provider, timeout=30)
    return sorted((m['id'] for m in result.get('data', [])))

def compose_input(prompt, state=None):
    if state is None:
        return prompt
    return prompt + '\n\nCURRENT FLUX BUS ENGINE STATE (application data):\n' + json.dumps(state, ensure_ascii=False, indent=2)

def generate(provider, key, model, prompt, state=None, history=None, context_options=None):
    model = model.strip().removeprefix('models/')
    if not re.fullmatch('[A-Za-z0-9_.:-]+', model):
        raise ValueError('Choose or enter a model ID')
    history = history or []
    context_report = None
    if provider == 'gemini' and context_options and context_options.get('auto_fit'):
        url = 'https://generativelanguage.googleapis.com/v1beta/models/' + urllib.parse.quote(model, safe='')
        metadata = request_json(url, key, provider, timeout=30)
        budget = context_options.get('input_budget', 24000)
        if type(budget) is not int or budget < 1:
            raise ValueError('Input token budget must be positive')
        model_limit = metadata.get('inputTokenLimit')
        if type(model_limit) is int and model_limit > 0:
            budget = min(budget, max(1, model_limit - 1024))
        count_method = ['Gemini countTokens']

        def count(contents):
            try:
                counted = request_json(url + ':countTokens', key, provider, {'contents': contents}, timeout=45)
            except RuntimeError as error:
                message = str(error).lower()
                if message.startswith(('http 400:', 'http 413:')) and ('token' in message and any((word in message for word in ('exceed', 'too large', 'too long', 'limit'))) or 'request entity too large' in message):
                    return budget + 1
                if not str(error).startswith(('HTTP 404:', 'HTTP 501:')):
                    raise
                count_method[0] = 'Conservative UTF-8 byte estimate (countTokens unavailable)'
                return len(json.dumps(contents, ensure_ascii=False).encode('utf-8'))
            tokens = counted.get('totalTokens')
            if type(tokens) is not int or tokens < 0:
                raise ValueError('Gemini did not return a valid input token count')
            return tokens
        prompt, history, context_report = fit_context(prompt, state, history, budget, count, compose_input)
        context_report.update(method=count_method[0], model_input_limit=model_limit)
    sent_input = compose_input(prompt, state)
    if provider == 'gemini':
        contents = gemini_contents(prompt, state, history, compose_input)
        raw = request_json('https://generativelanguage.googleapis.com/v1beta/models/' + urllib.parse.quote(model, safe='') + ':generateContent', key, provider, {'contents': contents})
        candidates = raw.get('candidates', [])
        candidate = candidates[0] if candidates else {}
        output = '\n'.join((p['text'] for p in candidate.get('content', {}).get('parts', []) if 'text' in p and (not p.get('thought'))))
        status = candidate.get('finishReason', raw.get('promptFeedback', {}).get('blockReason', 'NO_TEXT'))
        usage = raw.get('usageMetadata', {})
        reply_wire = {**candidate.get('content', {}), 'role': 'model'} if candidate.get('content') else None
    elif provider == 'openai':
        inputs = []
        for message in history:
            if message['role'] == 'assistant' and message.get('wire'):
                inputs.extend(message['wire'])
            else:
                inputs.append({'role': message['role'], 'content': message['content']})
        inputs.append({'role': 'user', 'content': sent_input})
        raw = request_json('https://api.openai.com/v1/responses', key, provider, {'model': model, 'input': inputs, 'store': False, 'include': ['reasoning.encrypted_content']})
        output = '\n'.join((p.get('text', p.get('refusal', '')) for item in raw.get('output', []) if item.get('type') == 'message' for p in item.get('content', []) if p.get('type') in {'output_text', 'refusal'}))
        status, usage = (raw.get('status', 'UNKNOWN'), raw.get('usage', {}))
        if raw.get('error'):
            raise RuntimeError(redact(raw['error'].get('message', 'Request failed'), key))
        reply_wire = [item for item in raw.get('output', []) if item.get('type') == 'message' or (item.get('type') == 'reasoning' and item.get('encrypted_content'))]
    else:
        raise ValueError('Unknown provider')
    context_preview = None
    if context_report is not None:
        from ..source.conversations import preview
        context_preview = preview(prompt, state, history, compose_input)
    return {'provider': provider, 'model': model, 'output': output, 'status': status, 'usage': usage, 'request_id': raw.get('id', raw.get('responseId')), 'input': sent_input, 'state_included': state is not None, 'conversation_reply': reply_wire, 'context_report': context_report, 'context_preview': context_preview}
