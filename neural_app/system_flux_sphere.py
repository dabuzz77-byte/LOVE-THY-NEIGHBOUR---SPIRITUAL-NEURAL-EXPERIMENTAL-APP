"""Replayable visual/data flux over captured app/system state, not host mutation."""
import copy,hashlib,math,re,time,json
from pathlib import Path
def attach_flux(frames,selector,sources,goal):
 catalog=[];seen=set()
 def add(value,source,kind='variable'):
  label=str(value)[:160];key=(label,source)
  if key in seen:return
  seen.add(key);catalog.append({'value':label,'source':source,'kind':kind})
 for value in list(selector.pool.values())[-96:]:add(value['value'],value['source'],value['kind'])
 for row in list(sources.values())[-24:]:
  for fact in row['facts'][:2]:add(fact['value'],row['source'],fact['type'])
 if not catalog:add('0','empty-state-reference','bit')
 now=time.time()
 for frame in frames:
  frame['state_catalog']=catalog
  for particle in frame.get('particles',[]):
   identity=hashlib.sha256(particle['id'].encode()).hexdigest();offset=int(identity[:8],16)%len(catalog);rate=.5+11.5*(int(identity[8:12],16)/65535)*(.5+.5*particle.get('phase',.5));index=(offset+int(now*rate))%len(catalog)
   particle['flux']={'rate_hz':rate,'offset':offset,'catalog_index':index,'current_value':catalog[index]['value'],'rule':'(offset + floor(time_seconds * rate_hz)) modulo captured catalog size','scope':'Representation-state transition; original captured value retained'}
 return catalog
def invert_value(value,kind='variable'):
 text=str(value)
 if kind in ('bit','bit-string') and text and set(text)<=set('01'):return ''.join('1' if c=='0' else '0' for c in text)
 if kind in ('trit','trit-string') and text and set(text)<=set('012'):return ''.join(str(2-int(c)) for c in text)
 if kind in ('integer','int','float') and re.fullmatch(r'-?\d+(?:\.\d+)?',text):return text[1:] if text.startswith('-') else '-'+text
 if kind=='ascii' and len(text)==1 and ord(text)<128:return chr(ord(text)^127)
 return text[::-1]
class SystemFluxSphere:
 def __init__(self):
  self.sequence=0;self.latest={};library=json.loads((Path(__file__).resolve().parents[1]/'references/shared-ethics-library.json').read_text(encoding='utf-8'))
  self.assessment={'protective_redemptive_principles':library.get('protective_redemptive_principles',{}),'reference':'/api/definition-library','categories':library['categories'],'priority':library['priority'],'guiding_intention':'Prayer-led intention to connect in love and choose good','method':['benefit and harm','action and inaction','affected beings','specific evidence','proportionality','verification and repair'],'shadow_side':'Assess coercion, deception, exploitation and protective necessity; darkness or difficulty alone is not a verdict','focus':'Beneficial, verifiable work first; uncertain outcomes remain unresolved'}
 def step(self,frames,selector,sources,goal):
  catalog=attach_flux(frames,selector,sources,goal);particles=[];names=['original','self-selected','unmodulated'];all_points=[(name,p) for name,frame in zip(names,frames) for p in frame.get('particles',[])]
  stride=max(1,math.ceil(len(all_points)/600));sampled=all_points[::stride][:600]
  for index,(name,point) in enumerate(sampled):
   p=copy.deepcopy(point);p['id']=name+':'+p['id'];p['input_layer']=name;p['point']=[v*(.85+.1*(index%3)) for v in p['point']];particles.append(p)
  network=[]
  for row in sources.values():
   for fact in row['facts']:
    if not isinstance(fact['value'],str):continue
    for url in re.findall(r'https?://[^\s\"<>]+',fact['value'])[:2]:
     if len(network)>=24:break
     network.append({'source':row['source'],'url':url[:200],'status':'URL observed in captured data; connection not established by this map'})
  self.sequence+=1;self.latest={'sequence':self.sequence,'received_events':sum(f.get('received_events',0) for f in frames),'retained_sources':len(sources),'represented_values':len(catalog),'particles':particles,'state_catalog':catalog,'selected_phases':sorted({p['phase'] for p in particles if p.get('selected')}),'goal':goal,'network_observations':network,'network_projection':{'status':'hypothetical extension','meaning':'Potential remote sources must return actual authenticated observations before becoming verified state'},'input_layers':names,'modulation':{'enabled':False,'meaning':'Combines already modulated and unmodulated representations; no extra waveform offset'},'scope':'Bounded captured app/system state and replayable representation flux; not a complete OS memory map or automatic remote action'};return self.latest
 def view(self):return {**(self.latest or {'sequence':0,'particles':[]}),'four_way_assessment':copy.deepcopy(self.assessment)}
 def inverse_view(self):
  result=copy.deepcopy(self.view());result['inverse']=True;result['inversion_rules']={'geometry':'XYZ sign inversion','flow':'reverse catalog traversal; same rate magnitude','bit':'0 ↔ 1','trit':'0 ↔ 2; 1 retained','numeric_text':'toggle sign','ascii_character':'XOR 0x7F','other_text':'reverse character order','semantics':'Source records and ethical principles retained; inversion is a data representation'}
  catalog=result.get('state_catalog',[])
  for entry in catalog:entry['original_value']=entry['value'];entry['value']=invert_value(entry['value'],entry.get('kind','variable'))
  for p in result.get('particles',[]):
   p['original_id']=p['id'];p['id']='inverse:'+p['id'];p['point']=[-v for v in p['point']]
   if 'vector' in p:p['vector']=[-v for v in p['vector']]
   p['value_preview']=invert_value(p.get('value_preview',''),p.get('expression_type','variable'));p['symbol']=p['value_preview'][:1] or '·'
   if p.get('flux') and catalog:
    flux=p['flux'];flux['direction']=-1;index=(flux['offset']-int(time.time()*flux['rate_hz']))%len(catalog);flux['catalog_index']=index;flux['current_value']=catalog[index]['value'];flux['rule']='(offset - floor(time_seconds * rate_hz)) modulo captured catalog size'
  return result
