# Ported engine definitions. Original launchers and UI entry points are excluded.
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
BASE = Path(__file__).resolve().parent
KEYS = ('access', 'comfort', 'transition', 'automation')
HORIZON = 60

def validate_scenario(data):
    if not isinstance(data, dict):
        raise ValueError('scenario must be an object')
    result = {}
    for key in KEYS:
        value = data.get(key)
        if type(value) not in (int, float) or not np.isfinite(value) or (not 0 <= value <= 100):
            raise ValueError(f'{key} must be a finite number from 0 to 100')
        result[key] = float(value)
    for key in ('valve', 'gate'):
        if type(data.get(key)) is not bool:
            raise ValueError(f'{key} must be true or false')
        result[key] = data[key]
    return result

def mean_step(states, controls, steps=1):
    """Mean increments from the source; quantities remain scenario percentages.

    Source attributes: eco_floor_security, comfort_distribution_rate,
    monetization_atrophy_index, automation_progress; valve and quarantine gate.
    This is a deterministic reduction of the random UI simulation, not world data.
    """
    y = np.array(states, dtype=np.float64, copy=True)
    controls = np.asarray(controls)
    valve, gate = (controls[:, 0] > 0.5, controls[:, 1] > 0.5)
    for _ in range(steps):
        y[:, 0] += np.where(valve, np.where(y[:, 0] < 95, 0.25, 0), np.where(y[:, 0] > 40, -0.05, 0))
        y[:, 1] += np.where(valve, np.where(y[:, 1] < 90, 0.2, 0), np.where(y[:, 1] > 10, -0.03, 0))
        y[:, 2] += np.where(valve, np.where(y[:, 2] < 100, 0.4, 0), np.where(y[:, 2] > 0, -0.1, 0))
        y[:, 3] += np.where(gate & (y[:, 3] < 98), 0.125, 0)
        np.clip(y, 0, 100, out=y)
    return y

def features(states, controls):
    return np.concatenate((states / 50 - 1, controls * 2 - 1), axis=1)

class NeuralEngine:

    def __init__(self, folder=None):
        self.folder = Path(folder or BASE / 'models')
        self.metadata = json.loads((self.folder / 'model.json').read_text(encoding='utf-8'))
        with np.load(self.folder / 'weights.npz', allow_pickle=False) as data:
            self.params = [np.array(data[key], dtype=np.float64) for key in ('w1', 'b1', 'w2', 'b2', 'w3', 'b3')]
        expected = [(6, 32), (32,), (32, 24), (24,), (24, 4), (4,)]
        if [p.shape for p in self.params] != expected or not all((np.all(np.isfinite(p)) for p in self.params)):
            raise ValueError('Invalid neural model weights')
        self.calls = 0
        self.last_ms = None

    def forward(self, x):
        w1, b1, w2, b2, w3, b3 = self.params
        a1 = np.tanh(x @ w1 + b1)
        a2 = np.tanh(a1 @ w2 + b2)
        output = a2 @ w3 + b3
        return (output, a1, a2)

    def infer(self, scenario):
        s = validate_scenario(scenario)
        started = time.perf_counter()
        states = np.array([[s[k] for k in KEYS]])
        controls = np.array([[int(s['valve']), int(s['gate'])]])
        prediction, a1, a2 = self.forward(features(states, controls))
        predicted = np.clip(prediction[0] * 100, 0, 100)
        reference = mean_step(states, controls, HORIZON)[0]
        self.calls += 1
        self.last_ms = (time.perf_counter() - started) * 1000
        return {'predicted': dict(zip(KEYS, map(float, predicted))), 'rule_reference': dict(zip(KEYS, map(float, reference))), 'horizon_ticks': HORIZON, 'latency_ms': self.last_ms, 'activations': [a1[0].tolist(), a2[0].tolist()], 'model_id': self.metadata['model_id'], 'basis': 'synthetic simulation rules'}

def train(folder=None, iterations=5000):
    folder = Path(folder or BASE / 'models')
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261012)
    states = rng.uniform(0, 100, (7000, 4))
    controls = rng.integers(0, 2, (7000, 2)).astype(float)
    x = features(states, controls)
    y = mean_step(states, controls, HORIZON) / 100
    train_x, test_x = (x[:6000], x[6000:])
    train_y, test_y = (y[:6000], y[6000:])
    params = [rng.normal(0, np.sqrt(2 / 6), (6, 32)), np.zeros(32), rng.normal(0, np.sqrt(2 / 32), (32, 24)), np.zeros(24), rng.normal(0, 0.12, (24, 4)), np.zeros(4)]
    moments, velocities = ([np.zeros_like(p) for p in params], [np.zeros_like(p) for p in params])
    loss_history = []
    started = time.perf_counter()
    for step in range(1, iterations + 1):
        idx = rng.integers(0, len(train_x), 128)
        bx, by = (train_x[idx], train_y[idx])
        w1, b1, w2, b2, w3, b3 = params
        a1 = np.tanh(bx @ w1 + b1)
        a2 = np.tanh(a1 @ w2 + b2)
        out = a2 @ w3 + b3
        d3 = 2 * (out - by) / out.size
        d2 = d3 @ w3.T * (1 - a2 * a2)
        d1 = d2 @ w2.T * (1 - a1 * a1)
        grads = [bx.T @ d1, d1.sum(0), a1.T @ d2, d2.sum(0), a2.T @ d3, d3.sum(0)]
        rate = 0.003 * (0.25 + 0.75 * (1 - step / iterations))
        for i, (p, g) in enumerate(zip(params, grads)):
            moments[i] = 0.9 * moments[i] + 0.1 * g
            velocities[i] = 0.999 * velocities[i] + 0.001 * g * g
            p -= rate * (moments[i] / (1 - 0.9 ** step)) / (np.sqrt(velocities[i] / (1 - 0.999 ** step)) + 1e-08)
        if step == 1 or step % 250 == 0:
            loss_history.append({'step': step, 'mse': float(np.mean((out - by) ** 2))})
    pred = np.clip(np.tanh(np.tanh(test_x @ params[0] + params[1]) @ params[2] + params[3]) @ params[4] + params[5], 0, 1)
    error = abs(pred - test_y) * 100
    source = BASE / 'source_reference' / 'post_scarcity_simulation.py'
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    metadata = {'model_id': 'scenario-mlp-' + source_sha[:12], 'architecture': [6, 32, 24, 4], 'training_examples': 6000, 'held_out_examples': 1000, 'iterations': iterations, 'horizon_ticks': HORIZON, 'held_out_mae_points': float(error.mean()), 'mae_by_metric': dict(zip(KEYS, map(float, error.mean(0)))), 'held_out_p95_abs_error_points': float(np.quantile(error, 0.95)), 'training_seconds': time.perf_counter() - started, 'source_sha256': source_sha, 'basis': 'Synthetic samples of the supplied simulation using mean increments; not real-world observations.', 'loss_history': loss_history}
    np.savez_compressed(folder / 'weights.npz', **dict(zip(('w1', 'b1', 'w2', 'b2', 'w3', 'b3'), params)))
    (folder / 'model.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return metadata
