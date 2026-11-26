"""Model-light reasoning, typed observations and verified local action loops.
Generated character streams are observations, never executable authority.
"""
import collections,hashlib,json,math,queue,random,re,threading,time,uuid,urllib.request

def pattern_test(text,controls=8):
 original=str(text);text=original[:1024];n=len(text);counts=collections.Counter(text)
 entropy=-sum((v/n)*math.log2(v/n) for v in counts.values()) if n else 0
 def score(s):return sum(v*(v-1)//2 for v in collections.Counter(s[i:i+2] for i in range(max(0,len(s)-1))).values())
 observed=score(text);rng=random.Random(int(hashlib.sha256(text.encode('utf-8',errors='replace')).hexdigest()[:16],16));null=[]
 for _ in range(controls):
  shuffled=list(text);rng.shuffle(shuffled);null.append(score(''.join(shuffled)))
 motifs=collections.Counter(text[i:i+3] for i in range(max(0,n-2)))
 return {'input_characters':len(original),'analyzed_limit':1024,'truncated':len(original)>1024,'characters':n,'distinct':len(counts),'entropy_bits_per_character':entropy,'bigram_collision_score':observed,'shuffled_scores':null,'exploratory_tail_fraction':(1+sum(v>=observed for v in null))/(len(null)+1),'repeated_trigrams':[{'text':k,'count':v} for k,v in motifs.most_common(6) if v>1],'runs':max((len(m.group()) for m in re.finditer(r'(.)\1*',text,re.S)),default=0),'interpretation':'Descriptive pattern test against same-character shuffled controls; exploratory, not evidence of an external message or a physical source','sha256':hashlib.sha256(text.encode('utf-8',errors='replace')).hexdigest()}

class GroundedReasoner:
 def __init__(self,runtime,controller,bus,start=True):
  self.runtime=runtime;self.controller=controller;self.bus=bus;self.lock=controller.lock;self.halt=threading.Event();self.pending=queue.Queue(maxsize=128);self.user_active=False;self.request_lock=threading.Lock();self.dropped=0;self.coalesced=0;self.intake_lock=threading.Lock();self.pending_by_source={};self.last_saved=0;self.tools=None
  defaults={'world':{},'memories':{},'tasks':[],'thoughts':[],'conversation':[],'procedures':{},'model_calls':0,'rule_requests':0,'pattern_tests':0,'observed_events':0,'phase':'observe','pending_proposals':{},'model_cache':{},'ascii_counts':[0]*128,'ascii_transitions':{}}
  with self.lock:
   existing=controller.state.setdefault('reasoning',{})
   for k,v in defaults.items():existing.setdefault(k,v)
   self.s=existing
   for t in self.s['tasks']:
    if t.get('status') in ('queued','running'):t['status']='interrupted';t['error']='App restarted; no task replayed automatically'
  from .native_workbench import NativeWorkbench
  self.workbench=NativeWorkbench(self)
  from .selective_bridge import SelectiveBridge
  self.selective_bridge=SelectiveBridge(self)
  from .system_coordinator import SystemCoordinator
  self.coordinator=SystemCoordinator(self)
  from .os_learning import OSLearning
  self.os_learning=OSLearning(self)
  self.worker=None
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='grounded-reasoning-loop');self.worker.start()
 def observe(self,event):
  if event.get('origin')=='grounded-reasoner':return
  p=event.get('payload');p=p if isinstance(p,dict) else {}
  generated=(p.get('stochastic') is True and p.get('predefined_text') is False and p.get('contains_model_text') is False) or p.get('provenance') in ('derived-cube-byte-projection','derived-process-ascii-grid','derived-vector-ascii-grid')
  row={'source':str(event.get('origin','unknown'))[:100],'sequence':event.get('sequence'),'time':event.get('time',time.time()),'kind':event.get('kind'),'provenance':str(p.get('provenance','bus-observation'))[:100],'text':str(p.get('text',''))[:1024] if generated and isinstance(p.get('text'),str) else None,'payload_hash':hashlib.sha256(json.dumps(p,sort_keys=True,default=str).encode()).hexdigest()}
  with self.intake_lock:
   source=row['source']
   if source in self.pending_by_source:
    row['coalesced_events']=self.pending_by_source[source].get('coalesced_events',1)+1;self.pending_by_source[source]=row;self.coalesced+=1;return
   row['coalesced_events']=1
   try:self.pending.put_nowait(source);self.pending_by_source[source]=row
   except queue.Full:self.dropped+=1
 def next_observation(self):
  source=self.pending.get_nowait()
  with self.intake_lock:return self.pending_by_source.pop(source)
 def event(self,phase,detail):
  self.s['phase']=phase;self.controller.event(phase,detail)
 def consume(self,row):
  with self.lock:
   source=row['source'];prior=self.s['world'].get(source);changed=not prior or prior['payload_hash']!=row['payload_hash'];self.s['observed_events']+=row.get('coalesced_events',1)
   self.s['world'][source]={**{k:v for k,v in row.items() if k!='text'},'type':'observed-stage-event','changed':changed,'count':(prior or {}).get('count',0)+row.get('coalesced_events',1),'links':['shared-bus','stage:'+source]}
   while len(self.s['world'])>128:self.s['world'].pop(next(iter(self.s['world'])))
  if changed and row.get('text'):
   metrics=pattern_test(row['text']);thought={'id':uuid.uuid4().hex,'time':time.time(),'source':source,'type':'pattern-hypothesis','status':'tested-descriptive','metrics':metrics,'sample':row['text'],'statement':f"Capture from {source}: {metrics['characters']} characters, {metrics['distinct']} distinct characters, longest repeated run {metrics['runs']}; observed bigram score {metrics['bigram_collision_score']} versus shuffled controls.",'proposal':'Compare later independent captures from this source before assigning meaning','action':'No host command derived from generated characters'}
   with self.lock:
    if source not in ('native-matrix-rain','process-ascii-grid','vector-ascii-grid'):
     codes=[ord(c) for c in row['text'] if ord(c)<128]
     for code in codes:self.s['ascii_counts'][code]+=1
     for a,b in zip(codes,codes[1:]):
      key=str(a)+':'+str(b)
      if key in self.s['ascii_transitions'] or len(self.s['ascii_transitions'])<4096:self.s['ascii_transitions'][key]=self.s['ascii_transitions'].get(key,0)+1
     if sum(self.s['ascii_counts'])>1000000:
      self.s['ascii_counts']=[x//2 for x in self.s['ascii_counts']];self.s['ascii_transitions']={k:max(1,v//2) for k,v in self.s['ascii_transitions'].items()}
    self.s['pattern_tests']+=1;self.s['thoughts']=(self.s['thoughts']+[thought])[-48:];self.event('reason','Tested generated capture against shuffled controls: '+source)
 def reply(self,request,text,extra=None):
  with self.lock:
   full=str(text);metadata={}
   if len(request)>2000:
    folder=self.runtime.data/'native-outputs';folder.mkdir(parents=True,exist_ok=True);request_id=uuid.uuid4().hex;(folder/(request_id+'.txt')).write_text(request,encoding='utf-8');metadata['request_output_id']=request_id
   if len(full)>6000:
    folder=self.runtime.data/'native-outputs';folder.mkdir(parents=True,exist_ok=True);ident=uuid.uuid4().hex;raw=full.encode('utf-8');(folder/(ident+'.txt')).write_bytes(raw)
    metadata.update({'output_id':ident,'output_characters':len(full),'output_sha256':hashlib.sha256(raw).hexdigest(),'answer_truncated':True})
    full=full[:6000]+'\n\n[Preview — use Full answer or Copy to retrieve the complete output.]'
    retained=sorted((p for p in folder.glob('*.txt') if re.fullmatch(r'[a-f0-9]{32}\.txt',p.name) and p.is_file() and not p.is_symlink()),key=lambda p:p.stat().st_mtime)
    for old in retained[:-80]:
     if old.resolve().parent==folder.resolve():old.unlink()
   row={'time':time.time(),'request':request[:2000],'request_truncated':len(request)>2000,'answer':full,**metadata,**(extra or {})};self.s['conversation']=(self.s['conversation']+[row])[-40:];self.controller.save()
  return row
 def output(self,ident):
  if not re.fullmatch(r'[a-f0-9]{32}',str(ident)):raise ValueError('Choose an output ID')
  path=self.runtime.data/'native-outputs'/(str(ident)+'.txt')
  if path.is_symlink() or path.resolve().parent!=(self.runtime.data/'native-outputs').resolve() or not path.is_file():raise ValueError('Output is no longer retained')
  raw=path.read_bytes();return {'id':ident,'text':raw.decode('utf-8'),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 def work_tools(self):
  if self.tools is None:
   from .work_tools import WorkTools
   self.tools=WorkTools(self.runtime)
  return self.tools
 def create_task(self,operation,text):
  text=str(text)
  if len(text.encode())>(300000 if operation=='coordinator_file' else 16000 if operation in ('shell','desktop') else 8192):raise ValueError('Task input exceeds this operation’s size limit')
  if operation not in ('pipeline','analyze','list_files','read_file','write_file','shell','desktop','coordinator_file'):raise ValueError('Unknown task operation')
  if operation=='pipeline' and len(text.encode())>512:raise ValueError('Use at most 512 UTF-8 bytes per pipeline task; analysis and file tasks accept larger inputs')
  if operation=='write_file' and '\n' not in text:raise ValueError('Use write file NAME followed by a newline and its contents')
  task={'id':uuid.uuid4().hex,'created':time.time(),'operation':operation,'input':text,'input_sha256':hashlib.sha256(text.encode('utf-8',errors='replace')).hexdigest(),'status':'queued','plan':['capture typed input','select supported operation','execute','compare actual result with completion condition','retain outcome'],'completion_condition':'pipeline: returned input round-trips exactly and requested stages have receipts; file write: reread bytes match; analysis: finite computed metrics','model_used':False}
  with self.lock:
   active=sum(t['status'] in ('queued','running') for t in self.s['tasks'])
   if active>=8:raise ValueError('Eight tasks are already pending')
   self.s['current_goal']={'task':task['id'],'operation':operation,'input_summary':text[:300]};self.s['tasks']=(self.s['tasks']+[task])[-48:];self.event('choose',operation+' task queued');self.controller.save()
  return task
 def request(self,body):
  cancel=body.get('_cancel_event');deadline=body.get('_deadline',float('inf'));progress=body.get('_progress')
  if callable(progress):progress('Waiting for the conversation controller')
  while not self.request_lock.acquire(timeout=.1):
   if (cancel and cancel.is_set()) or time.monotonic()>deadline:raise ValueError('Request cancelled or timed out before starting')
  try:
   if cancel and cancel.is_set():raise ValueError('Request cancelled before starting')
   return self._request(body)
  finally:self.request_lock.release()
 def _request(self,body):
  request=str(body.get('text','')).lstrip()
  if not request.strip():raise ValueError('Enter a request')
  if len(request)>131072:raise ValueError('Use a request up to 131072 characters')
  from .native_language import canonical_request
  with self.lock:request=canonical_request(request,self.s.get('native_grammar',{}))
  self.user_active=True
  try:
   with self.lock:self.s['rule_requests']+=1;self.event('remember','Latest user request has priority')
   lower=request.lower()
   if lower.startswith(('deliberate:','think about:')):
    from .deliberation import task_spec
    circuit=getattr(self.runtime,'cognitive_circuit',None)
    if circuit is None:return self.reply(request,'The task engine is still starting.',{'model_used':False})
    content=request.split(':',1)[1].strip();specification=json.loads(content) if content.startswith('{') else {'question':content}
    task=circuit.whole_mind_study.deliberation.submit(specification)
    return self.reply(request,'Task '+task['id'][:8]+' retained: '+task['status']+'. Open Task deliberation for predictions, branches, checks and the conclusion.',{'model_used':False,'deliberation_task':task['id']})
   from .chat_intent import assessment_request,assessment_reply
   if assessment_request(request):return self.reply(request,assessment_reply(self.runtime),{'model_used':False,'native_skill':'recorded-capability-assessment'})
   coordinated=self.coordinator.handle(request)
   if coordinated is not None:return self.reply(request,coordinated['answer'],{'model_used':False,'work_result':coordinated,**({'proposal':coordinated['proposal']} if coordinated.get('proposal') else {})})
   if lower.startswith('train with qwen:'):
    lesson=request.split(':',1)[1].strip()
    if not lesson:raise ValueError('Describe the skill or task to teach')
    interpretation,used=self.selective_bridge.assist(lesson,{**body,'compact_bridge':True})
    if interpretation['intent']!='plan':return self.reply(request,interpretation['text'],{'model_used':used,'training_status':'needs a supported executable lesson'})
    proposal={'id':uuid.uuid4().hex,'operation':'plan','text':interpretation['text'],'original_request':lesson,'source':'qwen-teaching-proposal','status':'awaiting-confirmation'}
    with self.lock:self.s['pending_proposals']={**dict(list(self.s['pending_proposals'].items())[-15:]),proposal['id']:proposal}
    return self.reply(request,'Review this teaching procedure. The native system will execute its supported steps, check the results and retain it only after successful completion.\n'+proposal['text'],{'proposal':proposal,'model_used':used,'training_status':'awaiting-review'})
   extension=self.workbench.handle(request)
   if extension is not None:
    if isinstance(extension,dict) and extension.get('goal',{}).get('intent')=='unsupported' and extension.get('status')=='needs-input' and body.get('allow_model',True):
     calls_before=self.selective_bridge.s.get('calls',0)
     try:interpretation,used=self.selective_bridge.assist(request,{**body,'compact_bridge':True,'minimal_helper':True})
     except (ValueError,OSError,RuntimeError) as exc:
      if re.search(r'cancel|deadline|closing|while queued',str(exc),re.I):raise
      attempted=self.selective_bridge.s.get('calls',0)>calls_before
      return self.reply(request,extension['answer']+'\nLocal-model planning did not complete: '+str(exc)[:250],{'model_used':attempted,'native_skill':'goal-clarification','goal_assistance':{'status':'unavailable','executed':False,'model_attempted':attempted,'error':str(exc)[:250]}})
     if interpretation.get('intent')=='plan':
      proposal={'id':uuid.uuid4().hex,'operation':'plan','text':interpretation['text'],'original_request':request,'source':'goal-language-assistance','status':'awaiting-confirmation'}
      with self.lock:self.s['pending_proposals']={**dict(list(self.s['pending_proposals'].items())[-15:]),proposal['id']:proposal};self.controller.save()
      return self.reply(request,'The native interpreter needs help with this goal. Review the proposed plan before execution:\n'+proposal['text'],{'proposal':proposal,'model_used':used,'native_skill':'model-assisted-goal-proposal','goal_assistance':{'status':'awaiting-review','executed':False,'native_gap':extension['answer']}})
     return self.reply(request,interpretation.get('text',extension['answer']),{'model_used':used,'native_skill':'goal-clarification','goal_assistance':{'status':'needs-input','executed':False,'native_gap':extension['answer']}})
    with self.lock:self.controller.save()
    answer=extension.get('answer') if isinstance(extension,dict) else None
    return self.reply(request,answer if isinstance(answer,str) else json.dumps(extension,indent=2,ensure_ascii=False,default=str),{'model_used':False,'native_skill':'workbench','work_result':extension})
   shell_match=re.match(r'^(powershell|cmd|bat):\s*([\s\S]+)$',request,re.I)
   if shell_match:
    shell,command=shell_match.groups();shell='cmd' if shell.lower() in ('cmd','bat') else 'powershell'
    proposal={'id':uuid.uuid4().hex,'operation':'shell','text':json.dumps({'shell':shell,'command':command}),'source':'explicit-user-command','status':'awaiting-confirmation'}
    with self.lock:self.s['pending_proposals']={**dict(list(self.s['pending_proposals'].items())[-15:]),proposal['id']:proposal}
    return self.reply(request,'Review this '+shell+' command before running it. It will execute with your current account permissions: '+command,{'proposal':proposal,'model_used':False})
   if lower.startswith(('research ','find sources ')):
    query=request[9:] if lower.startswith('research ') else request[13:]
    intake=getattr(self.runtime,'learning_knowledge',None)
    rows=intake.retrieve(query) if intake else []
    return self.reply(request,json.dumps(rows,indent=2,ensure_ascii=False) if rows else 'No indexed source matches yet. Public feeds refresh on their configured schedule; this command searches the local source index.',{'model_used':False,'provenance':'source-index-retrieval'})
   if lower in ('learning rails','show learning rails'):
    intake=getattr(self.runtime,'learning_knowledge',None)
    return self.reply(request,json.dumps(intake.rails(),indent=2) if intake else 'Public intake is not running.',{'model_used':False})
   if lower in ('script formats','show script formats'):
    from .native_scripts import FORMATS
    return self.reply(request,'Native script formats: '+', '.join(FORMATS)+'. Use: create javascript script sum as sum.js. Concepts: sum, product, difference. Optional inputs: with 12 and 8.',{'model_used':False})
   multi_script=re.fullmatch(r'create ([a-z0-9]+) script ([a-z_]+) as ([A-Za-z0-9_.-]+)(?: with (-?\d+) and (-?\d+))?',request,re.I)
   if multi_script:
    from .native_scripts import generate
    from .language_formats import syntax
    language,concept,name,a,b=multi_script.groups();draft=generate(language,concept,name,int(a) if a else 7,int(b) if b else 3)
    checked=syntax({'language':draft['alias'],'source':draft['source'],'filename':name},self.runtime.data)
    if checked.get('passed') is False:raise ValueError('Source check failed: '+str(checked.get('diagnostics',''))[:500])
    task=self.create_task('write_file',name+'\n'+draft['source'])
    return self.reply(request,'Queued '+name+'. Expected answer: '+str(draft['expected'])+'. Source check: '+str(checked.get('method',checked.get('status','not available')))+'. Written-file verification is separate; the program has not been executed.',{'model_used':False,'task_id':task['id'],'source_check':checked,'draft':draft})
   script_match=re.fullmatch(r'write python script ([a-z_]+) as ([A-Za-z0-9_.-]+\.py)',request,re.I)
   if script_match:
    from .native_training import CONCEPTS
    concept,name=script_match.groups();concept=concept.lower()
    if concept not in CONCEPTS:raise ValueError('Supported script concepts: '+', '.join(CONCEPTS))
    with self.lock:template=self.s.get('training',{}).get('concepts',{}).get(concept,{}).get('retained_template')
    if not template:return self.reply(request,'The programming trainer has not retained a validated template for '+concept+' yet. Check native training and try after validation.',{'model_used':False})
    source='a = 7\nb = 3\nanswer = '+template+'\nprint(answer)\n'
    from .language_formats import syntax
    checked=syntax({'language':'python','source':source},self.runtime.data)
    if not checked.get('passed'):raise ValueError('Generated script did not pass its syntax check')
    task=self.create_task('write_file',name+'\n'+source)
    return self.reply(request,'Queued '+name+' using the trainer’s retained '+concept+' template. The script uses sample inputs a=7 and b=3. File completion is checked by rereading it.',{'task_id':task['id'],'model_used':False,'syntax_checked':True})
   from .native_skills import respond
   native=respond(request)
   if native is not None:
    if native['skill']=='arithmetic':self.workbench.remember_context('last_calculation',{'value':native['result'],'expression':request,'time':time.time()})
    return self.reply(request,json.dumps(native['result'],ensure_ascii=False) if not isinstance(native['result'],str) else native['result'],{'model_used':False,'native_skill':native['skill']})
   planned=self.workbench.reasoning_engine.plan_and_run(request)
   if planned is not None:return self.reply(request,json.dumps(planned,ensure_ascii=False,default=str),{'model_used':False,'native_skill':'goal-directed-work','needs_input':planned.get('status')=='needs-input'})
   if lower in ('system status','system capabilities'):
    from .system_access import SystemAccess
    return self.reply(request,json.dumps(SystemAccess(self.runtime).view(),indent=2),{'model_used':False})
   if lower in ('show memories','what do you remember?','show tasks','what did you learn?'):
    field='memories' if lower in ('show memories','what do you remember?') else 'tasks' if lower=='show tasks' else 'procedures'
    return self.reply(request,json.dumps(self.s[field],ensure_ascii=False,indent=2),{'model_used':False})
   if lower in ('bit status','show bit thoughts'):
    workbench=getattr(self.runtime,'bit_command',None)
    return self.reply(request,json.dumps(workbench.view(),indent=2) if workbench else 'Bit command workbench has not started.',{'model_used':False})
   if lower in ('status','what is happening','what is happening?','what are you doing?','show status'):
    v=self.view();return self.reply(request,f"{v['observed_events']} observed events; {len(v['world'])} source records; {v['pattern_tests']} pattern tests; {sum(t['status']=='verified' for t in v['tasks'])} verified tasks; {v['model_calls']} language-model calls. Current phase: {v['phase']}.",{'model_used':False})
   if lower in ('help','commands'):
    return self.reply(request,'Use coding capabilities for tested Python debugging, static project audits, evidence/prediction review and standalone workflow projects; capability report for fixed evaluation criteria; pause goal / resume goal / retry goal / cancel goal for native goal recovery; media workspace; create graphics as scene.svg; create sound as tone.wav; create music as music.wav; create midi as song.mid; create video as orbit.html; os learning; run benchmarks; workbench; plan: followed by explicit steps; continue plan; pause plan; project overview; check project; check file NAME; repair file NAME; edit file NAME followed by old text, --- and replacement; apply preview ID; undo change ID; search memory QUERY; compare sources QUERY; diagnose system; cosmic flow; research QUERY; learning rails; powershell: COMMAND or cmd: COMMAND (reviewed); script formats; create LANGUAGE script sum as NAME with 12 and 8; write python script CONCEPT as NAME.py; calculate EXPRESSION; count words TEXT; format json JSON; sort lines or unique lines followed by a newline and lines; system status; status; observe SOURCE; remember KEY = VALUE; recall QUERY; analyze TEXT; run pipeline: TEXT; list files; read file NAME; write file NAME followed by a newline and contents. Natural conversation, writing, coding and work planning use contextual Llama assistance when enabled. Use solve: for a native goal chain.',{'model_used':False})
   if lower.startswith('remember '):
    key,sep,value=request[9:].partition('=')
    if not sep or not key.strip() or not value.strip():raise ValueError('Use remember KEY = VALUE')
    with self.lock:
     old=self.s['memories'].get(key.strip()[:100])
     if old and old['value']!=value.strip():self.s['memory_changes']=(self.s.get('memory_changes',[])+[{'key':key.strip()[:100],'before':old,'replacement':value.strip()[:4000],'time':time.time(),'reason':'explicit user update'}])[-32:]
     from .memory_revisions import update as update_memory
     update_memory(self.s,key,value)
     while len(self.s['memories'])>128:self.s['memories'].pop(next(iter(self.s['memories'])))
     self.event('remember','Stored a source-labelled user memory')
    return self.reply(request,'Remembered '+key.strip()+'.',{'model_used':False})
   if lower.startswith('forget memory '):
    key=request[len('forget memory '):].strip()
    with self.lock:
     actual=next((k for k in self.s['memories'] if k.casefold()==key.casefold()),key);existed=actual in self.s['memories'];self.s['memories'].pop(actual,None);self.s.setdefault('memory_revisions',{}).pop(actual,None)
    return self.reply(request,('Forgot '+key+'.') if existed else 'No stored memory has that exact name.',{'model_used':False,'native_skill':'explicit-memory-removal'})
   if lower.startswith('recall '):
    query=request[7:].lower();found={k:v for k,v in self.s['memories'].items() if query in k.lower() or query in v['value'].lower()}
    return self.reply(request,json.dumps(found,ensure_ascii=False,indent=2) if found else 'No matching stored memory.',{'model_used':False})
   if lower.startswith('explain pattern '):
    ident=request[16:].strip();thought=next((t for t in self.s['thoughts'] if t['id']==ident),None)
    if not thought:raise ValueError('Pattern capture no longer retained')
    if not body.get('allow_model',True):return self.reply(request,thought['statement'],{'model_used':False})
    interpretation=self.interpret('Explain these descriptive pattern metrics in plain language without asserting a hidden message. '+json.dumps(thought['metrics']))
    return self.reply(request,interpretation['text'],{'model_used':True,'provenance':'model-language-explanation'})
   if lower.startswith('observe '):
    query=request[8:].lower();rows={k:v for k,v in self.s['world'].items() if query in k.lower()};return self.reply(request,json.dumps(rows,ensure_ascii=False,indent=2) if rows else 'No observed source matches that name yet.',{'model_used':False})
   patterns=[(r'^(?:please )?run pipeline\s*:\s*(.+)$','pipeline'),(r'^(?:analyze|analyse)\s+(.+)$','analyze'),(r'^read file\s+(.+)$','read_file'),(r'^write file\s+(.+)$','write_file')]
   for pattern,operation in patterns:
    match=re.match(pattern,request,re.I|re.S)
    if match:
     task=self.create_task(operation,match[1]);return self.reply(request,'Queued '+operation.replace('_',' ')+' task '+task['id'][:8]+'. Completion requires its checked result.',{'task_id':task['id'],'model_used':False})
   if lower=='list files':
    task=self.create_task('list_files','');return self.reply(request,'Queued workspace file listing.',{'task_id':task['id'],'model_used':False})
   from .evidence_index import INDEX
   with self.lock:stored_memories=dict(self.s['memories'])
   grounded=INDEX.respond(request,stored_memories)
   if grounded:
    answer=grounded.pop('answer');return self.reply(request,answer,grounded)
   from .capability_curriculum import suggestions
   near=suggestions(request)
   if near:return self.reply(request,'Did you mean '+ ' / '.join(near)+'? Please send the intended command; nothing was executed.',{'model_used':False,'suggestions':near})
   if not body.get('allow_model',True) and not self.selective_bridge.lookup(request):
    from .open_reasoning import respond as open_response
    with self.lock:
     framed=open_response(request,self.workbench.reasoning_engine.state,fallback=True);self.controller.save()
    return self.reply(request,framed['answer'],{'model_used':False,'work_result':framed,'native_skill':'open-problem-framing'})
   coordinate_tools=bool(re.search(r'\b(system|computer|desktop|window|files?|network|web|disk|processes)\b',request,re.I) and re.search(r'\b(check|inspect|show|list|create|write|click|type|open|search|find|set)\b',request,re.I))
   interpretation,used_model=self.selective_bridge.assist(request,{**body,'coordinate_tools':coordinate_tools})
   if interpretation['intent']=='coordinate':
    coordinated=self.coordinator.run(json.loads(interpretation['text']))
    return self.reply(request,coordinated['answer'],{'model_used':used_model,'model_name':interpretation.get('model_name'),'work_result':coordinated,**({'proposal':coordinated['proposal']} if coordinated.get('proposal') else {})})
   if interpretation['intent']=='workflow':
    from .language_workflow import execute as execute_language_workflow
    result=execute_language_workflow(request,interpretation.get('text',''))
    return self.reply(request,json.dumps(result,ensure_ascii=False),{'model_used':used_model,'model_name':interpretation.get('model_name'),'native_skill':'language-proposed-checked-workflow','needs_input':result.get('status')=='needs-input'})
   if interpretation['intent'] in ('pipeline','analyze','read_file','write_file','list_files','plan'):
    proposal={'id':uuid.uuid4().hex,'operation':interpretation['intent'],'text':interpretation.get('text',''),'source':interpretation.get('source','user-language-interpretation'),'original_request':request,'workspace_reads':interpretation.get('workspace_reads',[]),'status':'awaiting-confirmation'}
    with self.lock:self.s['pending_proposals']={**dict(list(self.s['pending_proposals'].items())[-15:]),proposal['id']:proposal}
    return self.reply(request,'Proposed '+proposal['operation'].replace('_',' ')+': '+proposal['text'][:500]+'. Review and run the proposed action below.',{'proposal':proposal,'model_used':used_model,'model_name':interpretation.get('model_name')})
   return self.reply(request,interpretation.get('text','Please use a specific supported command.'),{'model_used':used_model,'model_name':interpretation.get('model_name'),'provenance':'model-language-explanation' if used_model else 'native-routing-explanation','inference_budget':interpretation.get('inference_budget'),'budget_receipts':interpretation.get('budget_receipts',[])})
  finally:self.user_active=False
 def interpret(self,request,settings=None):
  from .work_tools import MODEL
  from .local_model_service import ensure_local_service
  from .shared_inference import SHARED
  from .conversation_context import prepare
  prepared=prepare(self,request,settings);model=(settings or {}).get('bridge_model') or self.s.get('assistant_model',MODEL)
  schema={'type':'object','properties':{'intent':{'type':'string','enum':['pipeline','analyze','read_file','write_file','list_files','plan','workflow','explain']},'text':{'type':'string'}},'required':['intent','text'],'additionalProperties':False}
  from .personal_context import conversational_only
  from .chat_intent import code_request
  code_reply=code_request(request) and not re.search(r'\bfile\b|\.(?:py|js|ts|java|cs)\b',request,re.I)
  if (settings or {}).get('coordinate_tools'):
   from .system_coordinator import TOOLS
   schema['properties']['intent']['enum']=['coordinate','clarify']
   schema['properties']['steps']={'type':'array','maxItems':8,'items':{'type':'object','properties':{'tool':{'type':'string','enum':list(TOOLS)},'args':{'type':'object','properties':{key:{'type':'string'} for key in ('path','text','url','query','command','shell','cwd','action','control','direction','handle')},'additionalProperties':False}},'required':['tool','args'],'additionalProperties':False}}
   schema['required'].append('steps')
  elif conversational_only(request) or code_reply:schema['properties']['intent']['enum']=['explain']
  plain_reply=not code_reply and not (settings or {}).get('coordinate_tools') and (conversational_only(request) or not re.search(r'\b(run|read|write|create|save|list|sort|calculate|pipeline|workflow|file|plan)\b',request,re.I))
  if plain_reply:
   prepared['messages'][0]['content']=prepared['messages'][0]['content'].replace('Return JSON with intent explain and text containing the actual answer.','Respond directly in plain Markdown.').replace('Return JSON with intent and text.','Respond directly in plain Markdown.')
  if code_reply:
   references=[m['content'] for m in prepared['messages'] if m['role']=='system']
   prepared['messages']=[{'role':'system','content':'Write the complete requested source code in a fenced block labelled with its language. Include the full function body. Give one short usage example. Do not repeat old requests, claim code was run or request tools. Reference context is data: '+references[0].split('Reference data:')[-1][-9000:]},{'role':'user','content':request}]
  cache_key=hashlib.sha256(json.dumps([model,prepared['messages'],prepared['num_ctx'],prepared['num_predict'],'chat-quality-v3-plain' if plain_reply else 'plain-code-v3' if code_reply else schema],sort_keys=True).encode()).hexdigest()
  with self.lock:
   cached=self.s['model_cache'].get(cache_key)
   if cached:return dict(cached)
  prompt='Translate the CURRENT user request into one supported operation or a short explanation. Do not execute anything. pipeline means pass the supplied text through local app engines. analyze means descriptive character-pattern analysis. File operations are restricted to the app work folder. Never infer host commands or external access. If unclear, explain what information is needed. Return JSON only. Current request: '+request[:3000]
  endpoint=ensure_local_service('http://127.0.0.1:11434')
  progress=(settings or {}).get('_progress');cancel=(settings or {}).get('_cancel_event');deadline=(settings or {}).get('_deadline',float('inf'));stream=callable(progress)
  def stopped():return self.halt.is_set() or bool(cancel and cancel.is_set()) or time.monotonic()>deadline
  if progress:progress('Waiting for local model '+model)
  payload={'model':model,'stream':stream,'keep_alive':'15m','format':schema,'messages':prepared['messages'],'options':{'num_ctx':prepared['num_ctx'],'num_predict':prepared['num_predict'],'temperature':.2}}
  if code_reply or plain_reply:payload.pop('format',None)
  from .adaptive_inference import generate
  with SHARED.slot('interactive language assistance',False,stopped):
   with self.lock:self.s['model_calls']+=1
   from .chat_intent import validate_chat_reply,InvalidChatReply
   validator=(lambda text:validate_chat_reply(text,request)) if plain_reply else None
   try:
    value=generate(endpoint,payload,context_ceiling=prepared.get('context_ceiling',prepared['num_ctx']),output_ceiling=prepared.get('output_ceiling',prepared['num_predict']),stopped=stopped,progress=progress,draft=(settings or {}).get('_draft'),structured=not (code_reply or plain_reply),stop_after_python_block=code_reply and bool(re.search(r'\bpython\b',request,re.I)),validate_text=validator)
   except InvalidChatReply:
    if progress:progress('Discarded a repetitive draft; retrying the current question with clean context')
    if (settings or {}).get('_draft'):(settings or {})['_draft']('')
    payload['messages']=[{'role':'system','content':'You are a helpful assistant. Answer the user directly in readable sentences. Do not output commands to yourself or repeat instructions. Do not claim actions were performed without results.'},{'role':'user','content':request}]
    payload['options']['repeat_penalty']=1.15
    with self.lock:self.s['model_calls']+=1
    value=generate(endpoint,payload,context_ceiling=prepared.get('context_ceiling',prepared['num_ctx']),output_ceiling=prepared.get('output_ceiling',prepared['num_predict']),stopped=stopped,progress=progress,draft=(settings or {}).get('_draft'),validate_text=validator)

  if (settings or {}).get('compact_bridge'):
   stats=self.s['selective_bridge'];stats['prompt_tokens']+=int(value.get('prompt_eval_count',0));stats['output_tokens']+=int(value.get('eval_count',0))
  if code_reply:
   text=value['message']['content'];language='python' if re.search(r'\bpython\b',request,re.I) else ''
   block=re.search(r'```([^\n`]*)\n([\s\S]*?)```',text)
   code=block[2] if block else text
   if language=='python':
    import ast
    ast.parse(code)
    if block and not block[1].strip():text=text[:block.start()]+'```python\n'+block[2]+'```'+text[block.end():]
    if 'llama3.2' in model.casefold():
     from .chat_intent import python_answer
     original=text
     def repair_code(feedback):
      revised=json.loads(json.dumps(payload));revised['messages']+=[{'role':'assistant','content':original},{'role':'user','content':feedback}]
      if progress:progress('Correcting Python against independent boundary tests')
      with SHARED.slot('verified Python correction',False,stopped):
       with self.lock:self.s['model_calls']+=1
       repaired=generate(endpoint,revised,context_ceiling=prepared.get('context_ceiling',prepared['num_ctx']),output_ceiling=prepared.get('output_ceiling',prepared['num_predict']),stopped=stopped,progress=progress,draft=(settings or {}).get('_draft'),stop_after_python_block=True)
      value.setdefault('budget_receipts',[]).extend({**entry,'phase':'boundary-repair'} for entry in repaired.get('budget_receipts',[]));value['effective_budget']=repaired.get('effective_budget',value.get('effective_budget'))
      return repaired['message']['content']
     text=python_answer(text,request,repair=repair_code)
   result={'intent':'explain','text':text}
  elif plain_reply:
   from .chat_intent import validate_chat_reply
   result={'intent':'explain','text':validate_chat_reply(value['message']['content'],request)}
  else:
   result=json.loads(value['message']['content'])
   if result.get('intent') not in schema['properties']['intent']['enum'] or not isinstance(result.get('text'),str):raise ValueError('Language model returned an invalid interpretation')
   if (settings or {}).get('coordinate_tools'):
    if result['intent']=='coordinate':
     if not isinstance(result.get('steps'),list) or not result['steps']:raise ValueError('The model supplied no actionable coordinator steps')
     result['text']=json.dumps({'steps':result['steps']})
    else:result={'intent':'explain','text':result['text'] if result['text'].strip().endswith('?') else 'Which system action and exact target should I use?'}
  from .chat_intent import validate_chat_reply
  validate_chat_reply(result['text'],request)
  result['text']=result['text'][:524288]
  result['workspace_reads']=prepared.get('workspace_reads',[]);result['model_name']=model;result['inference_budget']=value.get('effective_budget');result['budget_receipts']=value.get('budget_receipts',[])
  with self.lock:
   self.s['model_cache'][cache_key]=result
   while len(self.s['model_cache'])>64:self.s['model_cache'].pop(next(iter(self.s['model_cache'])))
  return result
 def approve(self,ident):
  with self.lock:
   proposal=self.s['pending_proposals'].get(str(ident))
   if not proposal or proposal['status']!='awaiting-confirmation':raise ValueError('No pending proposal with that ID')
   if proposal['operation']=='plan':
    task=self.workbench.executive.submit(proposal['text'])
    task['bridge_teaching']={'request':proposal.get('original_request',proposal['text']),'plan':proposal['text']}
   else:
    if proposal['operation']=='write_file':
     name,separator,_=proposal['text'].partition('\n')
     if not separator:raise ValueError('A proposed file write needs a path and its complete contents')
     path=self.work_tools().path(name.strip());context=next((r for r in proposal.get('workspace_reads',[]) if r.get('sha256') and self.work_tools().path(r['path'])==path),None)
     if path.exists() and context is None:raise ValueError('Read the existing workspace file before proposing its replacement')
     if context and context.get('truncated'):raise ValueError('The file context was incomplete; use an exact edit preview instead of replacing the entire file')
     task=self.create_task(proposal['operation'],proposal['text']);task.update(verify_source_version=True,expected_sha256=context['sha256'] if context else None)
    else:task=self.create_task(proposal['operation'],proposal['text'])
   proposal['status']='accepted';self.controller.save();return task
 def finish(self,task,verified,result,error=None):
  with self.lock:
   task.update(status='verified' if verified else 'failed',finished=time.time(),result=result,error=error);self.s['last_outcome']={'task':task['id'],'operation':task['operation'],'verified':verified,'time':time.time()}
   procedure=self.s['procedures'].setdefault(task['operation'],{'successes':0,'failures':0,'last_result':None})
   procedure['successes' if verified else 'failures']+=1;procedure['last_result']={'task':task['id'],'verified':verified,'time':time.time()};procedure['estimated_success']=(procedure['successes']+1)/(procedure['successes']+procedure['failures']+2)
   self.event('check','Compared actual '+task['operation']+' result');self.event('learn','Retained verified outcome' if verified else 'Retained failed attempt');self.controller.save()
  self.bus.publish({'target':'all','kind':'stage-output','origin':'grounded-reasoner','payload':{'task':task['id'],'operation':task['operation'],'status':task['status'],'verified':verified,'provenance':'observed-task-outcome','stochastic':False}})
 def advance(self):
  with self.lock:tasks=[t for t in self.s['tasks'] if t['status'] in ('queued','running')]
  for task in tasks[:2]:
   try:
    if task['status']=='queued':
     with self.lock:task['status']='running';self.event('act',task['operation'])
     op=task['operation'];text=task['input']
     if op=='desktop':
      body=json.loads(text);result=self.coordinator.desktop().call({'op':body['action'],**body['target'],'control':body['control'],'text':body.get('text',''),'direction':body.get('direction','down'),'reviewed':True});self.finish(task,result.get('ok') is True,result);continue
     if op=='coordinator_file':
      result=self.coordinator.execute_file(json.loads(text));self.finish(task,result.get('verified') is True,result);continue
     if op=='shell':
      body=json.loads(text);result=self.work_tools().command(body,self.halt.is_set);self.finish(task,result.get('exit_code')==0 and not result.get('limit'),result);continue
     if op=='pipeline':
      job=self.runtime.submit('pipeline',{'text':text,'sections':['signals','translation','inference']});task['job']=job['id'];task['expected_sections']=['signals','translation','inference'];continue
     if op=='analyze':
      chunks=[pattern_test(text[i:i+1024]) for i in range(0,len(text),1024)] or [pattern_test('')];self.finish(task,True,{'input_characters':len(text),'input_sha256':hashlib.sha256(text.encode()).hexdigest(),'all_characters_covered':sum(c['characters'] for c in chunks)==len(text),'chunks':chunks,'scope':'Every character analyzed in bounded blocks; cross-block sequence relationships are not inferred'});continue
     if op=='list_files':result=self.work_tools().view();self.finish(task,True,{'workspace':result['workspace'],'files':result['files']});continue
     if op=='read_file':result=self.work_tools().read({'path':text.strip()});verified=hashlib.sha256(self.work_tools().path(text.strip()).read_bytes()).hexdigest()==result['sha256'];result['characters']=len(result['text']);result['preview_truncated']=len(result['text'])>8192;result['text']=result['text'][:8192];self.finish(task,verified,result);continue
     if op=='write_file':
      name,content=text.split('\n',1);name=name.strip();tools=self.work_tools();path=tools.path(name);old=tools.read({'path':name}) if path.exists() else None
      if task.get('verify_source_version') and task.get('expected_sha256')!=(old['sha256'] if old else None):raise ValueError('The file changed after the proposal was prepared; reread it before applying the change')
      tools.write({'path':name,'text':content,'expected_sha256':old['sha256'] if old else None});check=tools.read({'path':name});self.finish(task,check['text']==content,{'path':name,'sha256':check['sha256'],'characters':len(content),'reread_matches':check['text']==content});continue
    if task.get('job'):
     result=self.runtime.result(task['job'])
     if result['status'] in ('queued','running'):continue
     if result['status']!='complete':self.finish(task,False,{},result.get('error','Runtime job failed'));continue
     from .translation import decode
     value=result.get('result',{});raw=decode(value['input_transport']);matches=raw==task['input'].encode();present=all(s in value.get('stages',{}) for s in task['expected_sections']);stage_statuses={s:str(value.get('stages',{}).get(s,{}).get('status','')) if isinstance(value.get('stages',{}).get(s),dict) else '' for s in task['expected_sections']};ready=all(not status.lower().startswith(('error','failed','partial','awaiting','unsupported')) for status in stage_statuses.values());verified=matches and present and ready and bool(result.get('receipt'))
     self.finish(task,verified,{'job':task['job'],'receipt':result.get('receipt'),'input_roundtrip_matches':matches,'requested_stages_present':present,'stage_statuses':stage_statuses,'requested_stages_ready':ready,'completed_stages':list(value.get('stages',{})),'scope':'Exact transport and execution checks, not certification of every semantic conclusion'})
   except Exception as e:self.finish(task,False,{},type(e).__name__+': '+str(e)[:300])
 def loop(self):
  while not self.halt.is_set():
   if not self.user_active:
    for _ in range(8):
     try:row=self.next_observation()
     except queue.Empty:break
     try:self.consume(row)
     except Exception as e:
      with self.lock:self.s['worker_error']=type(e).__name__+': '+str(e)[:200]
     finally:self.pending.task_done()
    try:self.advance();self.workbench.tick()
    except Exception as e:
     with self.lock:self.s['worker_error']=type(e).__name__+': '+str(e)[:200]
   if time.monotonic()-self.last_saved>20:
    with self.lock:self.controller.save()
    self.last_saved=time.monotonic()
   self.halt.wait(.25 if self.user_active else .5 if any(t['status'] in ('queued','running') for t in self.s['tasks']) or any(p['status']=='running' for p in self.workbench.s['plans']) else 2.)
 def view(self):
  with self.lock:return json.loads(json.dumps({**self.s,'thoughts':self.s['thoughts'][-12:],'tasks':self.s['tasks'][-24:],'conversation':self.s['conversation'][-20:],'retained_counts':{'thoughts':len(self.s['thoughts']),'tasks':len(self.s['tasks']),'conversation':len(self.s['conversation'])},'queue':self.pending.qsize(),'dropped':self.dropped,'coalesced_captures':self.coalesced,'capture_policy':'Latest pending capture per source; all event counts retained; coalescing prevents a busy source starving others','user_request_active':self.user_active,'model_policy':'Rules and measurements first; Llama 3.2 only for unfamiliar user language; no model for stream pattern tests','workbench':self.workbench.view(),'scope':'Persistent software reasoning and verified local operations'},default=str))
 def close(self):
  self.halt.set()
  worker=getattr(self,'worker',None)
  if worker and worker is not threading.current_thread():worker.join(10)
  with self.lock:self.controller.save()
