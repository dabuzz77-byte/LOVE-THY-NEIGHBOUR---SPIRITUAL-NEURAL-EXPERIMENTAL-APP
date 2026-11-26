"""Executable action contracts, counterfactual predictions and observed evidence."""
import collections,copy,json,math,time
from .branch_reasoning import arithmetic,equivalent
DEFINITIONS={
 'generation/preserve':('Retain the selected value','Any captured JSON value','Output equals input'),
 'generation/encode-json':('Encode a value as JSON text','JSON-serialisable value','Parsing the output reconstructs the input'),
 'generation/increment':('Increase an integer by one','Integer input','Output minus input is one'),
 'generation/decrement':('Decrease an integer by one','Integer input','Input minus output is one'),
 'generation/reverse':('Reverse character order','Text input','Reversing output reconstructs input'),
 'generation/rotate':('Move the first character to the end','Text input','Length and characters preserved'),
 'native/calculate':('Evaluate bounded arithmetic','Supported arithmetic expression','Independent rational evaluator agrees'),
 'native/sort':('Sort lines lexically','Text lines','Same line multiset in sorted order'),
 'native/unique':('Keep first occurrence of each line','Text lines','Ordered distinct lines'),
 'native/analyze':('Calculate descriptive pattern metrics','Captured text','Metrics refer to the captured input'),
 'native/read':('Read a workspace file','Available permitted file','Returned content hash matches file'),
 'native/check':('Check supported source syntax','Supported parser/compiler and file','Reported parser/compiler success'),
 'native/search':('Retrieve indexed memory matches','Indexed source records','Returned records retain provenance'),
 'native/research':('Retrieve source-labelled evidence','Available source index','Returned structure checked; claims need separate evaluation'),
 'native/project':('Inspect workspace inventory','Available workspace','Inventory returned from inspection'),
 'native/diagnose':('Read supported diagnostics','Available system measurements','Actual diagnostic result returned'),
 'bus/publish':('Deliver an event to registered observers','Valid authenticated bus packet','Observer receipts; actions require separate result checks'),
 'learning/world-action':('Apply an action in the local learning world','Current world state and action','Compare predicted and observed next state')}
from .decision_framework import assess
class ActionDefinitions:
 def __init__(self,saved=None):
  self.stats=copy.deepcopy((saved or {}).get('stats',{}));self.stage_stats=copy.deepcopy((saved or {}).get('stage_stats',{}));self.history=collections.deque(maxlen=128);self.sequence=0;self.ledger=None
 def predict(self,action,value):
  result={'action':action,'definition':DEFINITIONS.get(action),'predictable':False,'expected':None,'scope':'Software action contract; downstream usefulness needs goal-result evidence'}
  try:
   op=action.split('/')[-1]
   if action=='native/calculate':expected=arithmetic(value)
   elif action=='native/sort':expected=sorted(value.splitlines())
   elif action=='native/unique':expected=list(dict.fromkeys(value.splitlines()))
   elif action=='generation/preserve':expected=copy.deepcopy(value)
   elif action=='generation/encode-json':expected=json.dumps(value,ensure_ascii=True)
   elif action=='generation/increment' and type(value) is int:expected=value+1
   elif action=='generation/decrement' and type(value) is int:expected=value-1
   elif action=='generation/reverse' and isinstance(value,str):expected=''.join(reversed(value))
   elif action=='generation/rotate' and isinstance(value,str):expected=value[1:]+value[:1]
   else:return result
   result.update(predictable=True,expected=expected,decision_assessment=assess(action,expected))
  except (ValueError,TypeError,ZeroDivisionError,SyntaxError,OverflowError) as exc:result['predicted_error']=type(exc).__name__+': '+str(exc)[:160]
  return result
 def record(self,action,value,actual,verified=None,goal=None,stage=None):
  prediction=self.predict(action,value);matched=equivalent(prediction['expected'],actual) if prediction['predictable'] else None
  state=self.stats.setdefault(action,{'observed':0,'predicted':0,'matched':0,'verified_outcomes':0,'failed_outcomes':0});state['observed']+=1
  if matched is not None:state['predicted']+=1;state['matched']+=int(matched)
  if verified is not None:state['verified_outcomes']+=int(verified is True);state['failed_outcomes']+=int(verified is not True)
  if stage:
   key=stage+'/'+action;local=self.stage_stats.setdefault(key,{'observed':0,'predicted':0,'matched':0});local['observed']+=1
   if matched is not None:local['predicted']+=1;local['matched']+=int(matched)
  self.sequence+=1;row={'sequence':self.sequence,'stage':stage,'action':action,'goal':goal,'prediction':prediction,'actual_preview':str(actual)[:1000],'prediction_matches':matched,'operation_verified':verified,'decision_assessment':assess(action,prediction.get('expected'),verified),'time':time.time(),'evidence_type':'observed software execution; not proof of external physical causality'};self.history.append(row)
  if self.ledger:self.ledger.record(row)
  return row
 def alternatives(self,value):
  rows=[]
  for action in DEFINITIONS:
   if not action.startswith('generation/'):continue
   prediction=self.predict(action,value)
   if prediction['predictable']:rows.append(prediction)
  return rows
 def checkpoint(self):return {'stats':copy.deepcopy(self.stats),'stage_stats':copy.deepcopy(self.stage_stats)}
 def view(self):return {'definitions':[{'action':k,'effect':v[0],'conditions':v[1],'completion_check':v[2]} for k,v in DEFINITIONS.items()],'statistics':copy.deepcopy(self.stats),'stage_statistics':copy.deepcopy(self.stage_stats),'recent':list(self.history)[-20:],'sequence':self.sequence,'scope':'Definitions cover registered actions; unknown actions remain unresolved. Exact predicted transformations and task outcomes are recorded separately.'}
