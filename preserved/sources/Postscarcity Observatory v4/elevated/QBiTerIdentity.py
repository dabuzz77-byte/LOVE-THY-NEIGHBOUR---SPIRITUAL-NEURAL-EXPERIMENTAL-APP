"""Source clarity, Ennead thresholds and ternary distribution with a protected floor."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('identity', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
