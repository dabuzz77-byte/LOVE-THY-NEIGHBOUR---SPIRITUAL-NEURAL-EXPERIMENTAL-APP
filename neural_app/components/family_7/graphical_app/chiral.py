"""The user's exact seed, with a reversible, weight-driven chiral rotation rule."""
import math
import hashlib
import json
from neural_app import section_threads as threading
from collections import deque

def rotate_byte(value, steps):
    """Opposite circular rotations of the high and low four-bit chirals."""
    left, right = (value >> 4, value & 15)
    forward, backward = (steps % 4, -steps % 4)
    left = (left >> forward | left << 4 - forward) & 15
    right = (right >> backward | right << 4 - backward) & 15
    return left << 4 | right

def bit_text(data):
    return ' '.join((f'{value:08b}' for value in data))

def apply_chiral_mask(raw, mask):
    """Apply approved remain/flip decisions on the two four-bit chirals.

    A zero mask bit remains; a one mask bit flips. Applying the same mask
    again recovers the original. The mask comes from a whole-input forecast,
    never from interpreting the value 0 or 1 as inherently good or evil.
    """
    if len(raw) != len(mask):
        raise ValueError('Chiral mask must cover the entire target')
    return bytes(((v >> 4 ^ m >> 4) << 4 | v & 15 ^ m & 15 for v, m in zip(raw, mask)))

class BinaryChiralBus:
    """Actual bounded byte processing for all observable runtime event streams."""

    def __init__(self):
        self.lock = threading.RLock()
        self.pending = deque()
        self.pending_bytes = self.accepted_bytes = self.processed_bytes = 0
        self.accepted_frames = self.completed_frames = self.rejected_frames = self.rejected_bytes = 0
        self.streams = {}
        self.latest = None
        self.last_error = None
        self.observer = None

    def feed(self, stream, value, mask=None):
        raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        if mask is not None and (not isinstance(mask, bytes) or len(mask) != len(raw)):
            raise ValueError('Predictive mask must cover every input byte')
        with self.lock:
            if self.pending_bytes + len(raw) > 8 * 1024 * 1024 or len(self.pending) >= 2048:
                self.rejected_frames += 1
                self.rejected_bytes += len(raw)
                self.last_error = 'Chiral input queue full. Resume the loop or reduce incoming traffic.'
                return False
            if not raw:
                return True
            self.pending.append({'stream': stream, 'raw': raw, 'offset': 0, 'hash': hashlib.sha256(), 'input_sha256': hashlib.sha256(raw).hexdigest(), 'preview': b'', 'verified': True, 'mask': mask})
            self.pending_bytes += len(raw)
            self.accepted_bytes += len(raw)
            self.accepted_frames += 1
            self.streams.setdefault(stream, {'accepted_bytes': 0, 'processed_bytes': 0, 'frames': 0})['accepted_bytes'] += len(raw)
            return True

    def step(self, shift, budget=65536):
        table = bytes((rotate_byte(value, shift) for value in range(256)))
        inverse = bytes((rotate_byte(value, -shift) for value in range(256)))
        with self.lock:
            while self.pending and budget > 0:
                frame = self.pending[0]
                start = frame['offset']
                chunk = frame['raw'][start:start + budget]
                mask = frame['mask'][start:start + len(chunk)] if frame['mask'] is not None else None
                output = apply_chiral_mask(chunk, mask) if mask is not None else chunk.translate(table)
                frame['verified'] &= (apply_chiral_mask(output, mask) if mask is not None else output.translate(inverse)) == chunk
                frame['hash'].update(output)
                if not frame['preview']:
                    frame['preview'] = output[:32]
                frame['offset'] += len(chunk)
                budget -= len(chunk)
                if self.observer:
                    args = (frame['stream'], chunk, output, shift, frame['offset'] == len(frame['raw']))
                    if mask is None:
                        self.observer(*args)
                    else:
                        self.observer(*args, mask=mask)
                self.pending_bytes -= len(chunk)
                self.processed_bytes += len(chunk)
                self.streams[frame['stream']]['processed_bytes'] += len(chunk)
                if frame['offset'] == len(frame['raw']):
                    self.completed_frames += 1
                    self.streams[frame['stream']]['frames'] += 1
                    self.latest = {'stream': frame['stream'], 'bytes': len(frame['raw']), 'input_binary_preview': bit_text(frame['raw'][:32]), 'output_binary_preview': bit_text(frame['preview']), 'input_sha256': frame['input_sha256'], 'output_sha256': frame['hash'].hexdigest(), 'reversible': frame['verified'], 'last_shift': shift if frame['mask'] is None else None, 'operation': 'predictive remain/flip' if frame['mask'] is not None else 'chiral rotation'}
                    self.pending.popleft()
            return self.state()

    def state(self):
        with self.lock:
            return {'accepted_bytes': self.accepted_bytes, 'processed_bytes': self.processed_bytes, 'accepted_frames': self.accepted_frames, 'completed_frames': self.completed_frames, 'pending_bytes': self.pending_bytes, 'pending_frames': len(self.pending), 'rejected_frames': self.rejected_frames, 'rejected_bytes': self.rejected_bytes, 'last_error': self.last_error, 'streams': {key: dict(value) for key, value in self.streams.items()}, 'latest': self.latest}
