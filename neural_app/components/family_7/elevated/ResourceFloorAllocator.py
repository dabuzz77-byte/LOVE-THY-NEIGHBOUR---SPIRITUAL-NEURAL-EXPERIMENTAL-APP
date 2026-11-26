"""Conserving allocation from available resources above protected donor floors."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('allocation', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
