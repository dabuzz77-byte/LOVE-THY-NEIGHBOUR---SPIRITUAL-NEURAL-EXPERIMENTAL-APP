"""Within-unit before/after comparisons with explicit pairing and no causal shortcut."""
import math,statistics
from .empirical_learning import num

def compare(body):
 before=body.get('before');after=body.get('after');ids=body.get('ids')
 if not isinstance(before,list) or not isinstance(after,list) or len(before)!=len(after) or not 2<=len(before)<=512:raise ValueError('Provide matching before/after arrays with 2 to 512 paired observations')
 if ids is None:ids=list(range(1,len(before)+1))
 if not isinstance(ids,list) or len(ids)!=len(before) or any(not isinstance(v,(str,int)) or isinstance(v,bool) for v in ids) or len({str(v) for v in ids})!=len(ids):raise ValueError('Provide one unique short identifier per pair')
 if any(len(str(v))>100 for v in ids):raise ValueError('Use identifiers up to 100 characters')
 before=list(map(num,before));after=list(map(num,after));deltas=[b-a for a,b in zip(before,after)]
 return {'pair_count':len(before),'before_mean':statistics.fmean(before),'after_mean':statistics.fmean(after),'mean_change':math.fsum(deltas)/len(deltas),'median_change':statistics.median(deltas),'minimum_change':min(deltas),'maximum_change':max(deltas),'positive_changes':sum(v>0 for v in deltas),'negative_changes':sum(v<0 for v in deltas),'unchanged':sum(v==0 for v in deltas),'pairs':[{'id':identifier,'before':a,'after':b,'change':d} for identifier,a,b,d in zip(ids,before,after,deltas)],'assumptions':['each position follows the same unit across both measurements','measurement methods and units are comparable','the supplied pairing has not been independently authenticated'],'scope':'Descriptive within-unit change. Concurrent changes and confounding can explain it; no causal effect or success probability is inferred automatically.','model_calls':0}
