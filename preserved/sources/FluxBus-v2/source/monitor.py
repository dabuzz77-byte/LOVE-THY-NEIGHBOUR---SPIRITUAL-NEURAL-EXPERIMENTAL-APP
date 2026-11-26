"""Live, thread-safe telemetry for Python, Java and Opera process families."""
import copy
import os
import re
import random
import threading
import time
from collections import deque

try:
    import psutil
    PSUTIL_ACTIVE = True
except ImportError:
    psutil = None
    PSUTIL_ACTIVE = False

FAMILIES = ("python", "java", "opera")


def basename(value):
    return (value or "").replace("\\", "/").rsplit("/", 1)[-1].lower()


def classify(name, exe="", cmdline=None):
    """Match runtime executables, not incidental paths in editor/shell arguments."""
    names = {basename(name), basename(exe)}
    names = {n.removesuffix(".exe") for n in names}
    if any(re.fullmatch(r"(?:python(?:w|\d+(?:\.\d+)*(?:t|w)?)?|pypy(?:\d+(?:\.\d+)*)?|py)", n)
           for n in names):
        return "python"
    if names & {"java", "javaw", "javaws", "javac", "jshell", "jjs"}:
        return "java"
    if names & {"opera", "opera_gx", "opera_crashreporter"}:
        return "opera"
    # Opera's crash handlers are separate executables under its own installation.
    parts = (exe or "").lower().replace("\\", "/").split("/")
    if names & {"crashpad_handler", "launcher", "browser_assistant"} and any(
        part in {"opera", "opera gx", "opera developer", "opera beta", "opera air"} for part in parts
    ):
        return "opera"
    return None


def entrypoint(cmdline, family, name):
    args = cmdline or []
    for arg in args[1:]:
        if str(arg).lower().endswith((".py", ".pyw", ".pyc", ".java", ".jar")):
            return str(arg)
    if family == "python" and "-m" in args:
        index = args.index("-m")
        if index + 1 < len(args):
            return "module: " + args[index + 1]
    if family == "opera":
        for arg in args:
            if str(arg).startswith("--type="):
                return str(arg).split("=", 1)[1]
        return "browser / main"
    return name or "Metadata unavailable"


