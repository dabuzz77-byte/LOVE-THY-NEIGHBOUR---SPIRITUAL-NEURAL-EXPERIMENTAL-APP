"""Evidence-linked development proposals and revisioned, executable native skills."""
import ast,copy,hashlib,json,re,threading,time,uuid
from pathlib import Path
from .function_testing import FunctionTest,test_function,data_budget
from .deliberation import Deliberation

DOCS=['https://docs.python.org/3/library/functions.html','https://docs.python.org/3/library/unittest.html']
RECIPES={
 'sort-numbers':['def transform(value):\n    return sorted(value)\n','def transform(value):\n    return value\n'],
 'trim-text':['def transform(value):\n    return value.strip()\n','def transform(value):\n    return value\n'],
 'sum-numbers':['def transform(value):\n    return sum(value)\n','def transform(value):\n    return len(value)\n'],
}

def digest(x):return hashlib.sha256(x.encode()).hexdigest()
def name(value):
 if not isinstance(value,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}',value):raise ValueError('Use a simple lowercase skill name')
 return value
def check_cases(rows):
 if not isinstance(rows,list) or not 2<=len(rows)<=12:raise ValueError('Each test split needs 2–12 cases')
 for row in rows:
  if not isinstance(row,dict) or not isinstance(row.get('args'),list) or 'expected' not in row:raise ValueError('Use args and expected in every case')
  data_budget(row)
 return copy.deepcopy(rows)

def accepted_cases(row):
 unique={}
 for case in row.get('retained_cases',[])+row['training']+row['validation']+row['regression']+row.get('runtime_cases',[]):
  key=json.dumps(case['args'],sort_keys=True)
  if key in unique and unique[key]['expected']!=case['expected']:raise ValueError('Installed acceptance cases conflict')
  unique[key]=copy.deepcopy(case)
 return list(unique.values())

def case_digest(rows):return digest(json.dumps(rows,sort_keys=True,allow_nan=False))

