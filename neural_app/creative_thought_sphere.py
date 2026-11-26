"""Data-derived graphical experiments in a finite local scene grammar."""
import collections,copy,hashlib,json,math,random,threading,time
SHAPES=['point','ring','line','text','triangle','square']
MOTIONS=['orbit','pulse','drift','jitter','wave','still']
class CreativeThoughtSphere:
 def __init__(self):self.lock=threading.RLock();self.next_at=0;self.sequence=0;self.latest={};self.visits=collections.Counter();self.history=collections.deque(maxlen=24)
 def step(self,c,intent=''):
  if not isinstance(intent,str) or len(intent)>2000:raise ValueError('Use up to 2000 characters')
  with c.lock:
   variables=[{'source':r['source'],'path':f['path'],'value':copy.deepcopy(f['value']),'type':f['type'],'parent_event':r['parent_event']} for r in c.sources.values() if r['source']!='creative-thought-sphere' for f in r['facts']]
  if not variables:
   return {'status':'waiting for captured engine variables','sequence':self.sequence,'points':[],'coverage':{'available':0,'rendered':0}}
  with self.lock:
   rng=random.Random(random.SystemRandom().getrandbits(64));ordered=sorted(variables,key=lambda r:(self.visits[r['source']+json.dumps(r['path'])],rng.random()));chosen=ordered[:512];points=[];tests=[]
   for i,row in enumerate(chosen):
    key=row['source']+json.dumps(row['path']);self.visits[key]+=1;h=int(hashlib.sha256(key.encode()).hexdigest()[:16],16);z=1-2*((h%100000)/100000);a=((h>>16)%100000)/100000*math.tau;radius=.35+((h>>32)%650)/1000;xy=math.sqrt(max(0,1-z*z));shape=rng.choice(SHAPES);motion=rng.choice(MOTIONS)
    value=row['value'];numeric=type(value) in (int,float);amplitude=.02+.09*(abs(float(value))%1 if numeric and abs(value)<1e12 else rng.random());points.append({'id':hashlib.sha256(key.encode()).hexdigest()[:16],'position':[radius*xy*math.cos(a),radius*z,radius*xy*math.sin(a)],'w':rng.uniform(-1,1),'shape':shape,'motion':motion,'rate':.15+rng.random()*1.8,'amplitude':amplitude,'label':str(value)[:24],'source':row['source'],'path':row['path'],'type':row['type'],'parent_event':row['parent_event'],'colour':h%4})
   while len(self.visits)>8192:del self.visits[next(iter(self.visits))]
   for row in chosen[:12]:
    value=row['value'];encoded=json.dumps(value,ensure_ascii=False);recovered=json.loads(encoded);tests.append({'source':row['source'],'path':row['path'],'experiment':'JSON/Unicode preservation','passed':recovered==value})
   bounds=all(all(math.isfinite(v) and abs(v)<=1 for v in p['position']) for p in points)
   self.sequence+=1;self.latest={'sequence':self.sequence,'time':time.time(),'intent':intent or c.goal,'points':points,'tests':tests,'scene_checks':{'finite_bounded_positions':bounds,'known_shapes':all(p['shape'] in SHAPES for p in points),'known_motions':all(p['motion'] in MOTIONS for p in points),'fourth_coordinate_bounded':all(-1<=p['w']<=1 for p in points)},'coverage':{'available_captured_variables':len(variables),'rendered':len(points),'unique_variables_visited':len(self.visits),'selection':'least-visited captured variables with randomized tie breaks'},'grammar':{'shapes':SHAPES,'motions':MOTIONS},'dimensions':4,'projection':'4D coordinates and XW/YW rotations projected into a 3D scene', 'scope':'Experiments over the bounded captured-variable registry. Finite scene grammar; no arbitrary scripts, host actions or access to unregistered variables.'};self.history.append({'sequence':self.sequence,'tests_passed':sum(t['passed'] for t in tests),'rendered':len(points)})
   result=copy.deepcopy(self.latest)
  c.bus.publish({'origin':'creative-thought-sphere','target':'all','kind':'stage-output','payload':{'sequence':result['sequence'],'rendered_points':len(points),'passed_tests':sum(t['passed'] for t in tests),'position_bounds':bounds,'provenance':'local-data-graphics-experiment','stochastic':True,'predefined_text':True}})
  return result
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+3;self.step(c)
 def view(self):
  with self.lock:return {**copy.deepcopy(self.latest),'recent':list(self.history),'grammar':{'shapes':SHAPES,'motions':MOTIONS}}
