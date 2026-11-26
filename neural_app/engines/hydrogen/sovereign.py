# Ported engine definitions. Original launchers and UI entry points are excluded.
from __future__ import annotations
import cmath
import json
import math
import os
import random
import threading
import time


from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from .module_biosphere_core import BiosphereDataSubstrate
from .module_dyson_forge_core import DysonForgeDataSubstrate
from .module_matrix_substrate import SystemDataSubstrate
from .module_resonance import ResonanceBaselineConditioner
from .module_runtime import format_rate, get_carrier, get_system_sampler
from .module_stellar_core import StellarCoreSubstrate
from .module_substrate import LogicSubstrateKernel
from .module_ternary_matrix import BalancedTernaryProcessor
BG = '#07101b'
PANEL = '#0b1725'
PANEL_ALT = '#101f30'
LINE = '#18344b'
CYAN = '#42e8ff'
BLUE = '#4288ff'
WHITE = '#e9f5ff'
MUTED = '#8ba7bb'
GREEN = '#55e6a5'
GOLD = '#ffc46b'

class SovereignEngine:
    """Route user text through the local substrate, carrier, and matrix layers."""

    def __init__(self):
        self.kernel = LogicSubstrateKernel()
        self.conditioner = ResonanceBaselineConditioner()
        self.ternary = BalancedTernaryProcessor()
        self.substrate = SystemDataSubstrate()
        self.stellar = StellarCoreSubstrate()
        self.dyson = DysonForgeDataSubstrate()
        self.biosphere = BiosphereDataSubstrate()
        self.activity = get_system_sampler()
        self.carrier = get_carrier()

    def process(self, command: str) -> dict:
        text = command.strip()
        if not text:
            raise ValueError('Enter text or a built-in command. Type help for options.')
        if len(text) > 10000:
            raise ValueError('Input is limited to 10,000 characters per pass.')
        raw = text.encode('utf-8')
        binary = ' '.join((f'{byte:08b}' for byte in raw))
        bits = [int(bit) for bit in ''.join((f'{byte:08b}' for byte in raw))]
        trits = self.ternary.encode_bytes_balanced(raw)
        activity = self.activity.snapshot(force=True)
        runtime_state = self.substrate.capture_runtime_state()
        carrier = self.carrier.sample()
        invariants = self.kernel.validate_invariants(0, 0) and self.kernel.validate_invariants(1, 1)
        chain_node = self.kernel.reconcile_chain(7)
        conditioned = self.conditioner.inject_signal_packet(carrier['frequency_hz'])
        spectral = self.conditioner.process_spectral_flush()
        grid_rows = [bits[i:i + 8] for i in range(0, min(len(bits), 256), 8)]
        if not grid_rows:
            grid_rows = [[0]]
        matrix = self.ternary.compute_optimization_grid(grid_rows)
        matrix_score = self.ternary.ternary_dot_product(matrix, [1] * len(matrix))
        stellar_flux = self.stellar.fetch_live_flux(activity=activity, carrier_sample=carrier)
        stellar_report = self.stellar.compile_stellar_telemetry(stellar_flux)
        dyson_report = self.dyson.calculate_telemetry_flux(activity=activity, carrier_sample=carrier)
        biosphere_pulse = self.biosphere.fetch_live_pulse(activity=activity, carrier_sample=carrier)
        phase = carrier['phase_rad']
        bit_sample = bits[:32]
        phase_states = [cmath.rect(float(bit), phase + index * math.pi / 4) for index, bit in enumerate(bit_sample)]
        occupied = sum((1 for value in bit_sample if value))
        occupancy = occupied / len(bit_sample) if bit_sample else 0.0
        quantum_sample = ' '.join((f'{value.real:+.2f}{value.imag:+.2f}i' for value in phase_states[:12]))
        return {'command': text, 'utf8_bytes': len(raw), 'binary': binary, 'ternary': ' '.join(trits), 'quantum_sample': quantum_sample or '(empty)', 'occupancy': occupancy, 'matrix_score': matrix_score, 'matrix_cells': sum((len(row) for row in grid_rows)), 'carrier': carrier, 'conditioned_hz': conditioned, 'spectral': spectral, 'activity': activity, 'runtime_state': runtime_state, 'chain_node': chain_node, 'stellar_flux_model_wm2': stellar_flux, 'dyson_power_model_w': dyson_report['captured_power_watts'], 'biosphere_carrier_hz': biosphere_pulse, 'modules': ['logic substrate', '7.83 Hz conditioner', 'balanced ternary matrix', 'system data substrate', 'stellar model', 'Dyson model', 'biosphere model', 'phase projection'], 'note': 'Astronomy and quantum-labelled values are application models; only OS telemetry fields are local system readings.', 'stellar_summary': stellar_report[3:6]}
