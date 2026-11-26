"""Online source-pattern learning; prediction scored before each update."""
from collections import Counter, OrderedDict
import hashlib, math, json, os, threading, time, uuid
from .ambient_rail_evidence import compare_rails
from .ambient_source_identity import source_key

class EmergenceLearning:
 def __init__(self,path=None):
  self.lock=threading.RLock();self.path=path;self.next_save=0;self.saved=-1;self.storage_error=None;self.transitions={};self.seen=OrderedDict();self.tested=0;self.correct=0;self.loss=0.;self.sources=0
  from .ambient_predictive_models import PredictiveModels
  self.predictive_models=PredictiveModels()
  from .ambient_temporal_models import TemporalModels
  self.temporal_models=TemporalModels()
  from .ambient_representation_learning import RepresentationLearning
  self.representation_models=RepresentationLearning()
  self.pattern_checks=OrderedDict()
  self.pattern_trials=OrderedDict()
  self.previous_captures=OrderedDict()
  self.output_pending=None;self.on_update=None;self.pending=OrderedDict();self.halt=threading.Event();self.worker=None
  if path and path.exists():
   try:
    if path.stat().st_size>1500000:raise ValueError('Stored learner exceeds size budget')
    state=json.loads(path.read_text(encoding='utf-8'))
    if state.get('version')!=1:raise ValueError('Unknown learner version')
    transitions=state['transitions']
    if not isinstance(transitions,dict) or len(transitions)>256:raise ValueError('Invalid transition table')
    restored={}
    for key,counts in transitions.items():
     if not key.isdecimal() or not 0<=int(key)<256 or not isinstance(counts,dict) or len(counts)>256:raise ValueError('Invalid transition context')
     if any(not k.isdecimal() or not 0<=int(k)<256 or type(v) is not int or not 1<=v<=4096 for k,v in counts.items()):raise ValueError('Invalid transition count')
     restored[int(key)]=Counter({int(k):v for k,v in counts.items()})
    tested,correct,sources,loss=(state[k] for k in ('tested','correct','sources','loss'))
    if any(type(v) is not int or not 0<=v<=10**12 for v in (tested,correct,sources)) or correct>tested or type(loss) not in (int,float) or not math.isfinite(loss) or not 0<=loss<=10**15:raise ValueError('Invalid learner counters')
    seen=state.get('seen',[])
    if not isinstance(seen,list) or len(seen)>256 or any(not isinstance(r,list) or len(r)!=2 or not all(isinstance(v,str) for v in r) or len(r[0])>100 or len(r[1])!=64 or any(c not in '0123456789abcdef' for c in r[1]) for r in seen):raise ValueError('Invalid capture hashes')
    self.transitions=restored;self.tested=tested;self.correct=correct;self.sources=sources;self.loss=loss;self.seen=OrderedDict((tuple(r),True) for r in seen);self.saved=sources
   except (OSError,ValueError,TypeError,KeyError,AttributeError) as e:self.storage_error=type(e).__name__+': '+str(e)[:180]
 def enqueue(self,source,raw,conditions=None):
  with self.lock:
   self.pending[source_key(source)]=(bytes(raw[:1024]),conditions)
   while len(self.pending)>32:self.pending.popitem(last=False)
 def drain(self,limit=2):
  for _ in range(limit):
   with self.lock:
    if not self.pending:return
    source,(raw,conditions)=self.pending.popitem(last=False)
   self.observe(source,raw,conditions)
 def start(self):
  if self.worker is not None:return
  def run():
   while not self.halt.wait(.25):
    try:self.drain();self.tick(None)
    except Exception as exc:
     with self.lock:self.storage_error='Source worker: '+type(exc).__name__+': '+str(exc)[:180]
  self.worker=threading.Thread(target=run,name='ambient-source-validation',daemon=True);self.worker.start()
 def close(self):
  self.halt.set()
  if self.worker is not None:self.worker.join(2)
  self.flush()
 def observe(self,source,raw,conditions=None):
  with self.lock:
   result=self._observe(source,raw,conditions)
   check=result['heldout_pattern_checks'].get(source_key(source))
  if result.get('fresh') and check:
   with self.lock:self.output_pending=(source_key(source),check)
  return result
 def _observe(self,source,raw,conditions=None):
  source=source_key(source)
  raw=bytes(raw[:1024]);key=(source,hashlib.sha256(raw).hexdigest())
  if key in self.seen:
   if source not in self.pattern_checks:
    from .ambient_pattern_validation import validate
    self.pattern_checks[source]=validate(raw)
    if conditions:self.pattern_checks[source]['conditions']=conditions
    while len(self.pattern_checks)>32:self.pattern_checks.popitem(last=False)
   return {'fresh':False,**self.view()}
  self.seen[key]=True
  while len(self.seen)>256:self.seen.popitem(last=False)
  self.sources+=1
  from .ambient_pattern_validation import validate,predict_capture
  previous=self.previous_captures.get(source)
  self.pattern_checks[source]=validate(raw)
  self.pattern_checks[source]['adaptive_prediction']=self.predictive_models.observe(source,raw)
  self.pattern_checks[source]['temporal_prediction']=self.temporal_models.observe(source,raw)
  self.pattern_checks[source]['representation_prediction']=self.representation_models.observe(source,raw)
  if previous is not None:self.pattern_checks[source]['next_capture_prediction']=predict_capture(previous,raw)
  self.previous_captures[source]=raw;self.previous_captures.move_to_end(source)
  while len(self.previous_captures)>32:self.previous_captures.popitem(last=False)
  self.pattern_checks.move_to_end(source)
  if conditions:self.pattern_checks[source]['conditions']=conditions
  trials=(self.pattern_trials.get(source,[])+[{'source_sha256':key[1],'status':self.pattern_checks[source]['status']}])[-8:]
  self.pattern_trials[source]=trials;self.pattern_trials.move_to_end(source)
  positives=sum(r['status']=='candidate-structure' for r in trials)
  self.pattern_checks[source]['fresh_capture_review']={'checked_captures':len(trials),'candidate_captures':positives,'status':'recurring-candidate' if positives>=3 else 'needs-fresh-captures','scope':'Distinct capture hashes are not proof of independent observations; recurrence is not semantic understanding.'}
  while len(self.pattern_checks)>32:self.pattern_checks.popitem(last=False)
  while len(self.pattern_trials)>32:self.pattern_trials.popitem(last=False)
  for before,after in zip(raw,raw[1:]):
   counts=self.transitions.setdefault(before,Counter());total=sum(counts.values())
   if total>=8:
    prediction=min(counts,key=lambda v:(-counts[v],v));self.tested+=1;self.correct+=prediction==after
    self.loss-=math.log2((counts[after]+1)/(total+256))
   counts[after]+=1
   if sum(counts.values())>4096:
    self.transitions[before]=Counter({k:max(1,v//2) for k,v in counts.items()})
  return {'fresh':True,**self.view()}
 def view(self,detail=False):
  with self.lock:return {'pending_captures':len(self.pending),'validation_worker_alive':bool(self.worker and self.worker.is_alive()),'observed_sources':self.sources,'pre_update_predictions':self.tested,'correct_predictions':self.correct,'accuracy':self.correct/self.tested if self.tested else None,'mean_surprise_bits':self.loss/self.tested if self.tested else None,'uniform_reference_bits':8,'contexts':len(self.transitions),'persistent':self.path is not None,'storage_error':self.storage_error,'rail_comparisons':compare_rails(self.pattern_checks),'heldout_pattern_checks':dict(list(self.pattern_checks.items())[-32 if detail else -8:]),'role':'Learn source transition regularities and evaluate predictions before updating. Fresh random data may contain no predictable structure. This is a bounded learning component, not proof of intelligence or a physical void connection.'}
 def flush(self):
  if self.path is None:return
  with self.lock:
   if self.saved==self.sources:return
   state={'version':1,'transitions':self.transitions,'tested':self.tested,'correct':self.correct,'sources':self.sources,'loss':self.loss,'seen':list(self.seen)}
   raw=json.dumps(state,separators=(',',':'));sequence=self.sources
  tmp=self.path.with_name(self.path.name+'.'+uuid.uuid4().hex+'.tmp')
  try:
   self.path.parent.mkdir(parents=True,exist_ok=True);tmp.write_text(raw,encoding='utf-8');os.replace(tmp,self.path)
   with self.lock:self.saved=sequence;self.storage_error=None
  except OSError as e:
   with self.lock:self.storage_error=type(e).__name__+': '+str(e)[:180]
  finally:
   if tmp.exists():tmp.unlink()
 def tick(self,c):
  if c is not None and self.on_update:
   with self.lock:pending=self.output_pending;self.output_pending=None
   if pending:
    try:self.on_update(*pending)
    except Exception as exc:
     with self.lock:self.storage_error='Learning output: '+str(exc)[:180]
  if time.monotonic()<self.next_save:return
  self.next_save=time.monotonic()+60;self.flush()
