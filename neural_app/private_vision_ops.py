"""Private finite workflow interpreter. No arbitrary code or external I/O operations."""
import collections,hashlib,json,math,random,re,secrets,time,uuid
from pathlib import Path
DEFAULT_PLAN=[{'op':'randomize','count':256},{'op':'xor_source','pattern':0},{'op':'rotate','places':7},{'op':'hold_flip','labels':'GGG?E??G'},{'op':'boundary','limit':12},{'op':'queue','route':'memory'},{'op':'encode'},{'op':'entropy'},{'op':'phase','frequency':7.83,'amplitude':.5},{'op':'project','dimensions':3},{'op':'resource','maximum_bytes':32768},{'op':'decision_review','harm_prevented':8,'harm_caused':1,'evidence':1,'vulnerability':1,'claimed_good':True},{'op':'feedback','capacity':64},{'op':'checkpoint'}]
DESCRIPTIONS={'randomize':'Generate reproducible proposal bits from the recorded seed.','xor_source':'XOR each bit with the selected source pattern and intention-hash bit.','rotate':'Rotate the actual bit register.','reverse':'Reverse the actual bit register.','hold_flip':'G holds; E flips; ? remains deferred / held. Labels apply to bits.','boundary':'Correct proposed walk directions that would leave the declared boundary.','queue':'Send and receive actual in-process queue values with sequence receipts.','encode':'Convert bytes to balanced trits and basis indices; verify byte recovery.','entropy':'Measure empirical bit frequency and Shannon entropy.','phase':'Generate a finite software phase / amplitude series.','project':'Project bit groups to declared finite coordinate vectors.','resource':'Check the actual register size against its budget.','decision_review':'Four-way scenario assessment from declared harm and evidence estimates.','feedback':'Retain a bounded ring of actual decisions.','checkpoint':'Commit a hashed private state checkpoint.'}
def hashbits(bits):return hashlib.sha256(bits.encode('ascii')).hexdigest()
def info(data):
 folder=Path(data)/'private-vision/workflows';folder.mkdir(parents=True,exist_ok=True)
 profiles=[p.stem for p in folder.glob('profile-*.json')]
 runs=[]
 for p in sorted(folder.glob('run-*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:12]:
  try:r=json.loads(p.read_text());runs.append({'id':r['id'],'time':r['time'],'hash':r['output_sha256'],'steps':len(r['trace']),'seed':r['seed']})
  except (OSError,ValueError,KeyError):pass
 return {'default_plan':DEFAULT_PLAN,'operations':DESCRIPTIONS,'profiles':profiles,'runs':runs,'private':True}
def validate(plan):
 if not isinstance(plan,list) or not 1<=len(plan)<=32:raise ValueError('Use 1–32 declared operation blocks.')
 if any(not isinstance(node,dict) or node.get('op') not in DESCRIPTIONS for node in plan):raise ValueError('Use only the listed private operation names.')
 if len(json.dumps(plan,allow_nan=False))>32000:raise ValueError('Workflow plan is too large.')
 allowed={'op','count','pattern','places','labels','limit','route','frequency','amplitude','dimensions','maximum_bytes','harm_prevented','harm_caused','evidence','vulnerability','claimed_good','capacity'}
 if any(set(node)-allowed for node in plan):raise ValueError('Unrecognised operation parameter.')
 return plan
def save_profile(body,data):
 name=str(body.get('name','default'))
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',name):raise ValueError('Profile name: 1–40 letters, digits, underscore or dash.')
 plan=validate(body.get('plan'));folder=Path(data)/'private-vision/workflows';folder.mkdir(parents=True,exist_ok=True);(folder/('profile-'+name+'.json')).write_text(json.dumps(plan,indent=2),encoding='utf-8');return {'saved':name,'private':True}
def load_profile(name,data):
 if not re.fullmatch(r'profile-[A-Za-z0-9_-]{1,40}',str(name)):raise ValueError('Invalid private profile name.')
 return {'plan':json.loads((Path(data)/'private-vision/workflows'/(str(name)+'.json')).read_text())}
def execute(body,data):
 from .private_vision import catalog
 c=catalog(data);plan=validate(body.get('plan',DEFAULT_PLAN));seed=int(body.get('seed'))&0xffffffff if body.get('seed') not in ('',None) else secrets.randbits(32);rng=random.Random(seed);intent_hash=hashlib.sha256(str(body.get('intent',''))[:4000].encode()).hexdigest();bits='';trace=[];aux={};queue=collections.deque();ring=collections.deque(maxlen=64);started=time.monotonic();run_id=uuid.uuid4().hex
 seeds=c.get('binary_seeds')or['01']
 for index,node in enumerate(plan):
  op=node['op'];before=bits;details={}
  if op=='randomize':bits=''.join(str(rng.getrandbits(1)) for _ in range(max(1,min(4096,int(node.get('count',256))))));details={'recorded_seed':seed,'bits':len(bits)}
  elif op=='xor_source':
   pattern=seeds[int(node.get('pattern',0))%len(seeds)];bits=''.join(str(int(v)^int(pattern[i%len(pattern)])^(int(intent_hash[i%64],16)&1)) for i,v in enumerate(bits));details={'source_pattern_sha256':hashbits(pattern),'intention_sha256':intent_hash}
  elif op=='rotate':n=int(node.get('places',1))%max(1,len(bits));bits=bits[n:]+bits[:n];details={'places':n}
  elif op=='reverse':bits=bits[::-1]
  elif op=='hold_flip':
   labels=str(node.get('labels','G?E')).upper()
   if not labels or len(labels)>4096 or any(v not in 'GE?' for v in labels):raise ValueError('Bit labels use only G, E and ?.')
   bits=''.join(str(int(v)^int(labels[i%len(labels)]=='E')) for i,v in enumerate(bits));details={'flips':sum(labels[i%len(labels)]=='E' for i in range(len(bits))),'held_unknown':sum(labels[i%len(labels)]=='?' for i in range(len(bits)))}
  elif op=='boundary':
   limit=max(1,min(100,int(node.get('limit',12))));x=0;output=[];events=[]
   for i,v in enumerate(bits):
    bit=int(v);outside=abs(x+(1 if bit else -1))>limit;corrected=bit^int(outside);x+=1 if corrected else -1;output.append(str(corrected));events.append({'i':i,'proposal':bit,'output':corrected,'x':x,'corrected':outside})
   bits=''.join(output);aux['walk']=events;details={'limit':limit,'flips':sum(e['corrected'] for e in events),'final_x':x,'bounded':all(abs(e['x'])<=limit for e in events)}
  elif op=='queue':
   route=node.get('route','memory')
   if route not in ('memory','feedback','output'):raise ValueError('Private routes: memory, feedback, output.')
   for i,v in enumerate(bits):queue.append((i,v))
   received=[]
   while queue:received.append(queue.popleft())
   details={'route':route,'sent':len(bits),'received':len(received),'first_receipt':received[0][0] if received else None,'last_receipt':received[-1][0] if received else None,'transport':'in-process queue; no external transmission'}
  elif op=='encode':
   values=[int(bits[i:i+8].ljust(8,'0'),2) for i in range(0,len(bits),8)];ternary=[]
   for value in values:
    digits=[];n=value
    for _ in range(6):n,r=divmod(n,3);r=-1 if r==2 else r;n+=int(r==-1);digits.append(r)
    ternary+=list(reversed(digits))
   recovered=[sum(t*3**(5-j) for j,t in enumerate(ternary[i:i+6])) for i in range(0,len(ternary),6)];aux['encodings']={'bytes':values,'trits':ternary,'basis':[t+1 for t in ternary]};details={'byte_count':len(values),'trits':len(ternary),'qutrit_indices':len(ternary),'round_trip':recovered==values}
  elif op=='entropy':p=bits.count('1')/max(1,len(bits));details={'ones':bits.count('1'),'zeros':bits.count('0'),'entropy_bits_per_bit':sum(-v*math.log2(v) for v in (p,1-p) if v)}
  elif op=='phase':
   frequency=float(node.get('frequency',7.83));amplitude=float(node.get('amplitude',.5))
   if not math.isfinite(frequency+amplitude) or abs(frequency)>20000 or abs(amplitude)>1:raise ValueError('Use a finite frequency up to 20,000 and amplitude within ±1.')
   aux['phase']=[amplitude*math.sin(2*math.pi*frequency*i/4096) for i in range(128)];details={'frequency_Hz':frequency,'amplitude':amplitude,'samples':128,'scope':'software signal'}
  elif op=='project':dimensions=max(2,min(4,int(node.get('dimensions',3))));aux['coordinates']=[[1 if v=='1' else -1 for v in bits[i:i+dimensions]] for i in range(0,len(bits)-dimensions+1,dimensions)];details={'dimensions':dimensions,'vectors':len(aux['coordinates'])}
  elif op=='resource':maximum=max(1,min(1048576,int(node.get('maximum_bytes',32768))));details={'register_bytes':len(bits.encode()),'maximum_bytes':maximum,'passed':len(bits.encode())<=maximum}
  elif op=='decision_review':
   prevented=max(0,min(100,float(node.get('harm_prevented',0))));caused=max(0,min(100,float(node.get('harm_caused',0))));evidence=max(0,min(1,float(node.get('evidence',0))));vulnerable=max(0,min(1,float(node.get('vulnerability',1))));score=prevented*(1+vulnerable)-caused*2;beneficial=score>0;claimed=bool(node.get('claimed_good',True));category='unresolved' if evidence<.5 else 'true_good' if beneficial and claimed else 'false_evil' if beneficial else 'false_good' if claimed else 'true_evil';details={'category':category,'estimated_score':score,'evidence_input':evidence,'basis':'user-declared scenario estimates; not a verdict about a person'}
  elif op=='feedback':ring=collections.deque(({'i':i,'bit':v} for i,v in enumerate(bits)),maxlen=max(1,min(256,int(node.get('capacity',64)))));aux['feedback']=list(ring);details={'retained':len(ring),'capacity':ring.maxlen}
  elif op=='checkpoint':details={'state_sha256':hashbits(bits),'persisted_on_completion':True}
  changed=sum(a!=b for a,b in zip(before,bits))+abs(len(before)-len(bits));trace.append({'step':index+1,'op':op,'description':DESCRIPTIONS[op],'before_bits':before,'after_bits':bits,'before_sha256':hashbits(before),'after_sha256':hashbits(bits),'changed_positions':changed,'details':details})
 result={'id':run_id,'time':time.time(),'private':True,'seed':seed,'intent_sha256':intent_hash,'plan':plan,'trace':trace,'bits':bits,'output_sha256':hashbits(bits),'auxiliary':aux,'wall_seconds':time.monotonic()-started,'host_programs_executed':0,'external_transmissions':0}
 folder=Path(data)/'private-vision/workflows';folder.mkdir(parents=True,exist_ok=True);path=folder/('run-'+run_id+'.json');path.write_text(json.dumps(result,indent=2),encoding='utf-8');checkpoint=folder/'checkpoint.json';temporary=folder/'checkpoint.pending';temporary.write_text(json.dumps({'run':run_id,'sha256':result['output_sha256'],'seed':seed,'bits':bits}),encoding='utf-8');temporary.replace(checkpoint)
 previous=sorted(folder.glob('run-*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
 if len(previous)>1:
  old=json.loads(previous[1].read_text());result['comparison']={'previous_id':old['id'],'different_positions':sum(a!=b for a,b in zip(bits,old['bits']))+abs(len(bits)-len(old['bits'])),'same_output':result['output_sha256']==old['output_sha256']}
 result['checkpoint']={'written':True,'sha256':result['output_sha256'],'private':True};return result
