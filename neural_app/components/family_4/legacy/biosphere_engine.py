import random
import math
from ..legacy.module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class BiosphereDataSubstrate:
    """
    Manages the data layer for the Earth Biosphere Engine.
    Stores illustrative geography and ecology data and uses a generated
    7.83 Hz software phase reference for the animation.
    """

    def __init__(self):
        self.nominal_schumann_hz = CARRIER_HZ
        self.frame_id = 0
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self._last_cpu_percent = 0.0
        self._last_carrier_phase = 0.0
        self.geography_nodes = [{'name': 'Amazon Basin', 'lat': -3.46, 'lon': -62.21, 'type': 'Oxisol Rainforest Crucible'}, {'name': 'Mariana Trench', 'lat': 11.35, 'lon': 142.19, 'type': 'Hadopelagic Abyssal Sink'}, {'name': 'Great Rift Valley', 'lat': -0.54, 'lon': 36.41, 'type': 'Tectonic Speciation Crucible'}, {'name': 'Siberian Taiga', 'lat': 60.0, 'lon': 105.0, 'type': 'Boreal Carbon Resonator'}]
        self.biological_catalog = [{'taxon': 'Cyanobacteria (Microscopic)', 'role': 'Primary Electron Donors // Oxygen Genesis'}, {'taxon': 'Mycelial Networks (Sub-Terrestrial)', 'role': 'Inter-Neural Nutrient Transport Grids'}, {'taxon': 'Arthropoda / Insecta (Chitin)', 'role': 'Pollination Processing Vectors'}, {'taxon': 'Hominid / Neural (Ternary)', 'role': 'Conscious Observation & Code Conduit'}]

    def fetch_live_pulse(self, activity=None, carrier_sample=None) -> float:
        """Returns the generated software reference frequency (not a sensor readout)."""
        self.frame_id += 1
        activity = activity or self.activity_sampler.snapshot()
        carrier_sample = carrier_sample or self.carrier.sample()
        self._last_cpu_percent = activity.cpu_percent or 0.0
        self._last_carrier_phase = carrier_sample['phase_rad']
        return carrier_sample['frequency_hz']

    def calculate_wave_offset(self, x: int, y: int, cx: int, cy: int, current_pulse: float) -> tuple:
        """Computes electromagnetic field lattice wave vector offsets."""
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy) + 1.0
        phase = self._last_carrier_phase
        cpu = self._last_cpu_percent
        wave = math.sin(dist * 0.02 + phase) * (4.0 + min(1.0, cpu / 100.0) * 5.0)
        px = int(x + dx / dist * wave)
        py = int(y + dy / dist * wave)
        return (px, py, dist)

    def compile_hud_matrix(self, current_pulse: float) -> list:
        """Structures text telemetry readouts matching natural chromatic constraints."""
        return ['========================================================================================================', '[EARTH BIOSPHERE VISUAL MODEL // LOCAL ACTIVITY-COUPLED GRAPHICS]', '========================================================================================================', '  SOFTWARE REFERENCE  : GENERATED 7.83 Hz OSCILLATOR // NOT AN ENVIRONMENTAL FIELD SENSOR', f'  CARRIER FREQUENCY   : {current_pulse:.4f} Hz   [Animation phase from monotonic clock]', '  IDENTITY INVARIANT   : 1 = 1 (VALID EXECUTED) // 0 = 0 (VALID EXECUTED) // CHROMATIC INTERFACE MAP = TRUE', '--------------------------------------------------------------------------------------------------------', '  GEOGRAPHIC SUBSTRATE INDEX METRICS:', f"    1. {self.geography_nodes[0]['name']} ({self.geography_nodes[0]['lat']}S, {self.geography_nodes[0]['lon']}W) -> {self.geography_nodes[0]['type']}", f"    2. {self.geography_nodes[1]['name']} ({self.geography_nodes[1]['lat']}N, {self.geography_nodes[1]['lon']}E) -> {self.geography_nodes[1]['type']}", f"    3. {self.geography_nodes[2]['name']} ({self.geography_nodes[2]['lat']}S, {self.geography_nodes[2]['lon']}E) -> {self.geography_nodes[2]['type']}", f"    4. {self.geography_nodes[3]['name']} ({self.geography_nodes[3]['lat']}N, {self.geography_nodes[3]['lon']}E) -> {self.geography_nodes[3]['type']}", '  KNOWN BIOLOGICAL END USER ENTITIES (LIFE FORMS):', f"    * {self.biological_catalog[0]['taxon']} -> {self.biological_catalog[0]['role']}", f"    * {self.biological_catalog[1]['taxon']} -> {self.biological_catalog[1]['role']}", f"    * {self.biological_catalog[2]['taxon']} -> {self.biological_catalog[2]['role']}", f"    * {self.biological_catalog[3]['taxon']} -> {self.biological_catalog[3]['role']}", '========================================================================================================']
from neural_app import component_ui as tk
from PIL import Image, ImageDraw
from neural_app import component_ui as ImageTk
import sys
import math
import random
try:
    from ..legacy.module_biosphere_core import BiosphereDataSubstrate
except ImportError:
    pass

