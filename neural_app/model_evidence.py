"""Independently recompute reported final-evaluation errors from retained outcomes."""
import math

def audit(model):
 predicted=model.get('holdout_predictions');actual=model.get('holdout_observations')
 if not isinstance(predicted,list) or not isinstance(actual,list) or not predicted or len(predicted)!=len(actual):return {'status':'insufficient-record','verified':False,'reason':'Matching held-out predictions and outcomes are required'}
 try:
  values=predicted+actual+[model.get('holdout_RMSE'),model.get('baseline_RMSE')]
  if not all(type(v) in (int,float) and math.isfinite(v) for v in values):raise ValueError('Nonfinite or missing evaluation data')
  error=math.sqrt(math.fsum((a-b)**2 for a,b in zip(predicted,actual))/len(actual));reported=model['holdout_RMSE'];baseline=model['baseline_RMSE'];comparison=error<=baseline
  count_ok=model.get('holdout_count')==len(actual);error_ok=math.isclose(error,reported,rel_tol=1e-10,abs_tol=1e-10);claim_ok=model.get('validated_against_baseline') is comparison;ok=count_ok and error_ok and claim_ok and baseline>=0
  return {'status':'consistent' if ok else 'inconsistent','verified':ok,'recomputed_RMSE':error,'count_matches':count_ok,'error_matches':error_ok,'comparison_claim_matches':claim_ok,'scope':'Checks retained final-error arithmetic and comparison claims; does not authenticate measurements or verify the baseline construction'}
 except (TypeError,ValueError,OverflowError) as exc:return {'status':'inconsistent','verified':False,'reason':str(exc)[:200]}

def summary(models):
 rows=[{'name':name,**audit(model)} for name,model in models.items()]
 return {'models':rows,'consistent':sum(r['status']=='consistent' for r in rows),'inconsistent':sum(r['status']=='inconsistent' for r in rows),'insufficient_record':sum(r['status']=='insufficient-record' for r in rows),'scope':'Independent evaluation-record checks; no automatic capability grade'}
