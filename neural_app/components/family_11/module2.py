"""A small, genuine neural classifier with backpropagation and Adam.

NumPy is the only external dependency. Checkpoints are plain JSON, never pickle.
"""
from __future__ import annotations
import numpy as np
ARCHITECTURE = [2, 12, 8, 1]

class TotalBitRealityEngine:
    """A 2 -> 12 -> 8 -> 1 MLP: tanh hidden layers, sigmoid output."""

    def __init__(self, seed=42, learning_rate=0.012):
        self.seed = int(seed)
        self.rng = np.random.default_rng(seed)
        self.learning_rate = float(learning_rate)
        self.weights = [self.rng.normal(0, np.sqrt(2 / (a + b)), (a, b)) for a, b in zip(ARCHITECTURE[:-1], ARCHITECTURE[1:])]
        self.biases = [np.zeros((1, b)) for b in ARCHITECTURE[1:]]
        self.m = [np.zeros_like(p) for p in self.parameters]
        self.v = [np.zeros_like(p) for p in self.parameters]
        self.steps = 0
        self.bit_substrate = [0] * 8
        self.virtue_pass_active = True
        self.user_will_parity = True

    @property
    def parameters(self):
        return self.weights + self.biases

    def execute_total_inversion(self):
        if any((type(bit) is not int or bit not in (0, 1) for bit in self.bit_substrate)):
            raise ValueError('The substrate must contain integer bits only.')
        enabled = self.virtue_pass_active and self.user_will_parity
        return [1 - bit if enabled else bit for bit in self.bit_substrate]

    def forward(self, points):
        activations = [np.asarray(points, dtype=float).reshape(-1, 2)]
        for weight, bias in zip(self.weights[:-1], self.biases[:-1]):
            activations.append(np.tanh(activations[-1] @ weight + bias))
        logits = activations[-1] @ self.weights[-1] + self.biases[-1]
        probabilities = np.exp(-np.logaddexp(0, -logits))
        activations.append(probabilities)
        return (probabilities, activations, logits)

    def predict(self, points):
        return self.forward(points)[0]

    def loss_and_gradients(self, points, labels):
        probabilities, activations, logits = self.forward(points)
        labels = np.asarray(labels, dtype=float).reshape(-1, 1)
        loss = float(np.mean(np.logaddexp(0, logits) - labels * logits))
        delta = (probabilities - labels) / len(labels)
        weight_grads, bias_grads = ([], [])
        for layer in reversed(range(len(self.weights))):
            weight_grads.insert(0, activations[layer].T @ delta)
            bias_grads.insert(0, delta.sum(axis=0, keepdims=True))
            if layer:
                delta = delta @ self.weights[layer].T * (1 - activations[layer] ** 2)
        return (loss, weight_grads + bias_grads)

    def train_batch(self, points, labels, batch_size=64):
        if not len(points):
            raise ValueError('Add labeled examples before training.')
        indices = self.rng.choice(len(points), min(batch_size, len(points)), replace=False)
        loss, gradients = self.loss_and_gradients(points[indices], labels[indices])
        if not np.isfinite(loss) or not all((np.isfinite(g).all() for g in gradients)):
            raise ValueError('Training became unstable; reset and use a lower learning rate.')
        self.steps += 1
        for parameter, gradient, m, v in zip(self.parameters, gradients, self.m, self.v):
            np.clip(gradient, -5, 5, out=gradient)
            m *= 0.9
            m += 0.1 * gradient
            v *= 0.999
            v += 0.001 * gradient ** 2
            parameter -= self.learning_rate * (m / (1 - 0.9 ** self.steps)) / (np.sqrt(v / (1 - 0.999 ** self.steps)) + 1e-08)
        return loss

    def evaluate(self, points, labels):
        probabilities, _, logits = self.forward(points)
        return {'loss': float(np.mean(np.logaddexp(0, logits) - labels * logits)), 'accuracy': float(np.mean((probabilities >= 0.5) == labels))}

    def to_dict(self):
        return {'architecture': ARCHITECTURE, 'seed': self.seed, 'steps': self.steps, 'learning_rate': self.learning_rate, 'rng': self.rng.bit_generator.state, 'weights': [p.tolist() for p in self.weights], 'biases': [p.tolist() for p in self.biases], 'm': [p.tolist() for p in self.m], 'v': [p.tolist() for p in self.v]}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get('architecture') != ARCHITECTURE:
            raise ValueError('This checkpoint needs a 2-12-8-1 architecture.')
        seed, steps, rate = (data.get('seed'), data.get('steps'), data.get('learning_rate'))
        if type(seed) is not int or not 0 <= seed <= 2 ** 32 - 1:
            raise ValueError('Invalid checkpoint seed.')
        if type(steps) is not int or not 0 <= steps <= 10 ** 9:
            raise ValueError('Invalid training step count.')
        if isinstance(rate, bool) or not isinstance(rate, (float, int)) or (not 0.0001 <= rate <= 0.1):
            raise ValueError('Invalid learning rate.')
        model = cls(seed, rate)
        for key in ('weights', 'biases', 'm', 'v'):
            values, target = (data.get(key), getattr(model, key))
            if not isinstance(values, list) or len(values) != len(target):
                raise ValueError(f'Invalid checkpoint {key}.')
            for item, reference in zip(values, target):
                array = np.asarray(item, dtype=float)
                if array.shape != reference.shape or not np.isfinite(array).all() or np.max(np.abs(array)) > 1000000.0:
                    raise ValueError(f'Invalid checkpoint {key} shape or values.')
                if key == 'v' and (array < 0).any():
                    raise ValueError('Adam variance cannot be negative.')
                reference[:] = array
        try:
            model.rng.bit_generator.state = data['rng']
        except (KeyError, TypeError, ValueError):
            raise ValueError('Invalid checkpoint random state.') from None
        model.steps = steps
        return model
