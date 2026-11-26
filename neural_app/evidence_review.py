"""Compare explicit, attributed claims without converting repetition into proof."""
import itertools,json,math
from urllib.parse import urlsplit

def review(body):
 if not isinstance(body,dict) or len(json.dumps(body,allow_nan=False))>64000:raise ValueError('Use a bounded evidence review object')
 claims=body.get('claims')
 if not isinstance(claims,list) or not 1<=len(claims)<=24:raise ValueError('Supply 1 to 24 attributed claims')
 rows=[]
 for i,claim in enumerate(claims):
  if not isinstance(claim,dict):raise ValueError('Each claim must be an object')
  row={'id':str(claim.get('id',i+1))[:80]}
  for key in ('claim','metric','population','period','unit','method','source','publisher','study_id'):
   value=claim.get(key,'')
   if not isinstance(value,str) or len(value)>2000:raise ValueError('Claim fields must be bounded text')
   row[key]=value.strip()
  if not row['claim'] or not row['source']:raise ValueError('Each claim needs text and a source attribution')
  for key in ('value','lower','upper'):
   value=claim.get(key)
   if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e100):raise ValueError('Use finite bounded claim numbers')
   row[key]=value
  if (row['lower'] is None)!=(row['upper'] is None) or (row['lower'] is not None and row['lower']>row['upper']):raise ValueError('Provide an ordered lower/upper pair')
  row['missing_context']=[k for k in ('metric','population','period','unit','method') if not row[k]]
  row['independently_verified']=False
  rows.append(row)
 if len({r['id'] for r in rows})!=len(rows):raise ValueError('Claim IDs must be unique')
 comparisons=[]
 for a,b in itertools.combinations(rows,2):
  same_study=bool(a['study_id'] and a['study_id'].casefold()==b['study_id'].casefold())
  domain_a=urlsplit(a['source']).hostname;domain_b=urlsplit(b['source']).hostname
  shared=same_study or a['source']==b['source'] or bool(a['publisher'] and a['publisher'].casefold()==b['publisher'].casefold()) or bool(domain_a and domain_a==domain_b)
  dimensions=('metric','population','period','unit','method')
  missing=sorted(set(a['missing_context']+b['missing_context']))
  different=[k for k in dimensions if a[k] and b[k] and a[k].casefold()!=b[k].casefold()]
  comparable=not missing and not different and a['value'] is not None and b['value'] is not None
  overlap=None
  if comparable and all(r['lower'] is not None for r in (a,b)):overlap=max(a['lower'],b['lower'])<=min(a['upper'],b['upper'])
  comparisons.append({'claims':[a['id'],b['id']],'comparable_as_declared':comparable,'missing_context':missing,'different_dimensions':different,'shared_source_or_study':shared,'independence':'shared provenance; do not count as independent confirmation' if shared else 'not established merely by different URLs','numeric_difference':b['value']-a['value'] if comparable else None,'reported_intervals_overlap':overlap,'finding':'different reported values under matching declared conditions' if comparable and a['value']!=b['value'] else 'matching reported values' if comparable else 'resolve context before comparing'})
 return {'claims':rows,'comparisons':comparisons,'distinct_attributions':len({r['source'] for r in rows}),'open_questions':['Check the original study or record, measurement definition and date.','Check whether sources repeat the same underlying observation.','Seek relevant contrary evidence and explain differences before combining numbers.'],'scope':'Structured comparison of supplied claims, not automatic fact verification or evidence of causation. Different methods/populations/dates are not automatically contradictions.','model_calls':0}
