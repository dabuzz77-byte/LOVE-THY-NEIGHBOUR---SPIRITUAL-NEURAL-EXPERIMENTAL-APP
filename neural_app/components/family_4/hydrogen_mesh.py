"""Hydrogen Mesh desktop application. Python standard library only."""
from __future__ import annotations
import base64
from collections import deque
from neural_app.capture_output import redirect_stdout
import hashlib
import io
import json
import math
import os
from pathlib import Path
import queue
import random
import shutil
import subprocess
import sys
from neural_app import section_threads as threading
import time
from neural_app import component_ui as tk
from neural_app.component_ui import ttk, filedialog, messagebox
from urllib.request import Request, urlopen
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'legacy'))
from .legacy.sovereign_engine import SovereignEngine
from .legacy.module_runtime import get_system_sampler
from .mesh_bus import BusServer, encoded
from .bridges import DEFAULTS, FluxBridge, ObservatoryBridge, publish_chunks
from .catalog import discover, processes
from .signals import packet, from_bits, generate, decode
from .bounded_io import cap_directory, drain_process
try:
    from .scene_renderer import SceneRenderer
    from neural_app import component_ui as ImageTk
except ImportError:
    SceneRenderer = None
BG = '#071019'
PANEL = '#0d1c29'
EDGE = '#203747'
TEXT = '#e4f1f4'
MUTED = '#82a3b5'
CYAN = '#42ead5'
BLUE = '#548dff'
GOLD = '#ffd08a'

