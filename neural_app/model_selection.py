"""Bounded nonlinear transfer with separate selection and final evaluation sets."""
import math,statistics
from .empirical_learning import num

def basis(kind,x):
 if kind=='linear':return [1.,x]
 if kind=='quadratic':return [1.,x,x*x]
 if kind=='cubic':return [1.,x,x*x,x*x*x]
 if kind=='logarithmic':
  if x<=0:raise ValueError('Logarithmic models require positive x')
  return [1.,math.log(x)]
 raise ValueError('Unknown model family')

def solve(rows,ys):
 n=len(rows[0]);a=[[math.fsum(r[i]*r[j] for r in rows) for j in range(n)]+[math.fsum(r[i]*y for r,y in zip(rows,ys))] for i in range(n)]
 for col in range(n):
  pivot=max(range(col,n),key=lambda k:abs(a[k][col]))
  if abs(a[pivot][col])<1e-12:raise ValueError('Insufficient independent variation')
  a[col],a[pivot]=a[pivot],a[col];d=a[col][col];a[col]=[v/d for v in a[col]]
  for k in range(n):
   if k!=col:
    d=a[k][col];a[k]=[v-d*w for v,w in zip(a[k],a[col])]
 return [row[-1] for row in a]

def evaluate(model,x):
 z=(num(x)-model['centre'])/model['scale']
 return num(math.fsum(a*b for a,b in zip(model['coefficients'],basis(model['family'],z))))

def fit_candidates(body):
 xs=body.get('x');ys=body.get('y')
 if not isinstance(xs,list) or not isinstance(ys,list) or len(xs)!=len(ys) or not 15<=len(xs)<=512:raise ValueError('Provide 15 to 512 ordered x/y pairs')
 xs=list(map(num,xs));ys=list(map(num,ys));n=len(xs);test=max(3,n//5);validation=max(3,n//5);train=n-test-validation
 centre=statistics.fmean(xs[:train]);scale=max(abs(x-centre) for x in xs[:train])
 if scale<1e-12:raise ValueError('Insufficient training variation')
 baseline=statistics.fmean(ys[:train]);candidates=[]
 for family in ('linear','quadratic','cubic'):
  model={'family':family,'centre':centre,'scale':scale}
  try:model['coefficients']=solve([basis(family,(x-centre)/scale) for x in xs[:train]],ys[:train])
  except ValueError:continue
  model['selection_RMSE']=math.sqrt(statistics.fmean((evaluate(model,x)-y)**2 for x,y in zip(xs[train:n-test],ys[train:n-test])));candidates.append(model)
 if not candidates:raise ValueError('No supported model can be fitted')
 # Prefer the smaller model when selection differences are below numerical tolerance.
 selected=candidates[0]
 for candidate in candidates[1:]:
  if candidate['selection_RMSE']+max(1e-9,selected['selection_RMSE']*1e-6)<selected['selection_RMSE']:selected=candidate
 predictions=[evaluate(selected,x) for x in xs[n-test:]];error=math.sqrt(statistics.fmean((a-b)**2 for a,b in zip(predictions,ys[n-test:])));base=math.sqrt(statistics.fmean((y-baseline)**2 for y in ys[n-test:]))
 return {**selected,'model_type':'selected-polynomial','training_count':train,'selection_count':validation,'holdout_count':test,'holdout_RMSE':error,'baseline_RMSE':base,'validated_against_baseline':error<=base,'holdout_predictions':predictions,'holdout_observations':ys[n-test:],'observed_x_range':[min(xs),max(xs)],'training_residual_scale':math.sqrt(statistics.fmean((evaluate(selected,x)-y)**2 for x,y in zip(xs[:train],ys[:train]))),'candidates':[{'family':m['family'],'selection_RMSE':m['selection_RMSE']} for m in candidates],'source':str(body.get('source','user-supplied ordered observations'))[:300],'scope':'Training fits coefficients; selection chooses family; untouched final observations evaluate transfer. Association is not causal identification.','model_calls':0}

def stratified_comparison(body):
 rows=body.get('strata')
 if not isinstance(rows,list) or not 1<=len(rows)<=32:raise ValueError('Provide 1 to 32 strata with treated/control outcomes')
 details=[];all_t=[];all_c=[]
 for row in rows:
  t=row.get('treated');c=row.get('control')
  if not isinstance(t,list) or not isinstance(c,list) or not 1<=len(t)<=512 or not 1<=len(c)<=512:raise ValueError('Each stratum needs both comparison groups, at most 512 each')
  t=list(map(num,t));c=list(map(num,c));all_t+=t;all_c+=c;details.append({'name':str(row.get('name',''))[:100],'difference':statistics.fmean(t)-statistics.fmean(c),'weight':len(t)+len(c)})
 total=sum(r['weight'] for r in details);adjusted=math.fsum(r['difference']*r['weight']/total for r in details);pooled=statistics.fmean(all_t)-statistics.fmean(all_c)
 return {'pooled_difference':pooled,'standardized_difference':adjusted,'strata':details,'direction_reversal':pooled*adjusted<0,'weighting':'combined observed population of each stratum','assumptions':['strata are declared before comparison','both groups occur in every stratum','causal interpretation additionally requires adequate confounding control and consistent outcomes'],'scope':'Descriptive stratified comparison; unmeasured confounders and selection bias are not resolved automatically','model_calls':0}
