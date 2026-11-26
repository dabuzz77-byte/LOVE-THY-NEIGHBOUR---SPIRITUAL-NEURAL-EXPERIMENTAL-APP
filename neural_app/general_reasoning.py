"""Bounded reasoning with explicit assumptions, counterexamples and uncertainty."""
import copy,hashlib,itertools,json,math,time,re
from fractions import Fraction

def parse_logic(text):
 """Controlled English, preserving every clause; never silently drops words."""
 if not isinstance(text,str) or len(text)>8000:raise ValueError('Use up to 8000 characters of explicit premises and a query')
 def expression(source):
  tokens=re.findall(r'\(|\)|[^()\s]+',source);position=0
  if not tokens or len(tokens)>256:raise ValueError('Use 1–256 logical expression tokens')
  precedence={'iff':1,'implies':2,'or':3,'xor':3,'and':4}
  def read(minimum=1):
   nonlocal position
   if position>=len(tokens):raise ValueError('A logical operand is missing')
   token=tokens[position].casefold();position+=1
   if token=='not':left={'not':read(5)}
   elif token=='(':
    left=read()
    if position>=len(tokens) or tokens[position]!=')':raise ValueError('Close the logical parentheses')
    position+=1
   elif token in precedence or token==')':raise ValueError('A logical operand is missing')
   else:
    words=[tokens[position-1]]
    while position<len(tokens) and tokens[position].casefold() not in precedence and tokens[position] not in ('(',')'):
     if tokens[position].casefold()=='not':raise ValueError('Use an operator before not')
     words.append(tokens[position]);position+=1
    left=' '.join(words)
   while position<len(tokens):
    operator=tokens[position].casefold();level=precedence.get(operator,0)
    if level<minimum:break
    position+=1;right=read(level if operator=='implies' else level+1)
    left={ {'and':'all','or':'any'}.get(operator,operator):[left,right] }
   return left
  result=read()
  if position!=len(tokens):raise ValueError('Unparsed logical tokens remain; check parentheses and operators')
  return result
 clauses=[part.strip().rstrip('.') for part in re.split(r';|\n',text) if part.strip()]
 if not clauses or len(clauses)>65:raise ValueError('Supply semicolon-separated premises ending with Is ...? or Query: ...')
 query=re.fullmatch(r'(?:is\s+(.+?)\?|query:\s*(.+))',clauses[-1],re.I)
 if not query:raise ValueError('End with Is ...? or Query: ... so the intended conclusion is explicit')
 premises=[]
 for clause in clauses[:-1]:
  conditional=re.fullmatch(r'if (.+?) then (.+)',clause,re.I)
  if conditional:premises.append({'implies':[expression(conditional[1]),expression(conditional[2])]})
  else:premises.append(expression(re.sub(r'^either\s+','',clause,flags=re.I)))
 return {'mode':'deduction','premises':premises,'query':expression(query[1] or query[2]),'interpretation':'Controlled logic grammar: not, and, or, xor, implies, iff and parentheses; either/or is inclusive.'}

def budget(body):
 if not isinstance(body,dict):raise ValueError('Provide a reasoning object')
 if len(json.dumps(body,allow_nan=False))>32768:raise ValueError('Reasoning input exceeds 32 KB')

def atom(value):
 if not isinstance(value,str) or not value.strip() or len(value)>120:raise ValueError('Atoms need short nonempty text labels')
 return ' '.join(value.casefold().split())

def formula(node,atoms,counter,depth=0):
 counter[0]+=1
 if counter[0]>512 or depth>12:raise ValueError('Formula size or depth limit reached')
 if type(node)is bool:return ('constant',node)
 if isinstance(node,str):
  name=atom(node);atoms.add(name);return ('atom',name)
 if not isinstance(node,dict) or len(node)!=1:raise ValueError('Use atoms, booleans or a single logical operator')
 op,value=next(iter(node.items()))
 if op=='not':return (op,formula(value,atoms,counter,depth+1))
 if op not in ('all','any','implies','iff','xor') or not isinstance(value,list) or not 1<=len(value)<=16 or op in ('implies','iff','xor') and len(value)!=2:raise ValueError('Use all/any lists, not, or two-argument implies/iff/xor')
 return (op,tuple(formula(v,atoms,counter,depth+1) for v in value))

