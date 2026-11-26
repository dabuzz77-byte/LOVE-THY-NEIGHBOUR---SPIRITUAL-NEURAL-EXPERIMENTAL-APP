"""Source-derived ternary calculation on supplied values."""
from python_hub import calculate
inputs = {'payload': {}}
result = calculate('ternary', inputs['payload']) if inputs['payload'] else {'status':'awaiting input'}
print(result)
