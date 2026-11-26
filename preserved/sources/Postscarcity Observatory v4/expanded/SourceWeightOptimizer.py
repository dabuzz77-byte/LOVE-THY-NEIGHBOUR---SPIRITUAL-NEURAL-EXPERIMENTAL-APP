"""Source-derived optimize calculation on supplied values."""
from python_hub import calculate
inputs = {'payload': {}}
result = calculate('optimize', inputs['payload']) if inputs['payload'] else {'status':'awaiting input'}
print(result)
