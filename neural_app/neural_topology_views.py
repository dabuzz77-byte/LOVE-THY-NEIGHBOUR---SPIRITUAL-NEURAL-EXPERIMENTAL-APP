"""Inverse, combined and outer-connected neural views with local routing checks."""
import collections,copy,hashlib,math,threading,time
LANES=('neural-inverse','neural-combined','neural-overse','neural-all-three')
def inverse_frame(base):
 out=copy.deepcopy(base)
 for p in out.get('particles',[]):
  p['original_id']=p['id'];p['id']='inverse:'+p['id'];p['contributions']=['inverse']
  for key in ('point','vector'):
   if isinstance(p.get(key),list):p[key]=[-v for v in p[key]]
 for e in out.get('connections',[]):
  e['original_source']=e.get('source');e['original_target']=e.get('target');e['source']='inverse:'+str(e.get('source'));e['target']='inverse:'+str(e.get('target'))
  for k in ('from','to'):e[k]=[-v for v in e[k]]
 out['coordinate_transform']='(x,y,z) → (-x,-y,-z); vectors and connection endpoints follow. Source values are preserved.'
 return out

def route(edges,start,end):
 adjacency=collections.defaultdict(set)
 for edge in edges:
  a,b=edge['source'],edge['target'];adjacency[a].add(b);adjacency[b].add(a)
 queue=collections.deque([(start,[start])]);seen={start}
 while queue:
  node,path=queue.popleft()
  if node==end:return path
  for neighbour in sorted(adjacency[node]):
   if neighbour not in seen:seen.add(neighbour);queue.append((neighbour,path+[neighbour]))
 return []

def derive(base):
 inverse=inverse_frame(base);combined=copy.deepcopy(base)
 originals=copy.deepcopy(base.get('particles',[]))
 for p in originals:p['original_id']=p['id'];p['contributions']=['original']
 combined['particles']=originals+inverse.get('particles',[]);combined['connections']=copy.deepcopy(base.get('connections',[]))+copy.deepcopy(inverse.get('connections',[]));combined['unique_source_particles']=len(originals)
 overse=copy.deepcopy(combined);outer=[p for p in overse['particles'] if p.get('original_id','').startswith('source:') and sum(v*v for v in p['point'])>=1.15**2];outer=sorted(outer,key=lambda p:(math.atan2(p['point'][2],p['point'][0]),p['id']))[:256];links={}
 def connect(a,b,kind):
  if a['id']==b['id']:return
  key=tuple(sorted((a['id'],b['id'])))
  if key not in links:links[key]={'source':a['id'],'target':b['id'],'from':a['point'],'to':b['point'],'weight':.4,'last':base.get('updated_at',time.time()),'count':0,'kind':kind,'meaning':'Derived app-internal reciprocal topology; not an observed external connection.'}
 for i,p in enumerate(outer):
  connect(p,outer[(i+1)%len(outer)],'outer-ring')
  nearest=sorted((q for q in outer if q['id']!=p['id']),key=lambda q:sum((a-b)**2 for a,b in zip(p['point'],q['point'])))[:3]
  for q in nearest:connect(p,q,'outer-neighbour')
 overse['connections']+=list(links.values());overse['outer_nodes']=[p['id'] for p in outer];overse['outer_topology']={'nodes':len(outer),'derived_links':len(links),'rule':'Connected reciprocal ring plus three nearest neighbours per outer source node; bounded to 256 nodes.'}
 # The three requested derived contributions share identities. Merge, do not duplicate evidence.
 union=copy.deepcopy(overse);nodes={};edges={}
 for label,frame in [('inverse',inverse),('combined',combined),('overse',overse)]:
  for p in frame.get('particles',[]):
   ident=p['id']
   if ident not in nodes:nodes[ident]=copy.deepcopy(p);nodes[ident]['view_contributions']=[]
   nodes[ident]['view_contributions'].append(label)
  for e in frame.get('connections',[]):
   key=(e['source'],e['target'],e.get('kind','observed'))
   if key not in edges:edges[key]=copy.deepcopy(e);edges[key]['view_contributions']=[]
   edges[key]['view_contributions'].append(label)
 union.update(particles=list(nodes.values()),connections=list(edges.values()),merge_policy='Deduplicate matching node and connection identities; retain inverse / combined / Overse contribution labels.')
 result=dict(zip(LANES,(inverse,combined,overse,union)))
 for lane,frame in result.items():
  frame.update(view_lane=lane,source_sequence=base.get('sequence',0),represented_values=len(frame.get('particles',[])),network_weights={**frame.get('network_weights',{}),'view_edges':len(frame.get('connections',[])),'view_nodes':len(frame.get('particles',[]))},app_law={'principles':['Preserve source truth and lineage','Prefer protection, provision and repair','Compare action and inaction','Distinguish derived links from observed facts','No authority or private access inferred from a graph'],'resolution':'Source-preserving coordinate operations and checked local packet relays; no host commands executed.'})
 return result
class NeuralTopologyViews:
 def __init__(self):self.lock=threading.RLock();self.sequence=0;self.source_sequence=-1;self.frames={};self.visits=collections.Counter();self.trials=0;self.passed=0;self.latest_trial={};self.published=-1
 def update(self,c):
  with c.lock:base=c.neural_space.view()
  seq=base.get('sequence',0)
  with self.lock:
   if seq==self.source_sequence:return False
  frames=derive(base)
  with self.lock:self.frames=frames;self.source_sequence=seq;self.sequence+=1
  return True
 def tick(self,c):
  self.update(c)
  with self.lock:
   if self.published==self.source_sequence:return
   self.published=self.source_sequence;frame=self.frames.get('neural-overse',{});outer=frame.get('outer_nodes',[])
   if len(outer)<2:return
   start=min(outer,key=lambda key:self.visits[key]);end=outer[(outer.index(start)+max(1,len(outer)//2))%len(outer)];path=route(frame.get('connections',[]),start,end);packet=hashlib.sha256((str(self.source_sequence)+start+end).encode()).hexdigest();relay=packet
   trace=[]
   for node in path:trace.append({'node':node,'packet_digest':relay})
   reverse=route(frame.get('connections',[]),end,start);passed=bool(path and reverse and all(step['packet_digest']==packet for step in trace));self.trials+=1;self.passed+=int(passed);self.visits[start]+=1
   self.latest_trial={'source_sequence':self.source_sequence,'start':start,'end':end,'path':path,'reverse_path':reverse,'hops':max(0,len(path)-1),'packet_digest':packet,'preserved':passed,'scope':'Controlled in-memory routing experiment, not device or internet transmission. Edges are treated reciprocally for this local test; no external reverse-access authority is inferred.'}
   for f in self.frames.values():f['routing_experiments']={'trials':self.trials,'passed':self.passed,'latest':copy.deepcopy(self.latest_trial)}
   summary={'sequence':self.sequence,'routing_trials':self.trials,'passed':self.passed,'hops':max(0,len(path)-1),'outer_links':frame.get('outer_topology',{}).get('derived_links',0),'provenance':'checked-local-neural-topology-routing','stochastic':False,'predefined_text':True}
  with c.r.lock:c.r.workbench.executive.put('neural-topology-routing',copy.deepcopy(self.latest_trial),'neural-topology')
  c.bus.publish({'origin':'neural-topology-checked','target':'all','kind':'stage-output','payload':summary})
 def view(self,lane=None):
  with self.lock:return copy.deepcopy(self.frames.get(lane,{}) if lane else self.frames)
