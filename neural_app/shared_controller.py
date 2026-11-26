"""Bounded shared controller: interpret, stage, route, check, commit and explain."""
import copy,json,re,time

def route(text,work):
 from .investigation_dialogue import respond as investigation_response
 investigation=investigation_response(text,work.state)
 if investigation is not None:return investigation
 from .conversational_requests import normalize,arithmetic
 text=normalize(text)
 from .native_requests import resolve_clarification
 repair=resolve_clarification(text,work)
 if repair is not None:return repair
 from .workflow_revision import respond as revise_workflow
 revised=revise_workflow(text,work)
 if revised is not None:return revised
 numeric=arithmetic(text)
 if numeric is not None:return numeric
 from .study_reasoning import respond as study_response
 study=study_response(text,work.state)
 if study is not None:return study
 from .relational_induction import respond as relational_learning
 relation=relational_learning(text,work.state)
 if relation is not None:return relation
 if work.state.get('_controller_number') is not None:
  from fractions import Fraction
  instruction=re.sub(r'^(?:now|then)\s+','',text.strip().casefold()).rstrip('?.!')
  scalar=re.fullmatch(r'(double|halve|add|subtract|multiply by|divide by)(?:\s+([+-]?\d{1,12}(?:\.\d{1,12}|/\d{1,12})?))?',instruction)
  if scalar and ((scalar[1] in ('double','halve'))==(scalar[2] is None)):
   value=Fraction(work.state['_controller_number']);operand=Fraction(scalar[2]) if scalar[2] else 2
   if scalar[1] in ('double','multiply by'):value*=operand
   elif scalar[1] in ('halve','divide by'):value/=operand
   elif scalar[1]=='add':value+=operand
   else:value-=operand
   typed=int(value) if value.denominator==1 and work.state.get('_controller_number_kind')=='number' else str(value)
   return {'status':'complete','answer':str(value),'exact_result':str(value),'value':typed,'model_calls':0}
 from . import category_reasoning,table_work,proportional_reasoning,exact_work,calculation_comparison,formula_codegen,checked_function_library,function_batch_work,reasoning_workspace
 for module in (category_reasoning,table_work,proportional_reasoning,exact_work,calculation_comparison,formula_codegen,checked_function_library,function_batch_work):
  result=module.respond(text,work)
  if result is not None:return result
 # Single-function invocation is a pure bounded operation in practical_dialogue.
 if text.strip().casefold().startswith('run this function on:'):
  from .practical_dialogue import respond
  return respond(text,work)
 result=reasoning_workspace.respond(text,work.state)
 if result is not None:return result
 from .general_reasoning import request,reason,retain
 body=request(text,work.state.get('general_reasoning_spec'))
 if body is not None:
  result=reason(body);retain(work.state,body,result);work.state['focus_kind']='general-reasoning'
  return {**result,'answer':result.get('answer',json.dumps(result,ensure_ascii=False))}
 code=re.fullmatch(r'(?:write|create|generate) (?:a )?python(?: function)? (?:to|for)\s+(.+)',text,re.I|re.S)
 if code:
  from .native_task_batch import code_request
  return code_request(code[1],work)
 from .native_requests import compile_request,execute_request
 compiled=compile_request(text,work.state)
 if compiled:return execute_request(compiled,work)
 # Keep all stateful native reasoning families available to composed work.
 from . import practical_decisions,grounded_reading_dialogue,conversation_navigation,evidence_workbench,validated_forecast,concept_dialogue
 for module in (practical_decisions,grounded_reading_dialogue,conversation_navigation,evidence_workbench,validated_forecast,concept_dialogue):
  result=module.respond(text,work.state)
  if result is not None:return result
 from .broad_reasoning import respond as broad
 result=broad(text,work.state.get('broad_reasoning_result') if work.state.get('focus_kind')=='broad-reasoning' else None)
 if result is not None:
  work.state['broad_reasoning_result']=copy.deepcopy(result);work.state['focus_kind']='broad-reasoning'
  return result
 from .native_language_transfer import apply as learned_phrase
 learned=learned_phrase(text,work)
 if learned is not None:return learned
 from .native_reading_knowledge import respond as reading_knowledge
 return reading_knowledge(text,work.state)