class Runtime:

    def __init__(self, data_dir=None, port=8794):
        self.data = Path(data_dir or BASE / 'data')
        self.data.mkdir(parents=True, exist_ok=True)
        config_path = self.data / 'settings.json'
        self.config = {**DEFAULTS, **(json.loads(config_path.read_text()) if config_path.exists() else {})}
        config_path.write_text(json.dumps(self.config, indent=2), encoding='utf-8')
        storage = dict(max_storage_mb=self.config.setdefault('storage_limit_mb', 64), max_messages=self.config.setdefault('history_messages', 4000), max_age_hours=self.config.setdefault('history_hours', 24))
        config_path.write_text(json.dumps(self.config, indent=2), encoding='utf-8')
        self.server = BusServer(self.data, port, int(self.config.get('broadcast_port', 8796)), storage=storage)
        self.ledger = self.server.ledger
        self.engine = SovereignEngine()
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.errors = deque(maxlen=100)
        self.bridges = [FluxBridge(self.ledger, self.config), ObservatoryBridge(self.ledger, self.config['observatory_connection'])]
        for bridge in self.bridges:
            bridge.start()
        self.auto = True
        self.catalog = dict(items=[], visited=0, truncated=False, scanned=False)
        self.processes = []
        self.catalog_busy = False
        self.latest = None
        self.step = 0
        self.generator = False
        self.mode = 'OS random'
        self.size = 64
        self.seed = 'hydrogen'
        self.work = queue.Queue(maxsize=32)
        self.ui_events = queue.Queue(maxsize=512)
        self.cursor = self.ledger.cursor('hydrogen.engine', self.ledger.latest())
        self.last_inventory = None
        self.worker = threading.Thread(target=self.loop, daemon=True)
        self.worker.start()

    def notify(self, kind, data):
        try:
            self.ui_events.put_nowait((kind, data))
        except queue.Full:
            pass

    def scan(self):
        if self.catalog_busy:
            return
        self.catalog_busy = True

        def run():
            try:
                self.catalog = dict(discover(self.config['apps_root']), scanned=True)
                self.processes = processes()
                self.notify('catalog', self.catalog)
            except Exception as e:
                self.errors.append(str(e))
            finally:
                self.catalog_busy = False
        threading.Thread(target=run, daemon=True).start()

    def emit(self, topic, data, route=None, target='*'):
        result = self.ledger.publish(dict(source='hydrogen', topic=topic, data=data, route=route or ['hydrogen'], target=target))
        self.notify('published', result)
        return result

    def process(self, text, route=None, parent=None, reply_to=None):
        identity = 'hydrogen:' + hashlib.sha256(parent.encode()).hexdigest() if parent else 'hydrogen:' + os.urandom(16).hex()
        cache = self.data / 'processing'
        cache.mkdir(exist_ok=True)
        cache_path = cache / (hashlib.sha256(identity.encode()).hexdigest() + '.json')
        if parent and cache_path.exists():
            data = json.loads(cache_path.read_text(encoding='utf-8'))
            receipt = data['signal']
            result = data['result']
        else:
            with self.lock:
                result = self.engine.process(text)
            receipt = packet(text.encode('utf-8'), mode='UTF-8') if len(text.encode('utf-8')) <= 16384 else None
            data = dict(result=result, signal=receipt, parent_id=parent)
            if parent:
                temp = cache_path.with_suffix('.tmp')
                temp.write_bytes(encoded(data))
                temp.replace(cache_path)
        wire_result = {k: v for k, v in result.items() if k not in ('binary', 'ternary', 'quantum_sample')}
        wire_result.update(binary_preview=result.get('binary', '')[:512], ternary_preview=result.get('ternary', '')[:256], phase_preview=result.get('quantum_sample', '')[:256])
        wire_signal = {k: v for k, v in receipt.items() if k not in ('bits', 'hex')} if receipt else None
        publish_chunks(self.ledger, 'hydrogen', 'hydrogen.result', dict(result=wire_result, signal=wire_signal, parent_id=parent, encoding_note='Exact input in result.command; exact signal bytes in signal.base64. Expanded forms are previews.'), (route or []) + ['hydrogen'], identity, reply_to=reply_to)
        if receipt:
            self.latest = receipt
        self.notify('result', data)
        if parent:
            cache_path.unlink(missing_ok=True)
        return data

    def generate(self):
        value = generate(self.mode, self.size, self.seed, self.step)
        self.step += 1
        self.latest = value
        self.emit('signal.frame', value)
        self.notify('signal', value)
        return value

    def loop(self):
        self._shared_next_generation = getattr(self, '_shared_next_generation', 0)
        self._shared_next_process_scan = getattr(self, '_shared_next_process_scan', 0)
        self._shared_next_cleanup = getattr(self, '_shared_next_cleanup', 0)
        for _shared_tick in range(1):
            try:
                try:
                    action, payload = self.work.get_nowait()
                    try:
                        if action == 'text':
                            self.process(payload)
                        elif action == 'generate':
                            self.generate()
                        elif action == 'bits':
                            self.latest = from_bits(payload)
                            self.emit('signal.literal', self.latest)
                            self.notify('signal', self.latest)
                        elif action == 'legacy-pipeline':
                            from .legacy.pipeline_integrated_system import IntegratedSystemPipeline
                            capture = io.StringIO()
                            with redirect_stdout(capture):
                                IntegratedSystemPipeline().execute_system_pass(1)
                            self.emit('hydrogen.pipeline', {'output': capture.getvalue()})
                            self.notify('analysis', capture.getvalue())
                        elif action == 'llama':
                            self.llama(payload)
                        elif action == 'compact':
                            self.ledger.maintenance(force=True, compact=True)
                            info = self.ledger.stats()
                            self.notify('analysis', f"Storage compacted. {info['retained']:,} recent messages retained; {info['storage']['disk_bytes'] / 1048576:.2f} MB on disk. Old history expires automatically.")
                    finally:
                        self.work.task_done()
                except queue.Empty:
                    pass
                if self.generator and time.monotonic() >= self._shared_next_generation:
                    self.generate()
                    self._shared_next_generation = time.monotonic() + 1
                if time.monotonic() >= self._shared_next_cleanup:
                    self.ledger.maintenance()
                    cap_directory(self.data / 'processing', max_files=32)
                    cap_directory(self.data / 'launches')
                    self._shared_next_cleanup = time.monotonic() + 30
                if time.monotonic() >= self._shared_next_process_scan:
                    self.processes = processes()
                    self.notify('processes', self.processes)
                    self._shared_next_process_scan = time.monotonic() + 5
                    inventory = [dict(pid=p['pid'], name=p['name']) for p in self.processes]
                    if inventory != self.last_inventory:
                        self.emit('process.inventory', dict(processes=inventory, scope='Executable names and PIDs only; connection status is separate'))
                        self.last_inventory = inventory
                if self.auto:
                    for event in self.ledger.read(self.cursor, 4):
                        if len(event['route']) < 12 and event['source'] != 'hydrogen' and ('hydrogen' not in event['route']) and (event['target'] in ('*', 'hydrogen')) and (event['topic'] not in ('client.attached', 'process.inventory')):
                            text = self.processing_text(event)
                            self.process(text, event['route'], event['id'], reply_to=event['source'])
                            status = 'Hydrogen processed input or explicit bounded payload summary'
                        else:
                            status = None
                        self.cursor = event['seq']
                        self.ledger.advance('hydrogen.engine', self.cursor, event['id'] if status else None, status or 'skipped')
            except Exception as e:
                self.errors.append(str(e))
                self.notify('error', str(e))
                self.stop.wait(0.2)
            self.stop.wait(0.05)

    @staticmethod
    def processing_text(event):
        data = event['data']
        direct = data if isinstance(data, str) else data.get('text') if isinstance(data, dict) else None
        if isinstance(direct, str) and len(direct.strip()) and (len(direct) <= 8192):
            return direct
        raw = encoded(data)
        if len(raw) <= 2048:
            return raw.decode()
        return json.dumps(dict(processing_scope='Summary only; full original is in the rolling event ledger', source=event['source'], topic=event['topic'], payload_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), keys=list(data)[:32] if isinstance(data, dict) else [], preview=direct[:512] if isinstance(direct, str) else None), ensure_ascii=False)

    def llama(self, text):
        model = self.config.get('ollama_model', 'llama3')
        body = dict(model=model, stream=False, messages=[dict(role='system', content='Explain this local software signal pipeline concisely. Distinguish OS readings from mathematical simulations. Propose useful data processing; do not claim physical quantum or energy effects.'), dict(role='user', content=text)])
        try:
            with urlopen(Request('http://127.0.0.1:11434/api/chat', data=encoded(body), headers={'Content-Type': 'application/json'}), timeout=45) as response:
                answer = json.load(response)['message']['content']
            self.emit('inference.result', {'model': model, 'answer': answer})
            self.notify('analysis', answer)
        except Exception as e:
            self.notify('analysis', 'Local Ollama unavailable: ' + str(e))

    def launch(self, item):
        if item.get('error'):
            raise ValueError(item['error'])
        path = Path(item['path'])
        env = os.environ.copy()
        env['HYDROGEN_MESH_CONNECTION'] = str(self.server.connection)
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        if item['kind'] == 'Python':
            args = [sys.executable, str(BASE / 'launch_connected.py'), str(path)]
        elif item['kind'] == 'Java source':
            args = [shutil.which('java') or 'java', str(path)]
        elif item['kind'] == 'Java archive':
            args = [shutil.which('java') or 'java', '-jar', str(path)]
        else:
            args = [str(path)]
        log = self.data / 'launches'
        log.mkdir(exist_ok=True)
        child = subprocess.Popen(args, cwd=path.parent, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags)
        threading.Thread(target=drain_process, args=(child, log / (path.stem + '.log')), daemon=True).start()
        self.notify('analysis', f'Launched {path.name} · PID {child.pid}. Python receives MESH_BUS and MESH_INBOX. Java and executables need a cooperative adapter; launch alone does not connect their internal data.')
        return child.pid

    def close(self):
        self.stop.set()
        for bridge in self.bridges:
            bridge.close()
        self.server.close()

