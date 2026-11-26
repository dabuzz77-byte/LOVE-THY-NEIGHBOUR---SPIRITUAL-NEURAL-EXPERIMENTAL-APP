"""Typed reasoning-episode commands on the existing authenticated input bus."""
import collections,copy,hashlib,json,threading,time
from .sphere_functions import PROFILES

class EpisodeBus:
 def __init__(self):self.lock=threading.RLock();self.queue=collections.deque();self.seen=collections.OrderedDict();self.results=collections.deque(maxlen=64);self.pending=[]
 def observe(self,event):
  p=event.get('payload');target=event.get('target','all')
  if event.get('kind')!='input' or not isinstance(p,dict) or 'reasoning_episode' not in p:return
  body=p['reasoning_episode'];ident=p.get('command_id')
  with self.lock:
   if not isinstance(ident,str) or not 1<=len(ident)<=80:self.receipt(None,'rejected','A bounded command_id is required');return
   digest=hashlib.sha256(json.dumps(body,sort_keys=True,allow_nan=False).encode()).hexdigest()
   if ident in self.seen:
    if self.seen[ident]!=digest:self.receipt(ident,'rejected','command_id was reused with a different command')
    return
   if target not in ('all','intelligence-engine','reasoning-episode',*PROFILES):self.receipt(ident,'rejected','Unknown reasoning destination');return
   if not isinstance(body,dict) or len(json.dumps(body,allow_nan=False))>45000:self.receipt(ident,'rejected','Invalid episode command');return
   if len(self.queue)>=32:self.receipt(ident,'rejected','Episode input queue is full; retry later');return
   self.seen[ident]=digest
   while len(self.seen)>512:self.seen.popitem(last=False)
   self.queue.append({'id':ident,'digest':digest,'body':copy.deepcopy(body),'target':target,'parent_event':event.get('sequence'),'origin':event.get('origin')})
 def receipt(self,ident,status,message,**extra):
  row={'command_id':ident,'status':status,'message':message,'time':time.time(),**extra};self.results.append(row)
  self.pending.append({'origin':'reasoning-episode-bus','target':'all','kind':'stage-output','payload':{**row,'processing_receipt':True}});self.pending=self.pending[-64:]
 def apply(self,state):
  with self.lock:
   if not self.queue:return False
   row=self.queue.popleft()
  try:
   ledger=state.setdefault('episode_bus_commands',{})
   if row['id'] in ledger:
    with self.lock:self.receipt(row['id'],'duplicate' if ledger[row['id']]==row['digest'] else 'rejected','Persisted command ID has already been processed')
    return True
   from .reasoning_episode import command
   result=command(state,row['body'])
   ledger[row['id']]=row['digest']
   while len(ledger)>512:ledger.pop(next(iter(ledger)))
   with self.lock:self.receipt(row['id'],'applied','Typed episode command applied',episode_id=(result or {}).get('id'),episode_status=(result or {}).get('status'),target=row['target'],parent_event=row['parent_event'])
  except (ValueError,TypeError,KeyError,OverflowError) as exc:
   with self.lock:self.receipt(row['id'],'rejected',str(exc)[:240],parent_event=row['parent_event'])
  return True
 def view(self):
  with self.lock:return {'queued':len(self.queue),'recent':copy.deepcopy(list(self.results)),'targets':['all','intelligence-engine','reasoning-episode',*PROFILES],'operations':['start','observe','status','cancel'],'transport':'Existing input bus; listener port and authentication unchanged.'}
 def drain(self):
  with self.lock:rows=self.pending;self.pending=[];return rows
