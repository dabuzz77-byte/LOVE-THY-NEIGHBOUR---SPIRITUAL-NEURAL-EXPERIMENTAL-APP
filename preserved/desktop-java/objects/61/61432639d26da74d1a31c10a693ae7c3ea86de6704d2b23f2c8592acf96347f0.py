"""Core Interaction System — Python desktop workspace (standard library only).

Framework vocabulary comes from the original Java app and the user's Google AI
Mode conversation, 26 September 2026. Numeric models are software simulations;
network receipts, processing counters and journal hashes are measured data.
Run: python core_interaction_system.py   |   python core_interaction_system.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import math
import os
from pathlib import Path
import queue
import re
import sqlite3
import sys
import tempfile
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from urllib.error import HTTPError
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DEFAULT_URL = "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
LAYERS = ("ZERO POINT", "HYDROGEN", "STAR", "EARTH / CHNO", "LIFE", "KARMA", "SILICON")
MODES = ("Taoist · balance", "Science · direct", "Angel Taiji · gentle", "Monkey · explore", "God mind · target")
BG, PANEL, CARD, LINE = "#0a111d", "#111d2d", "#152437", "#263b50"
TEXT, MUTED, TEAL, BLUE, PURPLE, AMBER = "#e5edf6", "#99aec3", "#49dfbc", "#68b7ff", "#b7a0ff", "#ffbd79"


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def read_small(path: Path, limit=262144):
    with path.open("rb") as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Use a text file smaller than {limit // 1024} KB.")
    return data.decode("utf-8-sig")


@dataclass
class Framework:
    name: str = "Stateful Elevation Bridge"
    frequency_hz: float = 7.83
    cycles: int = 0
    self_response: float = .28
    mirror_response: float = .42
    balance_target: float = 0.0
    shield_limit: float = .85
    eco_floor: float = 1.0
    elevation_step: float = .05
    positive_words: str = "growth,success,improve,discovery,progress,stable,solution,protect,care"
    negative_words: str = "risk,loss,failure,conflict,decline,crisis,error,harm"

    def validate(self):
        if not isinstance(self.name, str) or not 1 <= len(self.name.strip()) <= 80:
            raise ValueError("Framework name must contain 1–80 characters.")
        bounds = {"frequency_hz": (.2, 30), "self_response": (.01, 1),
                  "mirror_response": (.01, 1), "balance_target": (-1, 1),
                  "shield_limit": (.05, 1), "eco_floor": (1, 1000000), "elevation_step": (0, 10)}
        for name, (low, high) in bounds.items():
            value = getattr(self, name)
            if type(value) not in (float, int) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be a finite number between {low} and {high}.")
        if type(self.cycles) is not int or not 0 <= self.cycles <= 1000000:
            raise ValueError("cycles must be 0 (continuous) or a whole number up to 1000000.")
        if abs(self.balance_target) > self.shield_limit:
            raise ValueError("The balance target must fit inside the containment limit.")
        for name in ("positive_words", "negative_words"):
            if not isinstance(getattr(self, name), str) or len(getattr(self, name)) > 4000:
                raise ValueError(f"{name} must be a comma-separated word list under 4000 characters.")
        return self

    @classmethod
    def parse(cls, text):
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Rules must be a JSON object.")
        unknown = set(data) - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError("Unknown rules: " + ", ".join(sorted(unknown)))
        return cls(**data).validate()

    def text(self):
        return json.dumps(asdict(self), indent=2, ensure_ascii=False) + "\n"


@dataclass
class Signal:
    source: str
    text: str
    value: float
    received: str


@dataclass
class Sample:
    cycle: int
    time: str
    source: str
    input: float
    self_value: float
    balance: float
    output: float
    stability: float
    contained: bool
    layer: str
    phase: float
    probability_zero: float
    probability_one: float
    eco_floor: float
    sky_elevation: float


class CoreEngine:
    """Single-owner deterministic model. UI and tests drive it on one thread."""
    def __init__(self, framework=None, persistent=None):
        self.framework = (framework or Framework()).validate()
        persistent = persistent or {}
        self.floor = max(self.framework.eco_floor, self._finite_state(persistent.get("floor", 1), 1))
        self.elevation = self._finite_state(persistent.get("elevation", 0), 0)
        self.pending = deque()
        self.history = deque(maxlen=2400)
        self.state = "READY"
        self.mode = MODES[0]
        self.reset_session()

    @staticmethod
    def _finite_state(value, fallback):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or value > 1e12:
            raise ValueError("Saved model state contains an invalid number.")
        return max(fallback, float(value))

    def reset_session(self):
        self.state = "READY"
        self.cycle = self.processed = self.contained = self.rejected = 0
        self.self_value = self.output = self.framework.balance_target
        self.elapsed = 0.0
        self.pending.clear()
        self.history.clear()

    def configure(self, framework):
        if self.state in ("RUNNING", "PAUSED"):
            raise ValueError("Stop the session before applying rules.")
        framework.validate()
        if framework.eco_floor < self.floor:
            raise ValueError(f"Anti-degradation: eco_floor must stay at or above {self.floor:g}.")
        self.framework = framework
        self.floor = max(self.floor, framework.eco_floor)
        self.reset_session()

    def start(self, mode=None):
        if self.state == "RUNNING":
            return
        if self.state == "PAUSED":
            self.state = "RUNNING"
            return
        pending = deque(self.pending)
        self.reset_session()
        self.pending = pending
        self.mode = mode or MODES[0]
        if self.mode not in MODES:
            raise ValueError("Unknown mind mode.")
        self.state = "RUNNING"

    def pause(self):
        if self.state == "RUNNING":
            self.state = "PAUSED"

    def stop(self):
        self.state = "STOPPED"
        self.pending.clear()

    def enqueue(self, source, text, explicit=None):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Enter some input text.")
        if len(text) > 16000:
            raise ValueError("Input is limited to 16000 characters.")
        # An explicit contradictory identity is quarantined, not silently rewritten.
        if re.search(r"(?<![\d.])(?:1\s*={1,2}\s*0|0\s*={1,2}\s*1)(?![\d.])", text):
            self.rejected += 1
            raise ValueError("Identity check: input contains 1=0 or 0=1. It was not queued. Review the source text.")
        if len(self.pending) >= 128:
            self.rejected += 1
            raise ValueError("The 128-item input queue is full. Wait for processing to catch up.")
        value = self.score(text) if explicit is None else explicit
        if type(value) not in (int, float) or not math.isfinite(value) or not -1 <= value <= 1:
            raise ValueError("The input signal must be between -1 and +1.")
        self.pending.append(Signal(str(source)[:200], text, float(value), utc_now()))
        return float(value)

    def score(self, text):
        positive = {w.strip().lower() for w in self.framework.positive_words.split(",")}
        negative = {w.strip().lower() for w in self.framework.negative_words.split(",")}
        tokens = re.findall(r"\w+", text.lower())
        plus = sum(word in positive for word in tokens)
        minus = sum(word in negative for word in tokens)
        return (plus - minus) / (plus + minus) if plus + minus else 0.0

    def tick(self, dt=None):
        if self.state != "RUNNING":
            return None
        f = self.framework
        dt = 1 / f.frequency_hz if dt is None else dt
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("Cycle duration must be a positive finite number.")
        item = self.pending.popleft() if self.pending else None
        raw = item.value if item else f.balance_target
        self.processed += int(item is not None)
        gain = {MODES[0]: 1, MODES[1]: 1, MODES[2]: .65, MODES[3]: 1.35, MODES[4]: .5}[self.mode]
        desired = raw * gain + (f.balance_target * .5 if self.mode == MODES[4] else 0)
        response = desired if self.mode == MODES[1] else self.self_value + f.self_response * (desired - self.self_value)
        balance = response + f.self_response * (f.balance_target - response)
        proposed = self.output + f.mirror_response * (balance - self.output)
        contained = abs(response) > f.shield_limit or abs(proposed) > f.shield_limit
        self.self_value = max(-f.shield_limit, min(f.shield_limit, response))
        self.output = max(-f.shield_limit, min(f.shield_limit, proposed))
        self.contained += int(contained)
        stability = max(0, 100 * (1 - abs(self.output - f.balance_target) / 2))
        self.elapsed += dt
        phase = math.tau * f.frequency_hz * self.elapsed
        # A normalized mathematical two-state model; this is not a hardware measurement.
        p0 = math.cos(phase / 2 + self.output) ** 2
        p1 = 1.0 - p0
        if not all(math.isfinite(x) for x in (self.self_value, self.output, stability, p0, p1)) or not math.isclose(p0 + p1, 1, abs_tol=1e-12):
            self.state = "FAULT"
            raise ValueError("Numeric invariant failed. Processing stopped.")
        if item:
            # Explicit progress points for accepted input, not money or a judgment of people.
            self.elevation = min(1e12, self.elevation + f.elevation_step * stability / 100)
        self.cycle += 1
        sample = Sample(self.cycle, utc_now(), item.source if item else "Feedback", raw, self.self_value,
                        balance, self.output, stability, contained, LAYERS[(self.cycle - 1) % len(LAYERS)],
                        phase % math.tau, p0, p1, self.floor, self.elevation)
        self.history.append(sample)
        if f.cycles and self.cycle >= f.cycles:
            self.state = "COMPLETE"
        return sample

    def snapshot(self):
        return {"floor": self.floor, "elevation": self.elevation}


class Journal:
    """Local event chain. Hashes detect changes; they do not prove factual truth."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time TEXT NOT NULL, payload TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)")
        self.db.commit()
        try:
            self.verify()
        except Exception:
            self.db.close()
            raise

    @staticmethod
    def digest(previous, stamp, payload):
        return hashlib.sha256((previous + "\n" + stamp + "\n" + payload).encode()).hexdigest()

    def append(self, kind, details, state):
        last = self.db.execute("SELECT digest FROM events ORDER BY id DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0" * 64
        stamp = utc_now()
        payload = json.dumps({"kind": kind, "details": details, "state": state}, sort_keys=True, ensure_ascii=False, allow_nan=False)
        digest = self.digest(previous, stamp, payload)
        with self.db:
            self.db.execute("INSERT INTO events(time,payload,previous,digest) VALUES(?,?,?,?)", (stamp, payload, previous, digest))
        return digest

    def verify(self):
        previous, count = "0" * 64, 0
        for event_id, stamp, payload, prior, digest in self.db.execute("SELECT id,time,payload,previous,digest FROM events ORDER BY id"):
            if prior != previous or digest != self.digest(prior, stamp, payload):
                raise ValueError(f"Journal integrity mismatch at event {event_id}. The existing journal was preserved.")
            previous, count = digest, count + 1
        return count

    def restore(self):
        row = self.db.execute("SELECT payload FROM events ORDER BY id DESC LIMIT 1").fetchone()
        return json.loads(row[0])["state"] if row else {}

    def close(self):
        self.db.close()


def validate_url(address):
    parsed = urlsplit(address.strip())
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Enter an HTTPS address without embedded login details.")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1")):
        raise ValueError("Use HTTPS. HTTP is supported only for local testing.")
    _ = parsed.port  # Validate malformed ports before starting a request.
    return address.strip()


