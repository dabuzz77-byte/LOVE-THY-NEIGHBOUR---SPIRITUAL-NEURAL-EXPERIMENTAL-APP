"""Named checked code snapshots; selecting a snapshot rechecks recorded examples."""
import copy,json,re

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');library=work.state.get('checked_functions',{})
 if key=='list saved functions':return {'status':'complete','answer':'\n'.join('- '+name+' → '+row['code']['function'] for name,row in library.items()) or 'No functions have been saved.','model_calls':0}
 match=re.fullmatch(r'(save function as|replace saved function|use saved function|forget saved function) ([a-z][a-z0-9_ -]{0,39})',key)
 if not match:return None
 action,name=match.groups();name=' '.join(name.split())
 from .native_work import digest
 if action in ('save function as','replace saved function'):
  code=work.state.get('last_generated_code')
  if not code or not code.get('usable',code.get('checks',{}).get('all_passed',False)) or code.get('counterexample_found'):raise ValueError('Save a generated function only after its retained checks pass')
  if digest(code['source']) in work.state.get('invalidated_function_sources',[]):raise ValueError('This function source has an unresolved failed check')
  if code.get('source_sha256')!=digest(code['source']):raise ValueError('Source changed after checking')
  if (action=='save function as')==(name in library):raise ValueError('Use an unused name to save, or explicitly replace an existing saved function')
  from .function_testing import test_function
  cases=copy.deepcopy(code.get('replay_cases',[]))
  if not cases:raise ValueError('This function lacks replayable examples; generate it again before saving')
  checked=test_function({'source':code['source'],'function':code['function'],'cases':cases})
  if not checked.get('all_passed'):raise ValueError('Recorded function examples no longer pass')
  row={'code':copy.deepcopy(code),'cases':cases};row['snapshot_sha256']=digest(row)
  updated={**library,name:row}
  if len(updated)>8 or len(json.dumps(updated,allow_nan=False))>196608:raise ValueError('Saved functions exceed the eight-function or 192 KB budget; forget a selected function first')
  work.state['checked_functions']=updated
  return {'status':'complete','answer':'Saved checked function '+name+'. Selecting it will rerun its recorded examples.','model_calls':0}
 if name not in library:raise ValueError('No saved function has that name')
 if action=='forget saved function':
  updated=copy.deepcopy(library);updated.pop(name);work.state['checked_functions']=updated
  return {'status':'complete','answer':'Forgot saved function '+name+'. The active function is unchanged.','model_calls':0}
 row=library[name]
 if row.get('snapshot_sha256')!=digest({k:v for k,v in row.items() if k!='snapshot_sha256'}):raise ValueError('Saved function snapshot changed; review and save it explicitly')
 code=copy.deepcopy(row['code'])
 if digest(code['source']) in work.state.get('invalidated_function_sources',[]):return {'status':'test-failed','answer':'This saved source has a later failed check. The active function was not replaced.','model_calls':0}
 if code.get('source_sha256')!=digest(code['source']):raise ValueError('Saved source does not match its receipt')
 from .function_testing import test_function
 checked=test_function({'source':code['source'],'function':code['function'],'cases':row['cases']})
 if not checked.get('all_passed'):return {'status':'test-failed','answer':'Saved examples failed. The active function was not replaced.','coding_result':checked,'model_calls':0}
 work.state['last_generated_code']=code;work.state['last_code_review']={'checks':checked,'scope':'Rechecked saved examples; this does not prove all-input correctness.'};work.state['focus_kind']='code'
 return {'status':'complete','answer':'Selected '+name+' after rechecking '+str(checked['total'])+' examples.','coding_result':checked,'model_calls':0}
