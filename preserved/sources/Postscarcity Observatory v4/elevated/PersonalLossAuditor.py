"""Actual statement CSV parsing with decimal totals and visible invalid rows."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('loss_audit', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
