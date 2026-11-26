"""Active, bounded hypothesis testing: ask for evidence rather than invent it."""
import copy,hashlib,itertools,json,math,time
from .native_synthesis import OPS,execute,bounded

def key(value):return json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False)

def create(body):
 if not isinstance(body,dict):raise ValueError('Provide name, examples, operations and optional probes')
 name=str(body.get('name','')).strip().casefold();rows=body.get('examples');ops=body.get('operations',['increment','double','absolute']);probes=body.get('probes',[-3,-1,0,1,2,3,5,8]);depth=body.get('max_depth',2)
 if not name or len(name)>80 or not isinstance(rows,list) or not 1<=len(rows)<=12:raise ValueError('Use a short name and 1–12 observed input/output pairs')
 if not isinstance(ops,list) or not 1<=len(ops)<=12 or any(op not in OPS for op in ops) or type(depth)is not int or not 1<=depth<=3:raise ValueError('Use registered operations and depth 1–3')
 if 'probes' not in body and rows and isinstance(rows[0],dict):
  sample=rows[0].get('input')
  if isinstance(sample,str):probes=['',' A ','b\na\nb','β','aa']
  elif isinstance(sample,list):probes=[[],[1,2],[-2,0],['b','a']]
 if not isinstance(probes,list) or not 1<=len(probes)<=12:raise ValueError('Supply 1–12 candidate probe inputs')
 checked=[]
 for row in rows:
  if not isinstance(row,dict) or 'input' not in row or 'output' not in row:raise ValueError('Examples require observed input and output')
  bounded(row['input']);bounded(row['output']);checked.append(copy.deepcopy(row))
 if len({key(r['input']) for r in checked})!=len(checked):raise ValueError('Initial observed inputs must be distinct')
 for value in probes:bounded(value)
 if len(key([checked,probes]))>32768:raise ValueError('Use an inquiry under 32 KB')
 count=sum(len(ops)**d for d in range(depth+1));programs=[[]]
 for d in range(1,depth+1):
  for program in itertools.islice(itertools.product(ops,repeat=d),max(0,256-len(programs))):programs.append(list(program))
  if len(programs)>=256:break
 return {'name':name,'observations':checked,'probes':copy.deepcopy(probes),'operations':list(ops),'max_depth':depth,'programs':programs,'catalogue_total':count,'catalogue_complete':len(programs)==count,'cursor':0,'survivors':[],'rejected':0,'phase':'enumerating','revision':0,'question':None,'comparisons':[],'history':[],'sequence':0,'model_calls':0,'scope':'Finite registered hypothesis catalogue; supplied observations are not independent proof of a world law.'}

