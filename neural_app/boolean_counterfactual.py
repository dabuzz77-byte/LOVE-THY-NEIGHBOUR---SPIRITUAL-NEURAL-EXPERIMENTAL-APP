"""Counterfactual consequences of caller-supplied Boolean structural equations."""
import copy,re
from .general_reasoning import formula,truth

def prepare(values,equations,outcome):
 if not isinstance(values,dict) or not isinstance(equations,dict) or not 1<=len(values)<=16 or not 1<=len(equations)<=16 or len(values)+len(equations)>24 or set(values)&set(equations):raise ValueError('Use disjoint observed inputs and Boolean equations, with at most 24 variables')
 names=set(values)|set(equations)
 if any(not isinstance(n,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}',n) for n in names) or any(type(v)is not bool for v in values.values()) or not isinstance(outcome,str) or outcome not in names:raise ValueError('Use lowercase variable identifiers, Boolean input values and a known outcome')
 compiled={};dependencies={};counter=[0]
 for name,expression in equations.items():
  atoms=set();compiled[name]=formula(expression,atoms,counter)
  if not atoms<=names:raise ValueError('A causal equation refers to unknown inputs: '+', '.join(sorted(atoms-names)))
  dependencies[name]=atoms&set(equations)
 remaining=set(equations);order=[]
 while remaining:
  ready=sorted(n for n in remaining if not dependencies[n]&remaining)
  if not ready:raise ValueError('The original causal model contains a cycle')
  order+=ready;remaining.difference_update(ready)
 def evaluate(changes,inputs=None):
  world={**values,**(inputs or {}),**changes}
  for name in order:
   if name not in changes:world[name]=truth(compiled[name],world)
  return world
 return {'names':names,'order':order,'evaluate':evaluate}

def solve(body):
 values=body.get('values');equations=body.get('equations');outcome=body.get('outcome');interventions=body.get('interventions',[])
 model=prepare(values,equations,outcome);names=model['names'];order=model['order'];evaluate=model['evaluate'];baseline=evaluate({})
 if not isinstance(interventions,list) or len(interventions)>32:raise ValueError('Use up to 32 explicit interventions')
 seen=set();rows=[]
 for change in interventions:
  if not isinstance(change,dict):raise ValueError('Each intervention needs a name and set values')
  name=change.get('name');setting=change.get('set')
  if not isinstance(name,str) or not name.strip() or len(name)>120 or name in seen or not isinstance(setting,dict) or not setting or not set(setting)<=names or any(type(v)is not bool for v in setting.values()):raise ValueError('Use distinct intervention names and explicit Boolean settings for known variables')
  seen.add(name);after=evaluate(setting);rows.append({'name':name,'set':copy.deepcopy(setting),'world':after,'outcome':after[outcome],'outcome_changed':after[outcome]!=baseline[outcome],'changed_variables':[n for n in sorted(names) if after[n]!=baseline[n]]})
 checks=[]
 for name in sorted(values):
  after=evaluate({name:not values[name]});checks.append({'input':name,'actual':values[name],'counterfactual':not values[name],'outcome':after[outcome],'outcome_changed':after[outcome]!=baseline[outcome]})
 answer={}
 if type(body.get('question_expected_value'))is bool and len(rows)==1:answer={'question':body.get('question'),'answer_to_question':rows[0]['outcome']==body['question_expected_value']}
 return {**answer,'status':'model-evaluated','complete':True,'baseline':baseline,'outcome_variable':outcome,'baseline_outcome':baseline[outcome],'interventions':rows,'single_input_checks':checks,'evaluation_order':order,'source_clauses':body.get('source_clauses',[]),'next_step':'Check whether the equations, background conditions and intervention assumptions describe the actual situation; distinguish modeled dependence from human judgments of blame or intent.','scope':'Deterministic counterfactual calculation in an explicitly supplied acyclic Boolean structural model. No causal graph, medical conclusion, moral blame or typical-human judgment is inferred from narrative alone.'}
