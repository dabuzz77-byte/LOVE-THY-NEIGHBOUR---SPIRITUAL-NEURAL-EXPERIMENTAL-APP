"""Fresh finite capability checks; scores are contracts, not a general intelligence grade."""
import copy,json,random,tempfile,threading,time,types,os
from pathlib import Path

def suite(seed,data=None):
 from .native_skills import respond
 from .native_language import canonical_request
 from .evidence_index import retrieve
 from .cognitive_executive import CognitiveExecutive
 from .teacher_intake import TeacherIntake,TASKS
 rng=random.Random(seed);rows=[]
 def check(domain,name,test):
  start=time.perf_counter()
  try:passed=test() is True;error=None
  except Exception as exc:passed=False;error=type(exc).__name__+': '+str(exc)[:120]
  rows.append({'domain':domain,'name':name,'passed':passed,'elapsed_ms':round((time.perf_counter()-start)*1000,3),'error':error})
 for i in range(12):
  a,b,c=[rng.randint(-500,500) for _ in range(3)]
  check('native-work','arithmetic-'+str(i),lambda a=a,b=b,c=c:respond(f'calculate ({a}+{b})*{c}')['result']==(a+b)*c)
 for i in range(5):
  values=[rng.randint(-20,20) for _ in range(11)];ordered=sorted(values);text=','.join(map(str,values))
  def stats(values=values,ordered=ordered,text=text):
   r=respond('statistics '+text)['result'];return r['count']==11 and r['sum']==sum(values) and r['median']==ordered[5] and r['minimum']==ordered[0] and r['maximum']==ordered[-1]
  check('native-work','statistics-'+str(i),stats)
 check('native-work','CSV quoted-cell handling',lambda:respond('csv to json\nname,note\nA,"two, words"')['result']==[{'name':'A','note':'two, words'}])
 check('native-work','JSON scalar CSV export',lambda:respond('json to csv [{"a":1,"b":"x,y"}]')['result']=='a,b\n1,"x,y"\n')
 check('conversation','natural numeric question',lambda:respond('what is 17 plus 8 times 2?')['result']==33)
 check('conversation','explicit correction',lambda:respond(canonical_request('no, I meant calculate 8+3'))['result']==11)
 check('conversation','literal punctuation preserved',lambda:respond(canonical_request('uppercase is it?'))['result']=='IS IT?')
 check('conversation','Unicode case',lambda:respond('uppercase Straße')['result']=='STRASSE')
 check('conversation','Unicode reversal',lambda:respond('reverse text a😀β')['result']=='β😀a')
 check('conversation','whitespace intent',lambda:respond('normalise whitespace  a\t b\n c')['result']=='a b c')
 for i in range(5):
  a,b,c=[rng.randint(1,40) for _ in range(3)]
  def plan(a=a,b=b,c=c):
   lock=threading.RLock();r=types.SimpleNamespace(s={},user_active=False,controller=types.SimpleNamespace(save=lambda:None));w=types.SimpleNamespace(r=r,lock=lock,record=lambda *args:None,context=lambda:{})
   e=CognitiveExecutive(w);r.workbench=w;g=e.submit(f'compute {a}+{b} then multiply that by {c} then subtract 1 from the result')
   for _ in range(3):e.tick(force=True)
   return g['status']=='complete' and g['steps'][-1]['result']==(a+b)*c-1 and all(s['status']=='verified' for s in g['steps'])
  check('planning','relative dependency chain-'+str(i),plan)
 def negative_plan():
  lock=threading.RLock();r=types.SimpleNamespace(s={});e=CognitiveExecutive(types.SimpleNamespace(r=r,lock=lock))
  try:e.parse('multiply that by 3');return False
  except ValueError:return True
 check('planning','missing antecedent rejected',negative_plan)
 docs=[{'id':'water','title':'Water provision','text':'Clean water supports daily provision and health.','provenance':'test fixture'},{'id':'stars','title':'Stellar study','text':'Hydrogen fusion in stars.','provenance':'test fixture'}]
 check('memory','relevant passage first',lambda:retrieve('clean water',docs)[0]['id']=='water')
 check('memory','unrelated passage abstention',lambda:retrieve('violin orchestration',docs)==[])
 check('memory','no fabricated document',lambda:retrieve('clean water',docs)[0]['text']==docs[0]['text'])
 with tempfile.TemporaryDirectory(dir=data,ignore_cleanup_errors=True) as folder:
  teacher=TeacherIntake(Path(folder))
  for name,task in TASKS.items():
   def learning(name=name,task=task):
    proposal=teacher.submit({'task':name,'teacher':'finite quality fixture','operations':task['operations']})
    sample='Z\nA\nZ\nβ' if 'lines' in name else '  MiXeD 😀  ' if 'text' in name else rng.randint(-500,500)
    result=teacher.run(proposal['id'],sample);reloaded=TeacherIntake(Path(folder));again=reloaded.run(proposal['id'],sample)
    return proposal['retained'] and result['verified'] and result['result']==again['result']
   check('learning','independent skill reuse '+name,learning)
 def reject_bad_csv():
  try:respond('csv to json\na,b\n1');return False
  except ValueError:return True
 check('verification','invalid CSV rejected',reject_bad_csv)
 def reject_nonfinite():
  try:respond('statistics 1,NaN,2');return False
  except ValueError:return True
 check('verification','nonfinite input rejected',reject_nonfinite)
 def command_is_data():return respond('run arbitrary command now') is None
 check('verification','unrecognised command not executed',command_is_data)
 from .reasoning_engine import pipeline,causal,ReasoningEngine
 from .conversation_work import summarise,compare
 for i in range(4):
  values=[rng.randrange(-30,30) for _ in range(17)]
  check('transfer','novel composed dataset-'+str(i),lambda values=values:pipeline(values,[{'op':'filter','relation':'greater','value':0},{'op':'scale','value':3},{'op':'sum'}])['result']==sum(v*3 for v in values if v>0))
 for i in range(4):
  x,delta,a,b=[rng.randrange(1,8) for _ in range(4)]
  check('causal-reasoning','intervention chain-'+str(i),lambda x=x,delta=delta,a=a,b=b:causal({'values':{'x':x},'equations':{'y':{'weights':{'x':a}},'z':{'weights':{'y':b}}},'intervention':{'x':x+delta}})['difference']['z']==delta*a*b)
 def infer_transfer():
  engine=ReasoningEngine({});engine.learn({'name':'clean','examples':[{'input':' A ','expected':'a'},{'input':' B ','expected':'b'},{'input':' NEW ','expected':'new'}]})
  return engine.handle('use workflow: '+json.dumps({'name':'clean','input':'  UNSEEN ÉCOLE  '}))['result']=='unseen école'
 check('learning','infer composition and transfer to unseen text',infer_transfer)
 check('conversation','extractive summary preserves sentences',lambda:all(x['text'] in 'Water supports life. Clean water matters. Water enables health.' for x in summarise('Water supports life. Clean water matters. Water enables health.',2)['extracts']))
 check('planning','explicit option comparison retains tie',lambda:len(compare({'weights':{'welfare':1},'options':[{'name':'a','scores':{'welfare':9}},{'name':'b','scores':{'welfare':9}}]})['selected'])==2)
 from .mind_challenge import challenge
 rows.extend(challenge(seed ^ 0x7F41))
 from .grade_step_challenge import challenge as grade_challenge
 rows.extend(grade_challenge(seed ^ 0xA154))
 from .progress_challenge import challenge as progress_challenge
 rows.extend(progress_challenge(seed))
 from .transfer_dialogue_challenge import challenge as transfer_challenge
 rows.extend(transfer_challenge(seed))
 from .coding_challenge import challenge as coding_challenge
 rows.extend(coding_challenge(seed))
 from .capability_challenge import challenge as capability_challenge
 rows.extend(capability_challenge(seed))
 from .ethical_refinement import review_contract_tests
 ethics=review_contract_tests()
 check('ethical-review','four-way operation-record checks',lambda:ethics['passed']==ethics['total']==8)
 return {'seed':seed,'checks':rows,'passed':sum(r['passed'] for r in rows),'total':len(rows),'all_passed':all(r['passed'] for r in rows),'domains':{d:{'passed':sum(r['passed'] for r in rows if r['domain']==d),'total':sum(r['domain']==d for r in rows)} for d in sorted({r['domain'] for r in rows})},'scope':'Finite native data, conversation-intent, dependency-plan, retrieval and learned-procedure contracts with fresh numeric inputs. Not an A+ certificate, general-language benchmark or model-weight training.'}

