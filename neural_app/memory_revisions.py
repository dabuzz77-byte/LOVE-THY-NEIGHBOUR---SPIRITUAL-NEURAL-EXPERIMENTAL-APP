"""Explicit named-memory revisions. Local state only; no passive account capture."""
import copy,re,time

def update(state,key,value):
 key=key.strip()[:100];value=value.strip()[:4000]
 if not key:raise ValueError('Name the information to remember')
 memories=state.setdefault('memories',{});actual=next((k for k in memories if k.casefold()==key.casefold()),key);old=memories.get(actual)
 if old and old.get('value')!=value:
  history=state.setdefault('memory_revisions',{});history[actual]=(history.get(actual,[])+[copy.deepcopy(old)])[-8:]
  while len(history)>128:history.pop(next(iter(history)))
 memories[actual]={'value':value,'provenance':'user-reported','time':time.time()}
 while len(memories)>128:
  removed=next(iter(memories));memories.pop(removed);state.setdefault('memory_revisions',{}).pop(removed,None)
 return {'key':actual,'updated':old is not None and old.get('value')!=value,'revision_count':len(state.get('memory_revisions',{}).get(actual,[]))}

def respond(text,state):
 restore=re.fullmatch(r'restore (?:my |memory )?(.+?) (?:revision )?(\d+)',text,re.I)
 if restore:
  key=restore[1].strip().casefold();actual=next((k for k in state.get('memories',{}) if k.casefold()==key),None)
  history=state.get('memory_revisions',{}).get(actual,[]);index=int(restore[2])
  if actual is None or not 1<=index<=len(history):raise ValueError('Choose a retained revision from memory history, numbered oldest first')
  value=history[index-1]['value'];result=update(state,actual,value)
  return {**result,'restored_revision':index,'answer':'Restored '+actual+' from retained revision '+str(index)+'. The replaced value remains in history.','model_calls':0}
 change=re.fullmatch(r'update my (.+?) to ([\s\S]+)',text,re.I)
 if change:return {**update(state,change[1],change[2]),'answer':'Updated '+change[1].strip()+'.'}
 timeline=re.fullmatch(r'(?:memory history|what was my) (.+?)[?]?',text,re.I)
 if not timeline:return None
 key=timeline[1].strip().rstrip('?').casefold();memories=state.get('memories',{});actual=next((k for k in memories if k.casefold()==key),None)
 if actual is None:return {'answer':'No named memory matches that name.','found':False}
 return {'key':actual,'current':copy.deepcopy(memories[actual]),'previous':copy.deepcopy(state.get('memory_revisions',{}).get(actual,[])),'scope':'Explicit user-reported revisions, not independent verification of their contents','model_calls':0}
