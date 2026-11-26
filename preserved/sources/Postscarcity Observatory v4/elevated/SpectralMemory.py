"""Inspect actual memory state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('memory', {'status':'awaiting runtime'})
print(result)
