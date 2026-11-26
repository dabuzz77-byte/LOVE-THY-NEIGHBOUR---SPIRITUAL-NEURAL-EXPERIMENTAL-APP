"""Measured PCM envelope modulates the software carrier without changing its cadence."""
import hashlib
import io
import math
from pathlib import Path
from neural_app import section_threads as threading
import time
import wave

class WavModulator:

    def __init__(self):
        self.lock = threading.RLock()
        self.envelope = []
        self.meta = {}
        self.intensity = 0.5
        self.running = False
        self.loop = True
        self.started = 0
        self.position = 0

    def load(self, raw, name='audio.wav'):
        if not 44 <= len(raw) <= 24 * 1024 * 1024:
            raise ValueError('Choose a PCM WAV of at most 24 MB')
        values = []
        with wave.open(io.BytesIO(raw), 'rb') as f:
            channels, width, rate, frames = (f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes())
            if channels not in (1, 2) or width not in (1, 2, 3, 4) or (not 8000 <= rate <= 192000) or (not 0 < frames / rate <= 600):
                raise ValueError('Use mono/stereo PCM, 8–32 bit, 8–192 kHz, up to ten minutes')
            size = max(1, round(rate / 7.83))
            total = 0
            while True:
                chunk = f.readframes(size)
                if not chunk:
                    break
                if len(chunk) % (width * channels):
                    raise ValueError('Truncated PCM frame')
                squares = 0
                count = len(chunk) // width
                for i in range(0, len(chunk), width):
                    sample = (chunk[i] - 128) / 128 if width == 1 else int.from_bytes(chunk[i:i + width], 'little', signed=True) / 2 ** (width * 8 - 1)
                    squares += sample * sample
                values.append(math.sqrt(squares / max(1, count)))
                total += len(chunk) // (width * channels)
            if total != frames:
                raise ValueError('Truncated WAV: frame count does not match its header')
        with self.lock:
            self.raw = raw
            self.envelope = values
            self.position = 0
            self.running = False
            self.meta = {'name': Path(name).name[:160], 'sha256': hashlib.sha256(raw).hexdigest(), 'channels': channels, 'sample_width': width, 'sample_rate': rate, 'duration': frames / rate, 'window_seconds': size / rate, 'peak_rms': max(values), 'bytes': len(raw), 'windows': len(values)}
        return self.view()

    def control(self, data):
        with self.lock:
            if 'intensity' in data:
                n = data['intensity']
                if type(n) not in (float, int) or not math.isfinite(n) or (not 0 <= n <= 1):
                    raise ValueError('Intensity must be 0–1')
                self.intensity = n
            if 'loop' in data:
                if type(data['loop']) is not bool:
                    raise ValueError('Loop must be true or false')
                self.loop = data['loop']
            action = data.get('action')
            if action == 'start':
                if not self.envelope:
                    raise ValueError('Insert a WAV first')
                if not self.running:
                    self.started = time.monotonic() - self.position
                    self.running = True
            elif action in ('pause', 'reset'):
                self.position = self.current()['position'] if action == 'pause' else 0
                self.running = False
            elif action is not None:
                raise ValueError('Choose start, pause or reset')
        return self.view()

    def current(self):
        with self.lock:
            pos = time.monotonic() - self.started if self.running else self.position
            if self.envelope and pos >= self.meta['duration']:
                if self.loop:
                    pos %= self.meta['duration']
                else:
                    self.running = False
                    self.position = 0
                    pos = 0
            rms = self.envelope[min(len(self.envelope) - 1, int(pos / self.meta['window_seconds']))] if self.envelope else 0
            envelope = rms / max(self.meta.get('peak_rms', 0), 1e-12)
            gain = 1 - self.intensity + self.intensity * envelope if self.running else 1
            return {'position': pos, 'rms': rms, 'gain': gain, 'running': self.running, 'intensity': self.intensity, 'loop': self.loop}

    def view(self):
        with self.lock:
            stride = max(1, len(self.envelope) // 400)
            return {**self.meta, **self.current(), 'waveform': self.envelope[::stride], 'formula': 'gain = (1 − intensity) + intensity × RMS / peak RMS; inactive gain = 1'}
