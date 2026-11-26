"""Native time-series forecasts selected by rolling, past-only backtests.

Forecast ranges are empirical error envelopes, never claimed confidence bounds.
No random/generated symbol stream is treated as measured world data.
"""
import copy,json,math,re
from fractions import Fraction

def number(value):
    if isinstance(value,bool) or not isinstance(value,(str,int,float)):
        raise ValueError('Observations must be finite numbers')
    if len(str(value))>80:
        raise ValueError('Observation is too large')
    try:
        result=Fraction(str(value))
    except (ValueError,ZeroDivisionError):
        raise ValueError('Observations must be finite numbers') from None
    if abs(result)>10**15:
        raise ValueError('Keep observation magnitudes at most 10^15')
    return result

def predict(values,method,horizon=1):
    n=len(values)
    if method=='last':return values[-1]
    if method=='mean':return sum(values)/n
    if method=='drift':return values[-1]+(values[-1]-values[0])*horizon/(n-1)
    if method=='linear':
        centre=Fraction(n-1,2);mean=sum(values)/n
        slope=sum((Fraction(i)-centre)*(v-mean) for i,v in enumerate(values))/sum((Fraction(i)-centre)**2 for i in range(n))
        return mean+slope*(n-1+horizon-centre)
    raise ValueError('Unknown forecast method')

