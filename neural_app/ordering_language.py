"""Finite ordering language mapped to fully enumerated, checked permutations."""
import itertools,re,time

def solve(text,parse_options,make_result):
 parsed=parse_options(text)
 if not parsed:return None
 body,choices=parsed
 inventory=re.search(r'\b(?:there (?:are|were)|sells) (three|five|seven) [^:]+:\s*(.+?)\.\s*([\s\S]+)',body,re.I)
 if not inventory:return None
 count={'three':3,'five':5,'seven':7}[inventory[1].lower()]
 names=[re.sub(r'^(?:a|an|the)\s+','',p.strip().casefold()) for p in re.split(r',\s*(?:and\s+)?|\s+and\s+',inventory[2]) if p.strip()]
 if len(names)!=count or len(set(names))!=count:return None
 # Increasing ranks mean older->newer, left->right, cheap->expensive, bottom->top,
 # or first->last for a race. Each paragraph must use one axis consistently.
 ranks={'oldest':('age',0),'newest':('age',-1),'second-newest':('age',-2),'second-oldest':('age',1),'third-newest':('age',-3),'third-oldest':('age',2),'leftmost':('horizontal',0),'rightmost':('horizontal',-1),'second from the left':('horizontal',1),'second from the right':('horizontal',-2),'third from the left':('horizontal',2),'third from the right':('horizontal',-3),'cheapest':('price',0),'most expensive':('price',-1),'second-cheapest':('price',1),'second-most expensive':('price',-2),'third-cheapest':('price',2),'third-most expensive':('price',-3),'top':('vertical',-1),'bottom':('vertical',0)}
 ordinals={'first':0,'second':1,'third':2,'fourth':3,'fifth':4,'sixth':5,'seventh':6,'last':-1}
 def position(rank):
  if not -count<=rank<count:raise ValueError('The named rank exceeds the number of declared objects')
  return rank%count
 relations={'older than':('age',-1),'newer than':('age',1),'to the left of':('horizontal',-1),'to the right of':('horizontal',1),'cheaper than':('price',-1),'more expensive than':('price',1),'above':('vertical',1),'below':('vertical',-1)}
 def noun(value):return re.sub(r'^the\s+','',value.strip().casefold())
 def claim(sentence):
  for phrase,(axis,sign) in relations.items():
   match=re.fullmatch(r'(.+?) (?:is|are) '+re.escape(phrase)+r' (.+)',sentence,re.I)
   if match and noun(match[1]) in names and noun(match[2]) in names:return {'axis':axis,'kind':'relative','a':noun(match[1]),'b':noun(match[2]),'sign':sign}
  match=re.fullmatch(r'(.+?) finished (above|below) (.+)',sentence,re.I)
  if match and noun(match[1]) in names and noun(match[3]) in names:return {'axis':'race','kind':'relative','a':noun(match[1]),'b':noun(match[3]),'sign':-1 if match[2].lower()=='above' else 1}
  match=re.fullmatch(r'(.+?) finished (\w+)',sentence,re.I)
  if match and noun(match[1]) in names and match[2].lower() in ordinals:return {'axis':'race','kind':'rank','a':noun(match[1]),'rank':position(ordinals[match[2].lower()])}
  match=re.fullmatch(r'(.+?) (?:is|are) (?:the |at the )?(.+)',sentence,re.I)
  if match and noun(match[1]) in names and match[2].lower() in ranks:
   axis,rank=ranks[match[2].lower()];return {'axis':axis,'kind':'rank','a':noun(match[1]),'rank':position(rank)}
  return None
 statements=[s.strip() for s in re.split(r'\.\s*',inventory[3]) if s.strip()];constraints=[claim(s) for s in statements];queries=[(letter,claim(s)) for letter,s in choices]
 if not constraints or any(c is None for c in constraints) or any(c is None for _,c in queries):return None
 if len({c['axis'] for c in constraints+[q for _,q in queries]})!=1:return None
 def holds(c,positions):return positions[c['a']]==c['rank'] if c['kind']=='rank' else positions[c['a']]<positions[c['b']] if c['sign']<0 else positions[c['a']]>positions[c['b']]
 models=[];deadline=time.monotonic()+1
 for order in itertools.permutations(names):
  if time.monotonic()>deadline:raise ValueError('Ordering search budget reached; no complete answer certified')
  positions={name:i for i,name in enumerate(order)}
  if all(holds(c,positions) for c in constraints):models.append(positions)
 if not models:return {'status':'inconsistent','answer':'The supplied ordering constraints conflict.','reasoning_family':'ordering','model_calls':0}
 selected=[letter for letter,q in queries if all(holds(q,m) for m in models)]
 if len(selected)!=1:return {'status':'needs-clarification','answer':'The constraints do not establish exactly one option.','models_remaining':len(models),'reasoning_family':'ordering','model_calls':0}
 return make_result('ordering','('+selected[0]+')',{'constraints':constraints,'consistent_orders':len(models),'witness_orders':models[:2]},'The selected option holds in every consistent ordering of the declared entities. Every statement after the inventory is parsed; unknown clauses or mixed ordering axes prevent an answer.')
