"""Native goal interpretation and one source-linked working record per active task.

Only a small, explicit goal grammar is compiled. No model, host or network action.
"""
import copy,json,math,re
from fractions import Fraction

def digest(value):
 from .native_work import digest as hash_value
 return hash_value(value)

def stamp(goal):
 goal.pop('receipt_sha256',None);goal['receipt_sha256']=digest(goal);return goal

def verify(goal):
 if goal.get('receipt_sha256')!=digest({k:v for k,v in goal.items() if k!='receipt_sha256'}):raise ValueError('Active task changed without a matching receipt; submit the task again')

def view(goal):
 report={k:copy.deepcopy(goal[k]) for k in ('version','intent','phase','revision','data_sha256','missing','assumptions','completion_conditions','verification','corrections','model_calls','receipt_sha256','failure_reason') if k in goal}
 report['original_request']=goal['original_request'][:1000]
 report['input_records']=len(goal['data']) if isinstance(goal.get('data'),list) else 0
 report['plan']=[step[:300] for step in goal['plan']]
 report['intermediate_results']=[{k:copy.deepcopy(row[k]) for k in ('step','status','outcome','result_sha256') if k in row} for row in goal['intermediate_results']]
 if goal.get('result'):
  report['result']={k:copy.deepcopy(v) for k,v in goal['result'].items() if k!='code'}
  if 'code' in goal['result']:
   code=goal['result']['code'];report['result']['code']={'function':code.get('function'),'source_sha256':code.get('source_sha256'),'checks':{k:code.get('checks',{}).get(k) for k in ('passed','total','all_passed')}}
 return report

def parse(text):
 original=text.strip();preview=False
 if original.casefold().startswith('preview goal:'):preview=True;original=original.split(':',1)[1].strip()
 elif original.casefold().startswith('goal:'):original=original.split(':',1)[1].strip()
 original=re.sub(r'^(?:please|could you|can you)\s+','',original,flags=re.I)
 instruction,separator,raw=original.partition(':')
 intent=None
 aliases=[(r'(?:summari[sz]e|summari[sz]e and analyse) (?:these|my) (expenses|numbers)',lambda m:'Analyse these '+m[1].lower()),(r'(?:give me|write) a summary of (?:these|my) (expenses|numbers|values)',lambda m:'Analyse these '+('numbers' if m[1].lower()=='values' else m[1].lower())),(r'write python to deduplicate and sort these integers',lambda m:'Write Python to sort and remove duplicates from these integers')]
 for pattern,canonical in aliases:
  alias=re.fullmatch(pattern,instruction,re.I)
  if alias:instruction=canonical(alias);break
 if re.fullmatch(r'analy[sz]e these (expenses|numbers)(?: and write a summary)?',instruction,re.I):
  kind=re.fullmatch(r'analy[sz]e these (expenses|numbers)(?: and write a summary)?',instruction,re.I)[1].lower();intent=kind
 elif re.fullmatch(r'(?:read this passage and answer the question|answer this question from the passage)',instruction,re.I):intent='passage'
 elif re.fullmatch(r'compare these options',instruction,re.I):intent='comparison'
 elif re.fullmatch(r'write python to sort and remove duplicates from these integers',instruction,re.I):intent='integer-code'
 else:return None
 if len(text)>16000:raise ValueError('Use a goal request within 16000 characters')
 data=json.loads(raw) if separator and raw.strip() else None
 return {'intent':intent,'original_request':text,'data':data,'preview':preview}

def validate_data(intent,data):
 if data is None:return
 if intent=='passage':
  if not isinstance(data,dict) or set(data)-{'text','question','source'} or not isinstance(data.get('text'),str) or not 1<=len(data['text'])<=12000 or not isinstance(data.get('question'),str) or not 1<=len(data['question'])<=500 or not isinstance(data.get('source','supplied passage'),str) or not 1<=len(data.get('source','supplied passage'))<=120:raise ValueError('Supply passage text, question and optional source label; use at most 12000 text characters')
  return
 if intent=='comparison':
  if not isinstance(data,dict) or set(data)-{'options','prefer'} or not isinstance(data.get('options'),list) or not 2<=len(data['options'])<=12 or data.get('prefer','minimum') not in ('minimum','maximum'):raise ValueError('Supply 2–12 named expression options and an optional minimum/maximum preference')
  return
 if not isinstance(data,list) or not 1<=len(data)<=500 or len(json.dumps(data,allow_nan=False))>48000:raise ValueError('Supply 1–500 records within 48 KB')
 if intent in ('numbers','integer-code'):
  if any(type(v) not in ((int,) if intent=='integer-code' else (int,float)) or not math.isfinite(v) or len(str(v))>100 for v in data):raise ValueError('Supply finite numeric values; code goals currently require whole integers. Booleans and numeric strings are not converted.')
 else:
  if any(not isinstance(row,dict) or not row or len(row)>24 or any(not isinstance(k,str) or not 1<=len(k)<=80 or type(v) not in (str,int,float,bool,type(None)) for k,v in row.items()) for row in data):raise ValueError('Supply scalar object rows with named expense columns')

