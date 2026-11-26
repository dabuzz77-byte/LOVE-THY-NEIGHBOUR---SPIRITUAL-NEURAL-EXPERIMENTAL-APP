"""Original velocity variance and bounded coherence calculation."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('convergence', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
