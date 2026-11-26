# app_dyson_forge_viewport.py
# LAYER 2: Desktop Presentation GUI Window, Mega-Particle Plasma Renderer, & Main Execution Loop
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import sys
import math
import random
from module_runtime import get_carrier, get_system_sampler

# Import megastructure data engine layer dependencies from companion module
try:
    from module_dyson_forge_core import DysonForgeDataSubstrate
except ImportError:
    pass

class DysonForgePresentationEngine:
    def __init__(self, root):
        self.root = root
        self.root.title("DYSON SWARM INTERFACE v10.0 // NATIVE HIGH FIDELITY HARDWARE SINK")
        self.WIDTH, self.HEIGHT = 1100, 850
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)

        # Enforce True Chromatic Earth-Solar Mega-Architecture Palette (RGB Formats)
        self.CLR_SPACE_VOID  = (0, 0, 0)         # Ambient Cosmos Backdrop
        self.CLR_SUN_WHITE   = (255, 255, 230)   # High-Energy Plasma Center
        self.CLR_DYSON_GOLD  = (230, 160, 0)     # Swarm Collector Shell Lattice
        self.CLR_EARTH_BLUE  = (20, 80, 200)     # Planetary Biosphere Anchor
        self.CLR_FORGE_CYAN  = (0, 230, 240)     # High-Voltage Rectenna Capture Node
        self.CLR_LASER_BEAM  = (255, 255, 255)   # Coherent Wireless Energy Beam / Invariant Highlights
        self.CLR_HUD_STEEL   = (70, 90, 140)     # Border Interface Matrices

        self.root.configure(bg="#000000")
        
        # Instantiate structural logic substrate
        self.substrate = DysonForgeDataSubstrate()
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        
        # Establish layout hubs for multiple spatial anchors
        self.sun_x, self.sun_y = 280, 520        # Solar center locus
        self.forge_x, self.forge_y = 820, 520    # Earth Orbit Star Forge locus

        self._initialize_canvas_viewport()
        self._execution_loop()

    def _initialize_canvas_viewport(self):
        """Constructs the native frame-swapping layout container."""
        self.viewport = tk.Label(self.root, bg="#000000", bd=0, highlightthickness=0)
        self.viewport.pack(fill="both", expand=True)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown_pipeline)

    def _compile_frame_buffer(self) -> Image.Image:
        """Processes space physics arrays, particle orbits, and laser fields entirely in memory."""
        frame = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=self.CLR_SPACE_VOID)
        draw = ImageDraw.Draw(frame)

        telemetry = self.substrate.calculate_telemetry_flux()
        carrier = self.carrier.sample()
        activity = self.activity_sampler.snapshot()
        cpu = activity.cpu_percent or 0.0
        time_factor = carrier["phase_rad"]

        # 1. Draw Background Higgs/Gravity Field Lattice Grid Distortion
        grid_spacing = 35
        for x in range(30, self.WIDTH, grid_spacing):
            for y in range(210, self.HEIGHT, grid_spacing):
                # Ripple field dynamically relative to the Sun's coordinate anchor
                px, py, dist = self.substrate.process_field_distortion(
                    x, y, self.sun_x, self.sun_y, telemetry
                )

                if 0 <= px < self.WIDTH and 0 <= py < self.HEIGHT:
                    # Color map fields relative to space proximity zones
                    dist_to_forge = math.sqrt((px - self.forge_x)**2 + (py - self.forge_y)**2)
                    
                    if dist < 140:
                        grid_color = (60, 40, 5)        # Solar inner boundary
                    elif dist_to_forge < 100:
                        grid_color = (0, 30, 50)        # Earth/Forge geostationary orbit well
                    else:
                        grid_color = (5, 15, 45)        # Interplanetary space vacuum
                    
                    draw.rectangle([px, py, px+1, py+1], fill=grid_color)

        # 2. Draw Directed High-Voltage Wireless Energy Transmission Beam
        # Thicker animated background path indicating plasma channel transfer
        draw.line([self.sun_x, self.sun_y, self.forge_x, self.forge_y], fill=(15, 80, 150), width=4)
        draw.line([self.sun_x, self.sun_y, self.forge_x, self.forge_y], fill=self.CLR_FORGE_CYAN, width=2)
        # Laser core invariant highlight path
        if random.random() > 0.15:
            draw.line([self.sun_x, self.sun_y, self.forge_x, self.forge_y], fill=self.CLR_LASER_BEAM, width=1)

        # 3. Draw the Central Sun and the Surrounding Dyson Swarm Orbit Tracks
        sun_pulse = 30 + math.sin(time_factor * 0.8) * 3
        draw.ellipse([self.sun_x - sun_pulse, self.sun_y - sun_pulse, self.sun_x + sun_pulse, self.sun_y + sun_pulse], fill=self.CLR_SUN_WHITE)
        
        # Render Dyson Swarm Layer (Multiple intersecting elliptical particle tracking bands)
        num_orbit_bands = 4
        for band in range(num_orbit_bands):
            band_phase = band * (math.pi / num_orbit_bands)
            swarm_radius_x = 75 + band * 15
            swarm_radius_y = 45 + band * 5
            
            # Populate discrete collector swarm points along the path ring
            num_collectors = 16
            for c in range(num_collectors):
                angle = (c * (math.pi * 2 / num_collectors)) + (time_factor * (0.15 + band * 0.03))
                
                # Orbit rotation transformations
                rx = swarm_radius_x * math.cos(angle)
                ry = swarm_radius_y * math.sin(angle)
                
                cx = int(self.sun_x + rx * math.cos(band_phase) - ry * math.sin(band_phase))
                cy = int(self.sun_y + rx * math.sin(band_phase) + ry * math.cos(band_phase))
                
                # Draw active golden collector matrices
                draw.rectangle([cx-2, cy-2, cx+2, cy+2], fill=self.CLR_DYSON_GOLD)
                if random.random() > 0.96:
                    draw.line([cx, cy, self.sun_x, self.sun_y], fill=self.CLR_SUN_WHITE, width=1)

        # 4. Draw Earth and the Synchronized Orbital Star Forge Component Node
        earth_radius = 24
        draw.ellipse([self.forge_x - earth_radius, self.forge_y - earth_radius, self.forge_x + earth_radius, self.forge_y + earth_radius], fill=self.CLR_EARTH_BLUE)
        
        # Star Forge Ring (Geostationary Rectenna Ring intercepting the energy beam)
        forge_radius = 50 + math.sin(time_factor) * (1.0 + cpu * 0.02)
        draw.ellipse([self.forge_x - forge_radius, self.forge_y - forge_radius, self.forge_x + forge_radius, self.forge_y + forge_radius], outline=self.CLR_FORGE_CYAN, width=2)
        
        # Construct specific structural receiver spires flashing on the forge array ring
        for sp in range(4):
            sp_angle = (sp * (math.pi / 2)) + (time_factor * 0.1)
            sx = int(self.forge_x + math.cos(sp_angle) * forge_radius)
            sy = int(self.forge_y + math.sin(sp_angle) * forge_radius)
            draw.ellipse([sx-4, sy-4, sx+4, sy+4], fill=self.CLR_LASER_BEAM)

        # 5. Render High-Fidelity Engineering Telemetry HUD
        hud_lines = self.substrate.compile_engineering_hud(telemetry)
        y_offset = 12
        for line in hud_lines:
            if "TRUE" in line or "VALID" in line or "ENGINE" in line or "Watts" in line:
                color = "#FFFFFF"  # Invariant white highlight track
            elif "MEGASTRUCTURE" in line or "Node" in line:
                color = "#FFC107"  # Dyson gold telemetry keys
            elif "SOLAR" in line or "SWARM" in line or "FORGE" in line:
                color = "#00E5FF"  # Forge cyan operations text
            else:
                color = "#78909C"  # Steel boundary accent elements

            draw.text((25, y_offset), line, fill=color)
            y_offset += 15

        activity_text = f"LOCAL CPU {cpu:.1f}%  RAM {'n/a' if activity.memory_percent is None else f'{activity.memory_percent:.1f}%'}  |  SOFTWARE CARRIER 7.83 Hz"
        draw.text((25, self.HEIGHT - 24), activity_text, fill="#00E5FF")

        return frame

    def _execution_loop(self):
        """Swaps presentation display frames continuously at ~60 FPS hardware bounds."""
        self.memory_frame = self._compile_frame_buffer()
        self.photo_buffer = ImageTk.PhotoImage(self.memory_frame)
        self.viewport.configure(image=self.photo_buffer)
        self.loop_id = self.root.after(33, self._execution_loop)

    def _shutdown_pipeline(self):
        """Halts scheduling thread and clears window memory assets safely."""
        self.root.after_cancel(self.loop_id)
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    # Boot megastructure model pipeline application
    runtime = tk.Tk()
    app = DysonForgePresentationEngine(runtime)
    runtime.mainloop()