def truth(node,world):
 op,value=node
 if op=='constant':return value
 if op=='atom':return world[value]
 if op=='not':return not truth(value,world)
 if op=='all':return all(truth(v,world) for v in value)
 if op=='any':return any(truth(v,world) for v in value)
 a,b=(truth(v,world) for v in value)
 return (not a or b) if op=='implies' else a==b if op=='iff' else a!=b

def deduction(body):
 premises=body.get('premises',[])
 if not isinstance(premises,list) or len(premises)>64 or 'query' not in body:raise ValueError('Provide up to 64 premises and a query')
 atoms=set();counter=[0];compiled=[formula(p,atoms,counter) for p in premises];query=formula(body['query'],atoms,counter)
 if len(atoms)>12:raise ValueError('Exact logical reasoning supports at most 12 atoms')
 names=sorted(atoms);limit=body.get('world_limit',4096)
 if type(limit)is not int or not 1<=limit<=4096:raise ValueError('World limit must be 1 to 4096')
 total=2**len(names);examined=positive=negative=consistent=0;witness=counterexample=None;deadline=time.monotonic()+1
 for values in itertools.product((False,True),repeat=len(names)):
  if examined>=limit or time.monotonic()>deadline:break
  examined+=1;world=dict(zip(names,values))
  if not all(truth(p,world) for p in compiled):continue
  consistent+=1
  if truth(query,world):positive+=1;witness=witness or world
  else:negative+=1;counterexample=counterexample or world
 complete=examined==total
 status='inconsistent-premises' if complete and not consistent else 'contingent' if positive and negative else 'entailed' if complete and positive else 'refuted' if complete and negative else 'undetermined'
 return {'status':status,'atoms':names,'query':copy.deepcopy(body['query']),'premise_count':len(premises),'worlds_examined':examined,'total_worlds':total,'consistent_worlds_examined':consistent,'query_true_worlds_examined':positive,'query_false_worlds_examined':negative,'complete':complete,'supporting_world':witness,'counterexample_world':counterexample,'next_step':'Resolve conflicting premises before using the conclusion.' if status=='inconsistent-premises' else 'Obtain evidence that distinguishes the supporting world from its counterexample.' if status=='contingent' else 'Increase the bounded search or simplify the problem.' if status=='undetermined' else 'Check whether the supplied premises apply to the real task.','scope':'Finite classical propositional logic over explicit premises; inconsistent premises do not certify an arbitrary conclusion. Truth counts are not empirical probabilities.'}

