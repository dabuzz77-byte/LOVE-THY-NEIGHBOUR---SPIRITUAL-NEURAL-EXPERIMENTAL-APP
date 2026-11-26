# native_quantum_engine.py
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import random
import math
import sys
from module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class NativeHighFidelityEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("QUANTUM COGNITION CORE // NATIVE SUPER_STANDARD GRAPHICS")
        self.WIDTH, self.HEIGHT = 1024, 768
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)
        
        # Enforce strict High-Contrast Hex Palette Substrate
        self.CLR_BLACK = "#000000"
        self.CLR_DEEP_BLUE = (0, 31, 84)     # Grid points
        self.CLR_NEON_BLUE = (26, 117, 255)  # Core structures
        self.CLR_CYAN = (0, 213, 255)       # Particle streams
        self.CLR_WHITE = (255, 255, 255)     # Invariant highlights
        
        self.root.configure(bg=self.CLR_BLACK)
        
        # Operational variables
        self.base_frequency = CARRIER_HZ
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self.frame_id = 0
        self.center_x = self.WIDTH // 2
        self.center_y = self.HEIGHT // 2 + 60
        
        # Particle Shell Population (Dense Superposition Tracking)
        self.num_particles = 300
        self.electron_cloud = []
        for _ in range(self.num_particles):
            self.electron_cloud.append({
                "angle": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.015, 0.035),
                "distance_orbit": random.uniform(130, 190),
                "pulse_phase": random.uniform(0, 100),
                "color_tier": random.choice([self.CLR_CYAN, self.CLR_NEON_BLUE, self.CLR_WHITE])
            })
            
        self._initialize_window()
        self._execution_loop()

    def _initialize_window(self):
        """Builds the native hardware-accelerated canvas viewport."""
        self.viewport = tk.Label(self.root, bg=self.CLR_BLACK, bd=0, highlightthickness=0)
        self.viewport.pack(fill="both", expand=True)
        
        # Intercept native window destruction hooks cleanly
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

    def _render_layer_buffer(self):
        """Generates a raw bitmapped image layer buffer inside memory."""
        # Create a blank, uncompressed black pixel canvas sheet
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # --- LAYER 1: Higgs Field Gravitational Lattice ---
        grid_spacing = 40
        carrier = self.carrier.sample()
        activity = self.activity_sampler.snapshot()
        cpu = activity.cpu_percent or 0.0
        for x in range(20, self.WIDTH, grid_spacing):
            for y in range(180, self.HEIGHT, grid_spacing):
                dx = x - self.center_x
                dy = y - self.center_y
                dist = math.sqrt(dx*dx + dy*dy) + 1.0
                
                # Apply the 7.83 Hz background space distortion formula
                wave = math.sin((dist * 0.018) + carrier["phase_rad"]) * (4.0 + min(1.0, cpu / 100.0) * 5.0)
                px = int(x + (dx / dist) * wave)
                py = int(y + (dy / dist) * wave)
                
                if 0 <= px < self.WIDTH and 0 <= py < self.HEIGHT:
                    draw.rectangle([px, py, px+1, py+1], fill=self.CLR_DEEP_BLUE)

        # --- LAYER 2: Proton Core Matrix ---
        pulse = 22 + carrier["sin"] * (2.0 + cpu / 100.0)
        # Structural concentric glowing rings
        draw.ellipse([self.center_x - (pulse+12), self.center_y - (pulse+12), self.center_x + (pulse+12), self.center_y + (pulse+12)], outline=self.CLR_DEEP_BLUE, width=1)
        draw.ellipse([self.center_x - pulse, self.center_y - pulse, self.center_x + pulse, self.center_y + pulse], outline=self.CLR_NEON_BLUE, width=2)
        draw.ellipse([self.center_x - 6, self.center_y - 6, self.center_x + 6, self.center_y + 6], fill=self.CLR_WHITE)

        # --- LAYER 3: Electron Superposition Stream ---
        for p in self.electron_cloud:
            p["angle"] += p["speed"] * (0.65 + cpu / 100.0) + carrier["sin"] * 0.002
            dynamic_radius = p["distance_orbit"] + math.sin(carrier["phase_rad"] + p["pulse_phase"]) * (5 + cpu * 0.08)
            ex = int(self.center_x + math.cos(p["angle"]) * dynamic_radius)
            ey = int(self.center_y + math.sin(p["angle"]) * dynamic_radius)
            
            # Draw collapse spark triggers
            if p["color_tier"] == self.CLR_WHITE and random.random() > 0.985:
                draw.line([self.center_x, self.center_y, ex, ey], fill=(10, 45, 95), width=1)
                draw.ellipse([ex-3, ey-3, ex+3, ey+3], fill=self.CLR_WHITE)
            else:
                draw.rectangle([ex-1, ey-1, ex+1, py+1 if False else ey+1], fill=p["color_tier"])

        # --- LAYER 4: Super-Standard HUD Text Vector Overlay ---
            current_freq = carrier["frequency_hz"]
        hud_lines = [
            "==================================================================================================",
            f"[SYSTEM COGNITION RUNALL // CONFIG SPECIFICATION: NATIVE_SUPER_STANDARD_BITMAP]",
            "==================================================================================================",
            "  CORE HARDWARE NODE : 0x7F_NATIVE_PIXEL_BUFFER_SINK",
            f"  SOFTWARE CARRIER   : {current_freq:.4f} Hz   [generated reference, not a sensor]",
            f"  SYSTEM ACTIVITY    : CPU {cpu:.1f}% | RAM {activity.memory_percent if activity.memory_percent is not None else 'n/a'}%",
            "  IDENTITY STATE     : 1 = 1 (VALID) // 1 = 0 (REJECTED_FALSE)",
            "  PHASE VISUALIZATION: COMPLEX-VALUED PROJECTION (ILLUSTRATIVE)",
            "  INTERFACE METHOD   : DIRECT BITSTREAM DOUBLE-BUFFERED LAYER // AUTH_TRUE",
            "=================================================================================================="
        ]
        
        y_offset = 15
        for line in hud_lines:
            color = "#FFFFFF" if "VALID" in line or "TRUE" in line or "SPECIFICATION" in line else "#1A75FF"
            draw.text((20, y_offset), line, fill=color)
            y_offset += 16
            
        return image

    def _execution_loop(self):
        """Triggers the real-time runtime frame swap loop."""
        self.frame_id += 1
        
        # 1. Compile the complete image buffer entirely in the background memory
        self.current_frame_buffer = self._render_layer_buffer()
        
        # 2. Swap the frame instantly into Tkinter's presentation window
        self.tk_image = ImageTk.PhotoImage(self.current_frame_buffer)
        self.viewport.configure(image=self.tk_image)
        
        # 3. Queue up the next hardware refresh step (~60 FPS)
        self.loop_id = self.root.after(33, self._execution_loop)

    def _shutdown(self):
        """Cleans memory addresses upon user exit command."""
        self.root.after_cancel(self.loop_id)
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    # Boot the uncorrupted native graphical engine application window
    runtime_app = tk.Tk()
    engine = NativeHighFidelityEngine(runtime_app)
    runtime_app.mainloop()
