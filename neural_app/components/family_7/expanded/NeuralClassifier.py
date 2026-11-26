"""Inspect actual v4 classifier state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('classifier', {'status':'awaiting runtime'})
print(result)