class SystemBusMonitor:
    def __init__(self, interval=1.5, demo=False):
        self.lock = threading.Lock()
        self.interval = interval
        self.demo = bool(demo or not PSUTIL_ACTIVE)
        self.running = True
        self.stop_event = threading.Event()
        self.wake_event = threading.Event()
        self.active_busses = dict.fromkeys(FAMILIES, 0)
        self.history = deque(maxlen=240)
        self.events = deque(maxlen=250)
        self.previous = {}
        self.sequence = 0
        self.thread = None
        self.snapshot = self.empty_snapshot()

    def empty_snapshot(self):
        return {"sequence": 0, "timestamp": None, "mode": "DEMO" if self.demo else "CONNECTING",
                "counts": dict.fromkeys(FAMILIES, 0), "processes": [], "host_cpu": None,
                "host_memory": None, "memory_used": 0, "memory_total": 0,
                "total_processes": 0, "partial_processes": 0, "scan_ms": 0,
                "error": "", "history": [], "events": []}

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.scan_process_bus, name="FluxBus telemetry", daemon=True)
            self.thread.start()

    def refresh(self):
        self.wake_event.set()

    def set_interval(self, interval):
        self.interval = float(interval)
        self.refresh()

    def scan_process_bus(self):
        while not self.stop_event.is_set() and self.running:
            self.sample_once()
            self.wake_event.wait(self.interval)
            self.wake_event.clear()

    def sample_once(self):
        start = time.perf_counter()
        try:
            result = self._demo_sample() if self.demo else self._live_sample()
        except Exception as error:
            # Keep the last successful sample; never replace an OS error with invented zeros.
            with self.lock:
                self.snapshot = {**self.snapshot, "mode": "STALE", "error": str(error)}
            return self.get_snapshot()
        self.sequence += 1
        now = time.time()
        counts = {family: sum(p["family"] == family for p in result["processes"]) for family in FAMILIES}
        identities = {(p["pid"], p["started"]): p for p in result["processes"]}
        if self.previous or self.sequence > 1:
            for key in identities.keys() - self.previous.keys():
                p = identities[key]
                self.events.appendleft({"time": now, "event": "STARTED", "pid": p["pid"], "name": p["name"], "family": p["family"]})
            for key in self.previous.keys() - identities.keys():
                p = self.previous[key]
                self.events.appendleft({"time": now, "event": "EXITED", "pid": p["pid"], "name": p["name"], "family": p["family"]})
        self.previous = identities
        self.history.append({"time": now, **counts, "cpu": result["host_cpu"], "memory": result["host_memory"]})
        with self.lock:
            self.active_busses = counts
            self.snapshot = {**result, "sequence": self.sequence, "timestamp": now,
                             "mode": "DEMO" if self.demo else "LIVE", "counts": counts,
                             "scan_ms": (time.perf_counter() - start) * 1000,
                             "error": "", "history": list(self.history), "events": list(self.events)}
        return self.get_snapshot()

    def _live_sample(self):
        gathered = {}
        refs = {}
        for proc in psutil.process_iter(["pid", "ppid", "name", "exe", "cmdline", "create_time"], ad_value=None):
            try:
                info = proc.info
                family = classify(info.get("name"), info.get("exe"), info.get("cmdline"))
                gathered[proc.pid] = {"pid": proc.pid, "ppid": info.get("ppid"),
                    "name": info.get("name") or "Unavailable", "exe": info.get("exe") or "",
                    "cmdline": info.get("cmdline") or [], "family": family, "direct": bool(family),
                    "started": info.get("create_time"), "partial": info.get("cmdline") is None,
                    "cpu": None, "memory": None, "status": "unavailable"}
                refs[proc.pid] = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        # Include every descendant, even helpers with unrelated executable names.
        changed = True
        while changed:
            changed = False
            for row in gathered.values():
                parent = gathered.get(row["ppid"])
                if not row["family"] and parent and parent["family"]:
                    row["family"] = parent["family"]
                    changed = True
        rows = []
        cores = psutil.cpu_count() or 1
        for pid, row in gathered.items():
            if not row["family"]:
                continue
            proc = refs[pid]
            try:
                with proc.oneshot():
                    measured = proc.cpu_percent(interval=None) / cores
                    row["cpu"] = measured if (pid, row["started"]) in self.previous else None
                    row["memory"] = proc.memory_info().rss
                    row["status"] = proc.status()
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            except psutil.AccessDenied:
                row["partial"] = True
            row["entry"] = entrypoint(row["cmdline"], row["family"], row["name"])
            rows.append(row)
        memory = psutil.virtual_memory()
        host_cpu = psutil.cpu_percent(interval=None)
        return {"processes": sorted(rows, key=lambda p: (p["family"], p["pid"])),
                "host_cpu": host_cpu if self.sequence else None, "host_memory": memory.percent,
                "memory_used": memory.used, "memory_total": memory.total,
                "total_processes": len(gathered), "partial_processes": sum(p["partial"] for p in rows)}

    def _demo_sample(self):
        rows = []
        now = time.time()
        for index, family in enumerate(FAMILIES):
            count = 3 + round(math_wave(self.sequence * .3 + index) * 2)
            for offset in range(count):
                rows.append({"pid": 1000 + index * 100 + offset, "ppid": 0, "family": family,
                             "name": family + ".exe", "exe": "Simulated process", "cmdline": [],
                             "started": 0, "partial": False, "direct": True,
                             "cpu": round(random.uniform(.1, 4), 1), "memory": (70 + offset * 20) * 1048576,
                             "status": "simulated", "entry": "Demo telemetry"})
        return {"processes": rows, "host_cpu": 20 + 10 * math_wave(now * .3), "host_memory": 38.4,
                "memory_used": 6 * 1073741824, "memory_total": 16 * 1073741824,
                "total_processes": len(rows), "partial_processes": 0}

    def get_counts(self):
        with self.lock:
            return self.active_busses.copy()

    def get_snapshot(self):
        with self.lock:
            return copy.deepcopy(self.snapshot)

    def stop(self, timeout=4):
        self.running = False
        self.stop_event.set()
        self.wake_event.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout)


def math_wave(x):
    import math
    return math.sin(x)
