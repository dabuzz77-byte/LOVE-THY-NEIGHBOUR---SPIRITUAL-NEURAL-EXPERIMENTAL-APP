"""Bounded deterministic work loop: predict, perform, independently check."""
from collections import Counter
from fractions import Fraction
from .action_definitions import ActionDefinitions
from .branch_reasoning import equivalent
class NativeReasoning:
 def __init__(self,definitions):self.definitions=definitions
 def run(self,action,value):
  if action not in ('native/calculate','native/sort','native/unique','generation/reverse','generation/rotate','generation/increment','generation/decrement'):raise ValueError('Choose a supported internal operation')
  if len(str(value))>8000:raise ValueError('Input exceeds this bounded operation limit')
  prediction=self.definitions.predict(action,value)
  if not prediction.get('predictable'):raise ValueError(prediction.get('predicted_error','Unsupported input type'))
  if action=='native/sort':
   actual=sorted(value.splitlines());verified=Counter(actual)==Counter(value.splitlines()) and all(a<=b for a,b in zip(actual,actual[1:]))
  elif action=='native/unique':
   actual=list(dict.fromkeys(value.splitlines()));verified=len(actual)==len(set(actual)) and set(actual)==set(value.splitlines()) and actual==sorted(set(value.splitlines()),key=value.splitlines().index)
  elif action=='generation/reverse':actual=value[::-1];verified=actual[::-1]==value
  elif action=='generation/rotate':actual=value[1:]+value[:1];verified=(actual[-1:]+actual[:-1] if actual else '')==value
  elif action=='generation/increment':actual=value+1;verified=actual-value==1
  elif action=='generation/decrement':actual=value-1;verified=value-actual==1
  else:
   from .branch_reasoning import arithmetic
   actual=arithmetic(value);verified=equivalent(prediction['expected'],actual)
  row=self.definitions.record(action,value,actual,verified=verified,stage='native-reasoning')
  return {'action':action,'result':actual,'verified':verified,'prediction_matches':row['prediction_matches'],'record':row['sequence'],'check':'Independent invariants for transforms; arithmetic uses the existing bounded evaluator and is not an independent second solver.','model_calls':0}
