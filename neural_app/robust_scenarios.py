"""Exact corner comparisons for bounded affine root uncertainty."""
import copy,itertools,math

def compare(body):
 from .decision_workspace import compare_scenarios
 from .reasoning_engine import finite
 model=body.get('model');ranges=body.get('ranges')
 if not isinstance(model,dict) or not isinstance(ranges,dict) or not 1<=len(ranges)<=6:raise ValueError('Provide a model and 1 to 6 root uncertainty ranges')
 roots=model.get('values',{});names=sorted(ranges);bounds=[]
 for name in names:
  pair=ranges[name]
  if name not in roots or not isinstance(pair,list) or len(pair)!=2:raise ValueError('Each range must name an existing root and contain two bounds')
  low,high=map(finite,pair)
  if low>high:raise ValueError('Range bounds must be ordered')
  bounds.append([low] if low==high else [low,high])
 point=compare_scenarios(body);records=[{'name':row['name'],'minimum_score':math.inf,'maximum_score':-math.inf,'wins_at_corners':0} for row in point['scenarios']];cases=[];all_winners=None
 for corner in itertools.product(*bounds):
  values={**roots,**dict(zip(names,corner))};out=compare_scenarios({**body,'model':{**model,'values':values}});scores=[r['score'] for r in out['scenarios']];best=max(scores);winners={i for i,score in enumerate(scores) if math.isclose(score,best,rel_tol=1e-12,abs_tol=1e-12)}
  all_winners=winners if all_winners is None else all_winners&winners
  for i,score in enumerate(scores):
   records[i]['minimum_score']=min(records[i]['minimum_score'],score);records[i]['maximum_score']=max(records[i]['maximum_score'],score);records[i]['wins_at_corners']+=int(i in winners)
  cases.append({'root_values':dict(zip(names,corner)),'scores':scores,'winning_indices':sorted(winners)})
 worst_best=max(r['minimum_score'] for r in records)
 return {'point_comparison':point,'scenario_ranges':records,'corners_examined':len(cases),'corner_results':cases,'robust_winning_indices':sorted(all_winners or set()),'maximin_selected_indices':[i for i,r in enumerate(records) if math.isclose(r['minimum_score'],worst_best,rel_tol=1e-12,abs_tol=1e-12)],'ranges':copy.deepcopy(ranges),'scope':'For the supplied affine model and fixed weights, root-box corners bound score changes. Corner wins are not probabilities. Robust and maximin rankings are conditional, not authorization or executed interventions.','model_calls':0}
