"""Eliminate explicit predictions and select conservative distinguishing probes."""
import json

def token(value):
 encoded=json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=True)
 if len(encoded)>1000:raise ValueError('Prediction values must be small JSON values')
 return encoded

def diagnose(body):
 candidates=body.get('hypotheses');observed=body.get('observations',{})
 if not isinstance(candidates,list) or not 1<=len(candidates)<=32 or not isinstance(observed,dict) or len(observed)>32:raise ValueError('Provide 1–32 hypotheses and up to 32 named observations')
 for value in observed.values():token(value)
 names=set();probes=set(observed);rows=[]
 for candidate in candidates:
  if not isinstance(candidate,dict):raise ValueError('Each hypothesis needs a name and predictions')
  name=candidate.get('name');predictions=candidate.get('predictions',{})
  if not isinstance(name,str) or not name.strip() or len(name)>120 or name.casefold() in names or not isinstance(predictions,dict) or len(predictions)>32:raise ValueError('Use distinct short hypothesis names and up to 32 predictions')
  names.add(name.casefold());probes.update(predictions)
  matches=[];mismatches=[];missing=[]
  for probe,value in observed.items():
   if probe not in predictions:missing.append(probe)
   elif token(predictions[probe])==token(value):matches.append(probe)
   else:mismatches.append(probe)
  for value in predictions.values():token(value)
  rows.append({'name':name,'predictions':predictions,'matches':matches,'mismatches':mismatches,'missing_predictions':missing,'status':'eliminated' if mismatches else 'compatible' if not missing else 'unresolved'})
 if len(probes)>64 or any(not isinstance(p,str) or not p.strip() or len(p)>120 for p in probes):raise ValueError('Use up to 64 distinct short probe names')
 live=[r for r in rows if r['status']!='eliminated'];ranked=[]
 for probe in sorted(probes-set(observed)):
  groups={};unknown=[]
  for row in live:
   if probe not in row['predictions']:unknown.append(row['name']);continue
   value=row['predictions'][probe];entry=groups.setdefault(token(value),{'outcome':value,'hypotheses':[]});entry['hypotheses'].append(row['name'])
  # Missing predictions may survive every outcome: never count them as excluded.
  worst=max([len(g['hypotheses'])+len(unknown) for g in groups.values()]+[len(unknown)])
  ranked.append({'probe':probe,'guaranteed_eliminations':len(live)-worst,'worst_case_remaining':worst,'outcomes':list(groups.values()),'unknown_predictions':unknown})
 ranked.sort(key=lambda r:(-r['guaranteed_eliminations'],r['probe']))
 status='no-compatible-hypothesis' if not live else 'single-compatible-hypothesis' if len(live)==1 and live[0]['status']=='compatible' and observed else 'needs-observations' if not observed else 'underdetermined'
 return {'status':status,'complete':True,'hypotheses':rows,'remaining':[r['name'] for r in live],'candidate_probes':ranked,'next_step':'Revise the hypothesis catalogue, prediction model or observations; none fits all supplied observations.' if not live else 'Observe '+ranked[0]['probe']+' to distinguish the surviving predictions.' if ranked and ranked[0]['guaranteed_eliminations'] else 'Supply a distinguishing prediction or independent observation; compatibility is not proof of cause.','scope':'Exact comparison of supplied deterministic predictions only. Missing predictions remain unknown. Probe ranking minimises worst-case survivors, without invented probabilities, test costs or causal certainty.'}

def compile_frame(frame):
 predictions=frame.get('predictions',[]);observations=frame.get('observations',[])
 if not predictions and not observations:return None
 options=frame.get('options',[])
 if not options:return {'clarification':'List the candidate explanations under options before comparing their predictions.'}
 rows={name:{'name':name,'predictions':{}} for name in options};observed={}
 try:
  for item in predictions:
   name,probe_value=item.split('|',1);probe,value=probe_value.split('=',1);name=name.strip();probe=probe.strip();value=json.loads(value)
   if name not in rows:raise ValueError('Prediction names must match the listed options')
   prior=rows[name]['predictions']
   if probe in prior and token(prior[probe])!=token(value):raise ValueError('Conflicting predictions for the same explanation and probe')
   prior[probe]=value
  for item in observations:
   probe,value=item.split('=',1);probe=probe.strip();value=json.loads(value)
   if probe in observed and token(observed[probe])!=token(value):raise ValueError('Conflicting observations for the same probe')
   observed[probe]=value
 except (ValueError,TypeError) as exc:return {'clarification':'Use predictions: OPTION | PROBE = JSON and observations: PROBE = JSON. '+str(exc)[:150]}
 return {'model':{'mode':'diagnostic','hypotheses':list(rows.values()),'observations':observed}}
