#!/usr/bin/env python3
"""Carrier Lab: 7.83 Hz paced OS-random bits, graphics, and local Ollama analysis.

Python 3.10+, standard library only. Run: python carrier_lab.py
A mathematical carrier supplies timing, NOT entropy. secrets.token_bytes uses
the OS CSPRNG; this software does not claim a hardware true-random source.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import math
import secrets
import sys
import threading
import time
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

FREQUENCY = 7.83
MAX_BITS = 262_144
SOURCE = "OS cryptographic random generator (Python secrets.token_bytes)"
LIMITATION = (
    "The 7.83 Hz carrier is a deterministic mathematical reference and batch clock, "
    "not an entropy source or a measurement of a physical field. The operating system "
    "supplies cryptographic randomness. Neither statistical tests nor an LLM can "
    "certify physical true randomness from a bit string."
)
BYTE_BITS = tuple(f"{i:08b}" for i in range(256))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def random_bits(count):
    """Unbiased extraction, preserving leading zeroes and exact requested length."""
    if type(count) is not int or not 1 <= count <= MAX_BITS:
        raise ValueError(f"Bit count must be an integer from 1 to {MAX_BITS:,}.")
    return "".join(BYTE_BITS[b] for b in secrets.token_bytes((count + 7) // 8))[:count]


def pack_bits(bits):
    """MSB first, zero-pad only the last byte; retain bit_count in metadata."""
    return bytes(int(bits[i:i + 8].ljust(8, "0"), 2) for i in range(0, len(bits), 8))


def statistics(bits):
    """Descriptive checks, not a randomness certification or a NIST test suite."""
    n = len(bits)
    if not n:
        return {"n": 0, "ones": 0, "zeros": 0, "ones_fraction": None,
                "marginal_entropy": None, "monobit_p": None, "runs": 0,
                "runs_z": None, "longest_run": 0, "lag1_correlation": None,
                "byte_histogram": [0] * 256, "window_balance": [],
                "window_size": 256, "cumulative_balance": []}
    ones = bits.count("1")
    zeros = n - ones
    p = ones / n
    entropy = -sum(x * math.log2(x) for x in (p, 1 - p) if x > 0)
    transitions = 0
    longest = run = 1
    pairs11 = 0
    for a, b in zip(bits, bits[1:]):
        pairs11 += a == b == "1"
        if a == b:
            run += 1
        else:
            transitions += 1
            longest = max(longest, run)
            run = 1
    longest = max(longest, run)
    runs = transitions + 1
    expected_runs = 1 + 2 * ones * zeros / n
    variance = (2 * ones * zeros * (2 * ones * zeros - n) /
                (n * n * (n - 1))) if n > 1 else 0
    runs_z = (runs - expected_runs) / math.sqrt(variance) if (
        n >= 128 and ones >= 10 and zeros >= 10 and variance > 0) else None
    m = n - 1
    sx, sy = ones - (bits[-1] == "1"), ones - (bits[0] == "1")
    denominator = math.sqrt(sx * (m - sx) * sy * (m - sy)) if m else 0
    correlation = (m * pairs11 - sx * sy) / denominator if denominator else None
    window_size = max(256, math.ceil(n / 128 / 256) * 256)
    balances, cumulative = [], []
    total_ones = 0
    for i in range(0, n, window_size):
        chunk = bits[i:i + window_size]
        total_ones += chunk.count("1")
        balances.append(chunk.count("1") / len(chunk))
        cumulative.append(total_ones / (i + len(chunk)))
    histogram = Counter(int(bits[i:i + 8], 2) for i in range(0, n - 7, 8))
    return {"n": n, "ones": ones, "zeros": zeros, "ones_fraction": p,
            "marginal_entropy": entropy,
            "monobit_p": math.erfc(abs(ones - zeros) / math.sqrt(2 * n)) if n >= 128 else None,
            "runs": runs, "runs_z": runs_z, "longest_run": longest,
            "lag1_correlation": correlation,
            "byte_histogram": [histogram[i] for i in range(256)],
            "window_balance": balances, "window_size": window_size,
            "cumulative_balance": cumulative}


class CarrierEngine:
    """One fresh batch per software carrier cycle; no reseeding or bit filtering."""

    def __init__(self):
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.worker = None
        self.chunks = []
        self.count = 0
        self.target = 8192
        self.batch_size = 256
        self.status = "idle"
        self.session_id = ""
        self.started_at = None
        self.finished_at = None
        self.started_clock = 0.0
        self.elapsed = 0.0
        self.cycles = 0
        self.lateness_ms = 0.0
        self.error = None
        self.version = 0
        self.cache = None

    def start(self, count, batch_size):
        if type(count) is not int or not 128 <= count <= MAX_BITS:
            raise ValueError(f"Choose between 128 and {MAX_BITS:,} bits.")
        if type(batch_size) is not int or batch_size not in (32, 128, 256, 512, 1024):
            raise ValueError("Choose a supported batch size.")
        with self.lock:
            if self.worker and self.worker.is_alive():
                raise ValueError("Stop the current capture before starting another.")
            self.chunks, self.count, self.cycles = [], 0, 0
            self.target, self.batch_size = count, batch_size
            self.session_id = secrets.token_hex(6)
            self.started_at, self.finished_at = utc_now(), None
            self.started_clock, self.elapsed = time.perf_counter(), 0.0
            self.lateness_ms, self.error = 0.0, None
            self.status, self.cache = "running", None
            self.version += 1
            self.stop_event.clear()
            self.worker = threading.Thread(target=self._capture, daemon=True)
            self.worker.start()

    def _capture(self):
        period = 1 / FREQUENCY
        deadline = self.started_clock + period
        try:
            while not self.stop_event.wait(max(0.0, deadline - time.perf_counter())):
                now = time.perf_counter()
                with self.lock:
                    size = min(self.batch_size, self.target - self.count)
                chunk = random_bits(size)
                with self.lock:
                    if self.stop_event.is_set():
                        break
                    self.chunks.append(chunk)
                    self.count += size
                    self.cycles += 1
                    self.lateness_ms = max(self.lateness_ms, (now - deadline) * 1000)
                    self.version += 1
                    if self.count >= self.target:
                        self.status = "complete"
                        break
                # Skip missed clock ticks instead of generating catch-up bursts.
                deadline += period
                if deadline <= time.perf_counter():
                    deadline += (math.floor((time.perf_counter() - deadline) / period) + 1) * period
        except Exception as exc:
            with self.lock:
                self.status, self.error = "error", str(exc)
        finally:
            with self.lock:
                if self.status == "running":
                    self.status = "stopped"
                self.elapsed = time.perf_counter() - self.started_clock
                self.finished_at = utc_now()
                self.version += 1

    def stop(self):
        self.stop_event.set()
        if self.worker and self.worker is not threading.current_thread():
            self.worker.join(timeout=2)

    def snapshot(self, include_bits=False):
        with self.lock:
            bits = "".join(self.chunks)
            version = self.version
            cached = self.cache if self.cache and self.cache[0] == version else None
            data = {"status": self.status, "session_id": self.session_id,
                    "target": self.target, "batch_size": self.batch_size,
                    "started_at": self.started_at, "finished_at": self.finished_at,
                    "elapsed": time.perf_counter() - self.started_clock if self.status == "running" else self.elapsed,
                    "cycles": self.cycles, "max_lateness_ms": self.lateness_ms,
                    "error": self.error, "frequency_hz": FREQUENCY, "source": SOURCE,
                    "limitation": LIMITATION, "preview": bits[-2048:]}
        stats = cached[1] if cached else statistics(bits)
        with self.lock:
            if self.version == version:
                self.cache = (version, stats)
        data["stats"] = stats
        if include_bits:
            data["bits"] = bits
            data["sha256_packed"] = hashlib.sha256(pack_bits(bits)).hexdigest()
            data["packing"] = "MSB first, final byte padded with zeroes; stats.n is the exact bit length"
        return data


class OllamaClient:
    def __init__(self, port=11434):
        self.port = port

    def request(self, method, path, payload=None, timeout=5):
        # Direct loopback HTTP: no proxy environment, redirects, remote host or API key.
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        try:
            body = json.dumps(payload).encode() if payload is not None else None
            conn.request(method, path, body=body, headers={"Content-Type": "application/json"})
            response = conn.getresponse()
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("Ollama returned an unexpectedly large response.")
            result = json.loads(raw)
            if response.status != 200:
                raise ValueError(str(result.get("error", f"Ollama HTTP {response.status}")))
            if not isinstance(result, dict):
                raise ValueError("Unexpected Ollama response.")
            return result
        except (OSError, http.client.HTTPException) as exc:
            raise ValueError(f"Cannot reach local Ollama on port {self.port}. Start Ollama and retry. ({exc})") from exc
        finally:
            conn.close()

    def models(self):
        models = self.request("GET", "/api/tags").get("models", [])
        # Ollama can also expose cloud models; this app only offers on-device models.
        local = [m["name"] for m in models if isinstance(m, dict) and m.get("name")
                 and "cloud" not in m["name"].lower()
                 and not m.get("remote_host") and not m.get("remote_model")]
        return sorted(local, key=lambda name: ("llama" not in name.lower(), name.lower()))

    def analyze(self, model, capture):
        if model not in self.models():
            raise ValueError("Select an installed, local Ollama model and refresh the model list.")
        summary = {key: capture[key] for key in ("session_id", "frequency_hz", "source", "limitation")}
        summary["stats"] = capture["stats"]
        summary["sample_first_1024_bits"] = capture["bits"][:1024]
        summary["sample_is_truncated"] = len(capture["bits"]) > 1024
        system = (
            "You are a careful statistics assistant in a local randomness lab. Interpret ONLY the supplied "
            "measurements; do not invent tests, p-values, physical signals, hidden messages or patterns. "
            "The bits come from the OS cryptographic RNG. A deterministic 7.83 Hz sine wave clocks batches "
            "and contributes no entropy. Marginal binary entropy near 1 describes balance, not independence. "
            "monobit_p is a normal-approximation two-sided balance check, unavailable below 128 bits. "
            "runs_z is an approximate standardized runs statistic; lag1_correlation is Pearson adjacent-bit "
            "correlation. Values marked null are unavailable. A small p-value can occur by chance. "
            "No statistic or LLM can certify true randomness, cryptographic security, or predict future bits. "
            "Write a concise plain-text report under 220 words with three short sections: Observations, "
            "Limitations, Next check. Use actual supplied numbers, distinguish chance fluctuations from "
            "evidence, and treat the small raw bit excerpt as a sample."
        )
        result = self.request("POST", "/api/chat", {
            "model": model, "stream": False,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": json.dumps(summary)}],
            "options": {"temperature": 0.15, "num_predict": 480, "num_ctx": 8192},
            "keep_alive": "5m",
        }, timeout=180)
        content = result.get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError("Ollama returned an empty report. Try a different local model.")
        return content


class Lab:
    def __init__(self, ollama_port):
        self.engine = CarrierEngine()
        self.ollama = OllamaClient(ollama_port)
        self.lock = threading.RLock()
        self.analysis = {"status": "idle", "text": "", "model": "", "session_id": ""}

    def start(self, count, batch):
        with self.lock:
            if self.analysis["status"] == "running":
                raise ValueError("Wait for the current local analysis to finish.")
            self.engine.start(count, batch)
            self.analysis = {"status": "idle", "text": "", "model": "", "session_id": ""}

    def analyze(self, model):
        with self.lock:
            if self.analysis["status"] == "running":
                raise ValueError("An analysis is already running.")
            capture = self.engine.snapshot(include_bits=True)
            if capture["status"] == "running":
                raise ValueError("Stop or finish the capture before analyzing.")
            if not capture["stats"]["n"]:
                raise ValueError("Generate some bits first.")
            self.analysis = {"status": "running", "text": "", "model": model,
                             "session_id": capture["session_id"]}

            def run():
                try:
                    text = self.ollama.analyze(model, capture)
                    with self.lock:
                        self.analysis.update(status="complete", text=text)
                except Exception as exc:
                    with self.lock:
                        self.analysis.update(status="error", text=str(exc))

            threading.Thread(target=run, daemon=True).start()

    def snapshot(self):
        with self.lock:
            capture = self.engine.snapshot()
            capture["analysis"] = dict(self.analysis)
            return capture


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = sys.platform != "win32"

    def __init__(self, address, lab):
        self.lab, self.token = lab, secrets.token_urlsafe(32)
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "CarrierLab/1.0"

    def log_message(self, *_):
        pass

    def allowed(self):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in hosts and (
            origin is None or origin in {f"http://{host}" for host in hosts})

    def send(self, value, status=200, content_type="application/json; charset=utf-8", filename=None):
        raw = json.dumps(value, allow_nan=False).encode() if isinstance(value, (dict, list)) else value
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; "
                         f"script-src 'nonce-{self.server.token}'; "
                         "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                         "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        if not self.allowed():
            return self.send({"error": "Only the local app origin is allowed."}, 403)
        route = urlsplit(self.path)
        try:
            if route.path == "/":
                return self.send(HTML.replace("__TOKEN__", self.server.token), content_type="text/html; charset=utf-8")
            if route.path == "/favicon.ico":
                return self.send(b"", 204, "image/x-icon")
            if route.path == "/api/state":
                return self.send(self.server.lab.snapshot())
            if route.path == "/api/models":
                return self.send({"models": self.server.lab.ollama.models()})
            if route.path == "/api/export":
                capture = self.server.lab.engine.snapshot(include_bits=True)
                if capture["status"] == "running" or not capture["stats"]["n"]:
                    raise ValueError("Finish a capture before exporting.")
                with self.server.lab.lock:
                    report = dict(self.server.lab.analysis)
                if report["session_id"] == capture["session_id"]:
                    capture["analysis"] = report
                fmt = parse_qs(route.query).get("format", ["json"])[0]
                name = f"carrier-{capture['session_id']}"
                if fmt == "txt":
                    return self.send(capture["bits"] + "\n", content_type="text/plain; charset=utf-8", filename=name + ".txt")
                if fmt == "bin":
                    return self.send(pack_bits(capture["bits"]), content_type="application/octet-stream", filename=name + ".bin")
                if fmt != "json":
                    raise ValueError("Unsupported export format.")
                return self.send(capture, filename=name + ".json")
            return self.send({"error": "Not found"}, 404)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send({"error": str(exc)}, 400)

    def do_POST(self):
        if not self.allowed() or self.headers.get("X-Lab-Token") != self.server.token:
            return self.send({"error": "Only actions from the local app are allowed."}, 403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192:
                raise ValueError("Invalid request size.")
            self.connection.settimeout(5)
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            path = urlsplit(self.path).path
            if path == "/api/start":
                self.server.lab.start(data.get("count"), data.get("batch"))
            elif path == "/api/stop":
                self.server.lab.engine.stop()
            elif path == "/api/analyze":
                model = data.get("model")
                if not isinstance(model, str) or not 1 <= len(model) <= 200:
                    raise ValueError("Select a local model first.")
                self.server.lab.analyze(model)
            else:
                return self.send({"error": "Not found"}, 404)
            return self.send({"ok": True})
        except (ValueError, OSError) as exc:
            return self.send({"error": str(exc)}, 400)


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Carrier Lab · 7.83 Hz</title>
<style>
:root{color-scheme:dark;--bg:#0b1016;--panel:#121a23;--line:#26323e;--muted:#91a2b4;--white:#eff4f8;--mint:#bafa75;--cyan:#67d7ed;--violet:#ac9cff;--orange:#ffbf79}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% 0%,#18313d55,transparent 45%),var(--bg);color:var(--white);font:14px/1.5 'Segoe UI',Arial,sans-serif}button,input,select{font:inherit}button{cursor:pointer}button:disabled{cursor:default;opacity:.4}button,input,select{outline-offset:4px}button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--cyan)}
.wrap{max-width:1490px;margin:auto;padding:0 40px 32px}header{height:88px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.brand{display:flex;gap:12px;align-items:center;font-size:20px;font-weight:650;letter-spacing:-.5px}.brand small{font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;display:block;font-weight:500}.brand svg{width:38px;height:38px}.topright{display:flex;gap:24px;align-items:center}.mono{font-family:Consolas,'Courier New',monospace}.micro{font-size:10px;letter-spacing:1.7px;text-transform:uppercase;color:var(--muted);font-weight:600}.pill{border:1px solid var(--line);padding:7px 12px;border-radius:20px;font-size:11px;color:#cad5df}.dot{width:6px;height:6px;border-radius:50%;background:var(--mint);display:inline-block;margin-right:7px}.dot.off{background:var(--orange)}
.intro{padding:32px 0 27px;display:flex;align-items:flex-end;justify-content:space-between;gap:20px}.intro h1{margin:5px 0 5px;font-size:36px;font-weight:500;letter-spacing:-1.2px}.intro p{margin:0;color:var(--muted);font-size:13px}.reference{font-size:11px;color:var(--muted);text-align:right;max-width:290px}.reference strong{display:block;color:var(--cyan);font-size:12px;font-weight:500}
.layout{display:grid;grid-template-columns:276px minmax(0,1fr);gap:20px;align-items:start}.panel{background:linear-gradient(130deg,#151e28,#111923);border:1px solid var(--line);border-radius:16px;overflow:hidden}.controls{padding:23px}.panel-title{font-size:14px;font-weight:600;display:flex;align-items:center;justify-content:space-between;gap:8px}.panel-title span.sub{font-size:10px;color:var(--muted);font-weight:400;letter-spacing:.8px}.rule{height:1px;background:var(--line);margin:20px 0}.frequency{margin:14px 0 20px;display:flex;align-items:baseline;gap:8px}.frequency b{font-size:52px;line-height:1.1;font-weight:450;letter-spacing:-3px}.frequency span{color:var(--mint);font-size:15px}.frequency small{margin-left:auto;color:var(--muted);font-size:10px}.control-label{display:block;font-size:11px;color:#b6c5d2;margin:17px 0 7px}.control-label .hint{float:right;color:#667c91}input[type=number],select{width:100%;border:1px solid #30404f;border-radius:8px;background:#0d141c;padding:11px 12px;color:var(--white);min-width:0}input[type=number]{font-family:Consolas,monospace;font-size:16px}select{font-size:12px;padding-right:6px}.duration{font-size:11px;color:var(--muted);margin:10px 0 20px}.duration span{color:var(--white)}.primary{border:0;background:var(--mint);color:#16200e;border-radius:9px;font-weight:650;padding:13px 12px;width:100%;display:flex;justify-content:space-between;align-items:center}.primary:hover:enabled{background:#d1ffa0}.secondary{border:1px solid #344557;background:#172331;color:var(--white);border-radius:8px;padding:9px 12px;font-size:12px}.secondary:hover:enabled{border-color:var(--cyan)}.stop{width:100%;margin-top:9px;background:transparent}.model-row{display:flex;gap:8px;align-items:center}.model-row select{flex:1}.refresh{background:transparent;color:var(--cyan);border:1px solid #344557;border-radius:8px;width:37px;height:40px;font-size:19px}.model-help{color:var(--muted);font-size:11px;line-height:1.6;margin:10px 0;overflow-wrap:anywhere}.check{display:flex;align-items:flex-start;font-size:11px;color:#bcc9d5;gap:8px;margin-top:16px}.check input{accent-color:var(--mint);margin:3px 0 0}.source-note{margin-top:16px;padding:17px 20px;border:1px solid #293b35;border-radius:12px;background:#15221960;color:#a7b9aa;font-size:11px;line-height:1.7}.source-note strong{display:block;color:var(--mint);font-size:11px;font-weight:500;margin-bottom:5px}.source-note code{color:#d4dfd6;font-size:10px}.main{min-width:0;display:grid;gap:16px}.scope{padding:20px 22px 16px;position:relative}.scope-head{display:flex;justify-content:space-between;align-items:center}.scope-head .panel-title{gap:10px}.live{color:var(--cyan);font-size:10px;letter-spacing:1px}.live:before{content:'';display:inline-block;width:5px;height:5px;background:var(--cyan);border-radius:50%;margin-right:7px}.scope canvas{display:block;width:100%;height:158px;margin-top:13px}.scope-foot{display:flex;justify-content:space-between;color:var(--muted);font-size:10px;margin:5px 0 13px;gap:12px}.progress{height:3px;background:#293544;border-radius:2px;overflow:hidden}.progress i{display:block;width:0;height:100%;background:var(--mint);transition:width .25s}.capture-line{display:flex;justify-content:space-between;align-items:center;font-size:11px;margin-top:10px}.capture-line span:first-child{color:var(--muted)}.capture-line b{font-weight:400;color:var(--mint)}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.metric{border:1px solid var(--line);border-radius:12px;background:#121a23;padding:16px 18px}.metric .value{font-size:26px;letter-spacing:-1px;margin:6px 0 2px;font-variant-numeric:tabular-nums}.metric .value small{font-size:13px;color:var(--muted);letter-spacing:0}.metric .caption{font-size:10px;color:var(--muted)}.mint{color:var(--mint)}.cyan{color:var(--cyan)}.violet{color:var(--violet)}
.charts{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}.chart{padding:17px 18px}.chart .panel-title{font-size:12px}.chart canvas{width:100%;height:132px;display:block;margin-top:12px}.chart-foot{color:var(--muted);font-size:10px;margin-top:7px;display:flex;justify-content:space-between;gap:4px}.legend{display:flex;gap:10px;font-size:9px;color:var(--muted)}.legend i{display:inline-block;width:6px;height:6px;margin-right:4px;border-radius:1px}.checks{display:flex;gap:0;flex-wrap:wrap;padding:14px 20px;align-items:center;border:1px solid var(--line);border-radius:12px;background:#101822}.check-stat{flex:1;min-width:90px;border-right:1px solid var(--line);padding:0 16px}.check-stat:first-child{padding-left:0}.check-stat:last-child{border:0;padding-right:0}.check-stat span{font-size:10px;color:var(--muted);display:block}.check-stat b{font-size:13px;font-weight:500;font-family:Consolas,monospace}.report{padding:20px 22px}.report-title{display:flex;justify-content:space-between;gap:15px;align-items:center}.report-title h2{font-size:14px;margin:0;font-weight:600}.report-title h2 span{color:var(--violet);margin-right:7px}.report-title p{font-size:10px;color:var(--muted);margin:4px 0 0}.report-body{margin:19px 0 6px;background:#0c131c;border:1px solid #233342;border-radius:10px;padding:18px 20px;white-space:pre-wrap;font-size:12px;line-height:1.8;color:#cfdae4;overflow-wrap:anywhere;min-height:92px}.report-body.empty{color:var(--muted)}.report-state{font-size:10px;color:var(--violet);margin-top:10px}.exports{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.exports span{margin-right:auto;color:var(--muted);font-size:11px}.exports button{padding:7px 13px;font-size:11px;background:transparent}.explain{font-size:10px;color:#8194a6;margin:1px 0 0;line-height:1.65}footer{margin-top:26px;border-top:1px solid var(--line);padding-top:16px;display:flex;justify-content:space-between;font-size:10px;color:#708397;gap:20px}#notice{display:none;margin:0 0 18px;padding:12px 16px;border:1px solid #695337;border-radius:9px;background:#302519;color:#ffd6a4;font-size:12px;overflow-wrap:anywhere}#notice.show{display:block}.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}a{color:var(--cyan)}
@media(max-width:1150px){.wrap{padding:0 24px 24px}.layout{grid-template-columns:250px minmax(0,1fr)}.metric{padding:14px 12px}.metric .value{font-size:23px}.chart{padding:14px 12px}.charts{gap:8px}.metric .micro{font-size:9px;letter-spacing:1px}.legend{gap:5px}.check-stat{padding:0 10px}}
@media(max-width:850px){.layout{grid-template-columns:1fr}.sidebar{display:grid;grid-template-columns:1fr}.controls{display:grid;grid-template-columns:1fr 1fr;gap:0 24px}.controls .rule{grid-column:1/-1}.controls .config-top{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between}.frequency{margin:0}.frequency b{font-size:37px}.source-note{margin-bottom:0}.reference{display:none}.intro h1{font-size:30px}.topright .micro{display:none}.check{margin-top:11px}.model-section{grid-column:2;grid-row:2}.generation-section{grid-column:1;grid-row:2}.controls>.rule{display:none}.main{margin-top:0}}
@media(max-width:560px){.wrap{padding:0 16px 20px}header{height:72px}.brand{font-size:17px}.topright{gap:0}.pill{font-size:9px;padding:6px 8px}.intro{padding:24px 0 22px}.intro h1{font-size:29px}.intro p{font-size:12px}.controls{padding:18px;gap:0 16px}.frequency b{font-size:30px}.frequency small{display:none}.controls .config-top{margin-bottom:7px}.charts{grid-template-columns:1fr}.chart canvas{height:150px}.metrics{grid-template-columns:1fr 1fr}.checks{row-gap:14px}.check-stat{flex-basis:40%;border-right:0;padding:0}.scope{padding:17px}.scope-foot{font-size:9px}.report{padding:17px}.report-title{align-items:flex-start}.report-title .secondary{font-size:11px;white-space:nowrap}.exports span{width:100%}footer{flex-direction:column;gap:6px}.micro{letter-spacing:1.2px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body><div class="wrap">
<header><div class="brand"><svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><rect x=".5" y=".5" width="39" height="39" rx="11" fill="#1e3027" stroke="#38513c"/><path d="M7 21h5l4-11 7 21 4-10h6" stroke="#bafa75" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><div>Carrier Lab<small>Local randomness studio</small></div></div><div class="topright"><span class="micro">Instrument / 001</span><span class="pill"><i id="connectionDot" class="dot off"></i><span id="connection">Connecting to Ollama</span></span></div></header>
<section class="intro"><div><div class="micro">A frequency. A sequence. A closer look.</div><h1>Make chance visible.</h1><p>Capture binary streams. Explore the statistics. Ask your local model.</p></div><div class="reference"><strong class="mono">7.83 cycles / second</strong>Mathematical carrier · OS random source</div></section>
<div id="notice" role="alert"></div>
<div class="layout"><aside class="sidebar"><section class="panel controls" aria-label="Capture controls"><div class="config-top"><div class="panel-title">Signal engine <span class="sub">01</span></div><div class="frequency"><b>7.83</b><span class="mono">Hz</span><small>FIXED CARRIER</small></div></div><div class="generation-section"><label class="control-label" for="count">Capture length <span class="hint">bits</span></label><input id="count" type="number" value="8192" min="128" max="262144" step="1"><label class="control-label" for="batch">Bits per cycle</label><select id="batch"><option>32</option><option>128</option><option selected>256</option><option>512</option><option>1024</option></select><div class="duration">Estimated capture <span id="estimate" class="mono">4.09 s</span></div><button class="primary" id="start"><span>Generate bits</span><span aria-hidden="true">↗</span></button><button class="secondary stop" id="stop" disabled>Stop capture</button></div><div class="rule"></div><div class="model-section"><label class="control-label" for="model">Local intelligence <span class="hint">Ollama</span></label><div class="model-row"><select id="model" aria-label="Local Ollama model"><option value="">Finding local models…</option></select><button class="refresh" id="refresh" aria-label="Refresh local models" title="Refresh local models">↻</button></div><p id="modelHelp" class="model-help">Looking for installed models on your computer.</p><label class="check"><input type="checkbox" id="auto" checked><span>Analyze automatically when the capture finishes</span></label></div></section><div class="source-note"><strong>Where the randomness comes from</strong>The carrier sets the batch timing. Python’s <code>secrets</code> draws bits from the OS cryptographic RNG. Physical true randomness requires a separately validated hardware source.</div></aside>
<main class="main"><section class="panel scope"><div class="scope-head"><div class="panel-title">Carrier waveform <span class="sub mono">7.83 Hz</span></div><span class="live">REFERENCE SIGNAL</span></div><canvas id="wave" role="img" aria-label="Animated mathematical 7.83 hertz sine wave, not a physical measurement"></canvas><div class="scope-foot mono"><span>−1.5 s</span><span>sin(2π · 7.83 · t) / normalized amplitude</span><span>now</span></div><div class="progress" role="progressbar" aria-label="Capture progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" id="progress"><i id="progressFill"></i></div><div class="capture-line"><span id="captureStatus">Ready to capture</span><b id="captureCount" class="mono">0 / 8,192 bits</b></div></section>
<section class="metrics" aria-label="Capture statistics"><div class="metric"><div class="micro">Bits captured</div><div id="nValue" class="value mint mono">0</div><div id="rateValue" class="caption">OS cryptographic source</div></div><div class="metric"><div class="micro">Ones balance</div><div class="value cyan mono"><span id="balanceValue">—</span><small> %</small></div><div class="caption">Reference: 50% ones</div></div><div class="metric"><div class="micro">Marginal entropy</div><div class="value violet mono"><span id="entropyValue">—</span></div><div class="caption">bits / bit · balance only</div></div><div class="metric"><div class="micro">Capture time</div><div class="value mono"><span id="timeValue">0.00</span><small> s</small></div><div id="cyclesValue" class="caption">0 carrier cycles</div></div></section>
<section class="charts" aria-label="Binary visualizations"><div class="panel chart"><div class="panel-title">Bit field <div class="legend"><span><i style="background:#263e4e"></i>0</span><span><i style="background:#bafa75"></i>1</span></div></div><canvas id="field" role="img" aria-label="Grid of the latest 1024 generated bits"></canvas><div class="chart-foot"><span>Latest 1,024 bits</span><span class="mono">32 × 32</span></div></div><div class="panel chart"><div class="panel-title">Balance over time <span class="sub cyan">1s / n</span></div><canvas id="balance" role="img" aria-label="Windowed and cumulative fraction of ones"></canvas><div class="chart-foot"><span id="windowLabel">256-bit windows</span><span class="legend"><span><i style="background:#67d7ed"></i>window</span><span><i style="background:#ac9cff"></i>total</span></span></div></div><div class="panel chart"><div class="panel-title">Byte distribution <span class="sub">0–255</span></div><canvas id="histogram" role="img" aria-label="Histogram of complete eight-bit byte values"></canvas><div class="chart-foot"><span>Complete bytes only</span><span id="byteCount" class="mono">0 samples</span></div></div></section>
<section class="checks" aria-label="Descriptive checks"><div class="check-stat" title="Two-sided normal-approximation balance p-value; at least 128 bits"><span>Monobit p-value</span><b id="pValue">—</b></div><div class="check-stat" title="Standardized runs count, with a normal approximation"><span>Runs z-score</span><b id="runsValue">—</b></div><div class="check-stat" title="Pearson correlation between adjacent bits; undefined for a constant sequence"><span>Adjacent correlation</span><b id="correlationValue">—</b></div><div class="check-stat" title="Longest uninterrupted stretch of identical bits"><span>Longest run</span><b id="longestValue">—</b></div></section>
<p class="explain">These are descriptive checks, not a randomness certificate. Balanced bits can still form predictable patterns; small samples fluctuate.</p>
<details class="panel" style="padding:14px 20px"><summary style="cursor:pointer;font-size:11px;color:#91a2b4">Inspect binary string · latest 512 bits</summary><pre id="binaryPreview" class="mono" style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;line-height:1.9;color:#bafa75;margin:12px 0 0">No bits captured yet.</pre></details>
<section class="panel report"><div class="report-title"><div><h2><span aria-hidden="true">✳</span> The local perspective</h2><p>Measured statistics + a short bit sample, interpreted by your model.</p></div><button class="secondary" id="analyze" disabled>Analyze capture ↗</button></div><div id="report" class="report-body empty" aria-live="polite">Your next capture has a story in the numbers.
Generate a stream to see what your local model makes of its balance, runs, and adjacent-bit correlation.</div><div id="reportState" class="report-state">Waiting for a capture</div></section>
<div class="exports"><span id="sessionLabel">No capture yet</span><button class="secondary" id="exportTxt" disabled>↓ Binary string</button><button class="secondary" id="exportJson" disabled>↓ Full report · JSON</button></div></main></div>
<footer><span>Carrier Lab / 7.83 <span class="mono">&nbsp;·&nbsp; localhost only</span></span><span>Software clock · No physical field measurement · LLM commentary is not proof</span></footer>
</div><script nonce="__TOKEN__">
'use strict';
const $=id=>document.getElementById(id),token='__TOKEN__';
let state=null,models=[],busy=false,autoSession=null,lastChartKey='',polling=false,apiFailed=false;
const fmt=new Intl.NumberFormat(),reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const num=(x,d=4)=>x===null||x===undefined?'—':Number(x).toFixed(d);
function notice(text){$('notice').textContent=text;$('notice').classList.toggle('show',!!text);}
async function api(path,data){const response=await fetch(path,{method:data===undefined?'GET':'POST',headers:data===undefined?{}:{'Content-Type':'application/json','X-Lab-Token':token},body:data===undefined?undefined:JSON.stringify(data)});const result=await response.json();if(!response.ok)throw Error(result.error||'The request did not complete.');return result;}
function estimate(){const n=Number($('count').value),b=Number($('batch').value);$('estimate').textContent=n>=128&&n<=262144?(Math.ceil(n/b)/7.83).toFixed(2)+' s':'128–262,144 bits';if(!state||state.status==='idle')$('captureCount').textContent='0 / '+fmt.format(n||0)+' bits';}
async function refreshModels(){ $('refresh').disabled=true;try{const previous=$('model').value;const result=await api('/api/models');models=result.models;$('model').replaceChildren();if(!models.length)$('model').append(new Option('No local models installed',''));for(const name of models)$('model').append(new Option(name,name));if(models.includes(previous))$('model').value=previous;$('connection').textContent=models.length?'Ollama connected':'Ollama · no local models';$('connectionDot').classList.toggle('off',!models.length);$('modelHelp').textContent=models.length?'On-device models only. Llama models appear first.':'Install a local Llama model with: ollama pull llama3.2:3b, then refresh.';}catch(error){models=[];$('model').replaceChildren(new Option('Ollama unavailable',''));$('connection').textContent='Ollama offline';$('connectionDot').classList.add('off');$('modelHelp').textContent=error.message;}finally{$('refresh').disabled=false;renderControls();}}
function renderControls(){const running=state?.status==='running',analyzing=state?.analysis.status==='running',hasBits=(state?.stats.n||0)>0;$('start').disabled=busy||running||analyzing;$('start').firstElementChild.textContent=running?'Capturing…':analyzing?'Model is analyzing…':'Generate bits';$('stop').disabled=busy||!running;for(const id of ['count','batch'])$(id).disabled=running||busy||analyzing;$('analyze').disabled=busy||running||analyzing||!hasBits||!$('model').value;$('model').disabled=analyzing;$('exportTxt').disabled=$('exportJson').disabled=running||!hasBits;}
function render(){if(!state)return;const s=state.stats,a=state.analysis,running=state.status==='running';$('nValue').textContent=fmt.format(s.n);$('balanceValue').textContent=s.n?num(s.ones_fraction*100,2):'—';$('entropyValue').textContent=num(s.marginal_entropy,5);$('timeValue').textContent=num(state.elapsed,2);$('cyclesValue').textContent=fmt.format(state.cycles)+' carrier cycles';$('rateValue').textContent=s.n&&state.elapsed>0?fmt.format(Math.round(s.n/state.elapsed))+' bits / second observed':'OS cryptographic source';$('pValue').textContent=s.monobit_p!==null&&s.monobit_p<.0001?s.monobit_p.toExponential(2):num(s.monobit_p,4);$('runsValue').textContent=num(s.runs_z,3);$('correlationValue').textContent=num(s.lag1_correlation,4);$('longestValue').textContent=s.n?s.longest_run+' bits':'—';const progress=100*s.n/state.target;$('progressFill').style.width=progress+'%';$('progress').setAttribute('aria-valuenow',String(Math.round(progress)));$('captureCount').textContent=fmt.format(s.n)+' / '+fmt.format(state.target)+' bits';$('captureStatus').textContent=({idle:'Ready to capture',running:'Capturing · one batch per cycle',complete:'Capture complete',stopped:'Capture stopped · partial data retained',error:'Capture error · '+state.error})[state.status];$('windowLabel').textContent=fmt.format(s.window_size)+'-bit windows';$('byteCount').textContent=fmt.format(Math.floor(s.n/8))+' samples';$('sessionLabel').textContent=state.session_id?'Capture '+state.session_id:'No capture yet';$('report').classList.toggle('empty',a.status==='idle'||a.status==='running');if(a.status==='complete'||a.status==='error'){$('report').textContent=a.text;}else if(a.status==='running'){$('report').textContent='Your local model is examining this capture.\nThe measured statistics and up to 1,024 sample bits are being analyzed on your computer. The first request may take longer while the model loads.';}else{$('report').textContent=s.n?'Capture ready for local interpretation.\nSelect an installed model and choose “Analyze capture” to explain these measurements.':'Your next capture has a story in the numbers.\nGenerate a stream to see what your local model makes of its balance, runs, and adjacent-bit correlation.';}$('reportState').textContent=({idle:s.n?'Statistics ready · interpretation is optional':'Waiting for a capture',running:'Analyzing with '+a.model+' · up to 3 minutes',complete:'Completed with '+a.model+' · '+a.session_id,error:'Analysis unavailable · capture is preserved'})[a.status];renderControls();const key=state.session_id+':'+s.n;if(key!==lastChartKey){drawCharts();lastChartKey=key;}}
async function poll(){if(polling)return;polling=true;try{state=await api('/api/state');if(apiFailed){notice('');apiFailed=false;}render();if(state.status==='complete'&&autoSession===state.session_id){autoSession=null;if($('auto').checked&&$('model').value&&state.analysis.status==='idle')await analyzeCapture();}}catch(error){if(!apiFailed){notice('Dashboard disconnected. Keep the Python engine running, then reload this page. '+error.message);apiFailed=true;}}finally{polling=false;}}
async function action(fn){busy=true;notice('');renderControls();try{await fn();}catch(error){notice(error.message);}finally{busy=false;renderControls();}}
async function analyzeCapture(){try{await api('/api/analyze',{model:$('model').value});state=await api('/api/state');render();}catch(error){notice(error.message);}}
$('start').addEventListener('click',()=>action(async()=>{if(!$('count').reportValidity())return;await api('/api/start',{count:Number($('count').value),batch:Number($('batch').value)});state=await api('/api/state');autoSession=state.session_id;render();}));
$('stop').addEventListener('click',()=>action(async()=>{autoSession=null;await api('/api/stop',{});state=await api('/api/state');render();}));
$('analyze').addEventListener('click',()=>action(analyzeCapture));$('refresh').addEventListener('click',refreshModels);$('model').addEventListener('change',renderControls);$('count').addEventListener('input',estimate);$('batch').addEventListener('change',estimate);
for(const [id,format] of [['exportTxt','txt'],['exportJson','json']])$(id).addEventListener('click',()=>{const a=document.createElement('a');a.href='/api/export?format='+format;a.download='';document.body.append(a);a.click();a.remove();});
function canvas(id){const element=$(id),rect=element.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);const w=Math.max(1,rect.width),h=Math.max(1,rect.height);if(element.width!==Math.round(w*dpr)||element.height!==Math.round(h*dpr)){element.width=Math.round(w*dpr);element.height=Math.round(h*dpr);}const ctx=element.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);return{ctx,w,h};}
function grid(ctx,w,h){ctx.strokeStyle='#273847';ctx.lineWidth=.6;for(let i=0;i<=4;i++){ctx.beginPath();ctx.moveTo(0,10+(h-20)*i/4);ctx.lineTo(w,10+(h-20)*i/4);ctx.stroke();}for(let i=0;i<=8;i++){ctx.beginPath();ctx.moveTo(w*i/8,0);ctx.lineTo(w*i/8,h);ctx.stroke();}}
function empty(ctx,w,h,text){ctx.font='10px Segoe UI, sans-serif';ctx.fillStyle='#71879a';ctx.textAlign='center';ctx.fillText(text,w/2,h/2+4);}
let lastFrame=0;
function waveFrame(ms){if(ms-lastFrame>30){lastFrame=ms;const{ctx,w,h}=canvas('wave');grid(ctx,w,h);const t=reduceMotion?0:ms/1000;const mid=h/2,amp=h*.32;ctx.strokeStyle='#4b6a7b';ctx.setLineDash([3,5]);ctx.beginPath();ctx.moveTo(0,mid);ctx.lineTo(w,mid);ctx.stroke();ctx.setLineDash([]);ctx.beginPath();for(let x=0;x<=w;x+=1){const y=mid-Math.sin(2*Math.PI*7.83*(t-1.5+x/w*1.5))*amp;if(x===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.strokeStyle='#67d7ed';ctx.lineWidth=1.8;ctx.shadowColor='#67d7ed';ctx.shadowBlur=9;ctx.stroke();ctx.shadowBlur=0;const y=mid-Math.sin(2*Math.PI*7.83*t)*amp;ctx.beginPath();ctx.arc(w-2,y,3,0,Math.PI*2);ctx.fillStyle='#bafa75';ctx.fill();ctx.fillStyle='#698497';ctx.font='9px Consolas, monospace';ctx.textAlign='left';ctx.fillText('+1',5,14);ctx.fillText('−1',5,h-5);}requestAnimationFrame(waveFrame);}
function drawCharts(){const s=state?.stats;{const{ctx,w,h}=canvas('field');const bits=state?.preview.slice(-1024)||'';const cell=Math.min(w/32,h/32),ox=(w-cell*32)/2,oy=(h-cell*32)/2;for(let i=0;i<1024;i++){ctx.fillStyle=i<bits.length?(bits[i]==='1'?'#bafa75':'#263e4e'):'#1d2934';ctx.fillRect(ox+(i%32)*cell,oy+Math.floor(i/32)*cell,Math.max(1,cell-1),Math.max(1,cell-1));}if(!bits)empty(ctx,w,h,'Awaiting bits');}
{const{ctx,w,h}=canvas('balance');grid(ctx,w,h);const x0=25,usable=w-x0-3;const y=p=>h-12-p*(h-24);ctx.strokeStyle='#71838e';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(x0,y(.5));ctx.lineTo(w,y(.5));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#748898';ctx.textAlign='left';ctx.font='8px Consolas, monospace';for(const p of [0,.5,1])ctx.fillText(Math.round(p*100)+'%',0,y(p)+3);if(!s?.n)empty(ctx,w,h,'Awaiting a capture');else{for(const [values,color] of [[s.window_balance,'#67d7ed'],[s.cumulative_balance,'#ac9cff']]){ctx.beginPath();values.forEach((p,i)=>{const x=x0+(values.length===1?.5:i/(values.length-1))*usable;i?ctx.lineTo(x,y(p)):ctx.moveTo(x,y(p));});ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.stroke();if(values.length===1){ctx.beginPath();ctx.arc(x0+usable/2,y(values[0]),2.5,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();}}}}
{const{ctx,w,h}=canvas('histogram');grid(ctx,w,h);const hist=s?.byte_histogram||[],max=Math.max(1,...hist),bw=w/256;if(!s?.n)empty(ctx,w,h,'Awaiting complete bytes');else{hist.forEach((v,i)=>{const bh=v/max*(h-16);ctx.fillStyle=i%2?'#8276c5':'#ac9cff';ctx.fillRect(i*bw,h-8-bh,Math.max(.5,bw-.25),bh);});const expected=Math.floor(s.n/8)/256/max*(h-16);ctx.setLineDash([3,4]);ctx.strokeStyle='#67d7ed99';ctx.beginPath();ctx.moveTo(0,h-8-expected);ctx.lineTo(w,h-8-expected);ctx.stroke();ctx.setLineDash([]);}}}
window.addEventListener('resize',()=>{drawCharts();});estimate();drawCharts();requestAnimationFrame(waveFrame);refreshModels();poll();setInterval(()=>{poll();$('binaryPreview').textContent=state?.preview.slice(-512).match(/.{1,64}/g)?.join('\n')||'No bits captured yet.';},400);
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=7837, help="Local dashboard port (default 7837)")
    parser.add_argument("--ollama-port", type=int, default=11434, help="Local Ollama port")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    parser.add_argument("--generate", type=int, metavar="BITS", help="Capture bits from the command line, then exit")
    parser.add_argument("--batch", type=int, choices=(32, 128, 256, 512, 1024), default=256, help="Bits per carrier cycle")
    parser.add_argument("--output", type=Path, help="New JSON output file for --generate")
    parser.add_argument("--model", help="Installed local Ollama model for command-line analysis")
    args = parser.parse_args()
    for port in (args.port, args.ollama_port):
        if not 1 <= port <= 65535:
            parser.error("Ports must be between 1 and 65535.")
    if args.generate is None and (args.output or args.model):
        parser.error("--output and --model require --generate.")
    lab = Lab(args.ollama_port)
    if args.generate is not None:
        if args.output and args.output.exists():
            parser.error("Output already exists; choose a new file name.")
        try:
            lab.start(args.generate, args.batch)
        except ValueError as exc:
            parser.error(str(exc))
        try:
            lab.engine.worker.join()
        except KeyboardInterrupt:
            lab.engine.stop()
        capture = lab.engine.snapshot(include_bits=True)
        if capture["error"]:
            print(capture["error"], file=sys.stderr)
            return 1
        if args.model:
            try:
                capture["analysis"] = {"model": args.model, "text": lab.ollama.analyze(args.model, capture)}
            except ValueError as exc:
                capture["analysis"] = {"model": args.model, "error": str(exc)}
                print(f"Analysis unavailable: {exc}", file=sys.stderr)
        result = json.dumps(capture, indent=2, allow_nan=False)
        if args.output:
            with args.output.open("x", encoding="utf-8") as output:
                output.write(result + "\n")
            print(f"Saved {capture['stats']['n']:,} bits to {args.output}")
        else:
            print(result)
        return 0
    try:
        server = LocalServer(("127.0.0.1", args.port), lab)
    except OSError as exc:
        print(f"Cannot open local port {args.port}: {exc}\nTry a different --port, for example --port 7838.", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Carrier Lab is running at {url}\n{LIMITATION}\nPress Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        lab.engine.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
