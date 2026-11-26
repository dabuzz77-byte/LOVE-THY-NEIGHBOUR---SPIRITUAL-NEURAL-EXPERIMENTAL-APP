"""Pure, question-specific experiments. No code execution, files or remote changes."""
import json,random

def choose(question):
 q=question.lower()
 if any(w in q for w in ('exact','integer','rounding','precision','rational','arithmetic')):return 'exact-arithmetic'
 if any(w in q for w in ('retry','duplicate','idempoten','delivery','network')):return 'retry-effects'
 if any(w in q for w in ('sort','order lines','sorting')):return 'sort-properties'
 if any(w in q for w in ('cpu','gpu','memory','resource','schedule','rate')):return 'resource-scheduling'
 if any(w in q for w in ('preserv','inver','encod','reverse','roundtrip','unicode')):return 'data-preservation'
 return None

def experiment(model,seed):
 rng=random.Random(seed);rows=[]
 if model=='exact-arithmetic':
  from fractions import Fraction
  cases=[(2**53+i,1) for i in range(1,21)]
  exact=sum(Fraction(a)+Fraction(b)==a+b for a,b in cases)
  floating=sum(Fraction.from_float(float(a)+float(b))==a+b for a,b in cases)
  rows=[{'hypothesis':'exact-rational-addition','passed':exact,'cases':len(cases)},{'hypothesis':'float-addition-is-always-exact','passed':floating,'cases':len(cases)}]
  conclusion='Exact rational results match integer arithmetic on these boundary cases; floating-point addition does not always do so.'
 elif model=='data-preservation':
  samples=['','line\nnext','日本語','0'*17+'1'*13]+[''.join(chr(rng.randrange(32,127)) for _ in range(rng.randrange(2,40))) for _ in range(16)]
  funcs={'json-roundtrip':lambda x:json.loads(json.dumps(x,ensure_ascii=True)),'reverse-twice':lambda x:x[::-1][::-1],'reverse-once':lambda x:x[::-1]}
  rows=[{'hypothesis':name,'passed':sum(fn(s)==s for s in samples),'cases':len(samples)} for name,fn in funcs.items()]
  conclusion='Exact preservation distinguishes reversible encoding from single reversal.'
 elif model=='sort-properties':
  samples=[[str(rng.randrange(10)) for _ in range(rng.randrange(2,40))] for _ in range(20)]
  funcs={'sort':sorted,'deduplicate':lambda x:sorted(set(x)),'reverse':lambda x:x[::-1]}
  rows=[{'hypothesis':name,'passed':sum(fn(x)==sorted(x) and sorted(fn(x))==sorted(x) for x in samples),'cases':len(samples)} for name,fn in funcs.items()];conclusion='Sorting must preserve multiplicities as well as order.'
 elif model=='retry-effects':
  for mode in ['append-every-retry','deduplicate-by-request-id']:
   passed=0
   for _ in range(20):
    ids=[rng.randrange(5) for _ in range(30)];actual=len(ids) if mode=='append-every-retry' else len(set(ids));passed+=actual==len(set(ids))
   rows.append({'hypothesis':mode,'passed':passed,'cases':20})
  conclusion='In this simulated receiver, deduplication prevents duplicate effects. Actual services need their own verification.'
 elif model=='resource-scheduling':
  pressures=[rng.uniform(0,1) for _ in range(20)]
  for mode in ['fixed-high','pressure-backoff']:
   waits=[.02 if mode=='fixed-high' or p<.85 else .5 for p in pressures]
   rows.append({'hypothesis':mode,'passed':sum(p<.85 or w>=.4 for p,w in zip(pressures,waits)),'cases':20})
  conclusion='Under the declared simulated pressure threshold, backoff respects the policy. This is not a hardware throughput benchmark.'
 else:raise ValueError('Unsupported model')
 return {'type':model,'seed':seed,'observations':rows,'conclusion':conclusion,'transfer':'Fresh generated cases test the same declared property; broader task transfer is not established.','scope':'Isolated software experiment; no real network or device intervention.'}