def explanation(body):
 from .symbolic_reasoning import infer,literal,opposite
 facts=body.get('facts',[]);rules=body.get('rules',[]);observations=body.get('observations');hypotheses=body.get('hypotheses')
 if not isinstance(facts,list) or len(facts)>100 or not isinstance(observations,list) or not 1<=len(observations)<=16 or not isinstance(hypotheses,list) or not 1<=len(hypotheses)<=12:raise ValueError('Provide up to 100 facts, 1–16 observations and 1–12 candidate hypothesis literals')
 facts=[literal(v) for v in facts];observations=[literal(v) for v in observations];hypotheses=[literal(v) for v in hypotheses]
 if len(set(hypotheses))!=len(hypotheses) or any(h in facts for h in hypotheses):raise ValueError('Hypotheses must be distinct and not already given as facts')
 costs=body.get('costs',{});
 if not isinstance(costs,dict) or any(k not in hypotheses or type(v)not in (int,float) or not math.isfinite(v) or not 0<v<=1e6 for k,v in costs.items()):raise ValueError('Hypothesis costs must be positive finite values on declared labels')
 base=infer({'facts':facts,'rules':rules,'query':observations[0],'include_conclusions':True})
 if base['contradictions']:return {'status':'conflicting-premises','conflicts':base['contradictions'],'explanations':[],'complete':True,'next_step':'Resolve contradictory background facts or rules first.','scope':'Conflicting supplied background premises; no hypothetical cause certified.'}
 limit=body.get('subset_limit',4096)
 if type(limit)is not int or not 1<=limit<=4096:raise ValueError('Subset limit must be 1 to 4096')
 best=None;winners=[];ties=examined=0;deadline=time.monotonic()+1;complete=True
 for count in range(len(hypotheses)+1):
  for subset in itertools.combinations(hypotheses,count):
   if examined>=limit or time.monotonic()>deadline:complete=False;break
   examined+=1;cost=sum((Fraction(str(costs.get(h,1))) for h in subset),Fraction(0))
   if best is not None and cost>best:continue
   proof=infer({'facts':facts+list(subset),'rules':rules,'query':observations[0],'include_conclusions':True});known=set(proof['conclusions'])
   if proof['contradictions'] or not all(o in known for o in observations):continue
   if best is None or cost<best:best=cost;winners=[];ties=0
   ties+=1
   if len(winners)<16:winners.append({'assumptions':list(subset),'cost':float(cost),'consequences':sorted(known),'observations_supported':list(observations)})
  if not complete:break
 alternatives=[]
 if len(winners)>1:
  candidates=sorted(set.union(*(set(w['consequences']) for w in winners))-set(facts)-set(observations)-set(hypotheses))
  for candidate in candidates:
   positive=sum(candidate in w['consequences'] for w in winners)
   negative=sum(opposite(candidate) in w['consequences'] for w in winners)
   if 0<positive<len(winners):alternatives.append({'observation':candidate,'explanations_predicting_it':positive,'explanations_refuting_it':negative,'unknown_explanations':len(winners)-positive-negative,'explicit_disagreement':bool(positive and negative),'retained_explanations':len(winners)})
 alternatives.sort(key=lambda r:(not r['explicit_disagreement'],abs(r['explanations_predicting_it']-r['retained_explanations']/2)))
 for winner in winners:
  known=set(winner.pop('consequences'));winner['derived_closure_size']=len(known)
  winner['test_predictions']=[{'observation':test['observation'],'status':'supported' if test['observation'] in known else 'refuted' if opposite(test['observation']) in known else 'unknown'} for test in alternatives[:4]]
 return {'status':'explained' if winners else 'no-explanation' if complete else 'undetermined','explanations':winners,'best_cost':float(best) if best is not None else None,'minimum_cost_proven':bool(winners and complete),'equal_cost_explanation_count':ties,'explanations_truncated':ties>len(winners),'subsets_examined':examined,'complete':complete,'suggested_observations':alternatives[:4],'next_step':'Seek additional observations; absent predictions remain unknown and assumptions have not become facts.' if winners else 'Expand the hypothesis catalogue or correct the observations and rules.','scope':'Minimum-cost explanation within supplied monotonic rules and assumptions; neither a confirmed cause nor a probability. Suggested differences concern retained best explanations only. Missing predictions do not refute a hypothesis.'}

def probability(value):
 if type(value)not in (int,float) or not math.isfinite(value) or not 0<=value<=1:raise ValueError('Probabilities must be finite numbers from zero to one')
 return value

def entropy(values):return -math.fsum(p*math.log2(p) for p in values if p)

def likelihood_map(value):
 if not isinstance(value,dict) or len(value)>64:raise ValueError('Provide a bounded likelihood mapping')
 result={}
 for name,number in value.items():
  key=atom(name)
  if key in result:raise ValueError('Likelihood labels collide after normalisation')
  result[key]=probability(number)
 return result

