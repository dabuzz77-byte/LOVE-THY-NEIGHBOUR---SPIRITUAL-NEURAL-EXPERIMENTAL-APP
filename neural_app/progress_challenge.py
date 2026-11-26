"""Cross-area finite acceptance checks for the current improvement pass."""
import json,math,time

def challenge(seed=0):
 from .exact_numbers import calculate
 from .decision_workspace import compare_workflows,compare_scenarios
 from .memory_revisions import update,respond
 from .symbolic_reasoning import smallest_facts
 from .empirical_learning import fit,predict
 from .reasoning_engine import ReasoningEngine,pipeline
 from .dialogue_work import resolve
 rows=[]
 def check(domain,name,fn):
  t=time.perf_counter()
  try:ok=fn() is True;error=None
  except Exception as exc:ok=False;error=str(exc)[:200]
  rows.append({'domain':domain,'name':name,'passed':ok,'error':error,'elapsed_ms':round((time.perf_counter()-t)*1000,3)})
 check('numeric-integrity','decimal tokens retained exactly',lambda:calculate('0.1+0.2')['exact_result']=='3/10')
 check('numeric-integrity','large integer cancellation exact',lambda:calculate('100000000000000000001-100000000000000000000')['exact_result']=='1')
 def oversized():
  try:calculate('1e999999999');return False
  except ValueError:return True
 check('numeric-integrity','unbounded decimal exponent rejected before allocation',oversized)
 def restoration():
  s={};update(s,'colour','blue');update(s,'colour','green');out=respond('restore my colour revision 1',s)
  return out['restored_revision']==1 and s['memories']['colour']['value']=='blue' and s['memory_revisions']['colour'][-1]['value']=='green'
 check('memory-continuity','restore retains replaced memory',restoration)
 def branches():
  data=[4,2,7];out=compare_workflows({'input':data,'alternatives':[{'name':'ascending','steps':[{'op':'sort'}]},{'name':'total','steps':[{'op':'sum'}]},{'name':'bad','steps':[{'op':'upper'}]}]})
  return out['verified_count']==2 and out['failed_count']==1 and data==[4,2,7] and out['alternatives'][0]['result']==[2,4,7] and out['alternatives'][1]['result']==13
 check('planning','alternative branch isolation and visible failure',branches)
 def cubic():
  xs=list(range(25));ys=[(seed%4+1)*x**3-2*x*x+3 for x in xs];m=fit({'family':'auto','x':xs,'y':ys});return m['family']=='cubic' and math.isclose(predict(m,26)['result'],(seed%4+1)*26**3-2*26*26+3,rel_tol=1e-8)
 check('learning-transfer','cubic transfer selected on separate observations',cubic)
 def exact_premises():
  out=smallest_facts({'facts':['a','b','c'],'rules':[{'if':['a'],'then':'q'},{'if':['b','c'],'then':'q'}],'query':'q'})
  return out['minimum_cardinality']==1 and out['sufficient_facts']==['a']
 check('logical-auditing','smallest premise set beats greedy deletion',exact_premises)
 def scenarios():
  out=compare_scenarios({'model':{'values':{'x':2},'equations':{'benefit':{'weights':{'x':3}},'cost':{'weights':{'x':1}}}},'criteria':{'benefit':1,'cost':-1},'scenarios':[{'name':'hold','intervention':{}},{'name':'raise','intervention':{'x':4}}]})
  return out['selected_under_supplied_weights']==['raise'] and out['scenarios'][1]['score']==4
 check('causal-reasoning','conditional scenario ranking exposes weighted consequences',scenarios)
 def undo():
  engine=ReasoningEngine({});out=pipeline('b\na',[{'op':'lines'},{'op':'sort'},{'op':'join'}]);history=[{'request':'work','answer':json.dumps(out)}]
  result=resolve('undo last data step',history,engine);history.append({'request':'undo','answer':json.dumps(result)});second=resolve('undo last data step',history,engine)
  return result['result']==['a','b'] and second['result']==['b','a'] and second['data_step_undone']=='sort'
 check('conversation','successive pure-step undo restores original ordering',undo)
 def evidence():
  from .model_evidence import audit
  model=fit({'x':list(range(12)),'y':[3*x+2 for x in range(12)]});good=audit(model);model['holdout_RMSE']=99;bad=audit(model)
  return good['verified'] and not bad['verified'] and bad['status']=='inconsistent'
 check('self-assessment','inconsistent reported model error detected',evidence)
 return rows
