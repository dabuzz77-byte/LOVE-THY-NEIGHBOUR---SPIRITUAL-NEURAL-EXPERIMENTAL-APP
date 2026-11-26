"""Inspect/add Windows VPN profiles; provider credentials stay in Windows UI."""
import json
import os
from pathlib import Path
import re
import subprocess
from neural_app import section_threads as threading
import time

class VpnManager:

    def __init__(self):
        self.lock = threading.RLock()
        self.profiles = []
        self.checked = 0
        self.error = None

    def call(self, body):
        if os.name != 'nt':
            raise ValueError('Windows VPN controls require Windows')
        executable = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        result = subprocess.run([str(executable), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(Path(__file__).with_name('vpn_windows.ps1'))], input=json.dumps(body), text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=20, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise ValueError((result.stderr.strip() or 'Windows VPN operation failed')[:800])
        return json.loads(result.stdout.lstrip('\ufeff'))

    def refresh(self):
        try:
            data = self.call({'action': 'status'})
            profiles = data.get('profiles') or []
            if not isinstance(profiles, list):
                profiles = [profiles]
            with self.lock:
                self.profiles = profiles
                self.error = None
                self.checked = time.monotonic()
        except Exception as exc:
            with self.lock:
                self.profiles = []
                self.error = str(exc)
                self.checked = time.monotonic()
        return self.view()

    def view(self):
        with self.lock:
            return {'profiles': [dict(p) for p in self.profiles], 'error': self.error, 'checked': bool(self.checked), 'fresh': bool(self.checked and time.monotonic() - self.checked < 20), 'scope': 'Windows built-in VPN profiles. Third-party VPN clients may not appear here.'}

    def connected(self, name):
        with self.lock:
            return bool(name and self.checked and (time.monotonic() - self.checked < 20) and (not self.error) and any((p['name'] == name and p['status'] == 'Connected' for p in self.profiles)))

    def add(self, body):
        name = body.get('name', '')
        server = body.get('server', '')
        tunnel = body.get('tunnel')
        if not isinstance(name, str) or not re.fullmatch('[\\w .()-]{1,64}', name) or name.startswith('-'):
            raise ValueError('Use a VPN name of 1–64 letters, numbers, spaces or .()-')
        if not isinstance(server, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9.-]{0,252}', server):
            raise ValueError('Enter the VPN provider server hostname or IPv4 address, without a URL or port')
        if tunnel not in ('Ikev2', 'Sstp'):
            raise ValueError('Choose IKEv2 or SSTP')
        result = self.call({'action': 'add', 'name': name.strip(), 'server': server, 'tunnel': tunnel})
        self.refresh()
        return result

    def open_settings(self):
        if os.name != 'nt':
            raise ValueError('Windows VPN settings require Windows')
        os.startfile('ms-settings:network-vpn')
        return {'opened': True, 'target': 'Windows VPN settings'}

    def connect(self, name):
        self.refresh()
        with self.lock:
            if not isinstance(name, str) or not any((p['name'] == name for p in self.profiles)):
                raise ValueError('Choose an existing Windows VPN profile')
        program = Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'System32/rasphone.exe'
        subprocess.Popen([str(program), '-d', name], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {'opened': True, 'profile': name, 'status': 'Windows connection dialog opened; connection is not yet confirmed.'}
