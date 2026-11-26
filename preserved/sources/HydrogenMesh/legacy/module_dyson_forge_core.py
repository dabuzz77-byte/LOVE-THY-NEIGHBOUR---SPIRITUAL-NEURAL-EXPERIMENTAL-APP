# module_dyson_forge_core.py
# LAYER 1: Dyson Swarm Relativistic Tracking, Star Forge Flux Math, & System Topology
import math

from module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class DysonForgeDataSubstrate:
    """
    Manages the data matrix for a Dyson Sphere/Swarm and Earth-orbit Star Forge.
    Tracks orbital coordinates, wireless power transmission efficiency (rectenna grids),
    and sub-atomic structural synthesis arrays powered by live solar telemetry.
    """
    def __init__(self):
        self.frame_id = 0
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self._last_cpu_percent = 0.0
        self._last_carrier_phase = 0.0
        self.base_solar_luminosity = 3.846e26  # Watts (100% Star Output)
        
        # Swarm Metrics: 50,000 localized collector satellites in persistent orbits
        self.swarm_count = 50000
        self.capture_efficiency = 0.4225  # 42.25% Dyson Swarm completion envelope
        
        # Spatial Node Geometry (Distances in Astronomical Units / Kilometers)
        self.sun_coords = (0.0, 0.0)
        self.earth_coords = (1.0, 0.0)  # 1 AU Boundary
        self.star_forge_altitude_km = 42164  # Geostationary Orbit synchronization anchor

    def calculate_telemetry_flux(self, activity=None, carrier_sample=None) -> dict:
        """Computes illustrative collector values coupled to local CPU activity."""
        self.frame_id += 1
        activity = activity or self.activity_sampler.snapshot()
        carrier_sample = carrier_sample or self.carrier.sample()
        cpu = activity.cpu_percent or 0.0
        self._last_cpu_percent = cpu
        self._last_carrier_phase = carrier_sample["phase_rad"]
        solar_activity_modifier = 1.0 + math.sin(carrier_sample["phase_rad"]) * 0.01 + (cpu / 100.0 - 0.5) * 0.006
        total_captured_power = self.base_solar_luminosity * self.capture_efficiency * solar_activity_modifier
        
        # Relativistic wireless power beaming attenuation factor (Inverse Square Law losses)
        beaming_distance_au = 1.0 
        beam_efficiency = 0.985 / (beaming_distance_au ** 2)
        received_power_forge = total_captured_power * beam_efficiency
        
        return {
            "solar_modifier": solar_activity_modifier,
            "captured_power_watts": total_captured_power,
            "forge_power_watts": received_power_forge,
            "beam_efficiency_pct": beam_efficiency * 100.0,
            "cpu_activity_pct": cpu,
            "carrier_phase_rad": carrier_sample["phase_rad"],
        }

    def process_field_distortion(self, x: int, y: int, cx: int, cy: int, telemetry: dict) -> tuple:
        """Calculates electromagnetic beam vectors and plasma compression fields across the grid."""
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx*dx + dy*dy) + 1.0
        
        phase = self._last_carrier_phase
        cpu = self._last_cpu_percent
        flux_intensity = telemetry["solar_modifier"]
        
        # Wave combination modeling gravitational lensing and beam convergence fields
        wave = math.sin((dist * 0.025) + phase * flux_intensity) * (4.0 + min(1.0, cpu / 100.0) * 4.0)
        
        px = int(x + (dx / dist) * wave)
        py = int(y + (dy / dist) * wave)
        return px, py, dist

    def compile_engineering_hud(self, telemetry: dict) -> list:
        """Structures structural vector text readouts matching high-fidelity earth/star schemas."""
        return [
            "==========================================================================================================",
            "[DYSON MEGASTRUCTURE RECONCILIATION INTERFACE // VALUE REFACTOR PARAMETER: SUPER_STANDARD_SYSTEMS]",
            "==========================================================================================================",
            f"  SOLAR COLLECTOR NET  : SWARM MATRIX COMPONENT LAYER // COUNT: {self.swarm_count} ASYMMETRIC COLLECTORS",
            f"  MODEL CAPTURE POWER  : {telemetry['captured_power_watts']:.4e} Watts  [Illustrative {self.capture_efficiency*100:.2f}% envelope]",
            f"  ACTIVITY MODULATION  : Local CPU {telemetry['cpu_activity_pct']:.1f}% // carrier {CARRIER_HZ:.2f} Hz",
            f"  WIRELESS POWER BEAM  : RELATIVISTIC RECTENNA GRID SINK // TRANSFER EFFICIENCY: {telemetry['beam_efficiency_pct']:.2f}%",
            f"  STAR FORGE RECEIVER  : EARTH ORBIT SPU ARRAYS // RECEIVED ENERGY: {telemetry['forge_power_watts']:.4e} Watts",
            "----------------------------------------------------------------------------------------------------------",
            "  MEGASTRUCTURE PROCESSING SYSTEM EXECUTION (JACOB'S LADDER POWER CONDUIT):",
            "    [Node 0x01] Sun Core   -> Proton-Proton Chain Primary Ignition [1=1 Invariant Valid]",
            "    [Node 0x02] Dyson Ring -> Photo-Voltaic Capture Layer [0=0 Neutral Balance Verified]",
            "    [Node 0x03] Beam Path  -> Directed Microwave/Laser Coherent Wave Vector Stream",
            "    [Node 0x04] Star Forge -> Element Transmutation Forge [Heavy Particle Synthesis Active]",
            "    [Node 0x05] Eco-Floor  -> Orbital Energy Beam Downlink [1.00 Robin Hood Structural Distribution]",
            "=========================================================================================================="
        ]