def prepare(spec,prior=None):
 validate_data(spec['intent'],spec['data'])
 goal={'version':1,'intent':spec['intent'],'original_request':spec['original_request'],'data':copy.deepcopy(spec['data']),'data_sha256':digest(spec['data']),'revision':(prior['revision']+1 if prior else 1),'corrections':copy.deepcopy(prior.get('corrections',[])) if prior else [],'phase':'awaiting-data','missing':[],'assumptions':[],'plan':[],'intermediate_results':[],'completion_conditions':[],'model_calls':0}
 if goal['data'] is None:goal['missing']=['data'];return stamp(goal)
 if goal['intent']=='passage':
  goal['phase']='planned';goal['plan']=['answer from source: '+json.dumps(goal['data'],ensure_ascii=False)];goal['completion_conditions']=['The entire passage is parsed within the supported source grammar.','The answer has complete, nonconflicting source support.'];goal['assumptions']=['Only supplied text is evidence; source attribution is not external verification.'];return stamp(goal)
 if goal['intent']=='comparison':
  if 'prefer' not in goal['data']:goal['phase']='awaiting-preference';goal['missing']=['minimum_or_maximum'];return stamp(goal)
  goal['phase']='planned';goal['plan']=['compare calculations: '+json.dumps(goal['data'],ensure_ascii=False)];goal['completion_conditions']=['Every option expression is checked exactly.','Selected options have the declared minimum or maximum value; ties are preserved.'];return stamp(goal)
 if goal['intent']=='expenses':
  columns=set.intersection(*(set(row) for row in goal['data']))
  amount=spec.get('amount_column','amount' if 'amount' in columns else None)
  if amount is None:goal['phase']='awaiting-column';goal['missing']=['amount_column'];goal['available_columns']=sorted(columns);return stamp(goal)
  if not isinstance(amount,str) or amount not in columns:raise ValueError('Choose a column present in every expense row')
  if any(type(row[amount]) not in (int,float) or not math.isfinite(row[amount]) or len(str(row[amount]))>100 for row in goal['data']):raise ValueError('The chosen expense column must contain finite numeric amounts in every row; missing values are not silently omitted')
  goal['amount_column']=amount;rows=goal['data'];field=amount
  goal['assumptions']=['Amounts are used with their supplied signs. Currency conversion, taxes and missing entries are not inferred.']
 elif goal['intent']=='numbers':rows=[{'value':v} for v in goal['data']];field='value'
 else:
  goal['phase']='planned';goal['plan']=['write Python to sort then deduplicate: '+json.dumps(goal['data'])];goal['completion_conditions']=['Generated Python passes bounded differential checks.','Output equals the sorted unique input integers.'];return stamp(goal)
 goal['plan']=['study table: '+json.dumps(rows,ensure_ascii=False)]
 for op in ('count','sum','mean','minimum','maximum'):goal['plan'].append('table query: '+json.dumps({'select':op,**({'field':field} if op!='count' else {})}))
 goal['completion_conditions']=['Every supplied row contributes once.','Count, total, mean and bounds match an exact check against the current source data.'];goal['phase']='planned'
 return stamp(goal)

def missing_reply(goal):
 if goal['phase']=='awaiting-data':question='Please provide task data: followed by JSON '+({'expenses':'expense rows.','numbers':'numeric values.','integer-code':'integer values.','passage':'with text and question.','comparison':'with named expression options.'}[goal['intent']])
 elif goal['phase']=='awaiting-preference':question='Should the smallest or largest expression value win? Reply prefer minimum or prefer maximum.'
 else:question='Which column contains expense amounts? Available in every row: '+(', '.join(goal.get('available_columns',[])) or 'none')+'. Reply use amount column NAME.'
 return {'status':'needs-input','answer':question,'goal':view(goal),'executed':False,'model_calls':0}