class App:

    def __init__(self, root, runtime):
        self.root = root
        self.rt = runtime
        self.events_cursor = max(0, runtime.ledger.latest() - 50)
        self.bits = ''
        self.previous = ''
        self.signal_total = 0
        self.frame = 0
        self.pulses = deque(maxlen=50)
        self.log_rows = deque(maxlen=300)
        self.pointer = None
        self.renderer = SceneRenderer() if SceneRenderer else None
        self.photo = None
        self.canvas_image = None
        self.next_ledger_poll = 0
        self.render_ms = 0
        self.root.title('Hydrogen Mesh · Unified signal studio')
        self.root.geometry('1320x900')
        self.root.minsize(860, 650)
        self.root.configure(bg=BG)
        self.setup_style()
        self.build()
        self.notebook.bind('<<NotebookTabChanged>>', self.tab_changed)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()

    def tab_changed(self, event=None):
        if self.notebook.index('current') == 2 and (not self.rt.catalog.get('scanned')):
            self.rt.scan()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', background=PANEL, foreground=MUTED, padding=(18, 10))
        style.map('TNotebook.Tab', background=[('selected', '#153848')], foreground=[('selected', CYAN)])
        style.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=28, borderwidth=0)
        style.configure('Treeview.Heading', background='#183241', foreground=MUTED)
        style.map('Treeview', background=[('selected', '#20506b')])
        style.configure('TCombobox', fieldbackground=PANEL, foreground=TEXT, background=EDGE)
        self.root.option_add('*TCombobox*Listbox.background', PANEL)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT)

    def label(self, parent, text, size=10, color=TEXT, **kw):
        return tk.Label(parent, text=text, font=('Segoe UI', size), bg=kw.pop('bg', BG), fg=color, **kw)

    def button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg='#173847', fg=TEXT, activebackground='#256071', activeforeground=CYAN, relief='flat', padx=13, pady=8, cursor='hand2', font=('Segoe UI', 10))

    def text(self, parent, height=8):
        frame = tk.Frame(parent, bg=PANEL)
        box = tk.Text(frame, bg=PANEL, fg=TEXT, insertbackground=CYAN, font=('Consolas', 10), wrap='word', relief='flat', padx=12, pady=10, height=height)
        scroll = ttk.Scrollbar(frame, command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        box.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        return (frame, box)

    def write(self, box, text):
        box.configure(state='normal')
        box.delete('1.0', 'end')
        box.insert('1.0', text)
        box.configure(state='disabled')

    def enqueue(self, action, data=None):
        try:
            self.rt.work.put_nowait((action, data))
        except queue.Full:
            messagebox.showinfo('Busy', 'The processing queue is full. Wait for existing jobs.')

    def build(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill='x', padx=24, pady=(18, 12))
        self.label(header, 'HYDROGEN / MESH', 22).pack(side='left')
        self.label(header, 'UNIFIED SIGNAL STUDIO', 10, CYAN).pack(side='left', padx=20)
        self.state_label = self.label(header, 'Starting…', 10, MUTED)
        self.state_label.pack(side='right')
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=18, pady=(0, 12))
        self.tabs = {}
        for title in ('Live matrix', 'Signal workbench', 'Applications & bus', 'Event ledger', 'Engine coverage'):
            tab = tk.Frame(self.notebook, bg=BG)
            self.notebook.add(tab, text=title)
            self.tabs[title] = tab
        self.build_matrix()
        self.build_workbench()
        self.build_apps()
        self.build_events()
        self.build_coverage()
        self.footer = self.label(self.root, 'Local loopback bus · 7.83 Hz is a software reference · astronomical values are illustrative models', 9, MUTED)
        self.footer.pack(fill='x', padx=24, pady=(0, 10))

    def build_matrix(self):
        tab = self.tabs['Live matrix']
        tools = tk.Frame(tab, bg=BG)
        tools.pack(fill='x', padx=12, pady=12)
        self.preset = tk.StringVar(value='Cosmos')
        ttk.Combobox(tools, textvariable=self.preset, values=['Cosmos', 'Hydrogen', 'Stellar', 'Earth', 'Matrix', 'Dyson'], state='readonly', width=13).pack(side='left')
        self.quality = tk.StringVar(value='Balanced')
        ttk.Combobox(tools, textvariable=self.quality, values=['Balanced', 'High', 'Low power'], state='readonly', width=10).pack(side='left', padx=8)
        self.visual_pulses = tk.BooleanVar(value=True)
        tk.Checkbutton(tools, text='Stochastic pulses', variable=self.visual_pulses, bg=BG, fg=CYAN, selectcolor=PANEL, activebackground=BG).pack(side='left', padx=6)
        self.hold = False
        self.button(tools, 'Hold / resume display', lambda: setattr(self, 'hold', not self.hold)).pack(side='right')
        self.canvas = tk.Canvas(tab, bg='#050d15', highlightthickness=1, highlightbackground=EDGE)
        self.canvas.pack(fill='both', expand=True, padx=12)
        self.canvas.bind('<Motion>', lambda e: setattr(self, 'pointer', (e.x, e.y)))
        self.canvas.bind('<Leave>', lambda e: setattr(self, 'pointer', None))
        self.metrics = self.label(tab, 'Waiting for a signal. Process text or generate a frame in Signal workbench.', 11, CYAN, anchor='w')
        self.metrics.pack(fill='x', padx=14, pady=12)
        row = tk.Frame(tab, bg=BG)
        row.pack(fill='x', padx=12, pady=(0, 14))
        self.button(row, 'Generate frame', lambda: self.enqueue('generate')).pack(side='left')
        self.button(row, 'Open workbench', lambda: self.notebook.select(self.tabs['Signal workbench'])).pack(side='left', padx=8)
        self.matrix_bus = self.label(row, '', 10, MUTED, anchor='e')
        self.matrix_bus.pack(side='right')

    def build_workbench(self):
        tab = self.tabs['Signal workbench']
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(3, weight=1)
        bar = tk.Frame(tab, bg=BG)
        bar.grid(row=0, column=0, sticky='ew', padx=12, pady=12)
        self.mode = tk.StringVar(value='OS random')
        self.size = tk.StringVar(value='64')
        self.seed = tk.StringVar(value='hydrogen')
        ttk.Combobox(bar, textvariable=self.mode, values=['OS random', 'Seeded test', 'Counter', 'Cellular automaton'], state='readonly', width=20).pack(side='left')
        self.label(bar, 'Bytes').pack(side='left', padx=(14, 4))
        tk.Entry(bar, textvariable=self.size, width=6, bg=PANEL, fg=TEXT, insertbackground=CYAN).pack(side='left')
        self.label(bar, 'Seed').pack(side='left', padx=(14, 4))
        tk.Entry(bar, textvariable=self.seed, width=14, bg=PANEL, fg=TEXT, insertbackground=CYAN).pack(side='left')
        self.button(bar, 'Generate', self.generate).pack(side='left', padx=12)
        self.running = tk.BooleanVar()
        tk.Checkbutton(bar, text='Stream 1 frame/s', variable=self.running, command=self.toggle_generator, bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG).pack(side='left')
        frame, self.input = self.text(tab, 5)
        frame.grid(row=1, column=0, sticky='ew', padx=12)
        self.input.insert('1.0', 'Hydrogen Mesh — connected signals, useful data.')
        actions = tk.Frame(tab, bg=BG)
        actions.grid(row=2, column=0, sticky='ew', padx=12, pady=10)
        for text, command in [('Process UTF-8', lambda: self.enqueue('text', self.input.get('1.0', 'end-1c'))), ('Send literal bits', lambda: self.enqueue('bits', self.input.get('1.0', 'end-1c'))), ('Import bytes', self.import_bytes), ('Export packet', self.export), ('Invert bits', self.invert), ('Local Llama', lambda: self.enqueue('llama', self.input.get('1.0', 'end-1c')))]:
            self.button(actions, text, command).pack(side='left', padx=(0, 6))
        splitter = tk.PanedWindow(tab, orient='horizontal', bg=BG, sashwidth=8)
        splitter.grid(row=3, column=0, sticky='nsew', padx=12, pady=(0, 12))
        left, self.output = self.text(splitter, 15)
        right, self.analysis = self.text(splitter, 15)
        splitter.add(left, minsize=240)
        splitter.add(right, minsize=220)
        self.write(self.output, 'Process text through the preserved logic substrate, ternary, spectral, stellar, Dyson and biosphere engines.\n\nSignals are reversible byte packets with SHA-256, CRC32 and explicit bit lengths. No random bits are described as computation results.')
        self.write(self.analysis, 'Local model replies and app errors appear here.\n\nOS random: operating-system random bytes\nSeeded test: repeatable fixtures\nCounter: transport/ordering tests\nCellular automaton: repeatable Rule 30 patterns\n\nLlama uses local Ollama at 127.0.0.1:11434; model is configurable in data/settings.json.')

    def build_apps(self):
        tab = self.tabs['Applications & bus']
        bar = tk.Frame(tab, bg=BG)
        bar.pack(fill='x', padx=12, pady=12)
        self.button(bar, 'Rescan apps', self.rt.scan).pack(side='left')
        self.button(bar, 'Launch selected', self.launch).pack(side='left', padx=8)
        self.button(bar, 'Open FluxBus', lambda: self.launch_external('flux')).pack(side='left', padx=8)
        self.button(bar, 'Open Observatory', lambda: self.launch_external('obs')).pack(side='left', padx=8)
        self.auto = tk.BooleanVar(value=True)
        tk.Checkbutton(bar, text='Process incoming data', variable=self.auto, command=lambda: setattr(self.rt, 'auto', self.auto.get()), bg=BG, fg=TEXT, selectcolor=PANEL, activebackground=BG).pack(side='right')
        cards = tk.Frame(tab, bg=BG)
        cards.pack(fill='x', padx=12)
        self.label(cards, f'LISTEN  127.0.0.1:{self.rt.server.port}  HTTP + UDP    |    BROADCAST  127.0.0.1:{self.rt.server.udp.broadcast_port}  UDP', 11, CYAN, anchor='w').pack(fill='x', pady=(0, 12))
        self.bridge_labels = []
        for bridge in self.rt.bridges:
            card = tk.Frame(cards, bg=PANEL, highlightbackground=EDGE, highlightthickness=1)
            card.pack(fill='x', pady=(0, 8))
            enabled = tk.BooleanVar(value=True)
            tk.Checkbutton(card, text=bridge.name.upper(), variable=enabled, command=lambda b=bridge, v=enabled: setattr(b, 'enabled', v.get()), bg=PANEL, fg=CYAN, selectcolor=BG, activebackground=PANEL).pack(side='left', padx=10, pady=12)
            label = self.label(card, 'Waiting…', 10, TEXT, bg=PANEL, anchor='w')
            label.pack(side='left', fill='x', expand=True)
            self.bridge_labels.append(label)
        self.label(tab, 'Launch Python with a two-way inbox. Existing processes and Java/executables require cooperative adapters to exchange internal data.', 10, MUTED, anchor='w').pack(fill='x', padx=12, pady=8)
        self.filter = tk.StringVar()
        entry = tk.Entry(tab, textvariable=self.filter, bg=PANEL, fg=TEXT, insertbackground=CYAN)
        entry.pack(fill='x', padx=12, pady=(0, 8))
        entry.bind('<KeyRelease>', lambda e: self.show_catalog())
        self.tree = ttk.Treeview(tab, columns=('app', 'kind', 'file'), show='headings', height=10)
        for key, width in [('app', 260), ('kind', 130), ('file', 550)]:
            self.tree.heading(key, text=key.upper())
            self.tree.column(key, width=width)
        scroll = ttk.Scrollbar(tab, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill='both', expand=True, padx=12)
        self.catalog_label = self.label(tab, 'Catalog loads on opening this tab; scans stay off the graphics thread.', 9, MUTED, anchor='w')
        self.catalog_label.pack(fill='x', padx=12, pady=8)
        self.process_label = self.label(tab, '', 9, MUTED, anchor='w', justify='left')
        self.process_label.pack(fill='x', padx=12, pady=(0, 10))

    def build_events(self):
        tab = self.tabs['Event ledger']
        bar = tk.Frame(tab, bg=BG)
        bar.pack(fill='x', padx=12, pady=10)
        self.label(bar, 'Rolling history: up to 24 hours / 4,000 messages, within the storage budget.', 10, MUTED).pack(side='left')
        self.button(bar, 'Compact storage', lambda: self.enqueue('compact')).pack(side='right', padx=8)
        self.button(bar, 'Export recent messages', self.export_events).pack(side='right')
        self.events = ttk.Treeview(tab, columns=('seq', 'source', 'topic', 'target'), show='headings', height=12)
        for key, width in [('seq', 70), ('source', 150), ('topic', 420), ('target', 160)]:
            self.events.heading(key, text=key.upper())
            self.events.column(key, width=width)
        self.events.pack(fill='both', expand=True, padx=12)
        self.events.bind('<<TreeviewSelect>>', self.event_detail)
        frame, self.detail = self.text(tab, 10)
        frame.pack(fill='both', expand=True, padx=12, pady=12)
        self.write(self.detail, 'Select an event to inspect its full message ID, route and data.')

    def build_coverage(self):
        tab = self.tabs['Engine coverage']
        frame, self.coverage = self.text(tab, 22)
        frame.pack(fill='both', expand=True, padx=12, pady=12)
        self.write(self.coverage, 'ACTIVE IN ONE PROCESS\n\nSovereignEngine → LogicSubstrateKernel → ResonanceBaselineConditioner → BalancedTernaryProcessor → SystemDataSubstrate → StellarCoreSubstrate → DysonForgeDataSubstrate → BiosphereDataSubstrate → phase projection\n\nShared OS sampler and software carrier remain active. The console pipeline is available below.\n\nPRESENTATION CONSOLIDATION\n\nHydrogen, Stellar, Dyson, Biosphere and Matrix presets share a resizable canvas. Colours, cells and traffic pulses respond to actual observed data. Original Tk/Pillow/Pygame presentation variants and all source files remain in legacy/. They are preserved, not falsely described as new independent computation engines.\n\nBUS COVERAGE\n\nFluxBus: exact input → existing TCP hub → existing pipeline → read-only completed-result reader → shared bus. A TCP ACK proves hub storage, not pipeline completion.\n\nObservatory: authenticated subscription → shared bus; return messages → authenticated runtime API, with explicit multipart framing for larger data. Runtime acceptance is separate from module execution.\n\nPython: cooperative adapter and launch wrapper. Java: Java 11+ adapter included. Already-running programs cannot expose their internal state without an integration point. Process detection alone is never counted as a two-way data connection.\n\nThe app catalog skips runtime/data/dependency/backup folders and scans at most 12,000 files. Nothing is auto-launched simply because it was discovered. Closing this studio stops its bus and adapters; independently launched apps retain their own lifecycle.')
        self.button(tab, 'Run preserved console pipeline', lambda: self.enqueue('legacy-pipeline')).pack(anchor='w', padx=12, pady=(0, 12))

    def generate(self):
        try:
            count = int(self.size.get())
            if not 1 <= count <= 16384:
                raise ValueError('Use 1–16384 bytes')
            self.rt.mode = self.mode.get()
            self.rt.size = count
            self.rt.seed = self.seed.get()
            self.enqueue('generate')
        except ValueError as e:
            messagebox.showerror('Generator', str(e))

    def toggle_generator(self):
        if self.running.get():
            self.generate()
        self.rt.generator = self.running.get()

    def import_bytes(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        try:
            if Path(path).stat().st_size > 16384:
                raise ValueError('Import up to 16 KiB per packet')
            value = packet(Path(path).read_bytes(), mode='file bytes')
            self.rt.latest = value
            self.rt.emit('signal.file', value)
            self.set_signal(value)
        except Exception as e:
            messagebox.showerror('Import', str(e))

    def export(self):
        value = self.rt.latest
        if not value:
            return messagebox.showinfo('Export', 'Generate or process a signal first.')
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Packet JSON', '*.json')])
        if not path:
            return
        try:
            if decode(value) != value['bits']:
                raise ValueError('Round-trip verification failed')
            Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
            Path(path).with_suffix('.bin').write_bytes(base64.b64decode(value['base64']))
            self.write(self.analysis, f"Saved packet and binary bytes.\nSHA-256 {value['sha256']}\nExact bit length {value['bit_length']}; padding {value['padding_bits']}.")
        except Exception as e:
            messagebox.showerror('Export', str(e))

    def invert(self):
        if not self.rt.latest:
            return
        original = self.rt.latest
        value = from_bits(''.join(('0' if b == '1' else '1' for b in original['bits'])))
        value['transform'] = dict(operation='NOT', parent_sha256=original['sha256'])
        self.rt.latest = value
        self.rt.emit('signal.transformed', value)
        self.set_signal(value)

    def set_signal(self, value):
        self.previous = self.bits
        self.bits = value['bits'][:4096]
        self.signal_total = value['bit_length']
        self.metrics.configure(text=f"{value['mode']}  ·  {value['bit_length']:,} bits  ·  {value['ones']:,} ones  ·  {value['transitions']:,} transitions  ·  balance entropy {value['bit_balance_entropy']:.3f}")
        view = {k: v for k, v in value.items() if k not in ('bits', 'base64', 'hex')}
        self.write(self.output, json.dumps(view, indent=2, ensure_ascii=False) + '\n\nBIT PREVIEW (up to 4096)\n' + self.bits)

    def show_catalog(self):
        self.tree.delete(*self.tree.get_children())
        term = self.filter.get().lower()
        for index, item in enumerate(self.rt.catalog['items']):
            if term and term not in (item['app'] + ' ' + item['name']).lower():
                continue
            self.tree.insert('', 'end', iid=str(index), values=(item['app'], item['kind'] + (' · invalid' if item['error'] else ''), item['name']))
        self.catalog_label.configure(text=f"{len(self.rt.catalog['items'])} entry points · {self.rt.catalog['visited']} files inspected · " + ('scan limit reached' if self.rt.catalog['truncated'] else 'scan complete') + ' · adapters and launch logs under data/')

    def launch(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.rt.catalog['items'][int(selection[0])]

        def run():
            try:
                self.rt.launch(item)
            except Exception as e:
                self.rt.notify('error', str(e))
        threading.Thread(target=run, daemon=True).start()

    def launch_external(self, which):
        root = Path(self.rt.config['apps_root'])
        path = root / ('FluxBus-v2/FluxBus-v2.exe' if which == 'flux' else 'Postscarcity Observatory v4/graphical_app/app.py')
        item = dict(path=str(path), kind='Application' if which == 'flux' else 'Python', error='')
        if not path.exists():
            return messagebox.showerror('Launch', 'Application not found: ' + str(path))
        if which == 'obs':

            def launch_obs():
                try:
                    launcher = root / 'Postscarcity Observatory v4/Launch Observatory.vbs'
                    if not launcher.exists():
                        raise FileNotFoundError(str(launcher))
                    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    child = subprocess.Popen(['wscript.exe', str(launcher)], cwd=launcher.parent, creationflags=flags)
                    self.rt.notify('analysis', f'Opened the installed Observatory launcher, PID {child.pid}. Its native connection is tracked above; startup errors remain in its own launcher logs.')
                except Exception as e:
                    self.rt.notify('error', str(e))
            threading.Thread(target=launch_obs, daemon=True).start()
        else:
            threading.Thread(target=lambda: self.launch_item(item), daemon=True).start()

    def launch_item(self, item):
        try:
            self.rt.launch(item)
        except Exception as e:
            self.rt.notify('error', str(e))

    def event_detail(self, event=None):
        selection = self.events.selection()
        if selection:
            selected = next((r for r in self.log_rows if str(r['seq']) == selection[0]), None)
            if selected:
                full = self.rt.ledger.find(selected['id'])
                self.write(self.detail, json.dumps(full or {'status': 'Expired from rolling history', 'summary': selected}, ensure_ascii=False, indent=2))

    def export_events(self):
        path = filedialog.asksaveasfilename(defaultextension='.jsonl')
        if path:
            with Path(path).open('w', encoding='utf-8') as handle:
                for row in self.log_rows:
                    handle.write(encoded(self.rt.ledger.find(row['id']) or row).decode() + '\n')

    def tick(self):
        if self.rt.stop.is_set():
            return
        try:
            for _ in range(30):
                try:
                    kind, data = self.rt.ui_events.get_nowait()
                except queue.Empty:
                    break
                if kind == 'result':
                    if data.get('signal'):
                        self.set_signal(data['signal'])
                    summary = {k: v for k, v in data['result'].items() if k not in ('binary', 'ternary', 'quantum_sample')}
                    self.write(self.analysis, encoded(summary).decode())
                elif kind == 'signal':
                    self.set_signal(data)
                elif kind in ('analysis', 'error'):
                    self.write(self.analysis, data)
                elif kind == 'catalog':
                    self.show_catalog()
                elif kind == 'processes':
                    self.process_label.configure(text='Detected runtimes (not connection proof): ' + ', '.join((f"{x['name']} [{x['pid']}]" for x in data[:16])))
            if time.monotonic() >= self.next_ledger_poll:
                self.next_ledger_poll = time.monotonic() + 1
                records = self.rt.ledger.read(self.events_cursor, 40)
                for event in records:
                    self.events_cursor = event['seq']
                    self.log_rows.append({k: v for k, v in event.items() if k != 'data'})
                    self.events.insert('', 'end', iid=str(event['seq']), values=(event['seq'], event['source'], event['topic'], event['target']))
                    if len(self.events.get_children()) > 300:
                        self.events.delete(self.events.get_children()[0])
                    self.pulses.append((time.monotonic(), event['source']))
                    if event['topic'].startswith('signal.') and isinstance(event['data'], dict) and ('bits' in event['data']):
                        self.previous = self.bits
                        self.bits = event['data']['bits'][:4096]
                        self.signal_total = event['data'].get('bit_length', len(event['data']['bits']))
                stats = self.rt.ledger.stats()
                storage = stats['storage']
                self.state_label.configure(text=f"{stats['retained']:,} retained  /  {storage['disk_bytes'] / 1048576:.1f} MB · {storage['database_limit_bytes'] / 1048576:.0f} MB DB cap")
                self.matrix_bus.configure(text=f'HTTP + UDP :{self.rt.server.port}  →  UDP :{self.rt.server.udp.broadcast_port} · {len(self.rt.processes)} runtimes')
                for label, bridge in zip(self.bridge_labels, self.rt.bridges):
                    label.configure(text=('Paused' if not bridge.enabled else bridge.status) + f'   |   → {bridge.sent}   ← {bridge.received}   |   retries/errors {bridge.failures}')
            visible = self.notebook.index('current') == 0
            if not self.hold and visible:
                self.draw()
        except Exception as e:
            self.footer.configure(text='UI: ' + str(e))
        self.frame += 1
        visible = self.notebook.index('current') == 0
        target = 40 if self.quality.get() == 'High' else 60 if self.quality.get() == 'Balanced' else 125
        delay = max(target, int(self.render_ms * 0.6)) if visible and (not self.hold) else 250
        self.root.after(delay, self.tick)

    def draw(self):
        if self.renderer is None:
            return self._draw_legacy()
        started = time.perf_counter()
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        if w < 100 or h < 100:
            return
        self.renderer.simulated = self.visual_pulses.get()
        image = self.renderer.render(w, h, self.preset.get(), self.bits, self.previous, list(self.pulses), self.pointer, self.quality.get())
        if self.photo is None or self.photo.width() != w or self.photo.height() != h:
            self.photo = ImageTk.PhotoImage(image)
            self.canvas.delete('all')
            self.canvas_image = self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        else:
            self.photo.paste(image)
        self.render_ms = (time.perf_counter() - started) * 1000

    def _draw_legacy(self):
        c = self.canvas
        w = max(1, c.winfo_width())
        h = max(1, c.winfo_height())
        now = time.monotonic()
        preset = self.preset.get()
        cw = max(12, min(25, w / 48))
        cols = max(1, int((w - 40) / cw))
        rows = max(1, int((h - 90) / cw))
        visible = min(cols * rows, 4096)
        bits = self.bits or '0' * visible
        changed = self.previous
        cx = w * 0.5
        cy = h * 0.51
        radius = min(w, h) * 0.23
        activity = self.rt.engine.activity.snapshot()
        cpu = activity.cpu_percent or 0
        cache_key = (w, h, preset, bits, changed)
        if getattr(self, '_matrix_cache', None) != cache_key:
            c.delete('all')
            self._matrix_cache = cache_key
            for index in range(visible):
                x = 24 + index % cols * cw
                y = 58 + index // cols * cw
                bit = bits[index] if index < len(bits) else '0'
                delta = index < len(changed) and index < len(bits) and (bit != changed[index])
                distance = math.hypot(x - cx, y - cy)
                wave = math.sin(distance * 0.026 - now * 1.2)
                color = GOLD if delta else CYAN if bit == '1' else '#163245'
                if preset == 'Matrix':
                    c.create_rectangle(x, y, x + cw - 5, y + cw - 5, fill=color, outline='')
                    if cw >= 20 and bit == '1':
                        c.create_text(x + (cw - 5) / 2, y + (cw - 5) / 2, text=bit, fill='#092b29', font=('Consolas', 8))
                else:
                    r = 1.1 + (1.8 if bit == '1' else 0.1)
                    offset = wave * (3 + cpu * 0.03)
                    c.create_oval(x + offset - r, y - r, x + offset + r, y + r, fill=color, outline='')
        c.delete('dynamic')
        if preset != 'Matrix':
            if preset == 'Dyson':
                for i in range(80):
                    angle = i * math.tau / 80 + now * 0.15
                    x = cx + math.cos(angle) * radius
                    y = cy + math.sin(angle) * radius * 0.47
                    c.create_rectangle(x - 2, y - 2, x + 2, y + 2, fill=GOLD, outline='', tags='dynamic')
                c.create_oval(cx - 24, cy - 24, cx + 24, cy + 24, fill=GOLD, outline=TEXT, tags='dynamic')
                ex = cx + radius * 1.7
                c.create_line(cx, cy, ex, cy, fill=CYAN, width=2, tags='dynamic')
                c.create_oval(ex - 14, cy - 14, ex + 14, cy + 14, fill=BLUE, outline=CYAN, tags='dynamic')
            elif preset == 'Biosphere':
                c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill='#0a2437', outline=CYAN, width=2, tags='dynamic')
                for latitude in (-0.75, -0.4, 0, 0.4, 0.75):
                    half = radius * math.sqrt(1 - latitude ** 2)
                    y = cy + latitude * radius
                    c.create_oval(cx - half, y - 10, cx + half, y + 10, outline='#286973', tags='dynamic')
                for i in range(50):
                    angle = i * 2.39996 + now * 0.03
                    rr = radius * math.sqrt(i / 50)
                    x = cx + math.cos(angle) * rr
                    y = cy + math.sin(angle) * rr
                    c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=CYAN if bits[i % len(bits)] == '1' else BLUE, outline='', tags='dynamic')
            else:
                for ring in range(3):
                    rr = radius * (0.65 + ring * 0.25)
                    c.create_oval(cx - rr, cy - rr * 0.55, cx + rr, cy + rr * 0.55, outline=GOLD if preset == 'Stellar' else '#285474', width=1, tags='dynamic')
                c.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, fill=GOLD if preset == 'Stellar' else CYAN, outline=TEXT, tags='dynamic')
                for i in range(55):
                    angle = i * 2.39996 + now * (0.15 + i % 3 * 0.04)
                    rr = radius * (0.65 + i % 3 * 0.25)
                    x = cx + math.cos(angle) * rr
                    y = cy + math.sin(angle) * rr * 0.55
                    c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=TEXT if bits[i % len(bits)] == '1' else BLUE, outline='', tags='dynamic')
        for stamp, source in self.pulses:
            age = now - stamp
            if age > 2:
                continue
            r = 12 + age * min(w, h) * 0.18
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline='#215960' if source == 'hydrogen' else '#654d37', tags='dynamic')
        c.create_rectangle(0, 0, w, 42, fill='#081622', outline='', tags='dynamic')
        c.create_text(18, 21, text=f'{preset.upper()}  /  {min(len(self.bits), visible):,} visible bits of {self.signal_total:,}  /  CPU {cpu:.1f}%', fill=MUTED, anchor='w', font=('Consolas', 10), tags='dynamic')
        if self.pointer and preset == 'Matrix':
            px, py = self.pointer
            col = int((px - 24) // cw)
            row = int((py - 58) // cw)
            idx = row * cols + col
            if 0 <= col < cols and 0 <= row < rows and (idx < len(self.bits)):
                c.create_text(w - 18, 21, text=f'bit [{idx}] = {self.bits[idx]}', anchor='e', fill=GOLD, font=('Consolas', 11, 'bold'), tags='dynamic')

    def close(self):
        self.rt.close()
        self.root.destroy()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data')
    parser.add_argument('--port', type=int, default=8794)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    root = tk.Tk()
    try:
        runtime = Runtime(args.data, args.port)
    except OSError as e:
        messagebox.showerror('Hydrogen Mesh', f'Cannot start the local bus: {e}\nUse another --port or close the existing studio.')
        root.destroy()
        return 1
    app = App(root, runtime)
    if args.smoke:
        app.enqueue('text', 'Hydrogen smoke test ✓')
        app.generate()

        def finish():
            report = dict(width=root.winfo_width(), height=root.winfo_height(), tabs=len(app.notebook.tabs()), messages=runtime.ledger.stats(), errors=list(runtime.errors), canvas=[app.canvas.winfo_width(), app.canvas.winfo_height()])
            (runtime.data / 'smoke.json').write_text(json.dumps(report, indent=2))
            app.close()
        root.after(3500, finish)
    root.mainloop()
    return 0
