"""Select a bounded numerical family before touching the final test set."""
import math
from .ambient_noisy_learning import fit

def estimate(model,x,z):
 if model['family']=='quadratic':return sum(a*b for a,b in zip(model['weights'],(1,x,z,x*x,x*z,z*z)))
 if model['family']=='affine':return sum(a*b for a,b in zip(model['weights'],(1,x,z)))
 return model['coefficient']*x**model['powers'][0]*z**model['powers'][1]

def _select(training,selection,testing,allow_quadratic=False):
 sets=[{tuple(r[:2]) for r in rows} for rows in (training,selection,testing)]
 if any(sets[i]&sets[j] for i,j in ((0,1),(0,2),(1,2))):return {'status':'overlapping-splits'}
 if len(training)<6 or min(len(selection),len(testing))<4:return {'status':'insufficient-observations'}
 if any(len(r)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 or v>1e10 for v in r) for rows in (training,selection,testing) for r in rows):return {'status':'invalid-observation'}
 candidates=[];power=fit(training,selection)
 if 'model' in power:candidates.append({'family':'power-product',**power['model']})
 features=[(1,x,z) for x,z,y in training]
 matrix=[[sum(f[i]*f[j] for f in features) for j in range(3)]+[sum(f[i]*r[2] for f,r in zip(features,training))] for i in range(3)]
 for i in range(3):
  pivot=max(range(i,3),key=lambda j:abs(matrix[j][i]));matrix[i],matrix[pivot]=matrix[pivot],matrix[i]
  if abs(matrix[i][i])<1e-10:break
  scale=matrix[i][i];matrix[i]=[v/scale for v in matrix[i]]
  for j in range(3):
   if i!=j:
    scale=matrix[j][i];matrix[j]=[a-scale*b for a,b in zip(matrix[j],matrix[i])]
 else:candidates.append({'family':'affine','weights':[matrix[i][3] for i in range(3)]})
 if allow_quadratic and len(training)>=12:
  features=[(1,x,z,x*x,x*z,z*z) for x,z,y in training];n=6
  matrix=[[sum(f[i]*f[j] for f in features) for j in range(n)]+[sum(f[i]*r[2] for f,r in zip(features,training))] for i in range(n)]
  for i in range(n):
   pivot=max(range(i,n),key=lambda j:abs(matrix[j][i]));matrix[i],matrix[pivot]=matrix[pivot],matrix[i]
   if abs(matrix[i][i])<1e-9:break
   scale=matrix[i][i];matrix[i]=[v/scale for v in matrix[i]]
   for j in range(n):
    if i!=j:
     scale=matrix[j][i];matrix[j]=[a-scale*b for a,b in zip(matrix[j],matrix[i])]
  else:candidates.append({'family':'quadratic','weights':[matrix[i][n] for i in range(n)]})
 def error(model,rows):return sum(abs(estimate(model,x,z)-y)/max(1e-12,abs(y)) for x,z,y in rows)/len(rows)
 if not candidates:return {'status':'unidentifiable'}
 scores=[{'family':m['family'],'selection_error':error(m,selection)} for m in candidates]
 model=min(candidates,key=lambda m:error(m,selection)+(0.002 if m['family']=='quadratic' else 0))
 # Suggest a discriminating observation without querying its answer.
 xs=[r[0] for r in training];zs=[r[1] for r in training]
 proposals=[(min(xs)*.9,min(zs)*.9),(max(xs)*1.2,min(zs)*.9),(min(xs)*.9,max(zs)*1.2),(max(xs)*1.2,max(zs)*1.2)]
 def disagreement(point):
  values=[estimate(m,*point) for m in candidates]
  return (max(values)-min(values))/max(1e-12,max(abs(v) for v in values))
 probe=max(proposals,key=disagreement)
 investigation={'inputs':probe,'predicted_disagreement':disagreement(probe),'observation_requested':True,'observation_received':False,'reason':'Compare candidate predictions; neither candidate is guaranteed correct'}
 if error(model,selection)>=.05:
  return {'status':'unresolved-model-family','selected_model':None,'best_unverified_candidate':model,'selection_scores':scores,'reserved_checks':[],'test_used_for_selection':False,'next_experiment':investigation}
 checks=[{'inputs':[x,z],'predicted':estimate(model,x,z),'observed':y,'relative_error':abs(estimate(model,x,z)-y)/abs(y)} for x,z,y in testing]
 passed=error(model,selection)<.05 and all(c['relative_error']<.08 for c in checks)
 return {'status':'reserved-test-supported' if passed else 'not-supported','selected_model':model if passed else None,'best_unverified_candidate':None if passed else model,'next_experiment':None if passed else investigation,'selection_scores':scores,'reserved_checks':checks,'test_used_for_selection':False,'scope':'Two registered numerical families; selection split and final test split are separate'}

def select(training,selection,testing,allow_quadratic=False):
 try:
  if any(len(rows)>128 for rows in (training,selection,testing)):return {'status':'input-budget-exceeded','selected_model':None}
  return _select(training,selection,testing,allow_quadratic)
 except (OverflowError,ZeroDivisionError,ValueError,TypeError,IndexError):return {'status':'numerically-unsupported','selected_model':None}

def investigate(training,selection,testing,oracle,budget=2):
 """Bounded simulator-only experiment loop; final test labels never enter fitting."""
 if type(budget)is not int or not 0<=budget<=4:return {'status':'invalid-experiment-budget'}
 evidence=list(training);trace=[];result=select(evidence,selection,testing)
 for _ in range(budget):
  # A failed final test must not be used to tune the same evaluation.
  if result.get('status')!='unresolved-model-family':break
  proposal=result.get('next_experiment')
  if not proposal:break
  point=tuple(proposal['inputs'])
  protected={tuple(r[:2]) for r in evidence+selection+testing}
  if point in protected:break
  before=min(r['selection_error'] for r in result['selection_scores'])
  observed=oracle(*point)
  if type(observed) not in (int,float) or not math.isfinite(observed) or not 0<observed<=1e10:
   return {'status':'invalid-experiment-observation','trace':trace,'result':result,'external_action':False}
  evidence.append((*point,observed));updated=select(evidence,selection,testing)
  scores=updated.get('selection_scores',[]);after=min((r['selection_error'] for r in scores),default=None)
  trace.append({'inputs':point,'observed':observed,'selection_error_before':before,'selection_error_after':after,'improved':after is not None and after<before,'hypothesis_family_expanded':False})
  result=updated
  if len(trace)>=2 and not any(t['improved'] for t in trace[-2:]):break
 return {'status':result.get('status'),'trace':trace,'result':result,'experiment_count':len(trace),'budget':budget,'external_action':False,'scope':'Pure numerical simulator observations only; unresolved evidence remains unresolved'}

def expand_family(training,selection,testing):
 initial=select(training,selection,testing)
 if initial.get('status')!='unresolved-model-family':return {'expanded':False,'result':initial}
 expanded=select(training,selection,testing,allow_quadratic=True)
 return {'expanded':True,'initial_status':initial['status'],'added_family':'quadratic','complexity_penalty':.002,'result':expanded,'scope':'One predeclared family expansion; final test results never trigger expansion'}