def execute(goal,work):
 verify(goal)
 if goal['phase']=='awaiting-intent':return {'status':'needs-input','answer':'Choose a supported goal before running this task.','model_calls':0}
 if goal['phase'] in ('awaiting-data','awaiting-column','awaiting-preference'):work.state['cognitive_goal']=copy.deepcopy(goal);work.state['focus_kind']='cognitive-goal';return missing_reply(goal)
 from .native_work import NativeWork
 from .shared_controller import respond as control
 trial=NativeWork(work.state)
 request='Work request:\n'+'\n'.join(str(i+1)+'. '+step for i,step in enumerate(goal['plan']))
 result=control(request,trial);record=copy.deepcopy(goal);record['intermediate_results']=copy.deepcopy(result['controller']['stages'])
 record['controller_receipt']=copy.deepcopy(result['controller']);record['phase']='blocked';record['verification']={'passed':False}
 if result['status']=='complete':
  if goal['intent']=='passage':
   evidence=result['controller']['stages'][-1]['outcome'];passed=evidence.get('complete') is True and evidence.get('status') in ('answered','refuted') and bool(evidence.get('answers') or evidence.get('counter_supporting_fact_ids')) and not evidence.get('counter_support_conflicted') and not any(a.get('has_conflicted_support') for a in evidence['answers']) and not evidence.get('unparsed_sentences')
   expected='Complete nonconflicting answer support from the supplied text';record['result']={'answers':evidence.get('answers',[]),'proof_graph':evidence.get('proof_graph',[]),'source_sha256':goal['data_sha256']}
   bindings=[a.get('bindings',{}) for a in evidence.get('answers',[])];summary='Answer from the supplied passage:\n'+('\n'.join(', '.join(k.lstrip('?').capitalize()+': '+str(v) for k,v in row.items()) for row in bindings) if any(bindings) else ('No. The supplied passage supports the opposite relation.' if evidence.get('status')=='refuted' else 'Yes. The supplied passage supports the stated relation.'))+'\nSource: '+goal['data'].get('source','supplied passage')+'.'
  elif goal['intent']=='comparison':
   comparison=result['controller']['stages'][-1]['outcome'];from .exact_numbers import calculate
   values=[Fraction(calculate(o['expression'])['exact_result']) for o in goal['data']['options']];best=(min if goal['data']['prefer']=='minimum' else max)(values);expected=[o['name'] for o,v in zip(goal['data']['options'],values) if v==best];passed=comparison.get('selected')==expected
   record['result']={'selected':comparison.get('selected'),'best_exact':str(best),'options':comparison.get('options',[]),'source_sha256':goal['data_sha256']};summary='Selected: '+', '.join(expected)+'. '+goal['data']['prefer'].capitalize()+' value: '+str(best)+'.'+(' Exact tie preserved.' if len(expected)>1 else '')
  elif goal['intent']=='integer-code':
   expected=sorted(set(goal['data']));code=trial.state.get('last_generated_code',{});passed=bool(code.get('checks',{}).get('all_passed')) and result['value']==expected
   record['result']={'value':result['value'],'code':copy.deepcopy(code)};summary='Checked Python for sorting and removing duplicates:\n```python\n'+code.get('source','')+'```\nVerified output: '+json.dumps(result['value'])
  else:
   values=[Fraction(str(row[goal['amount_column']])) for row in goal['data']] if goal['intent']=='expenses' else [Fraction(str(v)) for v in goal['data']]
   expected={'count':str(len(values)),'total':str(sum(values)),'mean':str(sum(values)/len(values)),'minimum':str(min(values)),'maximum':str(max(values))}
   actual={name:str(stage['outcome']) for name,stage in zip(('count','total','mean','minimum','maximum'),result['controller']['stages'][1:])}
   passed=actual==expected;record['result']={'metrics':actual,'source_sha256':goal['data_sha256']}
   summary=('Expenses summary' if goal['intent']=='expenses' else 'Numbers summary')+'\n'+'\n'.join(name.capitalize()+': '+value for name,value in actual.items())+'\nSource: '+str(len(values))+' supplied records, revision '+str(goal['revision'])+'.'
  record['verification']={'passed':passed,'expected':expected,'source_sha256':goal['data_sha256'],'scope':'Internal task-specific checks against the supplied source, not external verification of that source.'}
  if passed:
   record['phase']='complete';work.state.clear();work.state.update(trial.state);work.state['focus_kind']='cognitive-goal';work.state['previous']=copy.deepcopy(work.state.get('last'));work.state['last']=copy.deepcopy(record['result'].get('metrics',record['result'].get('value',record['result'].get('selected',record['result'].get('answers')))));work.state['has_last']=True;stamp(record);work.state['cognitive_goal']=record
   return {'status':'complete','answer':summary,'goal':view(record),'value':copy.deepcopy(record['result'].get('value')),'model_calls':0,'committed':True}
 record.pop('result',None);record['failure_reason']=result['answer'] if result['status']!='complete' else 'Task-specific outcome checks did not pass.'
 if goal['intent']=='passage' and record['intermediate_results']:
  evidence=record['intermediate_results'][-1].get('outcome') or {}
  if evidence.get('unparsed_sentences'):record['failure_reason']='The passage contains statements outside the supported source grammar. Clarify those statements before relying on a complete answer.'
  elif evidence.get('status')=='conflicting-support':record['failure_reason']='The passage contains conflicting support for this answer. Resolve the conflicting statements first.'
  elif evidence.get('status')=='unknown':record['failure_reason']='The supplied passage does not establish an answer to this question. Supply the missing relation or rule.'
 stamp(record);work.state['cognitive_goal']=record;work.state['focus_kind']='cognitive-goal'
 return {'status':'blocked','answer':record['failure_reason']+' Previous completed work is retained.','goal':view(record),'model_calls':0,'committed':False}

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');goal=work.state.get('cognitive_goal')
 if key in ('current task status','explain this task') or goal and work.state.get('focus_kind')=='cognitive-goal' and key in ('why is this verified','explain result plainly','explain the result plainly'):
  if not goal:return {'status':'needs-input','answer':'No interpreted task is active.','model_calls':0}
  verify(goal);answer='Task: '+goal['intent']+'. State: '+goal['phase']+'. Revision: '+str(goal['revision'])+'.\n'+'\n'.join(str(i+1)+'. '+step[:300] for i,step in enumerate(goal['plan']))
  if goal.get('result'):answer+='\nCurrent verified result: '+json.dumps(goal['result'].get('metrics',goal['result'].get('value',goal['result'].get('selected',goal['result'].get('answers')))))
  if goal.get('missing'):answer+='\nMissing: '+', '.join(goal['missing'])
  if goal.get('failure_reason'):answer+='\n'+goal['failure_reason']
  return {'status':'complete','answer':answer,'goal':view(goal),'action_repeated':False,'model_calls':0}
 if key=='run this task':
  if not goal:return {'status':'needs-input','answer':'Provide a supported goal first.','model_calls':0}
  verify(goal);return execute(goal,work)
 passage_question=re.fullmatch(r'ask this passage:\s*(.+)',text.strip(),re.I|re.S)
 option_change=re.fullmatch(r'change (?:alternative|option) (.+?) to (.+)',text.strip(),re.I|re.S)
 if goal and (passage_question and goal['intent']=='passage' or option_change and goal['intent']=='comparison'):
  verify(goal);data=copy.deepcopy(goal['data'])
  if data is None:return missing_reply(goal)
  if passage_question:data['question']=passage_question[1].strip()
  else:
   matches=[option for option in data['options'] if option.get('name','').casefold()==option_change[1].strip().casefold()]
   if len(matches)!=1:raise ValueError('Name one existing option to revise')
   matches[0]['expression']=option_change[2].strip()
  updated=prepare({'intent':goal['intent'],'data':data,'original_request':goal['original_request']},goal);updated['corrections']=(goal['corrections']+[{'instruction':text[:1000],'previous_data_sha256':goal['data_sha256'],'new_data_sha256':updated['data_sha256']}])[-8:];stamp(updated);return execute(updated,work)
 data_change=re.fullmatch(r'(replace task data|task data):\s*(.+)',text.strip(),re.I|re.S)
 column=re.fullmatch(r'use amount column (.+)',text.strip(),re.I)
 preference=re.fullmatch(r'prefer (minimum|maximum)',key)
 if preference and goal and goal['intent']=='comparison':
  verify(goal);data=copy.deepcopy(goal['data'])
  if data is None:return missing_reply(goal)
  data['prefer']=preference[1];updated=prepare({'intent':'comparison','data':data,'original_request':goal['original_request']},goal);updated['corrections']=(goal['corrections']+[{'instruction':text,'previous_data_sha256':goal['data_sha256'],'new_data_sha256':updated['data_sha256']}])[-8:];stamp(updated);return execute(updated,work)
 if data_change or column:
  if not goal:return {'status':'needs-input','answer':'Provide a supported goal before supplying its data or column.','model_calls':0}
  verify(goal)
  if goal['intent'] not in ('expenses','numbers','integer-code','passage','comparison'):return {'status':'needs-input','answer':'Provide a supported goal before supplying its data.','model_calls':0}
  if data_change:
   if data_change[1].casefold()=='task data' and goal['phase']!='awaiting-data':raise ValueError('Use replace task data to explicitly replace existing task input')
   new_data=json.loads(data_change[2]);spec={'intent':goal['intent'],'data':new_data,'original_request':goal['original_request'],**({'amount_column':goal['amount_column']} if 'amount_column' in goal else {})}
  else:
   if goal['intent']!='expenses':raise ValueError('An amount column applies only to an expense task')
   spec={'intent':goal['intent'],'data':goal['data'],'original_request':goal['original_request'],'amount_column':column[1].strip()}
  updated=prepare(spec,goal);updated['corrections']=(goal['corrections']+[{'instruction':text[:1000],'previous_data_sha256':goal['data_sha256'],'new_data_sha256':updated['data_sha256']}])[-8:];stamp(updated);return execute(updated,work)
 metric=re.fullmatch(r'(?:what is the|use task) (count|total|mean|minimum|maximum)',key)
 if metric and goal and work.state.get('focus_kind')=='cognitive-goal':
  verify(goal)
  if goal['phase']!='complete' or metric[1] not in goal.get('result',{}).get('metrics',{}):return {'status':'needs-input','answer':'Complete the current data-summary task before using that metric.','model_calls':0}
  value=goal['result']['metrics'][metric[1]]
  if key.startswith('use task'):
   from .exact_work import finish
   return finish(work,Fraction(value),[{'instruction':'selected '+metric[1]+' from verified task revision '+str(goal['revision']),'exact':value}],text)
  return {'status':'complete','answer':metric[1].capitalize()+': '+value,'exact_result':value,'source_sha256':goal['data_sha256'],'action_repeated':False,'model_calls':0}
 if goal and work.state.get('focus_kind')=='cognitive-goal' and goal['phase']!='complete' and re.match(r'^(?:now|then|convert that|why this choice)\b',key):return {'status':'needs-input','answer':'The current task is '+goal['phase']+'. Supply its missing information or run its plan before using a result.','model_calls':0}
 spec=parse(text)
 if spec is None:
  if key.startswith(('goal:','preview goal:')):
   unsupported={'version':1,'intent':'unsupported','original_request':text,'data':None,'data_sha256':digest(None),'revision':1,'corrections':[],'phase':'awaiting-intent','missing':['supported_goal'],'assumptions':[],'plan':[],'intermediate_results':[],'completion_conditions':[],'model_calls':0};stamp(unsupported);work.state['cognitive_goal']=unsupported;work.state['focus_kind']='cognitive-goal'
   return {'status':'needs-input','answer':'I can plan data summaries, supported source-passage questions, exact option comparisons, or Python that sorts and removes duplicate integers. Which is your task? Other goals need a supported explicit plan.','goal':view(unsupported),'model_calls':0}
  return None
 goal=prepare(spec)
 if spec['preview'] and goal['phase']=='planned':
  work.state['cognitive_goal']=copy.deepcopy(goal);work.state['focus_kind']='cognitive-goal'
  return {'status':'planned','answer':'Interpreted task: '+goal['intent']+'.\n'+'\n'.join(str(i+1)+'. '+step[:300] for i,step in enumerate(goal['plan']))+'\nNothing ran. Say run this task to execute.','goal':view(goal),'executed':False,'model_calls':0}
 return execute(goal,work)