class SelfImprovementEngine:
 def __init__(self,data):
  self.root=Path(data)/'self-improvement';self.root.mkdir(exist_ok=True);self.path=self.root/'state.json';self.lock=threading.RLock();self.wake=threading.Event();self.worker=None;self.pending=[];self.bus_queue=[];self.next_scan=0
  self.s={'proposals':{},'active':{},'weaknesses':[],'sources':[],'learning_enabled':True,'auto_research':True,'last_error':None}
  if self.path.exists():
   try:self.s.update(json.loads(self.path.read_text(encoding='utf-8')))
   except (ValueError,OSError):pass
 def save(self):Deliberation.write_json(self.path,self.s)
 def note_failure(self,service,error=''):
  with self.lock:
   if not any(r['service']==service for r in self.s['weaknesses']):
    self.s['weaknesses'].append({'service':str(service)[:100],'first_seen':time.time(),'status':'needs-task-contract','error_sha256':digest(str(error)),'public_learning_topic':'Python error handling regression testing','next':'Provide a reproducing task and expected outcome; private errors are not sent as search queries.'})
    self.s['weaknesses']=self.s['weaknesses'][-32:];self.save()
  self.wake.set()
 def submit(self,b):
  skill=name(b.get('name'));train=check_cases(b.get('training'));valid=check_cases(b.get('validation'));reg=check_cases(b.get('regression'))
  signatures=[json.dumps(r['args'],sort_keys=True) for r in train+valid+reg]
  if len(set(signatures))!=len(signatures):raise ValueError('Training, validation and regression inputs must be distinct')
  candidates=b.get('candidates') or RECIPES.get(b.get('recipe'),[])
  if not isinstance(candidates,list) or not 1<=len(candidates)<=4 or any(not isinstance(x,str) or len(x)>16000 for x in candidates):raise ValueError('Provide 1–4 candidate functions or a registered recipe')
  function=b.get('function','transform')
  if not isinstance(function,str) or not function.isidentifier():raise ValueError('Invalid function name')
  for source in candidates:FunctionTest(source)
  with self.lock:
   active=copy.deepcopy(self.s['active'].get(skill))
   predecessor=copy.deepcopy(self.s['proposals'].get(active['proposal_id'])) if active else None
  retained=[]
  if active:
   baseline=(self.root/active['proposal_id']/'validated.py').read_text(encoding='utf-8')
   if digest(baseline)!=active['sha256']:raise ValueError('Installed baseline changed; restore it before proposing an upgrade')
   if predecessor['function']!=function:raise ValueError('An upgrade must retain the installed function contract')
   retained=accepted_cases(predecessor)
   if len(retained)>192:raise ValueError('Acceptance history exceeds this bounded skill; create a new skill contract')
  else:baseline=b.get('baseline','def transform(value):\n    return value\n')
  FunctionTest(baseline)
  ident=uuid.uuid4().hex;folder=self.root/ident;folder.mkdir()
  for i,source in enumerate(candidates):(folder/f'candidate-{i}.py').write_text(source,encoding='utf-8')
  (folder/'baseline.py').write_text(baseline,encoding='utf-8')
  row={'id':ident,'name':skill,'question':str(b.get('question','Improve the declared task'))[:300],'status':'queued','phase':'research','function':function,'candidates':candidates,'baseline':baseline,'training':train,'validation':valid,'regression':reg,'trace':[],'created':time.time(),'recipe':b.get('recipe'),'test_origin':'User-supplied acceptance cases; finite checks do not establish universal correctness.','auto_activate':b.get('auto_activate') is True}
  row.update(baseline_registration=active,retained_cases=retained,baseline_cases_sha256=case_digest(retained))
  with self.lock:
   if len(self.s['proposals'])>=24:raise ValueError('Proposal history is full; archive reviewed proposals first')
   self.s['proposals'][ident]=row;self.save()
  self.wake.set();return copy.deepcopy(row)
 def research(self,reader=None):
  from .knowledge_library import search
  references=search('Python pure function validation regression testing',4)
  rows=[]
  if self.s['auto_research']:
   from .reviewed_web import read_page
   reader=reader or read_page
   for url in DOCS:
    old=next((r for r in self.s['sources'] if r.get('url')==url and time.time()-r.get('fetched',0)<(3600 if r.get('status')=='retrieved' else 300)),None)
    if old:rows.append(old);continue
    try:
     page=reader(url);text=page['text'];rows.append({'url':url,'status':'retrieved','fetched':time.time(),'sha256':digest(text),'excerpt':text[:1600],'relation':'Reference material; never executable authority.'})
    except Exception as exc:rows.append({'url':url,'status':'unavailable','fetched':time.time(),'error':str(exc)[:180]})
  with self.lock:self.s['sources']=rows;self.save()
  return {'reference_matches':references,'online_sources':copy.deepcopy(rows)}
 def advance(self,ident,reader=None):
  with self.lock:
   row=copy.deepcopy(self.s['proposals'][ident])
  if row['status'] not in ('queued','running'):return row
  phase=row['phase'];record={'phase':phase,'time':time.time()};row['status']='running'
  try:
   if phase=='research':row['research']=self.research(reader);row['phase']='compare'
   elif phase=='compare':
    results=[test_function({'source':source,'function':row['function'],'cases':row['training']}) for source in row['candidates']]
    best=min(range(len(results)),key=lambda i:(-results[i]['passed'],len(row['candidates'][i]),i));row['comparison']=results;row['selected']=best;row['phase']='validate'
   elif phase=='validate':
    source=row['candidates'][row['selected']];result=test_function({'source':source,'function':row['function'],'cases':row['validation']});baseline=test_function({'source':row['baseline'],'function':row['function'],'cases':row['validation']});regression=test_function({'source':source,'function':row['function'],'cases':row['regression']})
    retained=row.get('retained_cases',[])
    historical=[test_function({'source':source,'function':row['function'],'cases':retained[i:i+12]}) for i in range(0,len(retained),12)]
    row['checks']={'validation':result,'baseline_validation':baseline,'regression':regression,'historical_regression':historical,'training':row['comparison'][row['selected']],'selection_frozen_before_validation':True};row['phase']='stage'
    if not result['all_passed'] or not regression['all_passed'] or not row['checks']['training']['all_passed'] or result['passed']<=baseline['passed']:row.update(status='rejected',reason='Candidate must pass all splits and strictly improve held-out correctness over baseline. Validation cannot select a replacement.')
    if any(not check['all_passed'] for check in historical):row.update(status='rejected',reason='Candidate breaks an earlier accepted skill behaviour.')
   elif phase=='stage':
    source=row['candidates'][row['selected']];row['source_sha256']=digest(source);folder=self.root/ident;(folder/'validated.py').write_text(source,encoding='utf-8');row.update(status='ready',phase='activate',candidate_path=str(folder/'validated.py'))
   record['status']=row['status'];row['trace'].append(record)
  except Exception as exc:row.update(status='error',error=type(exc).__name__+': '+str(exc)[:300]);record['error']=row['error'];row['trace'].append(record)
  with self.lock:self.s['proposals'][ident]=row;self.save()
  if row['status']=='ready' and row['auto_activate']:return self.activate(ident)
  return copy.deepcopy(row)
 def activate(self,ident):
  with self.lock:
   row=self.s['proposals'][ident]
   if row['status']!='ready':raise ValueError('Only a checked, staged proposal can be activated')
   if self.s['active'].get(row['name'])!=row.get('baseline_registration'):raise ValueError('Installed skill changed during evaluation; evaluate the proposal again against the current version')
   baseline=row.get('baseline_registration')
   if baseline and case_digest(accepted_cases(self.s['proposals'][baseline['proposal_id']]))!=row.get('baseline_cases_sha256'):raise ValueError('New runtime acceptance evidence arrived; evaluate this upgrade again against the expanded contract')
   source=(self.root/ident/'validated.py').read_text(encoding='utf-8')
   if digest(source)!=row['source_sha256']:raise ValueError('Staged source changed; submit and test it again')
   previous=copy.deepcopy(self.s['active'].get(row['name']));row['previous_active']=previous;self.s['active'][row['name']]={'proposal_id':ident,'sha256':row['source_sha256'],'activated':time.time()};row.update(status='active',phase='monitor');self.save();self.receipt(row,'activated');return copy.deepcopy(row)
 def rollback(self,skill,expected_id=None):
  with self.lock:
   active=self.s['active'].get(name(skill))
   if not active:raise ValueError('Skill is not active')
   if expected_id is not None and active['proposal_id']!=expected_id:return {'name':skill,'skipped':True,'reason':'A newer registration is active; an older failure cannot roll it back'}
   row=self.s['proposals'][active['proposal_id']];previous=row.get('previous_active')
   if previous:self.s['active'][skill]=previous
   else:self.s['active'].pop(skill)
   row['status']='rolled-back';self.save();self.receipt(row,'rolled-back');return {'name':skill,'restored':previous}
 def run(self,b):
  skill=name(b.get('name'));args=b.get('args');data_budget(args)
  if 'expected' in b:data_budget(b['expected'])
  if not isinstance(args,list):raise ValueError('Use a JSON argument list')
  with self.lock:
   active=copy.deepcopy(self.s['active'].get(skill))
   if not active:raise ValueError('Skill is not active')
   row=copy.deepcopy(self.s['proposals'][active['proposal_id']])
  try:
   source=(self.root/row['id']/'validated.py').read_text(encoding='utf-8')
   if digest(source)!=active['sha256']:raise ValueError('Active source changed; execution withheld')
   result=FunctionTest(source).invoke(row['function'],args);data_budget(result)
   if 'expected' in b:
    from .workflow_contracts import equivalent
    if not equivalent(result,b['expected']):raise ValueError('Runtime acceptance check failed')
  except Exception as exc:
   with self.lock:
    actual=self.s['proposals'][row['id']];actual['runtime_failures']=(actual.get('runtime_failures',[])+[{'time':time.time(),'input_sha256':case_digest(args),'error':type(exc).__name__,'expected_supplied':'expected' in b}])[-16:];self.save()
    if self.s['active'].get(skill):self.rollback(skill,expected_id=row['id'])
   raise
  with self.lock:
   actual=self.s['proposals'][row['id']];stats=actual.setdefault('runtime_checks',{'runs':0,'acceptance_checked':0});stats['runs']+=1
   if 'expected' in b:
    stats['acceptance_checked']+=1
    case={'args':copy.deepcopy(args),'expected':copy.deepcopy(b['expected'])}
    cases=actual.setdefault('runtime_cases',[])
    if not any(c['args']==args for c in accepted_cases(actual)) and len(cases)<32:cases.append(case)
   self.save()
  return {'name':skill,'result':result,'proposal_id':row['id'],'source_sha256':active['sha256'],'execution':'bounded native function interpreter','host_access':False}
 def receipt(self,row,status):
  self.pending.append({'origin':'self-improvement-engine','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'proposal_id':row['id'],'name':row['name'],'status':status,'model_calls':0}});self.pending=self.pending[-32:]
 def view(self):
  with self.lock:return {'proposals':[{k:copy.deepcopy(r.get(k)) for k in ('id','name','question','phase','status','checks','research','reason','error','source_sha256','trace','candidate_path','runtime_checks','runtime_failures','runtime_cases')} for r in self.s['proposals'].values()],'active':copy.deepcopy(self.s['active']),'weaknesses':copy.deepcopy(self.s['weaknesses']),'sources':copy.deepcopy(self.s['sources']),'learning_enabled':self.s['learning_enabled'],'auto_research':self.s['auto_research'],'scope':'Writes revisioned candidate Python skills and executes checked pure functions. Full core-app rewrites require separate project-wide validation and deployment; model weights are unchanged.'}
 def command(self,b):
  op=b.get('op')
  if op in ('project_prepare','project_apply','project_recover','project_status'):
   from .project_changes import ProjectChanges
   circuit=getattr(self,'circuit',None)
   if circuit is None:raise ValueError('Project workbench is not attached')
   workbench=circuit.r.workbench;manager=ProjectChanges(workbench)
   with workbench.lock:
    if op=='project_prepare':return manager.prepare(b['changes'])
    if op=='project_apply':return manager.apply(b['id'])
    if op=='project_recover':return manager.recover(b['id'])
    return {'change_sets':[manager.summary(r) for r in manager.rows]}
  if op=='submit':return self.submit(b['proposal'])
  if op=='activate':return self.activate(b['id'])
  if op=='rollback':return self.rollback(b['name'])
  if op=='run':return self.run(b)
  if op=='configure':
   with self.lock:
    for key in ('learning_enabled','auto_research'):
     if key in b:
      if type(b[key]) is not bool:raise ValueError('Configuration switches require booleans')
      self.s[key]=b[key]
    self.save()
  elif op!='status':raise ValueError('Unknown improvement command')
  return self.view()
 def observe(self,event):
  payload=event.get('payload')
  if event.get('kind')!='input' or not isinstance(payload,dict) or not isinstance(payload.get('self_improvement'),dict):return
  ident=payload.get('command_id')
  if not isinstance(ident,str) or not 1<=len(ident)<=80:return
  with self.lock:
   seen=self.s.setdefault('bus_ids',[])
   if ident in seen:return
   if len(self.bus_queue)>=16:raise ValueError('Development command queue is full')
   seen.append(ident);self.s['bus_ids']=seen[-256:];self.bus_queue.append({'id':ident,'body':copy.deepcopy(payload['self_improvement'])})
  self.wake.set()
 def loop(self,c):
  while not c.halt.is_set():
   if not c.enabled:self.wake.wait(1);self.wake.clear();continue
   try:
    with self.lock:bus_item=self.bus_queue.pop(0) if self.bus_queue else None
    if bus_item:
     try:result=self.command(bus_item['body']);status='applied'
     except Exception as exc:result={'error':str(exc)[:240]};status='rejected'
     c.bus.publish({'origin':'self-improvement-command','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'command_id':bus_item['id'],'status':status,'result_id':result.get('id') if isinstance(result,dict) else None,'error':result.get('error') if isinstance(result,dict) else None}})
    with self.lock:enabled=self.s['learning_enabled'];candidate=next((r['id'] for r in self.s['proposals'].values() if r['status'] in ('queued','running')),None)
    if enabled and candidate:self.advance(candidate)
    if enabled and time.monotonic()>self.next_scan:
     self.next_scan=time.monotonic()+60
     with c.lock:errors=copy.deepcopy(c.service_errors)
     with self.lock:
      for service,error in errors.items():
       if not any(r['service']==service for r in self.s['weaknesses']):self.s['weaknesses'].append({'service':service,'first_seen':time.time(),'status':'needs-task-contract','public_learning_topic':'Python error handling regression testing','next':'Supply a reproducing task with expected outcomes before generating a code candidate.'})
      self.s['weaknesses']=self.s['weaknesses'][-32:];self.save()
     if self.s['weaknesses'] and not self.s['sources'] and self.s['auto_research']:self.research()
     if errors and getattr(c,'software_theory',None) and getattr(c.software_theory,'research',None):c.software_theory.research.request('Python error handling regression testing')
    with self.lock:events=self.pending;self.pending=[]
    for event in events:c.bus.publish(event)
   except Exception as exc:
    with self.lock:self.s['last_error']=str(exc)[:300]
   self.wake.wait(1);self.wake.clear()
