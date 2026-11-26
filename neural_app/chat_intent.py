"""Shared conversational intent helpers; generated stream data is never a reply."""
import re

class InvalidChatReply(ValueError):
 pass

def validate_chat_reply(text,request=''):
 """Reject mechanical repetition; this is a quality check, not a truth verdict."""
 if code_request(request) or re.search(r'\b(repeat|repetition|verbatim)\b',request,re.I):return text
 words=re.findall(r"[\w'-]+",str(text).casefold())
 if not words:raise InvalidChatReply('The assistant returned an empty answer')
 if len(words)==1 and words[0] in ('explain','plan','analyze','pipeline','coordinate'):
  raise InvalidChatReply('The assistant returned a routing label instead of an answer')
 if len(words)>=60:
  from collections import Counter
  if max(Counter(words).values())>max(12,len(words)*.3):
   raise InvalidChatReply('The assistant repeated words instead of answering')
  phrases=Counter(tuple(words[i:i+12]) for i in range(len(words)-11))
  if max(phrases.values(),default=0)>=5:
   raise InvalidChatReply('The assistant repeated a sentence or instruction instead of answering')
  if len(words)>=100 and len(re.findall(r'[.!?\n]',str(text)))<2:
   raise InvalidChatReply('The assistant returned an unstructured word stream instead of an answer')
 return text

def relevant_history(history,request):
 """Preserve follow-ups, while unrelated standalone topics start cleanly."""
 if re.search(r'\b(it|that|those|them|this|previous|earlier|again|continue|instead|shorter|longer|above|same|also)\b',request,re.I):return history[-12:]
 stop=set('the a an is are was were what how why when where who can could would should you your me my i we us do does did to of and or for in on with please write create make explain tell about'.split())
 def terms(value):return {w for w in re.findall(r'\w+',value.casefold()) if len(w)>2 and w not in stop}
 query=terms(request)
 return [row for row in history[-12:] if query&terms(str(row.get('request','')))] if query else []

def assessment_request(text):
 return bool(re.fullmatch(r'(?:please\s+)?(?:grade|rate|assess|evaluate)(?:\s+(?:the|my|this|your|entire|whole|current))*\s+(?:app|mind|ai|engine)(?:\s+(?:now|please|capabilities|capability))?[?.!]*',text.strip(),re.I))

def assessment_reply(runtime):
 from .capability_rubric import report
 quality=getattr(getattr(runtime,'cognitive_circuit',None),'cognition_quality',None)
 data=report(quality.view().get('latest',{}) if quality else {})
 evidence=data['current_regression_evidence']
 lines=['**App assessment**','No independently established overall letter grade is available. Internal checks measure particular tasks; they do not establish general intelligence.']
 if evidence.get('total'):
  lines.append('Latest recorded internal checks: '+str(evidence.get('passed',0))+'/'+str(evidence['total'])+'.')
 lines+=['- **Chat:** local-model-assisted; recent repetition and topic-switch failures show it still needs reliability improvements.', '- **Coding:** supported Python checks and reviewed edits are available; syntax checks alone do not prove correctness.', '- **Work:** supported tools can perform tasks and return receipts. General task completion needs end-to-end evaluation.', '- **Native engine:** processes streams and runs defined operations. Animated activity is not a measure of understanding.', 'The next useful test is an unfamiliar task with a clear expected result, followed by checking the actual output.']
 return '\n\n'.join(lines)

CAPABILITIES='''I can help with:

- **Conversation and writing:** explain topics, draft text and maintain relevant chat context.
- **Coding:** write and review code with a local model; natively test supported Python functions, inspect local helper dependencies and prepare tested edits.
- **Work:** calculate, transform data, organise supported tasks and check their results.
- **Files and desktop:** prepare reviewed text-file writes, inspect a selected app window and propose typing, clicking or scrolling its controls.
- **System:** inspect running processes, CPU, memory, disks and network status; propose reviewed commands.
- **Research:** read public HTTPS pages, search public scholarly sources, retrieve the app’s indexed sources and use its configured research tools.

Native tools perform the supported operations. Llama or Qwen helps with open-ended language and unfamiliar tasks. Current tool results show what actually completed.

Tell me the result you want—for example, “Write a Python function that removes duplicate items while keeping their order.”'''

def current_text(text):
 text=str(text)
 if 'CURRENT REQUEST:' in text:text=text.rsplit('CURRENT REQUEST:',1)[1]
 elif '[User message]' in text:text=text.rsplit('[User message]',1)[1]
 return text.strip()

def direct_reply(text):
 value=re.sub(r'[?.!]+$','',current_text(text).strip()).casefold()
 value=re.sub(r'^(?:please\s+|can you\s+|could you\s+)','',value)
 if re.fullmatch(r'(?:what (?:are|is) your|list your|describe your|tell me your) capabil[a-z]*',value):return CAPABILITIES
 if value in ('capabilities','your capabilities','what are your capabilities','what can you do','what can you help with','what can you help me with','tell me your capabilities','describe your capabilities','list your capabilities'):
  return CAPABILITIES
 if re.fullmatch(r'(?:write|create|generate)(?: me)?(?: a| some)? (?:python|python code|python script|python program)',value):
  return 'What should the Python program do? Describe its input and desired output, and I’ll write the code.'
 return None

def code_request(text):
 value=current_text(text)
 return bool(re.search(r'\b(write|implement|generate|create|refactor|fix|debug)\b[\s\S]*\b(python|javascript|typescript|function|class|code|script|program)\b',value,re.I))

def python_answer(answer,request,repair=None):
 """Present validated source rather than the small model's repetitive commentary."""
 if not re.search(r'\bpython\b',current_text(request),re.I):return answer
 import ast
 for attempt in range(2):
  block=re.search(r'```[^\n`]*\n([\s\S]*?)```',answer);source=block[1].strip() if block else answer.strip()
  tree=ast.parse(source);tests=None;value=current_text(request).casefold()
  if re.search(r'largest (?:number|value|element|item)',value) and 'list' in value and not re.search(r'\b(second|distinct|absolute|positive|negative|do not test|do not execute)\b',value):
   functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
   if len(functions)==1 and len(functions[0].args.args)==1:
    from .function_testing import test_function
    cases=[{'args':[xs],'expected':max(xs)} for xs in ([0],[0,1],[1,0],[-7,-2,-9],[3,3,1],[1.5,2.2],[-1])]
    if 'empty' in value and 'valueerror' in value:cases.append({'args':[[]],'raises':'ValueError'})
    tests=test_function({'source':source,'function':functions[0].name,'isolate_module':True,'cases':cases})
    if tests.get('status')=='unsupported-source':tests=None
  if not tests or tests['all_passed']:
   status='Python syntax checked. Execution tests have not run.' if not tests else 'Python syntax checked. Bounded function tests passed: '+str(tests['passed'])+'/'+str(tests['total'])+'. The full script was not executed.'
   return '```python\n'+source+'\n```\n\n'+status
  if repair is None or attempt:raise ValueError('Generated Python failed independent boundary cases; an incorrect function was withheld')
  import json
  feedback='The proposed Python function failed these native boundary tests: '+json.dumps([r for r in tests['cases'] if not r['passed']])[:2000]+'. Correct the complete function for the original request. Return one complete Python fenced block, without commentary.'
  answer=repair(feedback)
