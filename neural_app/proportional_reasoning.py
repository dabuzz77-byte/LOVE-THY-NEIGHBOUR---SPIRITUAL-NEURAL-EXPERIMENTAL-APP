"""Explicit proportional problems; no constant-rate assumption is silently added."""
import copy,re
from fractions import Fraction

N=r'([+-]?\d+(?:\.\d+)?)'

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');value=None;assumption=None;steps=[]
 match=re.fullmatch(rf'what percentage of {N} is {N}',key)
 if match:
  whole,part=map(Fraction,match.groups())
  if whole==0:raise ValueError('A percentage of a zero baseline is undefined')
  value=part/whole*100;assumption='Percentage means part divided by the explicitly supplied whole, multiplied by 100.'
  steps=[{'instruction':f'{part} / {whole} * 100','exact':str(value)}]
 match=re.fullmatch(rf'{N} is {N}% of what number',key)
 if match:
  part,percent=map(Fraction,match.groups())
  if percent==0:raise ValueError('A zero percentage does not determine a unique whole')
  value=part*100/percent;assumption='Solve part = whole × percentage / 100.';steps=[{'instruction':f'{part} * 100 / {percent}','exact':str(value)}]
 match=re.fullmatch(rf'at a constant unit price, {N} items cost {N}\. what do {N} items cost',key)
 if match:
  count,cost,wanted=map(Fraction,match.groups())
  if count<=0 or wanted<0 or cost<0 or count.denominator!=1 or wanted.denominator!=1:raise ValueError('Item counts must be whole numbers, the reference count positive, and cost and requested count nonnegative')
  unit=cost/count;value=unit*wanted;assumption='Constant unit price is explicitly supplied; discounts, fees and taxes are not inferred.';steps=[{'instruction':f'{cost} / {count} (unit price)','exact':str(unit)},{'instruction':f'{unit} * {wanted}','exact':str(value)}]
 if value is not None:
  from .exact_work import finish
  result=finish(work,value,steps,text);return {**result,'assumption':assumption}
 split=re.fullmatch(rf'split {N} in ratio (.+)',key);percentages=re.fullmatch(r'convert ratio (.+) to percentages',key)
 if split or percentages:
  raw=split[2] if split else percentages[1];parts=raw.split(':')
  if not 2<=len(parts)<=16 or any(not re.fullmatch(N,p.strip()) for p in parts):raise ValueError('Supply 2–16 numeric ratio weights separated by colons')
  weights=[Fraction(p.strip()) for p in parts]
  if any(w<0 for w in weights) or sum(weights)==0:raise ValueError('Ratio weights must be nonnegative with a positive total')
  total=Fraction(split[1]) if split else Fraction(100);denominator=sum(weights);values=[total*w/denominator for w in weights]
  if max(max(v.numerator.bit_length(),v.denominator.bit_length()) for v in values)>8192:raise ValueError('Ratio result exceeds the numeric budget')
  from .native_work import digest
  report={'request':text,'total':str(total),'weights':list(map(str,weights)),'exact_values':list(map(str,values)),'sum_exact':str(sum(values)),'scope':'Exact proportional allocation in input order; no rounding or indivisible-item allocation is inferred.'};report['receipt_sha256']=digest(report)
  work.state['proportional_result']=copy.deepcopy(report);work.state['focus_kind']='proportional-reasoning'
  return {'status':'complete','answer':', '.join(report['exact_values'])+(' percent' if percentages else ''),'exact_values':report['exact_values'],'allocation':report,'model_calls':0}
 if key=='explain this allocation':
  report=work.state.get('proportional_result')
  if not report:return {'status':'needs-input','answer':'Complete a ratio allocation first.','model_calls':0}
  from .native_work import digest
  if report.get('receipt_sha256')!=digest({k:v for k,v in report.items() if k!='receipt_sha256'}):raise ValueError('Allocation changed after its receipt; calculate it again')
  return {'status':'complete','answer':'Each share = '+report['total']+' × its weight / '+str(sum(map(Fraction,report['weights'])))+'. Shares: '+', '.join(report['exact_values'])+'. Their exact sum is '+report['sum_exact']+'. '+report['scope'],'action_repeated':False,'model_calls':0}
 return None
