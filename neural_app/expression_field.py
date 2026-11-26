"""Bounded multi-source expression field with balanced order/chaos sampling."""
import collections,hashlib,json,math,random,threading,time
def transform_view(point,view,axis='x'):
 x,y,z=point
 if view=='inverted':return [-x,-y,-z]
 if view=='base':return [x,y,z]
 if view not in ('plus90','minus90') or axis not in ('x','y','z'):raise ValueError('Choose base/inverted/plus90/minus90 and x/y/z')
 sign=1 if view=='plus90' else -1
 if axis=='x':return [x,-sign*z,sign*y]
 if axis=='y':return [sign*z,y,-sign*x]
 return [-sign*y,sign*x,z]
def transform_data(text,view):
 raw=text.encode('utf-8');count=len(raw);indices=list(range(count));side=math.ceil(math.sqrt(max(1,count)))
 if view=='inverted':data=bytes(value^255 for value in raw);rule='bitwise byte complement XOR 0xFF'
 elif view in ('plus90','minus90'):
  def rotated(index):
   row,col=divmod(index,side)
   return (col,side-1-row) if view=='plus90' else (side-1-col,row)
  indices.sort(key=rotated);data=bytes(raw[index] for index in indices);rule='clockwise row-major byte permutation' if view=='plus90' else 'counterclockwise row-major byte permutation'
 elif view=='base':data=raw;rule='identity'
 else:raise ValueError('Unknown expression data view')
 return {'data_bytes':list(data),'bits':''.join(f'{v:08b}' for v in data),'text':''.join(chr(v&127) for v in data),'source_indices':indices,'rule':rule,'source_encoding':'UTF-8 bytes','display_encoding':'low-seven-bit ASCII projection; exact data_bytes and bits retained','sha256':hashlib.sha256(data).hexdigest()}
