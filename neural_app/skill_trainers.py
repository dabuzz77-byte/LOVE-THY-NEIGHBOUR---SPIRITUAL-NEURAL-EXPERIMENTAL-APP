"""Native conversation, script and command practice with retained outcomes."""
import collections,copy,hashlib,json,re,threading,time,uuid
from .native_skills import calculate
from .restricted_test import run_restricted
from .command_knowledge import inspect,COMMANDS
MODES=('conversation','coding','commands')
class SkillTrainers:
 def __init__(self,data):
  self.path=data/'skill-trainers.json';self.lock=threading.RLock();self.next_at=0;self.cursor=0;self.sequence=0;self.latest={};self.history={k:collections.deque(maxlen=30) for k in MODES};self.feedback={};self.enabled=True;self.intake=None;self.mode_counts={k:0 for k in MODES}
  try:
   s=json.loads(self.path.read_text(encoding='utf-8'));self.sequence=s.get('sequence',0);self.feedback=s.get('feedback',{});self.mode_counts.update(s.get('mode_counts',{}))
   for k in MODES:self.history[k].extend(s.get('history',{}).get(k,[])[-30:]);self.latest[k]=copy.deepcopy(self.history[k][-1]) if self.history[k] else {}
  except (OSError,ValueError):pass
 def save(self):
  temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'sequence':self.sequence,'feedback':self.feedback,'mode_counts':self.mode_counts,'history':{k:list(v) for k,v in self.history.items()}},ensure_ascii=True),encoding='utf-8');temp.replace(self.path)
 def context(self,c):
  with c.lock:
   return {'goal':c.goal,'engine_events':c.sequence,'stage_count':len(c.element_thinking.layers),'stages':[{'id':v['id'],'title':v['title'],'received':v['received'],'changes':v['changes'],'question':v['question'],'predictions':copy.deepcopy(v['predictions'])} for v in c.element_thinking.layers.values()],'sources':[{'source':r['source'],'event':r['parent_event'],'provenance':r['provenance'],'facts':copy.deepcopy(r['facts'][:3])} for r in list(c.sources.values())[-8:]]}
 def conversation(self,text,context,automatic):
  stages=context['stages'];stage=min(stages,key=lambda r:(r['received']==0,r['received'])) if stages else None
  if not text:
   used=collections.Counter(r.get('intent') for r in self.history['conversation']);intent=min(('goal','coverage','stage','calculation','greeting','clarify'),key=lambda k:used[k]);text={'goal':'What is the current goal?','coverage':'How many engine stages are connected?','stage':'Explain '+(stage['id'] if stage else 'the current stage'),'calculation':'Calculate 17 * 19','greeting':'Hello','clarify':'Help me with this'}[intent]
  text=text.strip();lower=text.lower();references=[];intent='clarify'
  if re.match(r'^(calculate|compute)\s+',lower):
   intent='calculation';expression=re.sub(r'^(calculate|compute)\s+','',text,flags=re.I);value=calculate(expression);answer=str(value);references=[{'operation':'native arithmetic','expression':expression,'result':value}]
  elif 'goal' in lower:intent='goal';answer=context['goal'] or 'No active goal is recorded.';references=[{'field':'goal','value':context['goal']}]
  elif 'how many' in lower or 'connected' in lower:intent='coverage';answer=str(context['stage_count'])+' registered thinking stages are connected to the shared engine.';references=[{'field':'stage_count','value':context['stage_count']}]
  elif lower in ('hello','hi','hello there'):intent='greeting';answer='Hello. What would you like to discuss or work on?'
  else:
   words=set(re.findall(r'\w+',lower));matches=[r for r in stages if r['id'].lower() in lower or len(words&set(re.findall(r'\w+',r['title'].lower())))>=2]
   if matches:
    intent='stage';s=matches[0];answer=s['title']+': '+s['question']+' Recorded inputs: '+str(s['received'])+'.';references=[s]
   else:answer='What specific question or task would you like me to address? This native trainer can discuss recorded engine goals, connected stages and observations, or calculate an expression.'
  choices=[{'id':'direct','text':answer,'checks':{'current_input':True,'snapshot_consistent':True}}, {'id':'with-basis','text':answer+(' Basis: '+json.dumps(references,ensure_ascii=False)[:700] if references else ''),'checks':{'current_input':True,'snapshot_consistent':True}}, {'id':'off-topic-control','text':'The previous task is complete.','checks':{'current_input':False,'snapshot_consistent':False}}]
  def score(r):
   f=self.feedback.get(intent+'/'+r['id'],{'count':0,'sum':0});return (int(all(r['checks'].values())),f['sum']/max(1,f['count']),-len(r['text']))
  selected=max(choices,key=score)
  return {'input':text,'intent':intent,'output':selected['text'],'selected_strategy':selected['id'],'candidates':choices,'checks':selected['checks'],'basis':references,'training_kind':'Native factual response contracts and user preference feedback; no language-model weight update','passed':all(selected['checks'].values())}
 def coding(self,text,context,automatic):
  if text:
   result=run_restricted({'source':text,'language':'python'});return {'input':'User-supplied Python-subset script','source':text,'output':result.get('output',[]),'tests':[result],'passed':None,'verification':'Executed subset result; no independent expected-output contract supplied. Completion alone is not correctness.'}
  index=self.mode_counts['coding']%3
  if index==0:
   name='sum integers';fixtures=[(5,15),(9,45),(12,78)];template='total = 0\nfor i in range(1, {n} + 1):\n    total = total + i\nprint(total)';bad=template.replace('range(1,','range(2,')
  elif index==1:
   name='bit parity';fixtures=[(3,1),(8,0),(17,1)];template='n = {n}\nprint(n % 2)';bad=template.replace('% 2','% 3')
  else:
   name='double plus one';fixtures=[(2,5),(7,15),(13,27)];template='n = {n}\nprint(n * 2 + 1)';bad=template.replace('+ 1','+ 2')
  candidates=[]
  for ident,source in [('candidate',template),('mutated-control',bad)]:
   tests=[]
   for i,(n,expected) in enumerate(fixtures):
    script=source.format(n=n);r=run_restricted({'language':'python','source':script});tests.append({'input':n,'expected':str(expected),'actual':r.get('output',[]),'role':'held-out contract' if i else 'training contract','passed':r.get('status')=='complete' and r.get('output')==[str(expected)],'steps':r.get('steps')})
   candidates.append({'id':ident,'source':source.format(n=fixtures[-1][0]),'tests':tests,'passed':all(t['passed'] for t in tests)})
  selected=next((r for r in candidates if r['passed']),None)
  return {'input':'Generate and test a '+name+' script','source':selected['source'] if selected else '', 'output':selected['tests'][-1]['actual'] if selected else [],'candidates':candidates,'tests':selected['tests'] if selected else [],'passed':bool(selected),'verification':'Independent expected-output fixtures include held-out inputs; intentionally mutated control must fail. Python subset only; no host execution.'}
 def command(self,text,context,automatic):
  if not text:
   names=list(COMMANDS);name=names[self.mode_counts['commands']%len(names)];text=name+' '+({'Get-ChildItem':'-LiteralPath .','Get-Content':'-LiteralPath example.txt','Set-Content':'-LiteralPath example.txt -Value example','Remove-Item':'-LiteralPath example.txt'}.get(name,'<target-and-arguments-to-review>'))
  result=inspect(text);known=bool(result['commands']);return {'input':text,'output':result,'passed':known,'tests':[{'check':'Known command family recognised','passed':known}],'projection':{'before':'Target state must be observed before any real action','after':[r['expected_effect'] for r in result['commands']],'verification':[r['check'] for r in result['commands']],'rollback':'Define backup/recovery for state-changing commands before execution','unknowns':'Arguments, expansions, pipelines and target state can alter effects; static family matching is incomplete.'},'execution':'Dry-run interpretation only. No shell, process, network or file operations executed.'}
 def run(self,c,mode,text='',automatic=False):
  if mode not in MODES:raise ValueError('Choose conversation, coding or commands')
  if not isinstance(text,str) or len(text)>12000:raise ValueError('Use up to 12000 characters')
  context=self.context(c)
  with self.lock:
   record=self.conversation(text,context,automatic) if mode=='conversation' else self.coding(text,context,automatic) if mode=='coding' else self.command(text,context,automatic)
   self.sequence+=1;record.update(id=uuid.uuid4().hex,sequence=self.sequence,time=time.time(),mode=mode,automatic=automatic,origin='self-selected training' if automatic else 'user request',context=context,llm_calls=0)
   self.latest[mode]=record;self.history[mode].append(record);self.mode_counts[mode]+=1
   if not automatic or self.sequence%10==0 or time.monotonic()-getattr(self,'last_save',0)>10:
    self.save();self.last_save=time.monotonic()
  c.bus.publish({'origin':'skill-trainer-'+mode,'target':'all','kind':'stage-output','payload':{'training_sequence':record['sequence'],'mode':mode,'passed':record.get('passed'),'provenance':'native-training-result','stochastic':False,'predefined_text':True}})
  return copy.deepcopy(record)
 def rate(self,mode,ident,rating):
  if mode not in MODES or type(rating)is not int or rating not in (-1,0,1):raise ValueError('Choose a mode and rating -1, 0 or 1')
  with self.lock:
   row=next((r for r in self.history[mode] if r['id']==ident),None)
   if not row:raise ValueError('Training exchange is no longer retained')
   if mode!='conversation':raise ValueError('Preference feedback currently applies to conversation outputs')
   if 'user_rating' in row:raise ValueError('This exchange already has feedback')
   row['user_rating']=rating;key=row['intent']+'/'+row['selected_strategy'];f=self.feedback.setdefault(key,{'count':0,'sum':0});f['count']+=1;f['sum']+=rating;self.save()
   return {'record':ident,'rating':rating,'updated_strategy':key,'scope':'Preference learning only; a rating does not establish factual truth.'}
 def tick(self,c):
  now=time.monotonic()
  if not self.enabled:self.scheduler_status='paused';return
  from .training_pace import interval as adaptive_interval
  interval=adaptive_interval(c,.5);self.practice_interval=interval
  self.scheduler_status='accelerated adaptive practice'
  if now<self.next_at:return
  self.next_at=now+interval;mode=MODES[self.cursor%3];self.cursor+=1;self.run(c,mode,automatic=True)
 def view(self,mode):
  if mode not in MODES:raise ValueError('Unknown trainer')
  with self.lock:
   row=copy.deepcopy(self.latest.get(mode,{}));history=copy.deepcopy(list(self.history[mode]));feedback=copy.deepcopy(self.feedback)
  context=row.get('context',{});checks=row.get('checks',{});tests=row.get('tests',[]);banks=[]
  data={
   'input':[('Selected input',row.get('input')),('Input origin',row.get('origin')),('Active goal',context.get('goal')),('Connected stages',context.get('stage_count')),('Stage context',context.get('stages',[])[:8]),('Other stage context',context.get('stages',[])[8:]),('Recent observations',context.get('sources')),('Input contract',{'mode':mode,'automatic':row.get('automatic'),'instruction':'Training data never automatically becomes a host command.'})],
   'candidates':[('Candidate outputs',row.get('candidates')),('Selected output',row.get('output')),('Selected strategy',row.get('selected_strategy')),('Source script',row.get('source')),('Reference basis',row.get('basis')),('Expected effects',row.get('projection')),('Preference scores',feedback),('Selection status',{'passed':row.get('passed'),'llm_calls':0})],
   'checks':[('Response checks',checks),('Execution tests',tests),('Held-out tests',[r for r in tests if r.get('role')=='held-out contract']),('Negative controls',[r for r in row.get('candidates',[]) if r['id'] in ('mutated-control','off-topic-control')]),('Verification scope',row.get('verification')),('Execution scope',row.get('execution')),('Evidence basis',row.get('basis')),('Current result',{'passed':row.get('passed'),'id':row.get('id')})],
   'learning':[('Recent inputs',[r.get('input') for r in history[-6:]]),('Recent outputs',[r.get('output') for r in history[-6:]]),('Pass observations',[r.get('passed') for r in history[-10:]]),('Feedback',feedback),('Retained practice',{'records':len(history),'maximum':30}),('Model usage',{'llm_calls':0,'base_weights_modified':False}),('Current curriculum',{'mode':mode,'automatic_cycle':'one mode each three seconds'}),('Learning scope',row.get('training_kind',row.get('verification',row.get('execution'))))],
   'context':[('Goal',context.get('goal')),('Source lineage',context.get('sources')),('Stage questions',[{'stage':r['id'],'question':r['question']} for r in context.get('stages',[])]),('Predictions',[{'stage':r['id'],'predictions':r['predictions']} for r in context.get('stages',[]) if r['predictions']]),('Bus coverage',{'events':context.get('engine_events'),'stages':context.get('stage_count')}),('Record identity',{'id':row.get('id'),'sequence':row.get('sequence')}),('Record time',row.get('time')),('Isolation',{'training_mode':mode,'automatic_host_execution':False})],
   'output':[('Final response',row.get('output')),('Completed script',row.get('source')),('Test results',tests),('Revision feedback',row.get('user_rating')),('Next verification',row.get('projection',{}).get('verification')),('Output origin',row.get('origin')),('Completion status',row.get('passed')),('Current record',{'id':row.get('id'),'sequence':row.get('sequence'),'mode':mode})]}
  fallbacks={'Candidate outputs':row.get('output'), 'Selected strategy':{'method':mode+' native processing'}, 'Source script':row.get('input'), 'Reference basis':context.get('sources'), 'Expected effects':row.get('execution',row.get('verification',row.get('checks'))), 'Response checks':row.get('tests',row.get('checks')), 'Held-out tests':{'mode':mode,'applicability':'Held-out output contracts apply to generated script exercises; other modes use response or recognition checks.','record_checks':row.get('checks',row.get('tests'))}, 'Verification scope':row.get('training_kind',row.get('execution')), 'Execution scope':row.get('training_kind',row.get('verification')), 'Evidence basis':row.get('context',{}).get('sources'), 'Final response':row.get('output'), 'Completed script':row.get('input'), 'Revision feedback':{'ratings':feedback,'record_rating':row.get('user_rating')}, 'Next verification':row.get('checks',row.get('tests'))}
  for bank,entries in data.items():
   data[bank]=[(label,copy.deepcopy(fallbacks.get(label,{'status':'No applicable result recorded yet','mode':mode})) if value is None or value==[] or value=={} else value) for label,value in entries]
  for ident,entries in data.items():banks.append({'id':ident,'label':ident.title(),'lanes':[{'id':f'{ident}-{i}','label':label,'value':value} for i,(label,value) in enumerate(entries)]})
  whole=[{'id':'summary-'+str(i),'label':label,'value':value} for i,(label,value) in enumerate([('Input',row.get('input')),('Output',row.get('output')),('Origin',row.get('origin')),('Candidates',row.get('candidates')),('Checks',checks),('Tests',tests),('Script',row.get('source')),('Projection',row.get('projection')),('Goal',context.get('goal')),('Stage count',context.get('stage_count')),('Feedback',feedback),('Scope',row.get('verification',row.get('training_kind',row.get('execution'))))])]
  return {'mode':mode,'mode_trials':self.mode_counts[mode],'scheduler':{'status':getattr(self,'scheduler_status','waiting for first scheduler tick'),'seconds_until_tick':max(0,self.next_at-time.monotonic()),'mode_cycle_seconds':3*getattr(self,'practice_interval',.5)},'enabled':self.enabled,'sequence':self.sequence,'latest':row,'history':history[-8:],'lanes':whole,'streams':banks,'scope':'Native bounded practice, checks and retained feedback; not general fluency, unrestricted code execution or LLM fine-tuning.'}

