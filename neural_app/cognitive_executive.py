"""Persistent native goal planner, evidence graph and checked skill learning."""
import collections, copy, hashlib, json, re, time, uuid
from .mind_workspace import terms

OPS={'calculate','sort','unique','analyze','read','check','search','research','project','diagnose','reverse','upper','lower','statistics','test_python','debug_python','build_project','test_project','prepare_changes','constraints'}

def split_steps(text):
 parts=[];start=0;quote=False;escaped=False;stack=[];i=0
 while i<len(text):
  ch=text[i]
  if quote:
   if escaped:escaped=False
   elif ch=='\\':escaped=True
   elif ch=='"':quote=False
  elif ch=='"':quote=True
  elif ch in '[{(':stack.append(ch)
  elif ch in ']})':
   if not stack or '[{('.index(stack[-1])!=']})'.index(ch):raise ValueError('Unbalanced data delimiters in goal')
   stack.pop()
  elif not stack:
   match=re.match(r'\s+then\s+|\n',text[i:],re.I)
   if match:parts.append(text[start:i]);i+=len(match[0]);start=i;continue
  i+=1
 if quote or stack:raise ValueError('Close quoted or bracketed data before continuing the goal')
 parts.append(text[start:]);return parts
class CognitiveExecutive:
 def __init__(self,workbench):
  self.w=workbench;self.r=workbench.r;self.lock=workbench.lock;self.last_tick=0;self.inflight=set()
  self.s=self.r.s.setdefault('executive',{})
  for key,value in {'goals':[],'episodes':[],'skills':{},'nodes':{},'edges':[],'sequence':0,'predictions':{'tested':0,'correct':0},'model_calls':0}.items():self.s.setdefault(key,value)
  for goal in self.s['goals']:
   if goal['status']=='running':goal['status']='paused';goal['recovery']='Restart interrupted this goal. Resume explicitly; completed results are retained.'
   for step in goal['steps']:
    if step['status']=='running':step.update(status='pending',interrupted=True)
 def put(self,kind,value,source):
  digest=hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest();key=kind+':'+digest
  self.s['nodes'][key]={'id':key,'kind':kind,'value':value,'source':source,'time':time.time()}
  while len(self.s['nodes'])>256:self.s['nodes'].pop(next(iter(self.s['nodes'])))
  return key
 def link(self,a,relation,b):
  self.s['edges']=(self.s['edges']+[{'from':a,'relation':relation,'to':b}])[-512:]
 def retrieve(self,query):
  q=terms(query);rows=[]
  for episode in self.s['episodes']:
   score=len(q&terms(episode['goal']+' '+episode['input']))
   if score:rows.append((score,{**episode,'experience_status':'verified completion' if episode.get('verified') else 'failed attempt; inspect before reuse'}))
  for node in self.s['nodes'].values():
   if node['kind']!='generated-candidate':continue
   value=node['value'];score=len(q&terms(value.get('goal','')+' '+value.get('source','')))
   if score:rows.append((score,{'kind':'generated-candidate','verified':False,'source':node['source'],'candidate':value,'scope':'Unverified generated pattern; usable as a hypothesis, not a completed procedure'}))
  return [e for _,e in sorted(rows,key=lambda row:-row[0])[:5]]
 def parse(self,text):
  steps=[]
  for part in split_steps(text):
   part=part.strip()
   if not part:continue
   part=re.sub(r'^(?:please\s+|could you\s+|can you\s+)','',part,flags=re.I)
   part=re.sub(r'^(?:compute|evaluate)\s+','calculate ',part,flags=re.I)
   for phrase,operation in [('test python function','test_python'),('test python project','test_project'),('prepare project changes','prepare_changes'),('solve constraints','constraints'),('debug python','debug_python'),('build workflow project','build_project')]:part=re.sub('^'+phrase+r'(?:\s*:\s*|\s+)',operation+' ',part,flags=re.I)
   relative=re.fullmatch(r'(multiply|divide) (?:that|it|the result|result) by (.+)',part,re.I)
   additive=re.fullmatch(r'(add|subtract) (.+) (?:to|from) (?:that|it|the result|result)',part,re.I)
   if relative or additive:
    if not steps:raise ValueError('A relative step requires an earlier result')
    verb=relative[1].lower() if relative else additive[1].lower();operand=relative[2] if relative else additive[2];symbol={'multiply':'*','divide':'/','add':'+','subtract':'-'}[verb]
    part='calculate ({{previous}}) '+symbol+' ('+operand+')'
   if part.lower() in ('inspect project','project overview'):op,arg='project',''
   elif part.lower() in ('diagnose system','diagnostics'):op,arg='diagnose',''
   else:
    m=re.match(r'^('+'|'.join(sorted(OPS))+r')(?:\s*:\s*|\s+|$)([\s\S]*)$',part,re.I)
    if not m:raise ValueError('Use a supported step: calculate, sort, unique, analyze, read, check, search, research, project or diagnose. Join steps with “then”.')
    op,arg=m[1].lower(),m[2].strip()
   if op not in ('project','diagnose') and not arg:raise ValueError('Step needs input: '+op)
   if len(steps)>=12:raise ValueError('Use up to 12 steps per goal')
   steps.append({'operation':op,'input':arg,'status':'pending','attempts':0,'depends_on':len(steps)-1 if steps else None,'completion_condition':{'constraints':'feasible assignment independently checked; optimum claimed only on complete search','test_project':'selected local helper graph passes all supplied cases','prepare_changes':'multi-file proposal passes staged pure-function tests; originals unchanged','test_python':'all supplied function cases pass in bounded interpreter','debug_python':'test-validated repair proposal or already-passing report','build_project':'standalone project prepared with passing function cases','calculate':'finite native arithmetic result','sort':'same lines in sorted order','unique':'first occurrence of each line','read':'content hash matches workspace file','check':'parser or compiler check passed','analyze':'pattern metrics cover bounded captured input','search':'indexed matches returned with retrieval status','research':'source-labelled evidence returned with retrieval status','project':'workspace inventory returned','diagnose':'system diagnostic report returned','reverse':'text reverses back to original','upper':'Unicode uppercase transform','lower':'Unicode lowercase transform','statistics':'finite numeric summary and independent count, sum and extrema checks'}[op]})
  if not steps:raise ValueError('Provide a goal')
  return steps
 def submit(self,text):
  return self.create(text,self.parse(text))
 def create(self,text,steps):
  ident=uuid.uuid4().hex;node=self.put('goal',text,'user')
  goal={'id':ident,'node':node,'goal':text,'status':'running','steps':steps,'created':time.time(),'related_experience':self.retrieve(text),'planner':'native typed decomposition','roles':{'planner':'decompose goal and predict','executor':'existing native work skills','verifier':'operation-specific result checks'}}
  from .branch_reasoning import branches
  goal['world_model']=branches(steps,{'cosmological_chain':self.w.context() if hasattr(self.w,'context') else {},'related_experience':goal['related_experience']})
  self.s['goals']=(self.s['goals']+[goal])[-16:];self.r.controller.save();return goal
 def reuse(self,body):
  if not isinstance(body,dict) or not isinstance(body.get('input'),str) or len(body['input'])>8192:raise ValueError('Supply fresh text input up to 8192 characters')
  with self.lock:
   source=next((g for g in reversed(self.s['goals']) if g['status']=='complete' and (not body.get('goal_id') or g['id']==body['goal_id'])),None)
   pure={'calculate','reverse','upper','lower','sort','unique','statistics','analyze'}
   if source is None or not all(s['operation'] in pure and s['status']=='verified' for s in source['steps']):raise ValueError('Choose a completed pure-data goal; host, model and source actions are not replayed')
   steps=[{k:copy.deepcopy(s[k]) for k in ('operation','input','depends_on','completion_condition')} for s in source['steps']]
   for step in steps:step.update(status='pending',attempts=0)
   steps[0]['input']=body['input'];ident=source['id']
   goal=self.create('Reuse checked goal '+ident+' with fresh input',steps)
   goal['reused_from']=ident;goal['reuse_scope']='Same pure procedure, fresh input; every result is checked again. This is not an assertion of correctness before execution.'
   self.r.controller.save();return goal
 def perform(self,op,arg):
  from .native_skills import calculate
  if op in ('constraints','test_project','prepare_changes'):
   return self.w.handle({'constraints':'solve constraints: ','test_project':'test python project: ','prepare_changes':'prepare project changes: '}[op]+arg)
  if op=='test_python':
   if json.loads(arg).get('path'):return self.w.handle('test python function: '+arg)
   from .function_testing import test_function
   return test_function(json.loads(arg))
  if op in ('debug_python','build_project'):return self.w.handle(('debug python: ' if op=='debug_python' else 'build workflow project: ')+arg)
  if op=='calculate':return calculate(arg)
  if op=='reverse':return arg[::-1]
  if op=='upper':return arg.upper()
  if op=='lower':return arg.lower()
  if op=='statistics':
   from .data_skills import numeric_stats
   return numeric_stats(arg)
  if op=='sort':return sorted(arg.splitlines())
  if op=='unique':return list(dict.fromkeys(arg.splitlines()))
  if op=='analyze':
   from .grounded_reasoner import pattern_test
   return pattern_test(arg)
  if op=='read':return self.w.tools().read({'path':arg})
  if op=='check':return self.w.check_file(arg)
  if op=='search':return self.w.search(arg)
  if op=='research':return self.w.evidence(arg)
  if op=='project':return self.w.project()
  if op=='diagnose':return self.w.diagnostics()
  raise ValueError('Unsupported operation')
 def verify(self,op,arg,value):
  # Separate predicates check the returned result; success is not a routing receipt.
  import math
  if op=='constraints':return value.get('verified') is True and value.get('status') in ('feasible','optimal')
  if op=='test_project':return value.get('all_passed') is True and value.get('passed')==len(json.loads(arg)['cases'])
  if op=='prepare_changes':return value.get('status')=='prepared' and all(test.get('all_passed') is True for test in value.get('tests',[])) and value.get('source_files_changed') is False
  if op=='test_python':return value.get('all_passed') is True and value.get('passed')==len(json.loads(arg)['cases'])
  if op=='debug_python':return (value.get('status')=='validated-proposal' and value.get('training',{}).get('all_passed') is True and value.get('validation',{}).get('all_passed') is True) or (value.get('status')=='already-passing' and value.get('baseline',{}).get('all_passed') is True)
  if op=='build_project':return value.get('status')=='prepared' and value.get('tests',{}).get('all_passed') is True and set(value.get('files',{}))=={'main.py','test_main.py','README.md','project.json'}
  if op=='calculate':
   import ast
   from fractions import Fraction
   def rational(node):
    if isinstance(node,ast.Constant) and type(node.value) in (int,float):return Fraction(str(node.value))
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):return rational(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
    if isinstance(node,ast.BinOp):
     a,b=rational(node.left),rational(node.right)
     if isinstance(node.op,ast.Add):return a+b
     if isinstance(node.op,ast.Sub):return a-b
     if isinstance(node.op,ast.Mult):return a*b
     if isinstance(node.op,ast.Div):return a/b
     if isinstance(node.op,ast.Mod):return a%b
    raise ValueError('No independent arithmetic verifier for this expression')
   expected=rational(ast.parse(arg,mode='eval').body)
   return type(value) in (int,float) and math.isfinite(value) and math.isclose(value,float(expected),rel_tol=1e-12,abs_tol=1e-12)
  if op=='reverse':return isinstance(value,str) and value[::-1]==arg
  if op=='upper':return value==arg.upper() and value.upper()==value
  if op=='lower':return value==arg.lower() and value.lower()==value
  if op=='statistics':
   numbers=[float(x) for x in re.split(r'[\s,;]+',arg.strip()) if x]
   return isinstance(value,dict) and value.get('count')==len(numbers) and value.get('minimum')==min(numbers) and value.get('maximum')==max(numbers) and math.isclose(value.get('sum',math.nan),math.fsum(numbers),rel_tol=1e-12,abs_tol=1e-12) and math.isclose(value.get('mean',math.nan)*len(numbers),value['sum'],rel_tol=1e-12,abs_tol=1e-12)
  if op=='sort':return isinstance(value,list) and collections.Counter(value)==collections.Counter(arg.splitlines()) and all(a<=b for a,b in zip(value,value[1:]))
  if op=='unique':return value==list(dict.fromkeys(arg.splitlines()))
  if op=='read':return isinstance(value,dict) and hashlib.sha256(self.w.tools().path(arg).read_bytes()).hexdigest()==value.get('sha256')
  if op=='check':return isinstance(value,dict) and value.get('check',{}).get('passed') is True
  if op=='analyze':return isinstance(value,dict) and value.get('sha256')==hashlib.sha256(arg.encode('utf-8',errors='replace')).hexdigest() and value.get('characters')==min(1024,len(arg))
  return isinstance(value,(dict,list)) # Structural retrieval check, not factual adjudication.
 def prediction(self,op):
  skill=self.s['skills'].get(op,{});n=skill.get('attempts',0);p=(skill.get('successes',0)+1)/(n+2)
  return {'expected_success':p,'predict_success':p>=.5,'prior_attempts':n,'scope':'Empirical skill completion; not semantic truth probability'}
 def revise(self,index,text):
  if not self.s['goals']:raise ValueError('No goal to revise')
  goal=self.s['goals'][-1];steps=self.parse(text)
  if any(g==goal['id'] for g,i in self.inflight):raise ValueError('Wait for the current step to finish before revising it')
  if len(steps)!=1 or not 0<=index<len(goal['steps']):raise ValueError('Choose one existing step, numbered from 1')
  if any(s['status']!='verified' for s in goal['steps'][:index]):raise ValueError('Earlier dependencies must finish first')
  goal['steps'][index]=steps[0];goal['steps'][index]['depends_on']=index-1 if index else None
  for step in goal['steps'][index+1:]:
   step.update(status='pending',attempts=0)
   for key in ('result','error','decision','world_model_check','prediction','cost_ms'):step.pop(key,None)
  from .branch_reasoning import branches
  goal['world_model']=branches(goal['steps'],{'revision':True})
  goal['world_model']['actual_checks']=[{'step':i,'operation_verified':True,'prediction_matches':None,'prediction_status':'retained completed step'} for i,s in enumerate(goal['steps']) if s['status']=='verified']
  goal['status']='running';goal.pop('error',None);self.r.controller.save();return goal
 def control(self,action):
  with self.lock:
   if not self.s['goals']:raise ValueError('No goal exists yet')
   goal=self.s['goals'][-1]
   if action=='pause' and goal['status']=='running':goal['status']='paused'
   elif action=='cancel' and goal['status']!='complete':goal.update(status='cancelled',finished=time.time())
   elif action=='resume':
    if goal['status']!='paused':raise ValueError('Only a paused goal can be resumed; revise failed input or explicitly retry it')
    goal['status']='running'
   elif action=='retry':
    failed=next((s for s in goal['steps'] if s['status']=='failed'),None)
    if goal['status']!='needs-input' or failed is None:raise ValueError('No failed step is awaiting retry')
    if failed['attempts']>=3:raise ValueError('This step has failed three times; revise the input instead of repeating it')
    failed.update(status='pending');failed.pop('error',None);goal.update(status='running');goal.pop('error',None)
   elif action not in ('pause','cancel'):raise ValueError('Use pause, resume, retry or cancel')
   self.r.controller.save();return goal
 def tick(self,force=False):
  if self.r.user_active or (not force and time.monotonic()-self.last_tick<.5):return
  self.last_tick=time.monotonic()
  with self.lock:
   goal=next((g for g in reversed(self.s['goals']) if g['status']=='running'),None)
   if not goal:return
   if any(g==goal['id'] for g,i in self.inflight):return
   step=next((s for s in goal['steps'] if s['status']=='pending'),None)
   if not step:goal['status']='complete';return
   index=goal['steps'].index(step);arg=step['input']
   if index and goal['steps'][index-1]['status']!='verified':return
   if '{{previous}}' in arg:
    if not index:goal.update(status='needs-input',error='First step has no previous result');return
    prior=goal['steps'][index-1]
    if prior['status']!='verified':return
    v=prior['result'];arg=arg.replace('{{previous}}',v if isinstance(v,str) else json.dumps(v))
   circuit=getattr(getattr(self.r,'runtime',None),'cognitive_circuit',None)
   decision=circuit.deep_decision.decide(goal,self.s['skills']) if circuit and hasattr(circuit,'deep_decision') else None
   if decision and decision['selected']!='execute-next':
    if decision['selected']=='clarify':goal.update(status='needs-input',error='Decision review found an unresolved dependency; revise the task before continuing.')
    elif decision['selected']=='inspect-evidence':goal.update(status='needs-input',error='Decision review requires evidence or a corrected predicted failure before execution.')
    return
   step['decision']=decision
   step.update(status='running',attempts=step['attempts']+1,prediction=self.prediction(step['operation']));goal_id=goal['id'];self.inflight.add((goal_id,index))
  started=time.perf_counter();error=None;value=None
  try:
   value=self.perform(step['operation'],arg);ok=self.verify(step['operation'],arg,value)
   if not ok:error='Completion condition failed'
  except Exception as exc:ok=False;error=type(exc).__name__+': '+str(exc)[:300]
  with self.lock:
   self.inflight.discard((goal_id,index))
   step.update(status='verified' if ok else 'failed',result=value,error=error,cost_ms=(time.perf_counter()-started)*1000)
   if decision:circuit.deep_decision.observe(decision,ok,step['cost_ms'])
   from .branch_reasoning import check_actual
   if goal.get('world_model'):step['world_model_check']=check_actual(goal['world_model'],index,value,ok)
   skill=self.s['skills'].setdefault(step['operation'],{'attempts':0,'successes':0,'cost_ms':0});skill['attempts']+=1;skill['successes']+=int(ok);skill['cost_ms']+=step['cost_ms']
   self.s['predictions']['tested']+=1;self.s['predictions']['correct']+=int(step['prediction']['predict_success']==ok)
   event={'goal':goal['goal'],'input':arg[:2000],'operation':step['operation'],'verified':ok,'result':str(value)[:2000],'cost_ms':step['cost_ms'],'time':time.time()};self.s['episodes']=(self.s['episodes']+[event])[-128:]
   action=self.put('action',{'operation':step['operation'],'input':arg[:2000]},'native-planner');outcome=self.put('outcome',event,'native-verifier');self.link(goal['node'],'requests',action);self.link(action,'observed-result',outcome)
   if not ok and goal['status'] not in ('cancelled','paused'):goal.update(status='needs-input',error=error,recovery='Correct this step or explicitly retry it; completed steps remain recorded.')
   elif goal['status']=='running' and all(s['status']=='verified' for s in goal['steps']):goal['status']='complete';goal['finished']=time.time()
   if goal['status']=='complete' and hasattr(self.r,'selective_bridge'):self.r.selective_bridge.learn(goal)
   circuit=getattr(getattr(self.r,'runtime',None),'cognitive_circuit',None)
   if circuit:
    with circuit.lock:step['action_definition_check']=circuit.action_definitions.record('native/'+step['operation'],arg,value,ok,goal_id,stage='nativematrix')
   self.s['sequence']+=1;self.r.controller.save()
  self.w.record('executive-step',{'goal':goal_id,'step':index,'verified':ok,'operation':step['operation'],'cost_ms':step['cost_ms']})
  return event
 def view(self):
  with self.lock:return {'sequence':self.s['sequence'],'goals':self.s['goals'][-4:],'skills':self.s['skills'],'prediction_calibration':self.s['predictions'],'memory_nodes':len(self.s['nodes']),'memory_edges':len(self.s['edges']),'recent_experience':self.s['episodes'][-6:],'model_calls':self.s['model_calls'],'scope':'Native typed goal planning and checked execution; source retrieval checks are structural, not universal truth checks'}
