"""Inspect actual v4 resources state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('resources', {'status':'awaiting runtime'})
print(result)
