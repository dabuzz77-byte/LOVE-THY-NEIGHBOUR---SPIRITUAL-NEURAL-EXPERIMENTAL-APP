"""Native Paint-style raster practice with six bounded search streams."""
import base64,copy,json,math,random,threading,time
W,H=48,32
KINDS=['brush control','shape colouring','ellipse drawing','colour mixing','tonal shading','balanced composition']
SOURCE={'title':'Microsoft Paint: drawing, shapes and layers','url':'https://www.microsoft.com/en-us/windows/paint'}
def render(kind,p):
 x,y,size,r,g,b=p;pixels=bytearray([255]*(W*H*3))
 for yy in range(H):
  for xx in range(W):
   dx,dy=xx-x,yy-y;on=False;colour=(r,g,b)
   if kind==0:on=abs(dy-.45*dx)<=max(1,size/4) and abs(dx)<size*2
   elif kind==1:on=abs(dx)<=size and abs(dy)<=size*.65
   elif kind==2:on=(dx/max(1,size))**2+(dy/max(1,size*.7))**2<=1
   elif kind==3:on=abs(dx)<size and abs(dy)<size;colour=((r+xx*3)%256,(g+yy*4)%256,b)
   elif kind==4:on=abs(dx)<size and abs(dy)<size;colour=tuple(int(v*(.2+.8*xx/(W-1))) for v in (r,g,b))
   else:on=abs(abs(dx)-size*.6)<max(1,size*.3) and abs(dy)<size*.8
   if on:pixels[(yy*W+xx)*3:(yy*W+xx)*3+3]=bytes(colour)
 return bytes(pixels)
def error(a,b):return sum((x-y)**2 for x,y in zip(a,b))/(len(a)*255**2)
class PaintTrainer:
 def __init__(self,data):
  self.lock=threading.RLock();self.rng=random.Random(417);self.sequence=0;self.next_at=0;self.last_save=0;self.path=data/'paint-practice.json';self.latest={};self.lanes=[]
  for i,name in enumerate(KINDS):
   target=[24,16,8+i%4,40+i*22,85+i*12,170-i*15];p=[12,10,5,100,100,100];self.lanes.append({'id':i,'name':name,'target':target,'parameters':p,'error':error(render(i,p),render(i,target)),'attempts':0,'improvements':0})
  try:
   saved=json.loads(self.path.read_text(encoding='utf-8'))
   for lane,row in zip(self.lanes,saved['lanes']):
    p=row['parameters']
    if len(p)==6 and all(type(v)is int and 0<=v<=255 for v in p) and 0<=p[0]<W and 0<=p[1]<H and 1<=p[2]<=20:
     lane['parameters']=p;lane['error']=error(render(lane['id'],p),render(lane['id'],lane['target']));lane['attempts']=max(0,int(row.get('attempts',0)));lane['improvements']=max(0,int(row.get('improvements',0)))
  except (OSError,ValueError,KeyError,TypeError):pass
 def flush(self):
  with self.lock:self.path.write_text(json.dumps({'lanes':self.lanes}),encoding='utf-8')
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  from .training_pace import interval
  self.next_at=time.monotonic()+interval(c,.25)
  with self.lock:
   lane=self.lanes[self.sequence%6];kind=lane['id'];target=render(kind,lane['target']);best=lane['parameters'][:];score=lane['error'];before=score
   for _ in range(12):
    candidate=best[:];j=self.rng.randrange(6);bounds=[(0,W-1),(0,H-1),(1,20),(0,255),(0,255),(0,255)];lo,hi=bounds[j];candidate[j]=max(lo,min(hi,candidate[j]+self.rng.choice([-8,-3,-1,1,3,8])));candidate_score=error(render(kind,candidate),target)
    if candidate_score<score:best=candidate;score=candidate_score;lane['improvements']+=1
   lane.update(parameters=best,error=score,attempts=lane['attempts']+12);self.sequence+=1;self.latest={'test':'Candidate pixel error does not increase','stream':lane['name'],'before':before,'after':score,'passed':score<=before,'attempts':lane['attempts'],'retained':best[:],'scope':'Optimisation toward a procedural fixture, not a measure of artistic beauty or model-weight training.'}
  if time.monotonic()-self.last_save>30:self.flush();self.last_save=time.monotonic()
  c.bus.publish({'origin':'paint-trainer','target':'all','kind':'stage-output','payload':{'cycle':self.sequence,'stream':kind,'pixel_error':score,'improved':score<before,'passed':score<=before,'provenance':'native-raster-practice','stochastic':False,'predefined_text':True}})
 def view(self):
  with self.lock:lanes=copy.deepcopy(self.lanes);latest=copy.deepcopy(self.latest);sequence=self.sequence
  for lane in lanes:
   i=lane['id'];lane['pixels']=base64.b64encode(render(i,lane['parameters'])).decode();lane['target_pixels']=base64.b64encode(render(i,lane['target'])).decode()
  return {'sequence':sequence,'latest':latest,'width':W,'height':H,'streams':lanes,'source':SOURCE,'scope':'Original native raster workbench informed by public Paint concepts. Microsoft Paint binaries and proprietary internals are not imported.'}
