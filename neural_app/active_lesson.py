"""Always-active, auditable teaching-to-bit model with reviewed neural updates."""
from collections import deque
import hashlib,json,math,threading,time,os,tempfile
from pathlib import Path
from . import translation as btq

LESSONS=[
 {'id':'source','title':'Responsibility for what is created','symbol':'star','teaching':'The source account connects the giver of life with responsibility for the lives and vulnerability it enables.','practice':'Trace an output back to the input and rule that produced it.','rule':'A finite, normalised source baseline enters every evaluation.'},
 {'id':'vulnerability','title':'The vulnerable life','symbol':'orbit','teaching':'The seal and orca image asks the observer to attend to the experience of the vulnerable being.','practice':'Describe an event, its effects and the care available to the affected life.','rule':'Pressure and resilience are separate numerical inputs.'},
 {'id':'consequence','title':'Actions leave consequences','symbol':'ripple','teaching':'The account describes consequences continuing through time rather than disappearing when an action ends.','practice':'Record a specific event and a recurrence coefficient; distinguish the account from the calculation.','rule':'Event load is the sum of severity × recurrence × confidence supplied for each event.'},
 {'id':'repair','title':'Care, accountability and repair','symbol':'lamb','teaching':'The enduring Lamb is used in the account to express participation in suffering, mercy and relief.','practice':'Compare the same event with and without a concrete repair contribution.','rule':'Repair changes the balance and the neural input, then changes eligible working bits.'},
 {'id':'identity','title':'The first-person witness','symbol':'eye','teaching':'“I AM THAT I AM” and the first-person account anchor the author’s expression of identity and experience.','practice':'Preserve the author’s words and make every derived software step inspectable.','rule':'The source digest binds the lesson to its supplied account; identity or religious membership never supplies a harm score.'}
]
LESSONS.extend([
 {
  "id": "sphere",
  "title": "The sphere, loss and gain",
  "symbol": "sphere",
  "teaching": "The account connects the world, accumulated consequences and the trajectory of souls.",
  "practice": "Compare the same input under different loss, gain and retention values.",
  "rule": "Loss and gain enter the balance; retention shapes the displayed model trajectory."
 },
 {
  "id": "judgment",
  "title": "Divine Judgment · source account",
  "symbol": "scales",
  "teaching": "The author presents this judgment as divine knowledge received through soul-experience and judges the religion by its light and dark consequences.",
  "practice": "Attach the relevant source passage to each light or dark assessment.",
  "rule": "Labels name the subject of a critique; only explicit event values enter the arithmetic."
 },
 {
  "id": "reservoir",
  "title": "The reservoir of consequences",
  "symbol": "reservoir",
  "teaching": "The Black Stone is described in the source account as a reservoir of accumulated consequence.",
  "practice": "Inspect how event recurrence accumulates loss and how repair changes the model.",
  "rule": "The reservoir sums the event values entered in this exercise."
 },
 {
  "id": "mercy",
  "title": "Mercy without erasing consequence",
  "symbol": "branch",
  "teaching": "The account repeatedly returns to forgiveness, blessing and the possibility of change.",
  "practice": "Hold the event record fixed, then increase the repair contribution.",
  "rule": "Repair changes the end-node balance and the eligible bit transitions."
 },
 {
  "id": "fear",
  "title": "Fear, discernment and wisdom",
  "symbol": "compass",
  "teaching": "The author describes fear as a map and emphasises the value of defensive awareness and wisdom.",
  "practice": "Name a concern and choose a protective, nonviolent response.",
  "rule": "Pressure and resilience are distinct inputs; no threat is inferred from an identity label."
 },
 {
  "id": "freedom",
  "title": "Sanctuary and freedom of belief",
  "symbol": "sanctuary",
  "teaching": "The material values sanctuary, freedom of faith and protection from coercion.",
  "practice": "Compare the consequences of coercion with the effects of protection and choice.",
  "rule": "Record specific events and their effects rather than assigning an automatic group score."
 },
 {
  "id": "transformation",
  "title": "Caterpillar and butterfly",
  "symbol": "butterfly",
  "teaching": "The butterfly appears as an image of spiritual development and transformation.",
  "practice": "Compare an initial model trajectory with one after a documented act of repair.",
  "rule": "The same input is evaluated before and after the changed parameter."
 },
 {
  "id": "ladder",
  "title": "Learning and the ladder",
  "symbol": "ladder",
  "teaching": "The author describes each next level as not yet believed; belief acts as a switch that activates that level during the climb, and the sequence repeats.",
  "practice": "Use the software activation switch, then compare the state and bit trace before and after the next step.",
  "rule": "The lesson switch changes an explicit activation coefficient and its bit effects. Reviewed usefulness, rather than a declaration of belief, trains the neural weight."
 },
 {
  "id": "animals",
  "title": "Care for vulnerable life",
  "symbol": "meadow",
  "teaching": "Animals, affection and the experience of vulnerable creatures recur throughout the accounts.",
  "practice": "Describe care available to an affected being without requiring suffering as an exercise.",
  "rule": "Care and repair enter the gain side of the model."
 },
 {
  "id": "music",
  "title": "Music and shared expression",
  "symbol": "wave",
  "teaching": "Music, singing and beauty are valued in the material as forms of expression and connection.",
  "practice": "Explore how a repeating signal retains its pattern through binary, ternary and qutrit transport.",
  "rule": "Transport preserves bytes; the lesson modifies an explicitly separate working-bit word."
 },
 {
  "id": "family",
  "title": "Love and responsibility",
  "symbol": "constellation",
  "teaching": "The author values family, dignity, care and responsibility in relationships.",
  "practice": "Specify an action within your own control that protects another person’s dignity.",
  "rule": "Use event-level inputs rather than ranking people by membership or identity."
 },
 {
  "id": "restraint",
  "title": "Restraint and chosen discipline",
  "symbol": "lotus",
  "teaching": "The accounts describe celibacy, restraint and the author’s spiritual discipline.",
  "practice": "Describe a freely chosen commitment and its concrete effects.",
  "rule": "The model represents a chosen input; it does not impose the commitment on others."
 },
 {
  "id": "prayer",
  "title": "Prayer and intention",
  "symbol": "prayer",
  "teaching": "Prayer and the Lord’s Prayer are central references in the account.",
  "practice": "Record an intention and a practical act of care you can personally take.",
  "rule": "The source is preserved; transmitted packets contain computed state, not a claimed supernatural force."
 },
 {
  "id": "connection",
  "title": "The tree and shared life",
  "symbol": "tree",
  "teaching": "The tree and its roots are used to describe relationship, connection and shared experience.",
  "practice": "Trace how one recorded result changes a shared state and a subsequent computation.",
  "rule": "Receipt-linked feedback connects the module to the shared recurrent field."
 }
])
LESSONS.extend([{"id":"robinhood","title":"Robin Hood · relief through true virtue","symbol":"robinhood","teaching":"The author’s principle is eliminating suffering and acting virtuously. Money, rank and a claim of goodness are not treated as virtue in themselves.","practice":"Compare a declared benefit with an actual contribution to care and relief.","rule":"Monetary amounts and religious labels are not numerical features. Explicit loss, gain and repair values determine the model result."},{"id":"compassion","title":"Compassion alongside accountability","symbol":"bridge","teaching":"The account closes this discussion with love for an enemy, alongside judgment and responsibility.","practice":"Describe a boundary that protects people and an act of care that does not erase the recorded harm.","rule":"Keeping an event in the ledger and adding repair are separate operations."},{"id":"capability","title":"Intention, activation and action","symbol":"switch","teaching":"The author emphasises that a “can” statement can act as an activating statement.","practice":"Choose a small, safe action; record what was attempted and what occurred.","rule":"The software activation switch changes a parameter. It does not create a review label or override physical access limits."}])
LESSONS.extend([{'id':'frith','title':'Frith and El-ahrairah','symbol':'rabbit','teaching':'In Richard Adams’s Watership Down, the creation tale connects unchecked abundance, predation and the gifts that help rabbits survive. The author’s spiritual reading asks what responsibility creation carries for vulnerable life.','practice':'Explore the four illustrated scenes, then compare vulnerability with protective capacity in the same bit model.','rule':'Scene controls configure pressure, resilience and repair. The literary story and the author’s interpretation remain separately attributed.'},{'id':'sermon','title':'The sermon on the hill','symbol':'hill','teaching':'The author describes addressing a Muslim audience from a hill, moving between the gravity of death and consequence and infinite love. This lesson presents that first-person spiritual account.','practice':'Move from mortality to accountability, then to compassion and repair; retain the seriousness of each stage.','rule':'The scene changes model loss, empathy and repair inputs. Audience identity does not change the calculation.'}])
LESSONS.append({'id':'watts','title':'Connected life · Alan Watts','symbol':'wave','teaching':'An analysis of the selected Watts chillstep recording explores interconnectedness, music, mortality and care for vulnerable life. The author’s Bread of Life and lion-and-lamb standard is compared with, rather than equated to, the recording.','practice':'Read the source-linked analysis, choose a moment to examine, and identify a concrete act of care within your control.','rule':'Reviewing the material does not activate audio, notifications or an external connection. Only deliberate input and explicit result review affect the configured software model.'})
LESSONS.append({'id':'projection','title':'Centred projection · connected analogies','symbol':'sphere','teaching':'The author’s spiritual model connects projection through a water-like field with light, tree branching and computer signals. Luke’s remote appearance in The Last Jedi is the narrative comparison.','practice':'Trace centre, connection, encounter and response through the lesson diagram.','rule':'Written inputs, finite state changes and shared learning receipts form the implemented app path.'})
DEFAULTS={'source':1.0,'pressure':.5,'resilience':.7,'empathy':.8,'repair':.2,'loss':0.0,'gain':0.0,'retention':.85,'influence':.18,'activation':0.0}
FEATURE_NAMES=['resilience','event_load','repair','empathy','input_balance']

