"""Independent workflow completion contracts; never call the executor to verify it."""
import collections,csv,io,json,math,re
from fractions import Fraction

def equivalent(a,b):
 if type(a) is int and type(b) is int:return a==b
 if type(a) in (int,float) and type(b) in (int,float):
  try:return math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
  except OverflowError:return False
 if type(a)!=type(b):return False
 if isinstance(a,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
 if isinstance(a,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
 return a==b

def verify(before,step,after):
 op=step.get('op');expected=None
 try:
  if op in ('add','scale','divide') and type(before) in (int,float):
   a=Fraction(str(before));b=Fraction(str(step['value']));expected=float(a+b if op=='add' else a*b if op=='scale' else a/b)
  elif op=='strip':expected=before.strip()
  elif op=='lower':expected=before.lower()
  elif op=='upper':expected=before.upper()
  elif op=='reverse':return isinstance(after,str) and len(after)==len(before) and after[::-1]==before
  elif op=='lines':expected=before.splitlines()
  elif op=='words':expected=re.findall(r"[^\W_]+",before,re.UNICODE)
  elif op=='json':expected=json.loads(before) if isinstance(before,str) else before
  elif op=='csv':
   rows=list(csv.reader(io.StringIO(before)));expected=[dict(zip(rows[0],r)) for r in rows[1:]]
  elif op=='field':expected=[r[step['name']] for r in before] if isinstance(before,list) else before[step['name']]
  elif op=='group':
   names=[];expected=[];field=step['field'];aggregate=step.get('aggregate','count')
   for row in before:
    if row[field] not in names:names.append(row[field])
   for name in names:
    rows=[r for r in before if r[field]==name];values=[Fraction(str(r[step['value_field']])) for r in rows] if aggregate!='count' else []
    result=len(rows) if aggregate=='count' else float(sum(values)) if aggregate=='sum' else float(sum(values)/len(rows)) if aggregate=='mean' else float(min(values)) if aggregate=='minimum' else float(max(values))
    expected.append({'key':name,'value':result,'count':len(rows)})
  elif op=='count':expected=len(before)
  elif op=='join':expected=str(step.get('separator','\n'))[:100].join(map(str,before))
  elif op=='unique':
   expected=[]
   for v in before:
    if not any(json.dumps(v,sort_keys=True,allow_nan=False)==json.dumps(x,sort_keys=True,allow_nan=False) for x in expected):expected.append(v)
  elif op=='sort':
   if not isinstance(after,list) or len(after)!=len(before):return False
   enc=lambda v:json.dumps(v,sort_keys=True,allow_nan=False)
   if collections.Counter(map(enc,before))!=collections.Counter(map(enc,after)):return False
   key=step.get('field');values=[r[key] if key is not None else r for r in after]
   return all(a>=b if step.get('descending') else a<=b for a,b in zip(values,values[1:]))
  elif op=='frequencies':expected=dict(collections.Counter(map(str,before)))
  elif op=='numbers':expected=[float(v) for v in before]
  elif op=='filter':
   expected=[];target=step['value'];relation=step.get('relation','equal');field=step.get('field')
   for item in before:
    v=item[field] if field is not None else item
    keep={'equal':lambda:v==target,'greater':lambda:v>target,'less':lambda:v<target,'at_least':lambda:v>=target,'at_most':lambda:v<=target,'contains':lambda:target in v}[relation]()
    if keep:expected.append(item)
  elif op in ('add','scale','divide'):
   operand=Fraction(str(step['value']));expected=[float(Fraction(str(v))+operand if op=='add' else Fraction(str(v))/operand if op=='divide' else Fraction(str(v))*operand) for v in before]
  elif op in ('sum','mean'):
   total=sum((Fraction(str(v)) for v in before),Fraction(0));expected=float(total/len(before) if op=='mean' else total)
  elif op=='minimum':expected=min(before)
  elif op=='maximum':expected=max(before)
  elif op=='median':
   # Median contract uses counts around the candidate, plus central order statistics for even lists.
   if not before:return False
   ordered=sorted(before);n=len(ordered);expected=ordered[n//2] if n%2 else float((Fraction(str(ordered[n//2-1]))+Fraction(str(ordered[n//2])))/2)
  elif op=='take':expected=before[:step['count']]
  elif op=='replace':expected=before.replace(step['old'],step['new'])
  else:return False
  return equivalent(expected,after)
 except (TypeError,ValueError,KeyError,IndexError,ZeroDivisionError,OverflowError):return False
