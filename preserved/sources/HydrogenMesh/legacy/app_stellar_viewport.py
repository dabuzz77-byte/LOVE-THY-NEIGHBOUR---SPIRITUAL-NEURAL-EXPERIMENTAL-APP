# app_stellar_viewport.py
# LAYER 2: Graphical Window Interface, Chromatic Plasma Loop, & Radiative Render Presentation
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import sys
import math
import random
from module_runtime import get_carrier, get_system_sampler

# Import solar data layer dependencies from the companion code block module
try:
    from module_stellar_core import StellarCoreSubstrate
except ImportError:
    # Safe fallback if combined locally into a unified individual file script
    pass

class StellarPresentationEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("STELLAR FUSION ENGINE v9.0 // CHROMATIC SOLAR MATRIX")
        self.WIDTH, self.HEIGHT = 1100, 820
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)

        # Enforce Solar Chromatic Spectral Palette (RGB Formats)
        self.CLR_SPACE_VOID  = (0, 0, 0)         # Deep Space Ambient Containment
        self.CLR_CORE_WHITE  = (255, 255, 240)   # High-Density Fusion Core Zone
        self.CLR_SOLAR_GOLD  = (245, 180, 0)     # Relativistic Energy Radiative Field
        self.CLR_CORONA_ORNG = (220, 85, 5)      # Flaring Convection Plasma
        self.CLR_PROT_BROWN  = (110, 45, 10)     # Low-Temperature Outer Granulation Bounds
        self.CLR_LINE_BLUE   = (30, 75, 160)     # Telemetry Interface Boundaries

        self.root.configure(bg="#000000")
        
        # Instantiate solar logic substrate
        self.substrate = StellarCoreSubstrate()
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self.center_x = self.WIDTH // 2
        self.center_y = self.HEIGHT // 2 + 80

        self._initialize_canvas_viewport()
        self._execution_loop()

    def _initialize_canvas_viewport(self):
        """Constructs the native frame-swapping layout container."""
        self.viewport = tk.Label(self.root, bg="#000000", bd=0, highlightthickness=0)
        self.viewport.pack(fill="both", expand=True)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown_pipeline)

    def _compile_frame_buffer(self) -> Image.Image:
        """Processes plasma physics arrays, radiative zones, and element layers entirely in memory."""
        frame = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=self.CLR_SPACE_VOID)
        draw = ImageDraw.Draw(frame)

        live_flux = self.substrate.fetch_live_flux()
        carrier = self.carrier.sample()
        activity = self.activity_sampler.snapshot()
        cpu = activity.cpu_percent or 0.0
        time_factor = carrier["phase_rad"]

        # 1. Draw Geometric Plasma Lattice Wave
        grid_spacing = 32
        for x in range(30, self.WIDTH, grid_spacing):
            for y in range(230, self.HEIGHT, grid_spacing):
                px, py, dist = self.substrate.calculate_fusion_wave(
                    x, y, self.center_x, self.center_y, live_flux
                )

                if 0 <= px < self.WIDTH and 0 <= py < self.HEIGHT:
                    # Distribute solar spectral colors based on calculated core distance constraints
                    if dist < 70:     grid_color = self.CLR_CORE_WHITE  # Fusion center
                    elif dist < 150:  grid_color = self.CLR_SOLAR_GOLD  # Radiative zone
                    elif dist < 240:  grid_color = self.CLR_CORONA_ORNG # Convective loop
                    elif dist < 330:  grid_color = self.CLR_PROT_BROWN  # Solar limb boundaries
                    else:             continue                          # Space vacuum boundary

                    draw.rectangle([px, py, px+1, py+1], fill=grid_color)

        # 2. Draw Element Climbing Matrix Tracks (Jacob's Ladder Nucleosynthesis Mapping)
        num_ladders = 6
        climb_radius = 180 + math.sin(time_factor) * (12 + cpu * 0.08)
        for i in range(num_ladders):
            angle = (i * (math.pi * 2 / num_ladders)) + (time_factor * 0.25)
            
            # Element particle acceleration positions
            ex = int(self.center_x + math.cos(angle) * climb_radius)
            ey = int(self.center_y + math.sin(angle) * climb_radius)
            
            # Sub-atomic fusion interaction arcs
            ix = int(self.center_x + math.cos(angle + math.pi/3) * (climb_radius * 0.45))
            iy = int(self.center_y + math.sin(angle + math.pi/3) * (climb_radius * 0.45))
            
            draw.ellipse([ex-6, ey-6, ex+6, ey+6], fill=self.CLR_SOLAR_GOLD, outline=self.CLR_CORE_WHITE, width=1)
            draw.rectangle([ix-3, iy-3, ix+3, iy+3], fill=self.CLR_CORONA_ORNG)

            # High-fidelity gamma-ray burst particle visualization
            if random.random() > 0.965:
                draw.line([self.center_x, self.center_y, ex, ey], fill=self.CLR_CORE_WHITE, width=1)
                draw.ellipse([ex-9, ey-9, ex+9, ey+9], outline=self.CLR_CORE_WHITE, width=1)

        # 3. Draw Invariant Core Anchor
        center_pulse = 20 + math.sin(time_factor * 0.9) * 3
        draw.ellipse([self.center_x - center_pulse, self.center_y - center_pulse, self.center_x + center_pulse, self.center_y + center_pulse], outline=self.CLR_SOLAR_GOLD, width=2)
        draw.ellipse([self.center_x - 4, self.center_y - 4, self.center_x + 4, self.center_y + 4], fill=self.CLR_CORE_WHITE)

        # 4. Render Telemetry HUD Strings
        hud_lines = self.substrate.compile_stellar_telemetry(live_flux)
        y_offset = 12
        for line in hud_lines:
            if "TRUE" in line or "VALID" in line or "ENGINE" in line or "Watts" in line:
                color = "#FFFFFF"  # Relativistic white highlights
            elif "NUCLEOSYNTHESIS" in line or "Rung" in line:
                color = "#FFB300"  # Solar gold element steps
            elif "Hydrogen" in line or "Deuterium" in line or "Helium" in line:
                color = "#FF7043"  # Convective orange text for elements
            else:
                color = "#5C6BC0"  # Steel blue text for structure boundaries

            draw.text((25, y_offset), line, fill=color)
            y_offset += 15

        activity_text = f"LOCAL CPU {cpu:.1f}%  RAM {'n/a' if activity.memory_percent is None else f'{activity.memory_percent:.1f}%'}  |  SOFTWARE CARRIER 7.83 Hz"
        draw.text((25, self.HEIGHT - 24), activity_text, fill="#42E8FF")

        return frame

    def _execution_loop(self):
        """Swaps presentation display frames continuously at ~60 FPS hardware bounds."""
        self.memory_frame = self._compile_frame_buffer()
        self.photo_buffer = ImageTk.PhotoImage(self.memory_frame)
        self.viewport.configure(image=self.photo_buffer)
        self.loop_id = self.root.after(33, self._execution_loop)

    def _shutdown_pipeline(self):
        """Halts the scheduling thread and unloads window assets cleanly."""
        self.root.after_cancel(self.loop_id)
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    # Boot stellar model application
    runtime = tk.Tk()
    app = StellarPresentationEngine(runtime)
    runtime.mainloop()
