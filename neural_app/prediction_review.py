"""Score supplied predictions against outcomes and a declared comparison baseline."""
import math

def review(body):
 if not isinstance(body,dict):raise ValueError('Supply an outcome review object')
 rows=body.get('observations');kind=body.get('kind','numeric')
 if kind not in ('numeric','probability') or not isinstance(rows,list) or not 3<=len(rows)<=512:raise ValueError('Supply 3 to 512 numeric or probability observations')
 clean=[];ids=set()
 for i,row in enumerate(rows):
  if not isinstance(row,dict):raise ValueError('Each observation must be an object')
  ident=row.get('id',str(i+1))
  if not isinstance(ident,str) or len(ident)>120 or ident in ids:raise ValueError('Observation IDs must be unique bounded text')
  ids.add(ident);values=[]
  for key in ('predicted','actual','baseline'):
   v=row.get(key)
   if type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e100:raise ValueError('Each observation needs finite predicted, actual and baseline numbers')
   if kind=='probability' and (not 0<=v<=1 or key=='actual' and v not in (0,1)):raise ValueError('Use probabilities in [0,1] and observed outcomes 0 or 1')
   values.append(v)
  p,a,b=values;clean.append({'id':ident,'predicted':p,'actual':a,'baseline':b,'error':p-a,'absolute_error':abs(p-a),'baseline_absolute_error':abs(b-a)})
 n=len(clean);mae=math.fsum(r['absolute_error'] for r in clean)/n;baseline=math.fsum(r['baseline_absolute_error'] for r in clean)/n
 mse=math.fsum(r['error']**2 for r in clean)/n;baseline_mse=math.fsum((r['baseline']-r['actual'])**2 for r in clean)/n
 metrics={'count':n,'mae':mae,'baseline_mae':baseline,'rmse':math.sqrt(mse),'baseline_rmse':math.sqrt(baseline_mse),'beats_baseline_mae':mae<baseline,'beats_baseline_mse':mse<baseline_mse,'mean_signed_error':math.fsum(r['error'] for r in clean)/n}
 bins=[]
 if kind=='probability':
  metrics.update(brier_score=mse,baseline_brier_score=baseline_mse)
  for i in range(5):
   group=[r for r in clean if min(4,int(r['predicted']*5))==i]
   if group:bins.append({'range':[i/5,(i+1)/5],'count':len(group),'mean_prediction':math.fsum(r['predicted'] for r in group)/len(group),'observed_frequency':math.fsum(r['actual'] for r in group)/len(group)})
 return {'kind':kind,'metrics':metrics,'calibration_bins':bins,'observations':clean,'evidence_status':'Caller-supplied outcomes; timing, independence and held-out status require external verification.','scope':'Prediction accuracy for supplied cases only. Prediction is not causal identification, moral certainty or a guarantee of future outcomes.','model_calls':0}