def beliefs(body):
 hypotheses=body.get('hypotheses');evidence=body.get('evidence',[])
 if not isinstance(hypotheses,list) or not 2<=len(hypotheses)<=32 or not isinstance(evidence,list) or len(evidence)>32 or any(not isinstance(e,str) or not e or len(e)>120 for e in evidence) or len(set(evidence))!=len(evidence):raise ValueError('Provide 2–32 hypotheses and up to 32 distinct evidence labels')
 evidence=[atom(e) for e in evidence]
 if len(set(evidence))!=len(evidence):raise ValueError('Evidence labels must remain distinct after normalisation')
 if len(evidence)>1 and body.get('conditional_independence_assumed') is not True:raise ValueError('Multiple evidence items require an explicit conditional_independence_assumed:true model assumption')
 names=[];priors=[];logs=[]
 for row in hypotheses:
  if not isinstance(row,dict):raise ValueError('Each hypothesis needs name, prior and likelihoods')
  name=atom(row.get('name'));prior=probability(row.get('prior'));likelihoods=likelihood_map(row.get('likelihoods',{}))
  if name in names or not isinstance(likelihoods,dict):raise ValueError('Use unique hypothesis names and likelihood mappings')
  if any(atom(e) not in likelihoods for e in evidence):raise ValueError('Every hypothesis needs a likelihood for each evidence label')
  values=[likelihoods[atom(e)] for e in evidence];names.append(name);priors.append(prior)
  logs.append(math.log(prior)+sum(math.log(p) for p in values) if prior and all(values) else -math.inf)
 if not math.isclose(math.fsum(priors),1,rel_tol=0,abs_tol=1e-9):raise ValueError('Mutually exclusive exhaustive hypothesis priors must sum to one')
 maximum=max(logs)
 if maximum==-math.inf:return {'status':'impossible-evidence','posterior':None,'next_step':'The supplied likelihood model assigns zero probability to these observations; revise the model rather than invent a posterior.','scope':'Caller-supplied model; impossible evidence does not establish a real-world impossibility.'}
 weights=[math.exp(v-maximum) for v in logs];total=math.fsum(weights);posterior=[v/total for v in weights];tests=body.get('candidate_tests',[])
 if not isinstance(tests,list) or len(tests)>16:raise ValueError('Use up to 16 candidate binary tests')
 ranked=[];seen=set()
 for test in tests:
  if not isinstance(test,dict):raise ValueError('Each candidate test needs a name and positive_likelihoods')
  name=atom(test.get('name'));likelihoods=likelihood_map(test.get('positive_likelihoods'))
  if name in evidence:raise ValueError('An already observed evidence item is not a new candidate test')
  if name in seen or not isinstance(likelihoods,dict):raise ValueError('Candidate tests need distinct names and likelihood mappings')
  if any(n not in likelihoods for n in names):raise ValueError('Candidate tests need a likelihood for each hypothesis')
  seen.add(name);values=[likelihoods[n] for n in names];positive=math.fsum(p*v for p,v in zip(posterior,values));expected=0
  for outcome in (True,False):
   mass=positive if outcome else 1-positive
   if mass>0:expected+=mass*entropy([p*(v if outcome else 1-v)/mass for p,v in zip(posterior,values)])
  ranked.append({'test':name,'expected_information_bits':max(0,entropy(posterior)-expected),'positive_probability':positive})
 ranked.sort(key=lambda r:(-r['expected_information_bits'],r['test']))
 return {'status':'updated','posterior':[{'name':n,'prior':p,'posterior':q} for n,p,q in zip(names,priors,posterior)],'prior_entropy_bits':entropy(priors),'posterior_entropy_bits':entropy(posterior),'candidate_tests':ranked,'evidence':evidence,'conditional_independence_assumed':body.get('conditional_independence_assumed') is True,'next_step':'Measure a useful distinguishing test and check whether the likelihood model is justified.','scope':'Bayesian update under supplied mutually exclusive exhaustive hypotheses and likelihood assumptions; no empirical calibration or causal conclusion is established.'}

def reason(body):
 budget(body);started=time.perf_counter();mode=body.get('mode','deduction')
 if mode=='deduction':result=deduction(body)
 elif mode=='explanation':result=explanation(body)
 elif mode=='probability':result=beliefs(body)
 elif mode=='planning':
  from .reasoning_planner import plan
  result=plan(body)
 elif mode=='equations':
  from .linear_reasoning import solve
  result={**solve(body),'complete':True}
 elif mode=='decision':
  from .decision_reasoning import compare
  result=compare(body)
 elif mode=='case':
  from .reasoning_case import run
  result=run(body)
 elif mode=='relations':
  from .relational_reasoning import solve
  result=solve(body)
 elif mode=='reading':
  from .source_reasoning import read
  result=read(body)
 elif mode=='diagnostic':
  from .diagnostic_reasoning import diagnose
  result=diagnose(body)
 elif mode=='scenarios':
  from .scenario_reasoning import compare
  result=compare(body)
 elif mode=='units':
  from .quantity_reasoning import solve
  result=solve(body)
 elif mode=='written_quantities':
  from .written_quantities import solve
  result=solve(body)
 elif mode=='counterfactual':
  from .boolean_counterfactual import solve
  result=solve(body)
 elif mode=='causal_probability':
  from .causal_probability import solve
  result=solve(body)
 elif mode=='robustness':
  from .robustness_reasoning import audit
  result=audit(body)
 elif mode=='constraints':
  from .constraint_reasoning import solve
  result=solve(body)
 elif mode=='causal':
  from .reasoning_engine import causal
  result={**causal(body),'status':'model-evaluated','complete':True,'next_step':'Check the supplied equations and intervention assumptions against observations.'}
 else:raise ValueError('Choose deduction, explanation, probability, planning, equations, units, written_quantities, decision, case, relations, reading, diagnostic, scenarios, counterfactual, causal_probability, robustness, constraints or causal reasoning')
 result={**result,'mode':mode,'model_calls':0,'input_sha256':hashlib.sha256(json.dumps(body,sort_keys=True,allow_nan=False).encode()).hexdigest(),'elapsed_ms':round((time.perf_counter()-started)*1000,3)}
 if len(json.dumps(result,allow_nan=False))>131072:raise ValueError('Reasoning report exceeds 128 KB; use shorter labels or a smaller hypothesis catalogue')
 return result

