"""Godmind Mesh: local neural learning lab. Run with Python 3.10+ and NumPy."""
from __future__ import annotations

import argparse
from collections import deque
import csv
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlparse, parse_qs
import webbrowser

try:
    import numpy as np
except ImportError:
    raise SystemExit("NumPy is required. Install it with: python -m pip install -r requirements.txt")

from module2 import TotalBitRealityEngine, ARCHITECTURE
from module3 import DASHBOARD, DesertSubstrateAnalysis
from original_logic import report as original_logic_report, console_readout

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mesh_inputs", ROOT / "module 1.py")
inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs)
Filter = inputs.StructuralIdentityFilter
GRID_SIZE = 41
axis = np.linspace(-1, 1, GRID_SIZE)
gx, gy = np.meshgrid(axis, axis)
GRID = np.column_stack((gx.ravel(), gy.ravel()))


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RecursiveDrillEngine:
    """Own training, active queries, held-out evaluation and resumable state."""

    def __init__(self, dataset="moons", seed=42, checkpoint_path=None):
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.worker = None
        self.checkpoint_path = Path(checkpoint_path or ROOT / "models" / "latest.json")
        self.last_saved = None
        self.reset(dataset, seed)

    def log(self, text):
        self.events.appendleft({"time": utc_now(), "text": text})

    def reset(self, dataset="moons", seed=42):
        keep_custom = dataset == "custom" and getattr(self, "dataset", None) == "custom"
        if dataset not in inputs.DATASETS and not keep_custom:
            raise ValueError("Unknown dataset.")
        if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
            raise ValueError("Seed must be an integer from 0 to 4294967295.")
        self.running = False
        self.dataset, self.seed = dataset, seed
        self.rng = np.random.default_rng(seed)
        self.model = TotalBitRealityEngine(seed)
        if not keep_custom:
            self.train_x, self.train_y = inputs.make_dataset(dataset, 160, self.rng)
            self.test_x, self.test_y = inputs.make_dataset(dataset, 400, self.rng)
            self.pool_x, self.pool_y = inputs.make_dataset(dataset, 640, self.rng)
        self.active = False
        self.speed = 4
        self.queried = 0
        self.last_error = None
        self.history = deque(maxlen=300)
        self.events = deque(maxlen=12)
        self.log(f"{dataset.title()} ready. {len(self.train_x)} training examples, {len(self.test_x)} held out.")
        self.record_metrics()

    def record_metrics(self):
        train = self.model.evaluate(self.train_x, self.train_y)
        test = self.model.evaluate(self.test_x, self.test_y)
        self.metrics = {"train_loss": train["loss"], "test_loss": test["loss"],
                        "train_accuracy": train["accuracy"], "test_accuracy": test["accuracy"]}
        record = {"step": self.model.steps, **self.metrics}
        if self.history and self.history[-1]["step"] == self.model.steps:
            self.history[-1] = record
        else:
            self.history.append(record)

    def reveal(self, count=16):
        count = min(count, len(self.pool_x), inputs.MAX_SAMPLES - len(self.train_x))
        if count <= 0:
            return 0
        uncertainty = np.abs(self.model.predict(self.pool_x).ravel() - 0.5)
        chosen = np.argsort(uncertainty, kind="stable")[:count]
        self.train_x = np.concatenate((self.train_x, self.pool_x[chosen]))
        self.train_y = np.concatenate((self.train_y, self.pool_y[chosen]))
        self.pool_x = np.delete(self.pool_x, chosen, axis=0)
        self.pool_y = np.delete(self.pool_y, chosen, axis=0)
        self.queried += count
        self.log(f"Teacher labeled {count} uncertain examples from the training pool.")
        return count

    def train_steps(self, count):
        for _ in range(count):
            self.model.train_batch(self.train_x, self.train_y)
            if self.active and self.model.steps % 80 == 0:
                self.reveal()
            if self.model.steps % 10 == 0:
                self.record_metrics()

    def start_worker(self):
        if self.worker and self.worker.is_alive():
            return
        def run():
            while not self.stop_event.wait(0.04):
                with self.lock:
                    if self.running:
                        try:
                            self.train_steps(self.speed)
                        except Exception as error:
                            self.running = False
                            self.last_error = str(error)
                            self.log(f"Training paused: {error}")
        self.worker = threading.Thread(target=run, name="mesh-training", daemon=True)
        self.worker.start()

    def close(self):
        self.stop_event.set()
        if self.worker:
            self.worker.join(timeout=3)

    def execute_complete_synthesis_loop(self):
        """Compatibility entry point now returns measured model performance."""
        with self.lock:
            self.record_metrics()
            return {"steps": self.model.steps, "running": self.running, **self.metrics}

    def snapshot(self, probe=(0.25, 0.25)):
        with self.lock:
            prediction, activations, _ = self.model.forward([probe])
            return {"dataset": self.dataset, "seed": self.seed, "running": self.running,
                    "steps": self.model.steps, "learning_rate": self.model.learning_rate,
                    "speed": self.speed, "active": self.active, "queried": self.queried,
                    "train_count": len(self.train_x), "test_count": len(self.test_x),
                    "pool_count": len(self.pool_x), "metrics": self.metrics,
                    "history": list(self.history), "events": list(self.events),
                    "points": np.column_stack((self.train_x, self.train_y)).round(5).tolist(),
                    "grid": self.model.predict(GRID).ravel().round(5).tolist(),
                    "grid_size": GRID_SIZE, "architecture": ARCHITECTURE,
                    "weights": [w.round(4).tolist() for w in self.model.weights],
                    "activations": [a.ravel().round(5).tolist() for a in activations],
                    "probe": {"x": probe[0], "y": probe[1], "probability": float(prediction[0, 0])},
                    "last_error": self.last_error, "last_saved": self.last_saved,
                    "can_restore": self.checkpoint_path.is_file(),
                    "analysis": DesertSubstrateAnalysis().describe(self.metrics, len(self.train_x))}

    def checkpoint(self):
        with self.lock:
            self.record_metrics()
            return {"format": "godmind-mesh", "version": 1, "created": utc_now(),
                    "dataset": self.dataset, "seed": self.seed, "model": self.model.to_dict(),
                    "train_x": self.train_x.tolist(), "train_y": self.train_y.tolist(),
                    "test_x": self.test_x.tolist(), "test_y": self.test_y.tolist(),
                    "pool_x": self.pool_x.tolist(), "pool_y": self.pool_y.tolist(),
                    "active": self.active, "speed": self.speed, "queried": self.queried,
                    "rng": self.rng.bit_generator.state, "history": list(self.history)}

    def save(self):
        payload = json.dumps(self.checkpoint(), allow_nan=False)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.checkpoint_path.with_suffix(".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self.checkpoint_path)
        self.last_saved = utc_now()
        self.log("Checkpoint saved: weights, optimizer, examples and history.")

    def load(self, data):
        """Validate a whole checkpoint before changing any live state."""
        if not isinstance(data, dict) or data.get("format") != "godmind-mesh" or data.get("version") != 1:
            raise ValueError("Choose a Godmind Mesh version 1 JSON checkpoint.")
        model = TotalBitRealityEngine.from_dict(data.get("model"))
        arrays = {}
        for prefix in ("train", "test", "pool"):
            x = np.asarray(data.get(prefix + "_x"), dtype=float)
            y = np.asarray(data.get(prefix + "_y"), dtype=float)
            if prefix == "pool" and x.size == 0 and y.size == 0:
                x, y = np.empty((0, 2)), np.empty((0, 1))
            if x.ndim != 2 or x.shape[1] != 2 or y.shape != (len(x), 1):
                raise ValueError(f"Invalid {prefix} example shapes.")
            if len(x) > inputs.MAX_SAMPLES or (prefix != "pool" and len(x) < 2):
                raise ValueError(f"Invalid {prefix} example count.")
            if not np.isfinite(x).all() or (np.abs(x) > 1).any() or not np.isin(y, [0, 1]).all():
                raise ValueError(f"Invalid {prefix} coordinates or labels.")
            arrays[prefix + "_x"], arrays[prefix + "_y"] = x, y
        train_keys = set(map(tuple, arrays["train_x"]))
        test_keys = set(map(tuple, arrays["test_x"]))
        pool_keys = set(map(tuple, arrays["pool_x"]))
        if train_keys & test_keys or pool_keys & (train_keys | test_keys):
            raise ValueError("Training, test and pool examples must be separate.")
        dataset, seed = data.get("dataset"), data.get("seed")
        if dataset not in (*inputs.DATASETS, "custom") or type(seed) is not int or seed != model.seed:
            raise ValueError("Invalid dataset or seed.")
        speed, active, queried = data.get("speed"), data.get("active"), data.get("queried")
        if type(speed) is not int or speed not in (1, 4, 12) or type(active) is not bool:
            raise ValueError("Invalid training controls.")
        if type(queried) is not int or not 0 <= queried <= inputs.MAX_SAMPLES:
            raise ValueError("Invalid active-learning count.")
        rng = np.random.default_rng()
        try:
            rng.bit_generator.state = data["rng"]
        except (ValueError, TypeError, KeyError):
            raise ValueError("Invalid data random state.") from None
        history = data.get("history", [])
        if not isinstance(history, list) or len(history) > 300:
            raise ValueError("Invalid history.")
        previous = -1
        for entry in history:
            if not isinstance(entry, dict) or type(entry.get("step")) is not int or not previous <= entry["step"] <= model.steps:
                raise ValueError("Invalid history steps.")
            previous = entry["step"]
            for key in ("train_loss", "test_loss", "train_accuracy", "test_accuracy"):
                Filter.number(entry.get(key), key, 0, 1 if "accuracy" in key else 1e6)
        with self.lock:
            self.running = False
            self.model, self.rng = model, rng
            for key, value in arrays.items():
                setattr(self, key, value)
            self.dataset, self.seed = dataset, seed
            self.speed, self.active, self.queried = speed, active, queried
            self.history = deque(history, maxlen=300)
            self.last_error = None
            self.record_metrics()
            self.log("Checkpoint restored. Press Start learning to continue.")

    def command(self, action, data):
        with self.lock:
            if action == "start":
                self.running = True
                self.last_error = None
            elif action == "pause":
                self.running = False
                self.record_metrics()
            elif action == "step":
                self.running = False
                self.train_steps(1)
                self.record_metrics()
            elif action == "reset":
                self.reset(data.get("dataset", "moons"), data.get("seed", 42))
            elif action == "configure":
                rate = Filter.number(data.get("learning_rate", self.model.learning_rate), "Learning rate", 0.0001, 0.1)
                speed, active = data.get("speed", self.speed), data.get("active", self.active)
                if type(speed) is not int or speed not in (1, 4, 12) or type(active) is not bool:
                    raise ValueError("Invalid speed or active learning setting.")
                self.model.learning_rate, self.speed, self.active = rate, speed, active
            elif action == "sample":
                point, label = Filter.sample(data)
                if len(self.train_x) >= inputs.MAX_SAMPLES:
                    raise ValueError("The training set is full (4000 examples).")
                for rows in (self.train_x, self.test_x, self.pool_x):
                    if len(rows) and np.any(np.all(np.isclose(rows, point, atol=1e-7, rtol=0), axis=1)):
                        raise ValueError("This point already exists; choose a different location.")
                self.train_x = np.vstack((self.train_x, point))
                self.train_y = np.vstack((self.train_y, [[label]]))
                self.record_metrics()
                self.log(f"Your example added: ({point[0]:+.2f}, {point[1]:+.2f}), class {label}.")
            elif action == "reveal":
                if not self.reveal():
                    raise ValueError("No more teacher examples are available in this dataset.")
                self.record_metrics()
            elif action == "import":
                x, y = inputs.read_csv(data.get("csv"))
                rng = np.random.default_rng(self.seed)
                train_x, train_y, test_x, test_y = inputs.split_data(x, y, rng)
                self.running = False
                self.dataset = "custom"
                self.model = TotalBitRealityEngine(self.seed)
                self.train_x, self.train_y, self.test_x, self.test_y = train_x, train_y, test_x, test_y
                self.pool_x, self.pool_y = np.empty((0, 2)), np.empty((0, 1))
                self.rng, self.active, self.queried = rng, False, 0
                self.history.clear()
                self.last_error = None
                self.record_metrics()
                self.log(f"CSV imported: {len(train_x)} train / {len(test_x)} held out. Model reset.")
            elif action == "save":
                self.save()
            elif action == "restore":
                if not self.checkpoint_path.is_file():
                    raise ValueError("Save a checkpoint first.")
                self.load(json.loads(self.checkpoint_path.read_text(encoding="utf-8")))
            elif action == "load":
                self.load(data.get("checkpoint"))
            else:
                raise ValueError("Unknown command.")


def make_handler(engine, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return  # Keep the launcher readable; failures are returned in the UI.

        def send_bytes(self, status, content, content_type, filename=None):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def json_response(self, status, data):
            self.send_bytes(status, json.dumps(data, allow_nan=False).encode(), "application/json; charset=utf-8")

        def local_request(self):
            port = self.server.server_port
            allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
            origin = self.headers.get("Origin")
            return self.headers.get("Host") in allowed and (origin is None or origin in {f"http://{h}" for h in allowed})

        def do_GET(self):
            if not self.local_request():
                self.json_response(403, {"error": "Only this local dashboard can access the lab."})
                return
            path = urlparse(self.path).path
            if path == "/":
                self.send_bytes(200, DASHBOARD.replace("__MESH_TOKEN__", token).encode(), "text/html; charset=utf-8")
            elif path == "/api/original-logic":
                self.json_response(200, original_logic_report())
            elif path == "/api/state":
                try:
                    query = parse_qs(urlparse(self.path).query)
                    x = Filter.number(float(query.get("x", [0.25])[0]), "x", -1, 1)
                    y = Filter.number(float(query.get("y", [0.25])[0]), "y", -1, 1)
                    self.json_response(200, engine.snapshot((x, y)))
                except (ValueError, TypeError):
                    self.json_response(400, {"error": "Probe coordinates must be between -1 and 1."})
            elif path == "/api/checkpoint":
                self.send_bytes(200, json.dumps(engine.checkpoint(), allow_nan=False).encode(), "application/json", "godmind-mesh.json")
            elif path == "/api/examples":
                stream = io.StringIO(newline="")
                writer = csv.writer(stream)
                writer.writerow(["x", "y", "label"])
                with engine.lock:
                    for point, label in zip(engine.train_x, engine.train_y):
                        writer.writerow([float(point[0]), float(point[1]), int(label[0])])
                self.send_bytes(200, stream.getvalue().encode(), "text/csv; charset=utf-8", "mesh-training-examples.csv")
            elif path == "/favicon.ico":
                self.send_bytes(204, b"", "image/x-icon")
            else:
                self.json_response(404, {"error": "Not found."})

        def do_POST(self):
            if not self.local_request() or not secrets.compare_digest(self.headers.get("X-Mesh-Token", ""), token):
                self.json_response(403, {"error": "Refresh the local dashboard to reconnect."})
                return
            if self.path not in ("/api/control", "/api/probe"):
                self.json_response(404, {"error": "Not found."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    raise ValueError("Request must be between 1 byte and 2 MB.")
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Use application/json.")
                self.connection.settimeout(5)
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Expected a JSON object.")
                if self.path == "/api/probe":
                    x = Filter.number(data.get("x"), "x", -1, 1)
                    y = Filter.number(data.get("y"), "y", -1, 1)
                    with engine.lock:
                        probability, activations, _ = engine.model.forward([[x, y]])
                    self.json_response(200, {"probe": {"x": x, "y": y, "probability": float(probability[0, 0])},
                                              "activations": [a.ravel().tolist() for a in activations]})
                else:
                    engine.command(data.get("action"), data)
                    self.json_response(200, {"ok": True})
            except (ValueError, TypeError, KeyError, OverflowError) as error:
                self.json_response(400, {"error": str(error) or "Invalid input."})
            except OSError as error:
                self.json_response(503, {"error": f"Could not access the local file or connection: {error}"})

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Godmind Mesh — a live local neural learning lab")
    parser.add_argument("--port", type=int, default=8876)
    parser.add_argument("--headless", action="store_true", help="Do not open a browser automatically")
    parser.add_argument("--dataset", choices=inputs.DATASETS, default="moons")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--restore", action="store_true", help="Restore models/latest.json, paused")
    parser.add_argument("--demo-steps", type=int, default=0, help="Train this many batches, print metrics, then exit")
    parser.add_argument("--original-logic", action="store_true", help="Print the four preserved original reports, then exit")
    args = parser.parse_args()
    if args.original_logic:
        print(console_readout(), end="")
        return
    if not 1 <= args.port <= 65535 or not 0 <= args.seed <= 2**32 - 1 or not 0 <= args.demo_steps <= 100000:
        parser.error("Invalid port, seed or demo step count.")
    engine = RecursiveDrillEngine(args.dataset, args.seed)
    if args.restore:
        try:
            engine.command("restore", {})
        except (ValueError, OSError) as error:
            parser.error(str(error))
    if args.demo_steps:
        before = engine.execute_complete_synthesis_loop()
        engine.train_steps(args.demo_steps)
        print(json.dumps({"before": before, "after": engine.execute_complete_synthesis_loop()}, indent=2))
        return
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(engine, secrets.token_urlsafe(32)))
        server.daemon_threads = True
    except OSError as error:
        raise SystemExit(f"Cannot open local port {args.port}: {error}\nTry --port {args.port + 1}.") from None
    engine.start_worker()
    url = f"http://127.0.0.1:{args.port}"
    print(f"\nGODMIND MESH | Neural learning lab\n{url}\n")
    print("Keep this window open. Press Ctrl+C to stop. Save a checkpoint before closing.")
    if not args.headless:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\nClosing the neural lab.")
    finally:
        engine.close()
        server.server_close()


if __name__ == "__main__":
    main()
