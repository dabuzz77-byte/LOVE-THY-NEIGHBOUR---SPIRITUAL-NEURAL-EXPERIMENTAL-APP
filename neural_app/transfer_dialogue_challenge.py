"""Finite checks for parameter transfer, reversible conversation and robust choices."""
import json,math,time

def challenge(seed=0):
 from .reasoning_engine import ReasoningEngine,pipeline
 from .dialogue_work import resolve
 from .robust_scenarios import compare
 from .decision_workspace import compare_workflows
 rows=[]
 def check(domain,name,fn):
  t=time.perf_counter()
  try:passed=fn() is True;error=None
  except Exception as exc:passed=False;error=str(exc)[:200]
  rows.append({'domain':domain,'name':name,'passed':passed,'error':error,'elapsed_ms':round((time.perf_counter()-t)*1000,3)})
 def numeric_transfer():
  e=ReasoningEngine({});a=seed%5+2;b=seed%7+1;e.learn({'name':'affine','examples':[{'input':x,'expected':a*x+b} for x in (1,3,5,11)]})
  return e.handle('use workflow: '+json.dumps({'name':'affine','input':17}))['result']==a*17+b
 check('learning-transfer','numeric parameters inferred from training only',numeric_transfer)
 def record_transfer():
  e=ReasoningEngine({});e.learn({'name':'scores','examples':[{'input':[{'score':a},{'score':b}],'expected':[b,a]} for a,b in [(1,3),(2,5),(4,8)]]})
  return e.handle('use workflow: '+json.dumps({'name':'scores','input':[{'score':2},{'score':7}]}))['result']==[7,2]
 check('learning-transfer','field extraction and descending order transfer',record_transfer)
 def bad_holdout():
  e=ReasoningEngine({})
  try:e.learn({'name':'bad','examples':[{'input':1,'expected':4},{'input':2,'expected':7},{'input':3,'expected':999}]});return False
  except ValueError:return 'bad' not in e.state['recipes']
 check('self-assessment','heldout numeric mismatch rejects recipe',bad_holdout)
 def duplicate_holdout():
  e=ReasoningEngine({})
  try:e.learn({'name':'duplicate','examples':[{'input':x,'expected':x*3+1} for x in (1,2,3,1.0)]});return False
  except ValueError:return 'duplicate' not in e.state['recipes']
 check('self-assessment','duplicate training input cannot stand in for heldout input',duplicate_holdout)
 def revision():
  e=ReasoningEngine({});out=pipeline('b\na',[{'op':'lines'},{'op':'sort'}]);h=[{'request':'work','answer':json.dumps(out)}];revised=resolve('change last step to sort descending',h,e)
  return revised['result']==['b','a'] and revised['trace'][-1]['parameters']['descending'] and revised['input']=='b\na'
 check('dialogue-continuity','replace final transformation on original input',revision)
 def numeric_revision():
  e=ReasoningEngine({});out=pipeline(17,[{'op':'scale','value':3},{'op':'add','value':2}]);h=[{'request':'work','answer':json.dumps(out)}]
  revised=resolve('change last step to add 4',h,e);return revised['result']==55 and revised['input']==17 and len(revised['trace'])==2
 check('dialogue-continuity','numeric final-step replacement uses checked arithmetic',numeric_revision)
 def choose():
  e=ReasoningEngine({});out=compare_workflows({'input':[3,1,2],'alternatives':[{'name':'total','steps':[{'op':'sum'}]},{'name':'ordered','steps':[{'op':'sort'}]}]});h=[{'request':'compare','answer':json.dumps(out)}];chosen=resolve('use alternative ordered',h,e);h.append({'request':'select','answer':json.dumps(chosen)})
  return chosen['result']==[1,2,3] and resolve('now get mean',h,e)['result']==2
 check('dialogue-continuity','select checked branch then continue',choose)
 def uncertainty():
  out=compare({'model':{'values':{'x':0},'equations':{'y':{'weights':{'x':1}}}},'ranges':{'x':[-2,2]},'criteria':{'y':1},'scenarios':[{'name':'hold','intervention':{}},{'name':'zero','intervention':{'x':0}}]})
  return out['corners_examined']==2 and out['scenario_ranges'][1]['minimum_score']==-2 and out['scenario_ranges'][1]['maximum_score']==2 and not out['robust_winning_indices'] and out['maximin_selected_indices']==[0]
 check('causal-reasoning','ranking change across uncertainty remains visible',uncertainty)
 def changes():
  e=ReasoningEngine({});out=pipeline([1,1,2],[{'op':'unique'}]);h=[{'request':'deduplicate','answer':json.dumps(out)}];result=resolve('what changed?',h,e)
  return result['change_summary']['size_difference']==-1 and result['result']==[1,2] and result['action_repeated'] is False
 check('dialogue-continuity','retained input/output change summary',changes)
 def exact_continuation():
  from .exact_numbers import calculate
  h=[{'request':'exact calculate 0.1+0.2','answer':json.dumps(calculate('0.1+0.2'))}]
  return resolve('now multiply by 3',h,ReasoningEngine({}))['exact_result']=='9/10'
 check('dialogue-continuity','exact decimal follow-up retains rational value',exact_continuation)
 return rows
