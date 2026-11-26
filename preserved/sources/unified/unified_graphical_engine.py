#!/usr/bin/env python3
"""Unified Neural Engine — an interactive, local neural-network playground.

Run: python unified_graphical_engine.py
Options: --console (original text matrix), --self-test, --smoke-test
Requires Python 3.9+ with Tkinter. No third-party packages or internet needed.
The network learns synthetic two-class examples with actual backpropagation.
"""
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

APP_TITLE = "Unified Neural Engine"
DATASETS = ("XOR", "Circle", "Wave")
TOPOLOGIES = {"Compact  ·  4 / 3": (2, 4, 3, 1),
              "Balanced  ·  6 / 5": (2, 6, 5, 1),
              "Wide  ·  10 / 8": (2, 10, 8, 1)}
DEFAULT_TOPOLOGY = "Balanced  ·  6 / 5"
C = {"bg": "#090e19", "panel": "#111b2c", "plot": "#0c1423",
     "line": "#24344b", "text": "#e9f2ff", "muted": "#869ab6",
     "cyan": "#62e5ea", "pink": "#ff8eb4", "purple": "#b6a3ff",
     "green": "#a3e9ba", "button": "#203149"}


class EthicalSubstrate:
    """Original local bit-transform API, retained for console compatibility."""
    def __init__(self):
        self.bit_reality_one, self.bit_reality_zero = 1, 0
        self.tesla_law_favoured = True
        self.corporate_greed_favoured = False
        self.greed_mind_active = False
        self.structural_baseline = "UPWARDS"
        self.equilibrium_status = "HARMONIZED"
        self.economic_floor_weight = 1.0

    def cast_virtue_bit_array(self, bit_matrix, virtue_pass):
        invert = not virtue_pass or self.corporate_greed_favoured
        return [1 - b if invert else b for b in bit_matrix if b in (0, 1)]

    def generate_containers(self):
        return {"can_process_text_logic": "ACTIVE",
                "can_train_local_neural_network": "ACTIVE",
                "can_visualize_activations": "ACTIVE",
                "external_services": "NOT REQUIRED"}


class StructuralMatrixEngine:
    """Bounded version of the original text renderer."""
    def __init__(self, width=60, height=16):
        if not isinstance(width, int) or not isinstance(height, int) or width < 4 or height < 3:
            raise ValueError("The matrix must be at least 4 columns by 3 rows.")
        self.width, self.height, self.frame_index = width, height, 0
        self.clear_buffer()

    def clear_buffer(self, character="."):
        if not isinstance(character, str) or len(character) != 1:
            raise ValueError("The fill must be a single character.")
        self.buffer = [[character] * self.width for _ in range(self.height)]

    def compute_frame(self, substrate, processed_bits):
        self.clear_buffer()
        for x in range(self.width):
            self.buffer[0][x] = self.buffer[-1][x] = "#"
        for y in range(self.height):
            self.buffer[y][0] = self.buffer[y][-1] = "#"
        if processed_bits:
            for y in range(1, self.height - 1):
                b = processed_bits[y % len(processed_bits)]
                left = int(y * 2.8) + b + 2
                right = self.width - 3 - int(y * 2.8) - b
                for x, chars in ((left, str(b) + "O"),
                                 (right, "21" if b else "V0")):
                    for offset, char in enumerate(chars):
                        if 0 < x + offset < self.width - 1:
                            self.buffer[y][x + offset] = char
        label = "[VIRTUE 1] INF"
        start = self.width // 2 - len(label) // 2
        for i, char in enumerate(label):
            if 0 < start + i < self.width - 1:
                self.buffer[self.height // 2][start + i] = char


class ProductionPipeline:
    def __init__(self):
        self.substrate = EthicalSubstrate()
        self.engine = StructuralMatrixEngine(62, 16)
        self.session_inputs, self.session_outputs = [], []

    def execute_pipeline_cycle(self):
        self.engine.frame_index += 1
        bits = self.substrate.cast_virtue_bit_array([1, 0, 1, 1, 0, 0, 1, 0, 1, 1], True)
        self.engine.compute_frame(self.substrate, bits)
        print("=" * 64)
        print("UNIFIED TEXT MATRIX | FRAME %02d" % self.engine.frame_index)
        for row in self.engine.buffer:
            print(" ".join(row))
        print("=" * 64 + "\n")


def target_for(name, x, y):
    if name == "XOR":
        return int((x > 0) != (y > 0))
    if name == "Circle":
        return int(x * x + y * y < 0.55)
    if name == "Wave":
        return int(y > 0.45 * math.sin(3.8 * x))
    raise ValueError("Unknown dataset.")


def make_dataset(name, count=224, seed=41):
    rng = random.Random(seed)
    data = []
    for _ in range(count):
        x, y = rng.uniform(-1, 1), rng.uniform(-1, 1)
        data.append(([x, y], target_for(name, x, y)))
    return data


def sigmoid(value):
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-min(value, 700)))
    e = math.exp(max(value, -700))
    return e / (1.0 + e)


def blend(a, b, amount):
    t = max(0.0, min(1.0, amount))
    aa, bb = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % round(v + (w - v) * t) for v, w in zip(aa, bb))


