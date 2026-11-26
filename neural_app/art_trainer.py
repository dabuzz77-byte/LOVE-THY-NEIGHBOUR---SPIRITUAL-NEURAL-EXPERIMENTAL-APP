"""Small native scene trainer; published Cinema 4D concepts, no proprietary engine."""
import math
LESSONS=[('Scene construction','Create primitives and arrange position, rotation and scale.'),('Composition','Frame a subject with clear depth, balance and negative space.'),('Materials','Choose colour and compare surface appearance.'),('Lighting','Study key, fill and rim lighting; distinguish this wireframe workspace from a rendered light simulation.'),('Camera','Orbit the scene and compare perspective and silhouettes.'),('Keyframes','Record transforms at different times and interpolate between them.'),('Timing','Compare linear motion with smooth easing.'),('Topology','Study vertices, edges, faces and manifold geometry.'),('UV mapping','Plan how a two-dimensional image maps to a surface.'),('Rigging','Study parent-child transforms, joints and constraints.'),('Procedural art','Generate variations from bounded mathematical rules.'),('Rendering','Study sampling, shadows, colour management and export formats.')]
def catalogue():return {'lessons':[{'title':t,'exercise':e} for t,e in LESSONS],'sources':[{'title':'Maxon animation basics','url':'https://www.maxon.net/en/cinema-4d/features/animation-basics'},{'title':'Maxon timeline reference','url':'https://help.maxon.net/c4d/2025/en-us/Content/html/10596.html'}],'scope':'Native lightweight wireframe scene and keyframe practice. Advanced lesson topics are curriculum, not implemented Cinema 4D features.'}
def check(scene):
 objects=scene.get('objects',[])
 if not isinstance(objects,list) or len(objects)>64:raise ValueError('Use at most 64 objects')
 for o in objects:
  if o.get('shape') not in ('cube','octahedron','ring'):raise ValueError('Unsupported primitive')
  for key in ('position','rotation','scale'):
   a=o.get(key,[])
   if len(a)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>10000 for v in a):raise ValueError('Use three finite bounded transform values')
 return {'objects':len(objects),'passed':True,'checks':['Supported primitives','Finite bounded transforms','Scene object budget'],'next_exercise':'Record a second transform key and inspect the transition.'}

class ArtTrainer:
 def __init__(self):self.sequence=0;self.next_at=0;self.latest={}
 def view(self):return {**catalogue(),'sequence':self.sequence,'latest':self.latest}
 def tick(self,c):
  import time
  if time.monotonic()<self.next_at:return
  from .training_pace import interval
  self.next_at=time.monotonic()+interval(c)
  angle=(self.sequence%24)*math.pi/12;x,y=math.cos(angle),math.sin(angle);passed=abs(x*x+y*y-1)<1e-12
  self.sequence+=1;self.latest={'test':'Rotation preserves unit radius','angle':angle,'passed':passed}
  c.bus.publish({'origin':'art-trainer','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'passed':passed,'provenance':'native-transform-invariant-test','stochastic':False,'predefined_text':True}})
