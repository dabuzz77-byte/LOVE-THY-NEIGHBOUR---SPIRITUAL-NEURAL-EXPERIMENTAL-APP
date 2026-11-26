"""Separate dual-rail panel adapted from the user's supplied Tkinter program.

The original input, presets, two rails and 2.5-second display cycle are retained.
The classification and throughput are generated display values, not model
assessments or network measurements. This panel does not modify app settings.
"""
import asyncio
import json
import os
from pathlib import Path
import queue
import random
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from parallel_dual_rail import ParallelDualRailEngine
from blueprint_inspector import HypervisorBoundaryBridge
from persistent_drill import PersistentDrillWorker, parity_sweep
from kraken_audio import KrakenAudioDeploymentCore, TRIGGERS as KRAKEN_TRIGGERS

from dual_rail_rules import SEED_A, SEED_B, MODES, PRESETS, DEFAULT_PAYLOAD, display_step
MODULE_DIRECTORY = Path(__file__).resolve().parent.parent


class PostscarcityObservatoryV4:
    def __init__(self, root):
        self.root = root
        self.root.title('Postscarcity Observatory v4 | Dual-Rail Core - separate panel')
        self.root.geometry('1080x800')
        self.root.minsize(900, 720)
        self.root.configure(bg='#0a0a0a')
        self.pinnacle_bit = 1
        self.track_A_registers = list(SEED_A)
        self.track_B_registers = list(SEED_B)
        self.mode = 'original'
        self.rail_states = {name: (list(profile['a']), list(profile['b'])) for name, profile in MODES.items()}
        self.is_monitoring = False
        self.after_id = None
        self.drill_worker = PersistentDrillWorker()
        self.drill_enabled = tk.BooleanVar(master=root, value=False)
        self.drill_after_id = None
        self.drill_sweeps = 0
        self.rng = random.Random()
        self.configure_terminal_styles()
        self.build_observatory_canvas()
        self.root.protocol('WM_DELETE_WINDOW', self.close)

    def configure_terminal_styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', background='#0a0a0a', foreground='#00ff00')
        style.configure('TFrame', background='#0a0a0a')
        style.configure('TLabel', font=('Courier', 10))
        style.configure('Title.TLabel', font=('Courier', 14, 'bold'))
        style.configure('TButton', background='#1a1a1a', font=('Courier', 10, 'bold'), borderwidth=1)
        style.map('TButton', background=[('active', '#2a2a2a')], foreground=[('active', '#00ff00')])
        style.configure('TLabelframe', background='#0a0a0a', foreground='#00ff00')
        style.configure('TLabelframe.Label', font=('Courier', 10, 'bold'))

    def build_observatory_canvas(self):
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill=tk.X)
        ttk.Label(header, text='POSTSCARCITY OBSERVATORY v4 // DUAL-RAIL CORE', style='Title.TLabel').pack(anchor=tk.W)
        ttk.Label(header, text='Separate local visual panel | Windows user mode | Generated display values',
                  foreground='#a9b9a9').pack(anchor=tk.W, pady=4)
        ttk.Button(header, text='OPEN / LAUNCH OBSERVATORY APP', command=self.open_observatory).pack(anchor=tk.W, pady=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        display_page = ttk.Frame(self.notebook)
        self.notebook.add(display_page, text='Rail display')
        self.parallel_panel = ParallelEnginePanel(self.notebook, lambda: self.txt_payload.get('1.0', tk.END).strip())
        self.notebook.add(self.parallel_panel, text='Parallel engine')
        self.blueprint_panel = BlueprintInspectorPanel(self.notebook)
        self.notebook.add(self.blueprint_panel, text='Blueprint inspector')
        self.kraken_panel = KrakenAudioPanel(self.notebook)
        self.notebook.add(self.kraken_panel, text='Kraken trigger')
        workspace = ttk.Frame(display_page, padding=10)
        workspace.pack(fill=tk.BOTH, expand=True)
        workspace.columnconfigure(0, weight=1, uniform='panels')
        workspace.columnconfigure(1, weight=1, uniform='panels')
        workspace.rowconfigure(0, weight=1)
        controls = ttk.Labelframe(workspace, text=' [ Input & calibration ] ', padding=10)
        controls.grid(row=0, column=0, sticky='nsew', padx=5)
        ttk.Label(controls, text='Rail processing mode:').pack(anchor=tk.W)
        self.combo_mode = ttk.Combobox(controls, state='readonly',
                values=[profile['label'] for profile in MODES.values()], font=('Courier', 10))
        self.combo_mode.set(MODES[self.mode]['label'])
        self.combo_mode.pack(fill=tk.X, pady=6)
        self.combo_mode.bind('<<ComboboxSelected>>', self.select_processing_mode)
        ttk.Label(controls, text='Local logic payload (reference text):').pack(anchor=tk.W)
        self.txt_payload = scrolledtext.ScrolledText(controls, height=8, width=34, bg='#111111',
                fg='white', insertbackground='white', font=('Courier', 10), relief=tk.SOLID, borderwidth=1)
        self.txt_payload.pack(fill=tk.BOTH, expand=True, pady=6)
        self.txt_payload.insert(tk.END, DEFAULT_PAYLOAD)
        ttk.Label(controls, text='Systemic calibration baseline:').pack(anchor=tk.W)
        self.combo_baseline = ttk.Combobox(controls, values=PRESETS, font=('Courier', 10))
        self.combo_baseline.current(0)
        self.combo_baseline.pack(fill=tk.X, pady=6)
        ttk.Label(controls, text='Preset names are intention labels; the supplied\nlength + random-number display rule is retained.',
                  foreground='#a9b9a9').pack(anchor=tk.W, pady=4)
        self.btn_run = ttk.Button(controls, text='START DUAL-RAIL DISPLAY', command=self.toggle_observatory_core)
        self.btn_run.pack(fill=tk.X, pady=4)
        ttk.Button(controls, text='RESET RAIL DISPLAY', command=self.re_zero_registers).pack(fill=tk.X, pady=4)
        self.drill_toggle = ttk.Checkbutton(controls, text='Persistent local drill: A=1 / B=0 every 1.8s',
                variable=self.drill_enabled, command=self.configure_persistent_drill)
        self.drill_toggle.pack(anchor=tk.W, pady=4)

        telemetry = ttk.Labelframe(workspace, text=' [ Local matrix indicators ] ', padding=10)
        telemetry.grid(row=0, column=1, sticky='nsew', padx=5)
        self.pinnacle_indicator = ttk.Label(telemetry, text='STATUS: STANDBY', foreground='#ffff00')
        self.pinnacle_indicator.pack(anchor=tk.W, pady=2)
        self.lbl_pinnacle = ttk.Label(telemetry, text='PINNACLE DISPLAY BIT: 1 (CONSTANT)')
        self.lbl_pinnacle.pack(anchor=tk.W, pady=2)
        self.lbl_mode = ttk.Label(telemetry, text='MODE: ' + MODES[self.mode]['label'], foreground='#a9b9a9')
        self.lbl_mode.pack(anchor=tk.W, pady=2)
        self.lbl_drill = ttk.Label(telemetry, text='LOCAL DRILL: OFF', foreground='#a9b9a9')
        self.lbl_drill.pack(anchor=tk.W, pady=2)
        ttk.Label(telemetry, text='Track A: Pure Virtue Progression Ladder').pack(anchor=tk.W, pady=4)
        self.canvas_rail_A = tk.Canvas(telemetry, height=45, width=288, bg='#111111', highlightthickness=0)
        self.canvas_rail_A.pack(fill=tk.X, pady=2)
        ttk.Label(telemetry, text='Track B: Parallel Redemptive Refinery').pack(anchor=tk.W, pady=4)
        self.canvas_rail_B = tk.Canvas(telemetry, height=45, width=288, bg='#111111', highlightthickness=0)
        self.canvas_rail_B.pack(fill=tk.X, pady=2)
        for canvas in (self.canvas_rail_A, self.canvas_rail_B):
            canvas.bind('<Configure>', lambda event: self.render_register_rails())
        self.render_register_rails()
        ttk.Label(telemetry, text='Local display event output:').pack(anchor=tk.W, pady=4)
        self.txt_terminal_logs = scrolledtext.ScrolledText(telemetry, height=10, width=35, bg='#0d0d0d',
                fg='#00ff00', font=('Courier', 9), state=tk.DISABLED, borderwidth=0, wrap=tk.WORD)
        self.txt_terminal_logs.pack(fill=tk.BOTH, expand=True, pady=2)

        endpoint = ttk.Labelframe(display_page, text=' [ FURTHEST TRIBES - display status ] ', padding=10)
        endpoint.pack(fill=tk.X, padx=15, pady=10)
        self.lbl_mesh_status = ttk.Label(endpoint, text='DISPLAY: STANDBY | Generated throughput: 0 bps')
        self.lbl_mesh_status.pack(anchor=tk.W)
        ttk.Label(endpoint, text='Actual networking and model assessments remain in the Observatory app.',
                  foreground='#a9b9a9').pack(anchor=tk.W, pady=3)

    def write_terminal_trace(self, text):
        at_bottom = self.txt_terminal_logs.yview()[1] >= .98
        self.txt_terminal_logs.config(state=tk.NORMAL)
        self.txt_terminal_logs.insert(tk.END, f'[{time.strftime("%H:%M:%S")}] {text}\n')
        lines = int(self.txt_terminal_logs.index('end-1c').split('.')[0])
        if lines > 500:
            self.txt_terminal_logs.delete('1.0', f'{lines - 500 + 1}.0')
        if at_bottom:
            self.txt_terminal_logs.see(tk.END)
        self.txt_terminal_logs.config(state=tk.DISABLED)

    def render_register_rails(self):
        for canvas, values, color, outline in (
                (self.canvas_rail_A, self.track_A_registers, '#005500', '#00ff00'),
                (self.canvas_rail_B, self.track_B_registers, '#000055', '#0088ff')):
            canvas.delete('all')
            cell = max(288, canvas.winfo_width()) / len(values)
            for i, bit in enumerate(values):
                left, right = i * cell + 5, (i + 1) * cell - 5
                canvas.create_rectangle(left, 8, right, 35, fill=color if bit else '#222222', outline=outline)
                canvas.create_text((left + right) / 2, 21, text=str(bit), fill='white', font=('Courier', 10, 'bold'))

    def select_processing_mode(self, event=None):
        selected = next(name for name, profile in MODES.items() if profile['label'] == self.combo_mode.get())
        if selected == self.mode:
            return
        self.rail_states[self.mode] = (list(self.track_A_registers), list(self.track_B_registers))
        self.mode = selected
        saved_a, saved_b = self.rail_states[selected]
        self.track_A_registers, self.track_B_registers = list(saved_a), list(saved_b)
        self.lbl_mode.config(text='MODE: ' + MODES[selected]['label'])
        self.render_register_rails()
        self.lbl_mesh_status.config(text='DISPLAY: MODE SWITCHED | Waiting for the next display tick')
        self.write_terminal_trace('Mode: ' + MODES[selected]['label'] + '. Its saved rails are restored; payload and timer are retained.')

    def re_zero_registers(self):
        self.drill_enabled.set(False)
        self.stop_persistent_drillscript_worker()
        profile = MODES[self.mode]
        self.track_A_registers = list(profile['a'])
        self.track_B_registers = list(profile['b'])
        self.render_register_rails()
        self.write_terminal_trace('Display reset to the seeds for ' + profile['label'] + '. App ledgers are unchanged.')
        self.lbl_mesh_status.config(text='DISPLAY: SEEDS RESTORED | Generated throughput: 0 bps')

    def cancel_tick(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def toggle_observatory_core(self):
        self.cancel_tick()
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.btn_run.config(text='PAUSE DUAL-RAIL DISPLAY')
            self.pinnacle_indicator.config(text='STATUS: DISPLAY RUNNING', foreground='#00ff00')
            self.write_terminal_trace('Display started. Baseline label: ' + self.combo_baseline.get())
            self.execute_observatory_clock_tick()
            if self.drill_enabled.get():
                self.start_persistent_drillscript_worker()
        else:
            self.stop_persistent_drillscript_worker()
            self.btn_run.config(text='START DUAL-RAIL DISPLAY')
            self.pinnacle_indicator.config(text='STATUS: PAUSED', foreground='#ffff00')
            self.lbl_mesh_status.config(text='DISPLAY: PAUSED | Generated throughput: 0 bps')
            self.write_terminal_trace('Local display paused; the Observatory app continues independently.')

    def execute_observatory_clock_tick(self):
        self.cancel_tick()
        if not self.is_monitoring:
            return
        result = display_step(self.txt_payload.get('1.0', tk.END).strip(),
                self.track_A_registers, self.track_B_registers, self.rng, self.mode)
        self.track_A_registers, self.track_B_registers = result['a'], result['b']
        self.write_terminal_trace(f'Generated classification: {result["state"]} / {result["nature"]}; weight={result["weight"]}.')
        self.write_terminal_trace('Display basis: ' + result['reason'] + ' | ' + MODES[self.mode]['label'])
        self.write_terminal_trace(result['action'])
        self.render_register_rails()
        self.lbl_mesh_status.config(text=f'DISPLAY: RUNNING | Generated throughput: {result["display_bps"]:,} bps | A: ' +
                                    ''.join(map(str, self.track_A_registers)))
        self.after_id = self.root.after(2500, self.execute_observatory_clock_tick)

    def configure_persistent_drill(self):
        if self.drill_enabled.get():
            self.start_persistent_drillscript_worker()
        else:
            self.stop_persistent_drillscript_worker()

    def start_persistent_drillscript_worker(self):
        """Start the supplied A=1 / B=0 loop with main-thread display updates."""
        self.drill_enabled.set(True)
        if not self.is_monitoring:
            self.lbl_drill.config(text='LOCAL DRILL: READY - START DISPLAY')
            return
        if self.drill_worker.start():
            self.write_terminal_trace('Persistent local drillscript started: A=1 / B=0 every 1.8 seconds.')
        if self.drill_after_id is None:
            self.poll_persistent_drill()

    def poll_persistent_drill(self):
        self.drill_after_id = None
        if not self.is_monitoring or not self.drill_enabled.get():
            return
        if self.drill_worker.consume():
            self.track_A_registers, self.track_B_registers = parity_sweep(
                self.track_A_registers, self.track_B_registers)
            self.drill_sweeps += 1
            self.render_register_rails()
            self.lbl_drill.config(text=f'LOCAL DRILL: RUNNING - {self.drill_sweeps} sweeps')
            self.write_terminal_trace('Drillscript sweep: local Track A set to ones; local Track B set to zeros.')
        self.drill_after_id = self.root.after(50, self.poll_persistent_drill)

    def stop_persistent_drillscript_worker(self):
        was_alive = self.drill_worker.alive
        self.drill_worker.stop()
        if self.drill_after_id is not None:
            self.root.after_cancel(self.drill_after_id)
            self.drill_after_id = None
        self.lbl_drill.config(text='LOCAL DRILL: PAUSED' if self.drill_enabled.get() else 'LOCAL DRILL: OFF')
        if was_alive:
            self.write_terminal_trace('Persistent local drillscript stopped; pending sweep discarded.')

    def open_observatory(self):
        launcher = MODULE_DIRECTORY / 'Launch Observatory.cmd'
        if not launcher.is_file():
            messagebox.showerror('Observatory launcher missing', f'Keep this panel inside the Observatory folder.\nExpected: {launcher}', parent=self.root)
            return
        try:
            os.startfile(str(launcher))
            self.write_terminal_trace('Requested the existing Observatory launcher. The app reports its own startup status.')
        except OSError as exc:
            messagebox.showerror('Cannot open Observatory', str(exc), parent=self.root)

    def close(self):
        self.is_monitoring = False
        self.cancel_tick()
        self.stop_persistent_drillscript_worker()
        self.parallel_panel.close()
        self.root.destroy()


class KrakenAudioPanel(ttk.Frame):
    """Manual text-trigger panel; does not control either running rail engine."""
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.engine = KrakenAudioDeploymentCore()
        self.last_result = None
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text='Kraken audio blueprint - quote trigger', style='Title.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        inputs = ttk.Labelframe(self, text=' [ Timestamp & quote text ] ', padding=10)
        inputs.grid(row=1, column=0, sticky='nsew', padx=(0, 6))
        ttk.Label(inputs, text='Video timestamp / reference (optional):').pack(anchor=tk.W)
        self.timestamp = ttk.Entry(inputs, font=('Courier', 10))
        self.timestamp.pack(fill=tk.X, pady=5)
        ttk.Label(inputs, text='Quote / trigger text:').pack(anchor=tk.W)
        self.payload = scrolledtext.ScrolledText(inputs, height=8, width=35, bg='#111111', fg='white',
                insertbackground='white', font=('Courier', 10))
        self.payload.pack(fill=tk.BOTH, expand=True, pady=5)
        self.trigger_buttons = []
        for term in KRAKEN_TRIGGERS:
            button = ttk.Button(inputs, text='INSERT ' + term,
                                command=lambda trigger=term: self.insert_trigger(trigger))
            button.pack(fill=tk.X, pady=3)
            self.trigger_buttons.append(button)
        self.process_button = ttk.Button(inputs, text='PROCESS QUOTE TRIGGER', command=self.process)
        self.process_button.pack(fill=tk.X, pady=4)
        self.reset_button = ttk.Button(inputs, text='RESET KRAKEN REGISTERS', command=self.reset)
        self.reset_button.pack(fill=tk.X, pady=4)
        output = ttk.Labelframe(self, text=' [ Local register result & receipts ] ', padding=10)
        output.grid(row=1, column=1, sticky='nsew', padx=(6, 0))
        self.status = ttk.Label(output, text='STATUS: READY', foreground='#ffff00')
        self.status.pack(anchor=tk.W, pady=4)
        self.bits = ttk.Label(output, text='Local registers: 11001011')
        self.bits.pack(anchor=tk.W, pady=4)
        self.canvas = tk.Canvas(output, height=55, width=320, bg='#111111', highlightthickness=0)
        self.canvas.pack(fill=tk.X, pady=4)
        self.canvas.bind('<Configure>', lambda event: self.render())
        self.trace = scrolledtext.ScrolledText(output, height=14, width=40, bg='#0d0d0d', fg='#00ff00',
                font=('Courier', 9), state=tk.DISABLED, wrap=tk.WORD)
        self.trace.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(self, text='The supplied rule checks quote text. Timestamp is reference metadata; no audio is retrieved, played or measured by this panel.',
                  foreground='#a9b9a9', wraplength=1000).grid(row=2, column=0, columnspan=2, sticky='w', pady=10)
        self.render()

    def insert_trigger(self, term):
        if self.payload.get('1.0', 'end-1c'):
            self.payload.insert(tk.END, '\n')
        self.payload.insert(tk.END, term)

    def render(self):
        self.canvas.delete('all')
        values = self.engine.core_registers
        self.bits.config(text='Local registers: ' + ''.join(map(str, values)))
        width = max(288, self.canvas.winfo_width()) / len(values)
        for index, bit in enumerate(values):
            left, right = index * width + 5, (index + 1) * width - 5
            self.canvas.create_rectangle(left, 8, right, 44, fill='#005500' if bit else '#222222', outline='#00ff00')
            self.canvas.create_text((left + right)/2, 26, text=str(bit), fill='white', font=('Courier', 10, 'bold'))

    def append_receipt(self, receipt):
        at_bottom = self.trace.yview()[1] >= .98
        self.trace.config(state=tk.NORMAL)
        self.trace.insert(tk.END, json.dumps(receipt, indent=2) + '\n\n')
        lines = int(self.trace.index('end-1c').split('.')[0])
        if lines > 1000:
            self.trace.delete('1.0', f'{lines - 1000 + 1}.0')
        if at_bottom:
            self.trace.see(tk.END)
        self.trace.config(state=tk.DISABLED)

    def process(self):
        self.last_result = self.engine.process_kraken_audio_trigger(
            self.timestamp.get(), self.payload.get('1.0', 'end-1c'))
        self.render()
        matched = self.last_result['matched_triggers']
        self.status.config(text='STATUS: TRIGGER MATCHED - BITS SET TO ONE' if matched else 'STATUS: NO MATCH - BITS RETAINED',
                           foreground='#00ff00' if matched else '#ffff00')
        self.append_receipt(self.last_result)

    def reset(self):
        self.engine = KrakenAudioDeploymentCore()
        self.last_result = None
        self.render()
        self.status.config(text='STATUS: REGISTERS RESET', foreground='#ffff00')
        self.append_receipt({'action': 'reset local Kraken registers', 'registers': self.engine.core_registers.copy()})


class BlueprintInspectorPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=12)
        self.engine = HypervisorBoundaryBridge()
        self.last_result = None
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text='Boundary blueprint - local register inspector', style='Title.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        inputs = ttk.Labelframe(self, text=' [ Framework context ] ', padding=10)
        inputs.grid(row=1, column=0, sticky='nsew', padx=(0, 6))
        self.context = scrolledtext.ScrolledText(inputs, height=10, width=35, bg='#111111', fg='white',
                insertbackground='white', font=('Courier', 10))
        self.context.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(inputs, text='INSERT SUPPLIED TRIGGER', command=self.insert_trigger).pack(fill=tk.X, pady=4)
        ttk.Button(inputs, text='INSPECT BLUEPRINT / UPDATE LOCAL BITS', command=self.inspect).pack(fill=tk.X, pady=4)
        ttk.Button(inputs, text='RESET BLUEPRINT REGISTERS', command=self.reset).pack(fill=tk.X, pady=4)
        output = ttk.Labelframe(self, text=' [ Declarations & execution facts ] ', padding=10)
        output.grid(row=1, column=1, sticky='nsew', padx=(6, 0))
        self.bits = ttk.Label(output, text='Local registers: 10010110')
        self.bits.pack(anchor=tk.W, pady=5)
        self.trace = scrolledtext.ScrolledText(output, height=15, width=40, bg='#0d0d0d', fg='#00ff00',
                font=('Courier', 9), state=tk.DISABLED, wrap=tk.WORD)
        self.trace.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(self, text='The supplied "unlocked" and "bypassed" labels are blueprint declarations. This operation changes local register data; it does not execute hardware commands.',
                  foreground='#a9b9a9', wraplength=1000).grid(row=2, column=0, columnspan=2, sticky='w', pady=10)

    def insert_trigger(self):
        self.context.insert(tk.END, '\nlacks_direct_operational_capacity')

    def inspect(self):
        self.last_result = self.engine.execute_boundary_refraction(self.context.get('1.0', tk.END))
        self.bits.config(text='Local registers: ' + ''.join(map(str, self.last_result['local_register_result'])))
        self.trace.config(state=tk.NORMAL)
        self.trace.delete('1.0', tk.END)
        self.trace.insert(tk.END, json.dumps(self.last_result, indent=2))
        self.trace.config(state=tk.DISABLED)

    def reset(self):
        self.engine = HypervisorBoundaryBridge()
        self.last_result = None
        self.bits.config(text='Local registers: 10010110')
        self.trace.config(state=tk.NORMAL)
        self.trace.delete('1.0', tk.END)
        self.trace.config(state=tk.DISABLED)


class ParallelEnginePanel(ttk.Frame):
    """One background sweep at a time; all widget updates stay on Tk's thread."""
    def __init__(self, parent, copy_payload):
        super().__init__(parent, padding=12)
        self.copy_payload = copy_payload
        self.engine = ParallelDualRailEngine()
        self.results = queue.Queue()
        self.busy = False
        self.looping = False
        self.closed = False
        self.reset_pending = False
        self.loop_id = None
        self.poll_id = None
        self.last_result = None
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text='Concurrent Track A / Track B - local calculation', style='Title.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        inputs = ttk.Labelframe(self, text=' [ Parallel engine input ] ', padding=10)
        inputs.grid(row=1, column=0, sticky='nsew', padx=(0, 6))
        ttk.Label(inputs, text='Payload:').pack(anchor=tk.W)
        self.payload = scrolledtext.ScrolledText(inputs, height=8, width=35, bg='#111111', fg='white',
                insertbackground='white', font=('Courier', 10))
        self.payload.pack(fill=tk.BOTH, expand=True, pady=6)
        self.payload.insert(tk.END, DEFAULT_PAYLOAD)
        ttk.Button(inputs, text='COPY PAYLOAD FROM RAIL DISPLAY', command=self.copy_from_display).pack(fill=tk.X, pady=3)
        ttk.Button(inputs, text='RUN BOTH LANES ONCE', command=self.run_once).pack(fill=tk.X, pady=3)
        self.loop_button = ttk.Button(inputs, text='START PARALLEL LOOP', command=self.toggle_loop)
        self.loop_button.pack(fill=tk.X, pady=3)
        ttk.Button(inputs, text='RESET PARALLEL ENGINE', command=self.reset_engine).pack(fill=tk.X, pady=3)
        ttk.Label(inputs, text='Both lanes run concurrently. Loop waits 2.5 seconds\nafter each result. Inputs are text, not commands.',
                  foreground='#a9b9a9').pack(anchor=tk.W, pady=6)
        output = ttk.Labelframe(self, text=' [ Lane results & selected output ] ', padding=10)
        output.grid(row=1, column=1, sticky='nsew', padx=(6, 0))
        self.status = ttk.Label(output, text='STATUS: READY', foreground='#ffff00')
        self.status.pack(anchor=tk.W, pady=3)
        self.bits = ttk.Label(output, text='Selected output: awaiting a run')
        self.bits.pack(anchor=tk.W, pady=3)
        self.registers = ttk.Label(output, text='Stored A: 11111111 | Stored B: 00000000')
        self.registers.pack(anchor=tk.W, pady=3)
        self.trace = scrolledtext.ScrolledText(output, height=14, width=40, bg='#0d0d0d', fg='#00ff00',
                font=('Courier', 9), state=tk.DISABLED, wrap=tk.WORD)
        self.trace.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(self, text='Results describe the supplied keyword rules. Track B produces a candidate copy; its stored baseline stays unchanged.',
                  foreground='#a9b9a9', wraplength=1000).grid(row=2, column=0, columnspan=2, sticky='w', pady=10)
        self.poll_id = self.after(40, self.poll_results)

    def copy_from_display(self):
        self.payload.delete('1.0', tk.END)
        self.payload.insert(tk.END, self.copy_payload())

    def cancel_loop_timer(self):
        if self.loop_id is not None:
            self.after_cancel(self.loop_id)
            self.loop_id = None

    def run_once(self):
        if self.closed or self.busy:
            return
        self.cancel_loop_timer()
        self.busy = True
        payload = self.payload.get('1.0', tk.END).strip()
        self.status.config(text='STATUS: BOTH LANES RUNNING', foreground='#ffff00')
        engine = self.engine
        def calculate():
            try:
                self.results.put(('result', asyncio.run(engine.execute_synchronized_runall(payload))))
            except Exception as exc:
                self.results.put(('error', str(exc)))
        threading.Thread(target=calculate, name='dual-rail-local-calculation', daemon=True).start()

    def toggle_loop(self):
        self.looping = not self.looping
        self.loop_button.config(text='PAUSE PARALLEL LOOP' if self.looping else 'START PARALLEL LOOP')
        if self.looping:
            self.run_once()
        else:
            self.cancel_loop_timer()
            self.status.config(text='STATUS: FINISHING CURRENT RUN' if self.busy else 'STATUS: LOOP PAUSED')

    def reset_engine(self):
        if self.busy:
            self.reset_pending = True
            self.status.config(text='STATUS: RESET AFTER CURRENT RUN')
            return
        self.reset_pending = False
        self.engine = ParallelDualRailEngine()
        self.last_result = None
        self.bits.config(text='Selected output: awaiting a run')
        self.registers.config(text='Stored A: 11111111 | Stored B: 00000000')
        self.status.config(text='STATUS: ENGINE RESET')

    def poll_results(self):
        self.poll_id = None
        if self.closed:
            return
        try:
            kind, result = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            at_bottom = self.trace.yview()[1] >= .98
            self.trace.config(state=tk.NORMAL)
            self.trace.insert(tk.END, json.dumps(result, indent=2) + '\n\n')
            lines = int(self.trace.index('end-1c').split('.')[0])
            if lines > 1000:
                self.trace.delete('1.0', f'{lines - 1000 + 1}.0')
            if at_bottom:
                self.trace.see(tk.END)
            self.trace.config(state=tk.DISABLED)
            if kind == 'result':
                self.last_result = result
                self.status.config(text=f'STATUS: COMPLETE IN {result["elapsed_ms"]} ms', foreground='#00ff00')
                self.bits.config(text='Selected output: ' + ''.join(map(str, result['grounded_output_stream'])))
                self.registers.config(text='Stored A: ' + ''.join(map(str, result['stored_rail_A'])) +
                                      ' | Stored B: ' + ''.join(map(str, result['stored_rail_B'])))
            else:
                self.status.config(text='STATUS: ERROR - SEE TRACE', foreground='#ffff00')
            if self.reset_pending:
                self.reset_engine()
            if self.looping:
                self.loop_id = self.after(2500, self.run_once)
        self.poll_id = self.after(40, self.poll_results)

    def close(self):
        self.closed = True
        self.looping = False
        self.cancel_loop_timer()
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
            self.poll_id = None


def main():
    root = tk.Tk()
    try:
        PostscarcityObservatoryV4(root)
        root.mainloop()
    except Exception as exc:
        messagebox.showerror('Dual-Rail Core could not start', str(exc), parent=root)
        root.destroy()
        raise


if __name__ == '__main__':
    main()