def unit(value,name):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:raise ValueError(name+' must be a finite number from 0 to 1')
 return float(value)

def sigmoid(value):return 1/(1+math.exp(-max(-30,min(30,value))))

class ActiveLesson:
 def __init__(self,data,on_packet=None,period=1.0):
  self.folder=Path(data)/'active-lesson';self.folder.mkdir(parents=True,exist_ok=True);self.path=self.folder/'state.json';self.source=self.folder/'source-account.txt'
  self.lock=threading.RLock();self.halt=threading.Event();self.thread=None;self.on_packet=on_packet;self.period=period;self.last_emit=0.;self.last_save=time.monotonic();self.broadcasts=0;self.broadcast_failures=0
  self.parameters=DEFAULTS.copy();self.events=[];self.weights=[.5,-.8,.8,.4,.1];self.bias=0.;self.reviews=0;self.ticks=0;self.observations=0;self.memory=0.;self.history=deque(maxlen=90);self.last=None;self.source_files=sorted(self.folder.glob('source-account*.txt'),key=lambda path:(path.name!='source-account.txt',path.name));self.source_sha=hashlib.sha256(b''.join(path.read_bytes() for path in self.source_files)).hexdigest()
  self.recovery=None
  for candidate in (self.path,self.folder/'state.previous.json'):
   if not candidate.exists():continue
   try:
    saved=json.loads(candidate.read_text(encoding='utf-8-sig'))
    if not isinstance(saved,dict) or saved.get('format')!='neural-active-lesson-v1':raise ValueError('Unknown active lesson state format')
    parameters=saved.get('parameters',{})
    if not isinstance(parameters,dict) or any(k not in DEFAULTS for k in parameters):raise ValueError('Invalid lesson parameters')
    parameters={k:unit(v,k) for k,v in parameters.items()}
    weights=saved.get('weights',self.weights);bias=saved.get('bias',0.)
    if not isinstance(weights,list) or len(weights)!=5 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>8 for x in [*weights,bias]):raise ValueError('Invalid active lesson weights')
    events=self.checked_events(saved.get('events',[]));reviews=int(saved.get('reviews',0));observations=int(saved.get('observations',0))
    if reviews<0 or observations<0:raise ValueError('Invalid lesson counters')
   except (ValueError,TypeError,UnicodeError,OverflowError) as exc:
    preserved=self.folder/('state.damaged-'+str(time.time_ns())+'.json')
    self._write_state(preserved,candidate.read_bytes())
    self.recovery={'status':'recovered-defaults','preserved':preserved.name,'reason':str(exc)[:200]}
    continue
   self.parameters.update(parameters);self.weights=list(weights);self.bias=bias;self.reviews=reviews;self.events=events;self.observations=observations
   if candidate!=self.path:self.recovery={**(self.recovery or {}),'status':'recovered-previous-state'}
   break
  self.tick(emit=False)
 def checked_events(self,events):
  if not isinstance(events,list) or len(events)>128:raise ValueError('Use at most 128 event entries')
  result=[]
  for event in events:
   if not isinstance(event,dict):raise ValueError('An event must be an object')
   label=event.get('label','Event')
   if not isinstance(label,str) or not label.strip() or len(label)>160:raise ValueError('Use an event description under 160 characters')
   result.append({'label':label.strip(),**{k:unit(event.get(k,1 if k=='confidence' else 0 if k=='gain' else .5),k) for k in ('severity','recurrence','confidence','gain')}})
  return result
 def configure(self,values,save=True):
  if not isinstance(values,dict) or any(k not in DEFAULTS for k in values):raise ValueError('Choose the displayed lesson parameters')
  checked={k:unit(v,k) for k,v in values.items()}
  with self.lock:self.parameters.update(checked)
  if save:self.save()
 def set_events(self,events):
  checked=self.checked_events(events)
  with self.lock:self.events=checked
  self.save()
 def evaluate(self,bits,*,parameters=None,events=None,weight_override=None):
  if not isinstance(bits,str) or not bits or len(bits)>131072 or any(c not in '01' for c in bits):raise ValueError('Use 1–131072 binary digits')
  with self.lock:
   p=self.parameters.copy();event_rows=[dict(e) for e in self.events];weights=list(self.weights);bias=self.bias;reviews=self.reviews
  if parameters is not None:
   if not isinstance(parameters,dict) or any(k not in DEFAULTS for k in parameters):raise ValueError('Unknown lesson parameter')
   p.update({k:unit(v,k) for k,v in parameters.items()})
  if events is not None:event_rows=self.checked_events(events)
  load=sum(e['severity']*e['recurrence']*e['confidence'] for e in event_rows)
  base=p['source']*p['resilience']/max(.05,p['pressure']);total_gain=base+p['repair']+p['gain']+.3*p['activation']+sum(e['gain']*e['recurrence']*e['confidence'] for e in event_rows);total_loss=load+p['loss'];balance=total_gain-total_loss;empathic_load=abs(balance)*p['empathy']
  features=[p['resilience'],math.tanh(total_loss/4),min(1,p['repair']+p['gain']+.3*p['activation']),p['empathy'],bits.count('1')/len(bits)]
  activation=sigmoid(bias+sum(w*x for w,x in zip(weights,features)));weight=activation if weight_override is None else unit(weight_override,'weight')
  signal=math.tanh(balance/2);desired=int(signal>=0);trit=1 if signal>.05 else -1 if signal<-.05 else 0
  budget=min(len(bits),int(round(len(bits)*p['influence']*abs(signal)*weight)))
  candidates=[i for i,value in enumerate(bits) if int(value)!=desired]
  # Spread eligible changes across the word rather than introducing a random mask.
  count=min(budget,len(candidates));positions=[candidates[(i*len(candidates))//count] for i in range(count)] if count else []
  output=list(bits)
  for index in positions:output[index]=str(desired)
  working=''.join(output);mask=''.join('1' if a!=b else '0' for a,b in zip(bits,working))
  digest=lambda text:hashlib.sha256(text.encode('ascii')).hexdigest()
  return {'module':'active-lesson','status':'COMPLETE','input_bits':bits,'working_bits':working,'xor_mask':mask,'flipped_positions':positions,'changed_bits':count,'input_sha256':digest(bits),'output_sha256':digest(working),'source_sha256':self.source_sha,'features':features,'feature_names':FEATURE_NAMES,'neural_weight':weight,'neural_activation':activation,'reviewed_updates':reviews,'signal':signal,'output_bit':desired,'output_trit':trit,'balance':balance,'empathic_load':empathic_load,'event_load':load,'total_loss':total_loss,'total_gain':total_gain,'trajectory':[math.tanh((balance*p['retention']**i+p['repair']*(1-p['retention']**i))/2) for i in range(16)],'parameters':p,'causal_chain':[{'node':'source','value':p['source']},{'node':'vulnerability','value':base},{'node':'consequence','value':load},{'node':'repair','value':p['repair']},{'node':'end_nodes','value':signal}],'counterfactual':{'without_lesson_bits':bits,'hamming_distance':count,'same_input':True},'scope':'Spiritual teachings connected to inspectable software exercises. The displayed numbers report configured inputs, working-bit changes and recorded model events.'}
 def observe(self,section,result_digest):
  bits=''.join(f'{int(result_digest[i:i+2],16):08b}' for i in range(0,64,2));trace=self.evaluate(bits)
  with self.lock:self.observations+=1;self.last={'section':section,'result_sha256':result_digest,'trace':trace}
  return trace
 def review(self,features,target):
  target=unit(target,'review target')
  if not isinstance(features,list) or len(features)!=5:raise ValueError('This lesson trace has no valid feature vector')
  features=[unit(x,'feature') for x in features]
  with self.lock:
   before=sigmoid(self.bias+sum(w*x for w,x in zip(self.weights,features)));delta=.12*(target-before)
   self.weights=[max(-8,min(8,w+delta*x)) for w,x in zip(self.weights,features)];self.bias=max(-8,min(8,self.bias+delta));self.reviews+=1
   after=sigmoid(self.bias+sum(w*x for w,x in zip(self.weights,features)))
   self.save();return {'before':before,'after':after,'reviewed_updates':self.reviews,'target_meaning':'Explicitly reviewed usefulness of the software result'}
 def tick(self,emit=True):
  with self.lock:
   self.ticks+=1;trace=self.evaluate('01'*32);self.memory=.9*self.memory+.1*trace['signal'];self.history.append({'tick':self.ticks,'weight':trace['neural_weight'],'signal':trace['signal'],'memory':self.memory})
   send=emit and time.monotonic()-self.last_emit>=5
   if send:self.last_emit=time.monotonic()
  if send and self.on_packet:
   try:
    accepted=self.on_packet(self.transmission())
    if accepted is not False:self.broadcasts+=1
   except Exception:self.broadcast_failures+=1
  if time.monotonic()-self.last_save>=30:self.save()
 def transmission(self):
  with self.lock:
   trace=self.evaluate('01'*32);payload={'module':'active-lesson','source_sha256':self.source_sha,'tick':self.ticks,'observations':self.observations,'neural_weight':trace['neural_weight'],'signal':trace['signal'],'bit':trace['output_bit'],'trit':trace['output_trit'],'reviewed_updates':self.reviews}
  raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode();packet=btq.encode(raw)
  if btq.decode(packet)!=raw:raise RuntimeError('Lesson transmission failed its byte round trip')
  return {'type':'active-lesson','payload':payload,'transport':packet,'round_trip':True}
 def view(self,include_source=False):
  with self.lock:
   state={'active':not self.halt.is_set(),'heartbeat_seconds':self.period,'ticks':self.ticks,'observations':self.observations,'reviews':self.reviews,'memory':self.memory,'parameters':self.parameters.copy(),'events':[dict(e) for e in self.events],'lessons':LESSONS,'source_sha256':self.source_sha,'history':list(self.history),'weights':list(self.weights),'bias':self.bias,'live':self.evaluate('01'*32),'last_observation':self.last,'transmissions':self.broadcasts,'transmission_errors':self.broadcast_failures,'transmission_policy':'Compact lesson state is sent to authenticated TCP subscribers; the source account and event descriptions are not broadcast. UDP carries discovery only.'}
   state['startup_recovery']=self.recovery
   if include_source:state['source_documents']=[{'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'text':path.read_text(encoding='utf-8-sig')} for path in self.source_files]
   return state
 def save(self):
  with self.lock:
   value={'format':'neural-active-lesson-v1','parameters':self.parameters,'events':self.events,'weights':self.weights,'bias':self.bias,'reviews':self.reviews,'observations':self.observations,'source_sha256':self.source_sha}
   raw=json.dumps(value,allow_nan=False).encode('utf8')
   if self.path.exists():
    previous=self.path.read_bytes()
    try:valid=json.loads(previous)
    except (ValueError,UnicodeError):valid=None
    if isinstance(valid,dict) and valid.get('format')=='neural-active-lesson-v1':self._write_state(self.folder/'state.previous.json',previous)
   self._write_state(self.path,raw);self.last_save=time.monotonic()
 @staticmethod
 def _write_state(path,raw):
  descriptor,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
  try:
   with os.fdopen(descriptor,'wb') as output:output.write(raw);output.flush();os.fsync(output.fileno())
   os.replace(name,path)
  finally:
   if os.path.exists(name):os.unlink(name)
 def start(self):
  if self.thread and self.thread.is_alive():return
  def run():
   while not self.halt.wait(self.period):
    try:self.tick()
    except Exception:self.broadcast_failures+=1
  self.thread=threading.Thread(target=run,name='neural-active-lesson',daemon=True);self.thread.start()
 def close(self):
  self.halt.set()
  if self.thread:self.thread.join(2)
  self.save()