class NeuralNetwork:
    """Small tanh MLP, sigmoid output, binary cross entropy, momentum SGD."""
    def __init__(self, layers=(2, 6, 5, 1), seed=7):
        if tuple(layers) not in TOPOLOGIES.values():
            raise ValueError("Unsupported network shape.")
        self.layers = tuple(layers)
        rng = random.Random(seed)
        self.weights, self.biases = [], []
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
            raise ValueError("Expected two input values.")
        activations = [list(inputs)]
        for index, (weights, biases) in enumerate(zip(self.weights, self.biases)):
            func = sigmoid if index == len(self.weights) - 1 else math.tanh
            activations.append([func(sum(w * a for w, a in zip(row, activations[-1])) + bias)
                                for row, bias in zip(weights, biases)])
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
                    delta = [(1 - a * a) * sum(self.weights[layer][j][i] * d for j, d in enumerate(delta))
                             for i, a in enumerate(acts[layer])]
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
            return 0.0, 0.0
        total, correct = 0.0, 0
        for inputs, target in data:
            p = max(1e-9, min(1 - 1e-9, self.predict(inputs)))
            total -= target * math.log(p) + (1 - target) * math.log(1 - p)
            correct += int((p >= 0.5) == bool(target))
        return total / len(data), correct / len(data)

    def to_dict(self):
        return {"layers": list(self.layers), "weights": self.weights, "biases": self.biases,
                "updates": self.updates, "velocity_w": self.velocity_w, "velocity_b": self.velocity_b}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Missing network data.")
        layers = data.get("layers")
        if not isinstance(layers, list) or any(type(x) is not int for x in layers) or tuple(layers) not in TOPOLOGIES.values():
            raise ValueError("Unsupported network shape.")
        net = cls(layers)

        def numbers(values, size):
            if not isinstance(values, list) or len(values) != size:
                raise ValueError("Incorrect parameter dimensions.")
            if any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1000 for v in values):
                raise ValueError("Parameters must be finite numbers between -1000 and 1000.")
            return [float(v) for v in values]

        def matrices(values):
            if not isinstance(values, list) or len(values) != len(layers) - 1:
                raise ValueError("Incorrect layer count.")
            result = []
            for layer, (n_in, n_out) in zip(values, zip(layers, layers[1:])):
                if not isinstance(layer, list) or len(layer) != n_out:
                    raise ValueError("Incorrect layer width.")
                result.append([numbers(row, n_in) for row in layer])
            return result

        def vectors(values):
            if not isinstance(values, list) or len(values) != len(layers) - 1:
                raise ValueError("Incorrect bias count.")
            return [numbers(row, size) for row, size in zip(values, layers[1:])]

        net.weights = matrices(data.get("weights"))
        net.biases = vectors(data.get("biases"))
        if "velocity_w" in data:
            net.velocity_w = matrices(data["velocity_w"])
        if "velocity_b" in data:
            net.velocity_b = vectors(data["velocity_b"])
        updates = data.get("updates", 0)
        if type(updates) is not int or not 0 <= updates <= 10**12:
            raise ValueError("Invalid training counter.")
        net.updates = updates
        return net


def read_session(path):
    if Path(path).stat().st_size > 2_000_000:
        raise ValueError("This session is too large (maximum 2 MB).")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or data.get("format") != "unified-neural-engine" or data.get("version") != 1:
        raise ValueError("Choose a Unified Neural Engine session (.json).")
    name = data.get("dataset")
    if name not in DATASETS:
        raise ValueError("Unsupported dataset.")
    net = NeuralNetwork.from_dict(data.get("network"))
    rate = data.get("learning_rate", 0.08)
    if type(rate) not in (int, float) or not math.isfinite(rate) or not 0.005 <= rate <= 0.3:
        raise ValueError("Learning rate must be between 0.005 and 0.3.")
    return name, net, float(rate)


def write_session(path, dataset, network, learning_rate):
    payload = {"format": "unified-neural-engine", "version": 1, "dataset": dataset,
               "learning_rate": learning_rate, "network": network.to_dict()}
    destination = Path(path)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            json.dump(payload, handle, indent=2, allow_nan=False)
        os.replace(temp_path, destination)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


# Tkinter is imported only by the desktop entry point; console/tests stay headless.

class NeuralEngineApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk, self.root = tk, ttk, root
        self.root.title(APP_TITLE)
        self.root.configure(bg=C["bg"])
        self.root.geometry("1320x920")
        self.root.minsize(1080, 760)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.icon = tk.PhotoImage(width=32, height=32)
        self.icon.put(C["bg"], to=(0, 0, 32, 32))
        for ax, ay, bx, by in ((6, 8, 25, 16), (6, 24, 25, 16)):
            for step in range(25):
                x, y = round(ax + (bx - ax) * step / 24), round(ay + (by - ay) * step / 24)
                self.icon.put(C["muted"], (x, y))
        for cx, cy, color in ((6, 8, C["cyan"]), (6, 24, C["pink"]), (25, 16, C["cyan"])):
            for x in range(cx - 4, cx + 5):
                for y in range(cy - 4, cy + 5):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= 16:
                        self.icon.put(color, (x, y))
        self.root.iconphoto(True, self.icon)
        self.running, self.closed, self.dialog_open = True, False, False
        self.seed, self.rng = 7, random.Random(123)
        self.dataset_name = tk.StringVar(value="XOR")
        self.topology_name = tk.StringVar(value=DEFAULT_TOPOLOGY)
        self.rate = tk.DoubleVar(value=0.08)
        self.speed = tk.IntVar(value=4)
        self.follow = tk.BooleanVar(value=True)
        self.probe_x, self.probe_y = tk.DoubleVar(value=0.55), tk.DoubleVar(value=-0.55)
        self.model = NeuralNetwork()
        self.history, self.selected, self.node_positions = [], (3, 0), {}
        self.network_cache, self.map_cache = None, None
        self.last_metrics = self.last_map = self.last_probe = 0.0
        self.fps, self.frame_count, self.fps_clock = 0, 0, time.perf_counter()
        self.loss, self.accuracy, self.next_tick = 0.0, 0.0, None
        self.set_data("XOR")
        self.setup_styles()
        self.build_ui()
        self.root.bind("<space>", self.space_toggle)
        self.root.bind("<Control-s>", lambda event: self.save_session())
        self.root.bind("<Control-o>", lambda event: self.load_session())
        self.root.bind("<Escape>", lambda event: self.set_running(False))
        self.refresh_metrics()
        self.next_tick = self.root.after(50, self.tick)

    def setup_styles(self):
        style = self.ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=C["button"], background=C["button"],
                        foreground=C["text"], arrowcolor=C["cyan"], bordercolor=C["line"], padding=7)
        style.configure("Vertical.TScrollbar", background=C["button"], troughcolor=C["panel"],
                        arrowcolor=C["muted"], bordercolor=C["panel"], lightcolor=C["button"],
                        darkcolor=C["button"], arrowsize=11, borderwidth=0)
        style.map("TCombobox", fieldbackground=[("readonly", C["button"])],
                  foreground=[("readonly", C["text"])], selectbackground=[("readonly", C["button"])],
                  selectforeground=[("readonly", C["text"])])
        self.root.option_add("*TCombobox*Listbox.background", C["panel"])
        self.root.option_add("*TCombobox*Listbox.foreground", C["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["button"])
        self.root.option_add("*TCombobox*Listbox.font", "{Segoe UI} 10")

    def frame(self, parent, color=None, **kwargs):
        return self.tk.Frame(parent, bg=color or C["panel"], **kwargs)

    def label(self, parent, text="", size=10, color=None, bold=False, **kwargs):
        return self.tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color or C["text"],
                             font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def button(self, parent, text, command, accent=False, **kwargs):
        return self.tk.Button(parent, text=text, command=command, bd=0, relief="flat",
                              bg=C["cyan"] if accent else C["button"],
                              fg=C["bg"] if accent else C["text"],
                              activebackground=C["text"] if accent else C["line"],
                              activeforeground=C["bg"] if accent else C["text"],
                              disabledforeground=C["muted"], cursor="hand2",
                              font=("Segoe UI", 10, "bold"), padx=15, pady=9, **kwargs)

    def separator(self, parent):
        self.frame(parent, C["line"], height=1).pack(fill="x", pady=13)

    def scale(self, parent, variable, low, high, resolution, command=None):
        """Canvas slider stays legible across Windows themes and display scales."""
        canvas = self.tk.Canvas(parent, height=22, bg=C["panel"], highlightthickness=0,
                                cursor="hand2", takefocus=True, width=100)
        canvas.pack(fill="x", pady=(4, 0))

        def paint(*unused):
            canvas.delete("all")
            width = max(32, canvas.winfo_width())
            fraction = (variable.get() - low) / (high - low)
            x = 8 + max(0, min(1, fraction)) * (width - 16)
            canvas.create_line(8, 11, width - 8, 11, fill=C["line"], width=4, capstyle="round")
            canvas.create_line(8, 11, x, 11, fill=C["cyan"], width=4, capstyle="round")
            canvas.create_oval(x - 6, 5, x + 6, 17, fill=C["cyan"], outline=C["panel"], width=2)

        def assign(value):
            value = max(low, min(high, low + round((value - low) / resolution) * resolution))
            variable.set(int(value) if resolution == 1 else round(value, 3))
            if variable in (self.probe_x, self.probe_y):
                self.follow.set(False)
            if command is not None:
                command(str(variable.get()))

        def drag(event):
            canvas.focus_set()
            assign(low + (high - low) * (event.x - 8) / max(1, canvas.winfo_width() - 16))

        canvas.bind("<Configure>", paint)
        canvas.bind("<Button-1>", drag)
        canvas.bind("<B1-Motion>", drag)
        canvas.bind("<Left>", lambda event: assign(variable.get() - resolution))
        canvas.bind("<Right>", lambda event: assign(variable.get() + resolution))
        variable.trace_add("write", paint)
        return canvas

    def build_ui(self):
        shell = self.frame(self.root, C["bg"])
        shell.pack(fill="both", expand=True, padx=24, pady=18)
        header = self.frame(shell, C["bg"])
        header.pack(fill="x", pady=(0, 18))
        brand = self.frame(header, C["bg"])
        brand.pack(side="left")
        self.label(brand, "U N I F I E D   /   L A B  0 1", 9, C["cyan"], True).pack(anchor="w")
        self.label(brand, "Neural Engine", 27, bold=True).pack(anchor="w", pady=(2, 0))
        self.label(brand, "See a network learn. Follow every signal.", 10, C["muted"]).pack(anchor="w", pady=(2, 0))
        tools = self.frame(header, C["bg"])
        tools.pack(side="right", anchor="center")
        self.button(tools, "Open session", self.load_session).pack(side="left", padx=(0, 8))
        self.button(tools, "Save session", self.save_session).pack(side="left")
        metrics = self.frame(shell, C["bg"])
        metrics.pack(fill="x", pady=(0, 16))
        self.metric_labels = {}
        cards = [("updates", "TRAINING UPDATES", "0", C["text"]),
                 ("loss", "TRAINING LOSS", "0.000", C["cyan"]),
                 ("accuracy", "VALIDATION ACCURACY", "0.0%", C["green"]),
                 ("shape", "NETWORK SHAPE", "2 / 6 / 5 / 1", C["purple"])]
        for index, (key, title, value, color) in enumerate(cards):
            metrics.columnconfigure(index, weight=1, uniform="metric")
            card = self.frame(metrics, highlightbackground=C["line"], highlightthickness=1)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 10 if index < 3 else 0))
            self.label(card, title, 8, C["muted"], True).pack(anchor="w", padx=16, pady=(11, 3))
            label = self.label(card, value, 22 if key != "shape" else 19, color, True)
            label.pack(anchor="w", padx=16, pady=(0, 11))
            self.metric_labels[key] = label
        body = self.frame(shell, C["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, minsize=242)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        sidebar = self.frame(body, highlightbackground=C["line"], highlightthickness=1)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        sidebar_canvas = self.tk.Canvas(sidebar, bg=C["panel"], highlightthickness=0, width=222, height=100)
        sidebar_scroll = self.ttk.Scrollbar(sidebar, orient="vertical", command=sidebar_canvas.yview)
        sidebar_scroll.pack(side="right", fill="y")
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        sidebar_canvas.configure(yscrollcommand=sidebar_scroll.set)
        control = self.frame(sidebar_canvas)
        control_window = sidebar_canvas.create_window(14, 14, window=control, anchor="nw")
        control.bind("<Configure>", lambda event: sidebar_canvas.configure(scrollregion=(0, 0, sidebar_canvas.winfo_width(), control.winfo_reqheight() + 28)))
        sidebar_canvas.bind("<Configure>", lambda event: sidebar_canvas.itemconfigure(control_window, width=max(180, event.width - 28)))

        def scroll_controls(event):
            if sidebar.winfo_rootx() <= event.x_root <= sidebar.winfo_rootx() + sidebar.winfo_width() and sidebar.winfo_rooty() <= event.y_root <= sidebar.winfo_rooty() + sidebar.winfo_height():
                sidebar_canvas.yview_scroll(-int(event.delta / 120), "units")
        self.root.bind("<MouseWheel>", scroll_controls)
        self.label(control, "CONTROL ROOM", 9, C["muted"], True).pack(anchor="w", pady=(0, 12))
        self.label(control, "Learning task", 10, bold=True).pack(anchor="w")
        dataset = self.ttk.Combobox(control, textvariable=self.dataset_name, values=DATASETS,
                                    state="readonly", font=("Segoe UI", 10), width=22)
        dataset.pack(fill="x", pady=(6, 6))
        dataset.bind("<<ComboboxSelected>>", self.change_dataset)
        self.description = self.label(control, "", 9, C["muted"], wraplength=205, justify="left")
        self.description.pack(anchor="w")
        self.label(control, "Hidden layers", 10, bold=True).pack(anchor="w", pady=(13, 4))
        topology = self.ttk.Combobox(control, textvariable=self.topology_name, values=list(TOPOLOGIES),
                                     state="readonly", font=("Segoe UI", 9), width=22)
        topology.pack(fill="x")
        topology.bind("<<ComboboxSelected>>", self.change_topology)
        self.separator(control)
        lr_line = self.frame(control)
        lr_line.pack(fill="x")
        self.label(lr_line, "Learning rate", 10, bold=True).pack(side="left")
        self.rate_label = self.label(lr_line, "0.080", 10, C["cyan"])
        self.rate_label.pack(side="right")
        self.scale(control, self.rate, 0.005, 0.3, 0.005,
                   lambda value: self.rate_label.configure(text="%.3f" % float(value)))
        speed_line = self.frame(control)
        speed_line.pack(fill="x", pady=(9, 0))
        self.label(speed_line, "Training speed", 10, bold=True).pack(side="left")
        self.speed_label = self.label(speed_line, "4 batches", 9, C["cyan"])
        self.speed_label.pack(side="right")
        self.scale(control, self.speed, 1, 12, 1,
                   lambda value: self.speed_label.configure(text="%d batches" % float(value)))
        actions = self.frame(control)
        actions.pack(fill="x", pady=(14, 7))
        self.play_button = self.button(actions, "Pause", self.toggle, accent=True)
        self.play_button.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.step_button = self.button(actions, "Step", self.step)
        self.step_button.pack(side="left")
        self.button(control, "Reset network", self.reset).pack(fill="x")
        self.separator(control)
        self.label(control, "INPUT PROBE", 9, C["muted"], True).pack(anchor="w")
        follow = self.tk.Checkbutton(control, text="Follow live samples", variable=self.follow,
                                     bg=C["panel"], fg=C["text"], selectcolor=C["plot"],
                                     activebackground=C["panel"], activeforeground=C["cyan"],
                                     font=("Segoe UI", 9), highlightthickness=0, bd=0)
        follow.pack(anchor="w", pady=(7, 0))
        probe_line = self.frame(control)
        probe_line.pack(fill="x", pady=(6, 0))
        self.label(probe_line, "X / Y", 9, C["muted"]).pack(side="left")
        self.probe_label = self.label(probe_line, "+0.55 / −0.55", 9, C["cyan"])
        self.probe_label.pack(side="right")
        self.scale(control, self.probe_x, -1, 1, 0.01)
        self.scale(control, self.probe_y, -1, 1, 0.01)
        self.label(control, "Click the map to test any point.", 8, C["muted"]).pack(anchor="w", pady=(6, 0))
        main = self.frame(body, C["bg"])
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=6)
        main.rowconfigure(1, weight=5)
        network_panel = self.frame(main, highlightbackground=C["line"], highlightthickness=1)
        network_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        top = self.frame(network_panel)
        top.pack(fill="x", padx=17, pady=(13, 0))
        self.label(top, "LIVE NETWORK", 9, C["text"], True).pack(side="left")
        self.state_label = self.label(top, "●  TRAINING", 9, C["green"], True)
        self.state_label.pack(side="right")
        self.network_canvas = self.tk.Canvas(network_panel, bg=C["panel"], highlightthickness=0, height=235)
        self.network_canvas.pack(fill="both", expand=True, padx=8)
        self.network_canvas.bind("<Button-1>", self.pick_node)
        self.network_canvas.bind("<Configure>", lambda event: setattr(self, "network_cache", None))
        self.network_canvas.configure(cursor="hand2")
        self.inspector = self.label(network_panel, "", 9, C["muted"], anchor="w")
        self.inspector.pack(side="bottom", fill="x", padx=17, pady=(0, 6), before=self.network_canvas)
        legend = self.frame(network_panel)
        legend.pack(side="bottom", fill="x", padx=17, pady=(0, 12), before=self.inspector)
        self.label(legend, "━  positive weight", 8, C["cyan"]).pack(side="left", padx=(0, 16))
        self.label(legend, "━  negative weight", 8, C["pink"]).pack(side="left")
        self.label(legend, "Click a neuron to inspect", 8, C["muted"]).pack(side="right")
        bottom = self.frame(main, C["bg"])
        bottom.grid(row=1, column=0, sticky="nsew")
        bottom.columnconfigure(0, weight=1, uniform="bottom")
        bottom.columnconfigure(1, weight=1, uniform="bottom")
        bottom.rowconfigure(0, weight=1)
        map_panel = self.frame(bottom, highlightbackground=C["line"], highlightthickness=1)
        map_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        map_title = self.frame(map_panel)
        map_title.pack(fill="x", padx=15, pady=(12, 3))
        self.label(map_title, "DECISION MAP", 9, bold=True).pack(side="left")
        self.label(map_title, "●  class 1", 8, C["cyan"]).pack(side="right")
        self.label(map_title, "●  class 0", 8, C["pink"]).pack(side="right", padx=(0, 10))
        self.map_canvas = self.tk.Canvas(map_panel, bg=C["panel"], highlightthickness=0, height=160, cursor="crosshair")
        self.map_canvas.pack(fill="both", expand=True, padx=8)
        self.map_canvas.bind("<Button-1>", self.pick_point)
        self.map_canvas.bind("<B1-Motion>", self.pick_point)
        self.map_canvas.bind("<Configure>", lambda event: setattr(self, "map_cache", None))
        self.map_caption = self.label(map_panel, "", 8, C["muted"], anchor="w")
        self.map_caption.pack(side="bottom", fill="x", padx=15, pady=(2, 10), before=self.map_canvas)
        loss_panel = self.frame(bottom, highlightbackground=C["line"], highlightthickness=1)
        loss_panel.grid(row=0, column=1, sticky="nsew")
        self.label(loss_panel, "LEARNING CURVE", 9, bold=True).pack(anchor="w", padx=15, pady=(12, 3))
        self.loss_canvas = self.tk.Canvas(loss_panel, bg=C["panel"], highlightthickness=0, height=150)
        self.loss_canvas.pack(fill="both", expand=True, padx=6)
        loss_notes = self.frame(loss_panel)
        loss_notes.pack(side="bottom", fill="x", before=self.loss_canvas)
        self.label(loss_notes, "Cross entropy · lower is better", 8, C["muted"]).pack(anchor="w", padx=15, pady=(2, 4))
        self.label(loss_notes, "224 training / 96 held-out validation points", 8, C["muted"]).pack(anchor="w", padx=15, pady=(0, 10))
        footer = self.frame(shell, C["bg"])
        footer.pack(side="bottom", fill="x", pady=(11, 0), before=body)
        self.status = self.label(footer, "", 9, C["muted"], anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.performance = self.label(footer, "LOCAL  /  PYTHON", 8, C["muted"])
        self.performance.pack(side="right")
        self.update_description()
        self.set_status("Network active · Space pauses · Esc pauses · Ctrl+S saves")

    def set_data(self, name):
        self.training = make_dataset(name, 224, 41)
        self.validation = make_dataset(name, 96, 909)

    def update_description(self):
        descriptions = {"XOR": "Learn opposite quadrants: a classic nonlinear problem.",
                        "Circle": "Separate the inner circle from its surroundings.",
                        "Wave": "Find the curved boundary between two classes."}
        self.description.configure(text=descriptions[self.dataset_name.get()])

    def set_status(self, message):
        self.status.configure(text=message)

    def set_running(self, running):
        self.running = bool(running)
        self.play_button.configure(text="Pause" if running else "Resume")
        self.state_label.configure(text="●  TRAINING" if running else "●  PAUSED",
                                   fg=C["green"] if running else C["purple"])

    def toggle(self):
        self.set_running(not self.running)
        self.set_status("Training resumed." if self.running else "Training paused · Step runs one batch.")

    def space_toggle(self, event):
        if self.dialog_open or event.widget.winfo_class() in ("TCombobox", "Entry", "Scale", "Button", "Checkbutton"):
            return
        self.toggle()
        return "break"

    def reset(self):
        self.model = NeuralNetwork(TOPOLOGIES[self.topology_name.get()], self.seed)
        self.rng = random.Random(123)
        self.history = []
        self.network_cache = self.map_cache = None
        self.selected = (3, 0)
        self.last_metrics = self.last_map = 0.0
        self.refresh_metrics()
        self.set_status("Network reset · weights and learning history restarted.")

    def change_dataset(self, event=None):
        self.set_data(self.dataset_name.get())
        self.update_description()
        self.reset()
        self.set_status("Learning %s · new dataset and network." % self.dataset_name.get())

    def change_topology(self, event=None):
        self.reset()
        self.set_status("Network rebuilt · %s" % self.topology_name.get())

    def train(self, batches):
        for _ in range(batches):
            self.model.train_batch(self.rng.sample(self.training, 24), self.rate.get())

    def step(self):
        self.set_running(False)
        self.train(1)
        self.refresh_metrics()
        self.last_map = 0.0
        self.set_status("One batch complete · 24 examples processed.")

    def refresh_metrics(self):
        self.loss, _ = self.model.evaluate(self.training)
        _, self.accuracy = self.model.evaluate(self.validation)
        if not self.history or self.history[-1][0] != self.model.updates:
            self.history.append((self.model.updates, self.loss))
            self.history = self.history[-300:]
        self.metric_labels["updates"].configure(text="{:,}".format(self.model.updates))
        self.metric_labels["loss"].configure(text="%.4f" % self.loss)
        self.metric_labels["accuracy"].configure(text="%.1f%%" % (self.accuracy * 100))
        self.metric_labels["shape"].configure(text=" / ".join(map(str, self.model.layers)))
        self.draw_loss()

    def tick(self):
        if self.closed:
            return
        started = time.perf_counter()
        try:
            if not self.dialog_open:
                if self.running:
                    self.train(self.speed.get())
                if self.follow.get() and self.running and started - self.last_probe > 0.65:
                    sample = self.training[(self.model.updates // 3) % len(self.training)][0]
                    self.probe_x.set(round(sample[0], 2))
                    self.probe_y.set(round(sample[1], 2))
                    self.last_probe = started
                inputs = [self.probe_x.get(), self.probe_y.get()]
                activations = self.model.forward(inputs)
                self.probe_label.configure(text="%+.2f / %+.2f" % tuple(inputs))
                self.draw_network(activations, started)
                if started - self.last_metrics > 0.45:
                    self.refresh_metrics()
                    self.last_metrics = started
                if self.map_cache is None or started - self.last_map > 0.75:
                    self.draw_map()
                    self.last_map = started
                self.draw_probe(activations[-1][0])
                self.frame_count += 1
                if started - self.fps_clock > 1:
                    self.fps = round(self.frame_count / (started - self.fps_clock))
                    self.performance.configure(text="%d FPS  /  LOCAL PYTHON" % self.fps)
                    self.frame_count, self.fps_clock = 0, started
        except Exception as exc:
            self.set_running(False)
            self.set_status("Paused after an error: %s" % str(exc)[:100])
            print("Render/training error:", exc, file=sys.stderr)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        self.next_tick = self.root.after(max(8, 33 - elapsed_ms), self.tick)

    def pick_node(self, event):
        nearest = min(self.node_positions, key=lambda key: (self.node_positions[key][0] - event.x) ** 2 +
                      (self.node_positions[key][1] - event.y) ** 2, default=None)
        if nearest is not None:
            x, y = self.node_positions[nearest]
            if (x - event.x) ** 2 + (y - event.y) ** 2 < 32 ** 2:
                self.selected = nearest

    def build_network_canvas(self):
        canvas = self.network_canvas
        canvas.delete("all")
        w, h = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 140)
        self.node_positions, self.edges, self.nodes = {}, [], {}
        names = ("INPUT", "HIDDEN 01", "HIDDEN 02", "OUTPUT")
        for layer, count in enumerate(self.model.layers):
            x = 68 + (w - 136) * layer / 3
            canvas.create_text(x, 18, text=names[layer], fill=C["muted"], font=("Segoe UI", 8, "bold"))
            for j in range(count):
                y = 48 + (h - 88) * (j + 0.5) / count
                self.node_positions[layer, j] = (x, y)
        for layer, matrix in enumerate(self.model.weights):
            for j, row in enumerate(matrix):
                for i in range(len(row)):
                    x1, y1 = self.node_positions[layer, i]
                    x2, y2 = self.node_positions[layer + 1, j]
                    line = canvas.create_line(x1, y1, x2, y2, fill=C["line"], width=1)
                    dot = canvas.create_oval(0, 0, 4, 4, fill=C["cyan"], outline="")
                    self.edges.append((layer, j, i, line, dot, (x1, y1, x2, y2)))
        for key, (x, y) in self.node_positions.items():
            radius = 19 if key[0] in (0, 3) else min(11, max(5, (h - 88) / self.model.layers[key[0]] * 0.36))
            glow = canvas.create_oval(x - radius - 5, y - radius - 5, x + radius + 5, y + radius + 5,
                                      outline=C["line"], width=1)
            circle = canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                       fill=C["plot"], outline=C["cyan"], width=2)
            text = canvas.create_text(x, y, text="", fill=C["text"], font=("Segoe UI", 8, "bold"))
            self.nodes[key] = (glow, circle, text)
        self.output_text = canvas.create_text(w - 68, h - 17, text="", fill=C["cyan"], font=("Segoe UI", 9, "bold"))
        canvas.create_text(68, h - 17, text="x / y coordinates", fill=C["muted"], font=("Segoe UI", 8))
        self.network_cache = (w, h, self.model.layers)

    def draw_network(self, activations, clock):
        if self.network_cache is None:
            self.build_network_canvas()
        canvas = self.network_canvas
        for layer, j, i, line, dot, coords in self.edges:
            weight = self.model.weights[layer][j][i]
            color = C["cyan"] if weight >= 0 else C["pink"]
            strength = math.tanh(abs(weight) * 0.55)
            selected = self.selected in ((layer, i), (layer + 1, j))
            canvas.itemconfigure(line, fill=blend(C["line"], color, 0.2 + 0.55 * strength if selected else 0.12 + 0.32 * strength),
                                 width=1 + 1.4 * strength if selected else 0.7 + 0.6 * strength)
            phase = (clock * 0.52 - layer * 0.18 + i * 0.07 + j * 0.03) % 1
            x1, y1, x2, y2 = coords
            x, y = x1 + (x2 - x1) * phase, y1 + (y2 - y1) * phase
            activity = abs(activations[layer][i])
            radius = 1.3 + 0.9 * activity
            canvas.coords(dot, x - radius, y - radius, x + radius, y + radius)
            canvas.itemconfigure(dot, fill=blend(C["panel"], color, 0.2 + 0.7 * activity),
                                 state="normal" if self.running and activity > 0.12 else "hidden")
        for (layer, j), (glow, circle, text) in self.nodes.items():
            activation = activations[layer][j]
            color = C["cyan"] if activation >= 0 else C["pink"]
            strength = abs(activation)
            selected = (layer, j) == self.selected
            canvas.itemconfigure(glow, outline=color if selected else blend(C["panel"], color, 0.12 + 0.2 * strength), width=2 if selected else 1)
            canvas.itemconfigure(circle, fill=blend(C["plot"], color, 0.08 + 0.38 * strength), outline=blend(C["line"], color, 0.3 + 0.7 * strength))
            value = ("x" if j == 0 else "y") if layer == 0 else ("1" if activation >= 0.5 else "0") if layer == 3 else str(j + 1)
            canvas.itemconfigure(text, text=value)
        output = activations[-1][0]
        canvas.itemconfigure(self.output_text, text="P(1) = %.3f" % output)
        layer, neuron = self.selected
        value = activations[layer][neuron]
        if layer == 0:
            details = "INPUT %s   ·   value %+.3f   ·   drag the probe sliders or click the map" % ("X" if neuron == 0 else "Y", value)
        else:
            bias = self.model.biases[layer - 1][neuron]
            weights = self.model.weights[layer - 1][neuron]
            details = "%s / %02d   ·   activation %+.3f   ·   bias %+.3f   ·   %d incoming weights" % (
                "OUTPUT" if layer == 3 else "HIDDEN %02d" % layer, neuron + 1, value, bias, len(weights))
        self.inspector.configure(text=details)

    def map_bounds(self):
        canvas = self.map_canvas
        w, h = max(80, canvas.winfo_width()), max(80, canvas.winfo_height())
        return 29, 10, w - 14, h - 23

    def draw_map(self):
        canvas = self.map_canvas
        canvas.delete("all")
        left, top, right, bottom = self.map_bounds()
        cols, rows = 42, 26
        dx, dy = (right - left) / cols, (bottom - top) / rows
        low, high = "#542d51", "#205760"
        for row in range(rows):
            y = 1 - 2 * (row + 0.5) / rows
            for col in range(cols):
                x = -1 + 2 * (col + 0.5) / cols
                p = self.model.predict([x, y])
                color = blend(low, C["plot"], p * 2) if p < 0.5 else blend(C["plot"], high, (p - 0.5) * 2)
                canvas.create_rectangle(left + col * dx, top + row * dy, left + (col + 1) * dx + 1,
                                        top + (row + 1) * dy + 1, fill=color, outline="")
        for t in (0, 0.5, 1):
            x, y = left + t * (right - left), top + t * (bottom - top)
            canvas.create_line(x, top, x, bottom, fill="#344052", dash=(2, 5))
            canvas.create_line(left, y, right, y, fill="#344052", dash=(2, 5))
        for inputs, target in self.training[::3]:
            x = left + (inputs[0] + 1) / 2 * (right - left)
            y = top + (1 - inputs[1]) / 2 * (bottom - top)
            canvas.create_oval(x - 2.3, y - 2.3, x + 2.3, y + 2.3,
                               fill=C["cyan"] if target else C["pink"], outline=C["plot"], width=1)
        canvas.create_rectangle(left, top, right, bottom, outline=C["line"])
        for t, text in ((0, "−1"), (0.5, "0"), (1, "+1")):
            canvas.create_text(left + t * (right - left), bottom + 12, text=text, fill=C["muted"], font=("Segoe UI", 7))
        canvas.create_text(15, top + 3, text="+1", fill=C["muted"], font=("Segoe UI", 7))
        canvas.create_text(15, bottom - 3, text="−1", fill=C["muted"], font=("Segoe UI", 7))
        self.map_cache = (canvas.winfo_width(), canvas.winfo_height())

    def draw_probe(self, probability):
        canvas = self.map_canvas
        canvas.delete("probe")
        left, top, right, bottom = self.map_bounds()
        x = left + (self.probe_x.get() + 1) / 2 * (right - left)
        y = top + (1 - self.probe_y.get()) / 2 * (bottom - top)
        canvas.create_oval(x - 7, y - 7, x + 7, y + 7, outline=C["text"], width=2, tags="probe")
        canvas.create_line(x - 11, y, x + 11, y, fill=C["text"], tags="probe")
        canvas.create_line(x, y - 11, x, y + 11, fill=C["text"], tags="probe")
        predicted = int(probability >= 0.5)
        expected = target_for(self.dataset_name.get(), self.probe_x.get(), self.probe_y.get())
        self.map_caption.configure(text="Probe: class %d  ·  expected %d  ·  P(1) %.1f%%" % (predicted, expected, probability * 100))

    def pick_point(self, event):
        left, top, right, bottom = self.map_bounds()
        if right <= left or bottom <= top:
            return
        self.follow.set(False)
        self.probe_x.set(round(max(-1, min(1, 2 * (event.x - left) / (right - left) - 1)), 2))
        self.probe_y.set(round(max(-1, min(1, 1 - 2 * (event.y - top) / (bottom - top))), 2))

    def draw_loss(self):
        canvas = self.loss_canvas
        canvas.delete("all")
        w, h = max(180, canvas.winfo_width()), max(100, canvas.winfo_height())
        left, top, right, bottom = 43, 14, w - 20, h - 24
        peak = max(0.25, max((point[1] for point in self.history), default=1) * 1.15)
        for i in range(4):
            value = peak * i / 3
            y = bottom - i / 3 * (bottom - top)
            canvas.create_line(left, y, right, y, fill=C["line"], dash=(2, 5))
            canvas.create_text(left - 7, y, text="%.2f" % value, fill=C["muted"], font=("Segoe UI", 7), anchor="e")
        if not self.history:
            return
        start, end = self.history[0][0], self.history[-1][0]
        points = [(left + (step - start) / max(1, end - start) * (right - left),
                   bottom - value / peak * (bottom - top)) for step, value in self.history]
        if len(points) > 1:
            area = [(points[0][0], bottom)] + points + [(points[-1][0], bottom)]
            canvas.create_polygon(*[v for point in area for v in point], fill="#173440", outline="")
            canvas.create_line(*[v for point in points for v in point], fill=C["cyan"], width=2, smooth=False)
        x, y = points[-1]
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=C["cyan"], outline="")
        canvas.create_text(left, bottom + 14, text=str(start), anchor="w", fill=C["muted"], font=("Segoe UI", 7))
        canvas.create_text(right, bottom + 14, text="%d updates" % end, anchor="e", fill=C["muted"], font=("Segoe UI", 7))

    def save_session(self):
        from tkinter import filedialog, messagebox
        if self.dialog_open:
            return
        self.dialog_open = True
        try:
            path = filedialog.asksaveasfilename(parent=self.root, title="Save neural network session",
                                               defaultextension=".json", initialfile="unified_%s_session.json" % self.dataset_name.get().lower(),
                                               filetypes=[("Neural engine session", "*.json")])
            if path:
                write_session(path, self.dataset_name.get(), self.model, self.rate.get())
                self.set_status("Saved session · %s" % Path(path).name)
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Could not save session", str(exc), parent=self.root)
        finally:
            self.dialog_open = False

    def load_session(self):
        from tkinter import filedialog, messagebox
        if self.dialog_open:
            return
        self.dialog_open = True
        try:
            path = filedialog.askopenfilename(parent=self.root, title="Open neural network session",
                                              filetypes=[("Neural engine session", "*.json")])
            if path:
                name, model, rate = read_session(path)
                self.model = model
                self.dataset_name.set(name)
                self.topology_name.set(next(key for key, value in TOPOLOGIES.items() if value == model.layers))
                self.rate.set(rate)
                self.rate_label.configure(text="%.3f" % rate)
                self.set_data(name)
                self.update_description()
                self.history = []
                self.rng = random.Random(123)
                self.selected = (3, 0)
                self.network_cache = self.map_cache = None
                self.last_metrics = self.last_map = 0.0
                self.refresh_metrics()
                self.set_running(False)
                self.set_status("Session loaded · press Resume to continue learning.")
        except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
            messagebox.showerror("Could not open session", str(exc), parent=self.root)
        finally:
            self.dialog_open = False

    def close(self):
        self.closed = True
        if self.next_tick is not None:
            self.root.after_cancel(self.next_tick)
        self.root.destroy()


def run_self_tests():
    """Deterministic checks for learning, gradients, persistence and legacy bounds."""
    import unittest

    class EngineTests(unittest.TestCase):
        def test_bit_transform(self):
            core = EthicalSubstrate()
            self.assertEqual(core.cast_virtue_bit_array([1, 0, 5, 1], True), [1, 0, 1])
            self.assertEqual(core.cast_virtue_bit_array([1, 0, 1], False), [0, 1, 0])

        def test_matrix_boundaries(self):
            for width in (4, 5, 9, 17, 62):
                for height in (3, 6, 16):
                    engine = StructuralMatrixEngine(width, height)
                    engine.compute_frame(EthicalSubstrate(), [0, 1])
                    self.assertTrue(all(row[0] == row[-1] == "#" for row in engine.buffer))
                    self.assertTrue(all(ch == "#" for ch in engine.buffer[0] + engine.buffer[-1]))
                    engine.compute_frame(EthicalSubstrate(), [])
            with self.assertRaises(ValueError):
                StructuralMatrixEngine(1, 0)

        def test_learning(self):
            for name in DATASETS:
                net, rng = NeuralNetwork(), random.Random(123)
                data = make_dataset(name)
                initial, _ = net.evaluate(data)
                for _ in range(800):
                    net.train_batch(rng.sample(data, 24))
                loss, accuracy = net.evaluate(data)
                _, validation = net.evaluate(make_dataset(name, 96, 909))
                self.assertLess(loss, initial * 0.4, name)
                self.assertGreater(accuracy, 0.90, name)
                self.assertGreater(validation, 0.85, name)

        def test_gradient(self):
            net = NeuralNetwork()
            inputs, label = [0.4, -0.7], 1
            old = net.weights[0][0][0]
            epsilon, rate = 1e-5, 0.05
            net.weights[0][0][0] = old + epsilon
            plus = -math.log(net.predict(inputs))
            net.weights[0][0][0] = old - epsilon
            minus = -math.log(net.predict(inputs))
            net.weights[0][0][0] = old
            expected = (plus - minus) / (2 * epsilon) + 0.0001 * old
            net.train_batch([(inputs, label)], rate)
            observed = (old - net.weights[0][0][0]) / rate
            self.assertAlmostEqual(expected, observed, places=7)

        def test_session_roundtrip_and_continuation(self):
            net = NeuralNetwork()
            data = make_dataset("XOR", 24)
            net.train_batch(data)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "session.json"
                write_session(path, "XOR", net, 0.08)
                name, restored, rate = read_session(path)
                self.assertEqual(name, "XOR")
                self.assertEqual(rate, 0.08)
                self.assertEqual(net.to_dict(), restored.to_dict())
                net.train_batch(data)
                restored.train_batch(data)
                self.assertEqual(net.to_dict(), restored.to_dict())

        def test_invalid_sessions(self):
            import copy
            baseline = NeuralNetwork().to_dict()
            for value in (float("nan"), float("inf"), 1001, "bad", True):
                bad = copy.deepcopy(baseline)
                bad["weights"][0][0][0] = value
                with self.assertRaises(ValueError):
                    NeuralNetwork.from_dict(bad)
            for bad in ({}, {"layers": [2, 9999999, 1]}, None):
                with self.assertRaises(ValueError):
                    NeuralNetwork.from_dict(bad)
            self.assertEqual(sigmoid(10000), 1.0)
            self.assertGreaterEqual(sigmoid(-10000), 0.0)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EngineTests)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


