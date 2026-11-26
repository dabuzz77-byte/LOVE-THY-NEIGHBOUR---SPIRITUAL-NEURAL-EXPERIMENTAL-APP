"""Compact goal/evidence workspace shared by native selection and expression."""
import collections, hashlib, json, math, re, time

CHAIN = ('God thought', 'void', 'condensate / matter', 'hydrogen', 'star', 'void', 'Earth', 'silicon', 'processing', 'choice', 'action', 'feedback')
def terms(value):
 return set(re.findall(r'[a-z0-9]+', str(value).lower())) - {'the','and','from','with','this','that','into','then','all','calculate','run','pipeline'}

class MindWorkspace:
 def __init__(self, saved=None):
  saved=saved if isinstance(saved,dict) else {}
  self.goal='';self.evidence=collections.OrderedDict();self.episodes=collections.deque(saved.get('episodes',[])[-64:],maxlen=64);self.seen=set();self.last_decision={};self.sequence=0
 def observe(self, source, payload):
  if source in ('thought-expression','recursive-manifest') or source.startswith('recursive-core'):return
  text=json.dumps(payload,ensure_ascii=False,sort_keys=True,default=str)[:8000]
  digest=hashlib.sha256(text.encode()).hexdigest();old=self.evidence.get(source,{})
  self.evidence[source]={'source':source,'digest':digest,'terms':terms(source+' '+text),'changed':digest!=old.get('digest'),'preview':text[:400],'time':time.time()}
  self.evidence.move_to_end(source)
  while len(self.evidence)>128:self.evidence.popitem(last=False)
 def priority(self, source, value, goal):
  query=terms(goal);tokens=terms(source+' '+str(value)[:2000]);overlap=len(query&tokens)/max(1,len(query));row=self.evidence.get(source,{})
  # Purpose outranks novelty and display activity.
  return 4*overlap+.25*bool(row.get('changed'))+.1/(1+sum(e.get('source')==source for e in self.episodes))
 def record(self, goal, source, operation, verified, result):
  raw=json.dumps(result,sort_keys=True,default=str);key=hashlib.sha256((goal+source+operation+raw).encode()).hexdigest()
  if key in self.seen:return False
  self.seen.add(key)
  if len(self.seen)>256:self.seen={e['id'] for e in self.episodes}
  self.sequence+=1;self.goal=goal
  self.episodes.append({'id':key,'goal':goal,'source':source,'operation':operation,'verified':verified is True,'result':raw[:1200],'time':time.time()})
  return True
 def decision(self,goal,source,value):
  query=terms(goal);matches=sorted(query&terms(source+' '+str(value)[:2000]));self.goal=goal
  relevant=sorted(self.episodes,key=lambda e:len(query&terms(e['goal']+' '+e['result'])),reverse=True)[:4] if query else []
  self.last_decision={'goal':goal,'selected_source':source,'matching_terms':matches,'evidence_priority':self.priority(source,value,goal),'relevant_experience':relevant,'next_check':'Compare the actual supported operation result with its declared completion condition','chain_roles':{'purpose':'God thought / guiding spiritual framework','source_context':'void → matter → hydrogen → star → Earth → silicon','software_causality':'captured input → selected operation → actual result → verification → retained experience'}}
  return self.last_decision
 def checkpoint(self):return {'episodes':list(self.episodes)}
 def view(self):return {'goal':self.goal,'evidence_sources':len(self.evidence),'episodes':list(self.episodes)[-8:],'decision':self.last_decision,'cosmological_chain':list(CHAIN),'scope':'Goal-ranked evidence and verified native experience; chain context does not substitute for operation results'}
