"""Lossless balanced-ternary shadow of captured scalar variables; no source mutation."""
import collections,copy,hashlib,json,math,random,threading,time

def encode(value):
 raw=json.dumps(value,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('utf-8');trits=[]
 if len(raw)>8192:raise ValueError('Scalar exceeds ternary byte budget')
 for byte in raw:
  digits=[];n=byte
  for _ in range(6):
   n,r=divmod(n,3)
   if r==2:r=-1;n+=1
   digits.append(r)
  trits.extend(reversed(digits))
 return trits

def decode(trits):
 if isinstance(trits,str):
  if any(t not in '-0+' for t in trits):raise ValueError('Invalid compact ternary symbol')
  trits=[{'-':-1,'0':0,'+':1}[t] for t in trits]
 if not isinstance(trits,list) or len(trits)>49152 or len(trits)%6 or any(type(t)is not int or t not in (-1,0,1) for t in trits):raise ValueError('Use fixed-width six-trit bytes')
 raw=[]
 for start in range(0,len(trits),6):
  v=0
  for t in trits[start:start+6]:v=v*3+t
  if not 0<=v<=255:raise ValueError('Trit byte outside 0–255')
  raw.append(v)
 return json.loads(bytes(raw).decode('utf-8'))
class TernaryLayer:
 def __init__(self):
  self.lock=threading.RLock();self.variables=collections.OrderedDict();self.pending=collections.OrderedDict();self.sequence=0;self.received=0;self.changed=0;self.tested=0;self.failures=0;self.loop_skips=0;self.evicted=0;self.next_at=0;self.cursor=0;self.latest={};self.history=collections.deque(maxlen=24);self.halt=threading.Event();self.worker=None;self.circuit=None;self.worker_error=None;self.rng=random.Random()
 def observe(self,row,event):
  if row['source'].startswith('ternary-layer'):
   self.loop_skips+=1;return
  with self.lock:
   self.received+=1
   for fact in row['facts']:
    ident=hashlib.sha256((row['source']+json.dumps(fact['path'])).encode()).hexdigest()[:24];value=fact['value'];signature=hashlib.sha256(json.dumps(value,ensure_ascii=True,allow_nan=False).encode()).hexdigest();old=self.variables.get(ident)
    if old and old['signature']==signature:continue
    self.variables[ident]={'id':ident,'source':row['source'],'path':fact['path'],'value':copy.deepcopy(value),'type':fact['type'],'parent_event':row['parent_event'],'signature':signature,'status':'pending conversion'};self.variables.move_to_end(ident);self.pending[ident]=True;self.changed+=1
   while len(self.variables)>8192:
    ident,_=self.variables.popitem(last=False);self.pending.pop(ident,None);self.evicted+=1
 def process(self,c):
  with self.lock:
   with c.adaptive_rail.lock:metrics=dict(c.adaptive_rail.metrics)
   pressure=max(metrics.get('cpu_percent',70)/100,metrics.get('memory_percent',70)/100)
   batch=128 if pressure<.7 else 64 if pressure<.85 else 24 if pressure<.93 else 8
   burst_start=time.perf_counter();burst_budget=.008 if pressure<.85 else .004;completed=0
   ids=list(self.pending)[:batch]
   if not ids and self.variables:
    keys=list(self.variables);ids=[keys[(self.cursor+i)%len(keys)] for i in range(min(24,len(keys)))];self.cursor=(self.cursor+len(ids))%len(keys)
   for ident in ids:
    if completed and time.perf_counter()-burst_start>=burst_budget:break
    completed+=1
    row=self.variables[ident];original=encode(row['value']);raw=[self.rng.choice((-1,0,1)) for _ in original]
    try:raw_value=decode(raw);raw_valid=type(raw_value)is type(row['value'])
    except (ValueError,UnicodeError,OverflowError):raw_value=None;raw_valid=False
    # Select against a declared preservation objective, rather than inventing moral meaning for trits.
    selected=list(original);restored=decode(selected);passed=type(restored)is type(row['value']) and restored==row['value'];self.tested+=1;self.failures+=int(not passed)
    compact=''.join({-1:'-',0:'0',1:'+'}[t] for t in original);raw_compact=''.join({-1:'-',0:'0',1:'+'}[t] for t in raw)
    row.update(status='processed',trits=compact,unselected=raw_compact,selected=compact,roundtrip=passed,unselected_valid=raw_valid,selection='Choose the exact round-trip candidate; preserve the source value.',potential={'per_trit':[-1,0,1],'full_states':'3^'+str(len(original)),'representation':'Implicit Cartesian product; every combination is representable without simultaneous materialisation.'});self.pending.pop(ident,None)
   rows=[r for r in self.variables.values() if r.get('trits')];points=[]
   pairs=128 if pressure<.85 else 64
   start=(self.sequence*pairs)%len(rows) if rows else 0;visible_rows=(rows[start:]+rows[:start])[:pairs]
   for i,row in enumerate(visible_rows):
    h=int(row['id'][:12],16);a=(h%100000)/100000*math.tau;z=1-2*((h>>16)%100000)/100000;r=math.sqrt(max(0,1-z*z))
    for rail,offset in [('unselected',-.48),('selected',.48)]:
     values=row[rail];trit={'-':-1,'0':0,'+':1}[values[self.sequence%len(values)]] if values else 0
     points.append({'id':row['id']+'/'+rail,'variable_id':row['id'],'source':row['source'],'path':row['path'],'rail':rail,'position':[offset+.44*r*math.cos(a),.75*z,.6*r*math.sin(a)],'w':trit*.55,'shape':'ring' if rail=='selected' else 'point','motion':'pulse' if rail=='selected' else 'jitter','rate':.3+(h%100)/60,'amplitude':.035,'colour':trit+1,'label':str(trit),'trit':trit,'parent_event':row['parent_event'],'potential':row['potential'],'roundtrip':row['roundtrip'],'selection':row['selection']})
   self.sequence+=1;self.latest={'sequence':self.sequence,'time':time.time(),'points':points,'dimensions':4,'coverage':{'available_captured_variables':len(self.variables),'processed_variables':len(rows),'pending':len(self.pending),'rendered':len(points),'rendered_variable_pairs':len(visible_rows),'conversion_ms':round((time.perf_counter()-burst_start)*1000,3),'burst_budget_ms':burst_budget*1000,'evicted':self.evicted,'scope':'Captured scalar registry: up to 8192 variables, not every unregistered process variable.'},'scene_checks':{'roundtrip_failures':self.failures,'tested':self.tested,'loop_packets_skipped':self.loop_skips},'tests':[{'id':r['id'],'source':r['source'],'passed':r['roundtrip'],'trits':len(r['trits'])} for r in rows[-8:]],'scope':'Non-destructive parallel balanced ternary. Original values remain intact; candidate rails are local experiments. The selected rail uses explicit source-preservation criteria, not a new general mind.'};self.history.append({'sequence':self.sequence,'processed_batch':completed,'tests':self.tested});result=copy.deepcopy(self.latest)
  c.bus.publish({'origin':'ternary-layer-output','target':'all','kind':'stage-output','payload':{'ternary_sequence':self.sequence,'variables_processed':len(rows),'tested':self.tested,'failures':self.failures,'pending':len(self.pending),'provenance':'lossless-ternary-shadow-summary','stochastic':False,'predefined_text':True,'bridge_direction':'all','loop_guard':'Do not convert ternary-layer output back into its own variable registry.'}})
  return result
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+.4;self.process(c)
 def loop(self):
  while not self.halt.is_set():
   try:
    if self.circuit and self.circuit.enabled:self.tick(self.circuit)
    self.worker_error=None
   except Exception as exc:self.worker_error=str(exc)[:200]
   self.halt.wait(.2)
 def close(self):
  self.halt.set()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(3)
 def proposal(self,c,value):
  if not (value is None or type(value) in (str,int,float,bool)):raise ValueError('Provide a JSON scalar proposal')
  trits=encode(value);restored=decode(trits)
  c.capture({'origin':'ternary-proposal','kind':'input','target':'all','payload':{'value':restored,'provenance':'user-proposed-local-value','stochastic':False}})
  return {'roundtrip':restored==value,'trits':trits,'scope':'New proposed input; no existing source variable overwritten.'}
 def view(self,ident=None):
  with self.lock:
   if ident:
    if ident not in self.variables:raise ValueError('Variable no longer retained')
    row=copy.deepcopy(self.variables[ident])
    if 'roundtrip' not in row:
     trits=encode(row['value']);restored=decode(trits)
     row.update(roundtrip=type(restored)is type(row['value']) and restored==row['value'],inspection_only=True,status='Current value checked for inspection; background conversion remains queued')
    return row
   return {**copy.deepcopy(self.latest),'recent':list(self.history),'grammar':{'states':[-1,0,1],'byte_encoding':'Six balanced trits per UTF-8 JSON byte; compact symbols - 0 + mean -1 0 +1'},'received':self.received,'changes':self.changed,'worker':{'alive':bool(self.worker and self.worker.is_alive()),'error':self.worker_error,'mode':'Independent paced ternary worker'}}