def outcome(result):
 if 'study_analysis' in result:return result['study_analysis']['comparison']['exact_difference']
 if 'relation_prediction' in result:return result['relation_prediction']['prediction']
 if 'source_knowledge' in result:return [r['text'] for r in result['source_knowledge']['passages']]
 for key in ('value','exact_result','exact_values','exact_value'):
  if key in result:return copy.deepcopy(result[key])
 if 'table_result' in result:return result['table_result']['exact_result']
 if 'comparison' in result:return copy.deepcopy(result['comparison'])
 if result.get('mode')=='reading':return {k:copy.deepcopy(result[k]) for k in ('status','answers','proof_graph','complete','unparsed_sentences','conflicts','source_statements','counter_supporting_fact_ids','counter_support_conflicted') if k in result}
 if 'final_answer' in result:
  if result.get('reasoning_family') in ('exact-arithmetic','compositional-arithmetic'):
   from fractions import Fraction
   value=Fraction(result['final_answer']);return int(value) if value.denominator==1 else str(value)
  return result['final_answer']
 if 'concept_reasoning' in result:
  report=result['concept_reasoning']
  if report.get('answer_mode')=='count':return len(report['answers'])
  if report['status']=='refuted':return False
  answers=report.get('answers',[])
  if answers and all(not row['bindings'] for row in answers):return True
  if answers:return [next(iter(row['bindings'].values())) if len(row['bindings'])==1 else copy.deepcopy(row['bindings']) for row in answers]
 if 'decision' in result:return copy.deepcopy(result['decision'].get('selected',[]))
 if 'reading' in result:return [row['text'] for row in result['reading']['extracts']]
 if 'forecast' in result:return copy.deepcopy(result['forecast']['forecasts'])
 if 'research' in result:return copy.deepcopy(result['research']['passages'])
 return None

def succeeded(result):
 from .reasoning_case import accepted
 if result.get('status') in ('complete','saved','recorded','selected','forecast','evidence-found','source-answer'):return True
 if result.get('status')=='model-prediction' and 'relation_prediction' in result:return result['relation_prediction']['prediction'] is not None
 if result.get('status') in ('answered','refuted','counted') and 'concept_reasoning' in result:return result['concept_reasoning'].get('complete') is True and not any(a.get('has_conflicted_support') for a in result['concept_reasoning'].get('answers',[]))
 if result.get('status')=='answered' and 'reasoning_family' in result:return True
 return ('mode' in result and accepted(result)) or ('membership_types_examined' in result and result.get('status') in ('entailed','refuted'))

def normalize_request(text):
 """Recognise explicit user-authored lists, without splitting quoted task data."""
 match=re.match(r'^(answer these|do the following|please do the following|work through these):\s*\n(.+)',text.strip(),re.I|re.S)
 if match:
  lines=[line.strip() for line in match[2].splitlines() if line.strip()]
  steps=[]
  for line in lines:
   step=re.fullmatch(r'(?:[-*]|\d+[.)])\s+(.+)',line)
   if not step:return text
   steps.append(step[1])
  return 'Work request:\n'+'\n'.join(str(i)+'. '+step for i,step in enumerate(steps,1))
 if re.match(r'^first[, :]\s*',text,re.I) and '\n' in text:
  lines=[line.strip() for line in text.splitlines() if line.strip()];steps=[]
  for index,line in enumerate(lines):
   match=re.fullmatch(r'(first|then|next|finally)[,:]?\s+(.+)',line,re.I)
   if not match or (index==0)!=(match[1].casefold()=='first'):return text
   steps.append(match[2])
  return 'Work request:\n'+'\n'.join(str(i)+'. '+step for i,step in enumerate(steps,1))
 return text

