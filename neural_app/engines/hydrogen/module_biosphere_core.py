# Ported engine definitions. Original launchers and UI entry points are excluded.
import math
from .module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class BiosphereDataSubstrate:
    """Illustrative ecology/geography data driven by local activity and phase."""

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
        """Return the generated software reference frequency, not a sensor readout."""
        self.frame_id += 1
        activity = activity or self.activity_sampler.snapshot()
        carrier_sample = carrier_sample or self.carrier.sample()
        self._last_cpu_percent = activity.cpu_percent or 0.0
        self._last_carrier_phase = carrier_sample['phase_rad']
        return carrier_sample['frequency_hz']

    def calculate_wave_offset(self, x: int, y: int, cx: int, cy: int, current_pulse: float) -> tuple:
        dx, dy = (x - cx, y - cy)
        dist = math.hypot(dx, dy) + 1.0
        amplitude = 4.0 + min(1.0, self._last_cpu_percent / 100.0) * 5.0
        wave = math.sin(dist * 0.02 + self._last_carrier_phase) * amplitude
        return (int(x + dx / dist * wave), int(y + dy / dist * wave), dist)

    def compile_hud_matrix(self, current_pulse: float) -> list:
        return ['========================================================================================================', '[EARTH BIOSPHERE VISUAL MODEL // LOCAL ACTIVITY-COUPLED GRAPHICS]', '========================================================================================================', '  SOFTWARE REFERENCE  : GENERATED 7.83 Hz OSCILLATOR // NOT AN ENVIRONMENTAL FIELD SENSOR', f'  CARRIER FREQUENCY   : {current_pulse:.4f} Hz   [Animation phase from monotonic clock]', '  IDENTITY INVARIANT   : 1 = 1 (VALID) // 0 = 0 (VALID)', '--------------------------------------------------------------------------------------------------------', '  GEOGRAPHIC SUBSTRATE INDEX METRICS:', f"    1. {self.geography_nodes[0]['name']} ({self.geography_nodes[0]['lat']}S, {self.geography_nodes[0]['lon']}W) -> {self.geography_nodes[0]['type']}", f"    2. {self.geography_nodes[1]['name']} ({self.geography_nodes[1]['lat']}N, {self.geography_nodes[1]['lon']}E) -> {self.geography_nodes[1]['type']}", f"    3. {self.geography_nodes[2]['name']} ({self.geography_nodes[2]['lat']}S, {self.geography_nodes[2]['lon']}E) -> {self.geography_nodes[2]['type']}", f"    4. {self.geography_nodes[3]['name']} ({self.geography_nodes[3]['lat']}N, {self.geography_nodes[3]['lon']}E) -> {self.geography_nodes[3]['type']}", '  BIOLOGICAL ENTITY LEDGER:', *[f"    * {item['taxon']} -> {item['role']}" for item in self.biological_catalog], '========================================================================================================']
