"""Typed selection from retained generated values, shared across all stages."""
import collections,hashlib,json,re,time,os,random,math
from .mind_workspace import terms
from .symbol_bus import BUS as SYMBOL_BUS
class GenerationSelector:
 def __init__(self):
  self.pool=collections.OrderedDict();self.counts=collections.Counter();self.sequence=0;self.last={};self.enabled=True;self.feedback=True;self.overrides={};self.self_transform=True;self.next_due={};self.cadence={};self.cursor=0;self.depth=.5;self.rng=random.SystemRandom();self.parallel_gain=.5;self.fade_auto=False;self.fade_started=time.monotonic();self.parallel_sources={};self.phase_performance={};self.auto_spectrum=True;self.phase_started=time.monotonic()
 def observe(self,row,event):
  payload=event.get('payload') or {}
  if not isinstance(payload,dict) or payload.get('selection_trace') or row['source']=='cognitive-circuit':return
  source=row['source'];generated=payload.get('stochastic') is True or any(s in source for s in ('matrix','flux','cube','tesseract','sphere','expression','recursive','particle','ambient','generation'))
  if not generated:return
  def add(kind,value,path,derivation='captured value'):
   identity=hashlib.sha256(json.dumps([source,path,kind,value],sort_keys=True,default=str).encode()).hexdigest()
   self.pool[identity]={'id':identity,'kind':kind,'value':value,'source':source,'path':path,'parent_event':row['parent_event'],'derivation':derivation};self.pool.move_to_end(identity)
  selection_facts=row['facts']
  if payload.get('predefined_text') is False and payload.get('contains_model_text') is False and isinstance(payload.get('unicode_codes'),list):
   selection_facts=[{'value':chr(code),'path':['unicode_codes',i]} for i,code in enumerate(payload['unicode_codes'][:128]) if type(code)is int and 0<=code<=0x10ffff and not 0xD800<=code<=0xDFFF]
  elif payload.get('predefined_text') is False and payload.get('contains_model_text') is False and isinstance(payload.get('ascii_codes'),list):
   selection_facts=[{'value':chr(code),'path':['ascii_codes',i]} for i,code in enumerate(payload['ascii_codes'][:128]) if type(code)is int and 0<=code<128]
  for fact in selection_facts:
   value=fact['value'];path=fact['path'];add('variable',value,path)
   if type(value) is int:add('integer',value,path)
   if not isinstance(value,str) or not value:continue
   add('string',value,path)
   for char_index,char in enumerate(value[:32]):
    if ord(char)<128:add('ascii',char,path+['character',char_index],'character present in captured string')
    else:add('unicode',char,path+['character',char_index],'Unicode scalar present in generated string')
   if set(value)<=set('012'):
    for char in set(value):add('trit',int(char),path,'digit selected from captured ternary-compatible string')
   if set(value)<=set('01'):
    for char in set(value):add('bit',int(char),path,'digit selected from captured binary string')
   for word in value.split()[:12]:add('word',word,path,'token occurring in captured string')
   for sentence in re.split(r'(?<=[.!?])\s+',value)[:3]:
    if sentence.strip():add('sentence',sentence,path,'captured string segment; meaning not presumed')
  if payload.get('stochastic') is True:
   gain=self.effective_gain();retained=0;logic_gain=1-gain;logic_count=0
   for ident,candidate in list(self.pool.items()):
    if candidate['source']==source and candidate['derivation'].startswith(('parallel attenuated','parallel deterministic')):self.pool.pop(ident)
   if gain>0:
    for fact in row['facts'][:16]:
     value=fact['value']
     if isinstance(value,str):faded=value[:int(len(value)*gain)]
     elif type(value) in (int,float):faded=value*gain
     else:continue
     if faded=='' or faded is None:continue
     add('variable',faded,fact['path'],'parallel attenuated random contribution; gain='+str(round(gain,4)));retained+=1
   if logic_gain>0:
    for fact in row['facts'][:int(16*logic_gain)]:
     value=fact['value']
     if type(value) in (int,float,bool):result=int(value!=0)
     elif isinstance(value,str):result=int(len(value)>0)
     else:continue
     add('bit',result,['parallel_logic']+fact['path'],'parallel deterministic nonzero/nonempty predicate; gain='+str(round(logic_gain,4)));logic_count+=1
   self.parallel_sources[source]={'random_gain':gain,'logic_gain':logic_gain,'input_value_processing':gain>0,'output_value_emission':gain>0 and retained>0,'retained_random_values':retained,'retained_logic_values':logic_count,'logic_rule':'deterministic nonzero/nonempty predicate','scope':'Complementary parallel lanes; original source remains separate'}
   while len(self.parallel_sources)>128:self.parallel_sources.pop(next(iter(self.parallel_sources)))
  while len(self.pool)>2048:self.pool.popitem(last=False)
 def choose(self,stage,goal='',depth_override=None):
  if depth_override is None and self.enabled and stage not in self.overrides and 'all' not in self.overrides:
   states=[self.choose(stage,goal,d) for d in (0.,.25,.5,.75,1.)];states=[s for s in states if s]
   if not states:return None
   complexity=len(terms(goal));preferred=min(len(states),max(1,complexity//2))
   def priority(s):
    phase=self.phase_performance.get(str(s.get('spectrum_depth',0.)),{});learned=(phase.get('validation_passes',0)+1)/(phase.get('attempts',0)+2)
    return len(terms(goal)&terms(str(s.get('value',''))+' '+s.get('source','')))+(1 if s.get('action_check',{}).get('prediction_matches') else 0)+.1*learned
   def subset_score(mask):
    group=[s for i,s in enumerate(states) if mask&(1<<i)];coverage=1/(1+self.counts[stage+'/subset/'+str(mask)])
    return sum(priority(s) for s in group)/len(group)+.25*coverage-.1*abs(len(group)-preferred)
   mask=max(range(1,1<<len(states)),key=subset_score);self.counts[stage+'/subset/'+str(mask)]+=1
   selected=[s for i,s in enumerate(states) if mask&(1<<i)];count=len(selected);result=dict(max(selected,key=priority));result['available_phase_states']=[{'depth':d,'stochastic_weight':1-d,'logic_weight':d} for d in (0.,.25,.5,.75,1.)];result['selected_phase_states']=[{'phase':s.get('spectrum_depth',0),'kind':s['kind'],'value':s['value'],'operation':s.get('operation'),'source':s['source']} for s in selected];result['state_selection']='all' if count==len(states) else 'multiple' if count>1 else 'one';result['selected_mask']=mask;result['available_combinations']=(1<<len(states))-1;result['state_selection_basis']='all nonempty subsets compared by goal relevance, checked outcomes, coverage and workload'
   ranked_indices=sorted(range(len(states)),key=lambda i:priority(states[i]),reverse=True)
   groups={'all':list(range(len(states))),'multiple':[i for i in range(len(states)) if mask&(1<<i)] if 1<count<len(states) else ranked_indices[:min(3,len(states))],'one':ranked_indices[:1]}
   group_mask=max(range(1,8),key=lambda m:1/(1+self.counts[stage+'/groups/'+str(m)])+.01*int(bool(m&1) and complexity>6));self.counts[stage+'/groups/'+str(group_mask)]+=1
   result['parallel_selection_groups']={name:indices for i,(name,indices) in enumerate(groups.items()) if group_mask&(1<<i)};result['available_group_combinations']=7
   result['phase_candidates']=[{'phase':s.get('spectrum_depth',0),'kind':s['kind'],'value':s['value'],'operation':s.get('operation'),'source':s['source']} for s in states]
   self.last[stage]=result;return result
  depth=self.effective_depth(stage) if depth_override is None else depth_override
  if not self.enabled:return None
  override=self.overrides.get(stage,self.overrides.get('all'))
  if override is not None:
   self.sequence+=1;result={**override,'stage':stage,'selection':self.sequence,'time':time.time(),'reason':'explicit stream override','source':'user-stream-override'};self.last[stage]=result;return result
  if depth==0:
   self.sequence+=1;result={'kind':'integer','value':os.urandom(1)[0],'source':'OS-random baseline','stage':stage,'selection':self.sequence,'time':time.time(),'operation':'stochastic-sample','spectrum_depth':0,'parallel_weights':{'stochastic':1,'logic':0},'phase':'pure software stochastic baseline','chain_context':'zero-point / cosmological framework; software entropy source is explicitly identified'};self.last[stage]=result;self.cadence[stage]=.1;return result
  if not self.pool:return None
  candidates=list(self.pool.values());q=terms(goal);kinds={v['kind'] for v in candidates};kind=min(kinds,key=lambda k:(self.counts[stage+'/'+k],k))
  options=[c for c in candidates if c['kind']==kind]
  def score(c):return 3*len(q&terms(str(c['value'])+' '+c['source']))+1/(1+self.counts[stage+'/'+c['id']])
  explore=False if depth==1 else self.rng.random()>depth
  choice=self.rng.choice(candidates) if explore else max(options,key=score);kind=choice['kind'];self.counts[stage+'/'+kind]+=1;self.counts[stage+'/'+choice['id']]+=1;self.sequence+=1
  original=choice['value'];value=original;operation='preserve';output_kind=kind
  if self.self_transform:
   operations=['preserve','encode-json']
   if type(original) is int:operations+=['increment','decrement']
   if isinstance(original,str):operations+=['reverse','rotate']
   if depth==1:operation=next((op for op in operations if op!='preserve' and op.replace('-',' ') in goal.lower()),'preserve')
   elif explore:operation=self.rng.choice(operations)
   else:operation=min(operations,key=lambda op:self.counts[stage+'/operation/'+op])
   self.counts[stage+'/operation/'+operation]+=1
   if operation=='encode-json':value=json.dumps(original,ensure_ascii=True);output_kind='string'
   elif operation=='increment':value=original+1;output_kind='integer'
   elif operation=='decrement':value=original-1;output_kind='integer'
   elif operation=='reverse':value=original[::-1]
   elif operation=='rotate':value=original[1:]+original[:1]
  symbol_node=None
  if kind in ('ascii','unicode') and isinstance(original,str) and len(original)==1:
   symbol_node=SYMBOL_BUS.select(choice['source'],json.dumps(choice['path'])+':'+stage,ord(original),mode='self-select' if explore else 'hold',depth=depth,alphabet='unicode')
   value=symbol_node['selected'];output_kind='ascii' if ord(value)<128 else 'unicode';operation='symbol-select' if value!=original else 'preserve'
   symbol_node['set_alternatives']=SYMBOL_BUS.select_set(choice['source'],json.dumps(choice['path'])+':'+stage,ord(original))
  interval=.1 if score(choice)>2 else .5 if operation!='preserve' else 1.
  self.cadence[stage]=interval
  result={**choice,'symbol_node':symbol_node,'input_value':original,'value':value,'kind':output_kind,'operation':operation,'stage':stage,'goal':goal,'selection':self.sequence,'time':time.time(),'interval_seconds':interval,'spectrum_depth':depth,'parallel_weights':{'stochastic':1-depth,'logic':depth},'phase':'deterministic registered rules' if depth==1 else 'stochastic exploration' if explore else 'evidence / goal-guided selection','validation':'typed transformation only; semantic usefulness requires downstream task checks','reason':'goal relevance plus underused values, representations and operations'};self.last[stage]=result
  if hasattr(self,'definitions'):
   result['action_check']=self.definitions.record('generation/'+operation,original,value,goal=goal,stage=stage)
   result['alternatives']=self.definitions.alternatives(original)[:4]
  while len(self.counts)>8192:self.counts.pop(next(iter(self.counts)))
  return result
 def batch(self,stages,goal):
  names=list(stages);now=time.monotonic();out=[]
  for offset in range(len(names)):
   index=(self.cursor+offset)%len(names);stage=names[index]
   if now<self.next_due.get(stage,0):continue
   choice=self.choose(stage,goal)
   if choice:out.append(choice);self.next_due[stage]=now+self.cadence.get(stage,1.)
   if len(out)>=4:self.cursor=(index+1)%len(names);break
  return out
 def configure(self,b):
  for key in ('enabled','feedback','self_transform','auto_spectrum'):
   if key in b:
    if type(b[key]) is not bool:raise ValueError(key+' must be boolean')
    setattr(self,key,b[key])
  for key in ('depth','parallel_gain'):
   if key in b:
    value=float(b[key])
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError(key+' must be between zero and one')
    setattr(self,key,value)
  if 'fade_auto' in b:
   if type(b['fade_auto']) is not bool:raise ValueError('fade_auto must be boolean')
   self.fade_auto=b['fade_auto'];self.fade_started=time.monotonic()
  if 'stage' in b:
   from .element_thinking import SPECS
   stage=str(b['stage'])
   if stage!='all' and stage not in SPECS:raise ValueError('Choose an Intelligence Engine stage')
   if b.get('clear') is True:self.overrides.pop(stage,None)
   else:
    value=b.get('value');raw=json.dumps(value,allow_nan=False)
    if len(raw.encode())>4096:raise ValueError('Override must fit within 4096 bytes')
    kind=str(b.get('kind','variable'))
    if kind not in ('variable','string','sentence','word','ascii','integer','bit','trit'):raise ValueError('Choose a supported value type')
    if kind in ('bit','trit') and (type(value) is not int or value not in range(2 if kind=='bit' else 3)):raise ValueError('Use a valid bit or trit')
    if kind=='integer' and type(value) is not int:raise ValueError('Integer requires an integer value')
    if kind in ('string','word','sentence','ascii') and not isinstance(value,str):raise ValueError('Text type requires text')
    if kind=='ascii' and (len(value)!=1 or ord(value)>127):raise ValueError('ASCII requires one character from 0 to 127')
    self.overrides[stage]={'kind':kind,'value':value,'derivation':'explicit user replacement; stream data only'}
  return self.view()
 def effective_gain(self):return max(0.,self.parallel_gain*(1-min(1.,(time.monotonic()-self.fade_started)/60))) if self.fade_auto else self.parallel_gain
 def effective_depth(self,stage):
  if not self.auto_spectrum:return self.depth
  offset=int(hashlib.sha256(stage.encode()).hexdigest()[:4],16)%120
  phase=((time.monotonic()-self.phase_started+offset)%120)/60
  return round(phase if phase<=1 else 2-phase,2)
 def view(self):return {'depth':self.depth,'auto_spectrum':self.auto_spectrum,'parallel_gain':self.effective_gain(),'fade_auto':self.fade_auto,'parallel_random_lanes':dict(self.parallel_sources),'enabled':self.enabled,'feedback':self.feedback,'self_transform':self.self_transform,'cadence_seconds':dict(self.cadence),'overrides':dict(self.overrides),'pool_size':len(self.pool),'kinds':sorted({v['kind'] for v in self.pool.values()}),'sequence':self.sequence,'stages':dict(self.last),'scope':'Selected stream values and explicit replacements; no automatic source-code or host-state modification'}