class CheckedRedirect(HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, request, response, code, message, headers, address):
        validate_url(address)
        if urlsplit(request.full_url).scheme == "https" and urlsplit(address).scheme != "https":
            raise ValueError("An HTTPS source tried to redirect to an unencrypted address.")
        return super().redirect_request(request, response, code, message, headers, address)


class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def fetch_source(address, cancel=None):
    """Read a public text source with certificate checks, size and time limits."""
    address = validate_url(address)
    started = time.monotonic()
    request = Request(address, headers={"User-Agent": "CoreInteractionSystem/2.0 (desktop feed reader)",
                                      "Accept": "application/rss+xml, application/atom+xml, application/json, text/plain, text/html;q=0.8",
                                      "Accept-Encoding": "identity"})
    try:
        response = build_opener(CheckedRedirect()).open(request, timeout=5)
    except HTTPError as exc:
        code = exc.code
        exc.close()
        raise ValueError(f"Source returned HTTP {code}.") from None
    with response:
        kind = response.headers.get_content_type()
        if not (kind.startswith("text/") or "json" in kind or "xml" in kind):
            raise ValueError("The source must return text, HTML, JSON, RSS or Atom.")
        chunks, size = [], 0
        while True:
            if cancel is not None and cancel.is_set():
                raise InterruptedError("Request cancelled.")
            if time.monotonic() - started > 15:
                raise TimeoutError("The source exceeded the 15-second request limit.")
            chunk = response.read1(16384)
            if not chunk:
                break
            size += len(chunk)
            if size > 512 * 1024:
                raise ValueError("The source exceeds the 512 KB response limit.")
            chunks.append(chunk)
        charset = response.headers.get_content_charset() or "utf-8"
        body = b"".join(chunks).decode(charset, errors="replace")
        final_url = response.url
    title = urlsplit(final_url).hostname
    if "xml" in kind or body.lstrip().startswith(("<?xml", "<rss", "<feed")):
        if re.search(r"<!\s*(?:DOCTYPE|ENTITY)", body, re.I):
            raise ValueError("XML declarations that load or expand entities are not supported.")
        root = ET.fromstring(body)
        titles = [element.text.strip() for element in root.iter() if element.tag.split("}")[-1] == "title" and element.text and element.text.strip()]
        title = titles[0] if titles else title
        text = "\n".join("• " + item for item in titles[1:21]) if len(titles) > 1 else " ".join(root.itertext())
    elif "html" in kind:
        parser = ReadableHTML()
        parser.feed(body)
        text = " ".join(parser.parts)
    elif "json" in kind:
        text = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
    else:
        text = body
    text = html.unescape(text).strip()[:12000]
    if not text:
        raise ValueError("The source returned no readable content.")
    return {"url": final_url, "title": title, "text": text, "bytes": size,
            "latency_ms": round((time.monotonic() - started) * 1000), "received": utc_now()}


