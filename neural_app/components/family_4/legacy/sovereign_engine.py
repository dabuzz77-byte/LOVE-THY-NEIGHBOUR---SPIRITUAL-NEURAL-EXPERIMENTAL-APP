"""Unified local interface for the Hydrogen Atom matrix engines.

Text is treated as data and passed through the installed processing modules;
this interface does not execute shell commands or alter other processes.
"""
from __future__ import annotations
import cmath
import json
import math
import os
import random
from neural_app import section_threads as threading
import time
from neural_app import component_ui as tk
from neural_app.component_ui import ttk
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from ..legacy.module_biosphere_core import BiosphereDataSubstrate
from ..legacy.module_dyson_forge_core import DysonForgeDataSubstrate
from ..legacy.module_matrix_substrate import SystemDataSubstrate
from ..legacy.module_resonance import ResonanceBaselineConditioner
from ..legacy.module_runtime import format_rate, get_carrier, get_system_sampler
from ..legacy.module_stellar_core import StellarCoreSubstrate
from ..legacy.module_substrate import LogicSubstrateKernel
from ..legacy.module_ternary_matrix import BalancedTernaryProcessor
BG = '#07101b'
PANEL = '#0b1725'
PANEL_ALT = '#101f30'
LINE = '#18344b'
CYAN = '#42e8ff'
BLUE = '#4288ff'
WHITE = '#e9f5ff'
MUTED = '#8ba7bb'
GREEN = '#55e6a5'
GOLD = '#ffc46b'

class SovereignEngine:
    """Route user text through the local substrate, carrier, and matrix layers."""

    def __init__(self):
        self.kernel = LogicSubstrateKernel()
        self.conditioner = ResonanceBaselineConditioner()
        self.ternary = BalancedTernaryProcessor()
        self.substrate = SystemDataSubstrate()
        self.stellar = StellarCoreSubstrate()
        self.dyson = DysonForgeDataSubstrate()
        self.biosphere = BiosphereDataSubstrate()
        self.activity = get_system_sampler()
        self.carrier = get_carrier()

    def process(self, command: str) -> dict:
        text = command.strip()
        if not text:
            raise ValueError('Enter text or a built-in command. Type help for options.')
        if len(text) > 10000:
            raise ValueError('Input is limited to 10,000 characters per pass.')
        raw = text.encode('utf-8')
        binary = ' '.join((f'{byte:08b}' for byte in raw))
        bits = [int(bit) for bit in ''.join((f'{byte:08b}' for byte in raw))]
        trits = self.ternary.encode_bytes_balanced(raw)
        activity = self.activity.snapshot(force=True)
        runtime_state = self.substrate.capture_runtime_state()
        carrier = self.carrier.sample()
        invariants = self.kernel.validate_invariants(0, 0) and self.kernel.validate_invariants(1, 1)
        chain_node = self.kernel.reconcile_chain(7)
        conditioned = self.conditioner.inject_signal_packet(carrier['frequency_hz'])
        spectral = self.conditioner.process_spectral_flush()
        grid_rows = [bits[i:i + 8] for i in range(0, min(len(bits), 256), 8)]
        if not grid_rows:
            grid_rows = [[0]]
        matrix = self.ternary.compute_optimization_grid(grid_rows)
        matrix_score = self.ternary.ternary_dot_product(matrix, [1] * len(matrix))
        stellar_flux = self.stellar.fetch_live_flux(activity=activity, carrier_sample=carrier)
        stellar_report = self.stellar.compile_stellar_telemetry(stellar_flux)
        dyson_report = self.dyson.calculate_telemetry_flux(activity=activity, carrier_sample=carrier)
        biosphere_pulse = self.biosphere.fetch_live_pulse(activity=activity, carrier_sample=carrier)
        phase = carrier['phase_rad']
        bit_sample = bits[:32]
        phase_states = [cmath.rect(float(bit), phase + index * math.pi / 4) for index, bit in enumerate(bit_sample)]
        occupied = sum((1 for value in bit_sample if value))
        occupancy = occupied / len(bit_sample) if bit_sample else 0.0
        quantum_sample = ' '.join((f'{value.real:+.2f}{value.imag:+.2f}i' for value in phase_states[:12]))
        return {'command': text, 'utf8_bytes': len(raw), 'binary': binary, 'ternary': ' '.join(trits), 'quantum_sample': quantum_sample or '(empty)', 'occupancy': occupancy, 'matrix_score': matrix_score, 'matrix_cells': sum((len(row) for row in grid_rows)), 'carrier': carrier, 'conditioned_hz': conditioned, 'spectral': spectral, 'activity': activity, 'runtime_state': runtime_state, 'chain_node': chain_node, 'stellar_flux_model_wm2': stellar_flux, 'dyson_power_model_w': dyson_report['captured_power_watts'], 'biosphere_carrier_hz': biosphere_pulse, 'modules': ['logic substrate', '7.83 Hz conditioner', 'balanced ternary matrix', 'system data substrate', 'stellar model', 'Dyson model', 'biosphere model', 'phase projection'], 'note': 'Astronomy and quantum-labelled values are application models; only OS telemetry fields are local system readings.', 'stellar_summary': stellar_report[3:6]}

