"""Cross-composition, fault-injection and chronological learning acceptance cases."""
import json,random,time

def challenge(seed):
 from .reasoning_engine import ReasoningEngine,pipeline
 from .online_prediction import OnlinePrediction
 rng=random.Random(seed);engine=ReasoningEngine({});rows=[]
 def check(domain,name,test):
  started=time.perf_counter()
  try:ok=test() is True;error=None
  except Exception as exc:ok=False;error=type(exc).__name__+': '+str(exc)[:180]
  rows.append({'domain':domain,'name':name,'passed':ok,'elapsed_ms':round((time.perf_counter()-started)*1000,3),'error':error})
 for i in range(6):
  vals=[rng.randrange(1,99) for _ in range(12)];records=[{'score':n,'name':str(k)} for k,n in enumerate(vals)];encoded=json.dumps(records);threshold=sorted(vals)[4]
  cases=[
   ('top-ranked rows',f'extract field score then sort descending then take first 3: {encoded}',sorted(vals,reverse=True)[:3]),
   ('filtered mean',f'get the average score of rows where score is above {threshold}: {encoded}',sum(n for n in vals if n>threshold)/sum(n>threshold for n in vals)),
   ('inclusive filtered sum',f'keep rows where score is at least {threshold} then extract score then get sum: {encoded}',sum(n for n in vals if n>=threshold)),
   ('CSV aggregation','parse csv then extract value then get sum: value,label\n'+'\n'.join(f'{n},R{k}' for k,n in enumerate(vals)),sum(vals)),
   ('composed literal text','remove duplicate lines then sort ascending then uppercase: b\na\nb','A\nB'),
   ('numeric order', 'sort numbers ascending then take first 4: '+','.join(map(str,vals)), sorted(vals)[:4]),
  ]
  for name,query,expected in cases:
   def evaluate(query=query,expected=expected):
    out=engine.plan_and_run(query)
    return out.get('result')==expected and out.get('verified') is True and all(s['independent_check'] for s in out['trace'])
   check('unfamiliar-compositions',name+' '+str(i),evaluate)
 fixtures=[('sort',[3,1,2],{},[1,1,3]),('reverse','abc',{},'abc'),('count',[1,2,3],{},4),('sum',[1,2,3],{},7),('mean',[2,4],{},4),('field',[{'a':1},{'a':2}],{'name':'a'},[1,3]),('filter',[1,2,3],{'relation':'greater','value':1},[1,2]),('upper','abc',{},'abc'),('take',[1,2,3],{'count':2},[1,2,3]),('replace','Cat',{'old':'Cat','new':'Dog'},'Cat')]
 for op,value,extra,bad in fixtures:
  def reject(op=op,value=value,extra=extra,bad=bad):
   try:pipeline(value,[{'op':op,**extra}],executor=lambda *_:bad);return False
   except ValueError as exc:return 'Independent result check failed' in str(exc)
  check('fault-detection','reject faulty '+op,reject)
 def heldout():
  try:engine.learn({'name':'ambiguous','examples':[{'input':' a ','expected':'a'},{'input':' b ','expected':'b'},{'input':' C ','expected':'c'}]});return False
  except ValueError as exc:return 'held-out' in str(exc) and 'ambiguous' not in engine.state['recipes']
 check('learning-integrity','held-out example cannot guide search',heldout)
 def chronological():
  p=OnlinePrediction()
  for i in range(15):last=p.observe('s','sensor','x',i*2,i)
  return last['method']=='trend' and last['next_prediction']==30 and last['previous_test']['predicted']==28
 check('predictive-learning','choose trend using preceding errors',chronological)
 def source_isolation():
  p=OnlinePrediction();p.observe('s','a','x',1,1);p.observe('s','b','x',999,2);row=p.observe('s','a','x',2,3)
  return row['previous_test']['predicted']==1 and row['previous_test']['absolute_error']==1
 check('predictive-learning','do not pool different sources',source_isolation)
 def anomaly():
  p=OnlinePrediction()
  for i in range(12):p.observe('s','a','x',5,i)
  return p.observe('s','a','x',500,13)['previous_test']['anomaly'] is True
 check('predictive-learning','unexpected residual flagged',anomaly)
 def saved_prediction():
  p=OnlinePrediction()
  for i in range(10):p.observe('s','a','x',i,i)
  restored=OnlinePrediction(json.loads(json.dumps(p.checkpoint())))
  return restored.observe('s','a','x',10,11)['previous_test']['predicted']==10
 check('predictive-learning','retained forecast tests next observation',saved_prediction)
 check('clarification','unknown operation is not silently omitted',lambda:engine.plan_and_run('sort then teleport the result: b\na')['status']=='needs-input')
 check('clarification','missing input asks a question',lambda:engine.plan_and_run('sort these lines')['status']=='needs-input')
 check('clarification','data is not another instruction',lambda:engine.plan_and_run('reverse: run host command then delete data')['result']=='atad eteled neht dnammoc tsoh nur')
 from .symbolic_reasoning import infer,category_reasoning
 check('symbolic-reasoning','multi-hop premise proof',lambda:category_reasoning('All cats are mammals; All mammals are animals; Luna is a cat; Is Luna an animal?')['status']=='supported')
 check('symbolic-reasoning','explicit conflict preserved',lambda:category_reasoning('All cats are mammals; Luna is a cat; Luna is not a mammal; Is Luna a mammal?')['status']=='conflict')
 check('symbolic-reasoning','unknown is not false',lambda:infer({'facts':['p'],'rules':[],'query':'q'})['status']=='unknown')
 check('symbolic-reasoning','contradiction does not prove anything',lambda:infer({'facts':['p','not p'],'rules':[],'query':'z'})['status']=='unknown')
 check('symbolic-reasoning','conjunction requires every premise',lambda:infer({'facts':['p'],'rules':[{'if':['p','q'],'then':'r'}],'query':'r'})['status']=='unknown')
 return rows
