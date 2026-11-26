"""Composable pure work, explicit causal models and checked procedure transfer."""
import collections,copy,json,math,re,threading,time,uuid

def finite(v):
 if type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e100:raise ValueError('Use finite bounded numeric values')
 return v

def transform(value,step):
 if not isinstance(step,dict):raise ValueError('Each step must be an object')
 op=step.get('op')
 if op in ('add','scale','divide') and type(value) in (int,float):
  number=finite(value);operand=finite(step.get('value'))
  if op=='divide' and operand==0:raise ValueError('Cannot divide by zero')
  return finite(number+operand if op=='add' else number*operand if op=='scale' else number/operand)
 if op in ('strip','lower','upper','reverse','lines','words'):
  if not isinstance(value,str):raise ValueError(op+' requires text')
  return {'strip':lambda:value.strip(),'lower':lambda:value.lower(),'upper':lambda:value.upper(),'reverse':lambda:value[::-1],'lines':lambda:value.splitlines(),'words':lambda:re.findall(r"[^\W_]+",value,re.UNICODE)}[op]()
 if op=='json':return json.loads(value) if isinstance(value,str) else value
 if op=='csv':
  from .data_skills import csv_to_json
  return csv_to_json(value)
 if op=='take':
  count=step.get('count')
  if type(count) is not int or not 0<=count<=512 or not isinstance(value,(list,str)):raise ValueError('Take needs a count from 0 to 512 and a list or text')
  return value[:count]
 if op=='replace':
  if not all(isinstance(x,str) for x in (value,step.get('old'),step.get('new'))) or not step['old']:raise ValueError('Replace needs text and a nonempty search string')
  return value.replace(step['old'],step['new'])
 if op=='field':
  name=step.get('name')
  if not isinstance(name,str):raise ValueError('Field requires a name')
  return [r[name] for r in value] if isinstance(value,list) else value[name]
 if op=='group':
  if not isinstance(value,list) or len(value)>512:raise ValueError('Group requires at most 512 table rows')
  field=step.get('field');measure=step.get('value_field');aggregate=step.get('aggregate','count')
  if not isinstance(field,str) or aggregate not in ('count','sum','mean','minimum','maximum') or aggregate!='count' and not isinstance(measure,str):raise ValueError('Group needs a field, supported aggregate and numeric value_field except for count')
  groups={}
  for row in value:
   if not isinstance(row,dict) or not isinstance(row.get(field),str):raise ValueError('Every group key must be text in a table row')
   groups.setdefault(row[field],[]).append(1 if aggregate=='count' else finite(row[measure]))
  output=[]
  for key,items in groups.items():
   result=len(items) if aggregate=='count' else finite(math.fsum(items)) if aggregate=='sum' else finite(math.fsum(items)/len(items)) if aggregate=='mean' else min(items) if aggregate=='minimum' else max(items)
   output.append({'key':key,'value':result,'count':len(items)})
  return output
 if op in ('sort','unique','join','count','sum','mean','median','minimum','maximum','numbers','filter','scale','add','divide','frequencies'):
  if not isinstance(value,list) or len(value)>512:raise ValueError(op+' requires an array of at most 512 values')
  if op=='count':return len(value)
  if op=='join':return str(step.get('separator','\n'))[:100].join(map(str,value))
  if op=='unique':
   seen=set();out=[]
   for item in value:
    key=json.dumps(item,sort_keys=True,allow_nan=False)
    if key not in seen:seen.add(key);out.append(item)
   return out
  if op=='sort':return sorted(value,key=(lambda row:row[step['field']]) if step.get('field') is not None else None,reverse=bool(step.get('descending',False)))
  if op=='frequencies':return dict(collections.Counter(map(str,value)))
  if op=='numbers':return [finite(float(v)) for v in value]
  if op=='filter':
   target=step.get('value');relation=step.get('relation','equal');field=step.get('field')
   if relation not in ('equal','greater','less','at_least','at_most','contains'):raise ValueError('Choose equal, greater, less or contains')
   def keep(item):
    v=item[field] if field is not None else item
    return v==target if relation=='equal' else v>target if relation=='greater' else v<target if relation=='less' else v>=target if relation=='at_least' else v<=target if relation=='at_most' else target in v
   return [v for v in value if keep(v)]
  vals=[finite(v) for v in value]
  if op in ('scale','add','divide'):
   operand=finite(step.get('value'))
   if op=='divide' and operand==0:raise ValueError('Cannot divide by zero')
   return [finite(v*operand if op=='scale' else v/operand if op=='divide' else v+operand) for v in vals]
  if not vals:raise ValueError('Numeric aggregate needs at least one number')
  if op=='sum':return finite(math.fsum(vals))
  if op=='mean':return finite(math.fsum(vals)/len(vals))
  if op=='minimum':return min(vals)
  if op=='maximum':return max(vals)
  ordered=sorted(vals);n=len(vals);return ordered[n//2] if n%2 else finite((ordered[n//2-1]+ordered[n//2])/2)
 raise ValueError('Unknown pure operation: '+str(op))

def pipeline(value,steps,executor=None):
 from .native_operations import validate_steps
 validate_steps(steps)
 if len(json.dumps(value,allow_nan=False))>16384:raise ValueError('Input exceeds the bounded work size')
 from .workflow_contracts import verify
 original=copy.deepcopy(value);trace=[];execute=executor or transform
 for i,step in enumerate(steps):
  before=copy.deepcopy(value);value=execute(value,step)
  encoded=json.dumps(value,ensure_ascii=False,allow_nan=False)
  if len(encoded)>32768:raise ValueError('Intermediate result exceeds the bounded work size')
  checked=verify(before,step,value)
  if not checked:raise ValueError('Independent result check failed at step '+str(i+1)+' ('+str(step.get('op'))+')')
  trace.append({'step':i+1,'operation':step['op'],'parameters':{k:copy.deepcopy(v) for k,v in step.items() if k!='op'},'result':copy.deepcopy(value),'status':'verified','independent_check':True})
 return {'result':value,'input':original,'trace':trace,'verified':True,'model_calls':0,'scope':'Pure compositional data processing; no host commands'}

def causal(body):
 """Acyclic affine structural equations. Intervention replaces an equation."""
 base=body.get('values',{});equations=body.get('equations',{});change=body.get('intervention',{})
 if not all(isinstance(x,dict) for x in (base,equations,change)):raise ValueError('Use objects for values, equations and intervention')
 if len(base)+len(equations)>64 or set(base)&set(equations):raise ValueError('Use at most 64 distinct nodes')
 names=set(base)|set(equations)
 if not set(change)<=names:raise ValueError('Intervention names must exist in the model')
 for name in names:
  if not isinstance(name,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}',name):raise ValueError('Use simple node identifiers')
 for name,e in equations.items():
  if not isinstance(e,dict) or not isinstance(e.get('weights',{}),dict):raise ValueError('Each equation needs weights and an optional bias')
  if not set(e.get('weights',{}))<=names:raise ValueError('Unknown parent in causal equation')
  finite(e.get('bias',0))
  for v in e.get('weights',{}).values():finite(v)
 def run(overrides):
  values={k:finite(v) for k,v in base.items()};values.update({k:finite(v) for k,v in overrides.items()});pending=set(equations)-set(overrides)
  while pending:
   ready=sorted(k for k in pending if set(equations[k].get('weights',{}))<=set(values))
   if not ready:raise ValueError('Causal graph contains a cycle or unresolved parent')
   for k in ready:
    e=equations[k];values[k]=finite(math.fsum([e.get('bias',0)]+[w*values[p] for p,w in e.get('weights',{}).items()]));pending.remove(k)
  return values
 # Validate the original graph even when an intervention would hide a cycle.
 before=run({});after=run(change)
 return {'baseline':before,'intervened':after,'difference':{k:after[k]-before[k] for k in before},'assumptions':body.get('assumptions',[])[:16],'scope':'Consequences of supplied affine equations; not evidence that those equations describe the world','model_calls':0}

def synthesise(examples):
 from .program_search import search
 return search(examples)

class ReasoningEngine:
 def __init__(self,state,save=lambda:None,lock=None):
  self.lock=lock or threading.RLock();self.state=state;self.save=save;self.next_at=0;self.sequence=0;self.recent=collections.deque(maxlen=48);self.seen={};self.cursor=0;self.last_reviewed={};self.modulation={}
  from .core_modulators import CoreModulators
  self.wave=CoreModulators();self.wave.configure({'cmb_gain':.0001,'ohm_gain':.0006,'solfeggio_gain':.00005})
  if not isinstance(self.state.get('recipes'),dict):self.state['recipes']={}
  if not isinstance(self.state.get('relationships'),dict):self.state['relationships']={}
  if not isinstance(self.state.get('paired_observations'),dict):self.state['paired_observations']={}
  if not isinstance(self.state.get('jobs'),list):self.state['jobs']=[]
  self.state['jobs']=[j for j in self.state['jobs'][-32:] if isinstance(j,dict)]
  self.state['recipes']=dict(list(self.state['recipes'].items())[-64:])
  for job in self.state['jobs']:
   if job.get('status') in ('queued','running','waiting'):job.update(status='interrupted',error='Restarted before completion; submit again to rerun')
 def handle(self,text):
  from .investigation_dialogue import respond as investigation_response
  with self.lock:
   investigation=investigation_response(text,self.state)
   if investigation is not None:self.save();return investigation
  from .conversational_requests import normalize,questions
  text=normalize(text)
  from .native_work import NativeWork
  from .native_requests import resolve_clarification,compile_request,execute_request
  from .workflow_revision import respond as revise_workflow
  with self.lock:
   repair_work=NativeWork(self.state.get('native_tasks'))
   repaired=resolve_clarification(text,repair_work)
   if repaired is None:repaired=revise_workflow(text,repair_work)
   if repaired is None:
    from .table_work import respond as table_response
    repaired=table_response(text,repair_work)
   if repaired is None:
    candidate=compile_request(text,repair_work.state)
    if candidate and (candidate.get('clarification') or candidate.get('semantic_slots')):repaired=execute_request(candidate,repair_work)
   if repaired is not None:
    self.state['native_tasks']=copy.deepcopy(repair_work.state);self.save();return repaired
  parts=questions(text)
  if parts:text='Work request:\n'+'\n'.join(str(i)+'. '+part for i,part in enumerate(parts,1))
  from .study_reasoning import respond as study_response
  with self.lock:
   study=study_response(text,self.state)
   if study is not None:self.save();return study
  from .relational_induction import respond as relational_learning
  with self.lock:
   relation=relational_learning(text,self.state)
   if relation is not None:self.save();return relation
  if text.casefold().startswith(('teach native phrasing:','forget native phrasing ')) or text.strip().casefold()=='show learned native phrasings':
   from .native_language_transfer import engine_bridge
   with self.lock:
    learned=engine_bridge(text,self.state,True)
    if learned is not None:self.save();return learned
  from .concept_dialogue import respond as concept_respond
  with self.lock:
   concept=concept_respond(text,self.state)
   if concept is not None:self.save();return concept
  from .practical_decisions import respond as decision_conversation
  with self.lock:
   decision=decision_conversation(text,self.state)
   if decision is not None:self.save();return decision
  from .grounded_reading_dialogue import respond as reading_conversation
  with self.lock:
   reading=reading_conversation(text,self.state)
   if reading is not None:self.save();return reading
  from .conversation_navigation import respond as conversation_respond
  from .evidence_workbench import respond as evidence_respond
  from .validated_forecast import respond as forecast_respond
  with self.lock:
   for responder in (conversation_respond,evidence_respond,forecast_respond):
    result=responder(text,self.state)
    if result is not None:self.save();return result
   if self.state.get('focus_kind')=='open-reasoning' and re.match(r'^goal:\s*',text,re.I):
    from .open_reasoning import respond as open_goal_response
    opened=open_goal_response(text,self.state)
    if opened is not None:self.save();return opened
  from .reasoning_workspace import respond as workspace_respond
  with self.lock:
   workspace=workspace_respond(text,self.state)
   if workspace is not None:self.save()
  if workspace is not None:return workspace
  if text.casefold().strip().rstrip('?.!') in ('reasoning breadth report','broad reasoning assessment'):
   from .breadth_assessment import view
   return view()
  if text.casefold().strip().rstrip('?.!') in ('broad reasoning status','explain broad result') or text.casefold().strip().rstrip('?.!') in ('explain result plainly','explain the result plainly') and self.state.get('focus_kind')=='broad-reasoning':
   report=self.state.get('broad_reasoning_result')
   return {'status':report['status'],'answer':report['answer']+'\n\nRecorded computation:\n'+json.dumps(report.get('evidence',{}),ensure_ascii=False,indent=2),'action_repeated':False,'model_calls':0} if report else {'status':'needs-input','answer':'No broad-task result is retained.','model_calls':0}
  from .practical_dialogue import respond as practical_respond
  from .native_work import NativeWork
  with self.lock:
   practical_work=NativeWork(self.state.get('native_tasks'))
   for field in ('learned_relation_models','learned_native_phrases','suppressed_native_starters'):
    if field in self.state:practical_work.state[field]=copy.deepcopy(self.state[field])
   if self.state.get('focus_kind')=='study-analysis':
    practical_work.state.update({field:copy.deepcopy(self.state[field]) for field in ('study_analysis','study_input','focus_kind') if field in self.state})
   if self.state.get('focus_kind')=='investigation':
    practical_work.state.update({field:copy.deepcopy(self.state[field]) for field in ('investigation','focus_kind') if field in self.state})
   if text.strip().casefold().rstrip('?.!') in ('where are we','summarize current work','summarise current work') and self.state.get('focus_kind')=='general-reasoning':practical_work.state.update({k:copy.deepcopy(self.state[k]) for k in ('focus_kind','general_reasoning_result','reasoning_workspaces') if k in self.state})
   practical=practical_respond(text,practical_work)
   if practical is not None:
    self.state['native_tasks']=copy.deepcopy(practical_work.state)
    if practical.get('controller',{}).get('committed'):
     for field in ('investigation','study_analysis','study_input','concept_conversation','practical_decision','reading_dialogue','evidence_packet','evidence_report','validated_forecast','broad_reasoning_result','focus_kind','last','previous','has_last','learned_relation_models','learned_native_phrases','suppressed_native_starters'):
      if field in practical_work.state:self.state[field]=copy.deepcopy(practical_work.state[field])
    self.save()
  if practical is not None:return practical
  from .reference_language import clarify
  if text.strip().casefold().rstrip('?.!') in ('story reasoning report','narrative reasoning assessment'):
   from .narrative_assessment import view
   return view()
  clarified=clarify(text,self.state.get('broad_reasoning_result')) if self.state.get('focus_kind')=='broad-reasoning' else None
  if clarified is not None:
   with self.lock:self.state['broad_reasoning_result']=copy.deepcopy(clarified);self.save()
   return clarified
  from .broad_reasoning import respond as broad_respond
  broad=broad_respond(text,self.state.get('broad_reasoning_result') if self.state.get('focus_kind')=='broad-reasoning' else None)
  if broad is not None:
   with self.lock:self.state['broad_reasoning_result']=copy.deepcopy(broad);self.state['focus_kind']='broad-reasoning';self.save()
   return broad
  if self.state.get('focus_kind')=='general-reasoning':
   from .general_reasoning import followup
   recalled=followup(text,self.state.get('general_reasoning_result'))
   if recalled is not None:return recalled
  if text.casefold().strip().startswith(('run this function on:','write python expression:','run tasks:','preview tasks:','revise preview task ','test this code:')) or text.casefold().strip().rstrip('?.!') in ('run previewed tasks','cancel previewed tasks','show current code','show generated code') or text.casefold().strip().rstrip('?.!') in ('explain result plainly','explain the result plainly') and self.state.get('focus_kind')=='native-tasks' or re.fullmatch(r'(?:write|create|generate) (?:a )?python(?: function)? (?:to|for)\s+.+',text,re.I|re.S):
   from .native_work import NativeWork
   with self.lock:
    work=NativeWork(self.state.get('native_tasks'));result=work.handle(text)
    if result.get('status') in ('complete','planned','test-failed','cancelled'):self.state['native_tasks']=copy.deepcopy(work.state);self.state['focus_kind']='native-tasks';self.save()
   return result
  from .open_reasoning import respond as open_response
  with self.lock:
   opened=open_response(text,self.state)
   if opened is not None:self.save()
  if opened is not None:return opened
  from .general_reasoning import request,reason,summary,retain
  body=request(text,self.state.get('general_reasoning_spec'))
  if body is not None:
   result=reason(body)
   with self.lock:
    retain(self.state,body,result);self.state['focus_kind']='general-reasoning'
    self.recent.append({'kind':'general-reasoning','time':time.time(),'result':summary(result)});self.save()
   return result
  if text.casefold().strip() in ('general reasoning status','show reasoning assumptions'):return {'result':summary(self.state.get('general_reasoning_result')),'assumptions':copy.deepcopy(self.state.get('general_reasoning_spec'))}
  from .symbolic_reasoning import respond as symbolic_respond
  symbolic=symbolic_respond(text)
  if symbolic is not None:
   with self.lock:self.recent.append({'kind':'explicit-premise-reasoning','time':time.time(),'result':copy.deepcopy(symbolic)})
   return symbolic
  lower=text.lower()
  if lower.startswith('review harm claims:'):
   from .harm_claim_review import review
   return review(json.loads(text.split(':',1)[1]))
  if lower.startswith('review emergency delivery:'):
   from .emergency_review import review
   return review(json.loads(text.split(':',1)[1]))
  if lower.startswith('compare paired observations:'):
   from .paired_observations import compare as paired_compare
   body=json.loads(text.split(':',1)[1])
   if not isinstance(body,dict):raise ValueError('Provide a JSON object')
   return paired_compare(body)
  if lower.startswith('compare uncertain scenarios:'):
   from .robust_scenarios import compare as robust_compare
   body=json.loads(text.split(':',1)[1])
   if not isinstance(body,dict):raise ValueError('Provide a JSON object')
   return robust_compare(body)
  if lower=='audit model evidence':
   from .model_evidence import summary
   with self.lock:return summary(self.state['relationships'])
  if lower.startswith('exact calculate '):
   from .exact_numbers import calculate as exact_calculate
   return exact_calculate(text[len('exact calculate '):])
  for prefix,operation in [('compare workflows:','workflows'),('compare scenarios:','scenarios')]:
   if lower.startswith(prefix):
    from .decision_workspace import compare_workflows,compare_scenarios
    body=json.loads(text[len(prefix):])
    if not isinstance(body,dict):raise ValueError('Provide a JSON object')
    return (compare_workflows if operation=='workflows' else compare_scenarios)(body)
  if lower in ('reasoning engine','show reasoning engine'):return self.view()
  cancel=re.fullmatch(r'cancel workflow ([a-f0-9]{32})',lower)
  if cancel:
   with self.lock:
    job=next((j for j in self.state['jobs'] if j['id']==cancel[1]),None)
    if not job or job['status'] not in ('queued','waiting'):raise ValueError('Choose a queued or waiting workflow')
    job.update(status='cancelled',finished=time.time());self.save()
    return {'job_id':job['id'],'status':'cancelled'}
  if lower.startswith('compare strata:'):
   from .model_selection import stratified_comparison
   body=json.loads(text.split(':',1)[1])
   if not isinstance(body,dict):raise ValueError('Provide a JSON object')
   return stratified_comparison(body)
  for prefix,mode in [('fit relationship:','fit'),('predict relationship:','predict'),('causal sensitivity:','sensitivity'),('intervention study:','intervention')]:
   if lower.startswith(prefix):
    from .empirical_learning import fit,predict,sensitivity,intervention_study
    body=json.loads(text[len(prefix):])
    if not isinstance(body,dict):raise ValueError('Provide a JSON object')
    if mode=='sensitivity':return sensitivity(body)
    if mode=='intervention':return intervention_study(body)
    if mode=='predict':
     with self.lock:model=copy.deepcopy(self.state['relationships'].get(body.get('name')))
     if model is None:raise ValueError('No retained measured relationship has that name')
     return predict(model,body.get('x'))
    name=body.get('name')
    if not isinstance(name,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',name):raise ValueError('Use a short relationship name')
    result=fit(body)
    with self.lock:
     self.state['relationships'][name]=result
     while len(self.state['relationships'])>32:self.state['relationships'].pop(next(iter(self.state['relationships'])))
     self.save();self.recent.append({'kind':'measured-relationship','name':name,'time':time.time(),'validated_against_baseline':result['validated_against_baseline']})
    return result
  for prefix,mode in [('workflow:','workflow'),('causal model:','causal'),('learn workflow:','learn'),('use workflow:','reuse'),('queue workflow:','queue')]:
   if lower.startswith(prefix):
    body=json.loads(text[len(prefix):])
    if not isinstance(body,dict):raise ValueError('Provide a JSON object')
    if mode=='causal':
     result=causal(body)
     with self.lock:self.recent.append({'kind':'causal-intervention','time':time.time(),'result':copy.deepcopy(result)})
     return result
    if mode=='learn':return self.learn(body)
    if mode=='reuse':
     recipe=self.state['recipes'].get(body.get('name'))
     if not recipe:raise ValueError('No verified workflow by that name')
     return {**pipeline(body.get('input'),recipe['steps']),'reused_workflow':body['name'],'training_examples':recipe['examples']}
    if mode=='queue':return self.submit_workflow(body)
    return pipeline(body.get('input'),body.get('steps'))
  numbers=re.fullmatch(r'(?:find |calculate |what is (?:the )?)?(average|mean|sum|median|minimum|maximum)(?: of)?(?: (positive|negative))?(?: numbers)?[: ]+([0-9.,;\s+\-]+)[?]?',text,re.I)
  if numbers:
   values=[finite(float(v)) for v in re.split(r'[,;\s]+',numbers[3].strip()) if v]
   steps=[]
   if numbers[2]:steps.append({'op':'filter','relation':'greater' if numbers[2].lower()=='positive' else 'less','value':0})
   steps.append({'op':'mean' if numbers[1].lower()=='average' else numbers[1].lower()})
   return pipeline(values,steps)
  # Natural compositional intent transfers installed operations to unseen text.
  match=re.fullmatch(r'(?:please )?(sort and deduplicate|deduplicate and sort|count unique words|count words|reverse and uppercase)(?: this text)?:\s*([\s\S]*)',text,re.I)
  if match:
   ops={'sort and deduplicate':['lines','unique','sort','join'],'deduplicate and sort':['lines','unique','sort','join'],'count unique words':['lower','words','unique','count'],'count words':['words','count'],'reverse and uppercase':['reverse','upper']}[match[1].lower()]
   return pipeline(match[2],[{'op':op} for op in ops])
  from .native_language_transfer import engine_bridge
  with self.lock:
   learned=engine_bridge(text,self.state)
   if learned is not None:self.save()
  if learned is not None:return learned
  from .native_reading_knowledge import respond as reading_knowledge
  with self.lock:
   reading=reading_knowledge(text,self.state)
   if reading is not None:self.save()
  return reading
 def submit_workflow(self,body):
  if len(json.dumps(body,allow_nan=False))>20000:raise ValueError('Queued work is too large')
  steps=body.get('steps');allowed={'strip','lower','upper','reverse','lines','words','json','csv','take','replace','field','sort','unique','join','count','sum','mean','median','minimum','maximum','numbers','filter','scale','add','divide','frequencies'}
  if not isinstance(steps,list) or not 1<=len(steps)<=12 or any(not isinstance(step,dict) or step.get('op') not in allowed for step in steps):raise ValueError('Use 1 to 12 registered pure operations')
  priority=body.get('priority',0)
  if type(priority) is not int or not 0<=priority<=5:raise ValueError('Priority must be an integer from 0 to 5')
  dependency=body.get('input_from')
  with self.lock:
   if dependency is not None and not any(j['id']==dependency for j in self.state['jobs']):raise ValueError('Dependency must name an existing workflow')
   if dependency is not None and 'input' in body:raise ValueError('Choose explicit input or input_from, not both')
   pending=[j for j in self.state['jobs'] if j.get('status') in ('queued','running','waiting')]
   if len(pending)>=32:raise ValueError('Work queue is full; wait for completion')
   job={'id':uuid.uuid4().hex,'status':'waiting' if dependency else 'queued','submitted':time.time(),'input':body.get('input'),'steps':copy.deepcopy(steps),'priority':priority,'input_from':dependency}
   required={j.get('input_from') for j in pending+[job]};finished=[j for j in self.state['jobs'] if j.get('status') not in ('queued','running','waiting')];retained={j['id']:j for j in finished[-16:]}
   retained.update({j['id']:j for j in finished if j['id'] in required});self.state['jobs']=list(retained.values())+pending+[job];self.save()
  return {'job_id':job['id'],'status':job['status'],'priority':priority,'input_from':dependency}
 def plan_and_run(self,text):
  from .native_task_planner import compile_goal
  plan=compile_goal(text)
  if plan is None:return None
  if plan['status']!='planned':return plan
  try:result=pipeline(plan['input'],plan['steps'])
  except (TypeError,ValueError,KeyError,IndexError) as exc:return {'status':'needs-input','question':'Please check the data format or requested field: '+str(exc)[:180],'executed':False,'interpretation':plan['interpretation']}
  row={'kind':'goal-directed-work','time':time.time(),'interpretation':plan['interpretation'],'operations':[step['op'] for step in plan['steps']],'verified':result['verified']}
  with self.lock:self.recent.append(row)
  return {**result,'interpretation':plan['interpretation'],'planner':'native typed-goal compiler','status':'complete'}
 def learn(self,body):
  name=body.get('name');examples=body.get('examples');steps=body.get('steps')
  if not isinstance(name,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',name):raise ValueError('Use a short workflow name')
  if not isinstance(examples,list) or not 2<=len(examples)<=16:raise ValueError('Provide 2 to 16 input / expected examples')
  inferred=steps is None;attempts=0
  if inferred:steps,attempts=synthesise(examples)
  from .workflow_contracts import equivalent
  signatures=set()
  for example in examples:
   actual=pipeline(example['input'],steps)['result'];signatures.add(json.dumps(example['input'],sort_keys=True))
   if not equivalent(actual,example['expected']):raise ValueError('Workflow failed an expected-result example; nothing retained')
  if len(signatures)<(3 if inferred else 2):raise ValueError('Use distinct example inputs, including a separate held-out input for inferred workflows')
  with self.lock:
   self.state['recipes'][name]={'steps':copy.deepcopy(steps),'examples':len(examples),'time':time.time(),'inferred':inferred,'search_candidates':attempts,'scope':'Verified against supplied examples; new-input results still need task-specific checks'}
   while len(self.state['recipes'])>64:self.state['recipes'].pop(next(iter(self.state['recipes'])))
   self.save()
  return {'retained':name,'passed_examples':len(examples),'training_examples':len(examples)-1 if inferred else len(examples),'heldout_examples':1 if inferred else 0,'inferred':inferred,'steps':steps,'search_candidates':attempts,'scope':'Reusable verified composition, not model-weight training'}
 def learn_observed_pair(self,row):
  import hashlib
  grouped={}
  for fact in row.get('observations',[])[:12]:
   path=fact.get('path',[]);value=fact.get('value')
   if not isinstance(path,list) or not path or str(path[-1]).lower() not in ('x','y') or type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e12:continue
   parent=json.dumps(path[:-1],ensure_ascii=True);grouped.setdefault(parent,{})[str(path[-1]).lower()]=value
  for parent,pair in grouped.items():
   if set(pair)!={'x','y'}:continue
   identity=json.dumps([row.get('source'),parent]);name='observed_'+hashlib.sha256(identity.encode()).hexdigest()[:16];marker=[row.get('parent_event'),pair['x'],pair['y']]
   with self.lock:
    memory=self.state['paired_observations'].setdefault(name,{'x':[],'y':[],'last':None,'last_fit':0})
    if memory['last']==marker:continue
    memory['last']=marker;memory['x']=(memory['x']+[pair['x']])[-64:];memory['y']=(memory['y']+[pair['y']])[-64:]
    while len(self.state['paired_observations'])>16:self.state['paired_observations'].pop(next(iter(self.state['paired_observations'])))
    if len(memory['x'])<8 or time.time()-memory['last_fit']<10:continue
    memory['last_fit']=time.time()
    from .empirical_learning import fit
    try:model=fit({'x':memory['x'],'y':memory['y'],'family':'auto' if len(memory['x'])>=15 else 'linear','source':str(row.get('source'))+' / paired x-y capture'})
    except ValueError as exc:memory['status']=str(exc)[:160];continue
    model['captured_at']=time.time();model['origin']='automatic paired source captures';self.state['relationships'][name]=model;memory['status']='relationship evaluated on later captures';self.recent.append({'kind':'automatic-measured-relationship','name':name,'source':row.get('source'),'time':time.time(),'validated_against_baseline':model['validated_against_baseline']})
    while len(self.state['relationships'])>32:self.state['relationships'].pop(next(iter(self.state['relationships'])))
    self.save()
 def tick(self,c):
  if time.monotonic()<self.next_at or c.r.user_active:return
  self.next_at=time.monotonic()+.5
  with self.lock:
   for dependent in self.state['jobs']:
    if dependent.get('status')!='waiting':continue
    parent=next((j for j in self.state['jobs'] if j['id']==dependent.get('input_from')),None)
    if parent and parent['status']=='complete':dependent.update(status='queued',input=copy.deepcopy(parent['output']['result']))
    elif parent is None or parent['status'] in ('failed','cancelled','interrupted','blocked'):dependent.update(status='blocked',error='Required workflow did not complete successfully',finished=time.time())
   ready=[j for j in self.state['jobs'] if j['status']=='queued'];now=time.time()
   job=max(ready,key=lambda j:j.get('priority',0)+min(10,(now-j['submitted'])/30)) if ready else None
   if job:
    job['status']='running';started=time.perf_counter()
    try:job['output']=pipeline(job['input'],job['steps']);job['status']='complete'
    except Exception as e:job.update(status='failed',error=str(e)[:160])
    job['finished']=time.time();job['elapsed_ms']=round((time.perf_counter()-started)*1000,3);self.save();self.recent.append({'kind':'queued-work','id':job['id'],'status':job['status'],'time':time.time()})
  # Each selected stage executes a new pure computation, independently of open UI.
  with c.lock:rows=c.element_thinking.view()['layers']
  if rows:
   now=time.monotonic();wave=self.wave.sample();baseline=sorted(rows,key=lambda row:now-self.last_reviewed.get(row['id'],0)+min(2,row.get('attention',0)),reverse=True)
   ordered=sorted(baseline,key=lambda row:now-self.last_reviewed.get(row['id'],0)+min(2,row.get('attention',0))+wave['applied']*math.sin(rows.index(row)+self.sequence),reverse=True)
   self.modulation={**wave,'unmodulated_selection':[row['id'] for row in baseline[:2]],'modulated_selection':[row['id'] for row in ordered[:2]],'role':'Tiny scheduling tie variation; exact task inputs, answers and verification stay unmodulated'}
   for row in ordered[:2]:
    self.last_reviewed[row['id']]=now
    self.learn_observed_pair(row)
    marker=(row.get('source'),row.get('changes'))
    if self.seen.get(row['id'])==marker:continue
    self.seen[row['id']]=marker
    observation_engine=getattr(getattr(c,'active_thought',None),'engine',None)
    if observation_engine is None:continue
    computed=observation_engine.process(row);forecasts=computed.get('forecast_tests',[])
    if not forecasts:continue
    actual_tests=[f['previous_test'] for f in forecasts if f.get('previous_test') is not None]
    valid=all(math.isfinite(test['absolute_error']) and test['absolute_error']>=0 for test in actual_tests)
    self.sequence+=1;record={'kind':'automatic-stage-work','stage':row['id'],'source':row.get('source'),'parent_event':row.get('parent_event'),'result':{'streams':len(forecasts),'new_forecast_tests':len(actual_tests),'anomalies':sum(t['anomaly'] for t in actual_tests),'methods':[f['method'] for f in forecasts]},'verified':valid,'verification_scope':'Finite source-specific forecast bookkeeping; errors remain errors, not successful predictions','operation':'test and update source forecasts','time':time.time(),'sequence':self.sequence,'model_calls':0}
    with self.lock:self.recent.append(record)
    c.bus.publish({'origin':'native-reasoning-engine','target':'all','kind':'stage-output','payload':{**record,'processing_receipt':True,'predefined_text':True,'stochastic':False}})
 def brief(self):
  with self.lock:
   jobs=[]
   for job in self.state['jobs'][-8:]:
    value=job.get('output',{}).get('result');encoded=json.dumps(value,ensure_ascii=False)
    jobs.append({'id':job['id'],'operation':'data workflow','native_workflow':True,'status':job['status'],'priority':job.get('priority',0),'input_from':job.get('input_from'),'result':value if len(encoded)<2000 else {'preview':encoded[:2000],'truncated':True},'error':job.get('error'),'verified':job.get('output',{}).get('verified',False)})
   return {'jobs':jobs,'reusable_workflows':len(self.state['recipes']),'measured_relationships':len(self.state['relationships'])}
 def view(self):
  from .native_workbench import CHAIN
  from .model_evidence import summary
  with self.lock:return {'evidence_audit':summary(self.state['relationships']),'sequence':self.sequence,'recent':copy.deepcopy(list(self.recent)),'recipes':copy.deepcopy(self.state['recipes']),'measured_relationships':copy.deepcopy(self.state['relationships']),'paired_measurement_streams':{k:{'observations':len(v.get('x',[])),'status':v.get('status','waiting for eight paired captures')} for k,v in self.state['paired_observations'].items()},'jobs':[{k:copy.deepcopy(v) for k,v in j.items() if k not in ('input','steps')} for j in self.state['jobs']],'cosmological_chain':CHAIN,'modulation':copy.deepcopy(self.modulation),'capabilities':{'conversation':'Typed continuation, explanation continuity, reversible data steps and optional model-assisted dialogue','transfer':'Training-only parameter discovery and bounded composition search, with a distinct held-out input and checked reuse','symbolic_reasoning':'Explicit premises, chained proofs, contradictions and unknown conclusions','causal_reasoning':'Explicit interventions, range sensitivity, stratified comparisons and transparent scenario scoring','automatic_work':'Priority and dependency-aware workflows, cancellation, failure propagation and source-linked forecast tests'},'scope':'Compositional native workflows, explicit causal models and automatic registered-stage computations; no claim of general intelligence'}
