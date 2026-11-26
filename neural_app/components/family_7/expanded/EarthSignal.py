"""Inspect actual v4 earth state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('earth', {'status':'awaiting runtime'})
print(result)
