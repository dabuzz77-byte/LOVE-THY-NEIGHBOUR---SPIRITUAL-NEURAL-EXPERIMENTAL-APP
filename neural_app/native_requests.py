"""Finite natural request compiler. Produces inspectable pure-data workflows."""
import copy,json,re
from .instruction_clauses import partition_input

def compile_request(text,state):
 from .native_work import parse_steps,read_value
 original=text
 text=re.sub(r'^(?:(?:please|can you|could you|would you)\s+)+','',text.strip(),flags=re.I)
 preview=False
 m=re.match(r'^(?:preview|plan only|show me the plan for)\s*:?\s*(.+)$',text,re.I|re.S)
 if m:preview=True;text=m[1]
 expected=None;has_expected=False
 m=None;quoted=False;escaped=False;depth=0
 for index,char in enumerate(text):
  if quoted:
   if escaped:escaped=False
   elif char=='\\':escaped=True
   elif char=='"':quoted=False
  elif char=='"':quoted=True
  elif char in '[{':depth+=1
  elif char in ']}':depth-=1
  elif char==';' and depth==0:
   found=re.match(r';\s*(?:expect|expected)\s*:\s*(.+)$',text[index:],re.I|re.S)
   if found:m=(index,found[1]);break
 if m:expected=read_value(m[1]);has_expected=True;text=text[:m[0]].rstrip()
 instruction,sep,data=partition_input(text)
 prefix=re.match(r'^(?:take|using|start with|use)\s+',text,re.I)
 if prefix:
  try:
   value,end=json.JSONDecoder().raw_decode(text[prefix.end():])
   tail=text[prefix.end()+end:].strip()
   tail=re.sub(r'^(?:,\s*|then\s+|and\s+)+','',tail,flags=re.I)
   if tail:instruction=tail;data=json.dumps(value,ensure_ascii=False);sep=':'
  except ValueError:pass
 # These structural phrases preserve payload case and punctuation.
 m=re.fullmatch(r'(?:what is|find|calculate|give me) (?:the )?(sum|average|mean|median|minimum|maximum|count) of (.+)',text,re.I|re.S)
 if m:instruction=m[1];data=m[2];sep=':'
 else:
  m=re.fullmatch(r'(uppercase|lowercase|reverse|sort|deduplicate)\s+(\[.*\]|".*")',text,re.I|re.S)
  if m:instruction=m[1];data=m[2];sep=':'
 instruction=re.sub(r'\b(?:the )?previous result\b|\bthe result\b','it',instruction,flags=re.I)
 instruction=re.sub(r'^(?:now|then)\s+','',instruction.strip(),flags=re.I)
 instruction=re.sub(r'\s+(?:it|that|those)$','',instruction,flags=re.I)
 # Closed synonyms: unknown words are never silently dropped.
 for pattern,replacement in [(r'\bremove duplicate (?:items|values|lines)\b','deduplicate'),(r'\b(?:put|sort) (?:it |them )?in ascending order\b','sort'),(r'\bsort (?:it |them )?in descending order\b','sort descending'),(r'\bmake (?:it |them )?lowercase\b','lowercase'),(r'\bmake (?:it |them )?uppercase\b','uppercase')]:
  instruction=re.sub(pattern,replacement,instruction,flags=re.I)
 steps=parse_steps(instruction)
 recipe=state.get('recipes',{}).get(instruction.strip().casefold())
 if recipe:steps=copy.deepcopy(recipe['steps'])
 if not steps:return None
 if sep:value=read_value(data)
 elif state.get('has_last'):value=copy.deepcopy(state['last'])
 else:return None
 adapters=[]
 # Only explicit line/word operations split text. A text sort is ambiguous.
 first=steps[0]['op']
 if isinstance(value,str) and first in ('sort','unique','sum','mean','median','minimum','maximum','numbers'):
  return {'status':'needs-input','answer':'Should I split the text into lines or words first? Reply “lines” or “words”; the supplied text and requested operations are retained.','clarification':True,
          'pending_request':{'request':original,'steps':copy.deepcopy(steps),'input':value,'preview':preview,'expected':expected,'has_expected':has_expected,'adapters':[],'source':'finite-native-request-compiler'}}
 from .semantic_steps import parse as semantic_step
 from .instruction_clauses import split_clauses
 semantic_slots=any(semantic_step(clause) is not None for clause in split_clauses(instruction))
 return {'request':original,'steps':steps,'input':value,'preview':preview,'expected':expected,'has_expected':has_expected,'adapters':adapters,'source':'finite-native-request-compiler','semantic_slots':semantic_slots}

def execute_request(compiled,work):
 from .reasoning_engine import pipeline
 from .workflow_contracts import equivalent
 from .native_work import digest
 if compiled.get('clarification'):
  work.state['request_clarification']=copy.deepcopy(compiled['pending_request'])
  return {k:v for k,v in compiled.items() if k!='pending_request'}
 plan={'steps':compiled['steps'],'input_sha256':digest(compiled['input']),'expected':compiled['expected'] if compiled['has_expected'] else None,'has_expected':compiled['has_expected'],'source':compiled['source']}
 if compiled['preview']:
  work.state['proposed_work']=copy.deepcopy(compiled)
  work.state['focus_kind']='preview'
  return {'status':'planned','answer':'Planned pure-data steps: '+ ' → '.join(s['op'] for s in compiled['steps'])+'.\nNo result has been changed. Say “run that plan” to execute it.','plan':plan}
 result=pipeline(copy.deepcopy(compiled['input']),compiled['steps'])
 if compiled['has_expected'] and not equivalent(result['result'],compiled['expected']):
  failure={'expected':compiled['expected'],'actual':result['result'],'steps':compiled['steps'],'passed':False}
  work.state['last_acceptance_failure']=copy.deepcopy(failure)
  work.state['focus_kind']='acceptance-failure'
  return {'status':'acceptance-failed','answer':'The result did not match your expected value. The previous completed result is retained.\n'+json.dumps(failure,ensure_ascii=False,indent=2),'acceptance':failure,'committed':False}
 reply=work.commit(compiled['request'],result['result'],compiled['steps'],result)
 reply['plan']=plan;reply['acceptance']={'passed':True,'expected':compiled['expected']} if compiled['has_expected'] else {'passed':None,'scope':'No task-specific expected result was supplied.'}
 work.state['last_request_plan']=copy.deepcopy(plan)
 return reply

def resolve_clarification(text,work):
 """Resume a retained data task only on an explicit answer to its question."""
 pending=work.state.get('request_clarification')
 if not pending:return None
 key=text.strip().casefold().rstrip('?.!')
 if key in ('cancel clarification','cancel that question'):
  work.state.pop('request_clarification',None)
  return {'status':'complete','answer':'Cancelled the pending clarification. Earlier completed results remain unchanged.','model_calls':0}
 choices={'lines':'lines','split into lines':'lines','use lines':'lines','by lines':'lines','words':'words','split into words':'words','use words':'words','by words':'words'}
 if key not in choices:return None
 compiled=copy.deepcopy(pending);adapter={'op':choices[key]}
 compiled['steps']=[adapter]+compiled['steps'];compiled['adapters']=[adapter]
 # Stage on a copy: a failed operation keeps both the prior result and question.
 from .native_work import NativeWork
 trial=NativeWork(work.state);trial.state.pop('request_clarification',None)
 result=execute_request(compiled,trial)
 if result.get('status')=='acceptance-failed':return result
 work.state.clear();work.state.update(trial.state)
 return {**result,'clarification_resolved':choices[key],'model_calls':0}

