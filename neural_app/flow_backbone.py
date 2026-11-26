"""Parallel software-stage backbone. Original bus delivery is preserved."""
import collections,hashlib,json,queue,threading,time
from pathlib import Path
from .ambient_bus import STAGES
from .logic_cube import transform
from .runtime import SECTIONS
class FlowBackbone:
 def __init__(self,bus,start=True):
  self.bus=bus;self.lock=threading.RLock();self.stages=list(dict.fromkeys((*STAGES,*SECTIONS)));self.inbox={};self.history=collections.deque(maxlen=80);self.pending=queue.Queue(maxsize=128);self.halt=threading.Event();self.received=0;self.dropped=0;self.errors=0;self.last_error=None;self.sequence=0;self.enabled=True;self.ethics_library=json.loads((Path(__file__).resolve().parents[1]/'references/shared-ethics-library.json').read_text(encoding='utf-8'));self.element_tick=0;self.element_layers=[];self.next_elements=0
  for filename,prefix in [('original-panels.json','original/'),('java-sections.json','java/'),('python-sections.json','python/')]:
   try:
    catalog=json.loads((Path(__file__).resolve().parents[1]/filename).read_text(encoding='utf-8'));rows=catalog.values() if isinstance(catalog,dict) else catalog
    for row in rows:
     if isinstance(row,dict) and row.get('id'):self.stages.append(prefix+str(row['id']))
   except (OSError,ValueError):pass
  self.stages=list(dict.fromkeys(self.stages+['native-matrix-rain','grounded-reasoner','potential-sphere','omni-cube','ambient-combined/inverted','ambient-combined/plus90','ambient-combined/minus90']+['atomic/'+symbol for symbol in ['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si']]))
  if start:threading.Thread(target=self.loop,daemon=True,name='parallel-flow-backbone').start()
 def observe(self,event):
  if not self.enabled or event.get('origin')=='flow-backbone':return
  payload=event.get('payload');trace=payload.get('backbone_trace',[]) if isinstance(payload,dict) else []
  if trace:return
  try:self.pending.put_nowait(dict(event));self.received+=1
  except queue.Full:self.dropped+=1
 def process(self,event):
  p=event.get('payload');p=p if isinstance(p,dict) else {'value':p}
  direction=p.get('bridge_direction','all');entry=event.get('target','all');index=self.stages.index(entry) if entry in self.stages else None
  requested=p.get('bridge_targets')
  if requested is not None:
   if not isinstance(requested,list) or not requested or any(s not in self.stages for s in requested):raise ValueError('Choose registered bridge targets')
   targets=list(dict.fromkeys(requested))
  elif direction=='upstream' and index is not None:targets=self.stages[:index]
  elif direction=='downstream' and index is not None:targets=self.stages[index+1:]
  elif direction=='self' and index is not None:targets=[entry]
  elif direction=='all':targets=list(self.stages)
  else:raise ValueError('Choose all, upstream, downstream or self with a registered entry')
  bits=p.get('bits');labels=p.get('labels');filtered=None;classification='unresolved';rule='hold for review'
  if isinstance(bits,str) and bits and len(bits)<=2048 and set(bits)<=set('01'):
   if not isinstance(labels,list) or len(labels)!=len(bits):labels=['unknown']*len(bits)
   filtered=transform(bits,labels,p.get('global_state','PASS'));classification='supplied per-bit classifications';rule='good hold / evil invert / unknown hold'
  raw=json.dumps(p,sort_keys=True,ensure_ascii=True,separators=(',',':'));digest=hashlib.sha256(raw.encode()).hexdigest()
  # Arbitrary text is retained by hash/reference, never interpreted as host commands.
  with self.lock:
   self.sequence+=1
   receipt={'sequence':self.sequence,'time':time.time(),'source_sequence':event.get('sequence'),'source_origin':event.get('origin'),'entry':entry,'direction':direction,'targets':targets,'input_sha256':digest,'input_bytes':len(raw.encode()),'classification':classification,'rule':rule,'filtered':filtered,'cloud_projection':p.get('cloud_projection'),'element_layers':p.get('element_layers',self.element_layers),'four_way':{'true_good':'Traceable local sharing, exact bit filtering and preserved original flow','true_evil':'Data corruption, concealed actions and uncontrolled feedback are excluded','false_good':'A benevolent label alone does not establish a correct classification or completed execution','false_evil':'Reversible routing and removing needless barriers in software the owner controls can be beneficial'},'definition_library':{'version':self.ethics_library['version'],'reference':'/api/definition-library','priority':self.ethics_library['priority'],'correction':self.ethics_library['correction']},'original_flow_preserved':True,'delivery':'stage mailbox updated; subscriber execution is separately recorded','backbone_trace':[self.sequence],'hop_limit':1,'provenance':'derived-flow-backbone','stochastic':False}
   for stage in targets:self.inbox[stage]=receipt
   self.history.append(receipt)
  self.bus.publish({'target':'all','kind':'stage-output','origin':'flow-backbone','payload':receipt})
  return receipt
 def calculate_elements(self):
  from math import isfinite
  elements=[('H',1,13.5984),('He',2,24.5874),('Li',3,5.3917),('Be',4,9.3227),('B',5,8.2980),('C',6,11.2603),('N',7,14.5341),('O',8,13.6181),('F',9,17.4228),('Ne',10,21.5645),('Na',11,5.1391),('Mg',12,7.6462),('Al',13,5.9858),('Si',14,8.1517)]
  self.element_tick+=1;n=2+self.element_tick%7;e=1.602176634e-19;h=6.62607015e-34
  rows=[{'layer':symbol,'Z':z,'cycle':self.element_tick,'time':time.time(),'electrons_neutral':z,'nuclear_charge_C':z*e,'first_ionization_eV':ion,'threshold_frequency_Hz':ion*e/h,'one_electron_ion':{'charge':z-1,'n':n,'energy_eV':-13.605693122994*z*z/n**2,'scope':'infinite nuclear mass, nonrelativistic hydrogen-like model'},'provenance':'calculated-atomic-model','stochastic':False} for symbol,z,ion in elements]
  with self.lock:self.element_layers=rows
  self.bus.publish({'target':'all','kind':'stage-output','origin':'backbone-atomic-layers','payload':{'element_layers':rows,'cycle':self.element_tick,'stochastic':False,'provenance':'calculated-atomic-model'}})
 def loop(self):
  while not self.halt.is_set():
   if time.monotonic()>=self.next_elements:
    try:self.calculate_elements()
    except Exception as e:self.errors+=1;self.last_error=str(e)[:200]
    self.next_elements=time.monotonic()+10
   try:event=self.pending.get(timeout=.25)
   except queue.Empty:continue
   try:self.process(event)
   except Exception as e:self.errors+=1;self.last_error=str(e)[:200]
   finally:self.pending.task_done()
   self.halt.wait(.01)
 def view(self):
  with self.lock:return {'element_layers':self.element_layers,'element_cycle':self.element_tick,'enabled':self.enabled,'stages':self.stages,'sequence':self.sequence,'received':self.received,'pending':self.pending.qsize(),'dropped':self.dropped,'errors':self.errors,'last_error':self.last_error,'inlets':{s:{'sequence':v['sequence'],'source_sequence':v['source_sequence'],'input_sha256':v['input_sha256']} for s,v in self.inbox.items()},'history':list(self.history)[-12:],'scope':'registered local software stages; parallel to existing flow','filter':'good holds; evil working bits invert; unresolved holds for review; classification requires supplied criteria'}
 def close(self):self.halt.set()
