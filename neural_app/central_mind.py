"""Compact persistent controller state; measurements and checks run without an LLM."""
import collections,hashlib,json,threading,time
class CentralMind:
 def __init__(self,data=None):
  self.lock=threading.RLock();self.path=data/'central-controller.json' if data else None;self.state={'goal':'','tasks':[],'plans':[],'lessons':[],'events':[],'attention':[],'observations':{},'model_calls':0,'checks':0,'weights':{'relevance':1.0,'novelty':.8,'reliability':1.0,'processing_cost':.7}};self.phase='observe'
  if self.path:
   try:self.state.update(json.loads(self.path.read_text(encoding='utf-8')))
   except (OSError,ValueError):pass
 def save(self):
  with self.lock:
   if self.path:
    self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.state,default=str),encoding='utf-8');tmp.replace(self.path)
 def event(self,phase,detail):
  self.phase=phase;self.state['events']=(self.state['events']+[{'time':time.time(),'phase':phase,'detail':str(detail)[:240]}])[-24:]
 def goal(self,text):
  with self.lock:
   text=str(text)[:4000]
   if text!=self.state['goal']:
    self.state['goal']=text
    if text:self.state['tasks']=(self.state['tasks']+[{'goal':text,'created':time.time(),'status':'open','completion':'requires verified task-specific result or user confirmation'}])[-12:]
    self.event('remember','Current goal updated');self.save()
 def weights(self,values):
  import math
  with self.lock:
   clean=dict(self.state['weights'])
   for key,value in values.items():
    if key not in clean:raise ValueError('Unknown controller weight: '+key)
    value=float(value)
    if not math.isfinite(value) or value<0:raise ValueError('Weights must be finite and nonnegative')
    clean[key]=value
   self.state['weights']=clean;self.save();return clean
 def observe(self,streams):
  with self.lock:
   prior=self.state['observations'];rows=[];now={}
   for s in streams[:32]:
    text=str(s.get('text',''))[:512];name=str(s.get('name','generated'));digest=hashlib.sha256(text.encode()).hexdigest();now[name]=digest
    counts=collections.Counter(text);rows.append({'source':name,'changed':prior.get(name)!=digest,'characters':len(text),'distinct':len(counts),'digest':digest,'sample':text[:32]})
   weights=self.state['weights'];words=set(self.state['goal'].lower().split())
   for row in rows:
    relevant=len(words&set(row['source'].lower().split()));lessons=[l for l in self.state['lessons'] if l.get('engine')==row['source']];reliability=sum(l['outcome']=='verified' for l in lessons)/len(lessons) if lessons else .5
    row['attention_score']=weights['novelty']*row['changed']+weights['relevance']*relevant+weights['reliability']*reliability-weights['processing_cost']*row['characters']/16384
   rows.sort(key=lambda x:x['attention_score'],reverse=True);self.state['attention']=rows[:4];self.state['observations']=now
   changed=any(r['changed'] for r in rows);self.event('observe','Changed sources: '+str(sum(r['changed'] for r in rows))) if changed else None
   return {'changed':changed,'focus':rows[:4]}
 def plan(self,sequence,choices,streams,model_used=True):
  with self.lock:
   plans=[]
   available=[s for s in streams if s.get('text')]
   for c in choices[:4]:
    index=int(c['id'].split('>')[0]);source=available[index%len(available)] if available else {};text=str(source.get('text',''))[:256];raw=text.encode()[:256]
    expected=[b^255 if c['state']=='evil' else b for b in raw]
    p={'key':str(sequence)+':'+c['id'],'sequence':sequence,'route':c['id'],'from':c['from'],'engine':c['to'],'input':{'source':source.get('name'),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'state':c['state'],'expected':{'transform':'flip' if c['state']=='evil' else 'hold','sample':expected[:32]},'completion_condition':'successful destination receipt and byte transformation match; backend processing checked separately','status':'planned','backend_status':'not submitted'};plans.append(p)
   self.state['plans']=(self.state['plans']+plans)[-48:];self.state['model_calls']+=int(model_used);self.state['rule_decisions']=self.state.get('rule_decisions',0)+int(not model_used);self.event('choose',str(len(plans))+' bounded route plans');self.save();return plans
 def check(self,sequence,receipts):
  with self.lock:
   for p in self.state['plans']:
    if p['sequence']!=sequence:continue
    r=next((v for v in receipts if v.get('id')==p['route']),None)
    if not r:continue
    before=r.get('before');after=r.get('after');valid=isinstance(before,list) and isinstance(after,list) and len(before)==len(after) and len(before)>0
    match=valid and after==[b^255 if p['state']=='evil' else b for b in before]
    p['status']='verified' if r.get('applied') is True and match else 'failed';p['actual']={'applied':r.get('applied') is True,'transformation_matches':bool(match),'expected_sample_matches':after==p['expected']['sample'],'error':r.get('error')};self.state['checks']+=1
    lesson={'route':p['route'],'engine':p['engine'],'state':p['state'],'outcome':p['status'],'time':time.time()};self.state['lessons']=(self.state['lessons']+[lesson])[-32:]
   self.event('check','Compared actual route bytes and applied receipts');self.event('learn','Retained route successes / failures; goal remains open');self.save()
 def backend(self,decisions):
  with self.lock:
   lookup={(d['sequence'],j.get('choice')):j for d in decisions for j in d.get('backend_jobs',[])}
   for p in self.state['plans']:
    j=lookup.get((p['sequence'],p['route']))
    if j:p['backend_status']=j.get('status');p['backend_receipt']=j.get('receipt')
 def view(self):
  with self.lock:return json.loads(json.dumps({'phase':self.phase,**{k:v for k,v in self.state.items() if k!='reasoning'},'reasoning_summary':{k:self.state.get('reasoning',{}).get(k,0) for k in ('model_calls','rule_requests','pattern_tests','observed_events')}},default=str))
