"""Bounded integer constraint reasoning and optimisation, without model calls."""
import math,time

RELATIONS={'equal','less_or_equal','greater_or_equal'}
def solve(body):
 if not isinstance(body,dict):raise ValueError('Provide domains, constraints and optional objective')
 domains=body.get('domains');constraints=body.get('constraints',[]);objective=body.get('objective')
 if not isinstance(domains,dict) or not 1<=len(domains)<=16 or not isinstance(constraints,list) or len(constraints)>64:raise ValueError('Use 1 to 16 variables and up to 64 constraints')
 for name,values in domains.items():
  if not isinstance(name,str) or not name.isidentifier() or len(name)>60 or not isinstance(values,list) or not 1<=len(values)<=32 or any(type(v)is not int or abs(v)>10**9 for v in values):raise ValueError('Each variable needs 1 to 32 bounded integer domain values')
 domains={k:sorted(set(v)) for k,v in domains.items()}
 def linear(row):
  terms=row.get('terms')
  if not isinstance(terms,dict) or not terms or any(k not in domains or type(v)is not int or abs(v)>10**9 for k,v in terms.items()):raise ValueError('Use integer linear coefficients on declared variables')
  return terms
 for row in constraints:
  if not isinstance(row,dict):raise ValueError('Each constraint must be an object')
  if row.get('kind')=='all_different':
   names=row.get('variables')
   if not isinstance(names,list) or not names or len(set(names))!=len(names) or any(n not in domains for n in names):raise ValueError('all_different needs distinct declared variable names')
  elif row.get('relation') in RELATIONS and type(row.get('value'))is int and abs(row['value'])<=10**18:linear(row)
  else:raise ValueError('Use all_different or an integer linear relation')
 if objective is not None:
  if not isinstance(objective,dict) or objective.get('direction') not in ('minimise','maximise'):raise ValueError('Choose minimise or maximise for the objective')
  linear(objective)
 limit=body.get('node_limit',100000)
 if type(limit)is not int or not 1<=limit<=200000:raise ValueError('Node limit must be 1 to 200000')
 solution_limit=body.get('solution_limit',2 if body.get('check_uniqueness') is True else 1)
 if type(solution_limit)is not int or not 1<=solution_limit<=8:raise ValueError('Solution limit must be 1 to 8')
 if body.get('check_uniqueness') is True and solution_limit<2:raise ValueError('Uniqueness checking needs a solution limit of at least two')
 if objective is not None and (solution_limit!=1 or body.get('check_uniqueness') is True):raise ValueError('Alternative-solution checks apply to feasibility tasks; omit the objective')
 deadline=time.monotonic()+2;nodes=pruned=0;exhausted=True;best=None;best_score=None;solutions=[];solution_cap_reached=False;order=sorted(domains,key=lambda k:(len(domains[k]),k))
 def bounds(terms,assignment):
  low=high=0
  for name,coefficient in terms.items():
   if name in assignment:low+=coefficient*assignment[name];high+=coefficient*assignment[name]
   else:
    a=coefficient*domains[name][0];b=coefficient*domains[name][-1];low+=min(a,b);high+=max(a,b)
  return low,high
 def possible(assignment):
  for row in constraints:
   if row.get('kind')=='all_different':
    selected=[assignment[n] for n in row['variables'] if n in assignment]
    if len(selected)!=len(set(selected)):return False
   else:
    lo,hi=bounds(row['terms'],assignment);value=row['value'];rel=row['relation']
    if rel=='equal' and not lo<=value<=hi or rel=='less_or_equal' and lo>value or rel=='greater_or_equal' and hi<value:return False
  return True
 def visit(assignment,index):
  nonlocal nodes,pruned,exhausted,best,best_score,solution_cap_reached
  if nodes>=limit or time.monotonic()>deadline:exhausted=False;return
  nodes+=1
  if not possible(assignment):pruned+=1;return
  if objective and best is not None:
   lo,hi=bounds(objective['terms'],assignment)
   if objective['direction']=='minimise' and lo>=best_score or objective['direction']=='maximise' and hi<=best_score:pruned+=1;return
  if index==len(order):
   best=dict(assignment);best_score=sum(c*assignment[k] for k,c in objective['terms'].items()) if objective else None
   if objective is None:
    solutions.append(dict(assignment))
    if len(solutions)>=solution_limit:solution_cap_reached=True
   return
  name=order[index]
  for value in domains[name]:
   assignment[name]=value;visit(assignment,index+1)
   if not exhausted or solution_cap_reached:break
  assignment.pop(name,None)
 visit({},0)
 # Separate direct verification; interval-pruning receipts are not proof of feasibility.
 verified=best is not None and all(best[k] in domains[k] for k in domains)
 for candidate in solutions if objective is None else [best] if best is not None else []:
  verified=verified and all(candidate[k] in domains[k] for k in domains)
  for row in constraints:
   if row.get('kind')=='all_different':verified=verified and len({candidate[n] for n in row['variables']})==len(row['variables'])
   else:
    value=sum(c*candidate[n] for n,c in row['terms'].items());expected=row['value']
    verified=verified and (value==expected if row['relation']=='equal' else value<=expected if row['relation']=='less_or_equal' else value>=expected)
 if best is not None and not verified:raise ValueError('Independent solution verification failed')
 status='optimal' if best is not None and objective and exhausted else 'feasible' if best is not None else 'infeasible' if exhausted else 'incomplete'
 complete=exhausted and not solution_cap_reached
 uniqueness='not-requested' if objective is not None or solution_limit==1 else 'multiple' if len(solutions)>=2 else 'unique' if len(solutions)==1 and complete else 'no-solution' if best is None and complete else 'undetermined'
 return {'status':status,'assignment':best,'solutions':solutions if objective is None else [],'uniqueness':uniqueness,'solution_limit_reached':solution_cap_reached,'objective_value':best_score,'verified':verified,'optimality_proven':bool(objective and best is not None and exhausted),'infeasibility_proven':best is None and exhausted,'search_complete':complete,'nodes':nodes,'pruned':pruned,'model_calls':0,'scope':'Exact bounded integer-domain constraints supplied by the caller. Budget exhaustion is incomplete, not proof of infeasibility or uniqueness.'}
