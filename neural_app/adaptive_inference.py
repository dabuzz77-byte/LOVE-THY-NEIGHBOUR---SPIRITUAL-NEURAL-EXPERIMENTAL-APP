"""Bounded local inference with size-aware context and response recovery."""
import json,math,re,time,urllib.request
from urllib.error import HTTPError

def budget(messages,context_ceiling,output_ceiling,output_target,ratio=.6):
 context_ceiling=max(2048,int(context_ceiling));output=min(int(output_ceiling),int(output_target),context_ceiling//2)
 encoded=sum(len(str(m.get('content','')).encode('utf-8')) for m in messages)
 estimated=math.ceil(encoded*max(.15,min(1.,ratio)))+12*len(messages)+256
 context=min(context_ceiling,max(4096,((estimated+output+1024+4095)//4096)*4096))
 return {'context_tokens':context,'output_tokens':max(128,output),'estimated_input_tokens':estimated,'input_utf8_bytes':encoded,'context_ceiling':context_ceiling,'output_ceiling':int(output_ceiling),'estimate_only':True}

def generate(endpoint,payload,*,context_ceiling,output_ceiling,stopped=lambda:False,progress=None,draft=None,structured=False,transport=None,stop_after_python_block=False,validate_text=None):
 payload=json.loads(json.dumps(payload));attempts=[];context_recovered=False;output_recovered=False
 for attempt in range(3):
  if stopped():raise ValueError('Request cancelled or deadline reached')
  options=payload.setdefault('options',{});record={'attempt':attempt+1,'context_tokens':options.get('num_ctx'),'output_tokens':options.get('num_predict')};attempts.append(record)
  try:
   if transport:value=transport(payload)
   else:
    request=urllib.request.Request(endpoint+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=180) as response:
     if not payload.get('stream'):value=json.load(response)
     else:
      chunks=[];size=0;thinking=0;native_calls=0;done=False;last_draft=0
      for line in response:
       if stopped():raise ValueError('Request cancelled or deadline reached')
       if not line.strip():continue
       part=json.loads(line)
       if part.get('error'):raise ValueError(str(part['error'])[:300])
       message=part.get('message',{});content=message.get('content') or '';chunks.append(content);size+=len(content);thinking+=len(message.get('thinking') or '');native_calls+=len(message.get('tool_calls') or [])
       if size>524288:raise ValueError('Response exceeds the bounded transport budget')
       if validate_text and size>=512:
        check=''.join(chunks)
        if structured:
         from .reply_prefix import visible_prefix
         check=visible_prefix(check)
        if check:validate_text(check)
       if progress:progress('Generating response · '+str(size)+' characters received')
       if draft and time.monotonic()-last_draft>=.2:
        text=''.join(chunks)
        if structured:
         from .reply_prefix import visible_prefix
         text=visible_prefix(text)
        draft(text);last_draft=time.monotonic()
       if stop_after_python_block and '`' in content:
        match=re.search(r'```[^\n`]*\n([\s\S]*?)```',''.join(chunks))
        if match:
         try:
          import ast
          ast.parse(match[1]);value={'done_reason':'content-complete','completion_basis':'First complete Python block passed syntax validation; unneeded continuation stopped'};done=True;break
         except SyntaxError:pass
       if part.get('done'):value=part;done=True;break
      if not done:raise ValueError('The model connection ended before completing its response; retry is available')
      value['message']={'content':''.join(chunks)};value['thinking_characters']=thinking;value['native_calls']=native_calls
  except HTTPError as exc:
   detail=exc.read(16384).decode('utf-8',errors='replace')
   overflow=exc.code in (400,413) and bool(re.search(r'context|tokens.*exceed',detail,re.I))
   if overflow and not context_recovered and options.get('num_ctx',0)<context_ceiling:
    required=re.search(r'(?:request\s*\(|requested\s*)(\d+)\s*tokens',detail,re.I)
    wanted=(int(required[1])+512) if required else options.get('num_ctx',4096)*2
    options['num_ctx']=min(context_ceiling,max(options.get('num_ctx',4096)*2,wanted));context_recovered=True;record.update(status='context-overflow-recovered',detail=detail[:300])
    if progress:progress('Increasing context for the original request and retrying')
    if draft:draft('')
    continue
   raise ValueError(('The original input exceeds the available context budget. It has not been silently shortened. ' if overflow else 'Local model HTTP '+str(exc.code)+': ')+detail[:500]) from None
  reason=value.get('done_reason','stop');text=value.get('message',{}).get('content','')
  if validate_text:
   if structured:
    from .reply_prefix import visible_prefix
    validate_text(visible_prefix(text))
   else:validate_text(text)
  record.update(status='returned',finish_reason=reason,prompt_tokens_used=value.get('prompt_eval_count'),output_tokens_generated=value.get('eval_count'))
  if reason in ('length','max_tokens') and not output_recovered and options.get('num_predict',0)<output_ceiling:
   options['num_predict']=min(output_ceiling,max(1024,options.get('num_predict',512)*2));options['num_ctx']=min(context_ceiling,max(options.get('num_ctx',4096),options['num_predict']*2));output_recovered=True;record['status']='response-budget-increased'
   if progress:progress('The reply reached its initial budget; retrying with more response room')
   if draft:draft('')
   continue
  value['budget_receipts']=attempts;value['effective_budget']={'context_tokens':options.get('num_ctx'),'output_tokens':options.get('num_predict'),'context_ceiling':context_ceiling,'output_ceiling':output_ceiling};return value
 raise ValueError('The model exhausted its bounded recovery attempts; original input was preserved')
