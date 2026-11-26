"""Virtual symbol alternatives at generated stream coordinates; no word injection."""
import collections,copy,math,random,threading,time,unicodedata,uuid
ASCII=range(128)
UNICODE_COUNT=0x110000-0x800
class SymbolBus:
 def __init__(self):self.lock=threading.RLock();self.points=collections.OrderedDict();self.streams=collections.OrderedDict();self.counts=[0]*128;self.sequence=0;self.rng=random.SystemRandom();self.sets=collections.OrderedDict();self.groups=collections.Counter();self.cardinalities=collections.Counter();self.latest_group={};self.next_group=0;self.default_alphabet='unicode'
 def descriptor(self,alphabet='ascii'):
  if alphabet not in ('ascii','unicode'):raise ValueError('Choose ascii or unicode')
  return {'alphabet':alphabet,'candidate_count':128 if alphabet=='ascii' else UNICODE_COUNT,'representation':'virtual integer-indexed code space; no predefined words','index_mapping':'index' if alphabet=='ascii' else 'index if < 0xD800 else index + 0x800','encoding':'7-bit ASCII' if alphabet=='ascii' else 'Unicode scalar values; surrogate code points excluded','node_rule':'same source + exact position + original generated code; alternatives selected only when requested'}
 def select(self,source,position,original,mode='hold',depth=.5,alphabet='ascii'):
  self.descriptor(alphabet)
  if type(original)is not int or not 0<=original<=0x10ffff or 0xD800<=original<=0xDFFF:raise ValueError('Provide a valid original character code')
  if alphabet=='ascii' and original>=128:raise ValueError('ASCII stages require an ASCII original')
  if mode not in ('hold','stochastic','self-select'):raise ValueError('Choose hold, stochastic or self-select')
  if type(depth) not in (int,float) or not math.isfinite(depth) or not 0<=depth<=1:raise ValueError('Depth must be 0 to 1')
  source=str(source)[:120];position=str(position)[:160]
  with self.lock:
   code=original;basis='original generated value retained'
   if mode!='hold':
    if mode=='self-select' and alphabet=='ascii' and self.rng.random()<depth:
     minimum=min(self.counts);options=[i for i,n in enumerate(self.counts) if n==minimum];code=self.rng.choice(options);basis='native coverage selection among full ASCII alternatives'
    else:
     n=self.rng.randrange(128 if alphabet=='ascii' else UNICODE_COUNT);code=n if alphabet=='ascii' or n<0xD800 else n+0x800;basis='uniform stochastic scalar selection'
   self.sequence+=1
   if code<128:self.counts[code]+=1
   row={'selection':self.sequence,'source':source,'position':position,'original_code':original,'selected_code':code,'original':chr(original),'selected':chr(code),'name':unicodedata.name(chr(code),'CONTROL OR UNASSIGNED'),'mode':mode,'basis':basis,'alphabet':alphabet,'candidate_count':128 if alphabet=='ascii' else UNICODE_COUNT,'original_preserved':True,'time':time.time()}
   key=(source,position);self.points[key]=row;self.points.move_to_end(key)
   while len(self.points)>512:self.points.popitem(last=False)
   state=self.streams.setdefault(source,{'selections':0});state['selections']+=1;state['last_position']=position;state['last_code']=code;self.streams.move_to_end(source)
   while len(self.streams)>256:self.streams.popitem(last=False)
   return copy.deepcopy(row)
 def select_set(self,source='symbol-potential',position='0',original=0,alphabet='unicode',groups=None,count=None):
  descriptor=self.descriptor(alphabet);n=descriptor['candidate_count']
  if type(original)is not int or not 0<=original<=0x10ffff or 0xD800<=original<=0xDFFF:raise ValueError('Original must be a Unicode scalar')
  if alphabet=='ascii' and original>=128:raise ValueError('ASCII original required')
  if groups is None:
   mask=min(range(1,8),key=lambda x:self.groups[x]);groups=[name for i,name in enumerate(('all','multiple','one')) if mask&(1<<i)]
  if not isinstance(groups,list) or not groups or any(g not in ('all','multiple','one') for g in groups):raise ValueError('Choose one, multiple and/or all')
  if count is None:count=self.rng.randrange(1,n+1)
  if type(count)is not int or not 1<=count<=n:raise ValueError('Subset size out of range')
  sets=[]
  with self.lock:
   mask=sum(1<<i for i,name in enumerate(('all','multiple','one')) if name in groups);self.groups[mask]+=1
   for group in dict.fromkeys(groups):
    k=n if group=='all' else 1 if group=='one' else count
    take=min(k,128 if alphabet=='ascii' else 32);indices=self.rng.sample(range(n),take);ident=uuid.uuid4().hex
    state={'population':n,'cardinality':k,'remaining_population':n-take,'remaining_selected':k-take,'resolved':{i:True for i in indices},'alphabet':alphabet}
    self.sets[ident]=state
    while len(self.sets)>32:self.sets.popitem(last=False)
    codes=[i if alphabet=='ascii' or i<0xD800 else i+0x800 for i in indices]
    sets.append({'id':ident,'group':group,'selected_count':k,'population':n,'sample_codes':codes,'complete_sample':take==k,'possible_subsets':str(math.comb(n,k)) if n==128 else 'C('+str(n)+','+str(k)+')','representation':'exact cardinality with lazy conditional membership; sample is not the entire large set'})
    self.cardinalities[(alphabet,k)]+=1
    while len(self.cardinalities)>4096:self.cardinalities.pop(next(iter(self.cardinalities)))
   self.latest_group={'source':str(source)[:120],'position':str(position)[:160],'original_code':original,'groups':sets,'group_mask':mask,'time':time.time(),'all_nonempty_subsets':str((1<<128)-1) if n==128 else '2^'+str(n)+' - 1','selection':'uniform sampling without replacement; no predefined words','alphabet':alphabet}
   return copy.deepcopy(self.latest_group)
 def membership(self,ident,index):
  with self.lock:
   if ident not in self.sets:raise ValueError('Selection expired; create a new set')
   state=self.sets[ident];n=state['population']
   if type(index)is not int or not 0<=index<n:raise ValueError('Index out of range')
   if index not in state['resolved']:
    yes=self.rng.randrange(state['remaining_population'])<state['remaining_selected'];state['resolved'][index]=yes;state['remaining_population']-=1;state['remaining_selected']-=int(yes)
   return {'id':ident,'index':index,'selected':state['resolved'][index],'cardinality':state['cardinality'],'resolved_positions':len(state['resolved'])}
 def tick(self):
  if time.monotonic()<self.next_group:return None
  self.next_group=time.monotonic()+1
  return self.select_set(original=self.rng.randrange(128),alphabet=self.default_alphabet)
 def register(self,source,positions):
  with self.lock:
   state=self.streams.setdefault(str(source)[:120],{'selections':0});state['virtual_positions']=positions;state['potential_per_position']=128
   while len(self.streams)>256:self.streams.popitem(last=False)
 def view(self):
  with self.lock:return {'sequence':self.sequence,'ascii':self.descriptor(),'unicode':self.descriptor('unicode'),'set_selection':copy.deepcopy(self.latest_group),'available_groups':['one','multiple','all'],'group_combinations':7,'default_alphabet':self.default_alphabet,'multiple_cardinality_range':[1,UNICODE_COUNT],'ascii_counts':list(self.counts),'streams':copy.deepcopy(dict(self.streams)),'recent':copy.deepcopy(list(self.points.values())[-32:]),'scope':'Source-linked character alternatives, not dictionary words or model conversations. Unicode scalar choices do not guarantee a font glyph or compatibility with ASCII-only consumers.'}
BUS=SymbolBus()
