"""Transactional exact arithmetic chains with explicit conversational continuity."""
import copy,re
from fractions import Fraction
from .exact_numbers import calculate

NUMBER=r'[+-]?\d+(?:\.\d+)?'

def finish(work,value,steps,question):
 from .native_work import digest
 report={'exact_result':str(value),'steps':copy.deepcopy(steps),'question':question,'scope':'Exact rational arithmetic for explicitly supported numeric instructions. No empirical prediction is implied.'}
 report['receipt_sha256']=digest(report)
 work.state['exact_work']=copy.deepcopy(report);work.state['focus_kind']='exact-work'
 return {'status':'complete','answer':str(value),**report,'model_calls':0}

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');retained=work.state.get('exact_work')
 if key in ('explain this calculation','explain the calculation'):
  if work.state.get('focus_kind')!='exact-work' or not retained:return {'status':'needs-input','answer':'Complete an exact numeric calculation first.','model_calls':0}
  return {'status':'complete','answer':'\n'.join(str(row['instruction'])+' → '+row['exact'] for row in retained['steps']) or 'The explicit input value was retained unchanged.','action_repeated':False,'calculation_receipt':retained['receipt_sha256'],'model_calls':0}
 start=re.fullmatch(rf'start with ({NUMBER})\s*;\s*(.+)',key)
 follow=re.fullmatch(r'(?:now|then) (.+)',key)
 if start:value=Fraction(start[1]);tail=start[2];steps=[{'instruction':'start with '+start[1],'exact':str(value)}]
 elif follow and work.state.get('focus_kind')=='exact-work' and retained:
  from .native_work import digest
  if retained.get('receipt_sha256')!=digest({k:v for k,v in retained.items() if k!='receipt_sha256'}):raise ValueError('The retained exact result changed without a matching receipt')
  value=Fraction(retained['exact_result']);tail=follow[1];steps=copy.deepcopy(retained['steps'])
 else:return None
 clauses=re.split(r'\s*;\s*|\s+then\s+',tail)
 if not 1<=len(clauses)<=16 or len(steps)+len(clauses)>64:raise ValueError('Use up to 16 operations and 64 retained steps')
 for clause in clauses:
  clause=re.sub(r'^(?:then|now)\s+','',clause.strip())
  match=re.fullmatch(rf'(add|subtract|multiply by|divide by|increase by|decrease by) ({NUMBER})(%)?',clause)
  if clause in ('double','double it','halve','halve it'):value=value*2 if clause.startswith('double') else value/2
  elif match:
   verb,number,percent=match.groups();operand=Fraction(number)
   if verb in ('increase by','decrease by'):
    if not percent:raise ValueError('Use an explicit % for increase by or decrease by')
    value=value*(1+operand/100 if verb=='increase by' else 1-operand/100)
   else:
    if percent:raise ValueError('Use increase by or decrease by for relative percentages')
    operator={'add':'+','subtract':'-','multiply by':'*','divide by':'/'}[verb]
    value=Fraction(calculate('('+str(value)+')'+operator+'('+str(operand)+')')['exact_result'])
  else:raise ValueError('Uninterpreted numeric operation: '+clause[:160]+'. No part of the chain was committed.')
  if max(value.numerator.bit_length(),value.denominator.bit_length())>8192:raise ValueError('Exact numeric chain exceeds its result budget')
  steps.append({'instruction':clause,'exact':str(value)})
 return finish(work,value,steps,text)
