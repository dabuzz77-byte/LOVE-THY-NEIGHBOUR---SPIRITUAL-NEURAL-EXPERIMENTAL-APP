"""Local Windows speech synthesis. Text is data, never PowerShell source."""
import io
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import wave


class Speech:
    def __init__(self, data):
        self.data = Path(data).resolve()
        self.lock = threading.Lock()

    def render(self, text, rate=1):
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 6000:
            raise ValueError('Speak between 1 and 6,000 characters at a time')
        if type(rate) not in (int, float) or not math.isfinite(rate) or not .7 <= rate <= 1.3:
            raise ValueError('Choose a speech speed between 0.7 and 1.3')
        if os.name != 'nt':
            raise ValueError('Local Windows voice is unavailable. Choose a browser voice.')
        if not self.lock.acquire(blocking=False):
            raise ValueError('The Windows voice is finishing another request. Try again shortly.')
        try:
            # TemporaryDirectory owns only its newly generated child directory.
            with tempfile.TemporaryDirectory(prefix='speech-', dir=self.data) as directory:
                folder = Path(directory)
                request = folder/'request.json'
                output = folder/'voice.wav'
                request.write_text(json.dumps({'text':text, 'rate':round((rate-1)*10), 'output':str(output)}), encoding='utf-8')
                powershell = Path(os.environ.get('SystemRoot', r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
                result = subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                    '-File', str(Path(__file__).with_name('speak.ps1')), str(request)],
                    capture_output=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if result.returncode or not output.exists():
                    raise ValueError('Windows could not generate speech. Check installed Windows voices or choose a browser voice.')
                content = output.read_bytes()
                with wave.open(io.BytesIO(content)) as audio:
                    if audio.getnframes() <= 0:
                        raise ValueError('Windows returned an empty speech recording')
                return content
        except subprocess.TimeoutExpired:
            raise ValueError('Windows speech timed out. Try a shorter reply or a browser voice.') from None
        finally:
            self.lock.release()
