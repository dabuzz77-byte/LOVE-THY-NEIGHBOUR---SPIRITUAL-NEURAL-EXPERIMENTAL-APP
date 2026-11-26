"""Named reviewable native task bundles with revalidation and outcome receipts."""
import copy,json,re,time

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');library=work.state.get('saved_task_bundles',{})
 if key=='list saved tasks':return {'status':'complete','answer':'\n'.join('- '+name+' · '+str(len(row['body']['tasks']))+' stages' for name,row in library.items()) or 'No task bundles have been saved.','model_calls':0}
 if key in ('saved task status','explain last saved task'):
  attempt=work.state.get('last_saved_task_attempt')
  if not attempt:return {'status':'needs-input','answer':'No saved task has been run yet.','model_calls':0}
  return {'status':'complete','answer':'Task '+attempt['name']+': '+attempt['status']+'. '+('All stages committed.' if attempt['committed'] else 'No results from this attempt committed.')+'\n'+'\n'.join(row['id']+': '+row['status'] for row in attempt['stages'])+('\nStopped at: '+attempt['failed_task'] if attempt.get('failed_task') else ''),'attempt':copy.deepcopy(attempt),'failure_reason':attempt.get('failure_reason'),'action_repeated':False,'model_calls':0}
 definition=re.fullmatch(r'(define task|replace task) ([a-z][a-z0-9_ -]{0,39}):\s*(.+)',text.strip(),re.I|re.S)
 from .native_task_batch import validate,preview,run
 from .native_work import digest
 if definition:
  verb,name,raw=definition.groups();name=' '.join(name.casefold().split());body=json.loads(raw);validate(body)
  if (verb.casefold()=='define task')==(name in library):raise ValueError('Define an unused task name, or explicitly replace an existing task')
  row={'body':copy.deepcopy(body),'source_sha256':digest(body)};updated={**library,name:row}
  if len(updated)>8 or len(json.dumps(updated,allow_nan=False))>196608:raise ValueError('Saved tasks exceed eight bundles or 192 KB; forget a selected task first')
  work.state['saved_task_bundles']=updated
  return {'status':'complete','answer':'Saved '+name+' with '+str(len(body['tasks']))+' stages. Nothing ran. Preview or run saved task '+name+'.','executed':False,'model_calls':0}
 match=re.fullmatch(r'(preview saved task|run saved task|show saved task|forget saved task) ([a-z][a-z0-9_ -]{0,39})',key)
 if not match:return None
 verb,name=match.groups();name=' '.join(name.split())
 if name not in library:raise ValueError('No saved task has that name')
 row=library[name]
 if verb=='forget saved task':
  updated=copy.deepcopy(library);updated.pop(name);work.state['saved_task_bundles']=updated
  return {'status':'complete','answer':'Forgot saved task '+name+'. Completed results remain unchanged.','model_calls':0}
 if digest(row['body'])!=row['source_sha256']:raise ValueError('Saved task differs from its receipt; review and explicitly replace it')
 validate(row['body'])
 if verb=='show saved task':return {'status':'complete','answer':json.dumps(row['body'],ensure_ascii=False,indent=2),'executed':False,'model_calls':0}
 if verb=='preview saved task':return preview(copy.deepcopy(row['body']),work)
 result=run(copy.deepcopy(row['body']),work)
 attempt={'name':name,'source_sha256':row['source_sha256'],'status':result['status'],'committed':result.get('committed',False),'failed_task':result.get('failed_task'),'stages':[{'id':stage['id'],'status':stage['status']} for stage in result.get('outputs',[])],'time':time.time()}
 if not attempt['committed']:attempt['failure_reason']=result.get('answer','')[:1000]
 work.state['last_saved_task_attempt']=attempt
 return {**result,'saved_task':name,'attempt':copy.deepcopy(attempt)}
