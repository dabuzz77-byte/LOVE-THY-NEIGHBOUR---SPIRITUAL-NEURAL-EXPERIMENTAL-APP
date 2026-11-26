"""Compare explicit numeric alternatives using independently calculated exact values."""
import json,re
from fractions import Fraction
from .exact_numbers import calculate

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');previous=work.state.get('calculation_comparison')
 if work.state.get('focus_kind')=='calculation-comparison' and previous:
  from .native_work import digest
  if key in ('why this choice','explain this comparison','what would change this choice') or key.startswith('change alternative '):
   if previous.get('receipt_sha256')!=digest({k:v for k,v in previous.items() if k!='receipt_sha256'}):raise ValueError('Comparison receipt changed; run the comparison again')
  if key in ('why this choice','explain this comparison'):
   return {'status':'complete','answer':'The supplied preference is '+previous['prefer']+'.\n'+'\n'.join(row['name']+': '+row['expression']+' = '+row['exact_result'] for row in previous['options'])+'\nSelected: '+', '.join(previous['selected'])+'. Ties are preserved. No omitted criterion was assumed.','action_repeated':False,'model_calls':0}
  if key=='what would change this choice':
   return {'status':'complete','answer':'Change a supplied expression or the minimum/maximum preference. Use change alternative NAME to EXPRESSION to recalculate one alternative. Missing criteria and uncertainty require an explicit new model.','action_repeated':False,'model_calls':0}
  changed=re.fullmatch(r'change alternative (.+?) to (.+)',text.strip(),re.I|re.S)
  if changed:
   matches=[row for row in previous['options'] if row['name'].casefold()==changed[1].strip().casefold()]
   if len(matches)!=1:raise ValueError('Name one existing alternative to revise')
   options=[{'name':r['name'],'expression':changed[2].strip() if r is matches[0] else r['expression']} for r in previous['options']]
   result=respond('compare calculations: '+json.dumps({'options':options,'prefer':previous['prefer']}),work)
   result['previous_selected']=previous['selected'];result['selection_changed']=result['comparison']['selected']!=previous['selected'];return result
 if not text.strip().casefold().startswith('compare calculations:'):return None
 body=json.loads(text.split(':',1)[1])
 if not isinstance(body,dict) or set(body)-{'options','prefer'} or body.get('prefer') not in ('minimum','maximum'):raise ValueError('Supply options and prefer minimum or maximum')
 options=body.get('options')
 if not isinstance(options,list) or not 2<=len(options)<=12:raise ValueError('Compare 2–12 named explicit expressions')
 rows=[];names=set()
 for option in options:
  if not isinstance(option,dict) or set(option)!={'name','expression'} or not isinstance(option['name'],str) or not 1<=len(option['name'])<=80 or option['name'].casefold() in names:raise ValueError('Use distinct option names and explicit arithmetic expressions')
  names.add(option['name'].casefold());report=calculate(option['expression']);rows.append({'name':option['name'],'expression':option['expression'],'exact_result':report['exact_result'],'steps':report['steps']})
 values=[Fraction(r['exact_result']) for r in rows];best=(min if body['prefer']=='minimum' else max)(values);selected=[row['name'] for row,value in zip(rows,values) if value==best]
 from .native_work import digest
 receipt={'options':rows,'prefer':body['prefer'],'selected':selected,'best_exact':str(best)};receipt['receipt_sha256']=digest(receipt)
 work.state['calculation_comparison']=receipt;work.state['focus_kind']='calculation-comparison'
 return {'status':'complete','answer':'Selected '+', '.join(selected)+' with '+body['prefer']+' value '+str(best)+'.'+(' These alternatives tie exactly.' if len(selected)>1 else ''),'comparison':receipt,'model_calls':0,'scope':'Selection under the supplied arithmetic and preference only. Units, costs, uncertainty and omitted criteria are not inferred.'}
