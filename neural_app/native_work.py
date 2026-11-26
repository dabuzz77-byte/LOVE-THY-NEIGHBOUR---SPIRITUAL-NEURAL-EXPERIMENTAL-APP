"""Native compositional work, conversational follow-ups and tested Python export."""
import copy,difflib,hashlib,json,re,time
from .reasoning_engine import pipeline
from .native_synthesis import bounded
from .instruction_clauses import split_clauses,partition_input

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def parse_steps(instruction):
 text=instruction.strip()
 text=re.sub(r'^(?:please\s+|could you\s+|can you\s+)','',text,flags=re.I)
 chunks=split_clauses(text)
 aliases={'trim':'strip','strip':'strip','trim whitespace':'strip','lowercase':'lower','convert to lowercase':'lower','uppercase':'upper','convert to uppercase':'upper','reverse':'reverse','split into lines':'lines','split lines':'lines','lines':'lines','split into words':'words','words':'words','remove duplicates':'unique','deduplicate':'unique','unique':'unique','sort':'sort','sort ascending':'sort','join lines':'join','join':'join','sum':'sum','mean':'mean','average':'mean','median':'median','minimum':'minimum','maximum':'maximum','count':'count','convert to numbers':'numbers','numbers':'numbers','parse json':'json','parse csv':'csv','frequencies':'frequencies'}
 result=[]
 for chunk in chunks:
  original=chunk.strip();chunk=original.casefold()
  from .semantic_steps import parse as semantic_step
  semantic=semantic_step(original)
  if semantic is not None:result.append(semantic);continue
  if chunk in aliases:result.append({'op':aliases[chunk]});continue
  grouping=re.fullmatch(r'group by ([a-zA-Z_][\w-]{0,63}) (count|sum|mean|minimum|maximum)(?: ([a-zA-Z_][\w-]{0,63}))?',original,re.I)
  if grouping:
   field,aggregate,measure=grouping.groups();aggregate=aggregate.lower()
   if aggregate!='count' and not measure:return None
   result.append({'op':'group','field':field,'aggregate':aggregate,**({'value_field':measure} if measure else {})});continue
  replacement=re.fullmatch(r'''replace ["'](.*?)["'] with ["'](.*?)["']''',original,re.I)
  if replacement:result.append({'op':'replace','old':replacement[1],'new':replacement[2]});continue
  if chunk=='sort descending':result.append({'op':'sort','descending':True});continue
  field_sort=re.fullmatch(r'sort by ([a-zA-Z_][\w-]{0,63})(?: (ascending|descending))?',original,re.I)
  if field_sort:result.append({'op':'sort','field':field_sort[1],'descending':(field_sort[2] or '').lower()=='descending'});continue
  if chunk in ('double','halve'):result.append({'op':'scale' if chunk=='double' else 'divide','value':2});continue
  match=re.fullmatch(r'(add|subtract|multiply by|scale by|divide by|take)\s+(-?\d+(?:\.\d+)?)',chunk)
  if match:
   word,number=match.groups();value=float(number) if '.' in number else int(number)
   result.append({'op':'take','count':value} if word=='take' else {'op':'add' if word in ('add','subtract') else 'divide' if word=='divide by' else 'scale','value':-value if word=='subtract' else value});continue
  match=re.fullmatch(r'(?:extract|select) field ([a-zA-Z_][\w-]{0,63})',original,re.I)
  if match:result.append({'op':'field','name':match[1]});continue
  match=re.fullmatch(r'(?:keep|filter) (greater than|less than|at least|at most|equal to) (-?\d+(?:\.\d+)?)',chunk)
  if match:
   result.append({'op':'filter','relation':{'greater than':'greater','less than':'less','at least':'at_least','at most':'at_most','equal to':'equal'}[match[1]],'value':float(match[2])});continue
  return None
 return result if result and len(result)<=12 else None

def read_value(text):
 try:value=json.loads(text)
 except ValueError:value=text.lstrip(' \r\n')
 return bounded(value)

def python_export(steps,value,expected):
 lines=['def transform(value):'];level='    '
 for index,step in enumerate(steps):
  op=step['op'];expression=None
  if op in ('strip','lower','upper'):expression='value.'+op+'()'
  elif op=='reverse':expression='value[::-1]'
  elif op=='lines':expression='value.splitlines()'
  elif op=='join':expression=repr(step.get('separator','\n'))+'.join(str(item) for item in value)'
  elif op=='sort' and not step.get('field'):expression='sorted(value, reverse='+repr(bool(step.get('descending',False)))+')'
  elif op=='sort':
   sign='-' if step.get('descending') else ''
   lines+=['    decorated = [[item['+repr(step['field'])+'], '+sign+'index, item] for index, item in enumerate(value)]','    decorated = sorted(decorated, reverse='+repr(bool(step.get('descending',False)))+')','    value = [item[2] for item in decorated]'];continue
  elif op=='words':
   lines+=['    words = []',"    current_word = ''",'    for character in value:', '        if character.isalnum():','            current_word = current_word + character','        else:','            if current_word:','                words.append(current_word)',"                current_word = ''",'    if current_word:','        words.append(current_word)','    value = words'];continue
  elif op=='frequencies':
   lines+=['    counts = {}','    for item in value:','        key = str(item)','        if key in counts:','            counts[key] = counts[key] + 1','        else:','            counts[key] = 1','    value = counts'];continue
  elif op=='group':
   field=repr(step['field']);aggregate=step.get('aggregate','count');measure=repr(step.get('value_field'))
   lines+=['    if not isinstance(value, list) or len(value) > 512:',"        raise ValueError('Group requires at most 512 table rows')",'    groups = {}','    for row in value:','        if not isinstance(row, dict) or not isinstance(row['+field+'], str):',"            raise ValueError('Group keys must be text in table rows')",'        key = row['+field+']']
   if aggregate!='count':lines+=['        number = row['+measure+']','        if isinstance(number, bool) or not (isinstance(number, int) or isinstance(number, float)) or abs(number) > 1e100 or number - number != 0:',"            raise ValueError('Group measurements must be finite numbers')"]
   lines+=['        if key not in groups:','            groups[key] = []','        groups[key].append('+('1' if aggregate=='count' else 'row['+measure+']')+')','    result = []','    for key in groups:','        items = groups[key]']
   expressions={'count':'len(items)','sum':'sum(items)','mean':'sum(items) / len(items)','minimum':'min(items)','maximum':'max(items)'}
   lines+=['        result.append({"key": key, "value": '+expressions[aggregate]+', "count": len(items)})','    value = result'];continue
  elif op in ('count','sum','minimum','maximum'):expression={'count':'len','sum':'sum','minimum':'min','maximum':'max'}[op]+'(value)'
  elif op=='mean':expression='sum(value) / len(value)'
  elif op=='numbers':expression='[float(item) for item in value]'
  elif op=='take':expression='value[:'+repr(step['count'])+']'
  elif op=='replace':expression='value.replace('+repr(step['old'])+', '+repr(step['new'])+')'
  elif op=='filter':
   relation={'equal':'==','greater':'>','less':'<','at_least':'>=','at_most':'<=','contains':'contains'}.get(step.get('relation','equal'))
   if relation is None:raise ValueError('Unknown filter relation')
   item='item['+repr(step['field'])+']' if step.get('field') is not None else 'item'
   condition=repr(step['value'])+' in '+item if relation=='contains' else item+' '+relation+' '+repr(step['value'])
   expression='[item for item in value if '+condition+']'
  elif op=='median':
   lines+=['    ordered = sorted(value)','    size = len(ordered)','    if size % 2:','        value = ordered[size // 2]','    else:','        value = (ordered[size // 2 - 1] + ordered[size // 2]) / 2'];continue
  elif op=='unique':
   lines+=['    kept = []','    seen_keys = []','    for item in value:','        item_key = native_data_key(item)','        if item_key not in seen_keys:','            seen_keys.append(item_key)','            kept.append(item)','    value = kept'];continue
  elif op in ('scale','add','divide'):
   operator={'scale':'*','add':'+','divide':'/'}[op];operand=repr(step['value'])
   lines+=['    if isinstance(value, list):','        value = [item '+operator+' '+operand+' for item in value]','    else:','        value = value '+operator+' '+operand];continue
  elif op=='field':
   name=repr(step['name']);lines+=['    if isinstance(value, list):','        value = [item['+name+'] for item in value]','    else:','        value = value['+name+']'];continue
  else:raise ValueError('Python export does not yet support '+op+'; the native workflow remains available')
  # List comprehensions stay inside the bounded function test subset.
  if op=='join':
   lines+=['    pieces = [str(item) for item in value]','    value = '+repr(step.get('separator','\n'))+'.join(pieces)']
  else:lines.append(level+'value = '+expression)
 lines.append('    return value');source='\n'.join(lines)+'\n'
 if any(step['op']=='unique' for step in steps):
  helper=['def native_data_key(value):','    if isinstance(value, bool):',"        return ['bool', str(value)]",'    if isinstance(value, int):',"        return ['int', str(value)]",'    if isinstance(value, float):',"        return ['float', str(value)]",'    if isinstance(value, str):',"        return ['text', value]",'    if isinstance(value, list):',"        return ['list', [native_data_key(item) for item in value]]",'    if isinstance(value, dict):','        keys = sorted(value)',"        return ['object', [[key, native_data_key(value[key])] for key in keys]]",'    if value == None:',"        return ['null']", "    raise ValueError('Only JSON-compatible values are supported')"]
  source='\n'.join(helper)+'\n\n'+source
 from .function_testing import test_function
 candidates=[value]
 if isinstance(value,str):candidates+=['','  A  ','b\na\nb','β\nα\nβ']
 elif isinstance(value,list):candidates+=[[],[1],[-3,0,2,2],['b','a','b']]
 elif type(value) in (int,float):candidates+=[0,-3,2.5,11]
 cases=[{'args':[copy.deepcopy(value)],'expected':copy.deepcopy(expected)}]
 for sample in candidates[1:]:
  try:output=pipeline(copy.deepcopy(sample),steps)['result']
  except (ValueError,TypeError,ZeroDivisionError,KeyError,IndexError):continue
  cases.append({'args':[copy.deepcopy(sample)],'expected':output})
 checks=test_function({'source':source,'function':'transform','cases':cases})
 if not checks['all_passed']:raise ValueError('Python export failed bounded differential checks; code withheld: '+str(checks.get('diagnostics','')))
 return {'source':source,'source_sha256':digest(source),'checks':checks,'replay_cases':copy.deepcopy(cases),'scope':'Generated pure function checked against independently verified native workflow outputs; no full script or host actions executed.'}

