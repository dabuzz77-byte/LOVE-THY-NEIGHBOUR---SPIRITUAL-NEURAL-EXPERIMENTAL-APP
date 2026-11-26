"""Inspect actual rules state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('rules', {'status':'awaiting runtime'})
print(result)