class CognitionQuality:
 def __init__(self,data=None):
  self.lock=threading.RLock();self.next_at=0;self.sequence=0;self.latest={};self.history=[];self.busy=False;self.path=Path(data)/'cognition-quality.json' if data else None;self.storage_error=None
  if self.path:
   try:
    if self.path.stat().st_size>262144:raise ValueError('Quality snapshot too large')
    saved=json.loads(self.path.read_text(encoding='utf-8'))
    if saved.get('version')==1 and isinstance(saved.get('latest'),dict) and isinstance(saved.get('recent'),list):
     self.latest=saved['latest'];self.history=saved['recent'][-24:];self.sequence=max(0,int(self.latest.get('sequence',0)))
   except (OSError,ValueError,TypeError,AttributeError):pass

 def tick(self,c):
  if time.monotonic()<self.next_at or c.r.user_active:return
  self.next_at=time.monotonic()+120
  self.run(c)
 def run(self,c):
  with self.lock:
   if self.busy:return self.view()
   self.busy=True
  try:
   started=time.perf_counter();result=suite(time.time_ns()&0xffffffff,c.r.runtime.data)
   with self.lock:
    prior={r['name']:r['passed'] for r in self.latest.get('checks',[])}
    result['regressions']=[r['name'] for r in result['checks'] if not r['passed'] and prior.get(r['name']) is True]
    self.sequence+=1;result.update(sequence=self.sequence,elapsed_ms=round((time.perf_counter()-started)*1000,3),time=time.time(),model_calls=0);self.latest=result;self.history=(self.history+[{'sequence':self.sequence,'passed':result['passed'],'total':result['total'],'elapsed_ms':result['elapsed_ms'],'time':result['time']}])[-24:]
   if self.path:
    try:
     tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps({'version':1,'latest':result,'recent':self.history}),encoding='utf-8');os.replace(tmp,self.path);self.storage_error=None
    except OSError as exc:self.storage_error=type(exc).__name__
   c.bus.publish({'origin':'cognition-quality','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'passed':result['passed'],'total':result['total'],'processing_receipt':True,'provenance':'fresh-finite-native-contracts'}})
  finally:
   with self.lock:self.busy=False
  return self.view()
 def view(self):
  with self.lock:return {'latest':copy.deepcopy(self.latest),'recent':copy.deepcopy(self.history),'busy':self.busy,'storage_error':self.storage_error,'refresh_seconds':120,'scope':'Measured contract coverage, not a self-assigned intelligence grade.'}
