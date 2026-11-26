# Ported engine definitions. Original launchers and UI entry points are excluded.
import math
from .module_runtime import CARRIER_HZ, get_carrier, get_system_sampler

class StellarCoreSubstrate:
    """
    Manages the nuclear fusion and energy data layer for a model of the Sun.
    Simulates the proton-proton (p-p) chain nucleosynthesis matching
    Jacob's Ladder, tracking the transformation of Hydrogen into heavier elements
    driven by live-scaled solar radiative flux telemetry parameters.
    """

    def __init__(self):
        self.frame_id = 0
        self.carrier = get_carrier()
        self.activity_sampler = get_system_sampler()
        self._last_cpu_percent = 0.0
        self._last_carrier_phase = 0.0
        self.solar_radius_km = 696340
        self.core_temperature_kelvin = 15700000.0
        self.base_solar_flux_wm2 = 1361.2
        self.nucleosynthesis_ladder = [{'step': 0, 'element': 'Hydrogen (1H)', 'mass_amu': 1.0078, 'state': 'Primary Fuel Source'}, {'step': 1, 'element': 'Deuterium (2H)', 'mass_amu': 2.0141, 'state': 'First Rung // Proton Fusion'}, {'step': 2, 'element': 'Helium-3 (3He)', 'mass_amu': 3.016, 'state': 'Intermediate State // Gamma Emission'}, {'step': 3, 'element': 'Helium-4 (4He)', 'mass_amu': 4.0026, 'state': 'Stable Alpha Particle Core Ascent'}, {'step': 4, 'element': 'Beryllium-7 (7Be)', 'mass_amu': 7.0169, 'state': 'Heavier Side-Branch Synthesis'}, {'step': 5, 'element': 'Lithium-7 (7Li)', 'mass_amu': 7.016, 'state': 'Electron Capture Convergence'}, {'step': 6, 'element': 'Carbon (12C)', 'mass_amu': 12.0, 'state': 'Ultimate Threshold // CNO Cycle Anchor'}]

    def fetch_live_flux(self, activity=None, carrier_sample=None) -> float:
        """Model solar flux with small variation driven by local CPU and carrier phase."""
        self.frame_id += 1
        activity = activity or self.activity_sampler.snapshot()
        carrier_sample = carrier_sample or self.carrier.sample()
        cpu = activity.cpu_percent or 0.0
        self._last_cpu_percent = cpu
        self._last_carrier_phase = carrier_sample['phase_rad']
        modulation = (cpu / 100.0 - 0.5) * 0.7 + carrier_sample['sin'] * 0.3
        return self.base_solar_flux_wm2 + modulation * 1.4

    def calculate_fusion_wave(self, x: int, y: int, cx: int, cy: int, live_flux: float) -> tuple:
        """Computes thermodynamic compression vectors and radiative expansion fields."""
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy) + 1.0
        phase = self._last_carrier_phase
        cpu = self._last_cpu_percent
        energy_scale = live_flux / 1361.2
        amplitude = 5.0 + min(1.0, cpu / 100.0) * 4.0
        wave = math.sin(dist * 0.03 + phase * energy_scale) * amplitude
        px = int(x + dx / dist * wave)
        py = int(y + dy / dist * wave)
        return (px, py, dist)

    def compile_stellar_telemetry(self, live_flux: float) -> list:
        """Compiles technical logs tracking element ascent and total energy release calculations."""
        energy_per_reaction_mev = 26.73
        estimated_luminosity_watts = 3.846e+26 * (live_flux / 1361.2)
        return ['========================================================================================================', '[STELLAR CORE FUSION ENGINE // MODEL CONFIGURATION: SOLAR_CHROMATIC_RADIATIVE_MATRIX]', '========================================================================================================', f'  SOLAR FLUX SOURCE    : SIMULATED MODEL // MODULATED BY LOCAL SYSTEM ACTIVITY + {CARRIER_HZ:.2f} Hz SOFTWARE CARRIER', f'  MODEL ENERGY FLUX    : {live_flux:.4f} W/m²   [Not a satellite measurement]', f'  MODEL LUMINOSITY     : {estimated_luminosity_watts:.4e} Watts // Illustrative scaling', '--------------------------------------------------------------------------------------------------------', "  NUCLEOSYNTHESIS JACOB'S LADDER ASCENT (HYDROGEN TO HEAVIER ELEMENTS):", f"    Rung 0 -> {self.nucleosynthesis_ladder[0]['element']} ({self.nucleosynthesis_ladder[0]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[0]['state']}", f"    Rung 1 -> {self.nucleosynthesis_ladder[1]['element']} ({self.nucleosynthesis_ladder[1]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[1]['state']}", f"    Rung 2 -> {self.nucleosynthesis_ladder[2]['element']} ({self.nucleosynthesis_ladder[2]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[2]['state']}", f"    Rung 3 -> {self.nucleosynthesis_ladder[3]['element']} ({self.nucleosynthesis_ladder[3]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[3]['state']}", f"    Rung 4 -> {self.nucleosynthesis_ladder[4]['element']} ({self.nucleosynthesis_ladder[4]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[4]['state']}", f"    Rung 5 -> {self.nucleosynthesis_ladder[5]['element']} ({self.nucleosynthesis_ladder[5]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[5]['state']}", f"    Rung 6 -> {self.nucleosynthesis_ladder[6]['element']} ({self.nucleosynthesis_ladder[6]['mass_amu']} amu) -> {self.nucleosynthesis_ladder[6]['state']}", '--------------------------------------------------------------------------------------------------------', f'  ENERGY CONVERSION    : p-p Chain Target Energy Yield per Alpha Particle Event = {energy_per_reaction_mev} MeV', '========================================================================================================']
