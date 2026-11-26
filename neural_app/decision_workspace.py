"""Checked alternatives and model-based scenario comparison. No external actions."""
import copy,math

def compare_workflows(body):
 from .reasoning_engine import pipeline
 choices=body.get('alternatives')
 if not isinstance(choices,list) or not 1<=len(choices)<=16:raise ValueError('Provide 1 to 16 alternative workflows')
 rows=[]
 for i,choice in enumerate(choices):
  if not isinstance(choice,dict):raise ValueError('Each alternative must be an object')
  row={'name':str(choice.get('name',i+1))[:100]}
  try:
   result=pipeline(copy.deepcopy(body.get('input')),choice.get('steps'));row.update(status='verified',**result)
  except (ValueError,TypeError,KeyError,IndexError,OverflowError) as exc:row.update(status='failed',error=str(exc)[:250],verified=False)
  rows.append(row)
 return {'alternatives':rows,'verified_count':sum(r['verified'] for r in rows),'failed_count':sum(not r['verified'] for r in rows),'scope':'Each branch uses the same copied input and independently checked pure operations; no host or network actions','model_calls':0}

def compare_scenarios(body):
 from .reasoning_engine import causal,finite
 scenarios=body.get('scenarios');criteria=body.get('criteria');model=body.get('model')
 if not isinstance(model,dict) or not isinstance(scenarios,list) or not 1<=len(scenarios)<=16 or not isinstance(criteria,dict) or not 1<=len(criteria)<=16:raise ValueError('Supply a model, 1 to 16 scenarios, and 1 to 16 numeric outcome weights')
 baseline=causal(model)['baseline']
 if not set(criteria)<=set(baseline):raise ValueError('Each criterion must name a model node')
 weights={k:finite(v) for k,v in criteria.items()};rows=[]
 for i,scenario in enumerate(scenarios):
  if not isinstance(scenario,dict):raise ValueError('Each scenario must be an object')
  result=causal({**model,'intervention':scenario.get('intervention',{})});contributions={k:finite(weights[k]*result['difference'][k]) for k in weights};score=finite(math.fsum(contributions.values()))
  rows.append({'name':str(scenario.get('name',i+1))[:100],'intervention':scenario.get('intervention',{}),'outcomes':result['intervened'],'changes':result['difference'],'contributions':contributions,'score':score})
 best=max(r['score'] for r in rows)
 return {'baseline':baseline,'scenarios':rows,'selected_under_supplied_weights':[r['name'] for r in rows if math.isclose(r['score'],best,rel_tol=1e-12,abs_tol=1e-12)],'criteria':weights,'assumptions':model.get('assumptions',[]),'scope':'Conditional comparison under supplied equations and value weights. Selection is not automatic permission or proof of real-world benefit. No external action executed.','model_calls':0}
