"""Input validation and reproducible learning environments for Godmind Mesh.

The original filename is retained; drillscript loads it with importlib.
"""
from __future__ import annotations

import csv
import io
import numpy as np

DATASETS = ("moons", "rings", "xor", "spiral")
MAX_SAMPLES = 4000


class StructuralIdentityFilter:
    """Validate actual inputs instead of reporting hard-coded environment claims."""

    def __init__(self):
        self.raw_array_state = 1
        self.highest_virtue_pass = None
        self.execution_boundary = "LOCAL_LOOPBACK"

    def execute_virtue_bit_flip(self, bit: int, classification='unknown') -> int:
        from predictive_rules import conditional_bit
        return conditional_bit(bit,self.highest_virtue_pass,classification)

    def verify_environment_limits(self) -> dict:
        return {"execution_boundary": self.execution_boundary,
                "input_dimensions": 2, "classes": [0, 1],
                "coordinate_range": [-1, 1], "internet_required": False}

    @staticmethod
    def number(value, name, low, high):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number.")
        value = float(value)
        if not np.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be between {low} and {high}.")
        return value

    @classmethod
    def sample(cls, row):
        if not isinstance(row, dict) or not all(k in row for k in ("x", "y", "label")):
            raise ValueError("An example needs x, y and label fields.")
        x = cls.number(row["x"], "x", -1, 1)
        y = cls.number(row["y"], "y", -1, 1)
        label = cls.number(row["label"], "label", 0, 1)
        if label not in (0, 1):
            raise ValueError("Label must be 0 (coral) or 1 (mint).")
        return [x, y], int(label)


def make_dataset(name: str, count: int, rng: np.random.Generator):
    """Return bounded 2-D points and real labels from a synthetic teacher."""
    if name not in DATASETS:
        raise ValueError("Choose moons, rings, xor or spiral.")
    labels = np.arange(count) % 2
    rng.shuffle(labels)
    if name == "xor":
        points = rng.uniform(-0.95, 0.95, (count, 2))
        labels = (points[:, 0] * points[:, 1] > 0).astype(int)
    elif name == "rings":
        angle = rng.uniform(0, 2 * np.pi, count)
        radius = np.where(labels == 0, 0.34, 0.76) + rng.normal(0, 0.055, count)
        points = np.column_stack((radius * np.cos(angle), radius * np.sin(angle)))
    elif name == "moons":
        angle = rng.uniform(0, np.pi, count)
        x = np.where(labels == 0, np.cos(angle), 1 - np.cos(angle))
        y = np.where(labels == 0, np.sin(angle), 0.48 - np.sin(angle))
        points = np.column_stack(((x - 0.5) / 1.7, (y - 0.25) / 1.2))
        points += rng.normal(0, 0.043, (count, 2))
    else:
        radius = rng.uniform(0.12, 0.88, count)
        angle = 3.6 * radius + labels * np.pi + rng.normal(0, 0.12, count)
        points = np.column_stack((radius * np.cos(angle), radius * np.sin(angle)))
    return np.clip(points, -0.99, 0.99), labels.astype(float).reshape(-1, 1)


def read_csv(text: str):
    """CSV coordinates must already be normalized to [-1, 1]."""
    if not isinstance(text, str) or len(text) > 700_000:
        raise ValueError("CSV must be text smaller than 700 KB.")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if not reader.fieldnames or set(reader.fieldnames) != {"x", "y", "label"}:
        raise ValueError("CSV needs exactly these headers: x,y,label.")
    points, labels, seen = [], [], set()
    for index, row in enumerate(reader, 2):
        if index > MAX_SAMPLES + 1:
            raise ValueError(f"CSV supports at most {MAX_SAMPLES} rows.")
        try:
            point, label = StructuralIdentityFilter.sample({k: float(v) for k, v in row.items()})
        except (ValueError, TypeError):
            raise ValueError(f"Invalid CSV row {index}: use x,y in [-1,1] and label 0 or 1.") from None
        key = tuple(point)
        if key in seen:
            raise ValueError(f"Duplicate coordinates at row {index}; keep each point unique.")
        seen.add(key)
        points.append(point)
        labels.append(label)
    if len(points) < 20 or any(labels.count(label) < 5 for label in (0, 1)):
        raise ValueError("Provide at least 20 examples, with at least 5 of each class.")
    return np.asarray(points, dtype=float), np.asarray(labels, dtype=float).reshape(-1, 1)


def split_data(points, labels, rng):
    """Stratified holdout: no test example is used for training."""
    train, test = [], []
    for label in (0, 1):
        indices = np.flatnonzero(labels.ravel() == label)
        rng.shuffle(indices)
        boundary = max(1, int(len(indices) * 0.2))
        test.extend(indices[:boundary])
        train.extend(indices[boundary:])
    return points[train], labels[train], points[test], labels[test]