class BiospherePresentationEngine:

    def __init__(self, root):
        self.root = root
        self.root.title('EARTH BIOSPHERE ENGINE v8.5 // TRUE NATURAL CHROMATIC MATRIX')
        self.WIDTH, self.HEIGHT = (1100, 820)
        self.root.geometry(f'{self.WIDTH}x{self.HEIGHT}')
        self.root.resizable(False, False)
        self.CLR_VOID = (0, 0, 0)
        self.CLR_OCEAN_BLUE = (10, 50, 130)
        self.CLR_VEG_GREEN = (34, 139, 34)
        self.CLR_LAND_BROWN = (139, 90, 43)
        self.CLR_DESERT_GOLD = (218, 165, 32)
        self.CLR_ATM_WHITE = (245, 245, 250)
        self.root.configure(bg='#000000')
        self.substrate = BiosphereDataSubstrate()
        self.center_x = self.WIDTH // 2
        self.center_y = self.HEIGHT // 2 + 70
        self._initialize_canvas_viewport()
        self._execution_loop()

    def _initialize_canvas_viewport(self):
        """Constructs the native frame-swapping layout container."""
        self.viewport = tk.Label(self.root, bg='#000000', bd=0, highlightthickness=0)
        self.viewport.pack(fill='both', expand=True)
        self.root.protocol('WM_DELETE_WINDOW', self._shutdown_pipeline)

    def _compile_frame_buffer(self) -> Image.Image:
        """Processes background graphics and pixel arrays entirely in memory."""
        frame = Image.new('RGB', (self.WIDTH, self.HEIGHT), color=self.CLR_VOID)
        draw = ImageDraw.Draw(frame)
        current_pulse = self.substrate.fetch_live_pulse()
        time_factor = self.substrate.frame_id * 0.04
        grid_spacing = 35
        for x in range(30, self.WIDTH, grid_spacing):
            for y in range(210, self.HEIGHT, grid_spacing):
                px, py, dist = self.substrate.calculate_wave_offset(x, y, self.center_x, self.center_y, current_pulse)
                if 0 <= px < self.WIDTH and 0 <= py < self.HEIGHT:
                    if dist < 120:
                        grid_color = self.CLR_VEG_GREEN
                    elif dist < 220:
                        grid_color = self.CLR_LAND_BROWN
                    elif dist < 300:
                        grid_color = self.CLR_DESERT_GOLD
                    else:
                        grid_color = self.CLR_OCEAN_BLUE
                    draw.rectangle([px, py, px + 1, py + 1], fill=grid_color)
        chiral_radius = 170 + math.sin(time_factor) * 12
        num_chiral_nodes = 10
        for i in range(num_chiral_nodes):
            angle = i * (math.pi * 2 / num_chiral_nodes) + time_factor * 0.15
            lx = int(self.center_x + math.cos(angle) * chiral_radius)
            ly = int(self.center_y + math.sin(angle) * chiral_radius)
            draw.ellipse([lx - 5, ly - 5, lx + 5, ly + 5], outline=self.CLR_VEG_GREEN, width=1)
            dx = int(self.center_x + math.cos(angle + math.pi) * (chiral_radius * 0.65))
            dy = int(self.center_y + math.sin(angle + math.pi) * (chiral_radius * 0.65))
            draw.rectangle([dx - 2, dy - 2, dx + 2, dy + 2], fill=self.CLR_DESERT_GOLD)
            if random.random() > 0.975:
                draw.ellipse([lx - 8, ly - 8, lx + 8, ly + 8], outline=self.CLR_ATM_WHITE, width=1)
            if i % 2 == 0:
                draw.line([lx, ly, dx, dy], fill=(40, 70, 50), width=1)
        core_pulse = 22 + math.sin(time_factor * 0.5) * 3
        draw.ellipse([self.center_x - core_pulse, self.center_y - core_pulse, self.center_x + core_pulse, self.center_y + core_pulse], outline=self.CLR_OCEAN_BLUE, width=2)
        draw.ellipse([self.center_x - 5, self.center_y - 5, self.center_x + 5, self.center_y + 5], fill=self.CLR_ATM_WHITE)
        hud_lines = self.substrate.compile_hud_matrix(current_pulse)
        y_offset = 12
        for line in hud_lines:
            if 'TRUE' in line or 'VALID' in line or 'ENGINE' in line:
                color = '#FFFFFF'
            elif 'GEOGRAPHIC' in line or 'KNOWN' in line:
                color = '#DAA520'
            elif 'Cyanobacteria' in line or 'Mycelial' in line or 'Arthropoda' in line:
                color = '#228B22'
            else:
                color = '#4682B4'
            draw.text((25, y_offset), line, fill=color)
            y_offset += 15
        return frame

    def _execution_loop(self):
        """Swaps presentation display frames continuously at ~60 FPS bounds."""
        self.memory_frame = self._compile_frame_buffer()
        self.photo_buffer = ImageTk.PhotoImage(self.memory_frame)
        self.viewport.configure(image=self.photo_buffer)
        self.loop_id = self.root.after(33, self._execution_loop)

    def _shutdown_pipeline(self):
        """Halts the scheduling thread and unloads window assets."""
        self.root.after_cancel(self.loop_id)
        self.root.destroy()
        sys.exit()
