"""Inspect actual journal state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('journal', {'status':'awaiting runtime'})
print(result)
