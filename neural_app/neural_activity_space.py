"""Bounded whole-engine activity graph and parallel learned routing weights."""
import collections,copy,hashlib,math,time
class NeuralActivitySpace:
 def __init__(self):
  self.nodes=collections.OrderedDict();self.edges=collections.OrderedDict();self.sequence=0;self.next_at=0;self.latest={};self.pending=[];self.last_output=0;self.cursor=0
 def observe(self,row,event,stages):
  if row['source']=='neural-activity-space':return
  now=time.time();source='source:'+row['source'];self.node(source,'source',row['source'],row.get('facts',[]),now)
  target=event.get('target','all');targets=list(stages) if target=='all' else [target] if target in stages else []
  for stage in targets:
   ident='stage:'+stage;self.node(ident,'stage',stage,[],now);key=source+'>'+ident;edge=self.edges.get(key,{'source':source,'target':ident,'count':0,'weight':0.,'last':now,'meaning':'observed broadcast delivery eligibility; actual execution requires result evidence'})
   edge['count']+=1;edge['weight']=.9*edge['weight']+.1;edge['last']=now;edge['parent_event']=row.get('parent_event');self.edges[key]=edge;self.edges.move_to_end(key)
  while len(self.edges)>768:self.edges.popitem(last=False)
 def node(self,key,kind,label,facts,now):
  state=self.nodes.get(key,{'id':key,'kind':kind,'label':label,'events':0});state.update(events=state['events']+1,last=now,facts=copy.deepcopy(facts[:4]));self.nodes[key]=state;self.nodes.move_to_end(key)
  while len(self.nodes)>256:self.nodes.popitem(last=False)
 def step(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+max(.1,c.total_plane_sphere.interval);self.sequence+=1;points=[];positions={}
  # Deterministic source centres plus activity-driven radial motion, preserving node identity.
  for key,node in self.nodes.items():
   h=hashlib.sha256(key.encode()).hexdigest();a=int(h[:8],16)/0xffffffff*math.tau;z=2*int(h[8:16],16)/0xffffffff-1;r=math.sqrt(max(0,1-z*z));radius=.85 if node['kind']=='stage' else 1.3;point=[radius*r*math.cos(a),radius*z,radius*r*math.sin(a)];positions[key]=point
   value=node['facts'][0]['value'] if node['facts'] else node['label'];points.append({'id':key,'point':point,'phase':1 if node['kind']=='stage' else .5,'selected':time.time()-node['last']<3,'symbol':str(value)[:1] or '·','value_preview':str(value)[:120],'source':node['label'],'events':node['events']})
  sphere_frames=[c.expression_sphere.latest,c.selection_sphere.latest,c.selection_sphere.unmodulated,c.system_flux_sphere.view(),c.system_flux_sphere.inverse_view(),c.experiment_sphere.view(),c.total_plane_sphere.view(),c.potential_zero_sphere.view()]
  for i,frame in enumerate(sphere_frames):
   data=frame.get('particles',[]);offset=self.cursor%max(1,len(data));sample=(data[offset:]+data[:offset])[:32]
   for p in sample:
    point=copy.deepcopy(p);point['id']='sphere'+str(i)+':'+point['id'];points.append(point)
  self.cursor+=32
  edges=[{**copy.deepcopy(e),'from':positions[e['source']],'to':positions[e['target']]} for e in self.edges.values() if e['source'] in positions and e['target'] in positions]
  active=sorted(self.nodes.values(),key=lambda n:(-(time.time()-n['last']<3),-n['events']))[:8]
  self.latest={'sequence':self.sequence,'updated_at':time.time(),'particles':points,'connections':edges,'goal':c.goal,'received_events':c.sequence,'retained_sources':len(c.sources),'represented_values':len(points),'selected_phases':[0,.25,.5,.75,1],'self_selection':{'mode':'recency and observed activity; round-robin sphere samples; native controller','focus':[n['label'] for n in active],'controller':c.self_controller.view()},'behaviour_catalog':{'registered_actions':c.action_definitions.view()['definitions'],'sphere_behaviours':c.total_plane_sphere.latest.get('behaviours',[]),'adaptive_rates':c.adaptive_rail.view()},'network_weights':{'method':'exponential update per observed source-to-stage broadcast; no gradient-trained semantic network','edges':len(edges),'nodes':len(self.nodes)},'scope':'All captured registered-stage sources eligible. Bounded graph and rotating sphere samples; edges show routing observations, not every machine instruction or proof of causation.'}
  if time.monotonic()-self.last_output>2:
   self.last_output=time.monotonic();self.pending.append({'origin':'neural-activity-space','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'focus':[n['label'] for n in active],'nodes':len(self.nodes),'connections':len(edges),'provenance':'observed-routing-summary','processing_receipt':True,'selection_trace':True}})
 def view(self):return copy.deepcopy(self.latest or {'sequence':0,'particles':[]})
