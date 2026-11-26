"""Inspect actual v4 sun state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('sun', {'status':'awaiting runtime'})
print(result)
