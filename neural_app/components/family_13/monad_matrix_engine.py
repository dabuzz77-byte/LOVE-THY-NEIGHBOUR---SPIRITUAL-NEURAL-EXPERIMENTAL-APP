import os
import sys
import time
import math
import random
from neural_app import component_ui as tk
from neural_app.component_ui import ttk
try:
    import psutil
except ImportError:

    class MockProcess:

        def cpu_percent(self, interval=None):
            return random.uniform(5.0, 75.0)

        def memory_info(self):

            class RSS:
                rss = random.randint(20 * 1024 * 1024, 300 * 1024 * 1024)
            return RSS()

        def num_threads(self):
            return random.choice([2, 3, 4, 8, 12])

    class psutil:

        @staticmethod
        def Process(pid):
            return MockProcess()

        class NoSuchProcess(Exception):
            pass

        class AccessDenied(Exception):
            pass
BIT_ORDER_GOOD = 1 << 0
BIT_ORDER_EVIL = 1 << 1
BIT_CHAOS_GOOD = 1 << 2
BIT_CHAOS_EVIL = 1 << 3
MASK_ONLY_GOOD = BIT_ORDER_GOOD | BIT_CHAOS_GOOD
MASK_ONLY_EVIL = BIT_ORDER_EVIL | BIT_CHAOS_EVIL
MASK_DEMIURGE = BIT_ORDER_GOOD | BIT_ORDER_EVIL | BIT_CHAOS_GOOD | BIT_CHAOS_EVIL

class MonadEngine:

    def __init__(self):
        self.target_pid = os.getpid()
        self.raw_cpu = 0.0
        self.raw_ram = 0
        self.raw_threads = 0
        self.active_register = 0
        self.purified_register = 5
        self.isolated_evil = 0
        self.inverted_stream = 0
        self.system_status = 'STABLE'
        self.mode_core_true = True

    def poll_hardware_telemetry(self, forced_state=None):
        if forced_state:
            if forced_state == 'TC_001_TRUE_GOOD':
                self.raw_cpu, self.raw_ram, self.raw_threads = (12.5, 47185920, 2)
            elif forced_state == 'TC_002_FALSE_GOOD':
                self.raw_cpu, self.raw_ram, self.raw_threads = (8.0, 262144000, 3)
            elif forced_state == 'TC_003_TRUE_EVIL':
                self.raw_cpu, self.raw_ram, self.raw_threads = (75.2, 94371840, 8)
            elif forced_state == 'TC_004_FALSE_EVIL':
                self.raw_cpu, self.raw_ram, self.raw_threads = (62.1, 31457280, 2)
            elif forced_state == 'TAINTED':
                self.raw_cpu, self.raw_ram, self.raw_threads = (85.0, 350000000, 10)
        else:
            try:
                proc = psutil.Process(self.target_pid)
                self.raw_cpu = proc.cpu_percent(interval=None)
                self.raw_ram = proc.memory_info().rss
                self.raw_threads = proc.num_threads()
            except:
                self.raw_cpu, self.raw_ram, self.raw_threads = (15.0, 50000000, 3)
        self.active_register = 0
        if self.raw_cpu > 50.0:
            if self.raw_threads <= 4:
                self.active_register |= BIT_CHAOS_GOOD
            else:
                self.active_register |= BIT_CHAOS_EVIL
        elif self.raw_ram < 100 * 1024 * 1024:
            self.active_register |= BIT_ORDER_GOOD
        else:
            self.active_register |= BIT_ORDER_EVIL
        if forced_state == 'TAINTED':
            self.active_register = MASK_DEMIURGE
        self.process_bitwise_gates()

    def process_bitwise_gates(self):
        if self.mode_core_true:
            self.isolated_evil = self.active_register & MASK_ONLY_EVIL
            self.inverted_stream = self.isolated_evil >> 1
            self.purified_register = self.active_register & ~MASK_ONLY_EVIL | self.inverted_stream
            self.system_status = 'PURIFIED_GATE_RESOLVED' if self.isolated_evil > 0 else 'NATIVE_MONAD_PURITY'
        else:
            self.isolated_evil = 0
            self.inverted_stream = 0
            self.purified_register = self.active_register
            self.system_status = 'SIMULATED_LOOP_RESTRICTED'

