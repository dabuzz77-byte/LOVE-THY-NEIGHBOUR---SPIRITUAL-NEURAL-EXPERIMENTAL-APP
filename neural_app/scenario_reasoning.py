"""Exact scenario trade-offs without inventing likelihoods or risk preferences."""
from fractions import Fraction
import re

def number(value):
 if type(value) not in (str,int,float) or len(str(value))>120:raise ValueError('Use short finite numeric values')
 exponent=re.search(r'[eE]([+-]?\d+)$',str(value))
 if exponent and abs(int(exponent[1]))>300:raise ValueError('Scenario exponent exceeds the exact arithmetic limit')
 try:result=Fraction(str(value))
 except (ValueError,ZeroDivisionError,OverflowError):raise ValueError('Use finite rational numbers') from None
 if result.numerator.bit_length()>1024 or result.denominator.bit_length()>1024:raise ValueError('Scenario number exceeds the exact arithmetic limit')
 return result

def compare(body):
 states=body.get('scenarios');options=body.get('options');direction=body.get('direction','max')
 if not isinstance(states,list) or not 1<=len(states)<=32 or not isinstance(options,list) or not 2<=len(options)<=16 or direction not in ('min','max'):raise ValueError('Provide 1–32 scenario names, 2–16 options and min/max direction')
 def names(values):
  return all(isinstance(n,str) and n.strip() and len(n)<=120 for n in values) and len({n.casefold() for n in values})==len(values)
 if not names(states) or not all(isinstance(o,dict) for o in options) or not names([o.get('name') for o in options]):raise ValueError('Scenario and option names must be distinct nonempty labels')
 values=[]
 for option in options:
  outcomes=option.get('outcomes')
  if not isinstance(outcomes,dict) or set(outcomes)!=set(states):raise ValueError('Each option needs an explicit outcome for every scenario')
  values.append([number(outcomes[s]) for s in states])
 utilities=[[v if direction=='max' else -v for v in row] for row in values];best=[max(row[j] for row in utilities) for j in range(len(states))]
 probabilities=body.get('probabilities');weights=None
 if probabilities is not None:
  if not isinstance(probabilities,dict) or set(probabilities)!=set(states):raise ValueError('Supply a probability for every scenario')
  weights=[number(probabilities[s]) for s in states]
  if any(p<0 or p>1 for p in weights) or sum(weights)!=1:raise ValueError('Scenario probabilities must be nonnegative and sum exactly to one')
 rows=[];dominated=set()
 for i,option in enumerate(options):
  regrets=[b-v for b,v in zip(best,utilities[i])];dominators=[]
  for j,other in enumerate(options):
   if i!=j and all(a>=b for a,b in zip(utilities[j],utilities[i])) and any(a>b for a,b in zip(utilities[j],utilities[i])):dominators.append(other['name']);dominated.add(option['name'])
  row={'name':option['name'],'outcomes':{s:str(v) for s,v in zip(states,values[i])},'regrets':{s:str(v) for s,v in zip(states,regrets)},'worst_regret':str(max(regrets)),'worst_outcome':str(min(values[i]) if direction=='max' else max(values[i])),'dominated_by':dominators}
  if weights is not None:row['expected_outcome']=str(sum(w*v for w,v in zip(weights,values[i])))
  rows.append(row)
 minimum=min(number(r['worst_regret']) for r in rows)
 expected=[]
 if weights is not None:
  optimum=(max if direction=='max' else min)(number(r['expected_outcome']) for r in rows);expected=[r['name'] for r in rows if number(r['expected_outcome'])==optimum]
 return {'status':'compared','complete':True,'direction':direction,'options':rows,'undominated_options':[r['name'] for r in rows if r['name'] not in dominated],'minimax_regret_options':[r['name'] for r in rows if number(r['worst_regret'])==minimum],'expected_outcome_options':expected,'probabilities_supplied':weights is not None,'next_step':'Check which scenarios, outcomes and risk preference apply. Minimax regret and expected outcome answer different questions.','scope':'Exact rational comparison under supplied scenario outcomes, in one common declared measure. No likelihoods, preferences, empirical predictions or external actions are inferred.'}
