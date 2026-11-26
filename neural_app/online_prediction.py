"""Per-source, per-path rolling forecast tests; units are never pooled."""
import collections,copy,math,statistics
class OnlinePrediction:
 def __init__(self,saved=None):
  self.models=collections.OrderedDict();self.tested=0
  for key,row in list((saved or {}).get('models',{}).items())[-128:]:
   if not isinstance(key,str) or not isinstance(row,dict):continue
   try:
    if row['selected'] not in ('persistence','trend') or not isinstance(row['report'],dict):continue
    numbers=[row['last'],*row['forecasts'].values(),*row['chosen_errors'],*row['errors']['persistence'],*row['errors']['trend']]
    if any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e92 for v in numbers):continue
    if set(row['forecasts'])!={'persistence','trend'}:continue
    self.models[key]=copy.deepcopy(row)
   except (KeyError,TypeError,AttributeError):continue
 def observe(self,stage,source,path,value,parent_event=None):
  if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e90:raise ValueError('Use a bounded finite measurement')
  import json
  key=json.dumps([stage,source,path],ensure_ascii=True);old=self.models.get(key);prior=None
  if old and parent_event is not None and old.get('parent_event')==parent_event:return copy.deepcopy(old['report'])
  errors=copy.deepcopy(old.get('errors',{'persistence':[],'trend':[]})) if old else {'persistence':[],'trend':[]};chosen_errors=list(old.get('chosen_errors',[])) if old else []
  if old:
   predicted=old['forecasts'][old['selected']];error=abs(value-predicted);baseline=statistics.median(chosen_errors) if chosen_errors else 0
   prior={'predicted':predicted,'observed':value,'absolute_error':error,'method':old['selected'],'anomaly':len(chosen_errors)>=8 and error>max(1e-9,baseline*6),'baseline_residual':baseline}
   for method,estimate in old['forecasts'].items():errors[method]=(errors[method]+[abs(value-estimate)])[-16:]
   chosen_errors=(chosen_errors+[error])[-16:];self.tested+=1
  tested=len(errors['persistence']);scores={name:sum(vals)/len(vals) if vals else None for name,vals in errors.items()}
  selected='trend' if tested>=6 and scores['trend']<scores['persistence'] else 'persistence';delta=value-old['last'] if old else 0;forecasts={'persistence':value,'trend':value+delta}
  report={'stage':stage,'source':source,'path':path,'parent_event':parent_event,'previous_test':prior,'next_prediction':forecasts[selected],'method':selected,'tested':tested,'rolling_MAE':scores,'scope':'Repeated observations at this exact source/path; descriptive prediction, not proof of a cause'}
  self.models[key]={'last':value,'forecasts':forecasts,'selected':selected,'errors':errors,'chosen_errors':chosen_errors,'parent_event':parent_event,'report':report};self.models.move_to_end(key)
  while len(self.models)>128:self.models.popitem(last=False)
  return copy.deepcopy(report)
 def checkpoint(self):return {'models':copy.deepcopy(dict(self.models))}
 def view(self):return {'streams':len(self.models),'tested_forecasts':self.tested,'recent':[copy.deepcopy(r['report']) for r in list(self.models.values())[-12:]],'scope':'Model selection uses past errors only; newly observed values test previously emitted forecasts.'}
