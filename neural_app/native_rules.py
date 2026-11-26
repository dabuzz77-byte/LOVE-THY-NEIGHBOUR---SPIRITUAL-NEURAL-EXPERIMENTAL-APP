"""Exact low-degree numeric rule learning with separate validation and revocation."""
import copy,math
from fractions import Fraction

def number(value):
 if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e12:raise ValueError('Use finite bounded numbers')
 return Fraction(str(value))

def predict(points,value,exact=False):
 x=value if isinstance(value,Fraction) else number(value);total=Fraction(0)
 for i,(xi,yi) in enumerate(points):
  term=yi
  for j,(xj,_) in enumerate(points):
   if j!=i:term*=((x-xj)/(xi-xj))
  total+=term
  if total.numerator.bit_length()>1024 or total.denominator.bit_length()>1024:raise ValueError('Numeric rule exceeds precision budget')
 if abs(total)>10**100:raise ValueError('Rule prediction exceeds numeric range')
 return total if exact else int(total) if total.denominator==1 else float(total)

def learn(body):
 if not isinstance(body,dict):raise ValueError('Provide name, examples and holdout')
 name=str(body.get('name','')).strip().casefold();train=body.get('examples');holdout=body.get('holdout')
 if not name or len(name)>80 or not isinstance(train,list) or not 2<=len(train)<=8 or not isinstance(holdout,list) or not 2<=len(holdout)<=8:raise ValueError('Use a name, 2–8 examples and 2–8 separate validation cases')
 rows=[]
 for item in train+holdout:
  if not isinstance(item,dict):raise ValueError('Rule examples require input and output')
  rows.append((number(item['input']),number(item['output'])))
 if len({x for x,_ in rows})!=len(rows):raise ValueError('All training and validation inputs must be distinct')
 training=rows[:len(train)];validation=rows[len(train):];attempts=[]
 for degree in (1,2):
  if len(training)<degree+1:continue
  points=training[:degree+1];fitted=all(predict(points,x,exact=True)==y for x,y in training)
  if not fitted:attempts.append({'degree':degree,'training_passed':False});continue
  checks=[{'input':float(x),'expected':float(y),'actual':predict(points,x),'passed':predict(points,x,exact=True)==y} for x,y in validation]
  attempts.append({'degree':degree,'training_passed':True,'validation':checks})
  if not all(c['passed'] for c in checks):return {'retained':False,'name':name,'attempts':attempts,'scope':'Candidate rejected; validation data was not recycled to select another family.'}
  return {'retained':True,'active':True,'name':name,'degree':degree,'points':[[str(x),str(y)] for x,y in points],'training_cases':len(train),'validation':checks,'attempts':attempts,'scope':'Exact low-degree interpolation consistent with these finite cases; extrapolation is a prediction, not guaranteed truth.'}
 return {'retained':False,'name':name,'attempts':attempts,'scope':'No degree-one or degree-two rule fits the supplied training cases.'}

def use(rule,value,expected=None,check=False):
 if not isinstance(rule,dict) or not rule.get('active'):raise ValueError('Rule is unavailable or was revoked by contrary evidence')
 actual=predict([(Fraction(x),Fraction(y)) for x,y in rule['points']],value)
 result={'input':value,'prediction':actual,'validated_on_this_input':False,'rule':rule['name'],'model_calls':0}
 if check:
  passed=number(actual)==number(expected);result.update(expected=expected,passed=passed,checked_on_this_input=True,validated_on_this_input=passed,expected_source='explicit user-supplied check')
  if not passed:rule['active']=False;rule['counterexample']=copy.deepcopy(result)
 return result
