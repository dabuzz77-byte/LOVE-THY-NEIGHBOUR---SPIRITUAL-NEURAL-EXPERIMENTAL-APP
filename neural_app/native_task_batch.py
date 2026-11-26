"""Transactional composition of bounded reasoning, data work and Python exports."""
import copy,json,time,math

def input_binding(binding,outputs):
 from .reasoning_case import path_get
 from .native_work import digest
 from .scenario_reasoning import number
 row=next((r for r in outputs if r['id']==binding['task']),None)
 if row is None or row['status']!='complete':raise ValueError('Input binding requires an earlier completed task')
 value=copy.deepcopy(path_get(row,binding['path']));conversion=binding.get('convert','preserve')
 exact=None
 if conversion=='number':
  exact=number(value)
  value=int(exact) if exact.denominator==1 else float(exact)
  if type(value)is float and (not math.isfinite(value) or number(value)!=exact):raise ValueError('The referenced rational cannot be represented faithfully by this workflow; keep it in exact reasoning')
 elif conversion!='preserve':raise ValueError('Choose preserve or number for input binding conversion')
 return value,{'task':binding['task'],'path':binding['path'],'conversion':conversion,'exact_value':str(exact) if exact is not None else None,'source_output_sha256':digest(row),'value_sha256':digest(value)}

def code_request(request,work):
 from .native_requests import compile_request,execute_request
 from .native_work import python_export
 compiled=compile_request(request,work.state)
 if not compiled:return {'status':'needs-input','answer':'Supply a supported data transformation with explicit input, for example write Python to sort then deduplicate: [3,1,3].'}
 if compiled.get('clarification'):return compiled
 if compiled['preview']:return {'status':'needs-input','answer':'A code request needs a concrete transformation rather than a preview.'}
 # Do not commit the data result unless code generation and checks also succeed.
 trial=type(work)(work.state);result=execute_request(compiled,trial)
 if result['status']!='complete':return result
 exported=python_export(compiled['steps'],compiled['input'],result['value'])
 trial.state['focus_kind']='code';trial.state['last_code_review']={k:copy.deepcopy(exported[k]) for k in ('source_sha256','checks','scope')}
 trial.state['last_generated_code']={**copy.deepcopy(exported),'function':'transform','extra_checks':[]}
 work.state.clear();work.state.update(trial.state)
 return {'status':'complete','answer':'```python\n'+exported['source']+'```\n\nChecked '+str(exported['checks']['passed'])+' function cases.','code':exported,'value':result['value'],'model_calls':0}

def code_followup(text,work):
 key=text.casefold().strip().rstrip('?.!')
 if key not in ('show current code','show generated code') and not key.startswith('test this code:'):return None
 code=work.state.get('last_generated_code')
 if not code:return {'status':'needs-input','answer':'Generate a supported Python function first, then supply new test cases.','model_calls':0}
 if key.startswith('test this code:'):
  from .function_testing import test_function
  from .native_work import digest
  body=json.loads(text.split(':',1)[1])
  if not isinstance(body,dict) or set(body)!={'cases'}:raise ValueError('Provide only cases to test the retained generated function')
  checks=test_function({'source':code['source'],'function':code['function'],'cases':body['cases']})
  compact={k:copy.deepcopy(checks[k]) for k in ('passed','total','all_passed','source_sha256','scope') if k in checks}
  compact['cases']=[{**{k:r[k] for k in ('case','passed','error','exception','expected_exception') if k in r},'actual_preview':str(r.get('actual'))[:160],'expected_preview':str(r.get('expected'))[:160],'actual_sha256':digest(r.get('actual')),'expected_sha256':digest(r.get('expected'))} for r in checks.get('cases',[])]
  compact['full_result_retained']=False
  code['extra_checks']=(code.get('extra_checks',[])+[compact])[-8:]
  # A later passing sample must not erase an earlier counterexample.
  code['usable']=code['checks']['all_passed'] and all(r.get('all_passed') is True for r in code['extra_checks'])
  if not checks.get('all_passed'):
   code['counterexample_found']=True
   rejected=set(work.state.get('invalidated_function_sources',[]));rejected.add(digest(code['source']));work.state['invalidated_function_sources']=sorted(rejected)
  code['usable']=code['usable'] and not code.get('counterexample_found',False)
  work.state['last_code_review']={'source_sha256':code['source_sha256'],'checks':copy.deepcopy(compact),'all_retained_checks_passed':code['usable'],'scope':'New examples check the retained generated source; no repair or external action ran.'};work.state['focus_kind']='code'
  return {'status':'complete' if code['usable'] else 'test-failed','answer':'Additional function checks: '+str(checks.get('passed',0))+'/'+str(checks.get('total',0))+'. '+('All retained checks pass.' if code['usable'] else 'A counterexample or unsupported test remains; this code is not certified by the current checks.'),'coding_result':checks,'code_source_sha256':digest(code['source']),'model_calls':0}
 usable=code.get('usable',code['checks']['all_passed'])
 return {'status':'complete' if usable else 'test-failed','answer':'```python\n'+code['source']+'```\n\n'+('Passed its recorded bounded checks.' if usable else 'A later check failed; review the recorded counterexample.'),'code':copy.deepcopy(code),'model_calls':0}

