"""Chronological validation of measured affine relationships, not automatic causation."""
import json,math,statistics

def num(value):
 if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e12:raise ValueError('Use finite numbers within the supported measurement range')
 return float(value)

def fit(body):
 if body.get('family','linear') not in ('linear','auto'):raise ValueError('Choose linear or auto model family')
 if body.get('family')=='auto':
  from .model_selection import fit_candidates
  return fit_candidates(body)
 x=body.get('x');y=body.get('y')
 if not isinstance(x,list) or not isinstance(y,list) or len(x)!=len(y) or not 8<=len(x)<=512:raise ValueError('Provide matching x and y arrays of 8 to 512 observations in capture order')
 x=list(map(num,x));y=list(map(num,y));holdout=body.get('holdout',max(2,len(x)//4))
 if type(holdout) is not int or not 2<=holdout<=len(x)-4:raise ValueError('Reserve at least two holdout observations and four training observations')
 train=len(x)-holdout;mx=statistics.fmean(x[:train]);my=statistics.fmean(y[:train]);ss=math.fsum((v-mx)**2 for v in x[:train])
 if ss<=1e-20:raise ValueError('Training x values have insufficient variation to fit a relationship')
 slope=math.fsum((a-mx)*(b-my) for a,b in zip(x[:train],y[:train]))/ss;intercept=my-slope*mx
 predicted=[intercept+slope*v for v in x[train:]];errors=[actual-estimate for actual,estimate in zip(y[train:],predicted)];baseline=[actual-my for actual in y[train:]]
 rmse=math.sqrt(math.fsum(v*v for v in errors)/holdout);base_rmse=math.sqrt(math.fsum(v*v for v in baseline)/holdout);train_errors=[b-(intercept+slope*a) for a,b in zip(x[:train],y[:train])];sigma=math.sqrt(math.fsum(e*e for e in train_errors)/max(1,train-2))
 validated=rmse<=base_rmse and (base_rmse>0 or rmse==0)
 return {'slope':slope,'intercept':intercept,'training_count':train,'holdout_count':holdout,'training_x_range':[min(x[:train]),max(x[:train])],'observed_x_range':[min(x),max(x)],'holdout_predictions':predicted,'holdout_observations':y[train:],'holdout_RMSE':rmse,'baseline_RMSE':base_rmse,'validated_against_baseline':validated,'training_residual_scale':sigma,'source':str(body.get('source','user-supplied ordered observations'))[:300],'assumptions':['x and y are paired observations in the given order','The fitted relationship is affine','Later observations are excluded from fitting'],'scope':'Validated association under stated assumptions; this does not establish that changing x causes y','model_calls':0}

def predict(model,x):
 if model.get('model_type')=='selected-polynomial':
  from .model_selection import evaluate
  value=num(x);lo,hi=model['observed_x_range']
  return {'result':evaluate(model,value),'x':value,'extrapolation':not lo<=value<=hi,'validated_against_baseline':model['validated_against_baseline'],'residual_scale':model['training_residual_scale'],'source':model['source'],'family':model['family'],'model_calls':0}
 value=num(x);estimate=model['intercept']+model['slope']*value;lo,hi=model['observed_x_range'];return {'result':estimate,'x':value,'extrapolation':not lo<=value<=hi,'validated_against_baseline':model['validated_against_baseline'],'residual_scale':model['training_residual_scale'],'source':model['source'],'scope':'Prediction from a retained measured relationship; extrapolation and validation status remain explicit','model_calls':0}

def sensitivity(body):
 from .reasoning_engine import causal,finite
 baseline=causal(body);ranges=body.get('ranges',{})
 if not isinstance(ranges,dict) or len(ranges)>16:raise ValueError('Use up to 16 root-value ranges')
 roots=body.get('values',{});equations=body.get('equations',{});intervals={k:[finite(v),finite(v)] for k,v in roots.items()}
 for name,pair in ranges.items():
  if name not in roots or not isinstance(pair,list) or len(pair)!=2:raise ValueError('Ranges must name supplied root values and contain lower/upper numbers')
  low,high=map(finite,pair)
  if low>high:raise ValueError('Range lower bound must not exceed its upper bound')
  intervals[name]=[low,high]
 pending=set(equations)
 while pending:
  ready=[name for name in sorted(pending) if set(equations[name].get('weights',{}))<=set(intervals)]
  if not ready:raise ValueError('Unresolved or cyclic graph')
  for name in ready:
   e=equations[name];low=high=e.get('bias',0)
   for parent,weight in e.get('weights',{}).items():
    a,b=intervals[parent];products=[a*weight,b*weight];low+=min(products);high+=max(products)
   intervals[name]=[finite(low),finite(high)];pending.remove(name)
 return {'point_model':baseline,'ranges':intervals,'scope':'Conservative interval propagation under supplied equations; shared-parent dependencies can widen bounds. These are not statistical confidence intervals.','model_calls':0}

def intervention_study(body):
 """Independent-group permutation comparison; method reference is SciPy's official documentation."""
 import itertools,random
 treated=body.get('treated');control=body.get('control');design=body.get('design','observational')
 if not isinstance(treated,list) or not isinstance(control,list) or not 2<=len(treated)<=128 or not 2<=len(control)<=128:raise ValueError('Provide 2 to 128 outcomes in each group')
 if design not in ('observational','declared-randomized'):raise ValueError('Use observational or declared-randomized design')
 treated=list(map(num,treated));control=list(map(num,control));pool=treated+control;n=len(treated);total=math.fsum(pool);m=len(control);observed=statistics.fmean(treated)-statistics.fmean(control);possible=math.comb(len(pool),n);exact=possible<=20000;seed=body.get('seed',0)
 if type(seed) is not int:raise ValueError('Seed must be an integer')
 rng=random.Random(seed);count=possible if exact else 999;greater=less=0;tolerance=max(1e-12,abs(observed)*1e-12)
 indices=itertools.combinations(range(len(pool)),n) if exact else (rng.sample(range(len(pool)),n) for _ in range(count))
 for group in indices:
  selected=math.fsum(pool[i] for i in group);difference=selected/n-(total-selected)/m;greater+=difference>=observed-tolerance;less+=difference<=observed+tolerance
 adjustment=0 if exact else 1;p=min(1.,2*min((greater+adjustment)/(count+adjustment),(less+adjustment)/(count+adjustment)))
 return {'difference_in_means':observed,'treated_mean':statistics.fmean(treated),'control_mean':statistics.fmean(control),'group_sizes':[n,m],'permutation_p_value':p,'permutations':count,'exact':exact,'seed':None if exact else seed,'floating_comparison_tolerance':tolerance,'design':design,'causal_status':'conditional on the declared experimental assumptions' if design=='declared-randomized' else 'not identified from observational group differences alone','assumptions':['exchangeable observations under the comparison null','independent groups and consistent outcome measurement','declared assignment method has not been independently verified','no interference between units for a causal interpretation'],'scope':'A difference estimate and permutation compatibility test; the p-value is not a probability that an effect is causal','sources':[{'title':'SciPy permutation_test documentation','url':'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html'}],'model_calls':0}
