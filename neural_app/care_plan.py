"""Bounded, transparent care planning; never an inference about souls or people."""
import math
DEFAULT_NODES=[{'label':'Lamb · illustrative need','need':.9,'urgency':.8,'protection':.2},{'label':'Lion · illustrative need','need':.6,'urgency':.6,'protection':.6},{'label':'Butterfly · illustrative need','need':.8,'urgency':.7,'protection':.1},{'label':'Child · illustrative need','need':1.,'urgency':1.,'protection':.1}]
def unit(value,name):
 if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:raise ValueError(name+' must be a finite value from 0 to 1')
 return float(value)
def plan(body):
 budget=body.get('budget',1.5)
 if type(budget) not in (int,float) or not math.isfinite(budget) or not 0<=budget<=16:raise ValueError('Use a planning budget from 0 to 16 units')
 nodes=body.get('nodes',DEFAULT_NODES)
 if not isinstance(nodes,list) or not 1<=len(nodes)<=16:raise ValueError('Use 1–16 explicitly entered needs')
 checked=[]
 for index,node in enumerate(nodes):
  if not isinstance(node,dict):raise ValueError('Each need must be an object')
  label=node.get('label','Need '+str(index+1))
  if not isinstance(label,str) or not label.strip() or len(label)>80:raise ValueError('Use a short label of 1–80 characters')
  row={'id':index,'label':label.strip(),**{name:unit(node.get(name,.5),name) for name in ('need','urgency','protection')}}
  row['priority']=row['need']*(.5+.5*row['urgency'])*(1-.5*row['protection']);row['allocated']=0.;checked.append(row)
 remaining=float(budget);active=[r for r in checked if r['need']>0]
 # Weighted water filling. When one need is full, reallocate only the remainder.
 for _ in range(len(checked)+1):
  if remaining<=1e-12 or not active:break
  weight=sum(r['priority'] for r in active);offered=remaining;used=0.
  for row in active:
   amount=min(row['need']-row['allocated'],offered*row['priority']/weight);row['allocated']+=amount;used+=amount
  remaining=max(0.,remaining-used);active=[r for r in active if r['need']-r['allocated']>1e-12]
 total_need=sum(r['need'] for r in checked);allocated=sum(r['allocated'] for r in checked)
 for row in checked:row.update(unmet=max(0.,row['need']-row['allocated']),protection_after=row['protection'])
 return {'status':'COMPLETE','module':'care-plan','mode':'MOST_VULNERABLE_FIRST','anchor':'PRESERVE_PROTECTION','budget':float(budget),'allocated':allocated,'unallocated_budget':max(0.,float(budget)-allocated),'total_need':total_need,'unmet_need':max(0.,total_need-allocated),'coverage':allocated/total_need if total_need else 0.,'nodes':checked,'priority_order':[r['id'] for r in sorted(checked,key=lambda r:(-r['priority'],r['id']))],'formula':'need × (0.5 + 0.5 × urgency) × (1 − 0.5 × existing protection)','scope':'Illustrative planning units, supplied explicitly. No private-data scanning, medical triage, inferred spiritual state, identity-based penalty or claim that real aid was delivered. Protection is never reduced.'}
