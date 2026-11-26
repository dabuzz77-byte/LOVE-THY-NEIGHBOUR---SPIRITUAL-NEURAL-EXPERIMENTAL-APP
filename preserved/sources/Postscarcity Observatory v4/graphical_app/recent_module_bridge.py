"""Adapters from normal Observatory module inputs to the supplied local engines.

Inputs remain data. No payload is evaluated as Python, shell text or a permission
decision. Every run uses the existing worker, primary cascade and result bus.
"""
import asyncio
import hashlib
import json
import random

from blueprint_inspector import HypervisorBoundaryBridge
from dual_rail_rules import display_step
from kraken_audio import KrakenAudioDeploymentCore
from parallel_dual_rail import ParallelDualRailEngine
from persistent_drill import parity_sweep


def _bits(inputs, name):
    value = inputs.get(name)
    if not isinstance(value, list) or len(value) != 8 or any(type(bit) is not int or bit not in (0, 1) for bit in value):
        raise ValueError(f'{name} must contain exactly eight integer bits (0 or 1)')
    return value.copy()


def _text(inputs, name, default=''):
    value = inputs.get(name, default)
    if not isinstance(value, str):
        raise ValueError(f'{name} must be text')
    return value


def execute_component(kind, inputs, definitions):
    """Evaluate one invocation from editable input data, with no detached work."""
    if not isinstance(inputs, dict):
        raise ValueError('Module input must be a dictionary')
    payload = _text(inputs, 'payload')
    before = {}
    if kind in ('original', 'part1', 'parallel', 'drill'):
        a, b = _bits(inputs, 'rail_a'), _bits(inputs, 'rail_b')
        before = {'rail_a': a.copy(), 'rail_b': b.copy()}
    elif kind in ('blueprint', 'kraken'):
        registers = _bits(inputs, 'registers')
        before = {'registers': registers.copy()}
    else:
        raise ValueError('Unknown local component')

    if kind in ('original', 'part1'):
        seed = inputs.get('random_seed')
        if seed is not None and type(seed) is not int:
            raise ValueError('random_seed must be an integer or null')
        output = display_step(payload, a, b, random.Random(seed), kind)
        after = {'rail_a': output['a'], 'rail_b': output['b']}
    elif kind == 'parallel':
        engine = ParallelDualRailEngine()
        engine.register_rail_A, engine.register_rail_B = a, b
        output = asyncio.run(engine.execute_synchronized_runall(payload))
        after = {'rail_a': output['stored_rail_A'], 'rail_b': output['stored_rail_B']}
    elif kind == 'drill':
        a, b = parity_sweep(a, b)
        after = {'rail_a': a, 'rail_b': b}
        output = {'rail_a': a, 'rail_b': b, 'sweeps_completed': 1,
                  'payload_role': 'Recorded input context; the supplied sweep is unconditional.',
                  'repeat_with': 'Existing Observatory module loop controls'}
    elif kind == 'blueprint':
        engine = HypervisorBoundaryBridge()
        engine.core_registers = registers
        output = engine.execute_boundary_refraction(payload)
        after = {'registers': output['local_register_result']}
    else:
        engine = KrakenAudioDeploymentCore()
        engine.core_registers = registers
        output = engine.process_kraken_audio_trigger(_text(inputs, 'video_timestamp'), payload)
        after = {'registers': output['grounded_hardware_array']}

    transitions = {name: [i for i, (old, new) in enumerate(zip(before[name], bits)) if old != new]
                   for name, bits in after.items()}
    return {
        'component': kind,
        'intent': {'label': 'HIGH VIRTUE', 'goal': 'Alleviate suffering', 'basis': 'User-stated intent'},
        'algorithm_output': output,
        'registers_before': before,
        'registers_after': after,
        'changed_bit_positions': transitions,
        'input_sha256': hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest(),
        'definitions': definitions,
        'scope': 'Local register computation. Shared Observatory execution and admission checks apply.',
        'state_lifecycle': 'Fresh engine for each module run; supplied input registers are the starting state.',
    }
