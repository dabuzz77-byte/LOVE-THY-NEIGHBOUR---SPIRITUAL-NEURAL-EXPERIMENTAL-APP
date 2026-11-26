"""Exact finite abduction-action-prediction under explicitly supplied assumptions."""
import itertools,time,math
from fractions import Fraction
from .linear_reasoning import rational,checked
from .boolean_counterfactual import prepare

def solve(body):
 allowed={'mode','values','equations','outcome','observations','interventions','independent_inputs_assumed','probe_variables','test_target_intervention','question'}
 if set(body)-allowed:raise ValueError('Unsupported causal probability fields: '+', '.join(sorted(set(body)-allowed))+'. Correlated priors, time dynamics and measurement costs require a different explicit model')
 values=body.get('values');equations=body.get('equations');outcome=body.get('outcome');observations=body.get('observations',{});interventions=body.get('interventions',[])
 if not isinstance(values,dict) or not 1<=len(values)<=10:raise ValueError('Use 1–10 independent Boolean input factors')
 probabilities={}
 for name,value in values.items():
  if type(value)is bool:probabilities[name]=Fraction(int(value))
  elif isinstance(value,dict) and set(value)=={'probability_true'}:probabilities[name]=rational(value['probability_true'])
  else:raise ValueError('Each input needs a Boolean value or an explicit probability_true')
  if not 0<=probabilities[name]<=1:raise ValueError('Input probabilities must be from zero to one')
 uncertain=sum(0<p<1 for p in probabilities.values())
 if uncertain>1 and body.get('independent_inputs_assumed') is not True:raise ValueError('Explicitly declare independent_inputs_assumed for multiple uncertain factors; dependence is not inferred')
 model=prepare({name:False for name in values},equations,outcome);names=model['names'];evaluate=model['evaluate']
 def setting(value,allow_empty=False):
  if not isinstance(value,dict) or not allow_empty and not value or not set(value)<=names or any(type(v)is not bool for v in value.values()):raise ValueError('Observations and interventions need Boolean values for known variables')
 setting(observations,True)
 if not isinstance(interventions,list) or len(interventions)>16:raise ValueError('Use up to 16 explicit interventions')
 seen=set()
 for row in interventions:
  if not isinstance(row,dict) or set(row)!={'name','set'} or not isinstance(row.get('name'),str) or not row['name'].strip() or len(row['name'])>120 or row['name'] in seen:raise ValueError('Use distinct short intervention names and explicit set values only')
  seen.add(row['name']);setting(row.get('set'))
 probes=body.get('probe_variables',list(values))
 if not isinstance(probes,list) or len(probes)>16 or any(not isinstance(n,str) or n not in names or n==outcome for n in probes) or len(set(probes))!=len(probes):raise ValueError('Choose up to 16 distinct known probe variables, excluding the target outcome')
 selected_target=body.get('test_target_intervention',interventions[0]['name'] if interventions else 'baseline')
 if selected_target!='baseline' and selected_target not in seen:raise ValueError('The test target must be baseline or a known intervention name')
 deadline=time.monotonic()+2;keys=list(values);worlds=[];prior=Fraction(0);mass=Fraction(0);posterior=Fraction(0)
 for bits in itertools.product((False,True),repeat=len(keys)):
  if time.monotonic()>deadline:raise ValueError('Causal probability budget reached; no partial probability is certified')
  inputs=dict(zip(keys,bits));weight=Fraction(1)
  for key,bit in inputs.items():weight=checked(weight*(probabilities[key] if bit else 1-probabilities[key]))
  if not weight:continue
  world=evaluate({},inputs);prior=checked(prior+weight*world[outcome]);matches=all(world[n]==v for n,v in observations.items())
  worlds.append((inputs,world,weight,matches))
  if matches:mass=checked(mass+weight);posterior=checked(posterior+weight*world[outcome])
 base={'complete':True,'prior_outcome_probability':str(prior),'evidence_probability':str(mass),'outcome_variable':outcome,'observations':observations,'input_probabilities':{n:str(p) for n,p in probabilities.items()},'worlds_enumerated':len(worlds),'independent_inputs_assumed':body.get('independent_inputs_assumed') is True,'evaluation_order':model['order'],'scope':'Exact probabilities within the supplied acyclic Boolean model and explicitly declared independent-input priors. Conditioning observes the original world; intervention changes equations after conditioning. No causal structure, real-world calibration, blame or intent is learned from these calculations.'}
 if not mass:return {**base,'status':'impossible-evidence','posterior_outcome_probability':None,'interventions':[],'next_step':'The observations have zero probability under this model; revise the model, priors or evidence before drawing a conclusion.'}
 rows=[]
 for row in interventions:
  action=observed_mass=observed_outcome=Fraction(0)
  for inputs,world,weight,matches in worlds:
   if time.monotonic()>deadline:raise ValueError('Causal probability budget reached; no partial probability is certified')
   if not matches:continue
   changed=evaluate(row['set'],inputs);action=checked(action+weight*changed[outcome])
   if all(world[n]==v for n,v in row['set'].items()):observed_mass=checked(observed_mass+weight);observed_outcome=checked(observed_outcome+weight*world[outcome])
  rows.append({'name':row['name'],'set':row['set'],'counterfactual_probability_given_evidence':str(checked(action/mass)),'observational_probability_given_same_setting':str(checked(observed_outcome/observed_mass)) if observed_mass else None,'observational_setting_probability_given_evidence':str(checked(observed_mass/mass)),'observational_setting_impossible':not bool(observed_mass)})
 target_setting=next((r['set'] for r in interventions if r['name']==selected_target),{});samples=[];target_true=Fraction(0)
 for inputs,world,weight,matches in worlds:
  if not matches:continue
  if time.monotonic()>deadline:raise ValueError('Causal probability budget reached; no partial ranking is certified')
  target=evaluate(target_setting,inputs)[outcome];samples.append((world,weight,target));target_true=checked(target_true+weight*target)
 def entropy(probability):
  total=0.0
  for p in (probability,1-probability):
   if p:total-=float(p)*(math.log2(p.numerator)-math.log2(p.denominator))
  return max(0.0,total)
 target_entropy=entropy(target_true/mass);ranked=[]
 for probe in probes:
  conditional_entropy=0.0;outcomes=[]
  for value in (False,True):
   weight_sum=positive=Fraction(0)
   for world,weight,target in samples:
    if time.monotonic()>deadline:raise ValueError('Causal probability budget reached; no partial ranking is certified')
    if world[probe]==value:weight_sum=checked(weight_sum+weight);positive=checked(positive+weight*target)
   if weight_sum:
    event=weight_sum/mass;conditional_entropy+=float(event)*entropy(positive/weight_sum);outcomes.append({'value':value,'probability_given_evidence':str(event),'target_probability_if_observed':str(positive/weight_sum)})
  ranked.append({'variable':probe,'expected_information_bits':max(0.0,target_entropy-conditional_entropy),'already_observed':probe in observations,'outcomes':outcomes})
 ranked.sort(key=lambda r:(-r['expected_information_bits'],r['variable']))
 suggestion=ranked[0]['variable'] if ranked and ranked[0]['expected_information_bits']>1e-12 else None
 return {**base,'status':'updated','posterior_outcome_probability':str(checked(posterior/mass)),'interventions':rows,'candidate_observations':ranked,'suggested_observation':suggestion,'observation_target':selected_target,'noiseless_pre_intervention_observations_assumed':True,'next_step':'Compare observing and intervening separately, then check the causal equations, priors and independence assumptions. Candidate-observation rankings assume noiseless pre-intervention measurements and omit measurement costs.'}
