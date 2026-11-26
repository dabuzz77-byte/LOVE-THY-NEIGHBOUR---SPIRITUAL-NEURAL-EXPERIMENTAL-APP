"""Small immediate native routing model and verified-procedure memory."""
import collections,hashlib,json,math,re,threading,time
from .decision_framework import assess
SEEDS={
 'chat':['hello how are you','explain your answer','discuss this idea','tell me about friendship','what does this mean','help me understand the lesson','answer my question','talk with me'],
 'work':['write a document report','draft an email','create drawing graphics','edit this text','compose music','build a game prototype','write python code','summarise these notes'],
 'network':['search the web','find public sources','research online publications','check internet references','retrieve a public webpage','compare research sources','find latest published evidence','study web documentation'],
 'system':['inspect computer memory','check disk storage','list running processes','show cpu usage','review device backup','diagnose system performance','explain a powershell command','plan operating system repair']}
HOLDOUT=[('chat','hello please talk to me'),('chat','explain this idea please'),('work','draft a report'),('work','create music and graphics'),('network','find online sources'),('network','research public documentation'),('system','check cpu and memory'),('system','inspect running processes')]
def words(text):return re.findall(r'[a-z]{2,}',str(text).lower())[:160]
class NativeStudent:
 def __init__(self,data):
  self.path=data/'native-student-procedures.json';self.lock=threading.RLock();self.counts={k:collections.Counter() for k in SEEDS};self.documents=collections.Counter();self.vocabulary=set();self.procedures=[];self.sequence=0;self.next_at=0;self.latest={}
  for domain,examples in SEEDS.items():
   for text in examples:self.counts[domain].update(words(text));self.documents[domain]+=1;self.vocabulary.update(words(text))
  try:self.procedures=json.loads(self.path.read_text(encoding='utf-8'))[-64:]
  except (OSError,ValueError):pass
 def predict(self,text):
  text=str(text)[:2000]
  if re.search(r'(?i)(password|api.?key|token)\s*[:=]|sk-[A-Za-z0-9_-]{10,}',text):return {'domain':'unknown','needs_clarification':True,'reason':'Secret-like input excluded from routing features'}
  tokens=[w for w in words(text) if w in self.vocabulary];scores={}
  for domain,counter in self.counts.items():scores[domain]=math.log(self.documents[domain]/sum(self.documents.values()))+sum(math.log((counter[w]+1)/(sum(counter.values())+len(self.vocabulary))) for w in tokens)
  maximum=max(scores.values());weights={k:math.exp(v-maximum) for k,v in scores.items()};total=sum(weights.values());probabilities={k:round(v/total,4) for k,v in weights.items()};domain=max(scores,key=scores.get);unclear=not tokens or probabilities[domain]<.38
  return {'domain':'unknown' if unclear else domain,'route_probabilities':probabilities,'needs_clarification':unclear,'next_route':{'chat':'native conversation / configured assistant','work':'native workbench and supported work tools','network':'source-linked public research with operation-specific review','system':'diagnostic or command plan through existing permission-aware tools'}[domain] if not unclear else 'Ask for purpose and desired result','execution':False,'decision_review':assess('routing/'+domain),'model_kind':'Native word-feature routing model, not a generative conversational model'}
 def retain(self,result):
  if not (type(result.get('test_cases'))is int and result['test_cases']>0 and result.get('passed_cases')==result['test_cases']):return
  row={'investigation':result.get('investigation'),'test_cases':result['test_cases'],'passed_cases':result['passed_cases'],'retained':time.time(),'scope':'Verified test outcome reference; retrieve the actual investigation before reusing its procedure'}
  with self.lock:
   if any(r.get('investigation')==row['investigation'] for r in self.procedures):return
   self.procedures=(self.procedures+[row])[-64:];self.path.write_text(json.dumps(self.procedures),encoding='utf-8')
 def tick(self,c=None):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+5;expected,text=HOLDOUT[self.sequence%len(HOLDOUT)];result=self.predict(text);self.sequence+=1
  with self.lock:self.latest={'cycle':self.sequence,'input':text,'expected':expected,'predicted':result['domain'],'passed':result['domain']==expected,'test':'Held-out routing phrase; repeated checks remain repeated checks, not new training examples'}
 def view(self):
  with self.lock:return {'seed_examples':sum(self.documents.values()),'vocabulary_features':len(self.vocabulary),'domains':list(SEEDS),'verified_procedures':copy_rows(self.procedures),'test_cycles':self.sequence,'latest_test':dict(self.latest),'scope':'Immediately seeded native routing and retained verified procedures. Broader chat/work ability still uses existing native skills and configured model assistance.'}
def copy_rows(rows):return [dict(row) for row in rows]