def step(state,budget_ms=4):
 if state['phase']!='enumerating':return False
 started=time.perf_counter();changed=False
 while state['cursor']<len(state['programs']) and (time.perf_counter()-started)*1000<budget_ms:
  program=state['programs'][state['cursor']];state['cursor']+=1;changed=True
  try:consistent=all(type(actual:=execute(program,copy.deepcopy(row['input'])))==type(row['output']) and actual==row['output'] for row in state['observations'])
  except (ValueError,TypeError,OverflowError,RecursionError):consistent=False
  if consistent:state['survivors'].append(program)
  else:state['rejected']+=1
 if state['cursor']<len(state['programs']):return changed
 observed={key(row['input']) for row in state['observations']};comparisons=[]
 for probe in state['probes']:
  if key(probe) in observed:continue
  predictions=[]
  for program in state['survivors']:
   try:output=execute(program,copy.deepcopy(probe));error=None
   except (ValueError,TypeError,OverflowError,RecursionError) as exc:output=None;error=str(exc)[:120]
   predictions.append({'program':program,'prediction':output,'error':error})
  if any(row['error'] for row in predictions):continue
  bins={}
  for row in predictions:
   label=key({'value':row['prediction'],'error':row['error']});bins[label]=bins.get(label,0)+1
  total=max(1,len(predictions));gain=-sum((n/total)*math.log2(n/total) for n in bins.values())
  comparisons.append({'input':copy.deepcopy(probe),'distinct_predictions':len(bins),'disagreement_bits':gain,'predictions':[{'program':p['program'],'prediction_preview':str(p['prediction'])[:256],'prediction_sha256':hashlib.sha256(key(p['prediction']).encode()).hexdigest(),'error':p['error']} for p in predictions[:8]],'hypotheses_sampled':len(state['survivors'])})
 if len(state['survivors'])>1 and not any(r['disagreement_bits']>0 for r in comparisons) and not state.get('expanded_probe_revision')==state['revision']:
  sample=state['observations'][0]['input'];extra=[]
  if type(sample) in (int,float):extra=[-17,17,.5,-.5,101]
  elif isinstance(sample,str):extra=['  aB  ','aB\nBa','\tX\t','éΩ','ab cd']
  elif isinstance(sample,list):extra=[list(reversed(sample)),sample[:1]+sample[:1],[],[3,-1,3]]
  known={key(p) for p in state['probes']}|observed
  fresh=[p for p in extra if key(p) not in known]
  state['expanded_probe_revision']=state['revision']
  if fresh:
   state['probes']=(state['probes']+fresh)[-12:];state['auto_probe_source']='Deterministic input variations; no invented output observations'
   # All candidate fitting is retained. The next bounded tick scores the new probes.
   state['comparisons']=comparisons;return True
 state['sequence']+=1;state['comparisons']=comparisons
 if not state['survivors']:state['phase']='contradicted';state['question']='No candidate fits all observations. Which observation should be corrected, or which additional operation is needed?'
 elif len(state['survivors'])==1:state['phase']='consistent-candidate';state['question']='One candidate remains in the explored catalogue. Supply a fresh input/output observation to test it.'
 elif comparisons and max(row['disagreement_bits'] for row in comparisons)>0:
  best=max(comparisons,key=lambda row:row['disagreement_bits']);state['phase']='awaiting-observation';state['question']='What output is actually observed for input '+key(best['input'])+'? This separates '+str(best['distinct_predictions'])+' candidate predictions.';state['selected_probe']=best
 else:state['phase']='ambiguous';state['question']='Several candidates agree on the available probes. Supply a different probe or a new observed example.'
 state['history']=(state['history']+[{'revision':state['revision'],'tested':state['cursor'],'survivors':len(state['survivors']),'phase':state['phase'],'question':state['question'],'time':time.time()}])[-16:]
 return True

def answer(state,body):
 if not isinstance(body,dict) or 'input' not in body or 'output' not in body:raise ValueError('Supply the observed input and output')
 bounded(body['input']);bounded(body['output'])
 prospective=copy.deepcopy(state['observations'])
 existing=next((row for row in prospective if key(row['input'])==key(body['input'])),None)
 if existing:existing['output']=copy.deepcopy(body['output'])
 else:prospective.append({'input':copy.deepcopy(body['input']),'output':copy.deepcopy(body['output'])})
 if len(key([prospective,state['probes']]))>32768:raise ValueError('Inquiry observation storage budget reached')
 previous=next((row for row in state['observations'] if key(row['input'])==key(body['input'])),None)
 state.setdefault('evidence_updates',[])
 if previous:
  if not body.get('correct'):raise ValueError('That input is already observed; set correct:true to explicitly replace it')
  state['evidence_updates'].append({'input_sha256':hashlib.sha256(key(body['input']).encode()).hexdigest(),'previous_output_sha256':hashlib.sha256(key(previous['output']).encode()).hexdigest(),'new_output_sha256':hashlib.sha256(key(body['output']).encode()).hexdigest(),'explicit_correction':True,'time':time.time()})
  previous['output']=copy.deepcopy(body['output'])
 else:
  if len(state['observations'])>=16:raise ValueError('Observation budget reached')
  state['observations'].append({'input':copy.deepcopy(body['input']),'output':copy.deepcopy(body['output'])})
 state['evidence_updates']=state['evidence_updates'][-16:]
 state['revision']+=1;state['phase']='enumerating';state['cursor']=0;state['survivors']=[];state['rejected']=0;state['question']=None;state['comparisons']=[];state.pop('selected_probe',None)
 return state

