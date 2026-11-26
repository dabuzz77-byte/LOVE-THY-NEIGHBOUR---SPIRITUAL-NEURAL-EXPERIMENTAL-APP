"""Inspect actual v4 mesh state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('mesh', {'status':'awaiting runtime'})
print(result)
