"""Named, source-hashed pure reasoning snapshots; restored models are recalculated."""
import copy,hashlib,json,re,time

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()
def respond(text,state):
 key=text.strip().casefold().rstrip('?.!');collection=state.get('reasoning_workspaces',{})
 if key=='list saved reasoning':return {'status':'complete','answer':'\n'.join('- '+name+' · '+r['spec'].get('mode','deduction')+' · saved '+r['saved_status'] for name,r in collection.items()) or 'No named reasoning models are saved.','model_calls':0}
 match=re.fullmatch(r'(save reasoning as|replace saved reasoning|resume reasoning|forget saved reasoning) ([a-z][a-z0-9_ -]{0,39})',key)
 if not match:return None
 action,name=match.groups();name=' '.join(name.split())
 if action in ('save reasoning as','replace saved reasoning'):
  spec=state.get('general_reasoning_spec');result=state.get('general_reasoning_result')
  if state.get('focus_kind')!='general-reasoning' or not spec or not result:raise ValueError('Select an active reasoning model before saving it')
  if action=='save reasoning as' and name in collection:raise ValueError('That name exists; use replace saved reasoning to replace it explicitly')
  if action=='replace saved reasoning' and name not in collection:raise ValueError('No saved model has that name')
  row={'spec':copy.deepcopy(spec),'input_sha256':digest(spec),'saved_status':result['status'],'scope':result.get('scope',''),'saved_at':time.time()};updated={**collection,name:row}
  if len(updated)>8 or len(json.dumps(updated,allow_nan=False))>131072:raise ValueError('Saved reasoning exceeds its eight-model or 128 KB budget; forget an explicitly selected model first')
  state['reasoning_workspaces']=updated
  return {'status':'saved','answer':'Saved the supplied model as '+name+'. Resuming will recalculate it rather than trust an old result.','model_calls':0}
 if name not in collection:raise ValueError('No saved reasoning model has that name')
 if action=='forget saved reasoning':
  updated=copy.deepcopy(collection);updated.pop(name);state['reasoning_workspaces']=updated;return {'status':'complete','answer':'Forgot the saved reasoning model '+name+'.','model_calls':0}
 row=collection[name]
 if digest(row['spec'])!=row['input_sha256']:raise ValueError('The saved model changed without a matching source receipt; review and save it explicitly')
 from .general_reasoning import reason,retain
 report=reason(copy.deepcopy(row['spec']));retain(state,row['spec'],report);state['focus_kind']='general-reasoning'
 return {'status':report['status'],'answer':'Recalculated saved model '+name+':\n'+json.dumps(report,ensure_ascii=False,indent=2),'general_reasoning':report,'restored_from':name,'model_calls':0}
