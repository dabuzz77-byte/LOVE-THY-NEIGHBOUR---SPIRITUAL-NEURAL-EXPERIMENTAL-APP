"""Godmind Mesh Desktop — run this .py file with Python 3.10+ and NumPy.

Native Tk desktop interface. No browser or web server is needed. The optional
loopback TCP gateway starts only when its button is pressed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import threading
import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "neural_lab"))
from drillscript import RecursiveDrillEngine, inputs
from original_logic import report as original_report
from neural_weight import StructuralStateLedger, BackgroundWeightOptimizer, ProductionNetworkGateway

BG = "#0a1018"
PANEL = "#111b28"
EDGE = "#293849"
INK = "#e1eaf3"
MUTED = "#94a8bd"
MINT = "#73dfb9"
CORAL = "#f18a98"
BLUE = "#86b9eb"
GOLD = "#dbc893"
PROFILE_NAMES = ["Energetic resonance", "Spiritual cultivation", "Systemic automation",
                 "Resource optimization", "Sky elevator"]


class DesktopSession:
    """Single owner for the neural classifier, shared weight ledger and workers."""

    def __init__(self, data_directory=None):
        self.data_directory = Path(data_directory or ROOT / "data")
        self.neural = RecursiveDrillEngine(checkpoint_path=self.data_directory / "neural.json")
        self.ledger = StructuralStateLedger()
        self.optimizer = BackgroundWeightOptimizer(self.ledger)
        self.gateway = ProductionNetworkGateway(self.ledger)
        self.lock = threading.RLock()
        self.closed = False

    def start_workers(self):
        self.neural.start_worker()
        if not self.optimizer.is_alive():
            self.optimizer.start()

    def snapshot(self, probe=(.25, .25)):
        with self.lock:
            neural = self.neural.snapshot(probe)
            with self.optimizer.step_lock:
                ledger, optimizer = self.ledger.to_dict(), self.optimizer.snapshot()
            return {"neural": neural, "ledger": ledger, "optimizer": optimizer,
                    "gateway": self.gateway.snapshot()}

    def checkpoint(self):
        with self.lock, self.optimizer.step_lock:
            return {"format": "godmind-desktop", "version": 1,
                    "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "neural": self.neural.checkpoint(), "ledger": self.ledger.to_dict(),
                    "optimizer": self.optimizer.snapshot()}

    def save(self, path=None):
        path = Path(path or self.data_directory / "last_session.json")
        payload = json.dumps(self.checkpoint(), allow_nan=False, indent=2)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return path

    def load_data(self, data):
        if not isinstance(data, dict):
            raise ValueError("Choose a Godmind JSON session or neural checkpoint.")
        # Validate every component before pausing or changing the live session.
        neural_data = data if data.get("format") == "godmind-mesh" else data.get("neural")
        candidate = RecursiveDrillEngine()
        candidate.load(neural_data)
        ledger_data, optimizer_data = None, None
        if data.get("format") != "godmind-mesh":
            if data.get("format") != "godmind-desktop" or data.get("version") != 1:
                raise ValueError("Unsupported desktop session version.")
            ledger_data = StructuralStateLedger.from_dict(data.get("ledger")).to_dict()
            optimizer_data = data.get("optimizer")
            BackgroundWeightOptimizer.validate_state(optimizer_data)
        with self.lock:
            self.optimizer.pause_engine()
            self.gateway.stop_gateway()
            self.neural.load(neural_data)
            if ledger_data is not None:
                self.ledger.restore(ledger_data)
                self.optimizer.restore(optimizer_data)
            with self.gateway._lock:
                self.gateway.events.clear()
                self.gateway.last_response = None

    def load(self, path):
        path = Path(path)
        if path.stat().st_size > 5_000_000:
            raise ValueError("Session files must be smaller than 5 MB.")
        self.load_data(json.loads(path.read_text(encoding="utf-8-sig")))

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.gateway.stop_gateway()
        self.optimizer.stop_engine()
        self.neural.close()


class GodmindDesktop(tk.Tk):
    def __init__(self, session=None, start_workers=True, restore_last=True, visible=True):
        super().__init__()
        if not visible:
            self.withdraw()
        self.title("Godmind Mesh · Desktop Neural Lab")
        self.geometry("1450x940")
        self.minsize(1080, 780)
        self.configure(bg=BG)
        self.session = session or DesktopSession()
        self.latest = None
        self.probe = (.25, .25)
        self.map_bounds = None
        self.timer = None
        self.closing = False
        self.event_signature = None
        self.last_gate_signature = None
        self.styles()
        self.status = tk.StringVar(value="Ready. Start a learning engine or add your own examples.")
        self.autosave = tk.BooleanVar(value=True)
        self.build_header()
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel", anchor="w").pack(side="bottom", fill="x", padx=24, pady=(0, 12))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(4, 12))
        self.neural_tab = ttk.Frame(self.tabs, padding=12)
        self.weight_tab = ttk.Frame(self.tabs, padding=12)
        self.original_tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(self.neural_tab, text="  Neural lab  ")
        self.tabs.add(self.weight_tab, text="  Weight & text engine  ")
        self.tabs.add(self.original_tab, text="  Original logic  ")
        self.build_neural()
        self.build_weights()
        self.build_originals()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        if restore_last and (self.session.data_directory / "last_session.json").is_file():
            try:
                self.session.load(self.session.data_directory / "last_session.json")
                self.status.set("Previous session restored. Both learning engines are paused.")
            except (ValueError, OSError, TypeError, KeyError) as error:
                self.status.set(f"Could not restore the last session: {error}")
        self.sync_controls()
        if start_workers:
            self.session.start_workers()
        self.tick()

    def styles(self):
        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*TCombobox*Listbox.background", PANEL)
        self.option_add("*TCombobox*Listbox.foreground", INK)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=INK, bordercolor=EDGE, lightcolor=EDGE,
                        darkcolor=EDGE, troughcolor=BG, focuscolor=MINT)
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=INK)
        style.configure("Panel.TLabel", background=PANEL)
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 22))
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 12))
        style.configure("TButton", padding=(10, 7), background="#1a293a", borderwidth=1)
        style.map("TButton", background=[("active", "#294257"), ("disabled", "#152130")],
                  foreground=[("disabled", "#64798c")])
        style.configure("Accent.TButton", background=MINT, foreground="#10251f", font=("Segoe UI Semibold", 10))
        style.map("Accent.TButton", background=[("active", "#a3efd5")], foreground=[("active", "#10251f")])
        style.configure("TEntry", fieldbackground="#152131", foreground=INK, insertcolor=INK, padding=5)
        style.configure("TCombobox", fieldbackground="#152131", foreground=INK, arrowsize=14, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", "#152131")], foreground=[("readonly", INK)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), background="#121d2a", foreground=MUTED)
        style.map("TNotebook.Tab", background=[("selected", "#223446")], foreground=[("selected", MINT)], padding=[("selected", (18, 10))])
        style.configure("TCheckbutton", padding=4)
        style.map("TCheckbutton", indicatorbackground=[("selected", MINT)])
        style.configure("TLabelframe", bordercolor=EDGE, background=BG)
        style.configure("TLabelframe.Label", foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Horizontal.TScale", background=BG, troughcolor="#223448")

    def build_header(self):
        header = ttk.Frame(self, padding=(22, 18, 22, 10))
        header.pack(fill="x")
        title = ttk.Frame(header)
        title.pack(side="left")
        ttk.Label(title, text="GODMIND  MESH", style="Title.TLabel", font=("Segoe UI Semibold",22)).pack(anchor="w")
        ttk.Label(title, text="DESKTOP / LOCAL LEARNING / SHARED STATE", style="Muted.TLabel").pack(anchor="w")
        toolbar = ttk.Frame(header)
        toolbar.pack(side="right")
        ttk.Button(toolbar, text="Open session", command=self.open_session).grid(row=0, column=0, padx=4)
        ttk.Button(toolbar, text="Save session", command=self.save_session, style="Accent.TButton").grid(row=0, column=1, padx=4)
        ttk.Checkbutton(toolbar, text="Save on exit", variable=self.autosave).grid(row=1, column=0, columnspan=2, sticky="e", pady=(5,0))

    def field(self, parent, label, variable, values=None, width=22):
        ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor="w", pady=(10, 3))
        if values:
            widget = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=width)
        else:
            widget = ttk.Entry(parent, textvariable=variable, width=width)
        widget.pack(fill="x")
        return widget

    def button_row(self, parent, buttons):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(7,0))
        for text, action in buttons:
            ttk.Button(row, text=text, command=action).pack(side="left", fill="x", expand=True, padx=2)
        return row

    def sidebar(self, parent, width=258):
        """Keep every control reachable on smaller desktop displays."""
        outer=ttk.Frame(parent,padding=(0,0,12,0))
        outer.grid(row=0,column=0,sticky="nsew")
        canvas=tk.Canvas(outer,bg=BG,highlightthickness=0,width=width)
        scrollbar=ttk.Scrollbar(outer,orient="vertical",command=canvas.yview)
        scrollbar.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        content=ttk.Frame(canvas,padding=(0,0,8,10))
        window=canvas.create_window(0,0,window=content,anchor="nw")
        content.bind("<Configure>",lambda event:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda event:canvas.itemconfigure(window,width=event.width))
        return content

    def canvas_card(self, parent, title, subtitle, row, column, columnspan=1, height=260):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        card.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=5, pady=5)
        ttk.Label(card, text=title, style="Panel.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(card, text=subtitle, bg=PANEL, fg=MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(2,5))
        canvas = tk.Canvas(card, bg=PANEL, highlightthickness=0, height=height, width=180)
        canvas.pack(fill="both", expand=True)
        return canvas

    def stat_cards(self, parent, names):
        row = ttk.Frame(parent)
        row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0,8))
        variables = []
        for i, name in enumerate(names):
            row.columnconfigure(i, weight=1)
            frame = ttk.Frame(row, style="Panel.TFrame", padding=(14,12))
            frame.grid(row=0, column=i, sticky="nsew", padx=5)
            tk.Label(frame, text=name.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")
            value = tk.StringVar(value="—")
            tk.Label(frame, textvariable=value, bg=PANEL, fg=MINT if i==0 else INK,
                     font=("Consolas", 23)).pack(anchor="w", pady=(5,0))
            variables.append(value)
        return variables

    def build_neural(self):
        self.neural_tab.columnconfigure(1, weight=1)
        self.neural_tab.rowconfigure(0, weight=1)
        controls = self.sidebar(self.neural_tab)
        ttk.Label(controls, text="Experiment", style="Section.TLabel").pack(anchor="w")
        self.dataset = tk.StringVar(value="moons")
        self.seed = tk.StringVar(value="42")
        self.neural_rate = tk.StringVar(value="0.012")
        self.pace = tk.StringVar(value="Balanced")
        self.active_learning = tk.BooleanVar(value=False)
        self.field(controls, "Environment", self.dataset, ("moons", "rings", "xor", "spiral", "custom"))
        self.field(controls, "Random seed", self.seed)
        self.button_row(controls, [("New run", self.reset_neural), ("Single step", lambda:self.neural_action("step"))])
        self.neural_run = ttk.Button(controls, text="Start learning", style="Accent.TButton", command=self.toggle_neural)
        self.neural_run.pack(fill="x", pady=(10,0))
        self.field(controls, "Classifier learning rate", self.neural_rate)
        self.field(controls, "Training pace", self.pace, ("Gentle", "Balanced", "Fast"))
        ttk.Checkbutton(controls, text="Active learning · ask teacher", variable=self.active_learning,
                        command=self.configure_neural).pack(anchor="w", pady=(8,0))
        self.button_row(controls, [("Apply settings", self.configure_neural), ("Ask teacher", lambda:self.neural_action("reveal"))])
        ttk.Separator(controls).pack(fill="x", pady=15)
        ttk.Label(controls, text="Teach the network", style="Section.TLabel").pack(anchor="w")
        self.teach = tk.BooleanVar(value=False)
        self.point_class = tk.IntVar(value=0)
        ttk.Checkbutton(controls, text="Click map to add an example", variable=self.teach).pack(anchor="w", pady=5)
        choices = ttk.Frame(controls)
        choices.pack(fill="x")
        ttk.Radiobutton(choices, text="Coral · 0", variable=self.point_class, value=0).pack(side="left", padx=(0,12))
        ttk.Radiobutton(choices, text="Mint · 1", variable=self.point_class, value=1).pack(side="left")
        self.point_x, self.point_y = tk.StringVar(value="0.25"), tk.StringVar(value="0.25")
        points = ttk.Frame(controls)
        points.pack(fill="x", pady=8)
        ttk.Label(points, text="X").pack(side="left")
        ttk.Entry(points, textvariable=self.point_x, width=7).pack(side="left", padx=4)
        ttk.Label(points, text="Y").pack(side="left")
        ttk.Entry(points, textvariable=self.point_y, width=7).pack(side="left", padx=4)
        ttk.Button(controls, text="Add labeled example", command=self.add_typed_point).pack(fill="x")
        self.button_row(controls, [("Import CSV", self.import_csv), ("Export CSV", self.export_csv)])
        self.probe_text = tk.StringVar(value="Probe: (+0.25, +0.25)")
        ttk.Label(controls, textvariable=self.probe_text, style="Muted.TLabel", wraplength=232).pack(anchor="w", pady=(14,0))
        display = ttk.Frame(self.neural_tab)
        display.grid(row=0, column=1, sticky="nsew")
        display.columnconfigure(0, weight=1, uniform="neural")
        display.columnconfigure(1, weight=1, uniform="neural")
        display.rowconfigure(1, weight=3)
        display.rowconfigure(2, weight=2)
        self.neural_stats = self.stat_cards(display, ["Test accuracy", "Training loss", "Learning steps", "Labeled examples"])
        self.network_canvas = self.canvas_card(display, "Living network", "149 trainable parameters · nodes show the probe activation",1,0)
        self.map_canvas = self.canvas_card(display, "Decision landscape", "Background = prediction · dots = training examples",1,1)
        self.loss_canvas = self.canvas_card(display, "Learning over time", "Cross-entropy loss · mint = training · gold = held-out test",2,0, height=170)
        notebook = ttk.Frame(display, style="Panel.TFrame", padding=12)
        notebook.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        ttk.Label(notebook, text="Lab notebook", style="Panel.TLabel", font=("Segoe UI Semibold",11)).pack(anchor="w")
        self.neural_log = self.text_box(notebook, height=8)
        self.neural_insight = tk.StringVar()
        ttk.Label(display, textvariable=self.neural_insight, style="Muted.TLabel", wraplength=750).grid(row=3,column=0,columnspan=2,sticky="ew",padx=5,pady=6)
        self.map_canvas.bind("<Motion>", self.inspect_point)
        self.map_canvas.bind("<Button-1>", self.map_click)

    def text_box(self, parent, height=8, editable=False):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(8,0))
        text = tk.Text(frame, height=height, width=25, bg="#0b131e", fg=INK, insertbackground=MINT,
                       relief="flat", wrap="word", padx=10, pady=8, font=("Consolas",10))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        if not editable:
            text.configure(state="disabled")
        return text

    def build_weights(self):
        self.weight_tab.columnconfigure(1, weight=1)
        self.weight_tab.rowconfigure(0, weight=1)
        controls = self.sidebar(self.weight_tab)
        ttk.Label(controls,text="Profile optimizer",style="Section.TLabel").pack(anchor="w")
        ttk.Label(controls,text="Five weights → shared ledger → text/bit gate",style="Muted.TLabel",wraplength=248).pack(anchor="w",pady=(4,5))
        self.weight_run = ttk.Button(controls,text="Start weight engine",style="Accent.TButton",command=self.toggle_weights)
        self.weight_run.pack(fill="x",pady=8)
        self.weight_rate=tk.StringVar(value="0.05")
        self.clock_rate=tk.StringVar(value="7.83")
        self.field(controls,"Profile learning rate",self.weight_rate)
        self.field(controls,"Update frequency · Hz",self.clock_rate)
        self.button_row(controls,[("Apply settings",self.configure_weights),("Single step",self.step_weights)])
        ttk.Separator(controls).pack(fill="x",pady=14)
        ttk.Label(controls,text="Target profile",style="Section.TLabel").pack(anchor="w")
        self.target_vars=[]
        for name,value in zip(PROFILE_NAMES,[.90,.95,.85,.90,.95]):
            row=ttk.Frame(controls)
            row.pack(fill="x",pady=4)
            ttk.Label(row,text=name,style="Muted.TLabel").pack(side="left")
            variable=tk.StringVar(value=f"{value:.2f}")
            ttk.Entry(row,textvariable=variable,width=6).pack(side="right")
            self.target_vars.append(variable)
        ttk.Button(controls,text="Apply five targets",command=self.apply_targets).pack(fill="x",pady=5)
        ttk.Separator(controls).pack(fill="x",pady=14)
        ttk.Label(controls,text="Optional local TCP gateway",style="Section.TLabel").pack(anchor="w")
        self.port=tk.StringVar(value="9999")
        self.field(controls,"Port on 127.0.0.1",self.port)
        self.gateway_button=ttk.Button(controls,text="Start gateway",command=self.toggle_gateway)
        self.gateway_button.pack(fill="x",pady=8)
        self.gateway_status=tk.StringVar(value="OFF · in-app processing is available")
        ttk.Label(controls,textvariable=self.gateway_status,style="Muted.TLabel",wraplength=240).pack(anchor="w")
        ttk.Button(controls,text="Reset simulated counters",command=self.reset_counters).pack(fill="x",pady=(12,0))
        display=ttk.Frame(self.weight_tab)
        display.grid(row=0,column=1,sticky="nsew")
        display.columnconfigure(0,weight=1,uniform="weights")
        display.columnconfigure(1,weight=1,uniform="weights")
        display.rowconfigure(1,weight=2)
        display.rowconfigure(2,weight=3)
        self.weight_stats=self.stat_cards(display,["Mean integrity", "Target RMSE", "Profile steps", "Lower / baseline"])
        self.weight_canvas=self.canvas_card(display,"Five profile weights","Mint = current · gold tick = target",1,0,height=220)
        self.rmse_canvas=self.canvas_card(display,"Convergence trace","RMSE to the editable target profile · lower is closer",1,1,height=220)
        request_frame=ttk.Frame(display,style="Panel.TFrame",padding=12)
        request_frame.grid(row=2,column=0,sticky="nsew",padx=5,pady=5)
        ttk.Label(request_frame,text="Text & bit request",style="Panel.TLabel",font=("Segoe UI Semibold",11)).pack(anchor="w")
        tk.Label(request_frame,text="Uses the supplied keyword rules and mean ≥ 0.60",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",pady=4)
        self.intent_text=self.text_box(request_frame,height=5,editable=True)
        self.intent_text.insert("1.0","cooperation efficiency protect floor")
        self.bits=tk.StringVar(value="0, 1, 0, 1, 1, 0")
        ttk.Entry(request_frame,textvariable=self.bits).pack(fill="x",pady=8)
        ttk.Button(request_frame,text="Process text + bits",command=self.process_request,style="Accent.TButton").pack(fill="x")
        response_frame=ttk.Frame(display,style="Panel.TFrame",padding=12)
        response_frame.grid(row=2,column=1,sticky="nsew",padx=5,pady=5)
        self.gate_title=tk.StringVar(value="Gate result · awaiting a request")
        ttk.Label(response_frame,textvariable=self.gate_title,style="Panel.TLabel",font=("Segoe UI Semibold",11)).pack(anchor="w")
        self.gate_output=self.text_box(response_frame,height=10)
        self.ledger_summary=tk.StringVar()
        ttk.Label(display,textvariable=self.ledger_summary,style="Muted.TLabel",wraplength=790).grid(row=3,column=0,columnspan=2,sticky="ew",padx=5,pady=6)

    def build_originals(self):
        ttk.Label(self.original_tab,text="Original logic, preserved verbatim",style="Section.TLabel").pack(anchor="w")
        ttk.Label(self.original_tab,text="The four original scripts remain unchanged. These reports are separate from live training measurements.",
                  style="Muted.TLabel",wraplength=1050).pack(anchor="w",pady=8)
        ttk.Label(self.original_tab,text="The three neural-weight source files are also preserved in source_originals/neural_weight; their runnable integrations are in neural_weight/.",
                  style="Muted.TLabel",wraplength=1050).pack(anchor="w")
        self.original_output=self.text_box(self.original_tab,height=22)
        readout=original_report()
        self.replace_text(self.original_output,("VERIFIED · all four original files match their backup\n\n" if readout["all_sources_unchanged"] else "Original sources have been edited.\n\n")+readout["console"])

    @staticmethod
    def replace_text(widget,value):
        widget.configure(state="normal")
        widget.delete("1.0","end")
        widget.insert("1.0",value)
        widget.configure(state="disabled")

    def perform(self,action,message=None):
        try:
            result=action()
            if message:
                self.status.set(message)
            return result
        except (ValueError,OSError,TypeError,KeyError,RuntimeError,tk.TclError) as error:
            self.status.set(str(error))
            messagebox.showerror("Godmind Mesh",str(error),parent=self)
            return None

    def sync_controls(self):
        neural=self.session.neural
        self.dataset.set(neural.dataset);self.seed.set(str(neural.seed))
        self.neural_rate.set(f"{neural.model.learning_rate:g}")
        self.pace.set({1:"Gentle",4:"Balanced",12:"Fast"}[neural.speed])
        self.active_learning.set(neural.active)
        self.weight_rate.set(f"{self.session.optimizer.learning_rate:g}")
        self.clock_rate.set(f"{1/self.session.optimizer.interval:g}")
        for variable,value in zip(self.target_vars,self.session.ledger.get_weights()[1]):
            variable.set(f"{value:g}")

    def neural_action(self,action,data=None):
        self.perform(lambda:self.session.neural.command(action,data or {}))

    def toggle_neural(self):
        self.neural_action("pause" if self.session.neural.running else "start")

    def configure_neural(self):
        def apply():
            self.session.neural.command("configure",{"learning_rate":float(self.neural_rate.get()),
                "speed":{"Gentle":1,"Balanced":4,"Fast":12}[self.pace.get()],"active":self.active_learning.get()})
        self.perform(apply,"Classifier settings applied.")

    def reset_neural(self):
        if messagebox.askyesno("New experiment","Reset the classifier weights? Preset examples will be regenerated; imported examples will be kept.",parent=self):
            self.perform(lambda:self.session.neural.command("reset",{"dataset":self.dataset.get(),"seed":int(self.seed.get())}),"New neural experiment ready.")
            self.sync_controls()

    def add_typed_point(self):
        self.perform(lambda:self.session.neural.command("sample",{"x":float(self.point_x.get()),"y":float(self.point_y.get()),"label":self.point_class.get()}),"Labeled training example added.")

    def point_at(self,event):
        if self.map_bounds is None:return None
        left,top,size=self.map_bounds
        x=(event.x-left)/size;y=(event.y-top)/size
        return (2*x-1,1-2*y) if 0<=x<=1 and 0<=y<=1 else None

    def inspect_point(self,event):
        point=self.point_at(event)
        if point:self.probe=point

    def map_click(self,event):
        point=self.point_at(event)
        if point:
            self.probe=point
            self.point_x.set(f"{point[0]:.4f}");self.point_y.set(f"{point[1]:.4f}")
            if self.teach.get():
                self.perform(lambda:self.session.neural.command("sample",{"x":point[0],"y":point[1],"label":self.point_class.get()}),"Example added from the map.")

    def import_csv(self):
        path=filedialog.askopenfilename(parent=self,title="Import normalized examples",filetypes=[("CSV examples","*.csv")])
        if path and messagebox.askyesno("Import examples","Replace the classifier experiment with this CSV? 20% will be reserved for testing.",parent=self):
            def load():
                source=Path(path)
                if source.stat().st_size>700000:raise ValueError("CSV must be smaller than 700 KB.")
                self.session.neural.command("import",{"csv":source.read_text(encoding="utf-8-sig")})
                self.sync_controls()
            self.perform(load,"CSV imported. Start learning when ready.")

    def export_csv(self):
        path=filedialog.asksaveasfilename(parent=self,title="Export training examples",defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if path:
            def export():
                with self.session.neural.lock,open(path,"w",newline="",encoding="utf-8") as file:
                    writer=csv.writer(file);writer.writerow(["x","y","label"])
                    for point,label in zip(self.session.neural.train_x,self.session.neural.train_y):
                        writer.writerow([*map(float,point),int(label[0])])
            self.perform(export,"Training examples exported.")

    def toggle_weights(self):
        if self.session.optimizer.running:self.session.optimizer.pause_engine()
        else:self.perform(self.session.optimizer.resume_engine)

    def configure_weights(self):
        self.perform(lambda:self.session.optimizer.configure(float(self.weight_rate.get()),float(self.clock_rate.get())),"Profile optimizer settings applied.")

    def step_weights(self):
        self.session.optimizer.pause_engine()
        self.perform(self.session.optimizer.step_once)

    def apply_targets(self):
        def apply():
            with self.session.optimizer.step_lock:
                self.session.ledger.set_targets([float(v.get()) for v in self.target_vars])
        self.perform(apply,"Five target weights updated.")

    def toggle_gateway(self):
        if self.session.gateway.running:
            self.session.gateway.stop_gateway()
        else:
            def start():
                port=int(self.port.get())
                if not 1<=port<=65535:raise ValueError("Choose a TCP port from 1 to 65535.")
                self.session.gateway.port=port
                self.session.gateway.start_gateway()
            self.perform(start,"Local TCP gateway started.")

    def reset_counters(self):
        if messagebox.askyesno("Reset counters","Reset the simulated ledger counters to their original 1000 / 250 / 50 values?",parent=self):
            self.session.ledger.reset_counters()

    def process_request(self):
        def process():
            raw=self.bits.get().strip()
            if raw.startswith("["):bits=json.loads(raw)
            else:bits=[int(piece) for piece in raw.replace(","," ").split()]
            self.session.gateway.process_payload({"text":self.intent_text.get("1.0","end-1c"),"bits":bits})
        self.perform(process,"Request processed through the shared weight ledger.")

    def save_session(self):
        path=filedialog.asksaveasfilename(parent=self,title="Save complete Godmind session",defaultextension=".json",initialfile="godmind-session.json",filetypes=[("JSON session","*.json")])
        if path:self.perform(lambda:self.session.save(path),"Classifier, profile weights and ledger saved together.")

    def open_session(self):
        path=filedialog.askopenfilename(parent=self,title="Open desktop session or earlier neural checkpoint",filetypes=[("JSON session","*.json")])
        if path and messagebox.askyesno("Open session","Replace current progress with this file? Both learning engines will be paused.",parent=self):
            def load():
                self.session.load(path);self.sync_controls();self.last_gate_signature=None
            self.perform(load,"Session loaded. Both engines are paused; the gateway is off.")

    def tick(self):
        if self.closing:return
        if self.timer:
            self.after_cancel(self.timer)
            self.timer=None
        try:
            self.latest=self.session.snapshot(self.probe)
            self.update_readouts()
            selected=self.tabs.index(self.tabs.select())
            if selected==0:
                self.draw_network(self.latest["neural"])
                self.draw_map(self.latest["neural"])
                self.draw_trace(self.loss_canvas,self.latest["neural"]["history"],[("train_loss",MINT),("test_loss",GOLD)])
            elif selected==1:
                self.draw_weights(self.latest["ledger"])
                self.draw_trace(self.rmse_canvas,self.latest["optimizer"]["history"],[("rmse",MINT)])
        except Exception as error:
            self.status.set(f"Display update: {error}")
        self.timer=self.after(350,self.tick)

    def update_readouts(self):
        n,l,o,g=(self.latest[key] for key in ("neural","ledger","optimizer","gateway"))
        values=[f"{n['metrics']['test_accuracy']*100:.1f}%",f"{n['metrics']['train_loss']:.4f}",f"{n['steps']:,}",f"{n['train_count']:,}"]
        for variable,value in zip(self.neural_stats,values):variable.set(value)
        self.neural_run.configure(text="Pause learning" if n["running"] else "Start learning")
        self.neural_insight.set(f"{n['test_count']} held-out examples · {n['pool_count']} teacher examples remaining. {n['analysis']}")
        p=n["probe"]
        self.probe_text.set(f"Probe ({p['x']:+.2f}, {p['y']:+.2f})\nP(mint) = {p['probability']*100:.1f}%")
        events=json.dumps(n["events"])
        if events!=self.event_signature:
            self.event_signature=events
            self.replace_text(self.neural_log,"\n\n".join(f"{event['time'][11:19]}  {event['text']}" for event in n["events"]))
        nodes=l["nodes"]
        values=[f"{l['mean_system_integrity']:.3f}",f"{o['rmse']:.4f}",f"{o['steps']:,}",f"{nodes['lowest_floor_current']:g} / {nodes['lowest_floor_baseline']:g}"]
        for variable,value in zip(self.weight_stats,values):variable.set(value)
        self.weight_run.configure(text="Pause weight engine" if o["running"] else "Start weight engine")
        self.gateway_button.configure(text="Stop gateway" if g["running"] else "Start gateway")
        self.gateway_status.set(f"ON · {g['host']}:{g['port']}" if g["running"] else "OFF · in-app processing is available")
        self.ledger_summary.set(f"Simulated ledger: upper floor {nodes['upper_floor_wealth']:g} units · lower floor {nodes['lowest_floor_current']:g} · baseline {nodes['lowest_floor_baseline']:g}. The gate passes when keyword matches outweigh corporate matches and mean weight ≥ 0.60.")
        signature=json.dumps(g["last_response"])
        if signature!=self.last_gate_signature:
            self.last_gate_signature=signature
            response=g["last_response"]
            if response:
                self.gate_title.set(response["transformation_state"].replace("_"," "))
                self.replace_text(self.gate_output,f"Output bits: {response['output_bits']}\n\nKeyword matches: {response['virtue_count']}\nCorporate matches: {response['corporate_count']}\nMean weight at request: {response['mean_integrity_index']:.4f}\n\n{response['logistics_log']}\n\n{len(g['events'])} recent requests recorded.")
            else:
                self.gate_title.set("Gate result · awaiting a request")
                self.replace_text(self.gate_output,"Start the weight engine to approach its targets, then process text and bits. No TCP listener is needed for this panel.")
        if n["last_error"] or o["last_error"]:self.status.set(n["last_error"] or o["last_error"])

    @staticmethod
    def canvas_size(canvas):
        canvas.delete("all")
        return max(canvas.winfo_width(),180),max(canvas.winfo_height(),120)

    @staticmethod
    def label(canvas,x,y,text,fill=MUTED,size=9,anchor="center"):
        return canvas.create_text(x,y,text=str(text),fill=fill,font=("Consolas",size),anchor=anchor)

    def draw_network(self,n):
        c=self.network_canvas;w,h=self.canvas_size(c)
        sizes=n["architecture"]
        xs=[38+i*(w-76)/3 for i in range(4)]
        points=[[(xs[layer],h/2+(j-(count-1)/2)*min(21,(h-72)/11)) for j in range(count)] for layer,count in enumerate(sizes)]
        for layer,weights in enumerate(n["weights"]):
            for i,row in enumerate(weights):
                for j,value in enumerate(row):
                    strength=min(abs(value)/3,1)
                    color=self.mix("#1a293a",BLUE if value>=0 else CORAL,.15+.7*strength)
                    c.create_line(*points[layer][i],*points[layer+1][j],fill=color,width=.4+2*strength)
        for layer,positions in enumerate(points):
            for j,(x,y) in enumerate(positions):
                value=n["activations"][layer][j];radius=9 if layer in (0,3) else 5
                c.create_oval(x-radius,y-radius,x+radius,y+radius,fill=self.mix(PANEL,MINT if value>=0 else CORAL,.15+.85*min(abs(value),1)),outline=MINT if value>=0 else CORAL)
            self.label(c,xs[layer],14,["INPUT","HIDDEN 1","HIDDEN 2","OUTPUT"][layer],size=8)
            self.label(c,xs[layer],h-12,str(sizes[layer])+" nodes",size=8)
        self.label(c,xs[3],h/2+28,f"{n['probe']['probability']*100:.1f}%",MINT,11)

    @staticmethod
    def mix(a,b,t):
        return "#"+"".join(f"{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02x}" for i in (1,3,5))

    def draw_map(self,n):
        c=self.map_canvas;w,h=self.canvas_size(c)
        size=max(70,min(w-58,h-42));left=(w-size)/2;top=9
        self.map_bounds=(left,top,size)
        count=n["grid_size"];cell=size/count
        for iy in range(count):
            for ix in range(count):
                p=n["grid"][iy*count+ix]
                c.create_rectangle(left+ix*cell,top+size-(iy+1)*cell,left+(ix+1)*cell+.5,top+size-iy*cell+.5,
                                   fill=self.mix("#713946","#23695b",p),outline="")
        for i in range(5):
            pos=i*size/4
            c.create_line(left+pos,top,left+pos,top+size,fill="#4c6468",stipple="gray50")
            c.create_line(left,top+pos,left+size,top+pos,fill="#4c6468",stipple="gray50")
        spacing=size/(count-1)
        for iy in range(count-1):
            for ix in range(count-1):
                corners=[(ix,iy),(ix+1,iy),(ix+1,iy+1),(ix,iy+1)];hits=[]
                for edge in range(4):
                    a,b=corners[edge],corners[(edge+1)%4]
                    pa,pb=n["grid"][a[1]*count+a[0]],n["grid"][b[1]*count+b[0]]
                    if (pa<.5)!=(pb<.5):
                        t=(.5-pa)/(pb-pa)
                        hits.append((left+(a[0]+t*(b[0]-a[0]))*spacing,top+size-(a[1]+t*(b[1]-a[1]))*spacing))
                for k in range(0,len(hits)-1,2):c.create_line(*hits[k],*hits[k+1],fill="#c0d4d0",width=1)
        radius=2.5 if len(n["points"])<500 else 1.5
        for x,y,label in n["points"]:
            px=left+(x+1)*size/2;py=top+(1-y)*size/2
            c.create_oval(px-radius,py-radius,px+radius,py+radius,fill=MINT if label else CORAL,outline="#0c1922")
        px=left+(self.probe[0]+1)*size/2;py=top+(1-self.probe[1])*size/2
        c.create_oval(px-6,py-6,px+6,py+6,outline=INK,width=1.5)
        c.create_rectangle(left,top,left+size,top+size,outline="#66818e")
        for i in range(3):
            self.label(c,left+i*size/2,top+size+14,f"{i-1:.1f}",size=8)
            self.label(c,left-8,top+i*size/2,f"{1-i:.1f}",size=8,anchor="e")

    def draw_trace(self,c,history,series):
        w,h=self.canvas_size(c);left,top=42,14;width,height=w-55,h-38
        maximum=max(.02,max((row[key] for row in history for key,_ in series),default=1))*1.1
        start=history[0]["step"] if history else 0;end=max(start+1,history[-1]["step"] if history else 1)
        for i in range(4):
            y=top+i*height/3;c.create_line(left,y,left+width,y,fill=EDGE)
            self.label(c,left-6,y,f"{maximum*(1-i/3):.2f}",size=8,anchor="e")
        for key,color in series:
            coords=[]
            for row in history:coords.extend((left+(row["step"]-start)/(end-start)*width,top+(1-row[key]/maximum)*height))
            if len(coords)>=4:c.create_line(*coords,fill=color,width=2)
        self.label(c,left,h-9,start,size=8);self.label(c,left+width,h-9,history[-1]["step"] if history else 0,size=8)
        self.label(c,w/2,h-9,"STEPS",size=8)
        if len(history)<2:self.label(c,w/2,h/2,"Start learning to trace progress",size=9)

    def draw_weights(self,ledger):
        c=self.weight_canvas;w,h=self.canvas_size(c)
        left,right=32,w-50;row_height=(h-14)/5
        for i,(current,target) in enumerate(zip(ledger["current_weights"],ledger["target_profile"])):
            y=7+i*row_height
            self.label(c,left,y,PROFILE_NAMES[i],size=9,anchor="w")
            c.create_rectangle(left,y+12,right,y+23,fill="#223346",outline="")
            c.create_rectangle(left,y+12,left+(right-left)*current,y+23,fill=MINT,outline="")
            tx=left+(right-left)*target;c.create_line(tx,y+9,tx,y+26,fill=GOLD,width=2)
            self.label(c,right+6,y+18,f"{current:.3f}",INK,9,anchor="w")

    def on_close(self):
        if self.closing:return
        if self.autosave.get():
            try:self.session.save()
            except (ValueError,OSError) as error:
                if not messagebox.askyesno("Save failed",f"Could not save the session: {error}\n\nClose without saving?",parent=self):return
        self.closing=True
        if self.timer:self.after_cancel(self.timer)
        self.session.close()
        self.destroy()


def self_test():
    session=DesktopSession()
    try:
        before=session.neural.metrics["test_loss"]
        session.neural.train_steps(200);session.neural.record_metrics()
        assert session.neural.metrics["test_loss"]<before
        blocked=session.gateway.process_payload({"text":"cooperation efficiency", "bits":[0,1]})
        assert blocked["output_bits"]==[1,0] and not blocked["virtue_pass"]
        for _ in range(100):session.optimizer.step_once()
        passed=session.gateway.process_payload({"text":"cooperation efficiency", "bits":[0,1]})
        assert passed["output_bits"]==[0,1] and passed["virtue_pass"]
        assert passed["physical_ledger_state"]["lowest_floor_current"]==250
        assert passed["physical_ledger_state"]["upper_floor_wealth"]==1000
        restored=DesktopSession();restored.load_data(session.checkpoint())
        assert restored.ledger.to_dict()==session.ledger.to_dict()
        assert restored.neural.model.steps==session.neural.model.steps
        restored.close()
        print("PASS: neural learning, profile optimization, shared-ledger gate, bit transforms, simulated uplift, and combined session restore.")
        print(f"Held-out accuracy after 200 classifier steps: {session.neural.metrics['test_accuracy']:.1%}")
    finally:session.close()


def main():
    parser=argparse.ArgumentParser(description="Godmind Mesh native desktop app (.py)")
    parser.add_argument("--self-test",action="store_true",help="Test the integrated engines without opening a window")
    parser.add_argument("--fresh",action="store_true",help="Start without restoring the last desktop session")
    args=parser.parse_args()
    if args.self_test:
        self_test();return
    if sys.platform=="win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError,OSError):pass
    app=GodmindDesktop(restore_last=not args.fresh)
    app.mainloop()


if __name__=="__main__":
    main()
