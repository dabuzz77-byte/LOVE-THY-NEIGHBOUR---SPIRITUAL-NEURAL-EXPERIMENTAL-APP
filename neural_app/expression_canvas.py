"""Finite native expression operators on a shared experimental 2D/3D canvas."""
import copy,hashlib,math,random,threading,time
from .action_ethics import study_frame
MODES=['particle field','text constellation','wave study','source graph','3D geometry','drawing composition']
class ExpressionCanvas:
 def __init__(self):self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.frame={};self.history=[];self.rng=random.Random();self.last_modes={};self.last_priority_event=None
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  from .training_pace import interval
  delay=interval(c,self.rng.uniform(.4,1.4));self.next_at=now+delay
  with c.lock:sources=copy.deepcopy(list(c.sources.values()));goal=c.goal
  rows=[r for r in sources if r.get('facts') and r['source']!='expression-canvas']
  priority=getattr(c,'input_attention',{});event_id=priority.get('parent_event');urgent=next((row for row in rows if row['source']==priority.get('source')),None)
  source=urgent if urgent and event_id!=self.last_priority_event else rows[self.sequence%len(rows)] if rows else {'source':'awaiting input','facts':[],'parent_event':None}
  if urgent and event_id!=self.last_priority_event:self.last_priority_event=event_id
  facts=source['facts'][:24]
  mode=max(MODES,key=lambda name:now-self.last_modes.get(name,0)+self.rng.random()*2);self.last_modes[mode]=now;self.sequence+=1
  digest=hashlib.sha256((str(facts)+str(self.sequence)).encode()).hexdigest();seed=int(digest[:16],16);rng=random.Random(seed);points=[]
  for i in range(min(128,max(24,len(facts)*4))):
   angle=i*2.39996323;y=1-2*(i+.5)/min(128,max(24,len(facts)*4));r=math.sqrt(max(0,1-y*y));ordered=[r*math.cos(angle),y,r*math.sin(angle)];chaos=[rng.uniform(-1,1) for _ in range(3)];blend=(self.sequence%9)/8
   point=[ordered[j]*blend+chaos[j]*(1-blend) for j in range(3)]
   fact=facts[i%len(facts)] if facts else {'path':[],'value':0};value=fact.get('value');preview=str(value)[:32]
   points.append({'id':i,'point':point,'vector':[rng.uniform(-.15,.15) for _ in range(3)],'symbol':preview[:1] or '·','preview':preview,'source_path':fact.get('path',[]),'size':2+rng.random()*3})
  selection=getattr(c,'potential_selection',None);decision=selection.stage('expressioncanvas') if selection else {}
  record={'sequence':self.sequence,'time':time.time(),'mode':mode,'points':points,'source':source['source'],'parent_event':source.get('parent_event'),'source_digest':source.get('digest'),'goal':goal,'next_interval_seconds':delay,'dimensions':'2D canvas with 3D points, vectors and perspective projection','supported_operators':MODES,'selection':decision,'ethical_study':study_frame('expressioncanvas',self.sequence),'process':['Read bounded captured source','Select a registered expression operator','Derive geometry and symbols while retaining source paths','Render an isolated experiment','Publish numerical activity feedback'],'execution':'Native local representation only; no code from sources is evaluated','scope':'Six expression operators represent captured app data. This does not execute every app feature or invent unobserved inputs.'}
  with self.lock:self.frame=record;self.history=(self.history+[{'sequence':self.sequence,'mode':mode,'source':source['source']}])[-24:]
  c.bus.publish({'origin':'expression-canvas','target':'all','kind':'stage-output','payload':{'cycle':self.sequence,'points':len(points),'operator':MODES.index(mode),'provenance':'isolated-native-expression-operator','predefined_text':True,'stochastic':False}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'frame':copy.deepcopy(self.frame),'recent':copy.deepcopy(self.history)}
