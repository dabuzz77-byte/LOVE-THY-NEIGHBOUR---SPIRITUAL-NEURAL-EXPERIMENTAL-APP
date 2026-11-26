# Ported engine definitions. Original launchers and UI entry points are excluded.
import base64
import hashlib
import math
import random
import secrets
import zlib

def packet(raw, bit_length=None, mode='bytes'):
    if len(raw) > 16384:
        raise ValueError('Maximum 16 KiB per signal packet')
    count = len(raw) * 8 if bit_length is None else bit_length
    bits = ''.join((f'{byte:08b}' for byte in raw))[:count]
    p = bits.count('1') / max(1, count)
    entropy = 0 if p in (0, 1) else -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    return dict(mode=mode, base64=base64.b64encode(raw).decode(), hex=raw.hex(), bit_length=count, padding_bits=len(raw) * 8 - count, bits=bits, sha256=hashlib.sha256(raw).hexdigest(), crc32=f'{zlib.crc32(raw):08x}', ones=bits.count('1'), transitions=sum((a != b for a, b in zip(bits, bits[1:]))), bit_balance_entropy=entropy, note='Bit balance is a descriptive statistic, not a randomness certification.')

def from_bits(text):
    bits = ''.join(text.split())
    if not bits or any((x not in '01' for x in bits)):
        raise ValueError('Enter only 0 and 1')
    if len(bits) > 131072:
        raise ValueError('Maximum 131072 bits')
    padded = bits + '0' * (-len(bits) % 8)
    return packet(bytes((int(padded[i:i + 8], 2) for i in range(0, len(padded), 8))), len(bits), 'literal bits')

def generate(mode, size=64, seed='hydrogen', step=0):
    size = int(size)
    if not 1 <= size <= 16384:
        raise ValueError('Size must be 1–16384 bytes')
    if mode == 'OS random':
        raw = secrets.token_bytes(size)
    elif mode == 'Seeded test':
        raw = random.Random(f'{seed}:{step}').randbytes(size)
    elif mode == 'Counter':
        raw = bytes(((step + i) % 256 for i in range(size)))
    elif mode == 'Cellular automaton':
        rng = random.Random(seed)
        row = [rng.randrange(2) for _ in range(128)]
        out = []
        for _ in range(step % 256):
            row = [row[(i - 1) % 128] ^ (row[i] | row[(i + 1) % 128]) for i in range(128)]
        while len(out) < size * 8:
            out.extend(row)
            row = [row[(i - 1) % 128] ^ (row[i] | row[(i + 1) % 128]) for i in range(128)]
        raw = bytes((int(''.join(map(str, out[i:i + 8])), 2) for i in range(0, size * 8, 8)))
    else:
        raise ValueError('Unknown generator')
    result = packet(raw, mode=mode)
    result.update(seed=None if mode == 'OS random' else seed, step=step)
    return result

def decode(value):
    raw = base64.b64decode(value['base64'], validate=True)
    if hashlib.sha256(raw).hexdigest() != value['sha256']:
        raise ValueError('Packet hash mismatch')
    if not 0 <= value['bit_length'] <= len(raw) * 8:
        raise ValueError('Invalid bit length')
    return ''.join((f'{b:08b}' for b in raw))[:value['bit_length']]
