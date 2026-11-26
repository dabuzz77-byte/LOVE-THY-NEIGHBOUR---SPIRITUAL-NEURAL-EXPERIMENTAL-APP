"""Native-first reuse of reviewed, verified procedures; compact model assistance."""
import hashlib,re,time
NUMBER=re.compile(r'(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])')
def shape(text):return NUMBER.sub('{n}',text.strip().lower())
class SelectiveBridge:
 def __init__(self,reasoner):
  self.r=reasoner;self.s=reasoner.s.setdefault('selective_bridge',{'procedures':{},'calls':0,'native_reuses':0,'prompt_tokens':0,'output_tokens':0,'learned':0})
  self.s.setdefault('consecutive_failures',0);self.s.setdefault('failure_records',[])
 def lookup(self,request):
  exact=hashlib.sha256(request.strip().lower().encode()).hexdigest();p=self.s['procedures'].get(exact)
  if p:return {'intent':'plan','text':p['plan'],'source':'verified-exact-procedure','procedure':exact}
  numbers=NUMBER.findall(request)
  for ident,p in self.s['procedures'].items():
   if p.get('shape')!=shape(request) or not p.get('template') or len(numbers)!=p.get('parameters'):continue
   plan=p['template']
   for i,value in enumerate(numbers):plan=plan.replace('{arg'+str(i)+'}',value)
   self.r.workbench.executive.parse(plan)
   return {'intent':'plan','text':plan,'source':'parameterized-reviewed-procedure','procedure':ident}
  return None
 def learn(self,goal):
  teaching=goal.get('bridge_teaching')
  if not teaching or goal['status']!='complete' or not all(s['status']=='verified' for s in goal['steps']):return
  request=teaching['request'];plan=teaching['plan'];key=hashlib.sha256(request.strip().lower().encode()).hexdigest();numbers=NUMBER.findall(request);template=None
  # Numeric generalisation stays reviewable and only covers arithmetic procedures.
  if numbers and len(set(numbers))==len(numbers) and all(s['operation']=='calculate' for s in goal['steps']):
   mapping={v:'{arg'+str(i)+'}' for i,v in enumerate(numbers)};template=NUMBER.sub(lambda m:mapping.get(m[0],m[0]),plan)
  self.s['procedures'][key]={'request':request,'plan':plan,'shape':shape(request),'template':template,'parameters':len(numbers),'verified_steps':len(goal['steps']),'time':time.time(),'scope':'Reviewed procedure with verified operation outcomes; new parameter bindings require review'}
  while len(self.s['procedures'])>128:self.s['procedures'].pop(next(iter(self.s['procedures'])))
  self.s['learned']+=1
 def assist(self,request,body):
  cached=self.lookup(request)
  if cached:self.s['native_reuses']+=1;return cached,False
  mode=body.get('assistant_mode','automatic')
  if mode not in ('automatic','efficient','selected'):raise ValueError('Choose automatic, efficient or selected assistant mode')
  work=bool(re.search(r'\b(make|create|write|read|find|sort|calculate|compute|multiply|divide|add|subtract|organise|organize|check|inspect|analyse|analyze|work out|filter|aggregate|arrange|summarise|summarize|deduplicate|extract|refactor|debug|implement|build|fix|review|code|test)\b',request,re.I))
  # Explicit global route applies to conversation and work requests alike.
  from .assistant_models import installed
  models=installed();explicit=body.get('bridge_model');mode=body.get('assistant_mode','automatic')
  if mode not in ('automatic','efficient','selected'):raise ValueError('Choose automatic, efficient or selected assistant mode')
  circuit=getattr(self.r.runtime,'cognitive_circuit',None);node=getattr(circuit,'thin_inference',None)
  if node and node.route=='off' and not explicit:return {'intent':'explain','text':'The native engine needs a model-assisted planning step for this request, but model assistance is switched off.'},False
  pinned=node.model_for(models) if node and (node.route in ('qwen','llama') or node.selected_model) else None
  if node and (node.route in ('qwen','llama') or node.selected_model) and not pinned and not explicit:raise ValueError('The selected helper model is unavailable; no Llama fallback was made')
  explicit=explicit or pinned
  selected=self.r.s.get('assistant_model');complex_task=bool(body.get('workspace_files') or len(request)>900 or re.search(r'\b(code|coding|debug|implement|refactor|repository|codebase|script|python|javascript|architecture|research|compare)\b',request,re.I))
  use_selected=mode=='selected' or mode=='automatic' and complex_task
  helper=explicit or (selected if use_selected else None) or next((m['name'] for m in models if 'llama3.2_1b_2025_uncensored_v2' in m['name'].lower()),None) or next((m['name'] for m in models if 'llama3.2' in m['name'].lower()),None)
  if not explicit and mode!='selected' and self.s['consecutive_failures']>=2:
   candidates=[m for m in models if 'qwen' in m['name'].casefold()]
   if candidates:helper=min(candidates,key=lambda m:(0 if 'uncensored' in m['name'].casefold() else 1,m.get('size_bytes') or float('inf')))['name']
  if not helper:return {'intent':'explain','text':'Native tools need a compact language-planning step for this request. Install or explicitly select a helper model to continue.'},False
  settings={**body,'bridge_model':helper}
  if not use_selected and not explicit:settings.update(compact_bridge=True,minimal_helper=True)
  self.s['calls']+=1
  try:result=self.r.interpret(request,settings)
  except Exception as exc:
   if isinstance(exc,OSError) or re.search(r'cancel|deadline|closing|while queued',str(exc),re.I):raise
   self.s['consecutive_failures']+=1;self.s['failure_records']=(self.s['failure_records']+[{'model':helper,'error':str(exc)[:180],'time':time.time()}])[-8:];raise
  self.s['consecutive_failures']=0
  if result['intent']=='plan':
   try:self.r.workbench.executive.parse(result['text'])
   except ValueError as exc:result={'intent':'explain','text':'The proposed work plan needs correction before it can run: '+str(exc)}
  return result,True
 def view(self):return {**{k:v for k,v in self.s.items() if k!='procedures'},'procedures':list(self.s['procedures'].values())[-8:],'helper_preference':'Shared helper route and exact selected model; explicit per-request selection takes precedence; no implicit Llama fallback in Qwen-only mode','policy':'Native first; compact model proposal only on work gaps; reviewed reuse; actual verification before retention'}