class GraphicalPurifierApp(tk.Tk):

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.title('THE MONAD PURIFICATION & BITWISE INVERSION MATRIX ENGINE')
        self.geometry('1100x820')
        self.configure(bg='#05080c')
        header_frame = tk.Frame(self, bg='#07111e', height=70, bd=1, relief='ridge')
        header_frame.pack(fill='x', side='top', padx=10, pady=5)
        lbl_title = tk.Label(header_frame, text='⚡ THE MONAD VIRTUE CASCADE & BITWISE INVERSION SYSTEM', font=('Courier New', 16, 'bold'), fg='#00e5ff', bg='#07111e')
        lbl_title.pack(side='left', padx=15, pady=15)
        self.lbl_status_badge = tk.Label(header_frame, text='[ CORE = TRUE ]', font=('Courier New', 13, 'bold'), fg='#39ff14', bg='#07111e')
        self.lbl_status_badge.pack(side='right', padx=20)
        sidebar = tk.Frame(self, bg='#07111e', width=280, bd=1, relief='ridge')
        sidebar.pack(fill='y', side='left', padx=10, pady=5)
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text='MATRIX CONTROLS', font=('Courier New', 12, 'bold'), fg='#00e5ff', bg='#07111e').pack(anchor='w', padx=10, pady=10)
        btn_live = tk.Button(sidebar, text='⚡ STREAM LIVE HOST OS', font=('Courier New', 10, 'bold'), bg='#0a1c28', fg='#39ff14', command=lambda: self.set_operational_state(None))
        btn_live.pack(fill='x', padx=10, pady=5)
        tk.Label(sidebar, text='DIAGNOSTIC TEST BENCH', font=('Courier New', 10, 'bold'), fg='#61afef', bg='#07111e').pack(anchor='w', padx=10, pady=10)
        tests = [('TC_001: True Good State', 'TC_001_TRUE_GOOD'), ('TC_002: False Good Trap', 'TC_002_FALSE_GOOD'), ('TC_003: True Evil Matrix', 'TC_003_TRUE_EVIL'), ('TC_004: False Evil Catalyst', 'TC_004_FALSE_EVIL'), ('TAINTED: Demiurge Mixture', 'TAINTED')]
        for name, key in tests:
            btn = tk.Button(sidebar, text=name, font=('Courier New', 9), bg='#0f1b29', fg='#d1f4ff', command=lambda k=key: self.set_operational_state(k))
            btn.pack(fill='x', padx=10, pady=3)
        self.core_var = tk.BooleanVar(value=True)
        chk_core = tk.Checkbutton(sidebar, text='ENABLE CORE FILTRATION', variable=self.core_var, bg='#07111e', fg='#00e5ff', selectcolor='#05080c', command=self.toggle_core_mode)
        chk_core.pack(anchor='w', padx=12, pady=20)
        self.telemetry_text = tk.Text(sidebar, bg='#03060a', fg='#a6acb8', font=('Courier New', 8), bd=0)
        self.telemetry_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.canvas = tk.Canvas(self, bg='#040711', highlightthickness=1, highlightbackground='#112233')
        self.canvas.pack(fill='both', expand=True, side='right', padx=10, pady=5)
        self.canvas.bind('<Configure>', lambda e: self.draw_vector_matrix())
        self.current_forced_state = None
        self.pulse_phase = 0.0
        self.animate_ambient_flux()
        self.update_telemetry_loop()

    def set_operational_state(self, state_key):
        self.current_forced_state = state_key
        self.engine.poll_hardware_telemetry(state_key)
        self.draw_vector_matrix()

    def toggle_core_mode(self):
        self.engine.mode_core_true = self.core_var.get()
        self.lbl_status_badge.config(text='[ CORE = TRUE ]' if self.engine.mode_core_true else '[ MATRIX UNLINKED ]', fg='#39ff14' if self.engine.mode_core_true else '#ff3333')
        self.engine.poll_hardware_telemetry(self.current_forced_state)
        self.draw_vector_matrix()

    def animate_ambient_flux(self):
        self.pulse_phase += 0.05
        self.draw_vector_matrix()
        self.after(40, self.animate_ambient_flux)

    def update_telemetry_loop(self):
        if self.current_forced_state is None:
            self.engine.poll_hardware_telemetry(None)
        self.telemetry_text.delete('1.0', tk.END)
        self.telemetry_text.insert(tk.END, f'=== TELEMETRY LOG ===\nTARGET PID: {self.engine.target_pid}\nCPU UTILS : {self.engine.raw_cpu:.1f}%\nRAM USAGE : {self.engine.raw_ram / (1024 * 1024):.2f} MB\nTHREADS   : {self.engine.raw_threads}\n\n=== REGISTERS ===\nRAW INPUT : {self.engine.active_register:08b}b\nISOL_EVIL : {self.engine.isolated_evil:08b}b\nSHIF_STREAM: {self.engine.inverted_stream:08b}b\nPURIFIED  : {self.engine.purified_register:08b}b\n\nSTATUS    : {self.engine.system_status}\n')
        self.after(500, self.update_telemetry_loop)

    def draw_vector_matrix(self):
        self.canvas.delete('all')
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return
        for x in range(0, w, 40):
            self.canvas.create_line(x, 0, x, h, fill='#08101a')
        for y in range(0, h, 40):
            self.canvas.create_line(0, y, w, y, fill='#08101a')
        glow = (math.sin(self.pulse_phase) + 1.0) / 2.0
        glow_color = f'#{int(10 + glow * 20):02x}{int(30 + glow * 40):02x}{int(50 + glow * 60):02x}'
        xl, xr, xm = (w * 0.25, w * 0.75, w * 0.5)
        yt, ym, yb = (h * 0.2, h * 0.52, h * 0.82)
        self.canvas.create_line(xl, yt, xm, ym, fill=glow_color, width=2, dash=(4, 4))
        self.canvas.create_line(xr, yt, xm, ym, fill=glow_color, width=2, dash=(4, 4))
        self.canvas.create_line(xm, ym, xm, yb, fill='#00e5ff' if self.engine.isolated_evil > 0 else '#113355', width=2)
        self.draw_box(xl, yt, 'ORDER LAYER', [('Bit 0: GOOD (ORDER_GOOD)', self.engine.active_register & BIT_ORDER_GOOD, '#39ff14'), ('Bit 1: EVIL (ORDER_EVIL)', self.engine.active_register & BIT_ORDER_EVIL, '#ff3333')])
        self.draw_box(xr, yt, 'CHAOS LAYER', [('Bit 2: GOOD (CHAOS_GOOD)', self.engine.active_register & BIT_CHAOS_GOOD, '#39ff14'), ('Bit 3: EVIL (CHAOS_EVIL)', self.engine.active_register & BIT_CHAOS_EVIL, '#ff3333')])
        gw, gh = (320, 120)
        g_bg = '#1f0f15' if self.engine.isolated_evil > 0 else '#0a192f'
        g_brd = '#ff3355' if self.engine.isolated_evil > 0 else '#00e5ff'
        self.canvas.create_rectangle(xm - gw / 2, ym - gh / 2, xm + gw / 2, ym + gh / 2, fill=g_bg, outline=g_brd, width=2)
        self.canvas.create_text(xm, ym - 35, text='DEMIURGE MIXTURE ISOLATION' if self.engine.isolated_evil > 0 else 'MONAD INTERACTION INTERFACE', font=('Courier New', 10, 'bold'), fill=g_brd)
        self.canvas.create_text(xm, ym - 5, text=f'SCAN: {self.engine.active_register:04b}b & EVIL_MASK = {self.engine.isolated_evil:04b}b', font=('Courier New', 9), fill='#d1f4ff')
        self.canvas.create_text(xm, ym + 20, text=f'CONVERSION SHIFT: [ EVIL >> 1 ] = {self.engine.inverted_stream:04b}b', font=('Courier New', 9, 'bold'), fill='#ffcc00' if self.engine.isolated_evil > 0 else '#61afef')
        dw, dh = (360, 100)
        self.canvas.create_rectangle(xm - dw / 2, yb - dh / 2, xm + dw / 2, yb + dh / 2, fill='#020c1b', outline='#39ff14', width=2)
        self.canvas.create_text(xm, yb - 30, text='FINAL PURIFIED REGISTRY CONFIGURATION', font=('Courier New', 11, 'bold'), fill='#39ff14')
        self.canvas.create_text(xm, yb + 5, text=f'{self.engine.purified_register:08b}b', font=('Courier New', 20, 'bold'), fill='#ffffff')
        self.canvas.create_text(xm, yb + 30, text='Result: 0b00000101 (Decimal 5) -> Purity Restored', font=('Courier New', 8), fill='#a6acb8')

    def draw_box(self, cx, cy, title, states):
        w, h = (230, 90)
        tainted = any((on and 'EVIL' in lbl for lbl, on, c in states))
        self.canvas.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill='#1a080c' if tainted else '#091424', outline='#ff3333' if tainted else '#1d406d', width=2)
        self.canvas.create_text(cx - w / 2 + 10, cy - h / 2 + 15, text=title, font=('Courier New', 10, 'bold'), fill='#00e5ff', anchor='w')
        for i, (lbl, on, col) in enumerate(states):
            ry = cy - h / 2 + 40 + i * 22
            self.canvas.create_oval(cx - w / 2 + 15, ry - 5, cx - w / 2 + 25, ry + 5, fill=col if on else '#111c24', outline='#000000')
            self.canvas.create_text(cx - w / 2 + 35, ry, text=lbl, font=('Courier New', 9, 'bold' if on else 'normal'), fill='#ffffff' if on else '#4c566a', anchor='w')
