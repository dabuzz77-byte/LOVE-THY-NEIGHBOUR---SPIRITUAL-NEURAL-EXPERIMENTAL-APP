"""Inspect actual knowledge state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('knowledge', {'status':'awaiting runtime'})
print(result)
