"""Inspect actual core state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('core', {'status':'awaiting runtime'})
print(result)