def retain(state,body,result):
 state['general_reasoning_spec']=copy.deepcopy(body);state['general_reasoning_result']=copy.deepcopy(result)
 history=(state.get('general_reasoning_history',[])+[{'input':copy.deepcopy(body),'result':copy.deepcopy(result)}])[-8:]
 while len(history)>1 and len(json.dumps(history,allow_nan=False))>262144:history.pop(0)
 state['general_reasoning_history']=history

def summary(result):
 if not result:return None
 return {key:copy.deepcopy(result[key]) for key in ('mode','status','complete','minimum_cost_proven','next_step','input_sha256','scope','model_calls') if key in result}

def followup(text,result):
 if result and text.casefold().strip().rstrip('?.!') in ('explain result plainly','explain the result plainly'):
  from .result_explanation import explain
  return explain(result)
 if result and result.get('mode')=='causal_probability' and text.casefold().strip().rstrip('?.!') in ('what should i observe next','which observation would help'):
  if result.get('status')!='updated':return {'status':result['status'],'answer':result['next_step'],'action_repeated':False,'model_calls':0}
  name=result.get('suggested_observation');line=('Under this model, learning whether '+name+' is true has the greatest expected information gain for '+result['observation_target']+'.') if name else 'No available modeled probe adds information about the selected outcome under the current evidence.'
  return {'status':result['status'],'answer':line+'\n\n'+result['next_step'],'action_repeated':False,'model_calls':0}
 if not result or text.casefold().strip().rstrip('?.!') not in ('which sources support that','show source evidence','what remains uncertain','show reasoning summary'):return None
 lines=['Recorded '+str(result['mode'])+' reasoning: '+str(result.get('status','unknown'))+'.']
 if result['mode']=='reading' and text.casefold().strip().rstrip('?.!') in ('which sources support that','show source evidence'):
  graph=result.get('proof_graph',[]);sources={s['source'] for row in graph for s in row.get('given_sources',[])};rule_ids={row['proof']['rule'] for row in graph if row.get('proof',{}).get('kind')=='derived'}
  quoted=[row for row in result.get('source_statements',[]) if row['source'] in sources]+[row for row in result.get('source_rules',[]) if row['rule'] in rule_ids]
  lines+=['- '+row['source']+': '+row['text'][:500] for row in quoted[:20]] if quoted else ['No supporting source proof was established for that question.']
  if result.get('conflicts'):lines+=['The supplied evidence includes contradictions; review the proof and counter-proof together.']
 lines+=[result.get('next_step','Review the recorded inputs and results.'),result.get('scope','')]
 return {'status':result.get('status','unknown'),'answer':'\n\n'.join(lines),'action_repeated':False,'model_calls':0}

