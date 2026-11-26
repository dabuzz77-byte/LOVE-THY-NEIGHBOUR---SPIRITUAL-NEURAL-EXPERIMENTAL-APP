"""Original 15.5 loss-velocity multiplier as a recorded restoration proposal."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('restitution', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
