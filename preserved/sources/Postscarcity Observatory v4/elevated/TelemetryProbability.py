"""Normalized probabilities and entropy from supplied measured telemetry."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('distribution', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
