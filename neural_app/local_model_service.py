"""Reconnect the installed local Ollama service without changing bus ports."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler

_lock = threading.Lock()

def ensure_local_service(endpoint, timeout=15):
    endpoint = str(endpoint).rstrip('/')
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port or 80
    except ValueError:
        raise ValueError('Invalid Llama port. Use http://127.0.0.1:11434 in model connection settings.') from None
    if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.path or parsed.query or parsed.username:
        raise ValueError('Llama needs a local Ollama address, such as http://127.0.0.1:11434.')
    opener = build_opener(ProxyHandler({}))
    def ready():
        try:
            with opener.open(endpoint+'/api/version', timeout=1) as response:
                return bool(json.load(response).get('version'))
        except OSError as e:
            reason=getattr(e, 'reason', e)
            if getattr(reason, 'winerror', None)==10013:
                raise ValueError('Windows blocked the local Ollama connection at '+endpoint+' (WinError 10013). Restart Neural App normally from its launcher; keep the ambient bus on a separate port such as 8800.') from e
            return False
        except ValueError:
            return False
    if ready():
        return endpoint
    with _lock:
        if ready():
            return endpoint
        # Never start a second service on a user-defined port or on the input bus.
        if port != 11434:
            raise ValueError('No Ollama service at '+endpoint+'. Llama normally uses port 11434; the ambient input bus normally uses 8798. Check model connection settings.')
        executable = shutil.which('ollama')
        if not executable and os.name == 'nt':
            candidate = Path(os.environ.get('LOCALAPPDATA', ''))/'Programs/Ollama/ollama.exe'
            if candidate.is_file():
                executable = str(candidate)
        if not executable:
            raise ValueError('Ollama is not running at '+endpoint+'. Open Ollama, then retry Ask Llama.')
        env = os.environ.copy()
        env['OLLAMA_HOST'] = '127.0.0.1:11434'
        flags = (subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) if os.name == 'nt' else 0
        subprocess.Popen([executable, 'serve'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, env=env, creationflags=flags,
                         start_new_session=os.name != 'nt')
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            if ready():
                return endpoint
            time.sleep(.25)
    raise ValueError('Ollama did not become ready at '+endpoint+'. Open Ollama and retry. The input-bus port is separate.')
