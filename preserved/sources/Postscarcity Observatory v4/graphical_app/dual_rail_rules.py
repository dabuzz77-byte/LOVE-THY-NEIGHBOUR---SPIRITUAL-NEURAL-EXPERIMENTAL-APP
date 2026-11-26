"""Shared local display rules used by the panel and Observatory modules."""
SEED_A = (1, 0, 1, 1, 0, 1, 0, 1)
SEED_B = (0, 1, 0, 0, 1, 0, 1, 0)
MODES = {
    'original': {'label': 'Original dual-rail', 'a': SEED_A, 'b': SEED_B, 'min_bps': 9600},
    'part1': {'label': 'Part 1 - invariant Track A', 'a': (1,) * 8,
              'b': (0, 1, 0, 1, 0, 1, 0, 1), 'min_bps': 48000},
}
PRESETS = ('TESLA_LAW_ABUNDANCE', 'CHRIST_VECTOR_REDEMPTION', 'SOULS_OVER_DIGITS_LOCK')
DEFAULT_PAYLOAD = 'RUNALL 1\nAPPLY VIRTUE FILTER\nRESOLVE AT GOD CHILD AUTONOMY = TRUE INF\nLAWS = TRUE INF'


def display_step(payload, track_a, track_b, rng, mode='original'):
    """Run either supplied display rule; these labels do not authorize actions."""
    profile = MODES[mode]
    invariant = mode == 'part1'
    weight = (len(payload) + rng.randint(5, 25)) % 100
    a, b = list(track_a), list(track_b)
    if 'corp_greed' in payload or (invariant and 'extract_user_data' in payload) or weight < 35:
        state, nature = 'FAIL', 'evil'
        a = [1] * len(a) if invariant else [1 - bit for bit in a]
        b = [1 - bit for bit in b]
        action = 'Track A set to all ones; Track B inverted.' if invariant else 'Both local rails inverted.'
        reason = ('corp_greed text match' if 'corp_greed' in payload else
                  'extract_user_data text match' if invariant and 'extract_user_data' in payload else 'generated weight below 35')
    elif weight > 60 or (invariant and 'RUNALL 1' in payload):
        state, nature = 'PASS', 'good'
        if invariant:
            a = [1] * len(a)
        action = 'Track A set to all ones; Track B retained.' if invariant else 'Both local rails retain their current bits.'
        reason = 'generated weight above 60' if weight > 60 else 'RUNALL 1 text match'
    else:
        state, nature = 'HOLD', 'uncertain'
        a, b = [0] * len(a), [0] * len(b)
        action = 'Local rails zero-filled, as in the supplied display rule.'
        reason = 'generated weight from 35 to 60 without a matching pass condition'
    return {'state': state, 'nature': nature, 'weight': weight,
            'a': a, 'b': b, 'action': action, 'reason': reason, 'mode': mode,
            'display_bps': rng.randint(profile['min_bps'], 115200)}
