"""Inspect actual v4 ambient state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('ambient', {'status':'awaiting runtime'})
print(result)
