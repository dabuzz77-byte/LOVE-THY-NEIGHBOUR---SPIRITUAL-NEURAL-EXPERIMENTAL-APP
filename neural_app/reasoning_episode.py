"""Resumable multi-role investigations with chronological, held-out evidence."""
import copy,hashlib,json,math,statistics,time

ROLES={'research':'source-study','hypotheses':'whole-mind-study','experiment':'experiment','validation':'choice-study','predict':'consequence-study','observation':'action-study','check':'consequence-study','synthesis':'synthesis','retain':'whole-mind-study'}

def finite(x):return type(x) in (int,float) and math.isfinite(x) and abs(x)<1e100
def predict(model,values):
 if model=='persistence':return values[-1]
 if model=='mean':return statistics.fmean(values[-8:])
 if model=='trend':return values[-1]+statistics.median([values[i]-values[i-1] for i in range(max(1,len(values)-8),len(values))])
 raise ValueError('Unknown registered model')

def create(spec):
 if not isinstance(spec,dict):raise ValueError('Use an episode object')
 if len(json.dumps(spec,allow_nan=False))>40000:raise ValueError('Episode input exceeds 40 KB')
 name=spec.get('name');rows=spec.get('observations');source=spec.get('source');units=spec.get('units');origin=spec.get('origin')
 if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('Use a short episode name')
 if not isinstance(source,str) or not source.strip() or len(source)>500:raise ValueError('Declare the source')
 if not isinstance(units,str) or not units or len(units)>80:raise ValueError('Declare units')
 if origin not in ('measured','modelled','generated','user-supplied'):raise ValueError('Declare evidence origin: measured, modelled, generated or user-supplied')
 if not isinstance(rows,list) or not 12<=len(rows)<=128:raise ValueError('Provide 12–128 chronological observations')
 previous=-float('inf');clean=[]
 for row in rows:
  if not isinstance(row,dict) or not finite(row.get('time')) or not finite(row.get('value')) or row['time']<=previous:raise ValueError('Observations require finite values and strictly increasing numeric timestamps')
  previous=row['time'];clean.append({'time':row['time'],'value':row['value']})
 horizon=spec.get('horizon_seconds')
 if not finite(horizon) or not 0<horizon<=31536000:raise ValueError('Declare a positive forecast horizon in seconds')
 split=max(8,len(clean)*2//3)
 return {'id':hashlib.sha256(json.dumps([spec,time.time_ns()],sort_keys=True).encode()).hexdigest()[:20],
  'name':name.strip(),'source':source,'units':units,'origin':origin,'observations':clean,'training_count':split,
  'horizon_seconds':horizon,'phase':'research','status':'running','trace':[],'artifacts':{},'sequence':0,'created':time.time(),'model_calls':0}

def tests(model,rows,start,end):
 values=[r['value'] for r in rows];records=[]
 for i in range(start,end):
  estimate=predict(model,values[:i]);records.append({'time':rows[i]['time'],'prediction':estimate,'actual':values[i],'absolute_error':abs(estimate-values[i])})
 return {'model':model,'cases':len(records),'mae':statistics.fmean(r['absolute_error'] for r in records),'records':records}

def advance(ep):
 if ep['status']!='running':return False
 phase=ep['phase'];a=ep['artifacts'];rows=ep['observations'];n=ep['training_count'];record={'phase':phase,'role':ROLES[phase],'time':time.time()}
 if phase=='research':
  intervals=[rows[i]['time']-rows[i-1]['time'] for i in range(1,len(rows))];cadence=statistics.median(intervals)
  a['source_contract']={'source':ep['source'],'origin':ep['origin'],'units':ep['units'],'count':len(rows),'median_cadence_seconds':cadence,'declared_horizon_seconds':ep['horizon_seconds'],'cadence_matches_horizon':all(math.isclose(x,ep['horizon_seconds'],rel_tol=.05,abs_tol=1e-6) for x in intervals),'independently_verified':False,'data_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()}
  if not a['source_contract']['cadence_matches_horizon']:ep.update(status='needs-input',error='Observation cadence must match the declared horizon within 5%; resample or specify a matching horizon.');record['error']=ep['error']
  else:ep['phase']='hypotheses'
 elif phase=='hypotheses':a['models']=['persistence','mean','trend'];ep['phase']='experiment'
 elif phase=='experiment':
  comparisons=[tests(m,rows,3,n) for m in a['models']];selected=min(comparisons,key=lambda r:(r['mae'],r['model']!='persistence',r['model']));a['comparison']=comparisons;a['selected']=selected['model'];ep['phase']='validation'
 elif phase=='validation':
  # Never choose or replace a model using validation answers.
  chosen=tests(a['selected'],rows,n,len(rows));baseline=tests('persistence',rows,n,len(rows));a['validation']={'selected':chosen,'baseline':baseline,'beats_baseline':chosen['mae']<baseline['mae'],'no_worse_than_baseline':chosen['mae']<=baseline['mae'],'selection_frozen_before_validation':True}
  if chosen['mae']>baseline['mae']:ep.update(validation_failed=True,error='Selected model failed to match the held-out persistence baseline. More evidence or a revised model is needed.');ep['phase']='synthesis'
  else:ep['phase']='predict'
 elif phase=='predict':
  value=predict(a['selected'],[r['value'] for r in rows]);errors=[r['absolute_error'] for r in a['validation']['selected']['records']];width=max(errors)
  a['forecast']={'value':value,'target_time':rows[-1]['time']+ep['horizon_seconds'],'issued_at':time.time(),'model':a['selected'],'units':ep['units'],'empirical_error_band':[value-width,value+width],'band_scope':'Maximum held-out residual band; not a calibrated confidence interval.'};ep.update(phase='observation',status='awaiting-observation')
 elif phase=='check':
  obs=a['new_observation'];forecast=a['forecast'];error=abs(obs['value']-forecast['value']);base_error=abs(obs['value']-rows[-1]['value'])
  a['outcome']={'actual':obs['value'],'time':obs['time'],'absolute_error':error,'baseline_absolute_error':base_error,'no_worse_than_baseline':error<=base_error,'inside_empirical_band':forecast['empirical_error_band'][0]<=obs['value']<=forecast['empirical_error_band'][1],'source':obs['source'],'origin':obs['origin'],'independence':'Declared matching source; observation origin is not independently authenticated by this module.'};ep['phase']='synthesis'
 elif phase=='synthesis':
  a['conclusion']={'question':ep['name'],'selected_model':a['selected'],'validation':a.get('validation'),'outcome':a.get('outcome'),'source_contract':a['source_contract'],'scope':'Bounded numeric model comparison on declared observations. No general causal or scientific claim follows.','next_step':'Retain the tested case and collect another independent observation; revise a failed model rather than conceal its error.'};ep['phase']='retain'
 elif phase=='retain':ep.update(status='inconclusive' if ep.get('validation_failed') else 'complete',retained=True)
 record['artifact_keys']=list(a);record['status']=ep['status'];ep['trace'].append(record);ep['sequence']+=1
 return True

def observe(ep,body):
 if ep['status']!='awaiting-observation':raise ValueError('Episode is not awaiting an observation')
 if body.get('episode_id')!=ep['id']:raise ValueError('Observation must name the exact episode_id')
 if body.get('source')!=ep['source'] or body.get('units')!=ep['units'] or body.get('origin')!=ep['origin']:raise ValueError('Source, units and origin must match the episode contract')
 if not finite(body.get('value')) or not finite(body.get('time')):raise ValueError('Observation requires a finite value and timestamp')
 if not math.isclose(body['time'],ep['artifacts']['forecast']['target_time'],rel_tol=0,abs_tol=max(1e-6,ep['horizon_seconds']*.05)):raise ValueError('Observation must match the forecast target time within 5% of its horizon')
 ep['artifacts']['new_observation']={k:copy.deepcopy(body[k]) for k in ('source','units','origin','time','value')}
 ep['trace'].append({'phase':'observation','role':ROLES['observation'],'time':time.time(),'status':'accepted','scope':'Matching later input accepted as declared evidence; no external action executed.'})
 ep.update(status='running',phase='check');ep['sequence']+=1

def summary(ep):
 if not ep:return None
 return copy.deepcopy({k:ep.get(k) for k in ('id','name','phase','status','source','units','origin','sequence','trace','artifacts','error','retained','model_calls')})

def command(state,body):
 op=body.get('op');ep=state.get('reasoning_episode')
 if op=='status':return summary(ep)
 if op=='start':
  if ep and ep['status'] in ('running','awaiting-observation'):raise ValueError('Finish or cancel the current episode first')
  if ep:state['reasoning_episode_history']=(state.get('reasoning_episode_history',[])+[summary(ep)])[-8:]
  ep=create(body.get('spec'));state['reasoning_episode']=ep
 elif op=='observe':
  if not ep:raise ValueError('No episode exists')
  observe(ep,body.get('observation',{}))
 elif op=='cancel':
  if ep:ep['status']='cancelled'
 elif op!='status':raise ValueError('Use start, observe, status or cancel')
 state['focus_kind']='reasoning-episode'
 return summary(ep)
