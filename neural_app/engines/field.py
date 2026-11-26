# Ported engine definitions. Original launchers and UI entry points are excluded.


import math, random, threading, time, json, socket, os, queue, subprocess, sys, struct
from pathlib import Path
from collections import deque

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
APPS = Path.home() / 'Desktop/CHAT GPT APPS'
BG = '#080d19'
PANEL = '#0d1626'
CYAN = '#59e6db'
GOLD = '#e5b777'
TEXT = '#dce8f4'
MUTED = '#73899f'

class Engine:

    def __init__(self):
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.running = True
        self.mode = 'perimeter'
        self.depth = 5
        self.force_true = False
        self.ticks = 0
        self.stimulus = 0.0
        self.ms = 0.0
        self.feedback_gain = 0.35
        self.effective_bias = 0.5
        self.script_signal = 0.0
        self.script_at = 0.0
        self.script_samples = 0
        self.external_signal = 0.0
        self.external_at = 0.0
        self.feedback_terms = {}
        self.rng = random.Random(int.from_bytes(os.urandom(32), 'big'))
        self.bit_source = os.urandom
        self.window_ones = 0
        self.noise = 0.22
        self.bias = 0.5
        self.stochastic = True
        self.bits = [0] * 96
        self.bit_history = deque(maxlen=8192)
        self.walk = 0.0
        self.ones = 0
        self.generated = 0
        self.entropy = 0.0
        self.binary_signal = 0.0
        self.values = [0.0] * 96
        self.history = deque([0.0] * 160, maxlen=160)
        r = random.Random(7854)
        self.weights = [[r.uniform(-0.45, 0.45) for _ in range(8)] for _ in range(96)]
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def region(self):
        return [(x, y) for y in range(32) for x in range(32) if self.mode == 'field' or (self.mode == 'core' and (x - 15.5) ** 2 + (y - 15.5) ** 2 <= self.depth ** 2) or (self.mode == 'perimeter' and min(x, y, 31 - x, 31 - y) < self.depth)]

    def step(self):
        t = time.perf_counter()
        with self.lock:
            old = self.values
            if self.stochastic:
                now = time.monotonic()
                network = sum(old) / 96
                external = self.external_signal if now - self.external_at < 15 else 0.0
                script = self.script_signal if now - self.script_at < 15 else 0.0
                self.feedback_terms = dict(network=network, observatory=external, scripts=script, walk=self.walk)
                drive = self.feedback_gain * (0.5 * math.tanh(network * 3) + 0.25 * external + 0.2 * script + 0.05 * self.walk)
                probabilities = [max(0.01, min(0.99, self.bias + drive + self.feedback_gain * 0.12 * old[i])) for i in range(96)]
                self.effective_bias = sum(probabilities) / 96
                random_words = struct.unpack('<96I', self.bit_source(384))
                self.bits = [int(word / 4294967296 < p) for word, p in zip(random_words, probabilities)]
                for bit in self.bits:
                    if len(self.bit_history) == self.bit_history.maxlen:
                        self.window_ones -= self.bit_history[0]
                    self.bit_history.append(bit)
                    self.window_ones += bit
                self.ones += sum(self.bits)
                self.generated += 96
                self.binary_signal = sum(self.bits) / 48 - 1
                self.walk = max(-1.0, min(1.0, self.walk * 0.97 + self.rng.gauss(0, 0.045)))
                p = self.window_ones / len(self.bit_history)
                self.entropy = -(p * math.log2(p) + (1 - p) * math.log2(1 - p)) if 0 < p < 1 else 0.0
            else:
                self.binary_signal = 0.0
                self.walk = 0.0
            self.values = [math.tanh(sum((w * old[(i + j * 11 + 1) % 96] for j, w in enumerate(self.weights[i]))) + 0.24 * math.sin(self.ticks * 0.07 + i * 0.31) + self.stimulus + (self.noise * (self.rng.gauss(0, 0.45) + (self.bits[i] * 2 - 1) * 0.3 + self.walk * 0.4) if self.stochastic else 0)) for i in range(96)]
            self.stimulus *= 0.96
            self.ticks += 1
            self.history.append(sum((abs(v) for v in self.values)) / 96)
            self.ms = (time.perf_counter() - t) * 1000

    def loop(self):
        while not self.stop.is_set():
            if self.running:
                self.step()
            self.stop.wait(0.05)

    def snapshot(self):
        with self.lock:
            return dict(ticks=self.ticks, mode=self.mode, depth=self.depth, running=self.running, values=self.values[:], history=list(self.history), nodes=len(self.region()), ms=self.ms, force_true=self.force_true, noise=self.noise, bias=self.bias, stochastic=self.stochastic, bits=self.bits[:], entropy=self.entropy, generated=self.generated, binary_signal=self.binary_signal, walk=self.walk, effective_bias=self.effective_bias, feedback_gain=self.feedback_gain, feedback_terms=self.feedback_terms.copy(), script_samples=self.script_samples)

    def command(self, text):
        c = text.strip().lower()
        with self.lock:
            if c in ('pause', 'stop', 'pause engine'):
                self.running = False
            elif c in ('resume', 'start', 'run', 'run all', 'resume engine'):
                self.running = True
            elif c in ('core', 'runall at core', 'run at core', 'mode core'):
                self.mode = 'core'
            elif c in ('perimeter', 'run at depth of perimeter', 'runall at perimeter', 'mode perimeter'):
                self.mode = 'perimeter'
            elif c in ('field', 'mode field'):
                self.mode = 'field'
            elif c.startswith('depth '):
                d = int(c.split()[1])
                if not 1 <= d <= 15:
                    raise ValueError('Depth must be 1 to 15')
                self.depth = d
            elif c in ('true on', 'true off'):
                self.force_true = c.endswith('on')
            elif c in ('stochastic on', 'stochastic off'):
                self.stochastic = c.endswith('on')
            elif c.startswith(('noise ', 'bias ', 'feedback ')):
                key, value = c.split()
                value = float(value)
                if not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError('Use a number between 0 and 1')
                setattr(self, 'feedback_gain' if key == 'feedback' else key, value)
            elif c == 'pulse':
                self.stimulus = 0.9
            else:
                raise ValueError('Try core, perimeter, field, depth 5, pulse, pause, resume, true on/off, sync, scan, noise 0.3, bias 0.5, feedback 0.35, stochastic on/off.')
        return 'Applied: ' + text

    def close(self):
        self.stop.set()
        if self.thread.is_alive():
            self.thread.join(2)