def respond(text,work):
 original_text=text
 text=normalize_request(text)
 key=text.strip().casefold().rstrip('?.!')
 revision=re.fullmatch(r'revise controller step (\d+):\s*(.+)',text.strip(),re.I|re.S)
 if revision or key=='retry controller':
  from .native_work import digest
  plan=work.state.get('controller_plan')
  if not plan:return {'status':'needs-input','answer':'Submit a numbered work request first.','model_calls':0}
  if plan.get('source_sha256')!=digest({k:v for k,v in plan.items() if k!='source_sha256'}):raise ValueError('Controller plan changed without a matching receipt; submit it again')
  if revision:
   index=int(revision[1])-1
   if not 0<=index<len(plan['steps']) or '\n' in revision[2] or len(revision[2])>16000:raise ValueError('Revise one existing step with one bounded instruction')
   updated=copy.deepcopy(plan);updated['steps'][index]=revision[2];updated.pop('source_sha256');updated['source_sha256']=digest(updated);work.state['controller_plan']=updated
   return {'status':'planned','answer':'Revised step '+str(index+1)+'. Nothing ran. Say retry controller to rerun the complete plan with its completion condition.','executed':False,'model_calls':0}
  request='Work request:\n'+'\n'.join(str(i+1)+'. '+s for i,s in enumerate(plan['steps']))+('\nExpect final: '+json.dumps(plan['expected']) if plan['has_expected'] else '')
  return respond(request,work)
 if key in ('controller status','explain controller run'):
  receipt=work.state.get('controller_attempt')
  if not receipt:return {'status':'needs-input','answer':'No controller request has run.','model_calls':0}
  return {'status':'complete','answer':receipt['summary'],'controller':copy.deepcopy(receipt),'action_repeated':False,'model_calls':0}
 match=re.match(r'^(preview )?work request:\s*\n(.+)',text.strip(),re.I|re.S)
 if not match:return None
 lines=[line.strip() for line in match[2].splitlines() if line.strip()];steps=[];expected=None;has_expected=False
 for line in lines:
  expectation=re.fullmatch(r'Expect final:\s*(.+)',line,re.I)
  if expectation:
   if has_expected:raise ValueError('Supply one final expected value')
   expected=json.loads(expectation[1]);has_expected=True;continue
  number=re.fullmatch(r'(\d+)\.\s+(.+)',line)
  if not number or int(number[1])!=len(steps)+1 or has_expected:raise ValueError('Use consecutive numbered instructions followed by an optional Expect final: JSON')
  steps.append(number[2])
 if not 1<=len(steps)<=8 or len(text)>16000:raise ValueError('Use 1–8 numbered steps within 16000 characters')
 from .native_work import NativeWork,digest
 if match[1]:return {'status':'planned','answer':'Planned '+str(len(steps))+' native stages:\n'+'\n'.join(str(i+1)+'. '+s for i,s in enumerate(steps))+'\nNo stage ran. Submit the same request without preview to execute.','steps':steps,'executed':False,'model_calls':0}
 trial=NativeWork(work.state);rows=[];deadline=time.monotonic()+4;status='complete';value=None;error=None
 for index,instruction in enumerate(steps,1):
  try:
   if time.monotonic()>deadline:raise ValueError('Controller time budget reached')
   result=route(instruction,trial)
   if result is None:raise ValueError('Unsupported instruction; use a supported calculation, table question, logic model, code request or pure data operation')
   stage_passed=succeeded(result)
   rows.append({'step':index,'instruction':instruction,'status':result.get('status'),'answer':result.get('answer','')[:4000],'result_sha256':digest(result),'outcome':outcome(result)})
   if not stage_passed:raise ValueError(result.get('answer','Stage needs clarification or validation'))
   value=outcome(result)
   trial.state.pop('_controller_number',None)
   trial.state.pop('_controller_number_kind',None)
   if result.get('reasoning_family') in ('exact-arithmetic','compositional-arithmetic') or 'exact_result' in result:
    from fractions import Fraction
    try:trial.state['_controller_number']=str(Fraction(result.get('exact_result',result.get('final_answer'))))
    except (ValueError,TypeError,ZeroDivisionError):pass
   elif type(value) in (int,float):trial.state['_controller_number']=str(value)
   if trial.state.get('_controller_number') is not None:trial.state['_controller_number_kind']='number' if type(value) in (int,float) else 'exact-text'
   if value is not None:
    trial.state['previous']=copy.deepcopy(trial.state.get('last'));trial.state['last']=copy.deepcopy(value);trial.state['has_last']=True
   else:trial.state['has_last']=False
   if len(json.dumps(rows,allow_nan=False))>65536:raise ValueError('Controller output budget reached')
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError,SyntaxError,RecursionError) as exc:
   status='blocked';error='Stage '+str(index)+': '+str(exc)[:700];break
 if status=='complete' and has_expected:
  from .workflow_contracts import equivalent
  if not equivalent(value,expected):status='acceptance-failed';error='Final output did not match the supplied completion condition.'
 committed=status=='complete';summary=('Completed all '+str(len(steps))+' stages.' if committed else error+' No staged results were committed.')
 receipt={'status':status,'committed':committed,'stages':rows,'summary':summary,'request_sha256':digest(original_text),'normalized_request_sha256':digest(text),'has_expected':has_expected,'expected':expected if has_expected else None,'actual':copy.deepcopy(value),'scope':'Native supported skills only; no host or network action. Stage-level deadlines are cooperative. No model calls.','model_calls':0}
 if committed:
  trial.state.pop('_controller_number',None);trial.state.pop('_controller_number_kind',None);work.state.clear();work.state.update(trial.state)
 plan={'steps':steps,'expected':expected,'has_expected':has_expected};plan['source_sha256']=digest(plan);work.state['controller_plan']=plan
 work.state['controller_attempt']=copy.deepcopy(receipt)
 details='\n\n'.join('**Step '+str(row['step'])+'**\n'+row['answer'] for row in rows)
 return {'status':status,'answer':summary+('\n\n'+details if details else ''),'value':value if committed else None,'controller':receipt,'committed':committed,'model_calls':0}
