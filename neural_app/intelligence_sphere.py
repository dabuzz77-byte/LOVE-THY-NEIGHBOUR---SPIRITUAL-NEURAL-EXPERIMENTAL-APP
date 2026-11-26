"""Source-traceable bounded 3D projection of captured whole-engine flow."""
import collections,hashlib,math,random,time,copy
class IntelligenceSphere:
 def __init__(self,self_selecting=False):self.sources=collections.OrderedDict();self.sequence=0;self.received=0;self.cursor=0;self.latest={};self.unmodulated={};self.rng=random.SystemRandom();self.self_selecting=self_selecting
 def observe(self,row,event):
  if row['source']=='intelligence-expression-sphere':return
  p=event.get('payload') or {};facts=copy.deepcopy(p.get('expression_values',[])) if isinstance(p,dict) else []
  if isinstance(p,dict) and isinstance(p.get('text'),str):facts.insert(0,{'path':['completed_ascii'],'value':p['text'],'type':'str'})
  facts=facts or row['facts']
  self.received+=1;self.sources[row['source']]={'source':row['source'],'parent_event':row['parent_event'],'digest':row['digest'],'facts':copy.deepcopy(facts),'units':copy.deepcopy(row['units'])};self.sources.move_to_end(row['source'])
  while len(self.sources)>128:self.sources.popitem(last=False)
 def step(self,choices,goal,modulation=None):
  rows=list(self.sources.values());samples=[]
  if rows:
   start=self.cursor%len(rows);ordered=rows[start:]+rows[:start]
   for row in ordered[:64 if self.self_selecting else 128]:
    if row['facts']:
     fact=row['facts'][(self.sequence//max(1,len(rows)))%len(row['facts'])];samples.append({**fact,'source':row['source'],'parent_event':row['parent_event'],'digest':row['digest']})
   self.cursor+=1
  selected=set()
  for choice in choices:
   states=choice.get('phase_candidates',[])
   for indices in choice.get('parallel_selection_groups',{}).values():
    for i in indices:
     if i<len(states):selected.add(states[i]['phase'])
  if not selected:selected={.5}
  particles=[];n=max(1,len(samples));golden=math.pi*(3-math.sqrt(5))
  for i,sample in enumerate(samples):
   text=str(sample['value']);path_text=str(sample['path']).lower();form='variable'
   if type(sample['value']) is int:form='integer'
   elif type(sample['value']) is float:form='float'
   elif isinstance(sample['value'],str):
    form='bit-string' if text and set(text)<=set('01') else 'trit-string' if text and set(text)<=set('012') else 'sentence' if any(c in text for c in '.!?') else 'word' if ' ' not in text else 'string'
   for tag in ('ascii','code','vector','point','wave','geometry'):
    if tag in path_text:form=tag;break
   digest=hashlib.sha256((sample['source']+str(sample['path'])).encode()).hexdigest();y=1-2*(i+.5)/n;ring=math.sqrt(max(0,1-y*y));order=[ring*math.cos(i*golden),y,ring*math.sin(i*golden)]
   z=self.rng.uniform(-1,1);angle=self.rng.uniform(0,math.tau);radius=self.rng.random()**(1/3);r=math.sqrt(1-z*z);chaos=[radius*r*math.cos(angle),radius*z,radius*r*math.sin(angle)]
   for phase in (0.,.25,.5,.75,1.):
    point=[(chaos[k]*(1-phase)+order[k]*phase)*(1+phase*.4) for k in range(3)]
    for autonomy in ((0.,.25,.5,.75,1.) if self.self_selecting else (0.,)):
     choice=choices[i%len(choices)] if choices else None;adopt=bool(choice) and (autonomy==1 or (autonomy>0 and int(digest[:4],16)/65535<autonomy));expression=str(choice['value']) if adopt else text;position=[v*(1+autonomy*.12) for v in point]
     particles.append({'id':digest[:16]+':'+str(phase)+':'+str(autonomy),'point':position,'phase':phase,'autonomy':autonomy,'selected':phase in selected and (adopt or not self.self_selecting),'expression_type':choice.get('kind',form) if adopt else form,'symbol':expression[:1] or '·','value_preview':expression[:120],'source':sample['source'],'selected_source':choice.get('source') if adopt else None,'path':sample['path'],'parent_event':sample['parent_event'],'order_index':i,'source_digest':sample['digest']})
  self.sequence+=1;self.latest={'sequence':self.sequence,'self_selecting':self.self_selecting,'autonomy_lanes':[0,.25,.5,.75,1] if self.self_selecting else [0],'received_events':self.received,'retained_sources':len(rows),'represented_values':len(samples),'particles':particles,'selected_phases':sorted(selected),'goal':goal,'represented_forms':sorted({p['expression_type'] for p in particles}),'phase_lanes':[0,.25,.5,.75,1],'scope':'All observed bus sources enter a bounded capture index. Finite phase/autonomy samples are displayed simultaneously; selection adoption and geometry retain source references.'}
  self.unmodulated=copy.deepcopy(self.latest);self.unmodulated['modulation']={'enabled':False,'comparison':'Same frame, source samples, random positions and selections, before waveform offsets'}
  if modulation:
   amount=modulation.get('applied',0)
   for p in particles:
    distance=math.sqrt(sum(v*v for v in p['point']));gain=amount/(1+distance);p['point']=[v+gain*(1 if k!=1 else -1) for k,v in enumerate(p['point'])]
   self.latest['modulation']=copy.deepcopy(modulation)
  return self.latest
 def view(self):return self.latest or {'sequence':0,'particles':[],'retained_sources':len(self.sources)}
