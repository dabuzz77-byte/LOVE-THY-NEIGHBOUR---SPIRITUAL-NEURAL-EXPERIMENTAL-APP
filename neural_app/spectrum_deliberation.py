"""Spectrum proposals plus ordered search, selected on training contracts only."""
import collections,copy,hashlib,json,time

def program_at(index,operations,depth):
 n=len(operations)
 for length in range(1,depth+1):
  size=n**length
  if index<size:
   result=[]
   for _ in range(length):result.append(operations[index%n]);index//=n
   return result
  index-=size
 return None

class SpectrumDeliberation:
 def __init__(self,state=None,save=None):
  self.records=collections.OrderedDict();self.procedures={};self.next_at=0;self.cursor=0;self.latest={};self.sequence=0;self.state=state;self.save=save
  if isinstance(state,dict) and state.get('version')==1:
   from .native_synthesis import OPS
   stored=state.get('procedures',{});completed=state.get('completed_contracts',{})
   if not isinstance(stored,dict):stored={}
   if not isinstance(completed,dict):completed={}
   if type(state.get('sequence')) is int and 0<=state['sequence']<=10**12:self.sequence=state['sequence']
   for key,row in list(stored.items())[-32:]:
    if isinstance(row,dict) and row.get('id')==key and isinstance(row.get('operations'),list) and len(row['operations'])<=4 and all(op in OPS for op in row['operations']):self.procedures[key]=copy.deepcopy(row)
   for key,row in list(completed.items())[-16:]:
    if isinstance(row,dict) and row.get('status') in ('contract-verified','heldout-failed-revise-training','registered-search-exhausted','search-budget-reached'):self.records[key]={**copy.deepcopy(row),'seen':set()}
 def persist(self):
  if not isinstance(self.state,dict):return
  self.state.update(version=1,sequence=self.sequence,procedures=copy.deepcopy(self.procedures),completed_contracts={key:{k:copy.deepcopy(v) for k,v in row.items() if k not in ('seen','heldout_checks')} for key,row in self.records.items() if row['status']!='searching'})
  if self.save:self.save()
 def tick(self,c,frames):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+2
  investigations=getattr(c,'investigations',None)
  if not investigations:return
  from .native_synthesis import validate,execute,question_spec
  items=investigations.view().get('items',[]);tasks=[]
  for item in items:
   spec=item.get('experiment_spec') or question_spec(item.get('question',''))
   if spec:
    try:tasks.append((item,validate(spec)))
    except (ValueError,TypeError):continue
  if not tasks:
   self.latest={'status':'waiting-for-example-contract','next':'Register an investigation with training and distinct held-out input/output examples. Pattern and invariant checks continue independently.'};return
  item,spec=tasks[self.cursor%len(tasks)];self.cursor+=1
  signature=hashlib.sha256(json.dumps({k:spec[k] for k in ('examples','operations','max_depth')},sort_keys=True).encode()).hexdigest()
  key=item['id']+':'+signature
  record=self.records.setdefault(key,{'investigation':item['id'],'question':item.get('question'),'training_sha256':signature,'status':'searching','ordered_cursor':0,'tested':0,'seen':set(),'origin_counts':{'spectrum':0,'ordered':0}})
  while len(self.records)>16:self.records.popitem(last=False)
  if record['status']!='searching':self.latest={k:copy.deepcopy(v) for k,v in record.items() if k!='seen'};return
  proposed=[]
  for frame in frames:
   raw=frame['bits'];length=1+int(raw[:4] or '0',2)%spec['max_depth'];operations=[spec['operations'][int(raw[4+i*8:12+i*8] or '0',2)%len(spec['operations'])] for i in range(length)]
   proposed.append(('spectrum',operations))
  for i in range(16):
   operations=program_at(record['ordered_cursor']+i,spec['operations'],spec['max_depth'])
   if operations is not None:proposed.append(('ordered',operations))
  started=time.perf_counter();identity_fits=all(type(row['input'])==type(row['output']) and row['input']==row['output'] for row in spec['examples']);selected={'origin':'identity-baseline','operations':[]} if identity_fits else None
  for origin,operations in proposed:
   if selected:break
   if (time.perf_counter()-started)*1000>10:break
   if record['tested']>=4096:record['status']='search-budget-reached';break
   if origin=='ordered':record['ordered_cursor']+=1
   marker=tuple(operations)
   if marker in record['seen']:continue
   record['seen'].add(marker);record['tested']+=1;record['origin_counts'][origin]+=1
   try:passed=all(type(actual:=execute(operations,copy.deepcopy(row['input'])))==type(row['output']) and actual==row['output'] for row in spec['examples'])
   except (ValueError,TypeError,KeyError,OverflowError,RecursionError):passed=False
   if passed:selected={'origin':origin,'operations':operations};break
  record['elapsed_ms']=round((time.perf_counter()-started)*1000,3)
  if selected:
   # First training-fit program only. Never continue search using held-out failures.
   checks=[]
   for row in spec['holdout']:
    try:actual=execute(selected['operations'],copy.deepcopy(row['input']));passed=type(actual)==type(row['output']) and actual==row['output'];error=None
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError) as e:actual=None;passed=False;error=str(e)[:120]
    checks.append({'passed':passed,'actual':actual,'expected':row['output'],'error':error})
   record.update(selected=selected,identity_training_fits=identity_fits,heldout_checks=checks,status='contract-verified' if all(r['passed'] for r in checks) else 'heldout-failed-revise-training',scope='Training-selected pure program checked once on later cases. No further search uses these held-out outcomes.')
   if record['status']=='contract-verified':
    ident=hashlib.sha256((key+json.dumps(selected['operations'])).encode()).hexdigest()[:20]
    self.procedures[ident]={'id':ident,'operations':selected['operations'],'investigation':item['id'],'training_sha256':signature,'training_cases':len(spec['examples']),'heldout_cases':len(checks),'scope':'Checked on this example contract; fresh inputs still require verification.'};record['procedure']=ident
    while len(self.procedures)>32:self.procedures.pop(next(iter(self.procedures)))
   self.sequence+=1
   c.bus.publish({'origin':'spectrum-deliberation','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'sequence':self.sequence,'status':record['status'],'investigation':item['id'],'selected':selected,'heldout_passed':all(r['passed'] for r in checks),'predefined_text':True,'stochastic':False,'provenance':'training-only proposal selection followed by separate validation'}})
  elif program_at(record['ordered_cursor'],spec['operations'],spec['max_depth']) is None:record['status']='registered-search-exhausted'
  if record['status']!='searching':self.persist()
  self.latest={k:copy.deepcopy(v) for k,v in record.items() if k!='seen'}
 def view(self):return {'sequence':self.sequence,'persistent':self.state is not None,'latest':copy.deepcopy(self.latest),'retained_procedures':copy.deepcopy(list(self.procedures.values())),'scope':'Finite registered pure-operation search. Spectrum proposals and ordered alternatives are both tested; no external actions or execution of generated code.'}
 def use(self,body):
  from .native_synthesis import execute,bounded
  procedure=self.procedures.get(body.get('id')) if isinstance(body,dict) else None
  if procedure is None or 'input' not in body:raise ValueError('Choose a retained spectrum procedure and supply input')
  value=execute(procedure['operations'],copy.deepcopy(bounded(body['input'])))
  return {'result':value,'procedure':procedure['id'],'operations':procedure['operations'],'matches_supplied_expected':type(value)==type(body['expected']) and value==body['expected'] if 'expected' in body else None,'scope':procedure['scope'],'model_calls':0}
