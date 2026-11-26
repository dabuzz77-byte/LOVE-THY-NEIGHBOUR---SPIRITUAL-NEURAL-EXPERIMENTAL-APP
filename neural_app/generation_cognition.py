"""Bounded generation-to-candidate workspace with out-of-sample prediction."""
import collections,hashlib,json,math,re,threading,time
from .mind_workspace import terms

class GenerationCognition:
 def __init__(self,bus,reasoner,start=True):
  self.bus=bus;self.reasoner=reasoner;self.lock=threading.RLock();self.halt=threading.Event();self.worker=None;self.enabled=True;self.interval=.5;self.sources=collections.OrderedDict();self.pending={};self.history=collections.deque(maxlen=64);self.sequence=0;self.received=0;self.coalesced=0;self.errors=0;self.last_error=None;self.pending_predictions={};self.cross={};self.last_signature=None
  saved=reasoner.s.get('generation_cognition',{});self.learned=dict(saved.get('learned',{}));self.source_cursor=0
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='generation-cognition');self.worker.start()
 def configure(self,b):
  if 'enabled' in b:
   if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
   self.enabled=b['enabled']
  if 'interval' in b:
   n=float(b['interval'])
   if not math.isfinite(n):raise ValueError('Use finite intervals')
   self.interval=max(.1,min(30,n))
  return self.view()
 def observe(self,event):
  source=str(event.get('origin','unknown'))[:120];p=event.get('payload')
  if source in ('generation-cognition','flow-backbone') or not isinstance(p,dict) or p.get('cognition_trace'):return
  # Only generated representations are inputs here; conversational and scripture text are not stochastic evidence.
  generated=p.get('stochastic') is True or any(x in source for x in ('matrix','flux','cube','tesseract','potential','expression','particle','ambient','parallel','bit-command'))
  if not generated:return
  samples=[];stack=[(p,0)];visited=0
  while stack and len(samples)<16 and visited<128:
   value,depth=stack.pop();visited+=1
   if depth>5:continue
   if isinstance(value,dict):
    for k,v in list(value.items())[:48]:
     if any(s in k.lower() for s in ('secret','token','password','authorization')):continue
     if k in ('text','bits','trits','content','symbol','ascii','string') and isinstance(v,str):samples.append(v[:1024])
     elif isinstance(v,(list,dict)):stack.append((v,depth+1))
   elif isinstance(value,list):stack.extend((v,depth+1) for v in value[:32])
  if not samples:return
  text='\n'.join(samples)[:4096]
  with self.lock:
   self.received+=1;self.coalesced+=int(source in self.pending);self.pending[source]={'source':source,'text':text,'sequence':event.get('sequence'),'stochastic':p.get('stochastic') is True,'provenance':str(p.get('provenance','generated-source'))[:160],'time':time.time()}
   while len(self.pending)>128:self.pending.pop(next(iter(self.pending)))
 def features(self,text):
  counts=collections.Counter(text);n=len(text);pairs=collections.Counter(zip(text,text[1:]));motifs=collections.Counter(text[i:i+3] for i in range(max(0,n-2)))
  entropy=-sum(v/n*math.log2(v/n) for v in counts.values()) if n else 0
  repeats=[{'value':k,'count':v} for k,v in motifs.most_common(8) if v>1]
  runs=max((len(m[0]) for m in re.finditer(r'(.)\1*',text,re.S)),default=0)
  return {'characters':n,'unique':len(counts),'entropy':entropy,'repeat_trigrams':repeats,'longest_run':runs,'bit_fraction':sum(c in '01' for c in text)/max(1,n),'transition_types':len(pairs),'compression_proxy':1-len(counts)/max(1,n)},counts,pairs
 def step(self):
  with self.lock:
   rows=list(self.pending.values());self.pending.clear()
  if not rows:return None
  with self.reasoner.lock:goal=str(self.reasoner.s.get('current_goal',{}).get('input_summary',''));executive=getattr(self.reasoner.workbench,'executive',None)
  if executive:
   with self.reasoner.lock:
    active=next((g for g in reversed(executive.s['goals']) if g['status']=='running'),None)
    if active:goal=active['goal']
  q=terms(goal);candidates=[]
  with self.lock:
   for row in rows:
    source=row['source'];text=row['text'];digest=hashlib.sha256(text.encode()).hexdigest();old=self.sources.get(source,{})
    if digest==old.get('digest'):continue
    f,counts,pairs=self.features(text);learned=self.learned.setdefault(source,{'tested':0,'correct':0,'baseline_correct':0,'updates':0})
    prediction=self.pending_predictions.pop(source,None)
    if prediction and text:
     actual=text[0];learned['tested']+=1;learned['correct']+=int(prediction['symbol']==actual);learned['baseline_correct']+=int(prediction['baseline']==actual)
    transitions=old.get('transitions',collections.Counter()).copy();transitions.update(pairs)
    if len(transitions)>1024:transitions=collections.Counter(dict(transitions.most_common(1024)))
    last=text[-1];possible=[(count,b) for (a,b),count in transitions.items() if a==last];predicted=max(possible)[1] if possible else last
    self.pending_predictions[source]={'symbol':predicted,'baseline':last,'captured_sequence':row['sequence']}
    learned['updates']+=1;tested=learned['tested'];accuracy=learned['correct']/tested if tested else None;baseline=learned['baseline_correct']/tested if tested else None
    relevance=len(q&terms(source+' '+text))/max(1,len(q));surprise=abs(f['entropy']-old.get('features',f)['entropy']);support=max((x['count'] for x in f['repeat_trigrams']),default=0)
    outcome_advantage=(accuracy-baseline) if tested>=8 else 0
    candidate={'id':digest[:20],'source':source,'source_sequence':row['sequence'],'provenance':row['provenance'],'kind':'generated-pattern-candidate','features':f,'hypothesis':'A retained transition pattern may predict the first symbol of a later changed capture','prediction':{'symbol':predicted,'baseline':last,'tested':tested,'accuracy':accuracy,'baseline_accuracy':baseline,'advantage':outcome_advantage},'goal_relevance':relevance,'novelty':digest!=old.get('digest'),'score':3*relevance+max(0,outcome_advantage)+min(.5,surprise/8)+min(.25,support/100),'status':'candidate; not independently established meaning','goal':goal,'time':time.time()}
    self.sources[source]={**row,'digest':digest,'features':f,'transitions':transitions};self.sources.move_to_end(source);candidates.append(candidate)
    while len(self.sources)>128:
     removed,_=self.sources.popitem(last=False);self.pending_predictions.pop(removed,None)
    while len(self.learned)>128:self.learned.pop(next(iter(self.learned)))
   if not candidates:return None
   # Fair coverage prevents one high-volume or high-score source monopolising the workspace.
   candidates.sort(key=lambda c:(-c['score'],c['source']));selected=candidates[:3]
   if len(candidates)>3:selected.append(candidates[3+(self.source_cursor%len(candidates[3:]))]);self.source_cursor+=1
   motifs=collections.defaultdict(set)
   for c in candidates:
    for m in c['features']['repeat_trigrams']:motifs[m['value']].add(c['source'])
   shared=[{'motif':k,'sources':sorted(v),'status':'shared representation; sources may be causally linked'} for k,v in motifs.items() if len(v)>1][:12]
   self.sequence+=1;result={'sequence':self.sequence,'goal':goal,'selected':selected,'cross_source_patterns':shared,'sources_processed':len(candidates),'cognition_trace':True,'pipeline':['generated captures','features','temporal predictions','goal attention','candidate workspace','native reasoning feedback'],'scope':'Testable software candidates; shared motifs and random text are not automatically facts, instructions or external messages'};self.history.append(result)
  # Record candidate nodes distinctly from verified actions; never automatically execute generated text.
  if executive:
   with self.reasoner.lock:
    for c in selected:executive.put('generated-candidate',c,c['source'])
    self.reasoner.s['generation_cognition']={'learned':dict(self.learned),'time':time.time()}
  self.bus.publish({'origin':'generation-cognition','target':'all','kind':'stage-output','payload':{**result,'stochastic':False,'provenance':'derived-generated-candidates','text':json.dumps(selected,ensure_ascii=True)[:5000]}})
  return result
 def view(self):
  with self.lock:return {'enabled':self.enabled,'interval':self.interval,'sequence':self.sequence,'received':self.received,'coalesced':self.coalesced,'pending_sources':len(self.pending),'sources':len(self.sources),'last':self.history[-1] if self.history else None,'learned':dict(self.learned),'errors':self.errors,'last_error':self.last_error}
 def loop(self):
  while not self.halt.is_set():
   if self.enabled and not self.reasoner.user_active:
    try:self.step()
    except Exception as exc:self.errors+=1;self.last_error=type(exc).__name__+': '+str(exc)[:200]
   self.halt.wait(self.interval)
 def close(self):
  self.halt.set()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(5)
