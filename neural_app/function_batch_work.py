"""All-or-nothing invocation of retained checked functions on multiple inputs."""
import copy,json,time

def respond(text,work):
 key=text.strip().casefold()
 preview=key.startswith('preview this function for:')
 if not preview and not key.startswith('run this function for:'):return None
 from .function_testing import FunctionTest,data_budget,ProgramRaised
 from .native_work import digest
 code=work.state.get('last_generated_code')
 if not code or not code.get('usable',code.get('checks',{}).get('all_passed',False)) or code.get('counterexample_found'):return {'status':'needs-input','answer':'Generate a function with passing retained checks first.','model_calls':0}
 if digest(code['source']) in work.state.get('invalidated_function_sources',[]):raise ValueError('This source has an unresolved failed check; generate and check a corrected function')
 if code.get('source_sha256')!=digest(code['source']):raise ValueError('Source changed after its checked receipt; regenerate and test it')
 inputs=json.loads(text.split(':',1)[1])
 if not isinstance(inputs,list) or not 1<=len(inputs)<=24 or any(not isinstance(args,list) for args in inputs) or len(json.dumps(inputs,allow_nan=False))>16384:raise ValueError('Supply 1–24 JSON argument lists within 16 KB')
 data_budget(inputs)
 if preview:return {'status':'planned','answer':'Ready to apply '+code['function']+' to '+str(len(inputs))+' argument lists. Nothing has run.','function':code['function'],'input_sha256':digest(inputs),'source_sha256':digest(code['source']),'invocations':len(inputs),'executed':False,'model_calls':0}
 rows=[];deadline=time.monotonic()+2
 for index,args in enumerate(inputs):
  try:
   if time.monotonic()>=deadline:raise ValueError('Batch computation deadline reached')
   runner=FunctionTest(code['source']);runner.deadline=min(runner.deadline,deadline);value=runner.invoke(code['function'],copy.deepcopy(args));data_budget(value)
   rows.append({'index':index,'args_sha256':digest(args),'value':value,'steps':runner.steps})
   if len(json.dumps(rows,allow_nan=False))>65536:raise ValueError('Batch output exceeds 64 KB')
  except (ValueError,TypeError,IndexError,KeyError,ZeroDivisionError,OverflowError,RuntimeError,RecursionError,ProgramRaised) as exc:
   return {'status':'failed','answer':'Function batch stopped at input '+str(index+1)+': '+type(exc).__name__+'. No batch results were committed.','failed_input':index,'error':str(exc)[:300],'completed_before_failure':index,'committed':False,'host_access':False,'model_calls':0}
 values=[row['value'] for row in rows];receipt={'function':code['function'],'source_sha256':digest(code['source']),'input_sha256':digest(inputs),'output_sha256':digest(values),'rows':rows}
 work.state['previous']=copy.deepcopy(work.state.get('last'));work.state['last']=copy.deepcopy(values);work.state['has_last']=True;work.state['last_function_batch']=copy.deepcopy(receipt);work.state['focus_kind']='function-batch'
 return {'status':'complete','answer':json.dumps(values,ensure_ascii=False),'value':values,'function_batch':receipt,'committed':True,'host_access':False,'model_calls':0}