class NativeWork:
 def __init__(self,saved=None):self.state=copy.deepcopy(saved) if isinstance(saved,dict) else {};self.state.setdefault('receipts',[])
 def commit(self,text,value,steps,trace):
  self.state['focus_kind']='workflow'
  bounded(value);receipt={'id':digest([text,value,time.time_ns()])[:20],'request_sha256':digest(text),'input_sha256':digest(trace.get('input')),'output_sha256':digest(value),'steps':steps,'trace':[{**{k:v for k,v in row.items() if k!='result'},'result_sha256':digest(row.get('result')),'result_preview':str(row.get('result'))[:256]} for row in trace.get('trace',[])],'verified':trace.get('verified',False),'time':time.time(),'model_calls':0}
  self.state['previous']=copy.deepcopy(self.state.get('last'));self.state['last']=copy.deepcopy(value);self.state['has_last']=True;self.state['pending']=None;self.state.pop('focus_inquiry',None);self.state.pop('last_code_review',None);self.state['workflow']={'steps':steps,'input':trace.get('input'),'output':copy.deepcopy(value)};self.state['receipts']=(self.state['receipts']+[receipt])[-12:]
  answer=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)
  return {'answer':answer,'value':copy.deepcopy(value),'receipt':receipt,'status':'complete'}
 def think_step(self):
  goal=self.state.get('active_goal')
  if goal and goal['status']=='running':
   from .native_goals import advance
   changed=advance(goal,self);self.state['agenda']={'focus':goal['name'],'action':'execute checked native goal','phase':goal['status'],'completed_stages':goal['cursor'],'total_stages':len(goal['stages'])};return changed
  from .native_inquiry import step
  inquiries=self.state.get('inquiries',{})
  focused=inquiries.get(self.state.get('focus_inquiry'))
  current=focused if focused and focused['phase']=='enumerating' else next((v for v in inquiries.values() if v['phase']=='enumerating'),None)
  if current is None:return False
  changed=step(current)
  if changed:self.state['agenda']={'focus':current['name'],'action':'compare hypotheses' if current['phase']=='enumerating' else 'request discriminating observation' if current['phase']=='awaiting-observation' else 'review hypothesis set','phase':current['phase'],'question':current['question'],'candidate_count':len(current['survivors']),'sequence':current['sequence']}
  return changed
 def inquiry_summary(self,details=False):
  from .native_inquiry import explain
  if self.state.get('focus_kind')=='open-reasoning' and self.state.get('open_reasoning'):
   from .open_reasoning import render
   return render(self.state['open_reasoning'])
  if self.state.get('focus_kind')=='general-reasoning':
   from .general_reasoning import summary
   return 'Retained general reasoning result and next evidence check:\n'+json.dumps(self.state.get('general_reasoning_result') if details else summary(self.state.get('general_reasoning_result')),ensure_ascii=False,indent=2)
  mission=self.state.get('sphere_mission')
  if mission and self.state.get('focus_kind')=='sphere-mission':return 'Sphere task “'+mission['name']+'”: '+mission['status']+'; current role '+mission['phase']+'. '+str(len(mission['trace']))+' role records retained. '+('Final result committed.' if mission['committed'] else 'No final result committed yet.')
  lesson=self.state.get('workflow_lesson')
  if lesson and self.state.get('focus_kind')=='workflow-lesson':return 'Learning “'+lesson['name']+'”: '+str(len(lesson['examples']))+' training pairs and '+str(len(lesson['validation']))+' validation pairs retained. Supply at least two of each on distinct inputs. No procedure has been learned yet.'
  if self.state.get('focus_kind')=='goal':
   from .native_goals import summary
   return summary(self.state.get('active_goal'))
  collection=self.state.get('inquiries',{});current=collection.get(self.state.get('focus_inquiry')) or (list(collection.values())[-1] if collection else None)
  if current:return explain(current,details)
  study=self.state.get('self_study')
  if study:return 'I am running a bounded native practice study using a registered oracle.\n\n'+explain(study,details)
  results=self.state.get('study_results',[])
  if results:
   latest=results[-1];return 'No inquiry is currently computing. The latest native practice tested '+latest['task']+' on a fresh input; its prediction '+('matched' if latest['passed'] else 'did not match')+' the registered oracle. The next study waits for its scheduled interval.'
  return 'No inquiry is active. Give me observed input/output examples so I can compare explanations and select a useful next test.'
 def thought_status(self):
  from .native_inquiry import view
  study=self.state.get('self_study')
  return {'active_goal':copy.deepcopy(self.state.get('active_goal')),'agenda':copy.deepcopy(self.state.get('agenda',{})),'inquiries':[view(i) for i in self.state.get('inquiries',{}).values()],'autonomous_study':view(study) if study else None,'study_results':copy.deepcopy(self.state.get('study_results',[])),'scope':'Recorded hypotheses, observations and selected next checks. Autonomous practice uses a named registered native oracle, not a world-field measurement. No language model or external action.'}
 def autonomous_step(self,interval_seconds=30):
  from .native_inquiry import create,step,answer,apply_candidate
  if any(i['phase']=='enumerating' for i in self.state.get('inquiries',{}).values()):return False
  now=time.time();interval_seconds=max(2,min(120,float(interval_seconds)))
  if self.state.get('next_self_study',0)>now+interval_seconds:self.state['next_self_study']=now+interval_seconds
  if now<self.state.get('next_self_study',0):return False
  oracles={'absolute':abs,'double':lambda x:x*2,'negate':lambda x:-x,'uppercase':lambda x:x.upper(),'increment_then_double':lambda x:(x+1)*2,'double_then_increment':lambda x:x*2+1}
  study=self.state.get('self_study')
  if not study:
   metrics=self.state.setdefault('study_metrics',{});kind=min(oracles,key=lambda k:metrics.get(k,0));index=sum(metrics.values());is_text=kind=='uppercase';initial='' if is_text else 0
   study=create({'name':'native practice '+kind,'examples':[{'input':initial,'output':oracles[kind](initial)}],'operations':['lower','upper','strip','reverse'] if is_text else ['absolute','double','negate','increment'],'probes':[' A ','β','ab'] if is_text else [-3-index,1+index,2+index],'max_depth':2 if '_then_' in kind else 1});study['practice_oracle']=kind;study['practice_index']=index;self.state['self_study']=study
  kind=study.get('practice_oracle')
  if kind not in oracles:self.state.pop('self_study',None);return False
  if study['phase']=='enumerating':return step(study)
  if study['phase']=='awaiting-observation':
   value=copy.deepcopy(study['selected_probe']['input']);actual=oracles[kind](value);answer(study,{'input':value,'output':actual});study['last_oracle_observation']={'input':value,'output':actual,'source':'registered independent native practice oracle'};return True
  if study['phase']=='consistent-candidate':
   value=' Fresh β '+str(study['practice_index']) if kind=='uppercase' else -(101+study['practice_index']);prediction=apply_candidate(study,value);actual=oracles[kind](value);passed=type(prediction['prediction'])==type(actual) and prediction['prediction']==actual
   result={'task':kind,'candidate':prediction['program'],'fresh_input':value,'predicted':prediction['prediction'],'actual':actual,'passed':passed,'observations':len(study['observations']),'source':'registered native practice oracle','time':now}
  else:result={'task':kind,'passed':False,'status':study['phase'],'source':'bounded native practice catalogue','time':now}
  self.state['study_results']=(self.state.get('study_results',[])+[result])[-16:];metrics=self.state.setdefault('study_metrics',{});metrics[kind]=metrics.get(kind,0)+1;self.state['next_self_study']=now+interval_seconds;self.state.pop('self_study',None);return True
 def handle(self,text):
  from .conversational_requests import normalize,questions
  original=text;text=normalize(text)
  from .native_requests import resolve_clarification,compile_request,execute_request
  repaired=resolve_clarification(text,self)
  if repaired is not None:return repaired
  from .workflow_revision import respond as revise_workflow
  revised=revise_workflow(text,self)
  if revised is not None:return revised
  from .table_work import respond as table_response
  table=table_response(text,self)
  if table is not None:return table
  candidate=compile_request(text,self.state)
  if candidate and (candidate.get('clarification') or candidate.get('semantic_slots')):return execute_request(candidate,self)
  parts=questions(text)
  if parts:
   from .shared_controller import respond as composed
   result=composed('Work request:\n'+'\n'.join(str(i)+'. '+p for i,p in enumerate(parts,1)),self)
   result['request_interpretation']={'original':original,'stages':parts,'basis':'Explicit Also question boundaries outside quoted data'}
   return result
  from .native_language_transfer import command,apply
  taught=command(text,self)
  if taught is not None:return taught
  result=self._handle_builtin(text)
  if result is not None:return result
  learned=apply(text,self)
  if learned is not None:return learned
  from .native_reading_knowledge import respond as reading_knowledge
  return reading_knowledge(text,self.state)
 def _handle_builtin(self,text):
  key=text.casefold().strip().rstrip('?.!')
  from .investigation_dialogue import respond as investigation_response
  investigation=investigation_response(text,self.state)
  if investigation is not None:return investigation
  from .study_reasoning import respond as study_response
  study=study_response(text,self.state)
  if study is not None:return study
  from .relational_induction import respond as relational_learning
  relation=relational_learning(text,self.state)
  if relation is not None:return relation
  from .concept_dialogue import respond as concept_respond
  concept=concept_respond(text,self.state)
  if concept is not None:return concept
  from .practical_decisions import respond as decision_conversation
  decision=decision_conversation(text,self.state)
  if decision is not None:return decision
  from .grounded_reading_dialogue import respond as reading_conversation
  reading=reading_conversation(text,self.state)
  if reading is not None:return reading
  from .conversation_navigation import respond as conversation_respond
  conversation=conversation_respond(text,self.state)
  if conversation is not None:return conversation
  from .evidence_workbench import respond as evidence_respond
  evidence=evidence_respond(text,self.state)
  if evidence is not None:return evidence
  from .validated_forecast import respond as forecast_respond
  forecast=forecast_respond(text,self.state)
  if forecast is not None:return forecast
  if self.state.get('focus_kind')=='open-reasoning' and re.match(r'^goal:\s*',text,re.I):
   from .open_reasoning import respond as open_goal_response
   opened=open_goal_response(text,self.state)
   if opened is not None:return opened
  from .practical_dialogue import respond as practical_respond
  practical=practical_respond(text,self)
  if practical is not None:return practical
  from .reasoning_workspace import respond as workspace_respond
  workspace=workspace_respond(text,self.state)
  if workspace is not None:return workspace
  from .formula_codegen import respond as formula_respond
  formula=formula_respond(text,self)
  if formula is not None:return formula
  if key in ('explain result plainly','explain the result plainly') and self.state.get('focus_kind') in ('code','workflow','task-bundle','task-preview','broad-reasoning'):
   focus=self.state['focus_kind'];lines=[]
   if focus=='code':
    review=self.state.get('last_code_review',{});lines=['This is the recorded code review; no code was rerun.']
    for label in ('checks','training','validation'):
     checks=review.get(label)
     if isinstance(checks,dict):lines.append(label+': '+str(checks.get('passed',0))+'/'+str(checks.get('total',0))+' cases passed.')
    if review.get('all_retained_checks_passed') is False:lines.append('An earlier counterexample remains unresolved.')
    if review.get('status'):lines.append('Review status: '+review['status']+'.')
    lines.append(review.get('scope','The checks cover their recorded inputs, not every possible input.'))
   elif focus=='workflow':
    lines=['The current retained value is '+json.dumps(self.state.get('last'),ensure_ascii=False)+'.'];workflow=self.state.get('workflow',{})
    if digest(workflow.get('output'))==digest(self.state.get('last')):lines.append('The recorded operations were '+ ' → '.join(s['op'] for s in workflow.get('steps',[]))+'.')
    else:lines.append('The current value differs from the latest workflow receipt; no new transformation is claimed.')
   elif focus=='task-bundle':lines=['The completed task bundle committed its checked results to working memory.']+[r['id']+': '+r['status'] for r in self.state.get('last_task_bundle',{}).get('tasks',[])]
   elif focus=='task-preview':lines=['This is a task preview. No task result is claimed; execution and validation still need to succeed.']
   else:lines=[self.state.get('broad_reasoning_result',{}).get('answer','No broad result is retained.')]
   return {'status':'complete','answer':'\n\n'.join(lines),'action_repeated':False,'model_calls':0}
  if key in ('reasoning breadth report','broad reasoning assessment'):
   from .breadth_assessment import view
   return view()
  if key in ('story reasoning report','narrative reasoning assessment'):
   from .narrative_assessment import view
   return view()
  if key in ('broad reasoning status','explain broad result'):
   report=self.state.get('broad_reasoning_result')
   if not report:return {'status':'needs-input','answer':'No broad-task result is retained.','model_calls':0}
   return {'status':report['status'],'answer':report['answer']+'\n\nRecorded computation:\n'+json.dumps(report.get('evidence',{}),ensure_ascii=False,indent=2),'action_repeated':False,'model_calls':0}
  from .native_task_batch import code_followup
  code_reply=code_followup(text,self)
  if code_reply is not None:return code_reply
  if key.startswith('preview tasks:'):
   from .native_task_batch import preview
   return preview(json.loads(text.split(':',1)[1]),self)
  revision=re.fullmatch(r'revise preview task ([A-Za-z_]\w*):\s*(.+)',text,re.I|re.S)
  if revision:
   from .native_task_batch import preview
   body=copy.deepcopy(self.state.get('previewed_tasks'));changes=json.loads(revision[2])
   if not body or not isinstance(changes,dict) or 'id' in changes:raise ValueError('Choose a previewed task and update its fields without changing its identifier')
   task=next((t for t in body['tasks'] if t['id']==revision[1]),None)
   if task is None:raise ValueError('No previewed task has that identifier')
   task.update(changes);return preview(body,self)
  if key=='cancel previewed tasks':
   self.state.pop('previewed_tasks',None);return {'status':'cancelled','answer':'Task preview cancelled. Completed results are unchanged.','model_calls':0}
  if key=='run previewed tasks':
   from .native_task_batch import run
   body=self.state.get('previewed_tasks')
   if not body:return {'status':'needs-input','answer':'Preview a task bundle first.','model_calls':0}
   result=run(copy.deepcopy(body),self)
   if result['committed']:self.state.pop('previewed_tasks',None)
   return result
  from .reference_language import clarify
  clarified=clarify(text,self.state.get('broad_reasoning_result')) if self.state.get('focus_kind')=='broad-reasoning' else None
  if clarified is not None:self.state['broad_reasoning_result']=copy.deepcopy(clarified);return clarified
  from .broad_reasoning import respond as broad_respond
  broad=broad_respond(text,self.state.get('broad_reasoning_result') if self.state.get('focus_kind')=='broad-reasoning' else None)
  if broad is not None:
   self.state['broad_reasoning_result']=copy.deepcopy(broad);self.state['focus_kind']='broad-reasoning';return broad
  if self.state.get('focus_kind')=='general-reasoning':
   from .general_reasoning import followup
   recalled=followup(text,self.state.get('general_reasoning_result'))
   if recalled is not None:return recalled
  if key.startswith('run tasks:'):
   from .native_task_batch import run
   return run(json.loads(text.split(':',1)[1]),self)
  direct_code=re.fullmatch(r'(?:write|create|generate) (?:a )?python(?: function)? (?:to|for)\s+(.+)',text,re.I|re.S)
  if direct_code:
   from .native_task_batch import code_request
   return code_request(direct_code[1],self)
  from .open_reasoning import respond as open_response
  opened=open_response(text,self.state)
  if opened is not None:return opened
  from .general_reasoning import request as reasoning_request
  body=reasoning_request(text,self.state.get('general_reasoning_spec'))
  if body is not None:
   from .general_reasoning import reason,retain
   result=reason(body)
   retain(self.state,body,result);self.state['focus_kind']='general-reasoning'
   return {'status':result.get('status','complete'),'answer':json.dumps(result,ensure_ascii=False,indent=2),'general_reasoning':result,'model_calls':0}
  if key in ('general reasoning status','show reasoning assumptions'):
   from .general_reasoning import summary
   current=summary(self.state.get('general_reasoning_result'))
   return {'status':'complete' if current else 'needs-input','answer':json.dumps({'result':current,'assumptions':self.state.get('general_reasoning_spec')},ensure_ascii=False,indent=2),'general_reasoning':current}
  if key in ('list native operations','show native operations'):
   from .native_operations import catalogue
   result=catalogue();return {'status':'complete','answer':json.dumps(result,ensure_ascii=False,indent=2),'operations':result}
  if key in ('show last result','what was the result','what is the last result'):
   if not self.state.get('has_last'):return {'status':'needs-input','answer':'No completed result is available yet.'}
   value=copy.deepcopy(self.state['last'])
   return {'status':'complete','answer':value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2),'value':value,'recalled':True}
  if key in ('are there other solutions','is that unique','check for other solutions'):
   from .constraint_reasoning import solve
   spec=copy.deepcopy(self.state.get('last_constraint_spec'))
   if not spec:return {'status':'needs-input','answer':'Supply a constraint problem first so I can check its alternatives.'}
   if spec.get('objective') is not None:return {'status':'needs-input','answer':'The previous task optimised an objective. Supply a feasibility problem without that objective to check alternative solutions.'}
   spec.update(check_uniqueness=True,solution_limit=2);report=solve(spec)
   self.state.update(last_constraint_result=copy.deepcopy(report),focus_kind='constraints')
   return {'status':'complete' if report['uniqueness']!='undetermined' else 'incomplete','answer':json.dumps(report,ensure_ascii=False,indent=2),'value':report,'verification':'Alternatives are explicitly checked in the supplied finite domains; budget exhaustion leaves uniqueness undetermined.'}
  if key in ('cancel pending input','cancel pending request'):
   existed=bool(self.state.pop('pending',None));return {'status':'cancelled','answer':'Pending input request cancelled.' if existed else 'No input request is pending.'}
  if key in ('what input are you waiting for','what are you waiting for'):
   pending=self.state.get('pending')
   return {'status':'needs-input' if pending else 'complete','answer':'Waiting for input to: '+ ' → '.join(s['op'] for s in pending)+'. Use input: followed by literal text or JSON.' if pending else 'No input request is pending.','steps':copy.deepcopy(pending)}
  revision=re.fullmatch(r'(?:change|replace) step (\d+) (?:to|with):\s*(.+)',text,re.I|re.S)
  if revision:
   workflow=self.state.get('workflow')
   if not workflow:return {'status':'needs-input','answer':'Run a workflow first, then specify which step to change.'}
   index=int(revision[1])-1;replacement=parse_steps(revision[2])
   if not 0<=index<len(workflow['steps']) or not replacement:raise ValueError('Choose an existing step and supported replacement operations')
   steps=copy.deepcopy(workflow['steps']);steps[index:index+1]=replacement
   result=pipeline(copy.deepcopy(workflow['input']),steps)
   reply=self.commit(text,result['result'],steps,result);reply['revision']={'changed_step':index+1,'replayed_from_original_input':True};return reply
  if key.startswith('run learned skill:') and hasattr(self,'improvement_engine'):
   result=self.improvement_engine.run(json.loads(text.split(':',1)[1]))
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'status':'complete','managed_skill':result,'model_calls':0}
  if key.startswith('reasoning episode:') or key in ('reasoning episode status','cancel reasoning episode'):
   from .reasoning_episode import command
   body=json.loads(text.split(':',1)[1]) if ':' in text else {'op':'cancel' if key.startswith('cancel') else 'status'}
   result=command(self.state,body)
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'status':result['status'] if result else 'needs-input','reasoning_episode':result}
  if key in ('help','capabilities','what can you do','what are your capabilities','status','progress','why','what failed','what are you thinking','what is your thought process','explain your reasoning','show your work','continue','hello','hi','stop','cancel','list tasks','show tasks') or re.match(r'^(remember|recall|forget|deliberate)\b',key):return None
  if key.startswith('sphere task:'):
   from .sphere_mission import create,summary
   if self.state.get('sphere_mission',{}).get('status')=='running':return {'answer':'A sphere task is already running. Use sphere task status or cancel sphere task.','status':'needs-input'}
   mission=create(json.loads(text.split(':',1)[1]),self.state);self.state['sphere_mission']=mission;self.state['focus_kind']='sphere-mission'
   return {'answer':'Sphere roles will compare → validate → predict → act → verify → retain. Current phase: '+mission['phase']+'.','status':'running','sphere_mission':summary(mission)}
  if key in ('sphere task status','cancel sphere task'):
   from .sphere_mission import summary
   mission=self.state.get('sphere_mission')
   if key=='cancel sphere task' and mission and mission['status']=='running':mission['status']='cancelled'
   return {'answer':json.dumps(summary(mission),ensure_ascii=False,indent=2),'status':mission['status'] if mission else 'needs-input','sphere_mission':summary(mission)}
  if key.startswith('sphere experiment:'):
   from .relevant_experiment import run
   report=run(self.state,json.loads(text.split(':',1)[1]));self.state['focus_kind']='relevant-experiment'
   return {'answer':report['question']+'\nProcedure passed '+str(report['passed'])+'/'+str(report['total'])+' supplied cases; unchanged-input baseline passed '+str(report['baseline_passed'])+'/'+str(report['total'])+'. '+('A counterexample revoked the workflow.' if report['revoked'] else 'The workflow remains available.')+'\n'+report['scope'],'status':'experiment-failed' if report['revoked'] else 'experiment-passed','experiment':report}
  checked=re.fullmatch(r'check workflow (.+?):\s*(.+)',text,re.I|re.S)
  if checked:
   from .artifact_memory import check_workflow
   name=checked[1].strip().casefold();result=check_workflow(self.state,name,json.loads(checked[2]));self.state['focus_kind']='workflow-check';self.state['last_workflow_check']=copy.deepcopy(result)
   return {'answer':('Workflow check passed.' if result['passed'] else 'Counterexample found. The workflow is revoked; goals depending on it will stop before using it.')+'\n'+json.dumps(result,ensure_ascii=False,indent=2),'status':'checked' if result['passed'] else 'revoked','workflow_check':result}
  teach=re.fullmatch(r'(?:teach|learn) a workflow (?:called|named) ([\w -]{1,60})',text,re.I)
  if teach:
   self.state['workflow_lesson']={'name':teach[1].strip().casefold(),'examples':[],'validation':[]};self.state['focus_kind']='workflow-lesson'
   return {'status':'needs-input','answer':'Give me two training examples, then two separate validation examples. Use example: {"input":1,"output":2} and validation: {"input":3,"output":6}. I will derive the steps from training only.'}
  if key=='cancel workflow lesson':
   self.state.pop('workflow_lesson',None);return {'status':'cancelled','answer':'Workflow lesson cancelled. Existing saved work is unchanged.'}
  if key.startswith(('example:','validation:')) and self.state.get('workflow_lesson'):
   lesson=self.state['workflow_lesson'];slot='validation' if key.startswith('validation:') else 'examples';row=json.loads(text.split(':',1)[1])
   if not isinstance(row,dict) or 'input' not in row or 'output' not in row:raise ValueError('Provide an input/output pair')
   bounded(row['input']);bounded(row['output'])
   if any(digest(r['input'])==digest(row['input']) for r in lesson['examples']+lesson['validation']):raise ValueError('Use a different input for each training and validation example')
   if len(lesson[slot])>=8:raise ValueError('At most eight pairs per set')
   if len(json.dumps(lesson,ensure_ascii=True))+len(json.dumps(row,ensure_ascii=True))>32768:raise ValueError('Workflow lesson storage budget reached')
   lesson[slot].append(copy.deepcopy(row))
   if len(lesson['examples'])<2 or len(lesson['validation'])<2:return {'status':'needs-input','answer':'Retained '+str(len(lesson['examples']))+' training and '+str(len(lesson['validation']))+' validation pairs. '+('Supply another training example.' if len(lesson['examples'])<2 else 'Supply separate validation examples.')}
   text='learn workflow from examples: '+json.dumps(lesson);key=text.casefold();self.state.pop('workflow_lesson',None)
  if key.startswith(('learn workflow from examples:','plan from examples:')):
   from .native_example_planner import solve
   body=json.loads(text.split(':',1)[1]);report=solve(body);reports=self.state.setdefault('example_plans',{});reports[report['name']]=copy.deepcopy(report)
   while len(reports)>8:reports.pop(next(iter(reports)))
   self.state['focus_kind']='example-plan';self.state['last_example_plan']=report['name']
   previous=self.state.get('workflow_library',{}).get(report['name'])
   if report['status']=='validated-candidate' and previous and previous.get('active') is False:
    prior=previous.get('latest_check') or {};covered=next((r for r in body.get('examples',[])+body.get('validation',[]) if digest(r['input'])==prior.get('input_sha256')),None)
    from .workflow_contracts import equivalent
    if covered is None or (not equivalent(covered['output'],prior.get('expected')) and body.get('correct_previous_check') is not True):
     report['status']='counterexample-unresolved';report['scope']='Retest the previous counterexample in the new examples, or explicitly set correct_previous_check:true with a corrected output for that same input.';reports[report['name']]=copy.deepcopy(report)
   if report['status']=='validated-candidate':
    library=self.state.setdefault('workflow_library',{});library[report['name']]={'active':True,'superseded_check':copy.deepcopy(previous.get('latest_check')) if previous and previous.get('active') is False else None,'previous_check_explicitly_corrected':body.get('correct_previous_check') is True,'steps':copy.deepcopy(report['steps']),'source_input_sha256':digest(report['source_input']),'source_output_sha256':digest(report['source_output']),'created':time.time(),'validation':copy.deepcopy(report['validation']),'scope':report['scope']}
    while len(library)>32:library.pop(next(iter(library)))
    answer='Derived “'+report['name']+'”: '+' → '.join(row['op']+((' '+str(row['value'])) if 'value' in row else '') for row in report['steps'])+'. '+str(len(report['validation']))+' separate validation cases passed. Use '+report['name']+' on: followed by new input. Future results remain predictions of this finite example-derived procedure.'
   else:answer='Example planner: '+report['status']+'. '+report.get('reason',report.get('scope',''))+' No new workflow was retained. Any previously saved workflow with that name is unchanged.'
   return {'answer':answer,'status':report['status'],'example_plan':report}
  save=re.fullmatch(r'save (?:this|last) workflow as ([\w -]{1,60})',text,re.I)
  if save:
   workflow=self.state.get('workflow')
   if not workflow:return {'status':'needs-input','answer':'Complete a native workflow first so there is a checked procedure to save.'}
   name=save[1].strip().casefold();library=self.state.setdefault('workflow_library',{})
   if library.get(name,{}).get('active') is False:return {'status':'revoked','answer':'That name is revoked. Relearn it with separate validation and include its counterexample; saving the same workflow cannot clear contrary evidence.'}
   library[name]={'steps':copy.deepcopy(workflow['steps']),'source_input_sha256':digest(workflow['input']),'source_output_sha256':digest(workflow['output']),'created':time.time(),'scope':'Saved checked procedure; new inputs are checked again, not assumed correct.'}
   while len(library)>32:library.pop(next(iter(library)))
   return {'status':'complete','answer':'Saved workflow “'+name+'”. Use '+name+' on: followed by a JSON input.','saved_workflow':copy.deepcopy(library[name])}
  reuse=re.fullmatch(r'use (.+?) on:\s*(.+)',text,re.I|re.S)
  if reuse:
   name=reuse[1].strip().casefold();saved=self.state.get('workflow_library',{}).get(name)
   if not saved:return {'status':'needs-input','answer':'No saved workflow named “'+name+'”. Available: '+', '.join(self.state.get('workflow_library',{}))}
   if saved.get('active') is False:return {'status':'revoked','answer':'This workflow was revoked by a counterexample. Supply a corrected procedure and fresh validation before reuse.'}
   value=read_value(reuse[2]);result=pipeline(copy.deepcopy(value),saved['steps']);reply=self.commit(text,result['result'],copy.deepcopy(saved['steps']),result);reply['transfer']={'workflow':name,'source_input_sha256':saved['source_input_sha256'],'fresh_input_sha256':digest(value),'operation_checks_repeated':True};return reply
  revision=re.fullmatch(r'revise goal stage (\d+):\s*(.+)',text,re.I|re.S)
  if revision:
   from .native_goals import create,summary
   goal=self.state.get('active_goal')
   if not goal:return {'status':'needs-input','answer':'No retained goal is available to revise.'}
   if goal['status']=='running':return {'status':'needs-input','answer':'Cancel the running goal before revising its stages.'}
   index=int(revision[1])-1
   if not 0<=index<len(goal['stages']):raise ValueError('Choose an existing goal stage number')
   stages=[{'instruction':row['instruction'],**({'expected':row['expected']} if row['has_expected'] else {})} for row in goal['stages']]
   stages[index]=json.loads(revision[2]);new=create({'name':goal['name'],'input':goal['input'],'stages':stages},self.state.get('workflow_library'))
   new['revision_audit']=(goal.get('revision_audit',[])+[{'stage':index+1,'previous_status':goal['status'],'previous_trace_sha256':digest(goal['trace']),'time':time.time()}])[-8:]
   self.state['active_goal']=new;self.state['focus_kind']='goal'
   return {'status':'running','answer':'Revised stage '+str(index+1)+'. Rechecking the whole goal from its original input.\n'+summary(new),'goal':copy.deepcopy(new)}
  if key.startswith('work toward:'):
   from .native_goals import create,summary
   old=self.state.get('active_goal')
   if old and old['status']=='running':return {'status':'needs-input','answer':'A native goal is already running. Use goal status or cancel goal before replacing it.'}
   goal=create(json.loads(text.split(':',1)[1]),self.state.get('workflow_library'));self.state['active_goal']=goal;self.state['focus_kind']='goal'
   return {'status':'running','answer':summary(goal),'goal':copy.deepcopy(goal)}
  if key in ('goal status','continue goal','cancel goal'):
   from .native_goals import summary
   goal=self.state.get('active_goal')
   if key=='cancel goal' and goal and goal['status']=='running':goal['status']='cancelled'
   elif key=='continue goal':self.think_step()
   return {'answer':summary(goal),'goal':copy.deepcopy(goal),'status':goal['status'] if goal else 'needs-input'}
  focus=self.state.get('focus_inquiry');current=self.state.get('inquiries',{}).get(focus)
  observed=re.fullmatch(r'(?:the (?:observed )?(?:output|answer|result) is|it returns|observed:)\s+(.+)',text,re.I|re.S)
  if observed and current and current.get('selected_probe') and current['phase']=='awaiting-observation':
   from .native_inquiry import answer,view,explain
   answer(current,{'input':copy.deepcopy(current['selected_probe']['input']),'output':read_value(observed[1])});self.think_step();visible=view(current)
   return {'answer':explain(current),'inquiry':visible,'status':current['phase']}
  if key.startswith(('investigate pattern:','find a rule:')):
   from .native_inquiry import create,view,explain
   inquiry=create(json.loads(text.split(':',1)[1]));collection=self.state.setdefault('inquiries',{});collection[inquiry['name']]=inquiry
   while len(collection)>8:collection.pop(next(iter(collection)))
   self.state['focus_kind']='inquiry';self.state['focus_inquiry']=inquiry['name'];self.think_step();visible=view(inquiry)
   return {'answer':explain(inquiry),'inquiry':visible,'status':inquiry['phase']}
  if key.startswith('use inquiry '):
   from .native_inquiry import apply_candidate
   instruction,separator,data=text.partition(':');name=instruction[len('use inquiry '):].strip().casefold();inquiry=self.state.get('inquiries',{}).get(name)
   if inquiry is None or not separator:raise ValueError('Provide an inquiry name and input after a colon')
   result=apply_candidate(inquiry,read_value(data));self.state['focus_kind']='inquiry';self.state['focus_inquiry']=name
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'inquiry_prediction':result,'value':result['prediction'],'status':'prediction'}
  if key.startswith('export inquiry ') and key.endswith(' as python'):
   from .native_inquiry import export_candidate
   name=text[len('export inquiry '):-len(' as python')].strip().casefold();inquiry=self.state.get('inquiries',{}).get(name)
   if inquiry is None:raise ValueError('Unknown inquiry name')
   exported=export_candidate(inquiry);self.state['focus_kind']='code';self.state['last_code_review']={'checks':exported['checks'],'source_sha256':exported['source_sha256'],'scope':exported['scope']}
   return {'answer':'```python\n'+exported['source']+'```\n\nExample checks passed: '+str(exported['checks']['passed'])+'/'+str(exported['checks']['total'])+'. This is an inferred candidate, not proof for arbitrary inputs.','code':exported,'status':'complete'}
  if key.startswith('answer inquiry '):
   from .native_inquiry import answer,view,explain
   instruction,separator,data=text.partition(':');name=instruction[len('answer inquiry '):].strip().casefold();inquiry=self.state.get('inquiries',{}).get(name)
   if inquiry is None:raise ValueError('Unknown inquiry name')
   answer(inquiry,json.loads(data));self.state['focus_kind']='inquiry';self.state['focus_inquiry']=name;self.think_step();visible=view(inquiry)
   return {'answer':explain(inquiry),'inquiry':visible,'status':inquiry['phase']}
  if key in ('what should you test next','what information is missing','explain current inquiry'):
   status=self.thought_status();return {'answer':self.inquiry_summary(True),'thought_status':status,'status':'complete'}
  if key.startswith('run plan:'):
   from .native_plans import run_plan
   spec=json.loads(text.split(':',1)[1]);result=run_plan(spec)
   if result['committed']:
    self.state['previous']=copy.deepcopy(self.state.get('last'));self.state['last']=copy.deepcopy(result['output']);self.state['has_last']=True
   self.state['focus_kind']='plan';self.state.pop('last_code_review',None);self.state['last_plan']=copy.deepcopy(result);self.state['last_plan_spec']=copy.deepcopy(spec)
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'plan':result,'value':result['output'],'status':result['status']}
  if key=='export last plan as python':
   from .native_plans import export_plan
   exported=export_plan(self.state.get('last_plan_spec',{}),self.state.get('last_plan',{}));self.state['last_code_review']={'checks':exported['checks'],'source_sha256':exported['source_sha256'],'scope':exported['scope']}
   return {'answer':'```python\n'+exported['source']+'```\n\nBounded plan-function checks passed: '+str(exported['checks']['passed'])+'/'+str(exported['checks']['total'])+'.','code':exported,'status':'complete'}
  if key.startswith('learn numeric rule:'):
   from .native_rules import learn
   result=learn(json.loads(text.split(':',1)[1]))
   self.state['focus_kind']='rule';self.state['last_rule_review']=copy.deepcopy(result)
   if result['retained']:
    rules=self.state.setdefault('rules',{});rules[result['name']]=copy.deepcopy(result)
    while len(rules)>32:rules.pop(next(iter(rules)))
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'learning':result,'status':'complete' if result['retained'] else 'rejected'}
  if key.startswith(('apply rule ','check rule ')):
   from .native_rules import use
   instruction,separator,data=text.partition(':')
   if not separator:raise ValueError('Supply a JSON value after a colon')
   checking=key.startswith('check rule ');name=instruction[len('check rule ' if checking else 'apply rule '):].strip().casefold();rule=self.state.get('rules',{}).get(name);value=json.loads(data)
   result=use(rule,value['input'] if checking else value,value.get('expected') if checking else None,checking)
   self.state['focus_kind']='rule';self.state['last_rule_review']=copy.deepcopy(result)
   self.state['previous']=copy.deepcopy(self.state.get('last'));self.state['last']=copy.deepcopy(result['prediction']);self.state['has_last']=True
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'rule_result':result,'value':result['prediction'],'status':'complete' if not checking or result['passed'] else 'counterexample'}
  if key in ('compare with previous result','compare that to the last result'):
   if not self.state.get('has_last') or 'previous' not in self.state:return {'answer':'Two retained results are needed for comparison.','status':'needs-input'}
   previous=self.state['previous'];current=self.state['last'];result={'previous':copy.deepcopy(previous),'current':copy.deepcopy(current),'equal':type(previous)==type(current) and previous==current}
   if type(previous) in (int,float) and type(current) in (int,float):result['change']=current-previous
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'comparison':result,'status':'complete'}
  if key in ('explain last plan','why that branch'):
   plan=self.state.get('last_plan')
   return {'answer':'No plan result is retained.' if not plan else json.dumps({'status':plan['status'],'branches':[{'node':r['node'],'dependencies':r['dependencies'],'condition_result':r['branch'],'verified':r['verified']} for r in plan['trace']],'assertions':plan.get('assertions',[]),'scope':plan.get('scope')},ensure_ascii=False,indent=2),'status':'complete'}
  if key=='what did you understand':
   return {'answer':json.dumps({'pending_steps':self.state.get('pending'),'last_workflow':self.state.get('workflow'),'last_plan_status':self.state.get('last_plan',{}).get('status')},ensure_ascii=False,indent=2),'status':'complete'}
  if key=='undo last result':
   if 'previous' not in self.state:return {'answer':'No earlier result is available to restore.','status':'needs-input'}
   self.state['last'],self.state['previous']=self.state['previous'],self.state.get('last');return {'answer':'Restored the previous in-memory result:\n'+json.dumps(self.state['last'],ensure_ascii=False),'value':copy.deepcopy(self.state['last']),'status':'complete','scope':'Only conversation working memory changed; no file or task was undone.'}
  if key.startswith('teach intent:'):
   body=json.loads(text.split(':',1)[1]);phrase=str(body.get('phrase','')).strip().casefold();steps=body.get('steps');examples=body.get('examples');holdout=body.get('holdout')
   if not phrase or len(phrase)>100 or ':' in phrase or not isinstance(examples,list) or not isinstance(holdout,list) or not 2<=len(examples)<=8 or not 2<=len(holdout)<=8:raise ValueError('Teaching needs a short phrase, steps, 2–8 examples and 2–8 held-out cases')
   if {digest(r['input']) for r in examples}&{digest(r['input']) for r in holdout}:raise ValueError('Held-out inputs must differ from teaching inputs')
   checked=[]
   for case in examples+holdout:
    result=pipeline(bounded(case['input']),steps)
    if type(result['result'])!=type(case['output']) or result['result']!=case['output']:raise ValueError('The proposed phrase procedure failed an explicit teaching check')
    checked.append(digest(case))
   recipes=self.state.setdefault('recipes',{});recipes[phrase]={'steps':copy.deepcopy(steps),'case_digests':checked,'teaching_cases':len(examples),'held_out_cases':len(holdout),'updated':time.time()}
   while len(recipes)>32:recipes.pop(next(iter(recipes)))
   return {'answer':'Learned “'+phrase+'” after '+str(len(checked))+' explicit checks. Future inputs still pass every native workflow check.','status':'complete','teaching_checks':len(checked)}
  if key in ('why is this verified','what did you do','explain last result','show last receipt','show evidence'):
   if self.state.get('focus_kind')=='task-bundle':return {'status':'complete','answer':json.dumps(self.state.get('last_task_bundle'),ensure_ascii=False,indent=2),'model_calls':0}
   if self.state.get('focus_kind')=='open-reasoning' and self.state.get('open_reasoning'):
    from .open_reasoning import render
    frame=copy.deepcopy(self.state['open_reasoning']);return {'status':frame['status'],'answer':render(frame)+'\n\n'+frame['scope'],'open_reasoning':frame,'model_calls':0}
   if self.state.get('focus_kind')=='general-reasoning':return {'status':'complete','answer':'The result follows from the retained explicit assumptions and bounded reasoning procedure. Review its scope and completeness before generalising.\n'+json.dumps(self.state.get('general_reasoning_result',{}),ensure_ascii=False,indent=2),'general_reasoning':copy.deepcopy(self.state.get('general_reasoning_result'))}
   if self.state.get('focus_kind')=='constraints':return {'status':'complete','answer':'Candidate assignments were checked against every supplied constraint. Uniqueness requires a complete search or two distinct verified witnesses; a limited search may remain undetermined.\n'+json.dumps(self.state.get('last_constraint_result',{}),ensure_ascii=False,indent=2)}
   if self.state.get('focus_kind')=='sphere-mission':
    from .sphere_mission import summary
    return {'answer':json.dumps(summary(self.state.get('sphere_mission')),ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('focus_kind')=='relevant-experiment':return {'answer':json.dumps(self.state.get('relevant_experiments',[])[-1],ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('focus_kind')=='workflow-check':return {'answer':json.dumps(self.state.get('last_workflow_check',{}),ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('focus_kind')=='workflow-lesson':return {'answer':self.inquiry_summary(),'status':'needs-input'}
   if self.state.get('focus_kind')=='example-plan':return {'answer':'Example-derived procedure and separate validation evidence:\n'+json.dumps(self.state.get('example_plans',{}).get(self.state.get('last_example_plan'),{}),ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('focus_kind')=='goal':
    from .native_goals import summary
    return {'answer':summary(self.state.get('active_goal')),'goal':copy.deepcopy(self.state.get('active_goal')),'status':'complete'}
   if self.state.get('focus_kind')=='preview':return {'answer':'The workflow is only planned. No operation or result is claimed yet.\n'+json.dumps(self.state.get('proposed_work',{}),ensure_ascii=False,indent=2),'status':'planned'}
   if self.state.get('focus_kind')=='acceptance-failure':return {'answer':'The latest proposed result failed your explicit expected-value check. It was not committed; the previous completed result is retained.\n'+json.dumps(self.state.get('last_acceptance_failure',{}),ensure_ascii=False,indent=2),'status':'acceptance-failed'}
   if self.state.get('focus_kind')=='inquiry':return {'answer':self.inquiry_summary(True),'status':'complete'}
   if self.state.get('focus_kind')=='plan':return {'answer':json.dumps(self.state.get('last_plan',{}),ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('focus_kind')=='rule':return {'answer':'Numeric rule evidence and prediction status:\n'+json.dumps(self.state.get('last_rule_review',{}),ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('focus_kind')=='native':return {'answer':'The last reply used this native procedure:\n'+json.dumps(self.state.get('last_native_skill',{}),ensure_ascii=False,indent=2),'status':'complete'}
   if self.state.get('last_code_review'):
    review=self.state['last_code_review'];return {'answer':'The code was checked with the bounded Python function interpreter. Tests cover only their supplied inputs; no full script or host command ran.\n\n```json\n'+json.dumps(review,ensure_ascii=False,indent=2)+'\n```','coding_result':copy.deepcopy(review),'status':'complete'}
   receipt=self.state['receipts'][-1] if self.state['receipts'] else None
   return {'answer':'No completed workflow receipt yet.' if receipt is None else 'Each recorded transformation passed its independent check. This checks the stated operations, not whether they match an unstated intention.\n\n```json\n'+json.dumps(receipt,ensure_ascii=False,indent=2)+'\n```','receipt':receipt,'status':'complete'}
  if key in ('write python for last workflow','export python','show python code'):
   workflow=self.state.get('workflow')
   if not workflow:return {'answer':'Run a native workflow first so I have an input, procedure and checked output to export.','status':'needs-input'}
   self.state['focus_kind']='code';exported=python_export(workflow['steps'],workflow['input'],workflow['output']);self.state['last_code_review']={'source_sha256':exported['source_sha256'],'checks':exported['checks'],'scope':exported['scope']}
   return {'answer':'```python\n'+exported['source']+'```\n\nBounded function checks passed: '+str(exported['checks']['passed'])+'/'+str(exported['checks']['total'])+'. No full script was executed.','code':exported,'status':'complete'}
  if key.startswith('solve constraints:'):
   from .constraint_reasoning import solve
   spec=json.loads(text.split(':',1)[1]);result=solve(spec);self.state.update(last_constraint_spec=copy.deepcopy(spec),last_constraint_result=copy.deepcopy(result),focus_kind='constraints')
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'value':result,'status':'incomplete' if result['status']=='incomplete' else 'complete','verification':'Bounded native constraint solver; its completeness status is retained.'}
  if key.startswith(('test python:','repair python:')):
   body=json.loads(text.split(':',1)[1])
   if not isinstance(body,dict) or 'path' in body:raise ValueError('Supply explicit source, function and cases for the pure function checker')
   if key.startswith('test python:'):
    from .function_testing import test_function
    result=test_function(body)
   else:
    from .tested_repairs import repair
    result=repair(body)
   self.state['focus_kind']='code';self.state['last_code_review']=copy.deepcopy(result)
   answer=('```python\n'+result['source']+'\n```\n\n' if result.get('source') else '')
   if key.startswith('test python:'):answer+='Bounded function checks: '+str(result.get('passed',0))+'/'+str(result.get('total',0))+'. '+str(result.get('diagnostics') or result.get('scope',''))
   else:answer+='Repair status: '+result['status']+'. '+str(result.get('scope',''))+' Files were not changed.'
   return {'answer':answer,'coding_result':result,'status':'complete','verification':'Bounded AST checks; proposed source never replaces a file automatically.'}
  if key in ('run that plan','execute that plan'):
   from .native_requests import execute_request
   proposed=self.state.get('proposed_work')
   if not proposed:return {'status':'needs-input','answer':'No previewed native workflow is waiting. Use preview: followed by a supported request.'}
   result=execute_request({**proposed,'preview':False},self)
   if result.get('status')=='complete':self.state.pop('proposed_work',None)
   return result
  if re.match(r'^(?:take |using |start with |use |preview|plan only|show me the plan for|what is (?:the )?(?:sum|average|mean|median|minimum|maximum|count) of|find (?:the )?|give me (?:the )?|make (?:it )?(?:upper|lower)case|remove duplicate (?:items|values|lines)|sort (?:it |them )?in |(?:uppercase|lowercase|reverse|sort|deduplicate)\s+[\["])',text,re.I) or re.search(r';\s*(?:expect|expected)\s*:',text,re.I):
   from .native_requests import compile_request,execute_request
   compiled=compile_request(text,self.state)
   if compiled:return execute_request(compiled,self)
  instruction,separator,data=partition_input(text);steps=parse_steps(instruction)
  if instruction.strip().casefold() in self.state.get('recipes',{}):steps=copy.deepcopy(self.state['recipes'][instruction.strip().casefold()]['steps'])
  if not steps and separator and not self.state.get('pending'):
   from .native_task_planner import compile_goal
   plan=compile_goal(text)
   if plan:
    if plan['status']!='planned':return {'status':'needs-input','answer':plan['question'],'clarification':True}
    result=pipeline(copy.deepcopy(plan['input']),plan['steps'])
    reply=self.commit(text,result['result'],plan['steps'],result);reply['interpretation']=plan['interpretation'];return reply
  if instruction.strip().casefold() in ('repeat on','redo with','do that again with','use this instead'):
   previous=self.state.get('workflow')
   if not previous:return {'answer':'No previous workflow is available.','status':'needs-input'}
   steps=copy.deepcopy(previous['steps'])
  follow=re.sub(r'^(?:now|and|then|please)\s+','',key)
  follow=re.sub(r'\s+(?:it|that|those|the last result)$','',follow)
  if not separator and self.state.get('has_last') and follow!=key:steps=parse_steps(follow);value=copy.deepcopy(self.state['last'])
  elif separator and steps:value=read_value(data)
  elif self.state.get('pending'):
   if key.startswith('input:'):steps=copy.deepcopy(self.state['pending']);value=read_value(text.split(':',1)[1])
   elif re.match(r'^(?:what|why|how|who|when|where|can|could|would|is|are|do|does)\b',key) or text.rstrip().endswith('?'):return None
   else:steps=copy.deepcopy(self.state['pending']);value=read_value(text)
  elif steps:
   self.state['pending']=steps;return {'answer':'What input should I use for '+instruction+'? Send the text or a JSON value next.','status':'needs-input','steps':steps}
  else:
   first=key.split(' ',1)[0];suggestions=difflib.get_close_matches(first,['calculate','remember','recall','uppercase','lowercase','reverse','statistics'],n=1,cutoff=.82)
   if suggestions and first!=suggestions[0]:return {'answer':'Did you mean “'+suggestions[0]+'”? Please resend the corrected request; nothing ran.','status':'needs-input'}
   return None
  if not steps:return None
  result=pipeline(value,steps);return self.commit(text,result['result'],steps,result)
