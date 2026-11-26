"""Per-action review for the bottom section assistant; no blanket write grant."""
import json,threading,time,uuid
class ActionReview:
 def __init__(self):self.lock=threading.RLock();self.pending={}
 def request(self,job,operation):
  ident=uuid.uuid4().hex;entry={'id':ident,'operation':json.loads(json.dumps(operation)),'status':'awaiting-review'}
  with self.lock:self.pending[ident]=entry;job['permission_pending']=entry;job['phase']='awaiting permission'
  try:
   deadline=time.monotonic()+300
   while time.monotonic()<deadline:
    if job.get('status')!='running':raise PermissionError('Operation cancelled before execution')
    if entry['status']=='approved':return
    if entry['status']=='rejected':raise PermissionError('User declined this operation; nothing executed')
    time.sleep(.1)
   raise PermissionError('Permission request expired; nothing executed')
  finally:
   with self.lock:self.pending.pop(ident,None);job.pop('permission_pending',None)
 def resolve(self,value):
  with self.lock:
   entry=self.pending.get(value.get('id'))
   if not entry or entry['status']!='awaiting-review':raise ValueError('Request is no longer pending')
   entry['status']='approved' if value.get('approve') is True else 'rejected'
   return {'ok':True,'status':entry['status']}

def token_budget(native,context,output):
 native=max(2048,min(262144,int(native or 8192)));context=max(2048,min(native,int(context or 8192)));output=max(128,min(32768,context//2,int(output or 4096)))
 return {'native_context':native,'context_tokens':context,'output_tokens':output}
