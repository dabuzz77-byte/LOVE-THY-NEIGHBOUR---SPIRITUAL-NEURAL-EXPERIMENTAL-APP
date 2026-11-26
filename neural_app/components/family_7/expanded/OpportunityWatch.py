"""Inspect actual v4 watch state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('watch', {'status':'awaiting runtime'})
print(result)
