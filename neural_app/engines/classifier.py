# Ported engine definitions. Original launchers and UI entry points are excluded.
from __future__ import annotations
import argparse
import json
import math
import os
import random
import sys
import tempfile
import time
from pathlib import Path
APP_TITLE = 'Unified Neural Engine'
DATASETS = ('XOR', 'Circle', 'Wave')
TOPOLOGIES = {'Compact  ·  4 / 3': (2, 4, 3, 1), 'Balanced  ·  6 / 5': (2, 6, 5, 1), 'Wide  ·  10 / 8': (2, 10, 8, 1)}
DEFAULT_TOPOLOGY = 'Balanced  ·  6 / 5'
C = {'bg': '#090e19', 'panel': '#111b2c', 'plot': '#0c1423', 'line': '#24344b', 'text': '#e9f2ff', 'muted': '#869ab6', 'cyan': '#62e5ea', 'pink': '#ff8eb4', 'purple': '#b6a3ff', 'green': '#a3e9ba', 'button': '#203149'}

class EthicalSubstrate:
    """Original local bit-transform API, retained for console compatibility."""

    def __init__(self):
        self.bit_reality_one, self.bit_reality_zero = (1, 0)
        self.tesla_law_favoured = True
        self.corporate_greed_favoured = False
        self.greed_mind_active = False
        self.structural_baseline = 'UPWARDS'
        self.equilibrium_status = 'HARMONIZED'
        self.economic_floor_weight = 1.0

    def cast_virtue_bit_array(self, bit_matrix, virtue_pass):
        invert = not virtue_pass or self.corporate_greed_favoured
        return [1 - b if invert else b for b in bit_matrix if b in (0, 1)]

    def generate_containers(self):
        return {'can_process_text_logic': 'ACTIVE', 'can_train_local_neural_network': 'ACTIVE', 'can_visualize_activations': 'ACTIVE', 'external_services': 'NOT REQUIRED'}

class StructuralMatrixEngine:
    """Bounded version of the original text renderer."""

    def __init__(self, width=60, height=16):
        if not isinstance(width, int) or not isinstance(height, int) or width < 4 or (height < 3):
            raise ValueError('The matrix must be at least 4 columns by 3 rows.')
        self.width, self.height, self.frame_index = (width, height, 0)
        self.clear_buffer()

    def clear_buffer(self, character='.'):
        if not isinstance(character, str) or len(character) != 1:
            raise ValueError('The fill must be a single character.')
        self.buffer = [[character] * self.width for _ in range(self.height)]

    def compute_frame(self, substrate, processed_bits):
        self.clear_buffer()
        for x in range(self.width):
            self.buffer[0][x] = self.buffer[-1][x] = '#'
        for y in range(self.height):
            self.buffer[y][0] = self.buffer[y][-1] = '#'
        if processed_bits:
            for y in range(1, self.height - 1):
                b = processed_bits[y % len(processed_bits)]
                left = int(y * 2.8) + b + 2
                right = self.width - 3 - int(y * 2.8) - b
                for x, chars in ((left, str(b) + 'O'), (right, '21' if b else 'V0')):
                    for offset, char in enumerate(chars):
                        if 0 < x + offset < self.width - 1:
                            self.buffer[y][x + offset] = char
        label = '[VIRTUE 1] INF'
        start = self.width // 2 - len(label) // 2
        for i, char in enumerate(label):
            if 0 < start + i < self.width - 1:
                self.buffer[self.height // 2][start + i] = char

class ProductionPipeline:

    def __init__(self):
        self.substrate = EthicalSubstrate()
        self.engine = StructuralMatrixEngine(62, 16)
        self.session_inputs, self.session_outputs = ([], [])

    def execute_pipeline_cycle(self):
        self.engine.frame_index += 1
        bits = self.substrate.cast_virtue_bit_array([1, 0, 1, 1, 0, 0, 1, 0, 1, 1], True)
        self.engine.compute_frame(self.substrate, bits)
        print('=' * 64)
        print('UNIFIED TEXT MATRIX | FRAME %02d' % self.engine.frame_index)
        for row in self.engine.buffer:
            print(' '.join(row))
        print('=' * 64 + '\n')

def target_for(name, x, y):
    if name == 'XOR':
        return int((x > 0) != (y > 0))
    if name == 'Circle':
        return int(x * x + y * y < 0.55)
    if name == 'Wave':
        return int(y > 0.45 * math.sin(3.8 * x))
    raise ValueError('Unknown dataset.')

def make_dataset(name, count=224, seed=41):
    rng = random.Random(seed)
    data = []
    for _ in range(count):
        x, y = (rng.uniform(-1, 1), rng.uniform(-1, 1))
        data.append(([x, y], target_for(name, x, y)))
    return data

def sigmoid(value):
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-min(value, 700)))
    e = math.exp(max(value, -700))
    return e / (1.0 + e)

def blend(a, b, amount):
    t = max(0.0, min(1.0, amount))
    aa, bb = ([int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)])
    return '#' + ''.join(('%02x' % round(v + (w - v) * t) for v, w in zip(aa, bb)))

