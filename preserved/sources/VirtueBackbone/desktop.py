"""Desktop monitor and corpus editor for the local communication backbone."""
import json
from pathlib import Path
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import uuid

from backbone import BASE, Client, HZ


class Desktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Virtue Backbone | Texts & services")
        self.geometry("1120x800")
        self.minsize(940, 680)
        self.configure(bg="#101923")
        self.events, self.commands = queue.Queue(), queue.Queue()
        self.stop = threading.Event()
        self.child = None
        self.logfile = None
        self.graph = {"nodes": [], "edges": []}
        self.selected = {}
        self.last_pulse = 0
        self.intervals = []
        self.port = 17830
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#101923")
        style.configure("TLabel", background="#101923", foreground="#dfebf2", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("TNotebook", background="#101923", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9))
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10))
        header = ttk.Frame(self, padding=(24, 20, 24, 10))
        header.pack(fill="x")
        ttk.Label(header, text="VIRTUE BACKBONE", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(header, text="A shared rhythm for software. A traceable map of ideas.", foreground="#9fb6c9").pack(anchor="w", pady=(5, 12))
        self.status = tk.StringVar(value="Starting local backbone…")
        ttk.Label(header, textvariable=self.status, foreground="#7ce1bb").pack(anchor="w")
        self.metrics = tk.StringVar(value="Target 7.83 Hz  ·  Waiting for measured timing")
        ttk.Label(header, textvariable=self.metrics, font=("Consolas", 12)).pack(anchor="w", pady=(9, 0))
        self.chart = tk.Canvas(header, height=46, bg="#152330", highlightthickness=0)
        self.chart.pack(fill="x", pady=(12, 0))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=12)
        texts, services, discovery = [ttk.Frame(self.tabs, padding=12) for _ in range(3)]
        self.tabs.add(texts, text="Text knowledge map")
        self.tabs.add(services, text="Connected services")
        self.tabs.add(discovery, text="Source discovery")
        toolbar = ttk.Frame(texts)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Import texts…", command=self.import_texts).pack(side="left")
        ttk.Button(toolbar, text="Export map…", command=self.export_map).pack(side="left", padx=8)
        ttk.Label(toolbar, text="Links show interpretations; source references stay attached.", foreground="#9fb6c9").pack(side="left", padx=8)
        self.map = tk.Canvas(texts, height=245, bg="#152330", highlightthickness=0)
        self.map.pack(fill="both", expand=True)
        self.map.bind("<Configure>", lambda event: self.draw_map())
        self.sources = ttk.Treeview(texts, columns=("title", "reference"), show="headings", height=4)
        self.sources.heading("title", text="Text")
        self.sources.heading("reference", text="Passage / edition")
        self.sources.column("title", width=220)
        self.sources.column("reference", width=600)
        self.sources.pack(fill="x", pady=(10, 0))
        self.sources.bind("<<TreeviewSelect>>", self.show_source)
        self.detail = tk.Text(texts, height=4, wrap="word", bg="#101923", fg="#dfebf2", relief="flat", font=("Segoe UI", 10))
        self.detail.pack(fill="x", pady=(8, 0))
        self.detail.configure(state="disabled")
        self.service_table = ttk.Treeview(services, columns=("service", "topics"), show="headings")
        for key, label in [("service", "Service"), ("topics", "Subscriptions")]:
            self.service_table.heading(key, text=label)
        self.service_table.column("service", width=270)
        self.service_table.column("topics", width=650)
        self.service_table.pack(fill="both", expand=True)
        ttk.Label(services, text="Only authenticated participants appear here. Finding an application on disk does not connect it.", foreground="#9fb6c9").pack(anchor="w", pady=12)
        self.discovery_text = tk.Text(discovery, wrap="word", bg="#152330", fg="#dfebf2", relief="flat", font=("Segoe UI", 11), padx=18, pady=18)
        self.discovery_text.pack(fill="both", expand=True)
        self.load_discovery()
        footer = ttk.Frame(self, padding=(24, 0, 24, 16))
        footer.pack(fill="x")
        ttk.Label(footer, text="Local software heartbeat · timing varies with system load · close this window to stop its backbone", foreground="#9fb6c9").pack(side="left")
        self.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self.worker, daemon=True).start()
        self.after(80, self.poll)

    def load_discovery(self):
        report = BASE / "reports" / "source-inventory.json"
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            s = data["summary"]
            text = f"{s['source_count']} source files inspected\n{s['languages']}\n{s['interface_candidates']} files contain possible communication interfaces.\n\n"
            text += "Running programs: " + data["process_scan"]["status"] + "\n"
            text += data["process_scan"].get("reason", "") + "\n\n"
            text += "Existing applications need a compatible adapter to participate. This scan reads source files without importing or executing them.\n\n"
            text += "Full inventory: reports/source-inventory.json\n\n"
            for f in data["files"]:
                if set(f["capabilities"]) & {"tcp-listener", "http", "udp"}:
                    text += f["path"] + "\n  " + ", ".join(f["capabilities"]) + "\n\n"
        except (OSError, ValueError):
            text = "No source inventory yet. Run scan_sources.py to inspect selected application folders."
        self.discovery_text.insert("1.0", text)
        self.discovery_text.configure(state="disabled")

    def connect(self):
        return Client(self.port, BASE / "data" / "token.txt", "desktop-" + uuid.uuid4().hex[:8],
                      ["pulse", "knowledge.updated", "service.status"])

    def worker(self):
        client = None
        try:
            try:
                client = self.connect()
            except (OSError, EOFError, ConnectionError):
                (BASE / "data").mkdir(exist_ok=True)
                self.logfile = (BASE / "data" / "server.log").open("a", encoding="utf-8")
                self.child = subprocess.Popen([sys.executable, str(BASE / "backbone.py"), "serve", "--port", str(self.port)],
                    cwd=BASE, stdout=self.logfile, stderr=self.logfile,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                for _ in range(50):
                    if self.stop.wait(.1):
                        return
                    if self.child.poll() is not None:
                        raise RuntimeError("The backbone could not start. Check data/server.log; the port may already be in use.")
                    try:
                        client = self.connect()
                        break
                    except (OSError, EOFError, ConnectionError):
                        continue
                if client is None:
                    raise RuntimeError("The backbone did not respond within five seconds.")
            client.publish("service.status", {"role": "text-map-monitor", "state": "ready"})
            self.events.put(("graph", client.graph()))
            last_status = 0
            while not self.stop.is_set():
                while not self.commands.empty():
                    kind, data = self.commands.get_nowait()
                    if kind == "import":
                        completed = 0
                        for p in data:
                            try:
                                client.request("import", passage=p)
                                completed += 1
                            except ValueError as exc:
                                self.events.put(("import-error", f"Imported {completed} passage(s); the next passage was rejected: {exc}"))
                                break
                        self.events.put(("graph", client.graph()))
                        if completed == len(data):
                            self.events.put(("notice", f"Imported {completed} passage(s)."))
                msg = client.receive()
                if msg.get("topic") == "pulse":
                    self.events.put(("pulse", msg["data"]))
                elif msg.get("topic") == "knowledge.updated":
                    self.events.put(("graph", client.graph()))
                if time.monotonic() - last_status >= 1:
                    self.events.put(("status", client.request("status")["data"]))
                    last_status = time.monotonic()
        except Exception as exc:
            self.events.put(("error", str(exc)))
        finally:
            if client:
                client.close()
            if self.stop.is_set():
                self.stop_owned_server()

    def poll(self):
        while not self.events.empty():
            kind, data = self.events.get_nowait()
            if kind == "error":
                self.status.set("Connection stopped: " + data)
            elif kind == "notice":
                messagebox.showinfo("Texts imported", data, parent=self)
            elif kind == "import-error":
                messagebox.showerror("Import incomplete", data, parent=self)
            elif kind == "graph":
                self.graph = data
                self.sources.delete(*self.sources.get_children())
                self.selected = {n["id"]: n for n in data["nodes"] if n["type"] == "passage"}
                for id_, node in self.selected.items():
                    self.sources.insert("", "end", iid=id_, values=(node["title"], node["reference"]))
                self.draw_map()
            elif kind == "status":
                hz = data["measured_hz"]
                rate = f"{hz:.3f}" if hz is not None else "warming up"
                self.metrics.set(f"Target 7.83 Hz  |  Measured {rate} Hz  |  Pulses {data['pulse_count']}  |  Missed {data['skipped_ticks']}")
                self.status.set(f"Connected · 127.714 ms target interval · {len(data['services'])} software service(s)")
                self.service_table.delete(*self.service_table.get_children())
                for row in data["services"]:
                    self.service_table.insert("", "end", values=(row["id"], ", ".join(row["topics"])))
            elif kind == "pulse":
                now = data["sent_monotonic_ns"] / 1e9
                if self.last_pulse:
                    self.intervals.append((now - self.last_pulse) * 1000)
                    self.intervals = self.intervals[-100:]
                self.last_pulse = now
                self.draw_chart()
        if not self.stop.is_set():
            self.after(80, self.poll)

    def draw_chart(self):
        c = self.chart
        c.delete("all")
        w = max(c.winfo_width(), 100)
        c.create_line(0, 24, w, 24, fill="#34546a", dash=(4, 4))
        for i, value in enumerate(self.intervals):
            x = 8 + i * (w - 16) / 100
            y = 24 - max(-20, min(20, (value - 1000 / HZ) * 2))
            c.create_line(x, 24, x, y, fill="#7ce1bb", width=3)
        c.create_text(w-12, 9, anchor="ne", text="Pulse interval deviation · centre = target", fill="#9fb6c9", font=("Segoe UI", 8))

    def draw_map(self):
        c = self.map
        c.delete("all")
        texts = [n for n in self.graph["nodes"] if n["type"] == "passage"][:12]
        themes = [n for n in self.graph["nodes"] if n["type"] == "theme"]
        w, h = max(c.winfo_width(), 600), max(c.winfo_height(), 220)
        coords = {}
        for i, n in enumerate(texts):
            coords[n["id"]] = (w*.28, 24+(i+.5)*(h-48)/max(1,len(texts)))
        for i, n in enumerate(themes):
            coords[n["id"]] = (w*.75, 24+(i+.5)*(h-48)/max(1,len(themes)))
        for edge in self.graph["edges"]:
            if edge["from"] in coords and edge["to"] in coords:
                c.create_line(*coords[edge["from"]], *coords[edge["to"]], fill="#436875", width=2,
                              dash=(4,3) if edge["basis"] == "keyword-suggestion" else ())
        for n in texts+themes:
            x,y = coords[n["id"]]
            c.create_oval(x-5,y-5,x+5,y+5,fill="#7ce1bb",outline="")
            label = n["title"] if n["type"] == "theme" else n["title"]+" · "+n["reference"].split(",")[0]
            if len(label)>34: label=label[:31]+"…"
            c.create_text(x-12 if n["type"]=="passage" else x+12,y,text=label,
                          anchor="e" if n["type"]=="passage" else "w",fill="#dfebf2",font=("Segoe UI",9))
        if not texts:
            c.create_text(w/2,h/2,text="Waiting for the text map…",fill="#9fb6c9")
        if len(self.selected)>12:
            c.create_text(10,10,anchor="nw",text="First 12 passages shown; all passages are listed below.",fill="#9fb6c9")

    def show_source(self, event=None):
        selection = self.sources.selection()
        if not selection: return
        n = self.selected[selection[0]]
        self.detail.configure(state="normal")
        self.detail.delete("1.0","end")
        self.detail.insert("1.0", f"{n['text']}\n{n['author']} · {n['reference']} · {n['kind']}\nSource: {n['source']}")
        self.detail.configure(state="disabled")

    def import_texts(self):
        path = filedialog.askopenfilename(parent=self,title="Import passages with source references",filetypes=[("JSON passages","*.json")])
        if not path: return
        try:
            if Path(path).stat().st_size > 2_000_000: raise ValueError("Import file exceeds 2 MB")
            passages = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            if isinstance(passages,dict): passages=[passages]
            if not isinstance(passages,list) or not passages: raise ValueError("Expected a non-empty list of passages")
            self.commands.put(("import",passages))
        except (OSError,ValueError) as exc:
            messagebox.showerror("Could not import",str(exc),parent=self)

    def export_map(self):
        path = filedialog.asksaveasfilename(parent=self,title="Save knowledge map",defaultextension=".json",initialfile="knowledge-map.json")
        if path:
            try: Path(path).write_text(json.dumps(self.graph,ensure_ascii=False,indent=2),encoding="utf-8")
            except OSError as exc: messagebox.showerror("Could not save",str(exc),parent=self)

    def stop_owned_server(self):
        if self.child and self.child.poll() is None:
            self.child.terminate()
            try: self.child.wait(timeout=3)
            except subprocess.TimeoutExpired: self.child.kill()
        if self.logfile:
            self.logfile.close()

    def close(self):
        self.stop.set()
        self.stop_owned_server()
        self.destroy()


if __name__ == "__main__":
    Desktop().mainloop()
