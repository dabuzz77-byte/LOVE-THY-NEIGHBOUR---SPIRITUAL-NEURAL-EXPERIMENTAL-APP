"""Inspect actual v4 signals state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('signals', {'status':'awaiting runtime'})
print(result)
