"""Fine-phase, bounded experiments on source-labelled registered app captures."""
import collections,copy,hashlib,inspect,json,math,os,threading,time

PHASES=1025

def period_check(values):
 # Propose on the first half, verify on the later half; no language dictionary.
 if len(values)<16:return None
 cut=len(values)//2
 for width in range(1,min(16,cut//2)+1):
  if all(values[i]==values[i%width] for i in range(width,cut)):
   return {'period':width,'training_items':cut,'heldout_items':len(values)-cut,'heldout_passed':all(values[i]==values[i%width] for i in range(cut,len(values)))}
 return None

def experiment(bits,original,variant):
 from .logic_cube import transform
 filtered=transform(bits,['unknown']*len(bits))
 decoded=bytes(int(bits[i:i+8],2) for i in range(0,len(bits)-7,8))
 period=period_check(decoded);source_period=period_check(original)
 return {'bit_filter':{k:filtered[k] for k in ('holds','flips','unresolved','roundtrip')},'encoding_roundtrip':''.join(f'{b:08b}' for b in decoded)==bits,'reverse_involution':bits[::-1][::-1]==bits,'ordered_bit_count_preserved':sum(map(int,sorted(bits)))==bits.count('1'),'ones':bits.count('1'),'zeros':bits.count('0'),'runs':1+sum(a!=b for a,b in zip(bits,bits[1:])) if bits else 0,'period_proposal':period,'source_period':source_period,'pattern_supported_in_original':bool(period and period['heldout_passed'] and source_period and source_period['heldout_passed'] and source_period['period']==period['period']),'variant':variant,'scope':'Algebraic invariants are checks of the transform. A generated periodic pattern is not a discovered message or world fact. Unclassified candidate bits hold; no moral label is inferred from bit value.'}

class SpectrumLogicSphere:
 def __init__(self,state=None,save=None):
  self.lock=threading.RLock();self.sources=collections.OrderedDict();self.sequence=0;self.events=0;self.duplicates=0;self.evictions=0;self.cursor=0;self.phase_cursor=0;self.covered=set();self.latest={};self.frames=[];self.history=collections.deque(maxlen=32);self.next_at=0;self.closed=False;self.providers=[];self.provider_cursor=0;self.next_registry=0;self.provider_status={}
  from .spectrum_deliberation import SpectrumDeliberation
  self.thinking=SpectrumDeliberation(state,save)
 def snapshot_one(self,c):
  if time.monotonic()>=self.next_registry:
   self.next_registry=time.monotonic()+30;providers=[]
   for name,obj in list(vars(c).items()):
    if name in ('r','bus','spectrum_logic') or not type(obj).__module__.startswith('neural_app.'):continue
    method=getattr(obj,'view',None)
    if not callable(method):continue
    try:
     if any(p.default is inspect.Parameter.empty and p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD,p.KEYWORD_ONLY) for p in inspect.signature(method).parameters.values()):continue
    except (ValueError,TypeError):continue
    providers.append((name,method))
   self.providers=providers
  if not self.providers:return
  name,method=self.providers[self.provider_cursor%len(self.providers)];self.provider_cursor+=1
  try:
   value=method();self.observe_event({'origin':'engine-snapshot/'+name,'payload':{'data':value,'provenance':'recorded engine view; source references retain their original status'}})
   with self.lock:self.provider_status[name]={'status':'sampled','time':time.time()}
  except Exception as e:
   with self.lock:self.provider_status[name]={'status':'unavailable','error':type(e).__name__+': '+str(e)[:180]}
 def observe_event(self,event):
  if event.get('origin')=='spectrum-logic-sphere':return
  payload=event.get('payload');pending=[(payload,[])];facts=[];visited=0
  while pending and len(facts)<96 and visited<512:
   value,path=pending.pop();visited+=1
   if len(path)>7:continue
   if isinstance(value,dict):
    pending.extend((v,path+[str(k)]) for k,v in list(value.items())[:64] if not any(t in str(k).casefold() for t in ('password','secret','token','authorization')))
   elif isinstance(value,list):pending.extend((v,path+[i]) for i,v in enumerate(value[:32]))
   elif value is None or type(value) in (str,int,float,bool):
    if type(value) is float and not math.isfinite(value):continue
    facts.append({'path':path,'value':value[:1024] if isinstance(value,str) else value})
  digest=hashlib.sha256(json.dumps(facts,sort_keys=True,default=str).encode()).hexdigest()
  self.observe({'source':str(event.get('origin','unknown')),'parent_event':event.get('sequence'),'digest':digest,'facts':facts,'provenance':payload.get('provenance','registered processing receipt') if isinstance(payload,dict) else 'registered processing receipt'},event)
 def observe(self,row,event):
  if row.get('source')=='spectrum-logic-sphere':return
  value={k:row.get(k) for k in ('source','parent_event','digest','facts','units','provenance')}
  raw=json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode('utf-8')
  # Existing captures already exclude credential fields and bound fact depth.
  if len(raw)>65536:raw=raw[:65536];truncated=True
  else:truncated=False
  key=str(row['source'])[:120]
  with self.lock:
   self.events+=1;prior=self.sources.get(key)
   if prior and prior['source_digest']==row.get('digest'):self.duplicates+=1;return
   self.sources[key]={'raw':raw,'offset':0,'completed_bytes':0,'source':key,'source_digest':row.get('digest'),'capture_sha256':hashlib.sha256(raw).hexdigest(),'upstream_event':row.get('parent_event'),'provenance':row.get('provenance'),'source_urls':[f['value'] for f in row.get('facts',[]) if isinstance(f.get('value'),str) and f['value'].startswith(('https://','http://'))][:12],'capture_bytes':len(raw),'truncated':truncated};self.sources.move_to_end(key)
   while len(self.sources)>128:self.sources.popitem(last=False);self.evictions+=1
 def tick(self,c):
  now=time.monotonic()
  if self.closed or now<self.next_at:return
  self.next_at=now+.5;started=time.perf_counter()
  self.snapshot_one(c)
  with self.lock:
   if not self.sources:return
   source=list(self.sources.values())[self.cursor%len(self.sources)];self.cursor+=1
   begin=source['offset'];raw=source['raw'][begin:begin+64]
   if not raw:return
   source['offset']=(begin+len(raw))%len(source['raw']);source['completed_bytes']=max(source['completed_bytes'],begin+len(raw))
   context={k:copy.deepcopy(v) for k,v in source.items() if k!='raw'}
   phases=[0,PHASES-1]+[(self.phase_cursor+i)%(PHASES-2)+1 for i in range(14)];self.phase_cursor=(self.phase_cursor+14)%(PHASES-2)
  original=''.join(f'{v:08b}' for v in raw);random_bits=''.join(f'{v:08b}' for v in os.urandom(len(raw)))
  rank_bytes=os.urandom(2*len(original));thresholds=[int.from_bytes(rank_bytes[j:j+2],'big')%1024+1 for j in range(0,len(rank_bytes),2)]
  variants={'source-order':original,'reversed':original[::-1],'sorted-bits':''.join(sorted(original)),'rotate':original[8:]+original[:8]};frames=[]
  for index,phase in enumerate(phases):
   variant='source-order' if phase in (0,1024) else list(variants)[(self.sequence+index)%4];ordered=variants[variant]
   bits=''.join(ordered[j] if phase>=thresholds[j] else random_bits[j] for j in range(len(original)))
   result=experiment(bits,raw,variant)
   frames.append({'phase_index':phase,'phase':phase/1024,'bits':bits,'result':result,'candidate_sha256':hashlib.sha256(bits.encode()).hexdigest(),'original_unchanged':phase==1024 and bits==original,'interpretation':'source-supported pattern' if result['pattern_supported_in_original'] else 'generated candidate; no source meaning inferred'})
  from .decision_framework import assess
  app_law=assess('generation/preserve',expected={'original_capture_sha256':context['capture_sha256'],'side_effects':'none; experiments operate on binary copies'},verified=all(f['result']['encoding_roundtrip'] and f['result']['bit_filter']['roundtrip'] for f in frames))
  self.thinking.tick(c,frames)
  with self.lock:
   self.sequence+=1;self.covered.update(phases);self.frames=frames
   self.latest={'sequence':self.sequence,'source':context,'byte_window':[begin,begin+len(raw)],'phase_count':PHASES,'phase_step':1/1024,'covered_phase_positions':len(self.covered),'tested_candidates_this_cycle':len(frames),'verified_invariant_checks':sum(sum(bool(f['result'][k]) for k in ('encoding_roundtrip','reverse_involution','ordered_bit_count_preserved')) for f in frames),'source_supported_patterns':sum(f['result']['pattern_supported_in_original'] for f in frames),'elapsed_ms':round((time.perf_counter()-started)*1000,3),'scope':'Rolling 64-byte windows of bounded registered app captures, retaining provenance. 1,025 configured phase positions; 16 tested per cycle. Source order at 100% is deterministic preservation, not total knowledge or guaranteed logical correctness.'}
   self.latest['app_law_review']=app_law;self.latest['exploration_policy']='Broad pure-data experiments; source preservation, honest provenance and checked findings. No candidate code execution or automatic external effects.'
   self.history.append({k:v for k,v in self.latest.items() if k not in ('source','app_law_review')})
  c.bus.publish({'origin':'spectrum-logic-sphere','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'sequence':self.sequence,'source':context['source'],'upstream_event':context['upstream_event'],'source_sha256':context['capture_sha256'],'phases_tested':phases,'verified_checks':self.latest['verified_invariant_checks'],'predefined_text':True,'stochastic':False,'provenance':'bounded spectrum experiments; transform checks not world-truth claims'}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'captured_events':self.events,'retained_sources':len(self.sources),'duplicate_captures':self.duplicates,'evicted_sources':self.evictions,'registered_engine_views':len(self.providers),'engine_snapshot_status':copy.deepcopy(self.provider_status),'phase_count':PHASES,'covered_phase_positions':len(self.covered),'latest':copy.deepcopy(self.latest),'recent':copy.deepcopy(list(self.history)),'coverage':[{'source':r['source'],'capture_bytes':r['capture_bytes'],'completed_bytes':r['completed_bytes'],'source_digest':r['source_digest'],'truncated':r['truncated']} for r in self.sources.values()],'scope':'Registered app captures plus round-robin engine views, including retrieved network-source records. Not all computer memory, the whole internet, or every historical event. Rolling source retention and byte windows are explicitly counted.'}
 def sphere(self):
  state=self.view();state['deliberation']=self.thinking.view();particles=[]
  with self.lock:frames=copy.deepcopy(self.frames)
  for i,frame in enumerate(frames):
   for j in range(12):
    offset=j*max(1,len(frame['bits'])//12);bit=frame['bits'][offset:offset+1] or '0';index=i*12+j;angle=index*2.399963;y=1-2*(index+.5)/max(1,len(frames)*12);r=math.sqrt(max(0,1-y*y))
    particles.append({'id':'spectrum:'+str(frame['phase_index'])+':'+str(j),'point':[r*math.cos(angle),y,r*math.sin(angle)],'phase':frame['phase'],'autonomy':frame['phase'],'selected':frame['original_unchanged'] or frame['result']['pattern_supported_in_original'],'symbol':bit,'expression_type':'spectrum-bit-candidate','source':state['latest'].get('source',{}).get('source'),'parent_event':state['latest'].get('source',{}).get('upstream_event'),'path':[frame['phase_index'],offset],'value_preview':frame['interpretation'],'record':{k:v for k,v in frame.items() if k!='bits'}})
  return {'sequence':state['sequence'],'particles':particles,'received_events':state['captured_events'],'retained_sources':state['retained_sources'],'represented_values':sum(len(f['bits']) for f in frames),'selected_phases':[f['phase'] for f in frames],'spectrum_review':state,'thought_trace':[{'phase':f['phase'],'result':f['result']} for f in frames],'scope':state['scope']}
 def close(self):self.closed=True
