"""User's explicit eight-case good/evil bit table, independent of virtue pass.

Classifications are supplied evidence/annotations, not inferred from raw bits or
people's identities. Repeated evil flips have period two, not convergence.
"""
import hashlib
from ..graphical_app.alignment_core import BitVector
from ..graphical_app.chiral import rotate_byte

def evaluate_bits(body):
    bits = body.get('bits', '')
    labels = body.get('classifications', 'unknown')
    highest = body.get('highest_virtue')
    basis = body.get('evidence', '')
    if not isinstance(basis, str) or len(basis) > 2000:
        raise ValueError('Evidence must be text up to 2,000 characters')
    if not isinstance(bits, str) or not 1 <= len(bits) <= 4096 or set(bits) - {'0', '1'}:
        raise ValueError('Supply 1–4,096 binary digits')
    if highest is not None and type(highest) is not bool:
        raise ValueError('Highest virtue must be true, false or unknown')
    mapping = {'good': 'G', 'evil': 'E', 'unknown': '?'}
    if isinstance(labels, str) and labels.lower() in mapping:
        labels = mapping[labels.lower()] * len(bits)
    if not isinstance(labels, str) or len(labels) != len(bits) or set(labels) - {'G', 'E', '?'}:
        raise ValueError('Use good/evil/unknown for all bits, or one G, E or ? per bit')
    sweeps = body.get('sweeps', 4)
    if type(sweeps) is not int or not 1 <= sweeps <= 16:
        raise ValueError('Choose 1–16 trajectory steps')

    def flip(value):
        return ''.join((str(1 - int(bit)) if kind == 'E' else bit for bit, kind in zip(value, labels)))
    output = flip(bits)
    trajectory = []
    current = bits
    for index in range(sweeps):
        current = flip(current)
        trajectory.append({'step': index + 1, 'bits': current})
    raw, padding = BitVector.pack(output)
    return {'input_bits': bits, 'output_bits': output, 'classifications': labels, 'highest_virtue': highest, 'highest_virtue_changes_transform': False, 'changed_bits': labels.count('E'), 'good_preserved': labels.count('G'), 'unknown_preserved': labels.count('?'), 'classification_basis': 'User-supplied labels; no moral meaning inferred from 0/1', 'status': 'classified' if '?' not in labels else 'partial; unresolved labels preserved', 'inverse_verified': flip(output) == bits, 'output_sha256': hashlib.sha256(raw).hexdigest(), 'padding_bits': padding, 'evidence': basis, 'evidence_verified': False, 'bit_trace': [{'index': i, 'input': a, 'output': b, 'classification': kind, 'operation': 'flip' if kind == 'E' else 'preserve', 'resolved': kind != '?'} for i, (a, b, kind) in enumerate(zip(bits, output, labels))], 'trajectory': trajectory, 'period': 2 if 'E' in labels else 1, 'scope': 'Local data transform; no judgment of people, external action or privilege change.'}

def chiral_forecast(bits, target):
    if not isinstance(bits, str) or not bits or len(bits) > 4096 or len(bits) % 8 or set(bits) - {'0', '1'}:
        raise ValueError('Chiral forecast needs up to 4,096 bits, in complete bytes')
    if not isinstance(target, str) or len(target) != len(bits) or set(target) - {'0', '1'}:
        raise ValueError('Target must have the same binary width')
    raw = bytes((int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)))
    candidates = []
    for offset in range(4):
        changed = bytes((rotate_byte(b, offset) for b in raw))
        out = ''.join((f'{b:08b}' for b in changed))
        candidates.append({'offset': offset, 'mismatches': sum((a != b for a, b in zip(out, target))), 'bits': out, 'inverse_verified': bytes((rotate_byte(b, -offset) for b in changed)) == raw})
    best = min(candidates, key=lambda r: r['mismatches'])
    return {'input_bits': bits, 'target_bits': target, 'candidates': candidates, 'best': best, 'reduction': candidates[0]['mismatches'] - best['mismatches'], 'scope': 'Exhaustive four-state forecast of the original opposite-nibble rotation. A target is not a virtue classification.'}
