"""Local user interaction observations with explicit privacy and evidence boundaries."""
from contextlib import closing
import collections,hashlib,json,re,sqlite3,threading,time
INTENTS={'question':r'\b(what|why|how|when|where|explain|does|can)\b','create':r'\b(create|build|make|generate|write|draw|compose)\b','change':r'\b(change|edit|fix|replace|remove|increase|decrease|improve)\b','analyse':r'\b(analy[sz]e|compare|assess|study|review|evaluate)\b','test':r'\b(test|verify|check|benchmark|validate)\b','correction':r'\b(wrong|instead|correction|meant|actually)\b'}
SENSITIVE=re.compile(r'password|passwd|secret|token|credential|api.?key|authorization|private.?key|account|email|card.?number',re.I)
def sanitise(text):
 text=str(text)[:2000]
 if re.search(r'(?i)(?:bearer\s+\S+|sk-[A-Za-z0-9_-]{10,}|-----BEGIN .*PRIVATE KEY|(?:password|api.?key|token)\s*[:=]\s*\S+)',text):return None
 text=re.sub(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}','[email omitted]',text)
 text=re.sub(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)','[long numeric identifier omitted]',text)
 return text
class InteractionLearning:
 def __init__(self,data):
  self.path=data/'interaction-learning.sqlite3';self.settings=data/'interaction-learning-settings.json';self.lock=threading.RLock();self.enabled=True;self._context=None
  try:self.enabled=bool(json.loads(self.settings.read_text(encoding='utf-8')).get('enabled',True))
  except (OSError,ValueError):pass
  with closing(sqlite3.connect(self.path)) as db,db:db.execute('create table if not exists observations(id text primary key,section text,kind text,field text,intents text,text text,details text,created real)')
 def configure(self,b):
  if type(b.get('enabled')) is not bool:raise ValueError('Enabled must be boolean')
  with self.lock:self.enabled=b['enabled'];self.settings.write_text(json.dumps({'enabled':self.enabled}),encoding='utf-8')
  return self.view()
 def observe(self,b,c):
  self._context=None
  section=str(b.get('section','unknown'))[:80];field=str(b.get('field',''))[:120];kind=b.get('kind')
  if kind not in ('text','control','outcome'):raise ValueError('Unsupported interaction kind')
  if not self.enabled:return {'recorded':False,'reason':'paused'}
  if section in ('privatevision','googleworkspace','activity') or SENSITIVE.search(field):return {'recorded':False,'reason':'private field or section excluded'}
  text=sanitise(b.get('text','')) if kind=='text' else ''
  if text is None:return {'recorded':False,'reason':'credential-like content excluded'}
  intents=[k for k,p in INTENTS.items() if re.search(p,text or '',re.I)] if kind=='text' else ['operation-result' if kind=='outcome' else 'control-choice']
  details={'evidence':'User interaction; not established world truth','learning':'Intent/preference observation; temporal association is not causation'}
  if kind=='outcome':details.update(operation=str(b.get('operation',''))[:100],success=b.get('success') is True)
  else:details['value']=sanitise(b.get('value',''))[:100] if kind=='control' and sanitise(b.get('value','')) is not None else None
  ident=hashlib.sha256(json.dumps([section,field,kind,text,details],sort_keys=True).encode()).hexdigest()
  with self.lock,closing(sqlite3.connect(self.path,timeout=5)) as db,db:
   exists=db.execute('select 1 from observations where id=?',(ident,)).fetchone()
   if exists:return {'recorded':False,'reason':'duplicate observation'}
   db.execute('insert into observations values(?,?,?,?,?,?,?,?)',(ident,section,kind,field,json.dumps(intents),text,json.dumps(details),time.time()));db.execute('delete from observations where id not in (select id from observations order by created desc limit 500)')
  c.bus.publish({'origin':'interaction-learning','target':'all','kind':'stage-output','payload':{'intent_count':len(intents),'user_observation':True,'provenance':'local-interaction-metadata','predefined_text':True,'stochastic':False}})
  return {'recorded':True,'id':ident,'intents':intents,'scope':'Text stays in local observation storage; only numerical metadata enters the shared bus.'}
 def clear(self):
  self._context=None
  with self.lock,closing(sqlite3.connect(self.path)) as db,db:db.execute('delete from observations')
  return self.view()
 def context(self):
  if not self.enabled:return {}
  if self._context is not None:return self._context
  with self.lock,closing(sqlite3.connect(self.path)) as db,db:row=db.execute("select section,intents,text from observations where kind='text' order by created desc limit 1").fetchone()
  self._context={'section':row[0],'candidate_intents':json.loads(row[1]),'user_text':row[2],'basis':'Local user expression; candidate intent, not a verified fact or action authorization'} if row and self.enabled else {}
  return dict(self._context)
 def view(self):
  with self.lock,closing(sqlite3.connect(self.path,timeout=5)) as db,db:rows=db.execute('select section,kind,field,intents,text,details,created from observations order by created desc limit 30').fetchall();count=db.execute('select count(*) from observations').fetchone()[0]
  records=[{'section':a,'kind':b,'field':d,'intents':json.loads(e),'text':f,'details':json.loads(g),'time':h} for a,b,d,e,f,g,h in rows]
  return {'enabled':self.enabled,'count':count,'recent':records,'four_way':{'true_good':'Learn useful intent and corrections from chosen app interactions','false_good':'Call indiscriminate recording helpful while concealing privacy costs','false_evil':'Block ordinary local interaction learning despite informed choice','true_evil':'Capture credentials, private account fields or other people’s communications without permission'},'scope':'Neural App interactions only; no global keyboard recorder or screen capture. Outside activity requires separately paired connectors. This is local intent memory, not LLM weight training.'}