class ExpressionField:
 def __init__(self,bus,reasoner,start=True):
  self.bus=bus;self.reasoner=reasoner;self.lock=threading.RLock();self.halt=threading.Event();self.sources={};self.sequence=0;self.received=0;self.skipped=0;self.error=None;self.enabled=True;self.rate=1.;self.points=collections.deque(maxlen=6000);self.selection=[];self.rng=random.Random();self.cursor=0;self.last_output=0;self.coverage=collections.Counter();self.limit=96;self.axis='x';self.latest_views=[];self.yin_state={}
  if start:threading.Thread(target=self.loop,daemon=True,name='expression-field').start()
 def observe(self,event):
  origin=str(event.get('origin','unknown'))[:120];p=event.get('payload');p=p if isinstance(p,dict) else {}
  if origin in ('expression-field','flow-backbone') or p.get('expression_trace'):return
  records=[]
  nested=p.get('sources')
  if isinstance(nested,list):records=[s for s in nested[:64] if isinstance(s,dict)]
  records=[p]+records
  for n,row in enumerate(records):
   text=row.get('text');codes=row.get('ascii_codes');bits=row.get('bits');name=str(row.get('name',origin))[:120]
   if not isinstance(text,str) and isinstance(codes,list):text=''.join(chr(int(c)) for c in codes[:2048] if type(c) is int and 0<=c<128)
   if not isinstance(text,str) and isinstance(bits,str) and set(bits)<=set('01'):text=bits
   generated=row.get('stochastic') is True and row.get('predefined_text') is False and row.get('contains_model_text') is False
   declared=any(s in origin.lower() for s in ('matrix','flux','cube','tesseract','sphere','random','ascii','stochastic','ambient','bit-command'))
   if not isinstance(text,str) or not text or not (generated or declared or row.get('provenance')=='observed-native-calculation'):continue
   text=text[:2048];key=origin+'/'+name;digest=hashlib.sha256(text.encode()).hexdigest();geometry={k:row[k] for k in ('point','position','positions','angle','direction','vector','trajectory','rows','columns') if k in row}
   # Only small supplied geometry survives; do not ingest entire framebuffer arrays.
   if len(json.dumps(geometry,default=str))>4096:geometry={'scope':'supplied geometry exceeds retained budget'}
   with self.lock:
    prior=self.sources.get(key);self.received+=1
    if key not in self.sources and len(self.sources)>=self.limit:self.skipped+=1;continue
    self.sources[key]={'id':key,'origin':origin,'text':text,'sha256':digest,'changed':prior is None or prior['sha256']!=digest,'updates':(prior or {}).get('updates',0)+1,'generated':generated,'provenance':row.get('provenance',p.get('provenance','declared-stage-output')),'geometry':geometry,'captured':time.time()}
 def configure(self,b):
  with self.lock:
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.enabled=b['enabled']
   if 'axis' in b:
    if b['axis'] not in ('x','y','z'):raise ValueError('Choose x, y or z axis')
    self.axis=b['axis']
   if 'rate' in b:
    value=float(b['rate'])
    if not math.isfinite(value):raise ValueError('Rate must be finite')
    self.rate=max(.1,min(64,value))
  return self.view()
 def step(self):
  with self.reasoner.lock:goal=str(self.reasoner.s.get('current_goal',{}).get('input_summary','')).lower();words=set(goal.split())
  with self.lock:
   rows=list(self.sources.values());self.sequence+=1
   if not rows:return None
   # Coverage explores every retained source; novelty and current-goal relevance select additional attention.
   floor=min(self.coverage[r['id']] for r in rows);under=[r for r in rows if self.coverage[r['id']]==floor]
   source=under[self.cursor%len(under)] if self.sequence%4==0 else max(rows,key=lambda r:1/(1+self.coverage[r['id']])+.5*int(r['changed'])+len(words&set(r['id'].lower().split())))
   self.cursor+=1;self.coverage[source['id']]+=1;source['changed']=False;text=source['text'];new=[]
   for i in range(27):
    order=(i%9)/8;phase=self.sequence*.04+i*.2;index=(self.cursor*27+i)%len(text);symbol=text[index]
    # Ordered planar spiral versus isotropic displacement, blended at nine equally represented bins.
    ordered=[math.cos(phase)*(1+i/27),0,math.sin(phase)*(1+i/27)];noise=[self.rng.uniform(-2,2) for _ in range(3)]
    point=[(1-order)*ordered[k]+order*noise[k] for k in range(3)]
    geometry=source['geometry'];supplied=geometry.get('point',geometry.get('position'))
    if isinstance(supplied,list) and len(supplied)==3 and all(type(v) in (int,float) and math.isfinite(v) for v in supplied):point=[max(-5,min(5,float(v)))+order*noise[k]*.1 for k,v in enumerate(supplied)]
    new.append({'point':point,'char':symbol,'source':source['id'],'chaos':order,'rate_scale':.1*(640**order),'born':time.time(),'geometry_basis':'supplied centre + spectrum spread' if supplied is not None else 'derived expression projection'})
   branch_data={view:transform_data(''.join(p['char'] for p in new),view) for view in ('base','inverted','plus90','minus90')}
   for i,p in enumerate(new):p['view_chars']={view:d['text'][i%len(d['text'])] for view,d in branch_data.items()}
   self.points.extend(new);attention={'source':source['id'],'reason':'coverage exploration' if self.sequence%4==0 else 'novelty / goal relevance / coverage','coverage':self.coverage[source['id']],'goal':goal[:200],'centre':[0,0,0],'plane':'y=0','flow':'centre → entire plane; plane + 3D sources → self-selection → shared backbone','spectrum':'nine equally allocated bins; chaos is spatial variability, not moral classification'}
   self.selection=(self.selection+[attention])[-12:]
   output={'text':''.join(p['char'] for p in new),'source_id':source['id'],'selection':attention,'stochastic':source['generated'],'predefined_text':False if source['generated'] else None,'contains_model_text':False if source['generated'] else None,'provenance':'derived-expression-field','expression_trace':[self.sequence],'bridge_direction':'all','geometry':[p['point'] for p in new],'definition_library':'/api/definition-library'}
  output['view_frames']=[{'id':view,'axis':self.axis,'geometry':[transform_view(p['point'],view,self.axis) for p in new],**branch_data[view],'source_id':source['id'],'clock_cycle':self.sequence} for view in ('base','inverted','plus90','minus90')]
  from .yin_expression import derive
  output['view_frames'].extend(derive(rows,new,self.sequence,self.yin_state))
  for i,p in enumerate(new):
   p['view_points']={v['id']:v['geometry'][i] for v in output['view_frames'] if v['id'].startswith('yin-')}
   p['view_bits']={v['id']:v['particle_states'][i]['bit'] for v in output['view_frames'] if v['id'].startswith('yin-')}
   p['view_vectors']={v['id']:v['particle_states'][i]['vector'] for v in output['view_frames'] if v['id'].startswith('yin-')}
   p['view_rates']={v['id']:v['particle_states'][i]['rate_scale'] for v in output['view_frames'] if v['id'].startswith('yin-')}
   p['view_chars'].update({v['id']:v['text'][i%len(v['text'])] for v in output['view_frames'] if v['id'].startswith('yin-')})
  output['sources']=[{'name':'expression-field/'+v['id'],'text':v['text'],'bits':v['bits'],'data_bytes':v['data_bytes'],'source_indices':v['source_indices'],'rule':v['rule'],'axis':v['axis'],'point':v['geometry'][0],'particle_states':v.get('particle_states',[]),'stochastic':source['generated'],'predefined_text':False if source['generated'] else None,'contains_model_text':False if source['generated'] else None,'provenance':'derived-expression-data-view'} for v in output['view_frames']]
  with self.lock:self.latest_views=output['view_frames']
  if time.monotonic()-self.last_output>=1:
   for start in range(0,len(output['view_frames']),2):
    views=output['view_frames'][start:start+2]
    wire={**output,'sources':output['sources'][start:start+2],'view_frames':[{'id':v['id'],'axis':v['axis'],'geometry':[[round(x,6) for x in point] for point in v['geometry']],'sha256':v['sha256'],'rule':v['rule'],'clock_cycle':v['clock_cycle'],'aggregate_sha256':v.get('aggregate_sha256'),'input_sources':v.get('input_sources'),'chaos':v.get('chaos'),'rate_scale':v.get('rate_scale'),'data_reference':'sources/'+str(i)} for i,v in enumerate(views)],'view_packet':start//2,'view_packets':3}
    self.bus.publish({'target':'all','kind':'stage-output','origin':'expression-field','payload':wire})
   self.last_output=time.monotonic()
  return output
 def loop(self):
  while not self.halt.is_set():
   if self.enabled:
    try:self.step()
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:180]
   self.halt.wait(max(.03,.2/max(.1,self.rate)))
 def view(self):
  with self.lock:return {'view_data':self.latest_views,'views':['base','inverted','plus90','minus90','yin-order-chaos','yin-chaos-order'],'axis':self.axis,'enabled':self.enabled,'rate':self.rate,'sequence':self.sequence,'received':self.received,'skipped':self.skipped,'sources':[{k:v for k,v in row.items() if k!='text'} for row in self.sources.values()],'points':list(self.points)[-600:],'selection':self.selection[-4:],'coverage':dict(self.coverage),'error':self.error,'scope':'96 registered retained sources, 2048 characters each; bounded projection; not infinite computation or a physical field measurement'}
 def close(self):self.halt.set()
