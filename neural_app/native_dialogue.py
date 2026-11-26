"""Conversation directly with native skills and deliberation; no model route."""
import copy,json,re,threading,time
from pathlib import Path
from .deliberation import task_spec,Deliberation

class NativeDialogue:
 def __init__(self,deliberation,data=None):
  from .native_work import NativeWork
  self.shared_reasoning_worker=False;self.goal_worker=None;self.on_result=None;self.evaluation={};self.work=NativeWork();self.engine=deliberation;self.lock=threading.RLock();self.messages=[];self.memory={};self.selected=None;self.path=Path(data)/'native-only-dialogue.json' if data else None
  if self.path and self.path.exists():
   try:
    if self.path.stat().st_size>2_000_000:raise ValueError('Conversation checkpoint too large')
    saved=json.loads(self.path.read_text(encoding='utf-8'))
    if not isinstance(saved,dict) or not isinstance(saved.get('messages',[]),list) or not isinstance(saved.get('memory',{}),dict):raise ValueError('Invalid native dialogue checkpoint')
    self.messages=saved.get('messages',[])[-60:];self.memory=saved.get('memory',{});self.selected=saved.get('selected');self.work=NativeWork(saved.get('work'))
   except (ValueError,OSError,TypeError):pass
  if data:
   try:
    check_path=Path(data)/'native-improvement-checks.json'
    if check_path.stat().st_size<100000:self.evaluation=json.loads(check_path.read_text(encoding='utf-8'))
   except (OSError,ValueError):pass
 def start_goal_worker(self):
  if self.shared_reasoning_worker:return
  with self.lock:
   goal=self.work.state.get('active_goal')
   if not goal or goal['status']!='running' or self.goal_worker and self.goal_worker.is_alive():return
   def run():
    for _ in range(14):
     time.sleep(.35)
     with self.lock:
      goal=self.work.state.get('active_goal')
      if not goal or goal['status']!='running':return
      try:
       self.work.think_step()
       if self.path:Deliberation.write_json(self.path,{'messages':self.messages,'memory':self.memory,'selected':self.selected,'work':self.work.state})
      except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError,OSError) as exc:
       goal['status']='failed';goal['error']='Native goal worker: '+str(exc)[:300];return
   self.goal_worker=threading.Thread(target=run,name='native-goal-worker',daemon=True);self.goal_worker.start()
 def _task(self):
  tasks=self.engine.view()['tasks']
  return next((t for t in tasks if t['id']==self.selected),tasks[-1] if tasks else None)
 def _describe(self,task,why=False):
  if not task:return 'No task is selected. Tell me a supported task or supply an example contract.'
  text='**'+task['question']+'**\n\nState: '+task['status']+'. Tested '+str(task['tested'])+' candidate branches.'
  if task.get('solution') is not None:text+='\n\nPassing procedure: '+(' → '.join(task['solution']) or 'identity')+'.\n'+json.dumps(task.get('result'),ensure_ascii=False,indent=2)
  elif task.get('conclusion'):text+='\n\n'+task['conclusion']
  if why:
   trace=[t for t in task['trace'] if t['phase'] in ('check','revise','conclude','stop','critique')][-4:]
   text+='\n\nRecorded process:\n'+'\n'.join('- '+t['phase']+': '+t['summary'] for t in trace)
   if task['counterexamples']:text+='\n\nLatest rejected branch:\n```json\n'+json.dumps(task['counterexamples'][-1],ensure_ascii=False,indent=2)+'\n```'
  return text
 def _send(self,body):
  if not isinstance(body,dict) or not isinstance(body.get('text'),str):raise ValueError('Provide a text message')
  text=body['text'].lstrip()
  if not text.strip() or len(text)>16000:raise ValueError('Enter 1–16000 characters')
  from .conversational_requests import normalize
  text=normalize(text)
  key=text.strip().casefold().rstrip('?.!');task=None;work_result=None;concise_answer=None
  aliases={'how did you get that':'why is this verified','what can you help me with':'help','what are you doing':'what are you thinking','show the evidence':'show evidence','why did you ask that':'explain current inquiry','what are the alternatives':'explain current inquiry'}
  if key in aliases:text=aliases[key];key=text
  with self.lock:
   try:
    if key in ('help','capabilities','what can you do','what are your capabilities'):
     from .native_capabilities import describe
     concise_answer=describe(self.work)
    elif key in ('show examples','show all native examples'):key='help';work_result=None
    elif key in ('explain result plainly','explain the result plainly') and self.messages:
     from .result_explanation import explain_attempt
     work_result=explain_attempt(self.messages[-1].get('work')) or self.work.handle(text)
    else:work_result=self.work.handle(text)
   except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError,SyntaxError) as exc:work_result={'answer':'The native operation did not complete: '+str(exc)[:500]+'. Previous results are retained.','status':'needs-input','error':str(exc)[:500]}
   if concise_answer is not None:answer=concise_answer
   elif work_result is not None:answer=work_result['answer']
   elif key in ('help','capabilities','what can you do','what are your capabilities'):
    answer='**Native-only chat**\n\nI use the app’s built-in calculations, data operations, explicit memory and task experiments. This chat makes zero language-model calls.\n\n- Ask “what is 23 times 17?”, then “now double it”.\n- Ask “find the sum of [2,3,5]” or `uppercase "Hello"`.\n- Preview work: `preview: sort then deduplicate: [3,1,3]; expect: [1,3]`, then “run that plan”.\n- Use `search knowledge: TOPIC` to retrieve source-linked procedures, rules, inquiries, goals and explicit memories.\n- Use `check workflow NAME: {"input":3,"expected":6}`; a failed check revokes it and invalidates dependent goals.\n- Use `sphere task: JSON` with workflows, training examples, separate validation, action input and expected result to drive Choice/Action/Consequence roles.\n- Use `sphere experiment: {"workflow":"NAME","question":"...","cases":[{"input":1,"expected":2},{"input":2,"expected":4}]}` for question-linked baseline comparisons.\n- Say “teach a workflow called NAME” and supply input/output examples plus separate validation examples; I derive the steps. A passing named procedure can then be a goal stage.\n- Use plain requests such as `take [3,1,3], deduplicate then sum then double`.\n- Use “save this workflow as NAME”, then `use NAME on: [new,data]` to transfer it.\n- Correct a stopped goal using `revise goal stage 2: {"instruction":"double","expected":10}`; every stage runs again.\n- Compose work: `trim then lowercase:  HELLO  `.\n- Use `sum: [2,3,5]`, `solve constraints: JSON`, or `write Python for last workflow`.\n- Ask “what is 23 times 17?”\n- Try “sort and deduplicate lines” or “reverse text” to study a checked procedure.\n- Use `deliberate: {"question":"...","spec":{"examples":[...],"holdout":[...],"operations":[...],"max_depth":4}}` for your own contract.\n- Use `run plan: JSON` for dependency/branch plans, and `export last plan as Python`.\n- Use `learn numeric rule: JSON`, `apply rule NAME: NUMBER` and `check rule NAME: JSON`.\n- Use `work toward: {"name":"total","input":[2,3],"stages":[{"instruction":"sum","expected":5},{"instruction":"double","expected":10}]}` for background staged work.\n- Use “goal status”, “continue goal” or “cancel goal”.\n- Search explicit memory with “what do you know about TOPIC”.\n- Ask “status”, “why?”, “what failed?” or “what are you thinking?”\n- Use `remember name = value` and `recall name`.\n\nMy language coverage is finite; an unsupported question receives clarification rather than a generated answer.'
   elif key=='why' and self.work.state.get('focus_kind') not in (None,'task'):
    explanation=self.work.handle('why is this verified');answer=explanation['answer']
    if self.work.state.get('focus_kind')=='open-reasoning':work_result=explanation
   elif key=='why' and self.work.state.get('focus_inquiry'):
    self.work.think_step();answer=self.work.inquiry_summary(True)
   elif key in ('what are you thinking','what is your thought process'):
    self.work.think_step();answer=self.work.inquiry_summary(True)
   elif key in ('status','progress','why','what failed','what are you thinking','what is your thought process','explain your reasoning','show your work','continue'):
    self.engine.advance();task=self._task();answer=self._describe(task,key not in ('status','progress'))
   elif key in ('stop','cancel'):
    task=self._task()
    answer=self._describe(self.engine.cancel(task['id'])) if task else 'No current task to stop.'
   elif key=='what have you learned':
    answer=json.dumps({'checked_procedures':self.engine.view().get('procedure_library',[]),'taught_phrases':list(self.work.state.get('recipes',{})),'numeric_rules':[{k:r.get(k) for k in ('name','degree','active','scope')} for r in self.work.state.get('rules',{}).values()]},ensure_ascii=False,indent=2)
   elif key in ('what should i do next','what do you need from me','what is missing'):
    goal=self.work.state.get('active_goal')
    if goal and goal['status']=='running':
     from .native_goals import summary
     answer=summary(goal)+'\n\nThe background engine can continue these supported stages; “continue goal” advances one now.'
    else:answer=self.work.inquiry_summary(True)
   elif key.startswith('find in my memories:'):
    query=text.split(':',1)[1] if ':' in text else text[len('what do you know about '):]
    tokens=set(re.findall(r'\w+',query.casefold()))-{'the','a','my','about','is','of','and','do','you','know'}
    ranked=[]
    for name,value in self.memory.items():
     words=set(re.findall(r'\w+',name.casefold()+' '+value.casefold()));overlap=tokens&words
     if overlap:ranked.append((len(overlap)/max(1,len(tokens)),name,value))
    ranked.sort(key=lambda r:(-r[0],r[1]))
    answer=('From your explicitly saved memories:\n'+'\n'.join('- '+name+': '+value for score,name,value in ranked[:5])+'\nThese are your saved statements, not independently verified facts.') if ranked else 'No saved memory matches those terms. Use remember name = value to save an explicit statement.'
   elif key.startswith(('search knowledge:','find knowledge about ','what do you know about ')) or key=='show knowledge':
    from .artifact_memory import search,index
    query=text.split(':',1)[1] if ':' in text else re.sub(r'^(?:find knowledge about|what do you know about)\s+','',text,flags=re.I)
    rows=index(self.work.state,self.memory) if key=='show knowledge' else search(self.work.state,query,self.memory)
    answer='Source-linked native knowledge:\n'+json.dumps(rows,ensure_ascii=False,indent=2) if rows else 'No saved memory or retained artifact matches those terms. No answer has been inferred from missing evidence.'
   elif key=='show my memories':answer=json.dumps(self.memory,ensure_ascii=False,indent=2)
   elif key in ('list tasks','show tasks'):
    answer='\n'.join('- '+t['question']+': '+t['status'] for t in self.engine.view()['tasks']) or 'No retained tasks.'
   elif key.startswith('remember '):
    name,separator,value=text[9:].partition('=')
    if not separator or not name.strip() or len(name)>80 or len(value)>2000:raise ValueError('Use remember name = value, with a short name and value')
    self.memory[name.strip().casefold()]=value.strip()
    while len(self.memory)>64:self.memory.pop(next(iter(self.memory)))
    answer='Remembered '+name.strip()+'.'
   elif key.startswith('forget '):
    name=text[7:].strip().casefold();existed=name in self.memory;self.memory.pop(name,None);answer='Forgot '+name+'.' if existed else 'No explicit memory with that name.'
   elif re.fullmatch(r'what (?:do you remember about|is my) .+',key):
    name=re.sub(r'^what (?:do you remember about|is my) ','',key);answer=self.memory.get(name,'No explicit memory with that name.')
   elif re.fullmatch(r'(?:no,? |actually,? )?my [\w ]{1,60} is .+',text,re.I):
    match=re.fullmatch(r'(?:no,? |actually,? )?my ([\w ]{1,60}?) is (.+)',text,re.I);name=match[1].strip().casefold();self.memory[name]=match[2].strip();answer='Remembered '+name+' = '+self.memory[name]+'.'
   elif key.startswith('recall '):answer=self.memory.get(text[7:].strip().casefold(),'No explicit memory with that name.')
   else:
    if key.startswith('deliberate:'):
     specification=json.loads(text.split(':',1)[1]);specification['allow_helper']=False;specification['source']='native-only-chat';task=self.engine.submit(specification)
    elif task_spec(text):task=self.engine.submit({'question':text,'allow_helper':False,'source':'native-only-chat'})
    if task:
     self.work.state['focus_kind']='task';self.selected=task['id'];self.engine.advance();task=self._task();answer=self._describe(task)
    else:
     from .native_skills import respond
     result=respond(text)
     if result:
      answer=result['result'] if isinstance(result['result'],str) else json.dumps(result['result'],ensure_ascii=False,indent=2)
      if result['skill']!='conversation':
       self.work.state['focus_kind']='native';self.work.state['last_native_skill']={'skill':result['skill'],'request':text,'verification':result.get('verification','Native arithmetic uses an independent rational check.' if result['skill']=='arithmetic' else 'Supported deterministic operation; task-specific expected output was not supplied.')}
       self.work.state['previous']=copy.deepcopy(self.work.state.get('last'));self.work.state['last']=copy.deepcopy(result['result']);self.work.state['has_last']=True
     else:
      from .concept_dialogue import respond as concept_response
      work_result=concept_response(text,self.work.state,fallback=True) if self.work.state.get('focus_kind')!='open-reasoning' and not self.work.state.get('pending') else None
      if work_result is None:
       from .open_reasoning import respond as open_response
       work_result=open_response(text,self.work.state,fallback=True)
      answer=work_result['answer']
   while len(self.memory)>64:self.memory.pop(next(iter(self.memory)))
   record={'time':time.time(),'user':text,'answer':answer,'task_id':task['id'] if task else self.selected,'model_calls':0,'route':'native-only','work':copy.deepcopy(work_result),'answer_sha256':__import__('hashlib').sha256(answer.encode()).hexdigest()}
   self.messages=(self.messages+[record])[-60:]
   while len(self.messages)>1 and len(json.dumps(self.messages,ensure_ascii=True))>400000:self.messages.pop(0)
   if self.path:Deliberation.write_json(self.path,{'messages':self.messages,'memory':self.memory,'selected':self.selected,'work':self.work.state})
   return copy.deepcopy(record)
 def send(self,body):
  try:
   record=self._send(body)
   if self.on_result:
    try:record['shared_engine_receipt']=self.on_result(record)
    except Exception as exc:record['shared_engine_error']=str(exc)[:200]
   return record
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError,SyntaxError) as exc:
   with self.lock:
    text=str(body.get('text',''))[:16000] if isinstance(body,dict) else ''
    record={'time':time.time(),'user':text,'answer':'The native request needs correction: '+str(exc)[:500]+'. No completed result is claimed.','task_id':self.selected,'model_calls':0,'route':'native-only','work':{'status':'needs-input','error':str(exc)[:500]}}
    self.messages=(self.messages+[record])[-60:]
    if self.path:Deliberation.write_json(self.path,{'messages':self.messages,'memory':self.memory,'selected':self.selected,'work':self.work.state})
    return copy.deepcopy(record)
 def view(self):
  with self.lock:return {'messages':copy.deepcopy(self.messages),'selected_task':self._task(),'model_calls':0,'route':'native-only','model_fallback':False,'work_state':copy.deepcopy(self.work.state),'evaluation':copy.deepcopy(self.evaluation),'native_thought':self.work.thought_status()}
