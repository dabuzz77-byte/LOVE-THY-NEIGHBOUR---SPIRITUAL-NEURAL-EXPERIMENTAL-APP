"""Compose learned simulator equations and verify goal-directed predictions."""
import math
from .ambient_coupled_discovery import predict

def reason(models,visit):
 if not all(k in models for k in ('stellar','earth')):return {'status':'waiting-for-learned-stages'}
 luminosity=1.07+(visit%19)*.031;distance=1.21+(visit%23)*.073;absorbed=.63
 flux=predict(models['stellar'],(luminosity,distance))
 temperature=predict(models['earth'],(flux,absorbed))
 observed=(1361*luminosity/distance**2*absorbed/(4*5.670374419e-8))**.25
 target=270.;earth=models['earth'];star=models['stellar'];a,b=earth['powers'];p,q=star['powers']
 checks=[{'stage':'combined-forward','predicted':temperature,'observed':observed,'passed':math.isfinite(temperature) and abs(temperature-observed)<=1e-8*max(1,abs(observed))}]
 result={'status':'forward-checked','trace':[{'stage':'stellar','inputs':[luminosity,distance],'output':flux,'units':'W/mÂ²'},{'stage':'earth','inputs':[flux,absorbed],'output':temperature,'units':'K'}],'checks':checks,'scope':'Composition and inverse planning in idealised software reference environments. Hydrogen remains a separate model: no learned link from atomic binding to stellar luminosity is asserted.'}
 # Isolate component errors using the observed upstream value, never the predicted one.
 reference_flux=1361*luminosity/distance**2
 isolated_earth=predict(earth,(reference_flux,absorbed))
 diagnostics=[]
 for name,estimate,actual in [('stellar',flux,reference_flux),('earth',isolated_earth,observed)]:
  error=abs(estimate-actual)/max(1.,abs(actual))
  diagnostics.append({'stage':name,'predicted':estimate,'observed':actual,'relative_error':error,'passed':math.isfinite(error) and error<=1e-8})
 failed=[d['stage'] for d in diagnostics if not d['passed']]
 result['component_checks']=diagnostics
 result['relearn_stages']=failed
 result['plan_eligible']=not failed
 if failed:return {**result,'status':'counterexample-found','next_investigation':'Relearn isolated stage(s): '+', '.join(failed),'goal_plan':None}
 if a==0 or q==0:return {**result,'status':'goal-not-identifiable'}
 required_flux=(target/(earth['coefficient']*absorbed**b))**(1/a)
 chosen_distance=(required_flux/(star['coefficient']*luminosity**p))**(1/q)
 if not math.isfinite(chosen_distance) or not 1e-6<=chosen_distance<=1e6:return {**result,'status':'goal-outside-supported-range'}
 actual=(1361*luminosity/chosen_distance**2*absorbed/(4*5.670374419e-8))**.25
 passed=abs(actual-target)<=1e-8*target
 result['goal_plan']={'target_kelvin':target,'chosen_distance_AU':chosen_distance,'reference_result_kelvin':actual,'passed':passed,'external_action':False}
 result['status']='composition-and-goal-verified' if passed and all(c['passed'] for c in checks) else 'counterexample-found'
 result['next_investigation']='Check component equations against new observations' if result['status']=='counterexample-found' else 'Test a fresh luminosity-distance combination'
 return result

def reason_noisy(memory,visit):
 """Compose only independently transfer-checked approximate models."""
 needed=('stellar','earth')
 missing=[k for k in needed if k not in memory.eligible or k not in memory.models]
 if missing:return {'status':'waiting-for-transfer-checked-models','missing_stages':missing,'external_action':False}
 luminosity=.91+visit*.0031;distance=1.37+visit*.0029;absorbed=.67
 star=memory.models['stellar'];earth=memory.models['earth']
 flux=predict(star,(luminosity,distance));temperature=predict(earth,(flux,absorbed))
 true_flux=1361*luminosity/distance**2
 observed=(true_flux*absorbed/(4*5.670374419e-8))**.25
 isolated_temperature=predict(earth,(true_flux,absorbed))
 checks=[]
 for stage,estimate,actual in [('stellar',flux,true_flux),('earth',isolated_temperature,observed),('combined',temperature,observed)]:
  error=abs(math.log(estimate/actual));checks.append({'stage':stage,'predicted':estimate,'observed':actual,'absolute_log_error':error,'passed':error<=.08})
 failed=[c['stage'] for c in checks if c['stage']!='combined' and not c['passed']]
 for stage in failed:memory.eligible.discard(stage);memory.models.pop(stage,None)
 interventions=[]
 for name,l,r in [('increase luminosity 10%',luminosity*1.1,distance),('increase distance 10%',luminosity,distance*1.1)]:
  altered_flux=predict(star,(l,r));altered_temperature=predict(earth,(altered_flux,absorbed))
  actual_temperature=(1361*l/r**2*absorbed/(4*5.670374419e-8))**.25
  interventions.append({'intervention':name,'predicted_kelvin':altered_temperature,'predicted_change_kelvin':altered_temperature-temperature,'reference_kelvin':actual_temperature,'passed':abs(math.log(altered_temperature/actual_temperature))<=.08,'scope':'Counterfactual in reference simulator only'})
 # Prior observed errors propagated through the learned Earth exponent.
 errors={k:memory.latest.get(k,{}).get('fresh_capture_check') or {} for k in needed}
 residual_budget=abs(earth['powers'][0])*(errors['stellar'].get('mean_log_error') or 0)+(errors['earth'].get('mean_log_error') or 0)
 return {'status':'approximate-chain-supported' if all(c['passed'] for c in checks) else 'approximate-chain-counterexample','checks':checks,'counterfactuals':interventions,'trace':[{'stage':'stellar','inputs':[luminosity,distance],'output':flux},{'stage':'earth','inputs':[flux,absorbed],'output':temperature}],'prior_error_propagation':residual_budget,'error_scope':'Propagation of prior mean log errors, not a guaranteed bound or confidence interval','withdrawn_stages':failed,'external_action':False,'scope':'Separate approximate software-model chain; no physical zero-point inference'}
