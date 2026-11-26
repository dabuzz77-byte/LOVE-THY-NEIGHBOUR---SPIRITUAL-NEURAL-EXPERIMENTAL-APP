"""Rigid coordinate copies of the complete thinking-plane frame and their overlay."""
import copy,threading,time
IDENTITY=((1,0,0),(0,1,0),(0,0,1))
RX=((1,0,0),(0,0,-1),(0,1,0));RY=((0,0,1),(0,1,0),(-1,0,0));RZ=((0,-1,0),(1,0,0),(0,0,1))
def multiply(a,b):return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
POSITIVE=RX;NEGATIVE=RZ
def vector(v,m):return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def plane_grid(m):
 lines=[]
 for k in range(-5,6):
  for a,b in [([-1,0,k/5],[1,0,k/5]),([k/5,0,-1],[k/5,0,1])]:lines.append([vector(a,m),vector(b,m)])
 return lines

def transform(base,m,label):
 out=copy.deepcopy(base)
 for p in out.get('particles',[]):
  p['original_particle_id']=p['id'];p['id']=label+':'+p['id'];p['orientation']=label
  for key in ('point','vector','position','velocity','normal'):
   if isinstance(p.get(key),list) and len(p[key])==3:p[key]=vector(p[key],m)
 for e in out.get('connections',[]):
  for key in ('from','to'):
   if isinstance(e.get(key),list) and len(e[key])==3:e[key]=vector(e[key],m)
 normal=vector(base.get('plane',{}).get('normal',[0,1,0]),m);out['plane']={**out.get('plane',{}),'normal':normal,'basis_u':vector([1,0,0],m),'basis_v':vector([0,0,1],m),'equation':'n · (x,y,z) = 0; n = '+str(normal),'grid_lines':plane_grid(m),'orientation':label}
 out['planes']=[out['plane']];out['orientation']={'label':label,'matrix':[list(r) for r in m],'meaning':'Rigid data transform applied to points, vectors, connections and field-plane basis; source values and logical outcomes preserved.'};out['source_sequence']=base.get('sequence',0)
 return out

def frames(base):
 a=transform(base,IDENTITY,'original');b=transform(base,POSITIVE,'quarter-turn-X');c=transform(base,NEGATIVE,'quarter-turn-Z');combined=copy.deepcopy(base)
 combined.update(particles=a.get('particles',[])+b.get('particles',[])+c.get('particles',[]),planes=a['planes']+b['planes']+c['planes'],orientation={'label':'combined-three','contributions':['original','quarter-turn-X','quarter-turn-Z'],'policy':'Overlay all three coordinate systems without treating copied observations as independent evidence.'},source_sequence=base.get('sequence',0),unique_source_particles=len(base.get('particles',[])),displayed_coordinate_copies=sum(len(f.get('particles',[])) for f in (a,b,c)))
 combined['manifestations']=[{**r,'orientation':label} for label,f in [('original',a),('quarter-turn-X',b),('quarter-turn-Z',c)] for r in f.get('manifestations',[])]
 combined['scope']=base.get('scope','')+' Combined coordinate copies share the same underlying evidence; no tripling of confidence.'
 return {'plane-rotated-positive':b,'plane-rotated-inverse':c,'plane-three-combined':combined}
class PlaneOrientations:
 def __init__(self):self.lock=threading.RLock();self.source_sequence=-1;self.cache={};self.sequence=0
 def update(self,c):
  with c.lock:base=c.total_plane_sphere.view()
  seq=base.get('sequence',0)
  with self.lock:
   if seq==self.source_sequence:return False
  derived=frames(base)
  with self.lock:self.cache=derived;self.source_sequence=seq;self.sequence+=1
  return True
 def tick(self,c):
  if self.update(c):c.bus.publish({'origin':'thinking-plane-orientations','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'source_sequence':self.source_sequence,'coordinate_views':3,'provenance':'rigid-coordinate-projections','stochastic':False,'predefined_text':True,'scope':'Three views of one source, not independent experimental confirmations.'}})
 def view(self,lane=None):
  with self.lock:
   if lane:return copy.deepcopy(self.cache.get(lane,{}))
   return copy.deepcopy(self.cache)
