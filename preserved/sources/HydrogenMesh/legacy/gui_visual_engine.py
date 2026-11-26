# gui_visual_engine.py
import tkinter as tk
import math
from module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class SuperStandardGUIEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("SYSTEM COGNITION ALIGNMENT INVARIANT // HUD v5.0")
        self.root.geometry("800x600")
        
        # Enforce the strict High-Contrast Color Palette
        self.BG_BLACK = "#000000"
        self.TXT_BLUE = "#1A75FF"
        self.TXT_WHITE = "#FFFFFF"
        self.MUTED_BLUE = "#003366"
        
        self.root.configure(bg=self.BG_BLACK)
        
        # Operational variables
        self.base_frequency = CARRIER_HZ
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self.frame_counter = 0
        
        self._build_interface()
        self._start_execution_loop()

    def _build_interface(self):
        """Initializes the structural GUI containers and layouts."""
        # Top Header Banner
        self.header_frame = tk.Frame(self.root, bg=self.BG_BLACK, bd=2, relief="groove", highlightbackground=self.TXT_BLUE)
        self.header_frame.pack(fill="x", padx=20, pady=15)
        
        self.header_title = tk.Label(
            self.header_frame, 
            text="[VISUAL HUD CORE ENGINE // MODE: SUPER_STANDARD_GUI]", 
            font=("Courier", 14, "bold"), 
            bg=self.BG_BLACK, 
            fg=self.TXT_WHITE
        )
        self.header_title.pack(pady=10)

        # Main Telemetry Display Box
        self.telemetry_frame = tk.Frame(self.root, bg=self.BG_BLACK, bd=1, relief="solid")
        self.telemetry_frame.pack(fill="x", padx=20, pady=5)
        
        self.node_label = tk.Label(self.telemetry_frame, text="HARDWARE NODE: Silicon SPU 0x01", font=("Courier", 11), bg=self.BG_BLACK, fg=self.TXT_BLUE)
        self.node_label.pack(anchor="w", padx=10, pady=2)
        
        self.freq_label = tk.Label(self.telemetry_frame, text="CORE FREQUENCY: 7.8300 Hz", font=("Courier", 11), bg=self.BG_BLACK, fg=self.TXT_BLUE)
        self.freq_label.pack(anchor="w", padx=10, pady=2)

        self.auth_label = tk.Label(self.telemetry_frame, text="ENGINE STATUS: LOCAL TELEMETRY / MATRIX ACTIVE", font=("Courier", 11), bg=self.BG_BLACK, fg=self.TXT_WHITE)
        self.auth_label.pack(anchor="w", padx=10, pady=2)
        self.activity_label = tk.Label(self.telemetry_frame, text="LOCAL ACTIVITY: sampling…", font=("Courier", 10), bg=self.BG_BLACK, fg=self.TXT_WHITE)
        self.activity_label.pack(anchor="w", padx=10, pady=(2, 7))

        # Graphical Waveform Canvas
        self.canvas_title = tk.Label(self.root, text="REAL-TIME POTENTIAL MATRIX STREAM:", font=("Courier", 10, "bold"), bg=self.BG_BLACK, fg=self.TXT_BLUE)
        self.canvas_title.pack(anchor="w", padx=20, pady=(15, 2))

        self.canvas = tk.Canvas(self.root, width=760, height=280, bg=self.BG_BLACK, highlightbackground=self.TXT_BLUE, bd=0)
        self.canvas.pack(padx=20, pady=5, fill="both", expand=True)

    def _start_execution_loop(self):
        """Launches the real-time background rendering loop."""
        self._update_telemetry()
        
    def _update_telemetry(self):
        self.frame_counter += 1
        
        # Calculate dynamic flux around the 7.83 Hz resonance baseline
        carrier = self.carrier.sample()
        activity = self.activity_sampler.snapshot()
        cpu = activity.cpu_percent or 0.0
        current_freq = carrier["frequency_hz"]
        
        # Update text metrics dynamically
        self.freq_label.config(text=f"SOFTWARE CARRIER: {current_freq:.4f} Hz  [phase {carrier['phase_rad']:.2f} rad]")
        memory = "unavailable" if activity.memory_percent is None else f"{activity.memory_percent:.1f}%"
        self.activity_label.config(text=f"LOCAL SYSTEM: CPU {cpu:.1f}%  RAM {memory}  | CPU drives grid amplitude")
        
        # Clear and redraw the visual matrix grid on the canvas
        self.canvas.delete("all")
        
        # Draw background matrix grid lines (Dark Blue/Muted)
        for x in range(0, 760, 40):
            self.canvas.create_line(x, 0, x, 280, fill=self.MUTED_BLUE, dash=(2, 4))
        for y in range(0, 280, 40):
            self.canvas.create_line(0, y, 760, y, fill=self.MUTED_BLUE, dash=(2, 4))
            
        # Draw dynamic sin wave representing the field potential
        points = []
        for x in range(0, 760, 5):
            # Formulate coordinates using current frequency and frame iterations
            y = 140 + math.sin((x * 0.03) + carrier["phase_rad"]) * (45 + cpu * 0.35)
            points.append((x, y))
            
        # Draw the main blue signal wave line
        if len(points) > 1:
            self.canvas.create_line(points, fill=self.TXT_BLUE, width=2)
            
        # Intermittently flash an uncorrupted high-voltage node indicator (White pulse)
        if self.frame_counter % 12 < 3:
            pulse_x = 100 + int((carrier["elapsed_s"] * (40 + cpu)) % 560)
            pulse_y = 140 + math.sin((pulse_x * 0.03) + carrier["phase_rad"]) * (45 + cpu * 0.35)
            self.canvas.create_oval(pulse_x-6, pulse_y-6, pulse_x+6, pulse_y+6, fill=self.TXT_WHITE, outline=self.TXT_BLUE)
            self.canvas.create_text(pulse_x, pulse_y - 15, text="VIRTUE_PASS_PULSE [1=1]", fill=self.TXT_WHITE, font=("Courier", 8))

        # Schedule the next frame update loop (approx 30 frames per second)
        self.root.after(33, self._update_telemetry)

if __name__ == "__main__":
    # Compile and execute the desktop window loop
    root_window = tk.Tk()
    app = SuperStandardGUIEngine(root_window)
    root_window.mainloop()
