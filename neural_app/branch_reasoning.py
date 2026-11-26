"""Isolated typed counterfactual state; previews never call host tools."""
import ast,copy,hashlib,json,math,time
from fractions import Fraction

def arithmetic(text):
 tree=ast.parse(text,mode='eval')
 if len(list(ast.walk(tree)))>64:raise ValueError('Expression too large')
 def visit(n):
  if isinstance(n,ast.Constant) and type(n.value) in (int,float) and abs(n.value)<1e12:return Fraction(str(n.value))
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):return visit(n.operand)*(1 if isinstance(n.op,ast.UAdd) else -1)
  if isinstance(n,ast.BinOp):
   a,b=visit(n.left),visit(n.right)
   if isinstance(n.op,ast.Add):v=a+b
   elif isinstance(n.op,ast.Sub):v=a-b
   elif isinstance(n.op,ast.Mult):v=a*b
   elif isinstance(n.op,ast.Div):v=a/b
   elif isinstance(n.op,ast.Mod):v=a%b
   else:raise ValueError('Unsupported arithmetic')
   if abs(v)>10**15:raise ValueError('Result too large')
   return v
  raise ValueError('Use bounded arithmetic')
 result=visit(tree.body);return int(result) if result.denominator==1 else float(result)

def equivalent(a,b):
 if type(a) in (int,float) and type(b) in (int,float):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
 return a==b

def simulate(steps,starting_state=None,name='original'):
 state=copy.deepcopy(starting_state or {'facts':{},'constraints':[]});predictions=[];previous=None;known=False;blocked=False
 started=time.perf_counter()
 for index,step in enumerate(steps):
  op=step['operation'];arg=step['input'];pred={'step':index,'operation':op,'input':arg,'status':'deferred','expected':None}
  if blocked:pred.update(status='blocked',reason='Prior simulated failure');predictions.append(pred);continue
  if '{{previous}}' in arg:
   if not known:pred['reason']='Dependency has no simulated result';predictions.append(pred);continue
   arg=arg.replace('{{previous}}',previous if isinstance(previous,str) else json.dumps(previous))
  pred['resolved_input']=arg
  if blocked:pred.update(status='blocked',reason='Prior simulated failure');predictions.append(pred);continue
  try:
   if op=='calculate':value=arithmetic(arg)
   elif op=='reverse':value=arg[::-1]
   elif op=='upper':value=arg.upper()
   elif op=='lower':value=arg.lower()
   elif op=='statistics':
    from .data_skills import numeric_stats
    value=numeric_stats(arg)
   elif op=='sort':value=sorted(arg.splitlines())
   elif op=='unique':value=list(dict.fromkeys(arg.splitlines()))
   else:known=False;pred['reason']='Requires actual source or host observation';predictions.append(pred);continue
   previous=value;known=True;pred.update(status='predicted',expected=value);state['facts']['step:'+str(index)]=value
  except (ValueError,SyntaxError,TypeError,ZeroDivisionError,OverflowError) as exc:
   known=False;blocked=True;pred.update(status='predicted-failure',reason=type(exc).__name__+': '+str(exc)[:200])
  predictions.append(pred)
 known_count=sum(p['status']=='predicted' for p in predictions);failures=sum(p['status']=='predicted-failure' for p in predictions)
 return {'name':name,'starting_state':copy.deepcopy(starting_state or {'facts':{},'constraints':[]}), 'state':state,'predictions':predictions,'predicted_steps':known_count,'failures':failures,'deferred_steps':sum(p['status']=='deferred' for p in predictions),'score':known_count/max(1,len(steps))-2*failures,'preview_cost_ms':(time.perf_counter()-started)*1000,'status':'predicted-failure' if failures else 'preview-complete' if known_count==len(steps) else 'needs-observation','host_actions_executed':False}

def branches(steps,context=None):
 initial={'facts':{},'constraints':[s.get('completion_condition','') for s in steps],'context':copy.deepcopy(context or {})}
 original=simulate(steps,initial,'dependency-preserving')
 # A second isolated branch materialises predicted dependencies; it must agree with the first.
 materialized=copy.deepcopy(steps)
 for step,pred in zip(materialized,original['predictions']):
  if pred.get('status')=='predicted':step['input']=pred['resolved_input']
 second=simulate(materialized,initial,'materialized-dependencies')
 agreement=all(a['status']==b['status'] and (a['status']!='predicted' or equivalent(a['expected'],b['expected'])) for a,b in zip(original['predictions'],second['predictions']))
 return {'branches':[original,second],'selected':original['name'],'selection_reason':'Preserve explicit user dependencies; compare isolated dependency representations before execution','representation_agreement':agreement,'comparison_kind':'equivalent-plan representations, not proof of an optimal real-world plan','actual_checks':[],'converged':False}

def compare_plans(plans,context=None):
 rows=[simulate(steps,context,'alternative-'+str(i+1)) for i,steps in enumerate(plans)]
 selected=max(rows,key=lambda r:(r['score'],-len(r['predictions'])))
 return {'branches':rows,'suggested':selected['name'],'criterion':'Predictable completed steps minus predicted failures; shorter plan breaks ties','scope':'Sandbox comparison only; alternatives may serve different goals and are not executed automatically'}

def check_actual(model,index,value,verified):
 pred=model['branches'][0]['predictions'][index]
 matched=equivalent(pred['expected'],value) if pred['status']=='predicted' else None
 row={'step':index,'prediction_status':pred['status'],'prediction_matches':matched,'operation_verified':verified,'time':time.time()}
 model['actual_checks'].append(row)
 model['converged']=len(model['actual_checks'])==len(model['branches'][0]['predictions']) and all(r['operation_verified'] and r['prediction_matches'] is not False for r in model['actual_checks'])
 return row
