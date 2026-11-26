"""Declared outreach observations; delivery is not a proxy for harm prevented."""
from pathlib import Path
import json

STAGES=('delivered','opened','understood','reported_reconsideration','followed_up')

def context(body):
    observations=body.get('observations',{})
    if not isinstance(observations,dict) or set(observations)-set(STAGES):
        raise ValueError('Use only the listed aggregate observation fields')
    for value in observations.values():
        if type(value) is not int or not 0<=value<=1000000:
            raise ValueError('Observation counts must be integers from 0 to 1000000')
    # These stages need not be nested: separate samples may answer different
    # questions. Missing observations stay missing rather than becoming zeros.
    evidence=json.loads((Path(__file__).resolve().parents[1]/'references'/'critical-doctrine-review.json').read_text(encoding='utf-8'))
    return {'causal_path':['permitted delivery','attention','understanding','possible reconsideration','action or restraint','follow-up'],
            'observations':{stage:observations.get(stage) for stage in STAGES},
            'observation_basis':'User-declared aggregate counts; not independently verified.',
            'attribution':'Association is not proof that the app caused an outcome. No prevented-death or repentance count is inferred.',
            'content_review':evidence,
            'delivery_scope':'No external sending, recipient discovery or device access occurs in this calculation.'}
