"""Inspect actual v4 planetary state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('planetary', {'status':'awaiting runtime'})
print(result)