def export_csv(path, samples):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=[field.name for field in fields(Sample)])
    writer.writeheader()
    for sample in samples:
        row = asdict(sample)
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                row[key] = "'" + value
        writer.writerow(row)
    atomic_write(Path(path), stream.getvalue())


def build_app(root, data_dir=DATA_DIR):
    # Import Tk only for graphical runs so the processing engine remains headless-friendly.
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    class App:
        def __init__(self):
            self.root, self.data_dir = root, Path(data_dir)
            self.closed = False
            self.results = queue.Queue()
            self.cancel = threading.Event()
            self.fetching = False
            self.generation = 0
            self.last_fingerprint = None
            self.last_poll = 0.0
            self.next_cycle = 0.0
            self.previous_cycle = None
            self.last_checkpoint = time.monotonic()
            self.actual_times = deque(maxlen=80)
            self.last_display_log = 0.0
            self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.selected_node = None
            self.field_size = None
            self.field_items = {}
            self.last_render = 0.0
            self.last_field_state = None
            self.last_chart_state = None
            self.journal = Journal(self.data_dir / "journal.sqlite3")
            rules = self.data_dir / "framework.json"
            self.framework = Framework.parse(read_small(rules)) if rules.exists() else Framework()
            self.engine = CoreEngine(self.framework, self.journal.restore())
            # Restored high-water floor is authoritative across restarts.
            self.framework.eco_floor = self.engine.floor
            self.mode = tk.StringVar(value=MODES[0])
            self.live = tk.BooleanVar(value=True)
            self.motion = tk.BooleanVar(value=True)
            self.manual_signal = tk.BooleanVar(value=False)
            self.signal = tk.DoubleVar(value=0)
            self.url = tk.StringVar(value=DEFAULT_URL)
            self.network_label = tk.StringVar(value="Ready to connect")
            self.status = tk.StringVar(value="Start a session to connect live input, or queue your own text.")
            self.title_state = tk.StringVar(value="●  READY")
            self.values = {name: tk.StringVar(value="—") for name in ("cycles", "stability", "queue", "invariants")}
            self.details = {name: tk.StringVar() for name in ("cycles", "stability", "queue", "invariants")}
            self.model_state = tk.StringVar()
            self.styles()
            root.title("Core Interaction System · Python")
            root.geometry("1360x930")
            root.minsize(1100, 880)
            root.configure(bg=BG)
            root.protocol("WM_DELETE_WINDOW", self.close)
            root.bind("<Control-space>", lambda event: self.pause() if self.engine.state == "RUNNING" else self.start())
            self.layout()
            self.refresh()
            self.log("SYSTEM", "Python workspace ready. Live input connects when you start.")
            self.audit("open", {"framework": self.framework.name})
            self.after_id = root.after(33, self.frame)

        def styles(self):
            style = ttk.Style(root)
            style.theme_use("clam")
            style.configure("TFrame", background=BG)
            style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
            style.configure("TButton", background=CARD, foreground=TEXT, borderwidth=1, bordercolor=LINE,
                            padding=(13, 9), font=("Segoe UI", 10, "bold"), focusthickness=1, focuscolor=TEAL)
            style.map("TButton", background=[("active", "#25455c")], foreground=[("disabled", "#61778c")])
            style.configure("Primary.TButton", background=TEAL, foreground=BG, bordercolor=TEAL)
            style.map("Primary.TButton", background=[("active", "#85f0d4"), ("disabled", "#224d49")])
            style.configure("TCheckbutton", background=BG, foreground=MUTED, font=("Segoe UI", 10), padding=3)
            style.map("TCheckbutton", background=[("active", BG)], foreground=[("active", TEXT)])
            style.configure("TEntry", fieldbackground=PANEL, foreground=TEXT, insertcolor=TEXT, bordercolor=LINE, padding=8)
            style.configure("TCombobox", fieldbackground=PANEL, background=CARD, foreground=TEXT, arrowcolor=TEAL, padding=7)
            style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)])
            root.option_add("*TCombobox*Listbox.background", PANEL)
            root.option_add("*TCombobox*Listbox.foreground", TEXT)
            style.configure("TNotebook", background=BG, borderwidth=0)
            style.configure("TNotebook.Tab", background=BG, foreground=MUTED, padding=(15,10), font=("Segoe UI",10))
            style.map("TNotebook.Tab", background=[("selected",PANEL)], foreground=[("selected",TEAL)])
            style.configure("Vertical.TScrollbar", background=LINE, troughcolor=BG, borderwidth=0, arrowcolor=MUTED)
            style.configure("Horizontal.TScale", background=BG, troughcolor=LINE)

        @staticmethod
        def label(parent, text="", size=10, color=TEXT, bold=False, **kwargs):
            return tk.Label(parent, text=text, bg=kwargs.pop("bg", BG), fg=color,
                            font=("Segoe UI",size,"bold" if bold else "normal"), **kwargs)

        def text_area(self, parent, height=5, mono=False, editable=True):
            holder = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
            widget = tk.Text(holder, height=height, width=20, bg=PANEL, fg=TEXT, insertbackground=TEAL,
                             relief="flat", wrap="word", padx=12, pady=10, spacing1=2, spacing3=3,
                             selectbackground="#315a75", font=("Consolas" if mono else "Segoe UI",10), undo=editable)
            bar = ttk.Scrollbar(holder, command=widget.yview)
            widget.configure(yscrollcommand=bar.set)
            widget.pack(side="left",fill="both",expand=True); bar.pack(side="right",fill="y")
            if not editable:
                widget.configure(state="disabled")
            return holder, widget

        @staticmethod
        def set_text(widget, text, readonly=False):
            widget.configure(state="normal")
            widget.delete("1.0","end"); widget.insert("1.0",text)
            if readonly:
                widget.configure(state="disabled")

        def layout(self):
            outer = tk.Frame(root,bg=BG,padx=24,pady=16);outer.pack(fill="both",expand=True)
            header = tk.Frame(outer,bg=BG);header.pack(fill="x",pady=(0,12))
            self.label(header,"C O R E   /   INTERACTION SYSTEM",10,TEAL,True).pack(anchor="w")
            self.label(header,"A living field of interaction.",24,TEXT,True).pack(anchor="w",pady=(3,2))
            self.label(header,"Your framework. Live information. Every response made visible.",11,MUTED).pack(anchor="w")
            self.label(header,textvariable=self.title_state,color=TEAL,bold=True).place(relx=1,x=-2,y=17,anchor="ne")
            self.label(header,"PYTHON  /  LOCAL WORKSPACE",9,MUTED).place(relx=1,x=-2,y=46,anchor="ne")
            metrics = tk.Frame(outer,bg=BG);metrics.pack(fill="x",pady=(0,16))
            for i,(key,title,color) in enumerate((("cycles","PROCESSING CYCLES",TEXT),("stability","TARGET STABILITY",TEAL),("queue","INPUT QUEUE",BLUE),("invariants","MODEL INVARIANTS",PURPLE))):
                metrics.columnconfigure(i,weight=1,uniform="cards")
                card=tk.Frame(metrics,bg=PANEL,padx=16,pady=9,highlightbackground=LINE,highlightthickness=1)
                card.grid(row=0,column=i,sticky="nsew",padx=(0,12 if i<3 else 0))
                self.label(card,title,9,MUTED,bg=PANEL).pack(anchor="w")
                self.label(card,size=23,color=color,bold=True,bg=PANEL,textvariable=self.values[key]).pack(anchor="w",pady=(3,2))
                self.label(card,size=9,color=MUTED,bg=PANEL,textvariable=self.details[key]).pack(anchor="w")
            main=tk.Frame(outer,bg=BG);main.pack(fill="both",expand=True)
            main.columnconfigure(0,weight=1);main.columnconfigure(1,weight=0,minsize=345);main.rowconfigure(0,weight=1)
            left=tk.Frame(main,bg=BG);left.grid(row=0,column=0,sticky="nsew",padx=(0,18))
            left.rowconfigure(0,weight=1);left.columnconfigure(0,weight=1)
            self.canvas=tk.Canvas(left,bg=BG,highlightbackground=LINE,highlightthickness=1,height=350)
            self.canvas.grid(row=0,column=0,sticky="nsew")
            self.canvas.bind("<Button-1>",self.select_node)
            self.chart=tk.Canvas(left,bg=PANEL,highlightthickness=0,height=100);self.chart.grid(row=1,column=0,sticky="ew",pady=(10,8))
            self.label(left,color=MUTED,size=10,textvariable=self.model_state).grid(row=2,column=0,sticky="w",pady=(0,8))
            controls=tk.Frame(left,bg=BG);controls.grid(row=3,column=0,sticky="ew",pady=(0,10))
            self.start_button=ttk.Button(controls,text="Start session",style="Primary.TButton",command=self.start);self.start_button.pack(side="left",padx=(0,7))
            self.pause_button=ttk.Button(controls,text="Pause",command=self.pause);self.pause_button.pack(side="left",padx=(0,7))
            self.stop_button=ttk.Button(controls,text="Stop",command=self.stop);self.stop_button.pack(side="left",padx=(0,7))
            ttk.Button(controls,text="Export CSV",command=self.export).pack(side="left",padx=(0,7))
            ttk.Checkbutton(controls,text="Motion",variable=self.motion).pack(side="left")
            self.output_tabs=ttk.Notebook(left);self.output_tabs.grid(row=4,column=0,sticky="ew")
            log_frame,self.log_text=self.text_area(self.output_tabs,height=4,mono=True,editable=False)
            source_frame,self.source_text=self.text_area(self.output_tabs,height=4,editable=False)
            self.output_tabs.add(log_frame,text="Activity");self.output_tabs.add(source_frame,text="Web source")
            self.set_text(self.source_text,"Live responses appear here with their source address, receipt time and byte count.\n\nNew text is scored against your editable keyword lists, then passed through the same core engine as manual input.",True)
            self.side=ttk.Notebook(main,width=345);self.side.grid(row=0,column=1,sticky="nsew")
            connect=ttk.Frame(self.side,padding=(14,16));manual=ttk.Frame(self.side,padding=(14,16));rules=ttk.Frame(self.side,padding=(12,14));notes=ttk.Frame(self.side,padding=(12,14))
            self.side.add(connect,text="Connect");self.side.add(manual,text="Input");self.side.add(rules,text="Rules");self.side.add(notes,text="Notes")
            self.connect_panel(connect);self.input_panel(manual);self.rules_panel(rules);self.notes_panel(notes)
            self.label(outer,color=MUTED,size=9,textvariable=self.status,anchor="w").pack(fill="x",pady=(12,0))

        def section(self,parent,title):
            self.label(parent,title,10,TEAL,True).pack(anchor="w",pady=(0,9))

        def connect_panel(self,panel):
            self.section(panel,"01  /  CORE SIGNATURE")
            self.mode_select=ttk.Combobox(panel,textvariable=self.mode,values=MODES,state="readonly")
            self.mode_select.pack(fill="x",pady=(0,18))
            self.section(panel,"02  /  LIVE WEB INPUT")
            self.label(panel,"RSS, JSON or readable HTTPS page",9,MUTED).pack(anchor="w",pady=(0,5))
            ttk.Entry(panel,textvariable=self.url).pack(fill="x",pady=(0,6))
            ttk.Checkbutton(panel,text="Connect every 30 seconds",variable=self.live,command=self.toggle_live).pack(anchor="w")
            self.fetch_button=ttk.Button(panel,text="Fetch now",command=self.fetch,style="Primary.TButton")
            self.fetch_button.pack(fill="x",pady=(7,7))
            self.label(panel,textvariable=self.network_label,size=9,color=BLUE).pack(anchor="w",pady=(0,20))
            self.label(panel,"THE STATEFUL BRIDGE",10,TEAL,True).pack(anchor="w",pady=(5,10))
            self.label(panel,"New source text enters the local core,\npasses through balance and containment,\nand becomes a visible output signal.\n\nYour source text stays available in\nWeb source. Repeated content is\nchecked without adding duplicates.",10,MUTED,justify="left").pack(anchor="w")

        def input_panel(self,panel):
            self.section(panel,"03  /  MANUAL INPUT")
            frame,self.input_text=self.text_area(panel,height=7);frame.pack(fill="x",pady=(0,6))
            self.input_text.insert("1.0","Progress through discovery; balance risk with a solution.")
            ttk.Checkbutton(panel,text="Set signal manually",variable=self.manual_signal).pack(anchor="w")
            ttk.Scale(panel,from_=-1,to=1,variable=self.signal,command=lambda value:self.signal_label.configure(text=f"Signal  {float(value):+.2f}  /  −1 to +1")).pack(fill="x",pady=(3,0))
            self.signal_label=self.label(panel,"Signal  +0.00  /  −1 to +1",9,MUTED);self.signal_label.pack(anchor="w",pady=(0,7))
            ttk.Button(panel,text="Queue input",command=self.queue_manual).pack(fill="x")
            self.label(panel,"Text uses transparent keyword scoring.\nNo AI account or API key is required.",9,MUTED,justify="left").pack(anchor="w",pady=(14,0))

        def rules_panel(self,panel):
            self.label(panel,"Rules are applied while the session is stopped.\nCycles: 0 = continuous. Frequency: model tick rate.",9,MUTED,justify="left").pack(anchor="w",pady=(0,10))
            frame,self.rule_text=self.text_area(panel,height=21,mono=True);frame.pack(fill="both",expand=True,pady=(0,10))
            self.rule_text.insert("1.0",self.framework.text())
            self.apply_button=ttk.Button(panel,text="Apply & save rules",style="Primary.TButton",command=self.apply_rules);self.apply_button.pack(fill="x",pady=(0,6))
            ttk.Button(panel,text="Import JSON rules",command=self.import_rules).pack(fill="x",pady=(0,6))
            ttk.Button(panel,text="Verify local audit trail",command=self.verify_journal).pack(fill="x")

        def notes_panel(self,panel):
            self.label(panel,"Source ideas and their implemented meaning",9,MUTED).pack(anchor="w",pady=(0,10))
            frame,self.notes_text=self.text_area(panel,height=25);frame.pack(fill="both",expand=True,pady=(0,10))
            path=self.data_dir/"framework_notes.md"
            default=APP_DIR/"FRAMEWORK_MAPPING.md"
            self.notes_text.insert("1.0",read_small(path) if path.exists() else read_small(default) if default.exists() else "Paste source framework text here. Prose is retained as notes; the Framework tab defines executable rules.")
            ttk.Button(panel,text="Import framework text",command=self.import_notes).pack(fill="x",pady=(0,6))
            ttk.Button(panel,text="Save notes locally",style="Primary.TButton",command=self.save_notes).pack(fill="x")

        def log(self,kind,message):
            line=f"{datetime.now():%H:%M:%S}  {kind:<9}  {message}\n"
            self.log_text.configure(state="normal");self.log_text.insert("end",line)
            if int(self.log_text.index("end-1c").split(".")[0])>400:
                self.log_text.delete("1.0","60.0")
            self.log_text.see("end");self.log_text.configure(state="disabled")
            self.status.set(message[:150])

        def error(self,exception):
            self.log("CHECK",str(exception))
            messagebox.showwarning("Check input",str(exception),parent=root)

        def audit(self,kind,details):
            try:
                self.journal.append(kind,details,self.engine.snapshot())
                return True
            except (OSError,sqlite3.Error) as exc:
                self.engine.stop()
                self.log("STORAGE",f"Processing stopped because the journal could not be saved: {exc}")
                return False

        def start(self):
            resumed=self.engine.state=="PAUSED"
            self.generation+=1
            self.engine.start(self.mode.get())
            self.next_cycle=time.monotonic()
            self.previous_cycle=None
            self.actual_times.clear()
            if not resumed:
                self.last_fingerprint=None
                self.session_id=datetime.now().strftime("%Y%m%d-%H%M%S")
            self.audit("resume" if resumed else "start",{"mode":self.mode.get(),"rules":asdict(self.framework),"session":self.session_id})
            self.log("SESSION","Resumed." if resumed else f"Started {self.framework.name} at {self.framework.frequency_hz:g} Hz.")
            if self.live.get() and self.engine.state=="RUNNING":
                self.fetch()
            self.refresh()

        def pause(self):
            self.engine.pause();self.generation+=1
            self.audit("pause",{"cycle":self.engine.cycle})
            self.log("SESSION","Paused. In-flight web results from before the pause are ignored.")
            self.refresh()

        def stop(self):
            self.engine.stop();self.generation+=1
            self.audit("stop",{"cycle":self.engine.cycle})
            self.log("SESSION","Stopped. History is available for export; floor and elevation are saved.")
            self.refresh()

        def queue_manual(self):
            try:
                text=self.input_text.get("1.0","end-1c")
                value=self.engine.enqueue("Manual",text,self.signal.get() if self.manual_signal.get() else None)
                self.audit("input",{"source":"Manual","signal":value,"sha256":hashlib.sha256(text.encode()).hexdigest()})
                self.log("INPUT",f"Manual input queued with signal {value:+.3f}.")
                self.refresh()
            except ValueError as exc:
                self.error(exc)

        def toggle_live(self):
            self.generation+=1
            if self.live.get() and self.engine.state=="RUNNING":
                self.fetch()
            elif not self.live.get():
                self.network_label.set("Live polling off")

        def fetch(self):
            if self.fetching or self.closed:
                return
            try:
                address=validate_url(self.url.get())
            except ValueError as exc:
                self.last_poll=time.monotonic()
                self.network_label.set("Check source address")
                self.error(exc);return
            self.fetching=True;self.last_poll=time.monotonic();generation=self.generation
            self.fetch_button.configure(state="disabled");self.network_label.set("Connecting…")
            def worker():
                try:
                    self.results.put((generation,fetch_source(address,self.cancel),None))
                except Exception as exc:
                    self.results.put((generation,None,str(exc)))
            threading.Thread(target=worker,name="core-web-input",daemon=True).start()

        def receive_web(self):
            while True:
                try:
                    generation,result,error=self.results.get_nowait()
                except queue.Empty:
                    break
                self.fetching=False;self.fetch_button.configure(state="normal")
                if generation!=self.generation:
                    self.network_label.set("Previous request discarded")
                    self.last_poll=0
                    continue
                if error:
                    self.network_label.set("Connection failed · retry available")
                    self.log("NETWORK",error)
                    self.set_text(self.source_text,"The latest request failed.\n"+error+"\n\nCheck the source address and your connection. Manual input remains available.",True)
                    self.audit("network_error",{"error":error[:500]})
                    continue
                self.network_label.set(f"Connected · {result['latency_ms']} ms · {datetime.now():%H:%M:%S}")
                self.set_text(self.source_text,f"{result['title']}\n{result['url']}\nReceived {result['received']} · {result['bytes']:,} bytes\n\n{result['text']}",True)
                fingerprint=hashlib.sha256((result["url"]+result["text"]).encode()).hexdigest()
                if fingerprint!=self.last_fingerprint:
                    try:
                        value=self.engine.enqueue("Web: "+urlsplit(result["url"]).hostname,result["text"])
                        self.last_fingerprint=fingerprint
                        self.log("NETWORK",f"Received {result['bytes']:,} bytes; queued signal {value:+.3f}.")
                        self.audit("network_input",{"host":urlsplit(result["url"]).hostname,"bytes":result["bytes"],"sha256":fingerprint,"signal":value})
                    except ValueError as exc:
                        self.log("REVIEW",str(exc));self.audit("quarantine",{"reason":str(exc),"sha256":fingerprint})
                else:
                    self.log("NETWORK","Source checked; content unchanged, so no duplicate was queued.")
                self.refresh()

        def apply_rules(self):
            try:
                candidate=Framework.parse(self.rule_text.get("1.0","end-1c"))
                if self.engine.state in ("RUNNING","PAUSED"):
                    raise ValueError("Stop the session before applying rules.")
                if candidate.eco_floor<self.engine.floor:
                    raise ValueError(f"Protection baseline is {self.engine.floor:g}; the new floor cannot be lower.")
                atomic_write(self.data_dir/"framework.json",candidate.text())
                self.engine.configure(candidate);self.framework=candidate
                self.audit("configure",asdict(candidate));self.refresh()
                self.log("FRAMEWORK","Rules saved and applied. The protection baseline is retained.")
            except (ValueError,OSError) as exc:
                self.error(exc)

        def import_rules(self):
            path=filedialog.askopenfilename(parent=root,title="Import framework rules",filetypes=[("JSON rules","*.json"),("All files","*.*")])
            if path:
                try:
                    candidate=Framework.parse(read_small(Path(path)))
                    self.set_text(self.rule_text,candidate.text())
                    self.log("FRAMEWORK","Imported into the editor. Apply & save rules activates them.")
                except (ValueError,OSError) as exc:
                    self.error(exc)

        def import_notes(self):
            path=filedialog.askopenfilename(parent=root,title="Import framework text",filetypes=[("Text or Markdown","*.txt *.md"),("All files","*.*")])
            if path:
                try:
                    self.set_text(self.notes_text,read_small(Path(path)))
                    self.log("NOTES","Framework text imported. Save notes locally to retain it.")
                except (ValueError,OSError) as exc:
                    self.error(exc)

        def save_notes(self):
            try:
                text=self.notes_text.get("1.0","end-1c")
                if len(text.encode("utf-8"))>262144:
                    raise ValueError("Notes must be smaller than 256 KB.")
                atomic_write(self.data_dir/"framework_notes.md",text)
                self.log("NOTES","Notes saved in the app's data folder.")
            except (ValueError,OSError) as exc:
                self.error(exc)

        def verify_journal(self):
            try:
                count=self.journal.verify()
                self.log("AUDIT",f"Verified {count:,} locally recorded events; hash chain matches.")
                messagebox.showinfo("Local audit trail",f"Verified {count:,} events.\n\nHashes detect changes within this local journal. They do not verify source claims or provide encryption.",parent=root)
            except (ValueError,sqlite3.Error) as exc:
                self.engine.stop();self.refresh();self.error(exc)

        def export(self):
            if not self.engine.history:
                self.log("EXPORT","Run a session before exporting its data.");return
            path=filedialog.asksaveasfilename(parent=root,title="Export session data",defaultextension=".csv",initialfile=f"core-session-{self.session_id}.csv",filetypes=[("CSV","*.csv")])
            if path:
                try:
                    export_csv(path,list(self.engine.history))
                    self.log("EXPORT",f"Exported {len(self.engine.history):,} recent cycles to {Path(path).name}.")
                except OSError as exc:
                    self.error(exc)

        def refresh(self):
            engine=self.engine;running=engine.state=="RUNNING";paused=engine.state=="PAUSED"
            self.title_state.set("●  "+engine.state)
            self.start_button.configure(text="Resume" if paused else "Start session",state="disabled" if running else "normal")
            self.pause_button.configure(state="normal" if running else "disabled")
            self.stop_button.configure(state="normal" if running or paused else "disabled")
            self.apply_button.configure(state="disabled" if running or paused else "normal")
            self.mode_select.configure(state="disabled" if running or paused else "readonly")
            self.values["cycles"].set(f"{engine.cycle:03d}")
            hz=(len(self.actual_times)-1)/(self.actual_times[-1]-self.actual_times[0]) if len(self.actual_times)>1 and self.actual_times[-1]>self.actual_times[0] else 0
            self.details["cycles"].set(f"{hz:.2f} Hz actual / {self.framework.frequency_hz:g} Hz target")
            latest=engine.history[-1] if engine.history else None
            self.values["stability"].set(f"{latest.stability:.1f}%" if latest else "—")
            self.details["stability"].set("Model output distance from target")
            self.values["queue"].set(str(len(engine.pending)))
            self.details["queue"].set(f"{engine.processed} processed / {engine.rejected} rejected")
            self.values["invariants"].set("PASS" if latest and engine.state!="FAULT" else "FAULT" if engine.state=="FAULT" else "READY")
            self.details["invariants"].set(f"{engine.contained} contained / P(0) + P(1) = 1")
            self.model_state.set(f"ECO-FLOOR  {engine.floor:.2f}     /     SKY ELEVATION  {engine.elevation:.3f} points     /     Saved locally")

        def frame(self):
            if self.closed:
                return
            self.receive_web()
            now=time.monotonic()
            if self.engine.state=="RUNNING":
                if now>=self.next_cycle:
                    dt=(now-self.previous_cycle) if self.previous_cycle is not None else 1/self.framework.frequency_hz
                    self.previous_cycle=now
                    # Reschedule against the planned deadline; skip missed deadlines rather than burst.
                    interval=1/self.framework.frequency_hz
                    self.next_cycle+=interval
                    if self.next_cycle<now:
                        self.next_cycle=now+interval
                    self.actual_times.append(now)
                    try:
                        sample=self.engine.tick(dt)
                        if sample.source!="Feedback" or now-self.last_display_log>=1:
                            self.log("CYCLE",f"{sample.cycle:04d} · {sample.layer} · {sample.input:+.2f} → {sample.output:+.3f}"+(" · contained" if sample.contained else ""))
                            self.last_display_log=now
                        if sample.source!="Feedback" or now-self.last_checkpoint>=1:
                            self.audit("cycle",asdict(sample));self.last_checkpoint=now
                        if self.engine.state=="COMPLETE":
                            self.generation+=1;self.audit("complete",{"cycle":self.engine.cycle})
                            self.log("SESSION","Session complete. You can export the data or start again.")
                    except (ValueError,OverflowError) as exc:
                        self.engine.state="FAULT";self.generation+=1;self.log("FAULT",str(exc))
                    self.refresh()
                if self.live.get() and now-self.last_poll>=30:
                    self.fetch()
            self.draw_field(now)
            self.draw_chart()
            self.after_id=root.after(33,self.frame)

        def node_positions(self):
            width,height=self.canvas.winfo_width(),self.canvas.winfo_height()
            cx=width*.5
            spread=min(width*.265,220)
            lower=max(110,height-160)
            upper=max(69,min(lower-65,height*.27))
            return [(cx-spread,lower),(cx,upper),(cx+spread,lower)]

        def select_node(self,event):
            self.selected_node=None
            for i,(x,y) in enumerate(self.node_positions()):
                if math.hypot(event.x-x,event.y-y)<48:
                    self.selected_node=i

        def draw_field(self, now):
            canvas = self.canvas
            width, height = canvas.winfo_width(), canvas.winfo_height()
            if width < 100 or height < 100:
                return
            cx, cy = width * .5, height * .46
            radius = min(width * .28, height * .37)
            stamp = (width, height, self.engine.cycle, self.engine.state, self.motion.get(), self.selected_node)
            animate = self.motion.get() and self.engine.state == "RUNNING"
            if self.field_size == (width, height):
                if not animate and stamp == self.last_field_state:
                    return
                if animate and now - self.last_render < .05:
                    return
            self.last_render, self.last_field_state = now, stamp
            nodes = self.node_positions()
            if self.field_size != (width, height):
                self.field_size = (width, height)
                canvas.delete("all")
                for y in range(18, height - 10, 30):
                    for x in range(20, width - 10, 30):
                        canvas.create_oval(x, y, x + 1, y + 1, fill="#223348", outline="")
                canvas.create_text(20, 22, text="CORE INTERACTION FIELD", fill=MUTED, font=("Segoe UI", 9, "bold"), anchor="w")
                canvas.create_text(width - 20, 22, text="SIMULATION + LIVE INPUT", fill=TEAL, font=("Segoe UI", 8), anchor="e")
                for i in range(3):
                    r = radius + i * 12
                    canvas.create_oval(cx-r, cy-r*.72, cx+r, cy+r*.72, outline="#1e3e50", width=1)
                self.field_items = {"cube": [], "particles": [], "nodes": [], "layers": []}
                for i in range(8):
                    for bit in (1, 2, 4):
                        if not i & bit:
                            self.field_items["cube"].append((i, i | bit, canvas.create_line(0, 0, 1, 1, fill="#284050")))
                for i in range(3):
                    canvas.create_line(*nodes[i], *nodes[(i+1) % 3], fill="#36576a", width=1, arrow="last")
                    for j in range(3):
                        self.field_items["particles"].append((i, j, canvas.create_oval(0, 0, 1, 1, fill=TEAL, outline="")))
                for (x, y), name, role, color in zip(nodes, ("LOCAL SELF", "GOD SELF", "EXTERNAL VECTOR"),
                        ("RECEIVE / RESPOND", "BALANCE / TARGET", "MIRROR / CONTAIN"), (TEAL, PURPLE, BLUE)):
                    for r, shade in ((53, "#102c35"), (44, "#183a45")):
                        canvas.create_oval(x-r, y-r, x+r, y+r, fill=shade, outline="")
                    arc = canvas.create_arc(x-44, y-44, x+44, y+44, start=0, extent=235, outline=color, style="arc", width=1)
                    border = canvas.create_oval(x-34, y-34, x+34, y+34, fill=PANEL, outline=color, width=2)
                    value = canvas.create_text(x, y, text="+0.00", fill=TEXT, font=("Consolas", 17, "bold"))
                    canvas.create_text(x, y+61, text=name, fill=TEXT, font=("Segoe UI", 10, "bold"))
                    if height >= 275:
                        canvas.create_text(x, y+79, text=role, fill=MUTED, font=("Segoe UI", 8))
                    self.field_items["nodes"].append((arc, border, value))
                self.field_items["detail"] = canvas.create_text(cx, height-63, text="", fill=MUTED, font=("Segoe UI", 9), width=width-70)
                spacing = (width-48) / len(LAYERS)
                for i, name in enumerate(LAYERS):
                    x = 24 + spacing * (i+.5)
                    box = canvas.create_rectangle(x-spacing*.43, height-41, x+spacing*.43, height-18, fill=PANEL, outline="")
                    label = canvas.create_text(x, height-29, text=name, fill=MUTED, font=("Segoe UI", 7, "bold"))
                    self.field_items["layers"].append((box, label))
            phase = now*.7 if animate else 0
            points = []
            for i in range(8):
                x, y, z = (1 if i & 1 else -1), (1 if i & 2 else -1), (1 if i & 4 else -1)
                xx = x*math.cos(phase*.3) - z*math.sin(phase*.3)
                zz = x*math.sin(phase*.3) + z*math.cos(phase*.3)
                points.append((cx+xx*radius*.45, cy+(y*.7+zz*.3)*radius*.45))
            for i, j, item in self.field_items["cube"]:
                canvas.coords(item, *points[i], *points[j])
            for i, j, item in self.field_items["particles"]:
                x, y = nodes[i]
                xx, yy = nodes[(i+1) % 3]
                t = (phase*.4+j/3) % 1
                px, py = x+(xx-x)*t, y+(yy-y)*t
                canvas.coords(item, px-3, py-3, px+3, py+3)
                canvas.itemconfigure(item, state="normal" if self.engine.state == "RUNNING" else "hidden")
            latest = self.engine.history[-1] if self.engine.history else None
            values = (latest.self_value, latest.balance, latest.output) if latest else (0, 0, 0)
            for i, ((arc, border, item), value) in enumerate(zip(self.field_items["nodes"], values)):
                canvas.itemconfigure(arc, start=(phase*40+i*120) % 360)
                canvas.itemconfigure(border, width=3 if i == self.selected_node else 2)
                canvas.itemconfigure(item, text=f"{value:+.2f}" if abs(value) >= .005 else "+0.00")
            if height >= 275:
                detail = "Receive  →  respond  →  balance  →  mirror  →  contain"
                if self.selected_node is not None:
                    detail = ("Local self smooths the incoming signal using your chosen mind mode.",
                              "God self pulls the response towards your configured balance target.",
                              "External vector mirrors the balanced response within its containment limit.")[self.selected_node]
                canvas.itemconfigure(self.field_items["detail"], text=detail, fill=TEAL if self.selected_node is not None else MUTED)
            active = (self.engine.cycle-1) % len(LAYERS) if self.engine.cycle else -1
            for i, (box, label) in enumerate(self.field_items["layers"]):
                canvas.itemconfigure(box, fill="#183d40" if i == active else PANEL)
                canvas.itemconfigure(label, fill=TEAL if i == active else MUTED)


        def draw_chart(self):
            canvas=self.chart;width,height=canvas.winfo_width(),canvas.winfo_height()
            stamp=(width,height,self.engine.cycle,len(self.engine.history))
            if stamp==self.last_chart_state:
                return
            self.last_chart_state=stamp;canvas.delete("all")
            if width<100:
                return
            canvas.create_text(16,17,text="SIGNAL HISTORY",fill=MUTED,font=("Segoe UI",9,"bold"),anchor="w")
            canvas.create_text(width-160,17,text="— Input",fill=TEAL,font=("Segoe UI",9),anchor="w")
            canvas.create_text(width-85,17,text="— Output",fill=BLUE,font=("Segoe UI",9),anchor="w")
            top,bottom,left,right=36,height-17,38,width-18
            for i,label in enumerate(("+1","0","−1")):
                y=top+(bottom-top)*i/2
                canvas.create_line(left,y,right,y,fill=LINE)
                canvas.create_text(17,y,text=label,fill=MUTED,font=("Consolas",8))
            samples=list(self.engine.history)[-140:]
            if not samples:
                canvas.create_text(left+15,(top+bottom)/2-12,text="Start a session to plot input and processed output.",fill=MUTED,font=("Segoe UI",9),anchor="w")
            for field,color in (("input",TEAL),("output",BLUE)):
                points=[]
                for i,sample in enumerate(samples):
                    points.extend((left+(right-left)*i/max(1,len(samples)-1),top+(1-getattr(sample,field))*(bottom-top)/2))
                if len(points)>=4:
                    canvas.create_line(*points,fill=color,width=2 if field=="output" else 1)

        def close(self):
            if self.closed:
                return
            self.closed=True;self.cancel.set();self.generation+=1
            root.after_cancel(self.after_id)
            self.audit("close",{"cycle":self.engine.cycle})
            self.journal.close()
            root.destroy()

    return App()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir",type=Path,default=DATA_DIR,help="Folder for local rules, notes and audit history")
    parser.add_argument("--self-test",action="store_true",help="Run a quick processing and persistence check")
    args=parser.parse_args()
    if args.self_test:
        with tempfile.TemporaryDirectory(prefix="core-selftest-", dir=APP_DIR) as folder:
            engine=CoreEngine(Framework(cycles=3));engine.enqueue("Self-test","progress",.75);engine.start()
            while engine.state=="RUNNING":
                engine.tick()
            assert engine.cycle==3 and engine.processed==1
            journal=Journal(Path(folder)/"check.sqlite3")
            journal.append("check",{},engine.snapshot());assert journal.verify()==1
            assert journal.restore()==engine.snapshot();journal.close()
        print("PASS: core processing, repeatable state, persistence and audit integrity")
        return
    import tkinter as tk
    from tkinter import messagebox
    root=tk.Tk()
    root.withdraw()
    try:
        app=build_app(root,args.data_dir)
    except Exception as exc:
        messagebox.showerror("Core Interaction System",f"The workspace could not open:\n\n{exc}\n\nExisting data was preserved.",parent=root)
        root.destroy()
        raise
    root.deiconify()
    root.mainloop()


if __name__=="__main__":
    main()
