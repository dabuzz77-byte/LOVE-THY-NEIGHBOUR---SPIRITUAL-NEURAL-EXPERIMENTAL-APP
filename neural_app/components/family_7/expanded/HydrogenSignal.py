"""Inspect actual v4 hydrogen state, preserving its declared evidence scope."""
result = globals().get('OBSERVATORY_RUNTIME', {}).get('python', {}).get('hydrogen', {'status':'awaiting runtime'})
print(result)