def view(state):
 return {k:copy.deepcopy(v) for k,v in state.items() if k not in ('programs','comparisons')}|{'candidate_count':len(state['survivors']),'probe_comparisons':[{k:v for k,v in row.items() if k!='predictions'} for row in state['comparisons']],'inference_status':'Bounded hypothesis comparison; no external effect claimed'}

def explain(state,details=False):
 count=len(state['survivors']);lines=['**'+state['name']+'**', 'I compared '+str(state['cursor'])+' candidate programs against '+str(len(state['observations']))+' supplied observations. '+str(count)+' explanations remain consistent.']
 if state['question']:lines.append(state['question'])
 if state.get('selected_probe'):lines.append('I selected that probe because the compared candidates predict different outputs (disagreement '+str(round(state['selected_probe']['disagreement_bits'],3))+' bits within the sampled catalogue).')
 if details and count:
  words={'absolute':'take the absolute value','double':'double the input','negate':'change its sign','strip':'trim surrounding whitespace','lower':'convert to lowercase','upper':'convert to uppercase','reverse':'reverse the text','to-lines':'split into lines','join-lines':'join lines','unique':'remove duplicates','sort':'sort the values'}
  lines.append('Possible explanations:\n'+'\n'.join('- '+(' → '.join(words.get(op,op) for op in program) or 'preserve the input') for program in state['survivors'][:8]))
 lines.append('Scope: '+str(state['cursor'])+'/'+str(state['catalogue_total'])+' registered candidates explored. Agreement with these observations is not proof for arbitrary inputs.')
 return '\n\n'.join(lines)

def apply_candidate(state,value):
 if state['phase']!='consistent-candidate' or len(state['survivors'])!=1:raise ValueError('Resolve the candidate ambiguity before using its prediction')
 bounded(value);program=state['survivors'][0];output=execute(program,copy.deepcopy(value))
 return {'prediction':output,'input':copy.deepcopy(value),'program':copy.deepcopy(program),'checked_against_new_observation':False,'catalogue_complete':state['catalogue_complete'],'scope':'Prediction from the surviving candidate; no actual output observation was supplied for this new input.'}

def export_candidate(state):
 if state['phase']!='consistent-candidate' or len(state['survivors'])!=1:raise ValueError('A single consistent candidate is needed before code export')
 expressions={'strip':'value.strip()','lower':'value.lower()','upper':'value.upper()','reverse':'value[::-1]','to-lines':'value.splitlines()','join-lines':"'\\n'.join(value)",'sort':'sorted(value)','sort-numbers':'sorted(value)','increment':'value + 1','double':'value * 2','absolute':'abs(value)','negate':'-value','length':'len(value)','words':'value.split()','sum':'sum(value)','minimum':'min(value)','maximum':'max(value)'}
 lines=['def transform(value):']
 for operation in state['survivors'][0]:
  if operation in ('unique','unique-numbers'):lines+=['    kept = []','    for item in value:','        if item not in kept:','            kept.append(item)','    value = kept']
  elif operation in expressions:lines.append('    value = '+expressions[operation])
  else:raise ValueError('Candidate export does not support '+operation)
 lines.append('    return value');source='\n'.join(lines)+'\n'
 from .function_testing import test_function
 checks=test_function({'source':source,'function':'transform','cases':[{'args':[row['input']],'expected':row['output']} for row in state['observations']]})
 if not checks['all_passed']:raise ValueError('Exported candidate failed example checks; source withheld')
 return {'source':source,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'checks':checks,'scope':'Inferred pure-function proposal checked on supplied observations only. New-input predictions are not independently verified.'}
