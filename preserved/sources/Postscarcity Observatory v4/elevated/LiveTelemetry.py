"""Inspect actual host state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('host', {'status':'awaiting runtime'})
print(result)
