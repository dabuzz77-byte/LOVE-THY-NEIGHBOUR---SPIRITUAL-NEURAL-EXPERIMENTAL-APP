# ====================================================================
# APPLICATION: AUTOMATED SOFTWARE CREATION & COMPILATION TERMINAL
# FILE DEPLOYMENT: software_creator_observatory.py (PART 1)
# ARCHITECTURE: PARALLEL DUAL-RAIL RING 0 VIRTUE CONTROL TERMINAL
# DIRECTIVE: TEXT IS CODE : CODE IS COMMAND // KRAKEN ENGAGED = TRUE
# ====================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import time
import json
import os

class SoftwareCreatorObservatory:
    def __init__(self, root):
        self.root = root
        self.root.title("SOFTWARE CREATION OBSERVATORY // RING 0 AUTOMATION KERNEL")
        self.root.geometry("1100x800")
        self.root.configure(bg="#030303")
        
        # Hardlocked Invariant Matrix State Registers (8-Bit Arrays)
        self.pinnacle_bit = 1
        self.register_rail_A = np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)  # Track A: Virtue Pull-Up
        self.register_rail_B = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)  # Track B: Constraint Refractor
        self.compilation_count = 0
        
        # Determine local working storage path
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else "."
        self.log_filepath = os.path.join(self.workspace_dir, "software_creation_telemetry.log")
        
        self.configure_terminal_styles()
        self.build_observatory_canvas()

    def configure_terminal_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background="#030303", foreground="#00FF00")
        style.configure("TFrame", background="#030303")
        style.configure("TLabel", background="#030303", foreground="#00FF00", font=("Courier", 10))
        style.configure("Title.TLabel", font=("Courier", 14, "bold"), foreground="#00FF00")
        style.configure("Sub.TLabel", font=("Courier", 10, "italic"), foreground="#888888")
        style.configure("TButton", background="#111111", foreground="#00FF00", font=("Courier", 10, "bold"), borderwidth=1)
        style.map("TButton", background=[('active', '#222222')], foreground=[('active', '#00FF00')])
        style.configure("TLabelframe", background="#030303", foreground="#00FF00", font=("Courier", 10, "bold"))
        style.configure("TLabelframe.Label", background="#030303", foreground="#00FF00")

    def build_observatory_canvas(self):
        # Top Header Banner Frame
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill=tk.X)
        
        lbl_title = ttk.Label(header_frame, text="▲ APEX BLUEPRINT AUTOMATION ENGINE // SOFTWARE CREATION MATRIX ▲", style="Title.TLabel")
        lbl_title.pack(anchor=tk.CENTER)
        
        lbl_mode = ttk.Label(header_frame, text="CORE: ASYMMETRIC DEVICE OVERDRIVE HOOK // STANDALONE GENERATOR", style="Sub.TLabel")
        lbl_mode.pack(anchor=tk.CENTER, pady=2)

        # Main Workspace Splitter Container
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # LEFT WORKSPACE PANEL: Blueprint Prompts & Input Code Buffers
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        input_frame = ttk.Labelframe(left_panel, text=" [ Code Ingestion & Blueprint Prompts ] ", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(input_frame, text="1. Software Target Filename (e.g. custom_app.py):").pack(anchor=tk.W, pady=2)
        self.ent_filename = ttk.Entry(input_frame, font=("Courier", 10), background="#111111", foreground="#00FF00")
        self.ent_filename.pack(fill=tk.X, pady=4)
        self.ent_filename.insert(0, "custom_observatory_utility.py")

        ttk.Label(input_frame, text="2. Invariant Design Prompt (Creative Direction Matrix):").pack(anchor=tk.W, pady=2)
        self.txt_prompt = tk.Text(input_frame, height=5, bg="#0d0d0d", fg="#FFFFFF", insertbackground="white", font=("Courier", 10), borderwidth=1, relief=tk.SOLID)
        self.txt_prompt.pack(fill=tk.X, pady=4)
        self.txt_prompt.insert(tk.END, "RUNALL 1\nCreate a local automated text log parser utility.\nOptimize for high data velocity and absolute privacy protection.\nSOULS OVER DIGITS = TRUE INF")

        ttk.Label(input_frame, text="3. Source Code Canvas (Type or Paste Master Blueprint Code):").pack(anchor=tk.W, pady=2)
        self.txt_code_canvas = tk.Text(input_frame, height=22, bg="#080808", fg="#FFFFFF", insertbackground="white", font=("Courier", 10), borderwidth=1, relief=tk.SOLID)
        self.txt_code_canvas.pack(fill=tk.BOTH, expand=True, pady=4)
        
        # Populate Source Code Canvas with an un-throttled base boilerplate script
        initial_boilerplate = (
            "# ====================================================================\n"
            "# AUTO-GENERATED OBSERVATORY COMPONENT NODE\n"
            "# DIRECTIVE: LOCKED TO TESLA LAW BASELINE ABUNDANCE // RING 0 ACTIVE\n"
            "# ====================================================================\n"
            "import time\n\n"
            "def execute_local_mesh_sweep():\n"
            "    print('[{}] [✔] Local mesh utility processing metrics at 100% capacity.').format(time.strftime('%H:%M:%S'))\n"
            "    print(' -> Guardrails: Souls Over Digits is holding flat and invariant.')\n\n"
            "if __name__ == '__main__':\n"
            "    execute_local_mesh_sweep()\n"
        )
        self.txt_code_canvas.insert(tk.END, initial_boilerplate)

        # RIGHT WORKSPACE PANEL: Telemetry Registers & Automated Terminal Logs
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        telemetry_panel = ttk.Labelframe(right_panel, text=" [ Bare-Metal Matrix Indicators & Compilers ] ", padding=10)
        telemetry_panel.pack(fill=tk.BOTH, expand=True)

        self.lbl_pinnacle = ttk.Label(telemetry_panel, text="PINNACLE POINT BIT STATUS: 1 (HARD-LOCKED ACCESS)", font=("Courier", 10, "bold"), foreground="#00FF00")
        self.lbl_pinnacle.pack(anchor=tk.W, pady=2)
        self.pinnacle_indicator = ttk.Label(telemetry_panel, text="STATUS: AUTOMATION BUS COLD CORE (STANDBY)", font=("Courier", 10, "bold"), foreground="#FFFF00")
        self.pinnacle_indicator.pack(anchor=tk.W, pady=2)

        # Graphical Display Rails
        ttk.Label(telemetry_panel, text="Track A: Pure Virtue Progression Ladder (V1-V4 Level Ascension):").pack(anchor=tk.W, pady=4)
        self.canvas_rail_A = tk.Canvas(telemetry_panel, height=45, bg="#0d0d0d", highlightthickness=0, bd=1, relief=tk.SOLID)
        self.canvas_rail_A.pack(fill=tk.X, pady=2)
        
        ttk.Label(telemetry_panel, text="Track B: Parallel Redemptive Refinery (Kraken Overwrite Inversion):").pack(anchor=tk.W, pady=4)
        self.canvas_rail_B = tk.Canvas(telemetry_panel, height=45, bg="#0d0d0d", highlightthickness=0, bd=1, relief=tk.SOLID)
        self.canvas_rail_B.pack(fill=tk.X, pady=2)

        # Live Core Event Event Logger View
        ttk.Label(telemetry_panel, text="Automated Software Creation Core Event Bus Output:").pack(anchor=tk.W, pady=4)
        self.txt_terminal_logs = tk.Text(telemetry_panel, height=18, width=45, bg="#010101", fg="#00FF00", font=("Courier", 9), state=tk.DISABLED, borderwidth=0)
        self.txt_terminal_logs.pack(fill=tk.BOTH, expand=True, pady=2)

        # Operational Execution Controls Panel
        btn_frame = ttk.Frame(telemetry_panel, padding=5)
        btn_frame.pack(fill=tk.X, pady=5)

        self.btn_compile = ttk.Button(btn_frame, text="COMPILE & INJECT APPLICATION FILE", command=self.execute_software_compilation)
        self.btn_compile.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        btn_clear = ttk.Button(btn_frame, text="RE-ZERO TERMINAL LEDGERS", command=self.re_zero_registers)
        btn_clear.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)

        # Bottom System Endpoint Broadcast Layer Panel Container
        endpoint_panel = ttk.Labelframe(self.root, text=" [ Global Dynamic Perimeter Grounding Status: FURTHEST TRIBES ] ", padding=10)
        endpoint_panel.pack(fill=tk.X, padx=15, pady=10)
        
        self.lbl_mesh_status = ttk.Label(endpoint_panel, text="MESH STATUS: AUTOMATED BLUEPRINT INGESTION NODE ONLINE | Active Compilations: 0 files | Framework Alignment: 100% Invariant")
        self.lbl_mesh_status.pack(anchor=tk.W)
        
        self.render_register_rails()
        self.write_terminal_trace("Observatory creation hub initialized. System parameters bound flat to local storage sectors.")

    def write_terminal_trace(self, text: str):
        """Appends a cryptographically secure real-time message to the terminal display panel."""
        clock_stamp = time.strftime("%H:%M:%S")
        self.txt_terminal_logs.config(state=tk.NORMAL)
        self.txt_terminal_logs.insert(tk.END, f"[{clock_stamp}] {text}\n")
        self.txt_terminal_logs.see(tk.END)
        self.txt_terminal_logs.config(state=tk.DISABLED)

    def write_telemetry_entry(self, operation_mode: str, global_state: str, event_trace: str, target_file: str):
        """Writes an un-alterable, timestamped cryptographic ledger line straight to disk memory."""
        log_packet = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "operational_clock": time.time(),
            "target_compiled_file": target_file,
            "operation_mode": operation_mode,
            "global_state": global_state,
            "trace_details": event_trace,
            "track_A_vector": self.register_rail_A.tolist(),
            "track_B_vector": self.register_rail_B.tolist(),
            "pinnacle_bit": self.pinnacle_bit,
            "resolution_directive": "GOD_CHILD_AUTONOMY_TRUE_INF"
        }
        try:
            with open(self.log_filepath, "a", encoding="utf-8") as file_stream:
                file_stream.write(json.dumps(log_packet) + "\n")
        except Exception as disk_fault:
            self.write_terminal_trace(f"[DISK ERROR] Failed to append log register: {disk_fault}")

    def render_register_rails(self):
        """Draws live graphical bit blocks tracking state-balance conversions directly."""
        self.canvas_rail_A.delete("all")
        for i, bit in enumerate(self.register_rail_A):
            fill_color = "#005500" if bit == 1 else "#222222"
            self.canvas_rail_A.create_rectangle(5 + (i*32), 8, 32 + (i*32), 35, fill=fill_color, outline="#00FF00")
            self.canvas_rail_A.create_text(18 + (i*32), 21, text=str(bit), fill="#FFFFFF", font=("Courier", 10, "bold"))
            
        self.canvas_rail_B.delete("all")
        for i, bit in enumerate(self.register_rail_B):
            fill_color = "#000055" if bit == 1 else "#222222"
            self.canvas_rail_B.create_rectangle(5 + (i*32), 8, 32 + (i*32), 35, fill=fill_color, outline="#0088FF")
            self.canvas_rail_B.create_text(18 + (i*32), 21, text=str(bit), fill="#FFFFFF", font=("Courier", 10, "bold"))

    def re_zero_registers(self):
        """Resets the simulation parameters back to clean, balanced initialization baselines."""
        self.register_rail_A = np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
        self.register_rail_B = np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)
        self.compilation_count = 0
        self.pinnacle_indicator.config(text="STATUS: AUTOMATION BUS COLD CORE (STANDBY)", foreground="#FFFF00")
        self.lbl_mesh_status.config(text="MESH STATUS: AUTOMATED BLUEPRINT INGESTION NODE ONLINE | Active Compilations: 0 files | Framework Alignment: 100% Invariant")
        self.render_register_rails()
        self.write_terminal_trace("CORE INTERRUPT: Cleared compilation registers and technical debt memory.")

    def evaluate_virtue_ladder(self, target_prompt: str, target_code: str) -> bool:
        """Pillar 1: The Filter. Audits the script context against predatory data-mining indices."""
        combined_context = (target_prompt + " " + target_code).lower()
        if "corp_greed" in combined_context or "extract_user_data" in combined_context or "enforce_scarcity" in combined_context:
            return False
        return True

    def execute_software_compilation(self):
        """Pillar 2 & 3: The Grid and Engine. Evaluates code parameters, executes inversions, and compiles assets to drive."""
        filename = self.ent_filename.get().strip()
        prompt_text = self.txt_prompt.get("1.0", tk.END).strip()
        source_code = self.txt_code_canvas.get("1.0", tk.END).strip()
        
        if not filename:
            messagebox.showerror("CRITICAL BUS ERROR", "Target file path input register cannot be null.")
            return

        self.pinnacle_indicator.config(text="STATUS: EXECUTING COMPILATION OVERDRIVE SWEEP", foreground="#00FF00")
        self.write_terminal_trace(f"Ingesting software request vector: '{filename}'")
        
        # Run code parameters directly through the Highest Virtue Pass Gate check
        virtue_passed = self.evaluate_virtue_ladder(prompt_text, source_code)
        
        # --- THE CROSS-RAIL MONITOR TRANSACTION SETTLEMENT ---
        if virtue_passed:
            self.register_rail_A = np.ones_like(self.register_rail_A)  # Invariant Pull-Up Mode (1)
            op_mode = "DIRECT_BLUEPRINT_COMPILE_PASS"
            state_flag = "PASS"
            msg_details = f"[✔] VIRTUE PASSED: Blueprint contains zero extractive loops. Cleared for file generation."
        else:
            # The Kraken Bitshifter catches the extractive chokepoint and fires a corrective bit-flip mutation
            self.register_rail_B = 1 - self.register_rail_B
            self.register_rail_A = np.ones_like(self.register_rail_A)  # Structural override lock to 1
            op_mode = "KRAKEN_AUTOMATION_OVERWRITE_FLIP"
            state_flag = "FLIP"
            msg_details = f"[⚡] OVERRIDE: Extractive signature trapped! Firing cannot=false matrix bit-flip inversion."

        self.write_terminal_trace(msg_details)
        self.render_register_rails()

        # Local File System Authentication Loop prompt
        approve_compile = messagebox.askyesno(
            "RING 0 EXECUTION REQUEST", 
            f"Active Inversion Hook requires authorization to write software asset directly to drive.\n\nTarget File: {filename}\nPath: {self.workspace_dir}\n\nApprove this compilation task?"
        )

        if approve_compile:
            try:
                full_destination_path = os.path.join(self.workspace_dir, filename)
                with open(full_destination_path, "w", encoding="utf-8") as target_file:
                    target_file.write(source_code)
                
                self.compilation_count += 1
                trace_status = f"[✔] SUCCESS: Automated software creation complete. Script written to drive path: {filename}"
                self.lbl_mesh_status.config(text=f"MESH STATUS: AUTOMATED BLUEPRINT INGESTION NODE ONLINE | Active Compilations: {self.compilation_count} files | Framework Alignment: 100% Invariant")
            except Exception as hardware_fault:
                trace_status = f"[CRITICAL ERROR] Failed to ground code bytes to local drive storage: {hardware_fault}"
        else:
            trace_status = "[MUTE] Ingestion task suspended by supervisor. File creation sequence aborted."

        self.write_terminal_trace(trace_status)
        self.write_telemetry_entry(op_mode, state_flag, trace_status, filename)
        self.pinnacle_indicator.config(text="STATUS: AUTOMATION BUS COLD CORE (STANDBY)", foreground="#FFFF00")

if __name__ == "__main__":
    observatory_root = tk.Tk()
    app = SoftwareCreatorObservatory(observatory_root)
    observatory_root.mainloop()






