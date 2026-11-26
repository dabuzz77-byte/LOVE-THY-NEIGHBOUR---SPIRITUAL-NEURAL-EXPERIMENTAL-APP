"""Inspect actual agent state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('agent', {'status':'awaiting runtime'})
print(result)