def build(body):
    if not isinstance(body,dict) or not isinstance(body.get('values'),list) or not 5<=len(body['values'])<=500:
        raise ValueError('Supply 5–500 equally spaced numeric observations')
    values=[number(v) for v in body['values']]
    horizon=body.get('horizon',1)
    if type(horizon)is not int or not 1<=horizon<=24:
        raise ValueError('Use an integer forecast horizon from 1 to 24')
    label=body.get('label','supplied observations');unit=body.get('unit','unspecified units')
    if not all(isinstance(v,str) and 0<len(v)<=160 for v in (label,unit)):
        raise ValueError('Use short label and unit strings')
    # Select on early folds; evaluate the selected method on untouched later folds.
    origins=list(range(3,len(values)))
    split=max(1,len(origins)//2)
    training,holdout=origins[:split],origins[split:]
    methods=['last','mean','drift','linear']
    errors={name:[predict(values[:i],name)-values[i] for i in training] for name in methods}
    scores={name:sum(abs(e) for e in errs)/len(errs) for name,errs in errors.items()}
    winner=min(methods,key=lambda name:(scores[name],methods.index(name)))
    validation=[{'index':i,'predicted':str(predict(values[:i],winner)), 'actual':str(values[i]),
                 'absolute_error':str(abs(predict(values[:i],winner)-values[i]))} for i in holdout]
    held_errors=[abs(predict(values[:i],winner)-values[i]) for i in holdout]
    baseline=[abs(values[i-1]-values[i]) for i in holdout]
    mae=sum(held_errors)/len(held_errors) if held_errors else None
    baseline_mae=sum(baseline)/len(baseline) if baseline else None
    envelope=max(held_errors) if held_errors else max(abs(e) for e in errors[winner])
    forecasts=[]
    # Freeze the method selected on early folds. Check each horizon against
    # later observations using only information available at each origin.
    origin_predictions={i:(predict(values[:i],winner,1),predict(values[:i],winner,2)-predict(values[:i],winner,1)) for i in holdout}
    for step in range(1,horizon+1):
        point=predict(values,winner,step)
        checks=[]
        for origin,(base,increment) in origin_predictions.items():
            target=origin+step-1
            if target>=len(values):continue
            predicted=base+increment*(step-1)
            checks.append({'origin':origin,'target_index':target,'prediction':str(predicted),'actual':str(values[target]),'absolute_error':str(abs(predicted-values[target])),'last_baseline_error':str(abs(values[origin-1]-values[target]))})
        errors_at_horizon=[Fraction(row['absolute_error']) for row in checks]
        baseline_at_horizon=[Fraction(row['last_baseline_error']) for row in checks]
        forecasts.append({'step':step,'point':str(point),'display':float(point),
                          'empirical_low':str(point-envelope*step),'empirical_high':str(point+envelope*step),
                          'horizon_backtest':{'cases':checks,'count':len(checks),'mae':str(sum(errors_at_horizon)/len(checks)) if checks else None,'baseline_mae':str(sum(baseline_at_horizon)/len(checks)) if checks else None,'scope':'Past-only evaluation with frozen method; overlapping cases are dependent, not independent trials.'},
                          'competing_method_points':{name:str(predict(values,name,step)) for name in methods}})
    return {'status':'forecast','label':label,'unit':unit,'observations':[str(v) for v in values],
            'method':winner,'selection_mae':{k:str(v) for k,v in scores.items()},'selection_origins':training,
            'heldout_validation':validation,'heldout_mae':str(mae) if mae is not None else None,
            'baseline_heldout_mae':str(baseline_mae) if baseline_mae is not None else None,
            'beats_last_baseline':mae<baseline_mae if mae is not None else None,
            'forecasts':forecasts,'model_calls':0,
            'scope':'Numeric extrapolation for equally spaced supplied observations. Selection uses early past-only folds; reported evaluation uses later folds. Error envelopes are not confidence intervals. Regime changes, causal explanations and unobserved world facts are not inferred.'}

def render(report):
    lines=[f"**Forecast: {report['label']}**",f"Selected method: {report['method']}."]
    for row in report['forecasts']:
        lines.append(f"- Step +{row['step']}: {row['point']} {report['unit']}; empirical error envelope {row['empirical_low']} to {row['empirical_high']}.")
        checked=row.get('horizon_backtest',{})
        if checked.get('count'):lines.append(f"Horizon +{row['step']}: {checked['count']} past-only evaluation cases; mean absolute error {checked['mae']}; last-observation baseline {checked['baseline_mae']}. Cases may overlap.")
        else:lines.append(f"No held-out evaluation cases are available for horizon +{row['step']}; one-step accuracy does not validate this horizon.")
        if len(set(row.get('competing_method_points',{}).values()))>1:lines.append('Candidate methods disagree at this horizon. Their forecasts are available in the recorded evidence; agreement or spread is not a confidence bound.')
    lines.append(f"Later held-out mean absolute error: {report['heldout_mae']}; last-observation baseline: {report['baseline_heldout_mae']}.")
    if not report['beats_last_baseline']:
        lines.append('This selected method has not beaten the last-observation baseline on the held-out observations.')
    lines.append(report['scope'])
    return '\n\n'.join(lines)

def respond(text,state):
    match=re.match(r'^(?:forecast|predict next|forecast series)\s*:\s*([\s\S]+)',text,re.I)
    old=state.get('validated_forecast')
    if match:
        body=json.loads(match[1]);body={'values':body} if isinstance(body,list) else body
    elif old and state.get('focus_kind')=='validated-forecast':
        key=text.strip().casefold().rstrip('?.!')
        if key in ('explain forecast','show forecast evidence','why this forecast','how did you predict that'):
            return {'status':'complete','answer':render(old)+'\n\nBacktest records:\n'+json.dumps(old['heldout_validation'],indent=2),'forecast':copy.deepcopy(old),'model_calls':0}
        update=re.fullmatch(r'(?:observe|add observation)\s*:\s*(.+)',text,re.I)
        horizon=re.fullmatch(r'(?:forecast|predict)\s+(\d+)\s+(?:more\s+)?steps?',key)
        if update:
            body={'values':old['observations']+[str(number(update[1]))], 'label':old['label'],'unit':old['unit'],'horizon':len(old['forecasts'])}
        elif horizon:
            body={'values':old['observations'],'label':old['label'],'unit':old['unit'],'horizon':int(horizon[1])}
        else:return None
    else:return None
    report=build(body)
    if old and 'update' in locals() and update:
        report['previous_prediction_check']={'predicted':old['forecasts'][0]['point'],'actual':str(number(update[1])),
                    'absolute_error':str(abs(number(old['forecasts'][0]['point'])-number(update[1])))}
    state['validated_forecast']=report;state['focus_kind']='validated-forecast'
    answer=render(report)
    if report.get('previous_prediction_check'):answer+='\n\nPrevious prediction checked: '+json.dumps(report['previous_prediction_check'])
    return {'status':'forecast','answer':answer,'forecast':copy.deepcopy(report),'model_calls':0}