def run_desktop(smoke_test=False):
    try:
        import tkinter as tk
    except ImportError:
        print("Tkinter is required for the desktop interface. Install Python with Tcl/Tk support.\n"
              "The --console option works without Tkinter.", file=sys.stderr)
        return 1
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Cannot open the desktop interface: %s\nUse --console on a machine without a display." % exc,
              file=sys.stderr)
        return 1
    app = NeuralEngineApp(root)
    failures = []
    if smoke_test:
        def exercise():
            try:
                app.set_running(False)
                before = app.model.updates
                app.step_button.invoke()
                assert app.model.updates == before + 1
                app.follow.set(False)
                app.probe_x.set(0.6)
                app.probe_y.set(-0.6)
                app.draw_network(app.model.forward([0.6, -0.6]), time.perf_counter())
                app.draw_map()
                app.draw_probe(app.model.predict([0.6, -0.6]))
                for name in DATASETS:
                    app.dataset_name.set(name)
                    app.change_dataset()
                    app.step()
                for name in TOPOLOGIES:
                    app.topology_name.set(name)
                    app.change_topology()
                    app.draw_network(app.model.forward([0, 0]), time.perf_counter())
                app.root.geometry("1080x760")
                app.root.update_idletasks()
                app.draw_map()
                assert app.network_canvas.winfo_width() > 400
                assert app.map_canvas.winfo_height() > 100
                print("GUI smoke test passed: training, step, probe, datasets, topology, resize.")
            except Exception as exc:
                failures.append(str(exc))
                print("GUI smoke test failed:", repr(exc), file=sys.stderr)
            finally:
                app.close()
        root.after(800, exercise)
    root.mainloop()
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=APP_TITLE + " — local interactive neural-network visualisation")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--console", action="store_true", help="render the repaired original text matrix")
    group.add_argument("--self-test", action="store_true", help="test learning and session handling")
    group.add_argument("--smoke-test", action="store_true", help="briefly open and exercise the desktop interface")
    args = parser.parse_args(argv)
    if args.console:
        ProductionPipeline().execute_pipeline_cycle()
        return 0
    if args.self_test:
        return run_self_tests()
    return run_desktop(args.smoke_test)


if __name__ == "__main__":
    raise SystemExit(main())