class SovereignWindow:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.engine = SovereignEngine()
        self.last_result = None
        self.frame_number = 0
        self.particles = [(random.random(), random.random(), random.uniform(0.5, 2.0), random.random() * math.tau) for _ in range(90)]
        self.root.title('HYDROGEN ATOM // SOVEREIGN MATRIX ENGINE')
        self.root.geometry('1320x980')
        self.root.minsize(1000, 740)
        self.root.configure(bg=BG)
        self._build()
        self.root.protocol('WM_DELETE_WINDOW', self.root.destroy)
        self._tick()

    def _build(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(5, weight=1)
        header = tk.Frame(self.root, bg=BG)
        header.grid(row=0, column=0, sticky='ew', padx=22, pady=(16, 9))
        header.columnconfigure(0, weight=1)
        tk.Label(header, text='SOVEREIGN MATRIX ENGINE', bg=BG, fg=WHITE, font=('Segoe UI', 20, 'bold')).grid(row=0, column=0, sticky='w')
        tk.Label(header, text='LOCAL SYSTEM TELEMETRY  /  CARRIER-DRIVEN FLUX  /  SAFE TEXT PROCESSING', bg=BG, fg=CYAN, font=('Consolas', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=(3, 0))
        self.clock_label = tk.Label(header, text='', bg=BG, fg=MUTED, font=('Consolas', 10))
        self.clock_label.grid(row=0, column=1, rowspan=2, sticky='e')
        metrics = tk.Frame(self.root, bg=BG)
        metrics.grid(row=1, column=0, sticky='ew', padx=22, pady=(0, 10))
        for i in range(5):
            metrics.columnconfigure(i, weight=1, uniform='metric')
        self.metric_vars = {}
        for index, (key, title) in enumerate((('cpu', 'CPU LOAD'), ('memory', 'MEMORY'), ('gpu', 'GPU LOAD'), ('network', 'TOTAL NETWORK'), ('carrier', 'SOFTWARE CARRIER'))):
            card = tk.Frame(metrics, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
            card.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 7, 0))
            tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=('Consolas', 9, 'bold')).pack(anchor='w', padx=13, pady=(10, 3))
            var = tk.StringVar(value='—')
            self.metric_vars[key] = var
            tk.Label(card, textvariable=var, bg=PANEL, fg=CYAN if key != 'memory' else GREEN, font=('Segoe UI', 16, 'bold')).pack(anchor='w', padx=13, pady=(0, 11))
        visual = tk.Frame(self.root, bg=BG)
        visual.grid(row=2, column=0, sticky='nsew', padx=22, pady=(0, 11))
        visual.columnconfigure(0, weight=3)
        visual.columnconfigure(1, weight=1)
        visual.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(visual, bg='#050b13', highlightthickness=1, highlightbackground=LINE, height=290)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=(0, 9))
        side = tk.Frame(visual, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        side.grid(row=0, column=1, sticky='nsew')
        tk.Label(side, text='ENGINE FLOW', bg=PANEL, fg=WHITE, font=('Consolas', 10, 'bold')).pack(anchor='w', padx=13, pady=(13, 8))
        self.flow_text = tk.Text(side, height=10, bg=PANEL, fg=CYAN, insertbackground=CYAN, relief='flat', wrap='word', font=('Consolas', 9), padx=12, pady=8)
        self.flow_text.pack(fill='both', expand=True, padx=8, pady=(0, 9))
        self.flow_text.configure(state='disabled')
        self.activity_source = tk.Label(side, text='', bg=PANEL, fg=MUTED, justify='left', wraplength=230, font=('Segoe UI', 8))
        self.activity_source.pack(fill='x', padx=13, pady=(0, 13))
        input_header = tk.Frame(self.root, bg=BG)
        input_header.grid(row=3, column=0, sticky='ew', padx=22)
        tk.Label(input_header, text='COMMAND INPUT', bg=BG, fg=WHITE, font=('Consolas', 10, 'bold')).pack(side='left')
        tk.Label(input_header, text='Text is processed as data; commands: help, status', bg=BG, fg=MUTED, font=('Segoe UI', 9)).pack(side='left', padx=12)
        actions = tk.Frame(input_header, bg=BG)
        actions.pack(side='right')
        self.analyze_button = self._button(actions, 'ANALYZE WITH LLAMA 3', self._analyze)
        self.analyze_button.pack(side='right', padx=(8, 0))
        self._button(actions, 'PROCESS THROUGH ENGINE', self._process).pack(side='right')
        self.command_input = tk.Text(self.root, height=6, bg='#0a1420', fg=WHITE, insertbackground=CYAN, relief='flat', wrap='word', font=('Consolas', 11), padx=12, pady=10, highlightthickness=1, highlightbackground=LINE)
        self.command_input.grid(row=4, column=0, sticky='ew', padx=22, pady=(7, 12))
        self.command_input.insert('1.0', 'Enter a command or any text to route through the matrix…')
        self.command_input.bind('<Control-Return>', lambda _event: self._process())
        outputs = tk.Frame(self.root, bg=BG)
        outputs.grid(row=5, column=0, sticky='nsew', padx=22, pady=(0, 12))
        outputs.columnconfigure(0, weight=1)
        outputs.columnconfigure(1, weight=1)
        outputs.rowconfigure(1, weight=1)
        tk.Label(outputs, text='ENGINE OUTPUT', bg=BG, fg=CYAN, font=('Consolas', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 5))
        tk.Label(outputs, text='LLAMA 3 PROCESSING ANALYSIS · LOCAL OLLAMA', bg=BG, fg=GOLD, font=('Consolas', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=(9, 0), pady=(0, 5))
        self.result_output = self._output_box(outputs, row=1, column=0)
        self.analysis_output = self._output_box(outputs, row=1, column=1, padx=(9, 0))
        self._set_text(self.analysis_output, 'Analysis is generated by the local Ollama endpoint when you select ‘Analyze with Llama 3’. No text is sent to a cloud service.')
        footer = tk.Label(self.root, text='7.83 Hz is a generated software reference used for animation and phase calculations, not an environmental sensor. CPU/RAM/network readings are local OS counters; GPU is shown when NVIDIA NVML is available.', bg=BG, fg=MUTED, font=('Segoe UI', 8), anchor='w')
        footer.grid(row=6, column=0, sticky='ew', padx=22, pady=(0, 12))

    def _button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg='#103148', fg=WHITE, activebackground='#175074', activeforeground=WHITE, relief='flat', padx=13, pady=8, font=('Segoe UI', 9, 'bold'), cursor='hand2')

    def _output_box(self, parent, row, column, padx=0):
        frame = tk.Frame(parent, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        frame.grid(row=row, column=column, sticky='nsew', padx=padx)
        box = tk.Text(frame, bg=PANEL, fg=WHITE, insertbackground=CYAN, relief='flat', wrap='word', font=('Consolas', 9), padx=11, pady=10)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=box.yview)
        box.configure(yscrollcommand=scroll.set, state='disabled')
        box.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        return box

    @staticmethod
    def _set_text(widget, text):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.configure(state='disabled')

    def _process(self):
        command = self.command_input.get('1.0', 'end-1c').strip()
        if command == 'Enter a command or any text to route through the matrix…':
            command = ''
        if command.lower() == 'help':
            command = 'help — process arbitrary text, or type status for a local telemetry snapshot.'
        elif command.lower() == 'status':
            command = 'SYSTEM STATUS'
        try:
            result = self.engine.process(command)
        except Exception as exc:
            self._set_text(self.result_output, f'Input not processed\n\n{exc}')
            return
        self.last_result = result
        self._set_text(self.result_output, self._format_result(result))

    @staticmethod
    def _format_result(result):
        activity = result['activity']
        cpu = 'unavailable' if activity.cpu_percent is None else f'{activity.cpu_percent:.1f}%'
        memory = 'unavailable' if activity.memory_percent is None else f'{activity.memory_percent:.1f}%'
        carrier = result['carrier']
        return f"INPUT  {result['command']}\nUTF-8 BYTES  {result['utf8_bytes']}\n\nBINARY  {result['binary'][:700]}{(' …' if len(result['binary']) > 700 else '')}\n\nBALANCED TERNARY  {result['ternary'][:700]}{(' …' if len(result['ternary']) > 700 else '')}\n\nPHASE PROJECTION SAMPLE  {result['quantum_sample']}\nONE-STATE OCCUPANCY  {result['occupancy']:.3f}  (derived visualization)\nMATRIX  {result['matrix_cells']} cells · aggregate state {result['matrix_score']:+d}\nPIPELINE  {' → '.join(result['modules'])}\n\nLOCAL TELEMETRY  CPU {cpu} · RAM {memory} · GPU {('unavailable' if activity.gpu_percent is None else f'{activity.gpu_percent:.1f}%')} · NET ↓ {format_rate(activity.network_recv_bytes_sec)} / ↑ {format_rate(activity.network_sent_bytes_sec)}\nSOFTWARE CARRIER  {carrier['frequency_hz']:.2f} Hz · phase {carrier['phase_rad']:.3f} rad · conditioner {result['conditioned_hz']:.4f} Hz\nMODEL VALUES  stellar flux {result['stellar_flux_model_wm2']:.2f} W/m² · Dyson capture {result['dyson_power_model_w']:.3e} W · biosphere {result['biosphere_carrier_hz']:.4f} Hz\n\n{result['note']}"

    def _analyze(self):
        if not self.last_result:
            self._process()
        if not self.last_result:
            return
        self.analyze_button.configure(state='disabled', text='ANALYZING…')
        self._set_text(self.analysis_output, 'Waiting for the local Ollama model…')
        result = self.last_result
        worker = threading.Thread(target=self._ollama_worker, args=(result,), daemon=True)
        worker.start()

    def _ollama_worker(self, result):
        endpoint = os.environ.get('GODMIND_OLLAMA_URL', 'http://127.0.0.1:11434/api/chat')
        model = os.environ.get('GODMIND_LLAMA_MODEL', 'llama3')
        parsed_endpoint = urlsplit(endpoint)
        if parsed_endpoint.scheme != 'http' or parsed_endpoint.hostname not in {'127.0.0.1', 'localhost', '::1'}:
            self.root.after(0, lambda: self._analysis_done('The Llama endpoint must be a local Ollama HTTP address (localhost, 127.0.0.1, or ::1).'))
            return
        compact = {'input': result['command'], 'bytes': result['utf8_bytes'], 'binary_prefix': result['binary'][:320], 'balanced_ternary_prefix': result['ternary'][:240], 'phase_projection_sample': result['quantum_sample'], 'carrier_hz': result['carrier']['frequency_hz'], 'carrier_phase_rad': result['carrier']['phase_rad'], 'matrix_state': result['matrix_score'], 'modules': result['modules'], 'telemetry': {'cpu_percent': result['activity'].cpu_percent, 'memory_percent': result['activity'].memory_percent, 'gpu_percent': result['activity'].gpu_percent, 'gpu_memory_percent': result['activity'].gpu_memory_percent, 'network_recv_bytes_sec': result['activity'].network_recv_bytes_sec, 'network_sent_bytes_sec': result['activity'].network_sent_bytes_sec, 'source': result['activity'].source}, 'modeled_subsystems': {'stellar_flux_model_wm2': result['stellar_flux_model_wm2'], 'dyson_power_model_w': result['dyson_power_model_w'], 'biosphere_carrier_hz': result['biosphere_carrier_hz'], 'conditioned_frequency_hz': result['conditioned_hz'], 'spectral_variance': result['spectral']['spectral_variance']}}
        body = {'model': model, 'stream': False, 'messages': [{'role': 'system', 'content': 'Analyze this local software pipeline run. Distinguish measured operating-system telemetry from generated simulations and the mathematical 7.83 Hz software carrier. Do not claim physical quantum computation or environmental resonance measurement. Be concise; report transformations, activity coupling, and any limitations.'}, {'role': 'user', 'content': json.dumps(compact, ensure_ascii=False)}]}
        try:
            request = Request(endpoint, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode('utf-8'))
            answer = payload.get('message', {}).get('content', 'No analysis text returned by Ollama.')
        except (URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
            answer = f"Local Llama 3 analysis is unavailable. Start Ollama and pull the '{model}' model, or set GODMIND_OLLAMA_URL / GODMIND_LLAMA_MODEL.\n\nDetails: {exc}"
        self.root.after(0, lambda: self._analysis_done(answer))

    def _analysis_done(self, answer):
        self._set_text(self.analysis_output, answer)
        self.analyze_button.configure(state='normal', text='ANALYZE WITH LLAMA 3')

    def _tick(self):
        snapshot = self.engine.activity.snapshot()
        carrier = self.engine.carrier.sample()
        cpu = '—' if snapshot.cpu_percent is None else f'{snapshot.cpu_percent:4.1f}%'
        if snapshot.memory_percent is None:
            memory = 'unavailable'
        elif snapshot.memory_used_gb is None or snapshot.memory_total_gb is None:
            memory = f'{snapshot.memory_percent:.1f}%'
        else:
            memory = f'{snapshot.memory_used_gb:.1f}/{snapshot.memory_total_gb:.1f} GB · {snapshot.memory_percent:.1f}%'
        self.metric_vars['cpu'].set(cpu)
        self.metric_vars['memory'].set(memory)
        self.metric_vars['gpu'].set('unavailable' if snapshot.gpu_percent is None else f'{snapshot.gpu_percent:.1f}%')
        self.metric_vars['network'].set(f'↓ {format_rate(snapshot.network_recv_bytes_sec)}  ↑ {format_rate(snapshot.network_sent_bytes_sec)}')
        self.metric_vars['carrier'].set(f"7.83 Hz  ·  {carrier['sin']:+.2f}")
        self.clock_label.configure(text=time.strftime('%Y-%m-%d  %H:%M:%S'))
        self.activity_source.configure(text=f'Readings: {snapshot.source}\nNetwork rates update from aggregate counter deltas.')
        self._draw_matrix(snapshot.cpu_percent or 0.0, carrier)
        self._set_text(self.flow_text, 'INPUT\n ↓\nUTF-8 → BINARY\n ↓\nBALANCED TERNARY\n ↓\nPHASE PROJECTION\n ↓\nSUBSTRATE + STELLAR + DYSON + BIOSPHERE\n ↓\nRESULT  /  LOCAL LLAMA 3')
        self.frame_number += 1
        self.root.after(40, self._tick)

    def _draw_matrix(self, cpu, carrier):
        canvas = self.canvas
        canvas.delete('all')
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        phase = carrier['phase_rad']
        amplitude = 5 + min(1.0, cpu / 100.0) * 15
        spacing = 27
        center_x, center_y = (width * 0.5, height * 0.59)
        for gx in range(14, width, spacing):
            for gy in range(10, height - 28, spacing):
                dx, dy = (gx - center_x, gy - center_y)
                distance = math.hypot(dx, dy) + 1.0
                ripple = math.sin(phase + distance * 0.037) * amplitude
                x = gx + dx / distance * ripple
                y = gy + dy / distance * ripple
                glow = max(0.15, 1.0 - distance / max(width, height))
                color = '#%02x%02x%02x' % (int(10 + 12 * glow), int(35 + 80 * glow), int(60 + 100 * glow))
                radius = 1 + (1 if glow > 0.65 else 0)
                canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline='')
        radius = min(width, height) * (0.16 + min(1.0, cpu / 100.0) * 0.025)
        for ring in range(3):
            r = radius + ring * 15 + math.sin(phase + ring) * 4
            canvas.create_oval(center_x - r, center_y - r, center_x + r, center_y + r, outline=CYAN if ring == 0 else LINE, width=2 if ring == 0 else 1)
        canvas.create_oval(center_x - 8, center_y - 8, center_x + 8, center_y + 8, fill=WHITE, outline=CYAN)
        orbit_rate = 0.12 + min(1.0, cpu / 100.0) * 0.34
        for index, (x0, y0, size, offset) in enumerate(self.particles):
            angle = offset + phase * (0.055 + orbit_rate * 0.12) + self.frame_number * 0.002
            orbit = radius * (1.12 + index % 5 * 0.15)
            x = center_x + math.cos(angle) * orbit * (1.0 + math.sin(phase + offset) * 0.035)
            y = center_y + math.sin(angle) * orbit * 0.52
            flicker = random.random() < 0.02 + min(0.25, cpu / 400.0)
            color = WHITE if flicker else CYAN if index % 3 else BLUE
            canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline='')
        wave_y = height - 22
        canvas.create_line(12, wave_y, width - 12, wave_y, fill=LINE)
        points = []
        for x in range(0, width, 5):
            sample_phase = phase - (width - x) * math.tau * 7.83 / max(1, width * 80)
            y = wave_y - math.sin(sample_phase) * min(12, 5 + cpu * 0.07)
            points.extend((x, y))
        if len(points) >= 4:
            canvas.create_line(*points, fill=CYAN, width=1.5, smooth=True)
        canvas.create_text(14, 14, text=f"ACTIVITY-COUPLED FLUX GRID   /   CPU {cpu:.1f}%   /   PHASE {carrier['phase_rad']:.2f} rad", fill=MUTED, anchor='nw', font=('Consolas', 9, 'bold'))

def main():
    root = tk.Tk()
    SovereignWindow(root)
    root.mainloop()
