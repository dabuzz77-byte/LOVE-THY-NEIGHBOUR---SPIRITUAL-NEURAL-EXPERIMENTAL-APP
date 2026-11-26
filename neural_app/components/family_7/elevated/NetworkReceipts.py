"""Inspect actual connections state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('connections', {'status':'awaiting runtime'})
print(result)