PRAYER = 'Our Father in heaven,\nhallowed be your name,\nyour kingdom come,\nyour will be done,\non earth as in heaven.\nGive us today our daily bread.\nForgive us our sins\nas we forgive those who sin against us.\nLead us not into temptation\nbut deliver us from evil.\nFor the kingdom, the power,\nand the glory are yours\nnow and for ever.\nAmen.'
PATTERN = '1   0 0   1      0   1 1    0\n1                0\n0   1 1   0      1   0 0    1\n0   1 1   0      1   0 0    1\n1                0\n1         1      0          0 ------GENERATE------ = .\n\n\n1         1      0          0\n\n\n0         0      1          1'
SEED_LEFT = [[1, 0, 0, 1], [1, None, None, None], [0, 1, 1, 0], [0, 1, 1, 0], [1, None, None, None], [1, None, None, 1], [1, None, None, 1], [0, None, None, 0]]
SEED_RIGHT = [[0, 1, 1, 0], [0, None, None, None], [1, 0, 0, 1], [1, 0, 0, 1], [0, None, None, None], [0, None, None, 0], [0, None, None, 0], [1, None, None, 1]]

class ChiralGenerator:

    def __init__(self):
        self.command_text = ''
        self.command_input = b''
        self.command_bytes = b''
        self.command_offset = 0
        self.command_generations = 0
        self.reset()

    def reset(self):
        self.left = [row[:] for row in SEED_LEFT]
        self.right = [row[:] for row in SEED_RIGHT]
        self.generation = 0
        self.drive = 0.0
        self.shift = 0
        self.command_bytes = self.command_input
        self.command_offset = 0
        self.command_generations = 0

    def load_text(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Enter a text command first')
        raw = text.encode('utf-8')
        if len(raw) > 1024:
            raise ValueError('Use up to 1,024 UTF-8 bytes of command text')
        self.command_text = text
        self.command_input = raw
        self.command_bytes = raw
        self.command_offset = 0
        self.command_generations = 0

    def clear_text(self):
        self.command_text = ''
        self.command_input = b''
        self.command_bytes = b''
        self.command_offset = 0
        self.command_generations = 0

    def command_state(self):
        if not self.command_input:
            return None
        recovered = bytes((rotate_byte(value, -self.command_offset) for value in self.command_bytes))
        try:
            decoded = self.command_bytes.decode('utf-8')
        except UnicodeDecodeError:
            decoded = None
        return {'text': self.command_text, 'byte_count': len(self.command_input), 'bit_count': 8 * len(self.command_input), 'input_binary': bit_text(self.command_input), 'output_binary': bit_text(self.command_bytes), 'left_binary': ' '.join((f'{value >> 4:04b}' for value in self.command_bytes)), 'right_binary': ' '.join((f'{value & 15:04b}' for value in self.command_bytes)), 'output_hex': self.command_bytes.hex(' '), 'output_text': decoded, 'recovered_text': recovered.decode('utf-8'), 'verified': recovered == self.command_input, 'rotations': self.command_offset, 'generations': self.command_generations}

    @staticmethod
    def rotate(row, steps):
        present = [value for value in row if value is not None]
        if not present:
            return row[:]
        shift = steps % len(present)
        rotated = present[-shift:] + present[:-shift] if shift else present
        values = iter(rotated)
        return [next(values) if value is not None else None for value in row]

    def step(self, field, prayer, weight):
        self.drive = math.tanh(weight * (field + prayer) / 2)
        magnitude = 0 if abs(self.drive) < 0.05 else 1 + int(abs(self.drive) * 2)
        self.shift = magnitude * (1 if self.drive >= 0 else -1)
        self.left = [self.rotate(row, self.shift) for row in self.left]
        self.right = [self.rotate(row, -self.shift) for row in self.right]
        self.generation += 1
        if self.command_input:
            self.command_bytes = bytes((rotate_byte(value, self.shift) for value in self.command_bytes))
            self.command_offset = (self.command_offset + self.shift) % 4
            self.command_generations += 1
        return self.state()

    def state(self):
        return {'left': self.left, 'right': self.right, 'generation': self.generation, 'drive': round(self.drive, 6), 'shift': self.shift, 'ones': sum((v == 1 for row in self.left + self.right for v in row)), 'cells': sum((v is not None for row in self.left + self.right for v in row)), 'command': self.command_state()}