def validate(body):
 if not isinstance(body,dict) or len(json.dumps(body,allow_nan=False))>32768:raise ValueError('Use a task bundle up to 32 KB')
 tasks=body.get('tasks')
 if not isinstance(tasks,list) or not 1<=len(tasks)<=8:raise ValueError('A task bundle needs 1–8 tasks')
 ids=set()
 for task in tasks:
  if not isinstance(task,dict) or not isinstance(task.get('id'),str) or not task['id'].isidentifier() or len(task['id'])>40 or task['id'] in ids or task.get('kind') not in ('workflow','reasoning','python'):raise ValueError('Use distinct task identifiers and workflow, reasoning or python kinds')
  binding=task.get('input_from')
  if binding is not None:
   if task['kind']=='reasoning' or not isinstance(binding,dict) or not isinstance(binding.get('task'),str) or binding['task'] not in ids or not isinstance(binding.get('path'),list) or not 1<=len(binding['path'])<=8 or any(type(p) not in (str,int) for p in binding['path']) or binding.get('convert','preserve') not in ('preserve','number'):raise ValueError('Input bindings need an earlier task, a bounded result path and an optional number conversion')
  ids.add(task['id'])
  cases=task.get('validation_cases')
  if cases is not None:
   if task['kind']=='reasoning' or not isinstance(cases,list) or not 1<=len(cases)<=8:raise ValueError('Use 1–8 fresh validation cases for workflow or python tasks')
   for case in cases:
    if not isinstance(case,dict) or set(case)!={'input','expected'} or len(json.dumps(case,allow_nan=False))>8192:raise ValueError('Validation cases need bounded input and expected values only')
   signatures=[json.dumps(c['input'],sort_keys=True,allow_nan=False) for c in cases]
   if len(set(signatures))!=len(signatures):raise ValueError('Use distinct validation inputs')
 return tasks

def validate_output(task,result,work,deadline):
 cases=task.get('validation_cases')
 if not cases:return result
 from .reasoning_engine import pipeline
 from .workflow_contracts import equivalent
 from .native_work import digest
 workflow=work.state['workflow'];rows=[]
 if any(digest(c['input'])==digest(workflow['input']) for c in cases):raise ValueError('Fresh validation inputs must differ from the primary task input')
 for index,case in enumerate(cases):
  if time.monotonic()>deadline:raise ValueError('Task validation computation budget reached')
  try:
   actual=pipeline(copy.deepcopy(case['input']),workflow['steps'])['result'];passed=equivalent(actual,case['expected'])
   rows.append({'case':index+1,'passed':passed,'input_sha256':digest(case['input']),'actual':actual,'expected':case['expected']})
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:rows.append({'case':index+1,'passed':False,'error':str(exc)[:300]})
 code_checks=None
 if task['kind']=='python':
  from .function_testing import test_function
  code_checks=test_function({'source':result['code']['source'],'function':'transform','cases':[{'args':[copy.deepcopy(c['input'])],'expected':copy.deepcopy(c['expected'])} for c in cases]})
 passed=all(r['passed'] for r in rows) and (code_checks is None or code_checks['all_passed'])
 checks={'all_passed':passed,'passed':sum(r['passed'] for r in rows),'total':len(rows),'cases':rows,'code_checks':code_checks,'scope':'Explicit fresh caller-supplied input/output checks; generated Python is also evaluated by the separate bounded interpreter.'}
 result['validation']=checks
 if not passed:result.update(status='validation-failed',answer='Fresh validation failed for '+task['id']+'. No bundle result will be committed.')
 return result