def request(text,previous=None):
 lower=text.casefold().strip();prefixes={'general reasoning:':None,'reason logically:':'deduction','compare explanations:':'explanation','update probabilities:':'probability','reason a plan:':'planning','compare choices:':'decision','reasoning case:':'case','reason over relations:':'relations','answer from source:':'reading','compare predictions:':'diagnostic','compare scenario outcomes:':'scenarios'}
 prefixes['analyse counterfactuals:']='counterfactual'
 prefixes['update causal probabilities:']='causal_probability'
 prefixes['check robustness:']='robustness'
 from .written_quantities import parse as written_problem
 written=written_problem(text)
 if written is not None:return written
 correction=re.fullmatch(r'change ([a-z][a-z0-9_]*) to (.+)',text.strip(),re.I|re.S)
 if correction and previous and previous.get('mode')=='written_quantities':return {**copy.deepcopy(previous),'overrides':{**previous.get('overrides',{}),correction[1].lower():correction[2].strip()}}
 if lower.rstrip('?.!') in ('what could change that conclusion','what would change that result','which premises matter','test nearby inputs'):
  from .robustness_reasoning import probes
  return probes(previous.get('task') if previous and previous.get('mode')=='robustness' else previous)
 if re.match(r'^(?:think causally:|causal assumptions:|assume\b)',text.strip(),re.I):
  from .causal_language import parse
  parsed=parse(text)
  if parsed is not None:return parsed
 hypothetical=re.fullmatch(r'what if ([a-z]\w*) (?:were|was|is) (true|false)\??',text.strip(),re.I)
 if hypothetical and previous and previous.get('mode') in ('counterfactual','causal_probability'):
  updated={**copy.deepcopy(previous),'interventions':[{'name':'follow_up','set':{hypothetical[1].lower():hypothetical[2].lower()=='true'}}],'question':text};updated.pop('question_expected_value',None);return updated
 observed=re.fullmatch(r'observe (?:that )?([a-z]\w*) (?:is|=) (true|false)\??',text.strip(),re.I)
 if observed and previous and previous.get('mode')=='causal_probability':
  name=observed[1].lower();value=observed[2].lower()=='true';evidence=copy.deepcopy(previous.get('observations',{}))
  if name in evidence and evidence[name]!=value:raise ValueError('This observation conflicts with retained evidence; explicitly revise the observations rather than silently replacing it')
  evidence[name]=value;return {**copy.deepcopy(previous),'observations':evidence}
 if lower.startswith(('calculate units:','convert units:')):
  from .quantity_reasoning import parse
  return parse(text.split(':',1)[1])
 conversion=re.fullmatch(r'convert that to (.+)',text.strip(),re.I)
 if conversion:
  if not previous or previous.get('mode') not in ('units','written_quantities'):raise ValueError('Calculate a quantity with units before converting its result')
  return {**copy.deepcopy(previous),'target':conversion[1].strip()}
 if lower.startswith(('from that source:','using those sources:')):
  if not previous or previous.get('mode')!='reading':raise ValueError('Supply a source-reading task before asking a source follow-up')
  return {**copy.deepcopy(previous),'question':text.split(':',1)[1].strip()}
 if lower.startswith('solve equations:'):
  from .linear_reasoning import parse
  return parse(text.split(':',1)[1])
 requested=re.fullmatch(r'(?:find|solve for|work out)\s+([A-Za-z_]\w*(?:\s*(?:,|and)\s*[A-Za-z_]\w*)*)\s*:\s*(.+)',text.strip(),re.I|re.S)
 if requested and '=' in requested[2] and not requested[2].lstrip().startswith(('[','{','"')):
  from .linear_reasoning import parse
  body=parse(requested[2]);targets=re.split(r'\s*(?:,|\band\b)\s*',requested[1],flags=re.I)
  if not set(targets)<=set(body['variables']):raise ValueError('A requested variable does not occur in the supplied equations')
  body['requested_variables']=targets;return body
 if lower.startswith('reason through:'):return parse_logic(text.split(':',1)[1])
 prefix=next((p for p in prefixes if lower.startswith(p)),None)
 if not prefix and not lower.startswith('revise reasoning:'):
  if re.match(r'^if\b',lower) and re.search(r'\bthen\b',lower):
   from .open_reasoning import natural_logic
   try:return natural_logic(text)
   except ValueError:return None
  return None
 body=json.loads(text.split(':',1)[1])
 if not isinstance(body,dict):raise ValueError('Provide a reasoning object')
 if lower.startswith('revise reasoning:'):
  if not previous:raise ValueError('Supply a general reasoning task before revising it')
  if 'mode' in body and body['mode']!=previous.get('mode','deduction'):raise ValueError('Start a fresh general reasoning task to change reasoning modes')
  return {**copy.deepcopy(previous),**body}
 if prefixes[prefix]:body['mode']=prefixes[prefix]
 return body
