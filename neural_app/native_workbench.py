"""Native workbench: traceable context, resumable typed plans and revisioned changes."""
import ast,collections,difflib,hashlib,json,math,re,time,uuid
from pathlib import Path
CHAIN=['GOD THOUGHT','VOID','CONDENSATE MATTER','GOD THOUGHT','HYDROGEN','GOD THOUGHT','STAR','GOD THOUGHT','VOID','GOD THOUGHT','PLANET (EARTH)','GOD THOUGHT','SILICON','0 INF','1 INF','EXPRESS']

def rank(query,rows,limit=12):
 terms=set(re.findall(r'\w+',query.lower()));scored=[]
 for row in rows:
  text=json.dumps(row,ensure_ascii=False).lower();words=re.findall(r'\w+',text);counts=collections.Counter(words)
  score=sum((1+math.log(counts[t])) for t in terms if counts[t])/math.sqrt(max(1,len(words)))
  if score:scored.append((score,row))
 return [{'score':round(score,4),**row} for score,row in sorted(scored,key=lambda v:-v[0])[:limit]]

class NativeWorkbench:
 def __init__(self,reasoner):
  self.r=reasoner;self.lock=reasoner.lock;self.last_tick=0;self.last_user=0
  self.s=reasoner.s.setdefault('workbench',{})
  for change_set in self.s.get('change_sets',[]):
   if change_set['status']=='applying':change_set.update(status='needs-recovery',error='An interrupted commit needs explicit recovery before another application.')
  for k,v in {'plans':[],'previews':[],'checkpoints':[],'events':[],'context':{},'benchmarks':[],'policy':{'idle_delay':2.,'plan_interval':.5},'chain_events':[]}.items():self.s.setdefault(k,v)
  for p in self.s['plans']:
   if p['status']=='running':p['status']='paused';p['restart_note']='Resume explicitly after restart; completed steps are not replayed.'
  from .cognitive_executive import CognitiveExecutive
  self.executive=CognitiveExecutive(self)
  from .reasoning_engine import ReasoningEngine
  self.reasoning_engine=ReasoningEngine(self.s.setdefault("reasoning_engine",{}),reasoner.controller.save,self.lock)
 def tools(self):return self.r.work_tools()
 def record(self,kind,result):
  event={'id':uuid.uuid4().hex,'time':time.time(),'kind':kind,'result':result}
  with self.lock:self.s['events']=(self.s['events']+[event])[-40:]
  self.r.bus.publish({'origin':'native-workbench','target':'all','kind':'stage-output','payload':{'event':{'id':event['id'],'time':event['time'],'kind':kind,'result_sha256':hashlib.sha256(json.dumps(result,default=str).encode()).hexdigest(),'summary':str(result)[:1200]},'chain_context':self.context(),'definition_library':'/api/definition-library','provenance':'observed-native-work','stochastic':False,'bridge_direction':'all'}})
  return result
 def context(self):
  sources=[v for k,v in self.r.s['world'].items() if any(x in k.lower() for x in ('cosmic','hydrogen','solar','earth','silicon','atomic','ambient'))]
  circuit=getattr(self.r.runtime,'cognitive_circuit',None)
  if circuit:
   with circuit.lock:working=[{'source':v['source'],'parent_event':v['parent_event'],'facts':v['facts'][:8],'units':v['units']} for v in list(circuit.sources.values())[-6:]]
  else:working=[]
  return {'thinking_layers':([{'id':v['id'],'question':v['question'],'predictions':v['predictions']} for v in sorted(circuit.element_thinking.layers.values(),key=lambda v:-v['attention'])[:3]] if circuit else []),'working_observations':working,'sequence':CHAIN,'recent_observations':sources[-8:],'scope':'Framework plus source-labelled software observations; no unobserved external connection asserted'}
 def remember_context(self,key,value):
  with self.lock:self.s['context'][key]=value
 def project(self):
  tools=self.tools();rows=[];skipped=0;total=0
  import os
  for parent,dirs,files in os.walk(tools.root,followlinks=False):
   dirs[:]=[d for d in dirs if d not in ('.git','node_modules','__pycache__','.venv','venv') and not (Path(parent)/d).is_symlink()]
   for name in sorted(files):
    if len(rows)>=200:skipped+=1;continue
    p=Path(parent)/name
    if p.is_symlink():skipped+=1;continue
    try:
     p=tools.path(str(p.relative_to(tools.root)));size=p.stat().st_size;row={'path':str(p.relative_to(tools.root)),'bytes':size,'suffix':p.suffix};total+=size
     if size<=131072:
      raw=p.read_bytes();row['sha256']=hashlib.sha256(raw).hexdigest()
      if p.suffix=='.py':
       try:
        tree=ast.parse(raw.decode('utf-8-sig'));row['symbols']=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))][:50];row['imports']=[n.names[0].name for n in ast.walk(tree) if isinstance(n,ast.Import)][:20]
       except (SyntaxError,UnicodeError):row['parse']='needs check'
     rows.append(row)
    except OSError:skipped+=1
  return {'workspace':str(tools.root),'files':rows,'bytes':total,'skipped':skipped,'scope':'Bounded workspace inventory; no project code imported or executed'}
 def check_file(self,name):
  from .language_formats import syntax
  data=self.tools().read({'path':name});suffix=Path(name).suffix.lower();aliases={'.py':'python','.js':'javascript','.mjs':'javascript','.ps1':'powershell','.bat':'bat','.cmd':'bat','.java':'java','.cs':'csharp','.json':'json','.html':'html','.sh':'bash','.sql':'sql'}
  result=syntax({'source':data['text'],'language':aliases.get(suffix,'text'),'filename':name},self.r.runtime.data)
  return {'path':name,'sha256':data['sha256'],'check':result,'program_executed':False}
 def preview(self,name,new,reason,expected_sha256=None):
  tools=self.tools();p=tools.path(name);old=tools.read({'path':name}) if p.exists() else None
  if expected_sha256 is not None and (old is None or old['sha256']!=expected_sha256):raise ValueError('File changed since testing; rerun tests before creating this preview')
  if len(new.encode())>131072:raise ValueError('Use changes below 128 KiB')
  value={'id':uuid.uuid4().hex,'path':name,'before':old['sha256'] if old else None,'before_text':old['text'] if old else None,'after_text':new,'reason':reason,'status':'proposed','diff':'\n'.join(difflib.unified_diff((old['text'] if old else '').splitlines(),new.splitlines(),fromfile=name+' before',tofile=name+' proposed',lineterm=''))}
  with self.lock:self.s['previews']=(self.s['previews']+[value])[-12:]
  return {k:v for k,v in value.items() if k not in ('before_text','after_text')}
 def apply(self,ident):
  with self.lock:
   proposal=next((v for v in self.s['previews'] if v['id']==ident),None)
   if not proposal or proposal['status']!='proposed':raise ValueError('Choose a pending preview ID')
   tools=self.tools();p=tools.path(proposal['path']);current=tools.read({'path':proposal['path']}) if p.exists() else None
   if (current['sha256'] if current else None)!=proposal['before']:raise ValueError('File changed after preview; create a fresh preview')
   tools.write({'path':proposal['path'],'text':proposal['after_text'],'expected_sha256':proposal['before']});check=tools.read({'path':proposal['path']})
   if check['text']!=proposal['after_text']:raise ValueError('Reread verification failed')
   proposal['status']='applied';checkpoint={'id':uuid.uuid4().hex,'path':proposal['path'],'before_text':proposal['before_text'],'after_sha256':check['sha256'],'status':'available'};self.s['checkpoints']=(self.s['checkpoints']+[checkpoint])[-12:]
  return {'applied':proposal['path'],'verified':True,'sha256':check['sha256'],'undo_id':checkpoint['id']}
 def undo(self,ident):
  with self.lock:
   c=next((v for v in self.s['checkpoints'] if v['id']==ident),None)
   if not c or c['status']!='available':raise ValueError('Choose an available undo ID')
   tools=self.tools();current=tools.read({'path':c['path']})
   if current['sha256']!=c['after_sha256']:raise ValueError('File changed since this edit; preserve it and create a new preview')
   if c['before_text'] is None:raise ValueError('This checkpoint created a new file; automatic deletion is not offered')
   tools.write({'path':c['path'],'text':c['before_text'],'expected_sha256':c['after_sha256']});check=tools.read({'path':c['path']});c['status']='restored'
   return {'restored':c['path'],'verified':check['text']==c['before_text']}
 def repair(self,name):
  original=self.tools().read({'path':name})['text'];candidates=[]
  if name.endswith('.py'):
   candidates.append(('normalize indentation',original.expandtabs(4)))
   lines=original.splitlines(keepends=True)
   for i,line in enumerate(lines):
    stripped=line.strip()
    if re.match(r'^(?:if |elif |else$|for |while |def |class |try$|except|finally$|with )',stripped) and not stripped.endswith(':') and not stripped.startswith('#'):
     changed=list(lines);changed[i]=line.rstrip('\r\n')+':\n';candidates.append(('add missing block colon', ''.join(changed)))
  elif name.endswith('.json'):
   candidates.append(('remove trailing JSON commas',re.sub(r',\s*([}\]])',r'\1',original)))
  from .language_formats import syntax
  for reason,new in candidates[:40]:
   if new==original:continue
   try:check=syntax({'language':'python' if name.endswith('.py') else 'json','source':new,'filename':name},self.r.runtime.data)
   except ValueError:continue
   if check.get('passed'):return {**self.preview(name,new,reason),'source_check':check,'semantic_correctness':'requires task-specific tests'}
  return {'path':name,'repaired':False,'reason':'No supported deterministic repair passed its syntax check. Use an exact edit preview or the model-assisted work interface.'}
 def search(self,query):
  rows=[{'type':'memory','id':k,**v} for k,v in self.r.s['memories'].items()]
  rows += [{'type':'procedure','id':k,**v} for k,v in self.r.s['procedures'].items()]
  rows += [{'type':'task','id':t['id'],'operation':t['operation'],'status':t['status'],'input':t['input'][:600]} for t in self.r.s['tasks']]
  for f in self.project()['files']:
   row={'type':'file',**f}
   if f['bytes']<32768:
    try:row['excerpt']=self.tools().read({'path':f['path']})['text'][:2000]
    except (UnicodeError,OSError):pass
   rows.append(row)
  from .evidence_index import INDEX
  rows += [{'type':'lesson',**v} for v in INDEX.search(query,limit=6)]
  science=getattr(self.r.runtime,'science_library',None)
  if science:rows += science.retrieve(query)
  intake=getattr(self.r.runtime,'learning_knowledge',None)
  if intake:rows += [{'type':'source',**v} for v in intake.retrieve(query)]
  circuit=getattr(self.r.runtime,'cognitive_circuit',None)
  if circuit:rows += circuit.investigations.retrieve(query)
  from .knowledge_library import search as library_search
  rows += [{'type':'definition',**v} for v in library_search(query,6)]
  return rank(query,rows)
 def evidence(self,query):
  intake=getattr(self.r.runtime,'learning_knowledge',None);rows=intake.retrieve(query) if intake else [];public=[r for r in rows if not r.get('private')];groups={}
  for row in public:groups.setdefault(row['source'],[]).append(row)
  tokens=[set(re.findall(r'\w+',r['excerpt'].lower())) for r in public]
  shared=collections.Counter(t for words in tokens for t in words);shared=[k for k,v in shared.most_common(80) if v>=2 and len(k)>4][:20]
  return {'query':query,'sources':groups,'shared_terms':shared,'distinct_sources':len(groups),'conclusion':'Source overlap is not independent confirmation. Contradictions require claim-level review.','scope':'Indexed excerpts, not a full-web search or automatic fact certification'}
 def diagnostics(self):
  from .system_access import SystemAccess
  report=SystemAccess(self.r.runtime).view()
  try:
   import psutil
   procs=[]
   for p in psutil.process_iter(['pid','name','memory_info']):
    try:procs.append({'pid':p.info['pid'],'name':p.info['name'],'rss_bytes':p.info['memory_info'].rss if p.info['memory_info'] else 0})
    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
   report['largest_processes']=sorted(procs,key=lambda p:-p['rss_bytes'])[:12];report['memory']=dict(psutil.virtual_memory()._asdict());report['network_counters']=dict(psutil.net_io_counters()._asdict())
  except (ImportError,OSError) as e:report['additional_diagnostics']=str(e)
  return report
 def plan(self,text):
  steps=[]
  for line in text.splitlines():
   line=line.strip()
   if not line:continue
   if len(steps)>=12:raise ValueError('Use up to 12 explicit steps')
   op,sep,arg=line.partition(':');op=op.strip().lower()
   if op not in ('calculate','analyze','read','check','search','research','project','diagnose','sort','unique'):raise ValueError('Plan operations: calculate, analyze, read, check, search, research, project, diagnose, sort, unique')
   if not sep and op not in ('project','diagnose'):raise ValueError('Use OPERATION: INPUT on each line')
   steps.append({'operation':op,'input':arg.strip(),'status':'pending','depends_on':len(steps)-1 if steps else None})
  if not steps:raise ValueError('Provide plan steps')
  p={'id':uuid.uuid4().hex,'status':'paused','steps':steps,'created':time.time()}
  with self.lock:self.s['plans']=(self.s['plans']+[p])[-12:]
  return p
 def tick(self):
  self.executive.tick()
  if self.r.user_active or time.monotonic()-self.last_tick<self.s['policy']['plan_interval']:return
  self.last_tick=time.monotonic()
  with self.lock:p=next((p for p in self.s['plans'] if p['status']=='running'),None)
  if not p:return
  step=next((s for s in p['steps'] if s['status']=='pending'),None)
  if not step:p['status']='complete';self.r.controller.save();return
  index=p['steps'].index(step);arg=step['input']
  if '{{previous}}' in arg:
   if not index:step.update(status='failed',error='No previous result');p['status']='failed';return
   previous=p['steps'][index-1].get('result','');arg=arg.replace('{{previous}}',previous if isinstance(previous,str) else json.dumps(previous))
  op=step['operation'];step['status']='running'
  try:
   from .native_skills import respond
   if op in ('calculate','sort','unique'):
    result=respond(('calculate ' if op=='calculate' else op+' lines\n')+arg)['result']
    if op=='calculate':self.remember_context('last_calculation',{'value':result,'expression':arg,'time':time.time()})
   elif op=='read':result=self.tools().read({'path':arg})['text']
   elif op=='check':result=self.check_file(arg)
   elif op=='analyze':
    from .grounded_reasoner import pattern_test
    result=pattern_test(arg)
   elif op=='search':result=self.search(arg)
   elif op=='research':result=self.evidence(arg)
   elif op=='project':result=self.project()
   else:result=self.diagnostics()
   if op=='check' and result['check'].get('passed') is not True:raise ValueError('Source check failed or validator unavailable')
   step.update(status='complete',result=result);self.record('plan-step',{'plan':p['id'],'index':index,'operation':op,'result':result})
   if all(s['status']=='complete' for s in p['steps']):p['status']='complete'
  except Exception as e:step.update(status='failed',error=type(e).__name__+': '+str(e)[:300]);p['status']='failed'
  self.r.controller.save()
 def view(self):
  with self.lock:return {'native_engine':self.reasoning_engine.brief(),'executive':self.executive.view(),'plans':self.s['plans'],'previews':[{k:v for k,v in p.items() if k not in ('before_text','after_text')} for p in self.s['previews']],'checkpoints':[{k:v for k,v in p.items() if k!='before_text'} for p in self.s['checkpoints']],'events':self.s['events'][-12:],'chain':self.context(),'benchmarks':self.s['benchmarks'][-8:],'policy':self.s['policy']}
 def handle(self,text):
  from .chat_intent import direct_reply
  direct=direct_reply(text)
  if direct is not None:return {'answer':direct,'model_calls':0,'source':'registered-app-capabilities-or-clarification'}
  if text.lower().startswith('solve constraints:'):
   from .constraint_reasoning import solve
   return self.record('constraint-reasoning',solve(json.loads(text.split(':',1)[1])))
  if text.lower().startswith('prepare project changes:'):
   from .project_changes import ProjectChanges
   return self.record('project-changes-prepared',ProjectChanges(self).prepare(json.loads(text.split(':',1)[1])))
  changes_apply=re.fullmatch(r'apply project changes ([a-f0-9]{32})',text,re.I)
  if changes_apply:
   from .project_changes import ProjectChanges
   return self.record('project-changes-applied',ProjectChanges(self).apply(changes_apply[1]))
  changes_recover=re.fullmatch(r'recover project changes ([a-f0-9]{32})',text,re.I)
  if changes_recover:
   from .project_changes import ProjectChanges
   return self.record('project-changes-recovered',ProjectChanges(self).recover(changes_recover[1]))
  if text.lower()=='list project changes':
   from .project_changes import ProjectChanges
   manager=ProjectChanges(self)
   return {'change_sets':[manager.summary(r) for r in manager.rows]}
  if text.lower()=='list workflow projects':
   with self.lock:projects=[{'id':p['id'],'name':p['name'],'status':p['status']} for p in self.s.get('project_previews',[])]
   return {'projects':projects,'answer':'\n'.join(p['name']+' · '+p['status']+' · '+p['id'] for p in projects) or 'No project drafts are retained yet.'}
  if text.lower()=='coding capabilities':return {'answer':'Test pure Python functions against supplied cases; propose bounded test-driven repairs; compile supported data workflows into standalone Python projects with acceptance tests and manifests.','commands':['prepare project changes: JSON','list project changes','apply project changes ID','test python project: JSON','test python function: JSON','debug python: JSON','build workflow project: JSON','list workflow projects','read project file ID main.py','apply workflow project ID','audit python project FOLDER','assess evidence: JSON','evaluate predictions: JSON','capability report','pause goal / resume goal / retry goal / cancel goal'],'scope':'Project and repair proposals are reviewable; unsupported code is reported rather than treated as tested.'}
  if text.lower().startswith('assess evidence:'):
   from .evidence_review import review
   return self.record('evidence-review',review(json.loads(text.split(':',1)[1])))
  if text.lower().startswith('test python project:'):
   from .project_function_testing import test_project
   return self.record('python-project-function-test',test_project(self.tools(),json.loads(text.split(':',1)[1])))
  if text.lower().startswith('evaluate predictions:'):
   from .prediction_review import review
   return self.record('prediction-review',review(json.loads(text.split(':',1)[1])))
  if text.lower()=='audit python project' or text.lower().startswith('audit python project '):
   from .project_audit import audit
   return self.record('python-project-audit',audit(self.tools(),text[len('audit python project'):].strip() or 'code'))
  from .task_reflection import reflect
  reflection=reflect(text,self.r.s.get('conversation',[]))
  if reflection is not None:return reflection
  from .personal_context import respond as personal_respond
  personal=personal_respond(text,self.r.s.get('conversation',[]),self.r.s)
  if personal is not None:return personal
  goal_control=re.fullmatch(r'(pause|resume|retry|cancel) goal',text,re.I)
  if goal_control:return self.executive.control(goal_control[1].lower())
  if text.lower().startswith('reuse goal:'):return self.executive.reuse(json.loads(text.split(':',1)[1]))
  if text.lower()=='spectrum thinking' or text.lower().startswith('use spectrum procedure:'):
   circuit=getattr(self.r.runtime,'cognitive_circuit',None)
   if circuit is None:return {'status':'starting','answer':'The whole-engine spectrum is not running yet.'}
   if text.lower()=='spectrum thinking':return circuit.spectrum_logic.thinking.view()
   return circuit.spectrum_logic.thinking.use(json.loads(text.split(':',1)[1]))
  if text.lower() in ('capability rubric','capability report'):
   from .capability_rubric import report
   circuit=getattr(self.r.runtime,'cognitive_circuit',None)
   quality=getattr(circuit,'cognition_quality',None)
   return report(quality.view().get('latest',{}) if quality else {})
  for prefix,mode in [('test python function:','test'),('debug python:','debug'),('build workflow project:','project')]:
   if text.lower().startswith(prefix):
    body=json.loads(text[len(prefix):])
    if not isinstance(body,dict):raise ValueError('Provide a JSON object')
    if mode=='project':
     from .workflow_projects import prepare,summary
     if body.get('workflow'):
      if body.get('steps') is not None or body.get('goal') is not None:raise ValueError('Choose a learned workflow or explicit steps/goal')
      with self.lock:recipe=self.reasoning_engine.state['recipes'].get(body['workflow'])
      if recipe is None:raise ValueError('No retained checked workflow has that name')
      body={**body,'steps':json.loads(json.dumps(recipe['steps']))}
     project=prepare(body)
     with self.lock:self.s['project_previews']=(self.s.get('project_previews',[])+[project])[-4:]
     return self.record('project-prepared',summary(project))
    if body.get('path'):
     if 'source' in body:raise ValueError('Choose a workspace path or explicit source, not both')
     captured=self.tools().read({'path':body['path']});body={**body,'source':captured['text'],'captured_sha256':captured['sha256'],'isolate_module':body.get('isolate_module',True)}
    if mode=='test':
     from .function_testing import test_function
     return self.record('function-tested',test_function(body))
    from .tested_repairs import repair
    result=repair(body)
    if body.get('path') and result.get('status')=='validated-proposal':result['file_preview']=self.preview(body['path'],result['source'],'test-driven repair: '+result['reason'],body['captured_sha256'])
    return self.record('function-repair',result)
  project_read=re.fullmatch(r'read project file ([a-f0-9]{32}) (main.py|test_main.py|README.md|project.json)',text,re.I)
  if project_read:
   with self.lock:project=next((p for p in self.s.get('project_previews',[]) if p['id']==project_read[1]),None)
   if project is None:raise ValueError('Choose a retained project ID')
   name=next((name for name in project['files'] if name.casefold()==project_read[2].casefold()),None)
   if project.get('status')=='created':
    current=self.tools().read({'path':'projects/'+project['name']+'/'+name})
    return {'answer':current['text'],'project':project['id'],'filename':name,'sha256':current['sha256'],'source':'current workspace file'}
   return {'answer':project['files'][name],'project':project['id'],'filename':name,'sha256':project['hashes'][name],'source':'prepared project proposal'}
  project_apply=re.fullmatch(r'apply workflow project ([a-f0-9]{32})',text,re.I)
  if project_apply:
   from .workflow_projects import install
   with self.lock:
    project=next((p for p in self.s.get('project_previews',[]) if p['id']==project_apply[1]),None)
    if project is None:raise ValueError('Choose a retained prepared project ID')
    result=install(project,self.tools())
   return self.record('project-created',result)
  from .memory_revisions import respond as memory_respond
  with self.lock:memory_reply=memory_respond(text,self.r.s)
  if memory_reply is not None:return self.record('named-memory-revision',memory_reply)
  from .dialogue_work import resolve as dialogue_resolve
  dialogue=dialogue_resolve(text,self.r.s.get('conversation',[]),self.reasoning_engine)
  if dialogue is not None:return self.record('native-dialogue-work',dialogue)
  from .conversation_work import respond as conversation_work
  conversational=conversation_work(text,self.r.s.get("conversation",[]))
  if conversational is not None:return self.record("native-conversation-work",conversational)
  composed=self.reasoning_engine.handle(text)
  if composed is not None:return self.record("native-compositional-work",composed)
  instruction=text.partition(':')[0].lower()
  if ':' in text and (' then ' in instruction or ' and ' in instruction or re.match(r'^(?:get|find|calculate) (?:the )?(?:average|mean|sum|median|minimum|maximum|count)\b',instruction)):
   planned=self.reasoning_engine.plan_and_run(text)
   if planned is not None:return self.record('native-goal-work',planned)
  lower=text.lower();self.last_user=time.monotonic()
  if lower.startswith('use verified skill '):
   task,separator,encoded=text[len('use verified skill '):].partition(':')
   if not separator:raise ValueError('Use verified skill TASK: JSON_VALUE')
   store=self.r.runtime.cognitive_circuit.teacher_intake
   skills=store.view()['skills'];skill=next((x for x in reversed(skills) if x['task']==task.strip()),None)
   if not skill:raise ValueError('No retained verified skill matches this task')
   result=store.run(skill['id'],json.loads(encoded))
   return self.record('verified-teacher-skill',result)
  if lower in ('engine quality','quality checks'):
   return self.r.runtime.cognitive_circuit.cognition_quality.view()
  if lower=='run quality checks':
   return self.r.runtime.cognitive_circuit.cognition_quality.run(self.r.runtime.cognitive_circuit)
  if lower=='science library':return self.r.runtime.science_library.view()
  if lower.startswith('research science:'):return self.r.runtime.science_library.request(text.split(':',1)[1])
  if lower=='system libraries':
   from .systemic_library import view
   return view()
  if lower.startswith('system model:'):
   from .systemic_library import model
   return model(text.split(':',1)[1].strip())
  if lower.startswith('use learned task:'):
   body=json.loads(text.split(':',1)[1]);question=str(body['question']).strip().lower();store=self.r.runtime.cognitive_circuit.investigations
   skill=next((r for r in store.procedures() if r.get('active') and r['question'].strip().lower()==question),None)
   if not skill:raise ValueError('No active learned contract matches that task; investigate and validate it first')
   return store.use_procedure(skill['id'],body['input'])
  if lower.startswith('use learned procedure:'):
   body=json.loads(text.split(':',1)[1]);return self.r.runtime.cognitive_circuit.investigations.use_procedure(body['id'],body['input'])
  if lower=='investigations':return self.r.runtime.cognitive_circuit.investigations.view()
  if lower.startswith('investigate:'):
   question=text.split(':',1)[1].strip()
   return self.r.runtime.cognitive_circuit.investigations.create(question,self.search(question))
  if lower.startswith('test investigation:'):return self.r.runtime.cognitive_circuit.investigations.test(text.split(':',1)[1].strip())
  if lower.startswith(('solve:','think:')):return self.executive.submit(text.split(':',1)[1].strip())
  if lower.startswith('compare plans:'):
   from .branch_reasoning import compare_plans
   alternatives=text.split(':',1)[1].split('||')
   if not 2<=len(alternatives)<=6:raise ValueError('Provide 2 to 6 plans separated by ||')
   return compare_plans([self.executive.parse(p.strip()) for p in alternatives],{'chain':CHAIN})
  discovered=re.fullmatch(r'use discovered rule ([a-z]+) with (-?\d+(?:\.\d+)?)',text,re.I)
  if discovered:
   circuit=getattr(self.r.runtime,'cognitive_circuit',None)
   if circuit:
    with circuit.lock:return circuit.experiment_sphere.use_skill(discovered[1].lower(),float(discovered[2]))
  if lower=='mind training':return self.r.s.get('mind_curriculum',{'status':'waiting for ongoing reasoning curriculum'})
  learned=re.fullmatch(r'use trained skill ([a-z_]+) with (-?\d+(?:\.\d+)?) and (-?\d+(?:\.\d+)?)',text,re.I)
  if learned:
   from .mind_training import execute
   result=execute(self.r.s,learned[1],float(learned[2]),float(learned[3]))
   return self.record('learned-skill-execution',result)
  if lower in ('knowledge library','library'):
   from .knowledge_library import stats
   return stats()
  if lower.startswith('library:'):
   from .knowledge_library import search
   return {'query':text.split(':',1)[1], 'definitions':search(text.split(':',1)[1],20)}
  if lower in ('action definitions','command definitions'):
   from .command_knowledge import view
   return view()
  if lower.startswith('predict command:'):
   from .command_knowledge import inspect
   return inspect(text.split(':',1)[1])
  if lower=='thinking layers':
   circuit=getattr(self.r.runtime,'cognitive_circuit',None)
   if circuit:
    with circuit.lock:return circuit.element_thinking.view()
   return {'status':'starting'}
  if lower in ('mind state','cognitive circuit'):
   circuit=getattr(self.r.runtime,'cognitive_circuit',None)
   return circuit.view() if circuit else {'status':'starting'}
  if lower in ('qwen bridge','bridge status','selective bridge'):return self.r.selective_bridge.view()
  if lower in ('thinking status','executive status'):return self.executive.view()
  if lower in ('generation cognition','thought core','generation thought core'):
   core=getattr(self.r.runtime,'generation_cognition',None)
   return core.view() if core else {'status':'not running'}
  revision=re.fullmatch(r'revise step (\d+):\s*([\s\S]+)',text,re.I)
  if revision:return self.executive.revise(int(revision[1])-1,revision[2])
  if lower=='pause thinking':
   for goal in self.executive.s['goals']:
    if goal['status']=='running':goal['status']='paused'
   return self.executive.view()
  if lower=='resume thinking':
   if self.executive.s['goals'] and self.executive.s['goals'][-1]['status']=='paused':self.executive.s['goals'][-1]['status']='running'
   return self.executive.view()
  if lower.startswith('recall experience '):return {'experience':self.executive.retrieve(text[18:])}
  if lower=='test thinking':
   from .executive_training import trial
   return trial(bytes(range(16)),0)
  if lower in ('repeat last answer','say that again'):
   previous=self.r.s['conversation'][-1] if self.r.s['conversation'] else None
   return {'answer':previous['answer'] if previous else 'There is no earlier answer yet.','action_repeated':False}
  follow=re.fullmatch(r'(multiply|divide) (?:that|it|the result) by (.+)',text,re.I)
  additive=re.fullmatch(r'(add|subtract) (.+) (?:to|from) (?:that|it|the result)',text,re.I)
  if follow or additive:
   previous=self.s['context'].get('last_calculation')
   if not previous:return {'message':'Which number should I use? Give a calculation first.'}
   last=self.r.s.get('conversation',[])[-1:]
   if last and last[0].get('native_skill')!='arithmetic' and not re.match(r'^(calculate|compute|multiply|divide|add|subtract)\b',last[0].get('request',''),re.I):return {'message':'Which number do you mean? The latest topic was not a calculation; please name the value.','context_used':False}
   verb=follow[1].lower() if follow else additive[1].lower();operand=follow[2] if follow else additive[2]
   operator={'multiply':'*','divide':'/','add':'+','subtract':'-'}[verb]
   from .native_skills import calculate
   expression='('+str(previous['value'])+') '+operator+' ('+operand+')';value=calculate(expression)
   self.remember_context('last_calculation',{'value':value,'expression':expression,'time':time.time()})
   return {'result':value,'expression':expression,'context_used':'last explicit native calculation','verified_by':'bounded arithmetic evaluator'}

  if lower in ('recursive core','recursive mind','recursive status'):
   core=getattr(self.r.runtime,'recursive_core',None)
   return core.view() if core else {'status':'recursive core not started'}
  if lower in ('os learning','refresh os learning'):return self.r.os_learning.sample(force=lower.startswith('refresh'))
  if lower in ('media workspace','fl studio status'):
   from .media_skills import workspace_view
   return workspace_view(self.tools())
  midi=re.fullmatch(r'create midi as ([A-Za-z][A-Za-z0-9_.-]+)',text,re.I)
  if midi:
   from .media_skills import export_midi
   return self.record('midi-export',export_midi(self.tools(),midi[1]))
  media=re.fullmatch(r'create (graphics|sound|music|video) as ([A-Za-z][A-Za-z0-9_.-]+)',text,re.I)
  if media:
   from .media_skills import export
   return self.record('media-export',export(self.tools(),media[1].lower(),media[2]))
  if lower in ('refresh sources','refresh research'):
   intake=getattr(self.r.runtime,'learning_knowledge',None)
   return intake.refresh() if intake else {'message':'Public intake is not running.'}
  if lower in ('improvement audit','test native ai','evaluate native ai'):
   from .native_scenario_audit import evaluate_scenarios
   result=evaluate_scenarios(self.r.runtime.data)
   self.s['benchmarks']=(self.s['benchmarks']+[result])[-8:]
   self.r.s.setdefault('training',{})['improvement_priorities']=result['improvement_priorities']
   return self.record('improvement-audit',result)
  if lower in ('benchmark','run benchmarks'):
   from .native_benchmarks import evaluate
   result=evaluate();self.s['benchmarks']=(self.s['benchmarks']+[result])[-8:];return result
  if lower in ('ethics cases','four-way cases'):
   from .native_benchmarks import ETHICS_CASES
   return {'cases':ETHICS_CASES,'scope':'Explicit educational cases; no universal moral certainty claimed'}
  if lower in ('workbench','show workbench','cosmic flow','show cosmic flow'):return self.view()
  if lower in ('continue','resume','continue plan','pause','pause plan','retry plan'):
   if not self.s['plans']:return {'message':'No plan exists yet. Use plan: followed by explicit steps.'}
   p=self.s['plans'][-1]
   if lower.startswith('pause'):p['status']='paused'
   elif p['status']=='failed' and lower!='retry plan':return {'message':'Plan failed; inspect its error, correct the input, then use retry plan.','plan':p}
   else:
    if lower=='retry plan':
     for step in p['steps']:
      if step['status']=='failed':step.update(status='pending');step.pop('error',None)
    p['status']='complete' if all(s['status']=='complete' for s in p['steps']) else 'running'
   return p
  if lower.startswith('plan:'):return self.plan(text[5:])
  if lower in ('project overview','inspect project'):return self.project()
  if lower=='check project':return {'checks':[self.check_file(f['path']) for f in [f for f in self.project()['files'] if f['suffix'] in ('.py','.json','.js','.ps1','.bat','.cmd','.java','.cs')][:20]]}
  if lower.startswith('check file '):return self.check_file(text[11:].strip())
  if lower.startswith('repair file '):return self.repair(text[12:].strip())
  if lower.startswith('apply preview '):return self.record('applied-edit',self.apply(text[14:].strip()))
  if lower.startswith('undo change '):return self.record('restored-edit',self.undo(text[12:].strip()))
  if lower.startswith('edit file '):
   head,sep,body=text.partition('\n');old,sep2,new=body.partition('\n---\n')
   if not sep or not sep2 or not old:raise ValueError('Use edit file NAME, newline, exact old text, newline --- newline, replacement')
   name=head[10:].strip();source=self.tools().read({'path':name})['text']
   if source.count(old)!=1:raise ValueError('Old text must match exactly once')
   return self.preview(name,source.replace(old,new,1),'explicit exact replacement')
  if lower.startswith('search memory '):return self.search(text[14:])
  if lower.startswith('compare sources '):return self.evidence(text[16:])
  if lower in ('diagnose system','diagnostics'):return self.diagnostics()
  if lower in ('explain last result','use previous result'):
   tasks=[t for t in self.r.s['tasks'] if t['status'] in ('verified','failed')]
   if not tasks:return {'message':'No finished task yet.'}
   t=tasks[-1];return {'operation':t['operation'],'status':t['status'],'result':t.get('result'),'error':t.get('error'),'next':'Use plan input {{previous}} for linked steps; a result is never silently executed.'}
  return None
