"""Persistent investigation records with source evidence and isolated experiments."""
import copy,hashlib,json,sqlite3,time,uuid,re
from contextlib import contextmanager
from pathlib import Path
class Investigations:
 def __init__(self,data):
  self.path=Path(data)/'investigations.sqlite3';self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.connect() as db:
   db.execute('create table if not exists investigations(id text primary key,question text,record text,updated real)')
   db.execute('create virtual table if not exists investigation_search using fts5(ident UNINDEXED,question,body,status UNINDEXED)')
   db.execute('create table if not exists investigation_revisions(ident text,revision integer,record text,stamp real,primary key(ident,revision))')
   db.execute('create table if not exists native_procedures(ident text primary key,record text)')
   if db.execute('select count(*) from investigation_search').fetchone()[0]!=db.execute('select count(*) from investigations').fetchone()[0]:
    db.execute('delete from investigation_search')
    for ident,q,raw in db.execute('select id,question,record from investigations').fetchall():db.execute('insert into investigation_search values(?,?,?,?)',(ident,q,raw,json.loads(raw)['status']))
 @contextmanager
 def connect(self):
  db=sqlite3.connect(self.path,timeout=5)
  try:
   with db:yield db
  finally:db.close()
 def create(self,question,evidence=None):
  question=str(question).strip()[:2000]
  if not question:raise ValueError('Provide an investigation question')
  ident=uuid.uuid4().hex
  row={'id':ident,'question':question,'status':'needs-experiment','evidence':copy.deepcopy((evidence or [])[:20]),'hypotheses':[],'experiments':[],'conclusion':None,'revision':1,'assessment':{'principles':['essential needs','protection','forgiveness and repair','avoid deception','accountability'],'alternatives':['act','wait','correct','disruptive-change-in-isolated-model'],'scope':'Consequences for affected parties; institutions and proposed interventions both require scrutiny.'},'missing':['a discriminating experiment','affected parties and dependencies','independent outcome evidence']}
  self.save(row);return row
 def save(self,row):
  raw=json.dumps(row,ensure_ascii=True)
  with self.connect() as db:
   db.execute('insert or replace into investigations values(?,?,?,?)',(row['id'],row['question'],raw,time.time()))
   db.execute('delete from investigation_search where ident=?',(row['id'],));db.execute('insert into investigation_search values(?,?,?,?)',(row['id'],row['question'],raw,row['status']))
   db.execute('insert or replace into investigation_revisions values(?,?,?,?)',(row['id'],row['revision'],raw,time.time()))
 def revisions(self,ident):
  with self.connect() as db:rows=db.execute('select revision,stamp,record from investigation_revisions where ident=? order by revision',(ident,)).fetchall()
  return [{'revision':r,'time':t,'status':json.loads(raw)['status']} for r,t,raw in rows]
 def set_spec(self,ident,spec):
  from .native_synthesis import validate
  row=self.get(ident);row['experiment_spec']=validate(spec);row['revision']+=1;row['status']='needs-experiment';self.save(row);return row
 def procedures(self):
  with self.connect() as db:return [json.loads(r[0]) for r in db.execute('select record from native_procedures')]
 def use_procedure(self,ident,value):
  from .native_synthesis import execute
  with self.connect() as db:r=db.execute('select record from native_procedures where ident=?',(ident,)).fetchone()
  if not r:raise ValueError('Unknown learned procedure')
  skill=json.loads(r[0])
  if not skill.get('active'):raise ValueError('Procedure requires revalidation after conflicting evidence')
  return {'procedure':ident,'operations':skill['operations'],'input':value,'output':execute(skill['operations'],copy.deepcopy(value)),'scope':'Execution of a retained pure program; success outside its learned contract needs verification.'}
 def get(self,ident):
  with self.connect() as db:r=db.execute('select record from investigations where id=?',(ident,)).fetchone()
  if not r:raise ValueError('Investigation not found')
  return json.loads(r[0])
 def test(self,ident):
  from .investigation_models import choose,experiment
  row=self.get(ident)
  from .native_synthesis import question_spec,synthesize
  spec=row.get('experiment_spec') or question_spec(row['question'])
  if spec:
   result=synthesize(spec);result['time']=time.time();row['experiments'].append(result);row['experiments']=row['experiments'][-20:];row['revision']+=1
   winner=result['solution'];row['status']='contract-validated' if winner else 'needs-better-hypothesis';row['conclusion']={'question_answered':bool(winner),'scope':'Specified software example contract only','tested':winner or 'No candidate passed the held-out contract within the search budget.'}
   if winner:
    ident_skill=hashlib.sha256(json.dumps([row['id'],winner['operations']],sort_keys=True).encode()).hexdigest()[:20]
    skill={'id':ident_skill,'source_investigation':row['id'],'question':row['question'],'operations':winner['operations'],'training_cases':result['training_cases'],'held_out_cases':result['held_out_cases'],'active':True,'validation':'held-out example contract'}
    with self.connect() as db:db.execute('insert or replace into native_procedures values(?,?)',(ident_skill,json.dumps(skill)))
    row['learned_procedure']=ident_skill
   self.save(row);return row
  model=choose(row['question'])
  if not model:
   row.update(status='needs-question-specific-model',conclusion={'question_answered':False,'next':'Define measurable inputs, competing predictions and an isolated test relevant to this question.'});self.save(row);return row
  result=experiment(model,int(uuid.uuid4().hex[:8],16));result['time']=time.time();row['experiments'].append(result);row['experiments']=row['experiments'][-20:]
  row['hypotheses']=[{'name':o['hypothesis'],'passed':o['passed'],'cases':o['cases']} for o in result['observations']]
  row['revision']+=1;row['status']='local-test-complete; question-open';row['conclusion']={'tested':result['conclusion'],'question_answered':False,'next':'Check applicability and dependencies before using the result outside this model.'};row['missing']=['real-system applicability','affected parties and dependencies','independent outcome evidence'];self.save(row);return row
 def add_evidence(self,ident,item):
  row=self.get(ident);text=str(item.get('claim','')).strip()[:2000]
  if not text:raise ValueError('Provide a claim')
  entry={'claim':text,'source':str(item.get('source','user supplied'))[:500],'relation':item.get('relation','context'),'status':'source assertion; not independently verified','time':time.time()}
  if entry['relation'] not in ('support','contradict','context'):raise ValueError('Relation must be support, contradict or context')
  if entry['relation']=='contradict':
   row['requires_revalidation']=True
   with self.connect() as db:
    for ident_skill,raw in db.execute('select ident,record from native_procedures').fetchall():
     skill=json.loads(raw)
     if skill.get('source_investigation')==ident:skill['active']=False;db.execute('update native_procedures set record=? where ident=?',(json.dumps(skill),ident_skill))
  entry['id']=hashlib.sha256((entry['source']+'\n'+text).encode()).hexdigest()
  if any(e.get('id')==entry['id'] for e in row['evidence']):return row
  row['evidence'].append(entry);row['evidence']=row['evidence'][-50:];row['revision']+=1;row['status']='evidence-updated';self.save(row);return row
 def tick(self):
  if time.monotonic()<getattr(self,'next_tick',0):return
  self.next_tick=time.monotonic()+5
  with self.connect() as db:found=db.execute("select id from investigations where record like ? order by updated asc limit 1",('%needs-experiment%',)).fetchone()
  if found:self.test(found[0])
 def assess_scenario(self,ident,scenario):
  from .causal_assessment import compare
  row=self.get(ident);row['consequence_assessment']=compare(scenario);row['scenario']=scenario;row['revision']+=1;self.save(row);return row
 def pending_models(self):
  with self.connect() as db:rows=db.execute("select record from investigations where record like ? order by updated asc limit 4",('%\"status\": \"needs-question-specific-model\"%',)).fetchall()
  return [json.loads(r[0]) for r in rows]
 def retrieve(self,query):
  words=re.findall(r'[^\W_]+',str(query),re.UNICODE)[:16]
  if not words:return []
  match=' OR '.join('"'+w+'"' for w in words)
  with self.connect() as db:rows=db.execute('select ident,question,body,status from investigation_search where investigation_search match ? order by bm25(investigation_search,0,8,1,0) limit 6',(match,)).fetchall()
  return [{'type':'investigation','id':ident,'title':q,'excerpt':json.dumps(json.loads(raw).get('conclusion') or json.loads(raw).get('missing')),'source':'local investigation','status':status} for ident,q,raw,status in rows]
 def view(self):
  with self.connect() as db:
   rows=db.execute('select record from investigations order by updated desc limit 12').fetchall();total=db.execute('select count(*) from investigations').fetchone()[0]
  return {'items':[json.loads(r[0]) for r in rows],'total_records':total,'search_scope':'all persisted investigations; display shows latest twelve','learned_procedures':self.procedures(),'workflow':['question','sources','competing hypotheses','safe discriminating test','prediction','observation','four-way assessment','revision','transfer test'],'status':'persistent native investigation workspace'}
