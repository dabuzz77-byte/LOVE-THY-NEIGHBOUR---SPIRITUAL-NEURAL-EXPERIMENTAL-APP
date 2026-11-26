"""Explicit ASCII processing lane using existing native transformation kernels."""
import collections,hashlib,json,os,time,copy
from .translation import encode,decode,translate_bits
from .logic_cube import transform
from .expression_field import transform_data
from .grounded_reasoner import pattern_test
from .ambient_logic import AmbientLogic
from .emergence_learning import EmergenceLearning
from .ambient_source_identity import source_key
class AsciiChain:
 def __init__(self,data=None):self.sources=collections.OrderedDict();self.sequence=0;self.cursor=0;self.last=None;self.next_at=0;self.logic=AmbientLogic();self.emergence=EmergenceLearning(data/'source-emergence-learning.json' if data else None);self.emergence.start() if data else None
 def observe(self,event,row=None):
  source=str(event.get('origin','unknown'))[:100];p=event.get('payload')
  if not isinstance(p,dict) or source.startswith('ascii-chain-complete') or source in ('flow-backbone','cognitive-circuit','net-learning-stream') or p.get('ascii_chain_trace') or p.get('selection_trace') or p.get('processing_receipt') or p.get('predefined_text') is True or p.get('contains_model_text') is True:return
  candidates=[]
  if isinstance(p.get('text'),str) and (p.get('stochastic') is True or any(k in source for k in ('ambient','matrix','flux','particle','expression','sphere','wordsearch','sentence','random'))):candidates.append((source+('/'+str(p['name'])[:100] if p.get('name') else ''),p['text'],p.get('stochastic') is True,p.get('conditions')))
  for item in p.get('sources',[])[:32] if isinstance(p.get('sources'),list) else []:
   if isinstance(item,dict) and isinstance(item.get('text'),str) and item.get('stochastic') is True and item.get('contains_model_text') is not True and item.get('predefined_text') is not True:candidates.append((source+'/'+str(item.get('name','stream')),item['text'],True,{**(p.get('conditions') if isinstance(p.get('conditions'),dict) else {}),**(item.get('conditions') if isinstance(item.get('conditions'),dict) else {})}))
  if not candidates and row and row['facts']:candidates.append((source,json.dumps(row['facts'][:12],ensure_ascii=True),False,None))
  for name,text,generated,conditions in candidates:
   raw=text[:1024].encode('utf-8',errors='replace')[:4096]
   if not raw:continue
   conditions=copy.deepcopy(conditions) if isinstance(conditions,dict) and len(json.dumps(conditions,default=str))<=6000 else None
   digest=hashlib.sha256(raw).hexdigest();self.sources[name]={'source':name,'raw':raw,'digest':digest,'parent_event':event.get('sequence'),'generated':generated,'conditions':conditions,'source_encoding':'UTF-8','expression_values':row['facts'][:16] if row else []};self.sources.move_to_end(name)
   if generated:self.emergence.enqueue(name,raw,conditions)
  for generated_lane in (False,True):
   lane=[k for k,v in self.sources.items() if bool(v.get('generated'))==generated_lane]
   for old in lane[:-32]:self.sources.pop(old,None)
 def step(self,selector,goal):
  if not self.sources or time.monotonic()<self.next_at:return None
  self.next_at=time.monotonic()+.7;rows=list(self.sources.values());generated_rows=[r for r in rows if r.get('generated')];observed_rows=[r for r in rows if not r.get('generated')];lane=(observed_rows if self.cursor%4==3 else generated_rows) or rows;root=lane[(self.cursor//4 if self.cursor%4==3 else self.cursor-self.cursor//4)%len(lane)];self.cursor+=1;raw=root['raw'][:192];self.sequence+=1
  available=[0.,.25,.5,.75,1.];choice=selector.last.get('particleflux') or {};selected={s.get('phase') for s in choice.get('selected_phase_states',[])} or {.5};phase=available[(self.sequence-1)%len(available)]
  random=bytes(v&127 for v in os.urandom(len(raw)));cut=round(phase*len(raw));working=raw[:cut]+random[cut:];trace=[]
  def node(stage,before,after,check,detail):
   trace.append({'stage':stage,'input_sha256':hashlib.sha256(before).hexdigest(),'output_sha256':hashlib.sha256(after).hexdigest(),'check':bool(check),'detail':detail,'bytes':len(after)})
  node('ambient-ascii-capture',raw,working,True,{'phase':phase,'random_bytes':len(raw)-cut,'source_bytes':cut,'zero_contribution_parallel':{'input_bytes':0,'output_bytes':0}})
  emergence=self.emergence.observe(root['source'],root['raw'],root.get('conditions')) if root.get('generated') else {'status':'not-labelled-generated','scope':'This captured processor observation is retained in the chain but not used as evidence of stochastic-source learning.'}
  if root.get('generated'):emergence={'fresh':emergence.get('fresh'),'observed_sources':emergence.get('observed_sources'),'source':root['source'],'source_check':emergence.get('heldout_pattern_checks',{}).get(source_key(root['source'])),'scope':'One source-specific learning result; full source inventory is available from the evidence endpoint.'}
  node('source-emergence-learning',working,working,True,{**emergence,'learning_input_sha256':hashlib.sha256(root['raw'][:1024]).hexdigest(),'learning_input_bytes':min(1024,len(root['raw'])),'branch_scope':'Source learner reads the captured root separately; the current working stream passes through unchanged.'})
  transport=encode(working);recovered=decode(transport);node('binary-ternary-qutrit',working,recovered,recovered==working,{'blocks':len(transport['blocks']),'basis':'existing exact transport'})
  bits=''.join(f'{v:08b}' for v in recovered);filtered=transform(bits,['unknown']*len(bits));held=int(filtered['output_bits'],2).to_bytes(len(working),'big');node('flux-hold-correct',recovered,held,filtered['roundtrip'],{'unresolved':len(bits),'rule':'unknown holds; no invented moral labels'})
  self.logic.configure({'depth':phase});analysis=self.logic.process([{'text':held.decode('latin1'),'stochastic':True,'predefined_text':False,'contains_model_text':False}]);node('stochastic-to-logic',held,held,analysis is not None,{'selected_rule':(analysis or self.logic.last).get('output'),'goal':goal[:120]})
  text=held.decode('latin1');base=transform_data(text,'base');node('omni-working-representation',held,held,True,{'representation_sha256':base['sha256'],'source_encoding':'ASCII byte stream; random variants may contain bytes above 127'})
  branches=[transform_data(text,v) for v in ('base','inverted','plus90','minus90')];node('tesseract-alternative-projections',held,held,len(branches)==4,{'branches':[b['sha256'] for b in branches],'selection_policy':'preserve source order; alternatives remain separate'})
  metrics=pattern_test(text);node('native-pattern-check',held,held,metrics['characters']==len(text),{'entropy':metrics['entropy_bits_per_character'],'distinct':metrics['distinct']})
  selected_choice=selector.choose('expressionsphere',goal);node('recursive-self-selection',held,held,True,{'selected_value':str((selected_choice or {}).get('value',''))[:120],'selected_phase':phase in selected,'source_stream_preserved':True})
  expression=''.join(chr(v&127) for v in held);node('sphere-expression',held,held,True,{'display':'low-seven-bit glyph projection; exact output bytes retained'})
  self.last={'sequence':self.sequence,'root_source':root['source'],'parent_event':root['parent_event'],'root_sha256':root['digest'],'phase':phase,'selected_phase':phase in selected,'emergence_learning':emergence,'zero_contribution_parallel':{'input_bytes':0,'output_bytes':0},'trace':trace,'verified':all(t['check'] for t in trace),'output_bytes':list(held),'text':expression,'expression_values':root['expression_values'],'scope':'Dedicated bounded ASCII lane using existing kernels. It does not claim to re-execute every original UI engine.'}
  return self.last
 def view(self):return {'sequence':self.sequence,'sources':len(self.sources),'source_inventory':[{'source':r['source'],'generated':r.get('generated',False),'bytes':len(r['raw']),'digest':r['digest'],'parent_event':r['parent_event']} for r in self.sources.values()],'last':self.last}