class NeuralNetwork:
    """Small tanh MLP, sigmoid output, binary cross entropy, momentum SGD."""

    def __init__(self, layers=(2, 6, 5, 1), seed=7):
        if tuple(layers) not in TOPOLOGIES.values():
            raise ValueError('Unsupported network shape.')
        self.layers = tuple(layers)
        rng = random.Random(seed)
        self.weights, self.biases = ([], [])
        for n_in, n_out in zip(layers, layers[1:]):
            limit = math.sqrt(6.0 / (n_in + n_out))
            self.weights.append([[rng.uniform(-limit, limit) for _ in range(n_in)] for _ in range(n_out)])
            self.biases.append([0.0] * n_out)
        self.reset_momentum()
        self.updates = 0

    def reset_momentum(self):
        self.velocity_w = [[[0.0 for _ in row] for row in layer] for layer in self.weights]
        self.velocity_b = [[0.0 for _ in layer] for layer in self.biases]

    def forward(self, inputs):
        if len(inputs) != self.layers[0]:
            raise ValueError('Expected two input values.')
        activations = [list(inputs)]
        for index, (weights, biases) in enumerate(zip(self.weights, self.biases)):
            func = sigmoid if index == len(self.weights) - 1 else math.tanh
            activations.append([func(sum((w * a for w, a in zip(row, activations[-1]))) + bias) for row, bias in zip(weights, biases)])
        return activations

    def predict(self, inputs):
        return self.forward(inputs)[-1][0]

    def train_batch(self, batch, learning_rate=0.08):
        if not batch:
            return
        gw = [[[0.0 for _ in row] for row in layer] for layer in self.weights]
        gb = [[0.0 for _ in layer] for layer in self.biases]
        for inputs, target in batch:
            acts = self.forward(inputs)
            delta = [acts[-1][0] - target]
            for layer in range(len(self.weights) - 1, -1, -1):
                for j, d in enumerate(delta):
                    gb[layer][j] += d
                    for i, a in enumerate(acts[layer]):
                        gw[layer][j][i] += d * a
                if layer:
                    delta = [(1 - a * a) * sum((self.weights[layer][j][i] * d for j, d in enumerate(delta))) for i, a in enumerate(acts[layer])]
        inv = 1.0 / len(batch)
        for layer, matrix in enumerate(self.weights):
            for j, row in enumerate(matrix):
                for i, weight in enumerate(row):
                    grad = max(-5, min(5, gw[layer][j][i] * inv + 0.0001 * weight))
                    velocity = 0.88 * self.velocity_w[layer][j][i] - learning_rate * grad
                    self.velocity_w[layer][j][i] = velocity
                    row[i] += velocity
                velocity = 0.88 * self.velocity_b[layer][j] - learning_rate * gb[layer][j] * inv
                self.velocity_b[layer][j] = velocity
                self.biases[layer][j] += velocity
        self.updates += 1

    def evaluate(self, data):
        if not data:
            return (0.0, 0.0)
        total, correct = (0.0, 0)
        for inputs, target in data:
            p = max(1e-09, min(1 - 1e-09, self.predict(inputs)))
            total -= target * math.log(p) + (1 - target) * math.log(1 - p)
            correct += int((p >= 0.5) == bool(target))
        return (total / len(data), correct / len(data))

    def to_dict(self):
        return {'layers': list(self.layers), 'weights': self.weights, 'biases': self.biases, 'updates': self.updates, 'velocity_w': self.velocity_w, 'velocity_b': self.velocity_b}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError('Missing network data.')
        layers = data.get('layers')
        if not isinstance(layers, list) or any((type(x) is not int for x in layers)) or tuple(layers) not in TOPOLOGIES.values():
            raise ValueError('Unsupported network shape.')
        net = cls(layers)

        def numbers(values, size):
            if not isinstance(values, list) or len(values) != size:
                raise ValueError('Incorrect parameter dimensions.')
            if any((type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1000 for v in values)):
                raise ValueError('Parameters must be finite numbers between -1000 and 1000.')
            return [float(v) for v in values]

        def matrices(values):
            if not isinstance(values, list) or len(values) != len(layers) - 1:
                raise ValueError('Incorrect layer count.')
            result = []
            for layer, (n_in, n_out) in zip(values, zip(layers, layers[1:])):
                if not isinstance(layer, list) or len(layer) != n_out:
                    raise ValueError('Incorrect layer width.')
                result.append([numbers(row, n_in) for row in layer])
            return result

        def vectors(values):
            if not isinstance(values, list) or len(values) != len(layers) - 1:
                raise ValueError('Incorrect bias count.')
            return [numbers(row, size) for row, size in zip(values, layers[1:])]
        net.weights = matrices(data.get('weights'))
        net.biases = vectors(data.get('biases'))
        if 'velocity_w' in data:
            net.velocity_w = matrices(data['velocity_w'])
        if 'velocity_b' in data:
            net.velocity_b = vectors(data['velocity_b'])
        updates = data.get('updates', 0)
        if type(updates) is not int or not 0 <= updates <= 10 ** 12:
            raise ValueError('Invalid training counter.')
        net.updates = updates
        return net