def preview(body,work):
 tasks=validate(body);work.state['previewed_tasks']=copy.deepcopy(body);work.state['focus_kind']='task-preview'
 return {'status':'planned','answer':'Planned native tasks:\n'+'\n'.join(str(i+1)+'. '+t['id']+' · '+t['kind']+(' · input from '+t['input_from']['task'] if t.get('input_from') else '') for i,t in enumerate(tasks))+'\nNo task has run. Say run previewed tasks to execute the bundle.','task_count':len(tasks),'executed':False,'model_calls':0}

def run(body,work):
 from .general_reasoning import reason,retain
 from .native_requests import compile_request,execute_request
 from .native_work import NativeWork,digest
 tasks=validate(body)
 trial=NativeWork(work.state);outputs=[];deadline=time.monotonic()+3
 for task in tasks:
  binding_receipt=None
  try:
   if time.monotonic()>deadline:raise ValueError('Task bundle time budget reached')
   if task['kind']=='reasoning':
    spec=task.get('task');report=reason(spec)
    from .reasoning_case import accepted
    if not accepted(report):
     result={'status':'unresolved','answer':'Reasoning did not establish a complete usable conclusion.','general_reasoning':report}
    else:
     retain(trial.state,spec,report);result={'status':'complete','general_reasoning':report,'answer':json.dumps(report,ensure_ascii=False,indent=2)}
   else:
    request=task.get('request')
    if not isinstance(request,str) or not request.strip() or len(request)>16000:raise ValueError('Provide a bounded transformation request')
    if task.get('input_from') is not None:
     from .instruction_clauses import partition_input
     if partition_input(request)[1]:raise ValueError('Use either an input binding or literal request input, not both')
     value,binding_receipt=input_binding(task['input_from'],outputs);trial.state['last']=value;trial.state['has_last']=True
    if task['kind']=='python':result=code_request(request,trial)
    else:
     compiled=compile_request(request,trial.state)
     result=execute_request(compiled,trial) if compiled else {'status':'needs-input','answer':'No supported transformation matched the request.'}
   if result['status']=='complete':result=validate_output(task,result,trial,deadline)
   outputs.append({'id':task['id'],**result,**({'input_binding':binding_receipt} if binding_receipt else {})})
   if result['status']!='complete':return {'status':'blocked','answer':'Stopped at '+task['id']+'. No changes from this bundle were committed.\n'+result['answer'],'committed':False,'outputs':outputs,'failed_task':task['id'],'model_calls':0}
   if len(json.dumps(outputs,allow_nan=False))>131072:raise ValueError('Task bundle output exceeds 128 KB')
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError,SyntaxError) as exc:
   return {'status':'blocked','answer':'Stopped at '+task['id']+': '+str(exc)[:500]+'. No changes from this bundle were committed.','committed':False,'outputs':outputs,'failed_task':task['id'],'model_calls':0}
 receipt={'tasks':[{'id':o['id'],'status':o['status'],'output_sha256':digest(o)} for o in outputs],'time':time.time(),'scope':'Pure native computations committed together to conversation working memory only; no file, network or host action was run.'}
 trial.state['last_task_bundle']=receipt;trial.state['focus_kind']='task-bundle';work.state.clear();work.state.update(trial.state)
 return {'status':'complete','answer':'\n\n'.join('**'+o['id']+'**\n'+o['answer'] for o in outputs),'committed':True,'outputs':outputs,'receipt':receipt,'model_calls':0}
