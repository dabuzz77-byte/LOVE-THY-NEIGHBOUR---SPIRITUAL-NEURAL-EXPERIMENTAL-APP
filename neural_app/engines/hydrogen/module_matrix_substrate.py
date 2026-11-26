# Ported engine definitions. Original launchers and UI entry points are excluded.
from .module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class SystemDataSubstrate:
    """
    Manages the core telemetry data and logical tracking layers for the 
        Global Matrix Engine. Holds the 7.83 Hz generated software carrier,
    solar flux parameters, and taxonomic classification data registers.
    """

    def __init__(self):
        self.nominal_schumann_hz = CARRIER_HZ
        self.carrier = get_carrier()
        self.activity = get_system_sampler()
        self.base_solar_flux_wm2 = 1361.2
        self.nucleosynthesis_ladder = [{'step': 1, 'element': 'Hydrogen (1H)', 'mass_amu': 1.0078, 'desc': 'Primary Fusion Fuel Source'}, {'step': 2, 'element': 'Deuterium (2H)', 'mass_amu': 2.0141, 'desc': 'First Rung // Proton Ignition'}, {'step': 3, 'element': 'Helium-3 (3He)', 'mass_amu': 3.016, 'desc': 'Intermediate State // Gamma Release'}, {'step': 4, 'element': 'Helium-4 (4He)', 'mass_amu': 4.0026, 'desc': 'Stable Alpha Particle Core Ascent'}, {'step': 5, 'element': 'Carbon (12C)', 'mass_amu': 12.0, 'desc': 'Ultimate Threshold // CNO Cycle Anchor'}]
        self.biological_catalog = [{'taxon': 'Cyanobacteria (Microscopic Base)', 'role': 'Primary Electron Donors // Oxygen Genesis'}, {'taxon': 'Mycelial Networks (Sub-Terrestrial)', 'role': 'Inter-Neural Nutrient Transport Grids'}, {'taxon': 'Arthropoda / Insecta (Chitin)', 'role': 'Pollination Processing Vectors'}, {'taxon': 'Hominid / Neural (Ternary)', 'role': 'Conscious Observation & Code Conduit'}]

    def capture_runtime_state(self) -> dict:
        """Return actual local OS readings alongside the generated carrier phase."""
        snapshot = self.activity.snapshot()
        carrier = self.carrier.sample()
        return {'cpu_percent': snapshot.cpu_percent, 'memory_percent': snapshot.memory_percent, 'memory_used_gb': snapshot.memory_used_gb, 'memory_total_gb': snapshot.memory_total_gb, 'network_sent_bytes_sec': snapshot.network_sent_bytes_sec, 'network_recv_bytes_sec': snapshot.network_recv_bytes_sec, 'gpu_percent': snapshot.gpu_percent, 'gpu_memory_percent': snapshot.gpu_memory_percent, 'telemetry_source': snapshot.source, 'carrier_hz': carrier['frequency_hz'], 'carrier_phase_rad': carrier['phase_rad'], 'sampled_at': snapshot.sampled_at}
