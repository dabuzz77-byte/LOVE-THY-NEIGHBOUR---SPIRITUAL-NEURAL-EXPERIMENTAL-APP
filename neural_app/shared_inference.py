"""One process-wide local inference queue and bounded episodic working memory."""
import threading,time,itertools,json,hashlib
from contextlib import contextmanager
from pathlib import Path
class SharedInference:
 def __init__(self):
  self.cv=threading.Condition();self.tickets=[];self.serial=itertools.count();self.active=None;self.completed=0;self.memory=[];self.path=None
 def configure(self,data):
  path=Path(data)/'central-mind-memory.json'
  with self.cv:
   if self.path==path:return
   self.path=path
   try:self.memory=json.loads(path.read_text(encoding='utf-8'))[-40:]
   except (OSError,ValueError):self.memory=[]
 @contextmanager
 def slot(self,role='conversation',background=False,cancelled=lambda:False):
  ticket=(1 if background else 0,next(self.serial),str(role)[:100]);start=time.monotonic()
  with self.cv:
   if len(self.tickets)>=64:raise ValueError('The shared model queue is full; retry shortly.')
   self.tickets.append(ticket)
   try:
    while self.active is not None or ticket!=min(self.tickets):
     if cancelled():raise ValueError('Model request cancelled while queued.')
     self.cv.wait(.1)
    if cancelled():raise ValueError('Model request cancelled while queued.')
    self.tickets.remove(ticket);self.active={'role':ticket[2],'background':background,'started':time.time(),'queued_seconds':time.monotonic()-start}
   except BaseException:
    self.tickets.remove(ticket);self.cv.notify_all();raise
  try:yield
  finally:
   with self.cv:self.active=None;self.completed+=1;self.cv.notify_all()
 def remember(self,role,question,answer,receipts=()):
  row={'time':time.time(),'role':role,'request':str(question)[-1200:],'answer':str(answer)[:1800],'receipts':list(receipts)[-8:]}
  with self.cv:
   self.memory=(self.memory+[row])[-40:]
   if self.path:
    self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.memory,default=str),encoding='utf-8');temp.replace(self.path)
 def relevant(self,query,limit=3):
  words=set(str(query).lower().split());rows=list(self.memory)
  ranked=sorted(enumerate(rows),key=lambda v:(len(words&set((v[1]['request']+' '+v[1]['answer']).lower().split())),v[0]),reverse=True)
  return [r for _,r in ranked[:limit] if words&set((r['request']+' '+r['answer']).lower().split())]
 def view(self):
  with self.cv:return {'active':dict(self.active) if self.active else None,'queued':[{'priority':'background' if t[0] else 'user','role':t[2]} for t in sorted(self.tickets)],'completed':self.completed,'memory_entries':len(self.memory),'recent':self.memory[-5:],'policy':'one local inference at a time; user requests first between model calls'}
SHARED=SharedInference()
