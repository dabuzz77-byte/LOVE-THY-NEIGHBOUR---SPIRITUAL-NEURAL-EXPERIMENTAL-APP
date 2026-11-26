"""Original wheat/chaff text rules as inspectable lexical flags."""
from elevation import evaluate

inputs = {'payload': {}}
result = evaluate('sifter', inputs['payload'], globals().get('OBSERVATORY_SOURCES', []))
print(result)
