"""Inspect actual wav state supplied by the Observatory runtime."""
from elevation import VIRTUE_RULES
result = globals().get('OBSERVATORY_RUNTIME', {}).get('wav', {'status':'awaiting runtime'})
print(result)
