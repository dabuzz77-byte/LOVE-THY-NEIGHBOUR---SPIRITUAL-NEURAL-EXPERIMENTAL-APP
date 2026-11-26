"""Bounded, idempotent chat jobs with observable progress and cancellation."""
import collections,copy,hashlib,json,queue,threading,time,uuid

class ChatRequests:
 def __init__(self,reasoner):
  self.r=reasoner;self.lock=threading.RLock();self.jobs=collections.OrderedDict();self.queue=queue.Queue(maxsize=4);self.closed=False;self.worker=threading.Thread(target=self.run,daemon=True,name='interactive-chat-requests');self.worker.start()
 def submit(self,body):
  if not isinstance(body,dict) or not isinstance(body.get('text'),str) or not body['text'].strip() or len(body['text'])>131072:raise ValueError('Enter a message up to 131072 characters')
  ident=body.get('request_id') or uuid.uuid4().hex
  if not isinstance(ident,str) or not 1<=len(ident)<=100:raise ValueError('Invalid request identifier')
  request={k:copy.deepcopy(body[k]) for k in ('text','allow_model','response_detail','assistant_mode','workspace_files') if k in body}
  digest=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
  with self.lock:
   if self.closed:raise ValueError('The chat service is closing')
   if ident in self.jobs:
    if self.jobs[ident]['digest']!=digest:raise ValueError('This request identifier belongs to a different message')
    return self.view(ident)
   if self.queue.full():raise ValueError('Four messages are already queued. Wait or cancel one before sending another.')
   while len(self.jobs)>=32:
    old=next((key for key,row in self.jobs.items() if row['status'] in ('complete','failed','cancelled')),None)
    if old is None:raise ValueError('Chat request capacity reached')
    self.jobs.pop(old)
   self.jobs[ident]={'id':ident,'digest':digest,'request':request,'status':'queued','progress':'Queued for the assistant','draft':'','created':time.time(),'cancel':threading.Event(),'result':None,'error':None};self.queue.put_nowait(ident)
   return self.view(ident)
 def view(self,ident):
  with self.lock:
   if ident not in self.jobs:raise ValueError('Request not found; check conversation history after a restart')
   row=self.jobs[ident]
   return {k:copy.deepcopy(v) for k,v in row.items() if k not in ('cancel','request','digest')}
 def cancel(self,ident):
  with self.lock:
   if ident not in self.jobs:raise ValueError('Request not found')
   row=self.jobs[ident]
   if row['status'] not in ('complete','failed','cancelled'):
    row['cancel'].set();row['status']='cancelled' if row['status']=='queued' else 'cancelling';row['progress']='Stopping; an active network read may take a moment to return'
   return self.view(ident)
 def run(self):
  while not self.closed:
   try:ident=self.queue.get(timeout=.2)
   except queue.Empty:continue
   try:
    with self.lock:
     row=self.jobs.get(ident)
     if row is None or row['cancel'].is_set():continue
     row.update(status='running',started=time.time(),progress='Understanding the current request')
    def progress(message):
     with self.lock:
      if not row['cancel'].is_set():row['progress']=str(message)[:250]
    def draft(text):
     with self.lock:
      if not row['cancel'].is_set():row['draft']=str(text)[:524288]
    try:
     result=self.r.request({**row['request'],'_cancel_event':row['cancel'],'_progress':progress,'_draft':draft,'_deadline':time.monotonic()+(900 if row['request'].get('response_detail')=='detailed' or len(row['request']['text'])>8192 else 180)})
     with self.lock:row.update(status='cancelled' if row['cancel'].is_set() else 'complete',result=result,finished=time.time(),progress='Stopped' if row['cancel'].is_set() else 'Response ready')
    except Exception as e:
     if hasattr(self.r,'reply'):
      try:
       message='Stopped at your request.' if row['cancel'].is_set() else 'The request did not complete: '+str(e)[:500]
       from .chat_intent import InvalidChatReply
       if isinstance(e,InvalidChatReply):row['draft']='';message='The local model returned repetitive or command-like text instead of an answer. That draft was discarded. Please retry or select another installed model.'
       if row['draft']:message+='\n\nPartial response (incomplete):\n'+row['draft']
       self.r.reply(row['request']['text'],message,{'model_used':False,'request_failed':True,'request_id':ident,'partial_response':bool(row['draft'])})
      except Exception:pass
     with self.lock:row.update(status='cancelled' if row['cancel'].is_set() else 'failed',error=type(e).__name__+': '+str(e)[:500],finished=time.time(),progress='Stopped' if row['cancel'].is_set() else 'The request failed; your message can be retried')
   finally:self.queue.task_done()
 def close(self):
  with self.lock:
   self.closed=True
   for row in self.jobs.values():
    if row['status'] not in ('complete','failed','cancelled'):row['cancel'].set()
  if self.worker is not threading.current_thread():self.worker.join(1)
