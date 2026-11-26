"""Auditable translation of supported natural problem forms into pure solvers.

No example targets, model calls, benchmark identifiers or answer tables are used.
Unsupported wording is left for clarification rather than guessed.
"""
import ast,hashlib,re

def result(family,answer,evidence,scope):
 return {'status':'answered','answer':str(answer)+'\n\n'+scope,'final_answer':str(answer),'reasoning_family':family,'evidence':evidence,'model_calls':0,'scope':scope}

def options(text):
 if '\nOptions:\n' not in text:return None
 body,tail=text.rsplit('\nOptions:\n',1);rows=[]
 for line in tail.splitlines():
  match=re.fullmatch(r'\(([A-Z])\)\s+(.+)',line.strip())
  if not match:return None
  rows.append((match[1],match[2]))
 return (body,rows) if 2<=len(rows)<=16 and len({k for k,_ in rows})==len(rows) else None

def boolean_expression(text):
 match=re.fullmatch(r'(?:(?:evaluate|what is)(?: the following)?(?: boolean)? expression\s*:\s*)?([\s\S]+?)\s+is\s*[?.]?',text,re.I)
 if not match:return None
 expression=match[1].strip()
 if not re.fullmatch(r'(?:True|False|not|and|or|\s|\(|\))+',expression):return None
 tree=ast.parse(expression,mode='eval')
 if sum(1 for _ in ast.walk(tree))>128:raise ValueError('Boolean expression exceeds the syntax budget')
 trace=[]
 def visit(node,depth=0):
  if depth>24:raise ValueError('Boolean expression is too deeply nested')
  if isinstance(node,ast.Constant) and type(node.value)is bool:value=node.value
  elif isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):value=not visit(node.operand,depth+1)
  elif isinstance(node,ast.BoolOp) and isinstance(node.op,(ast.And,ast.Or)):
   values=[visit(v,depth+1) for v in node.values];value=all(values) if isinstance(node.op,ast.And) else any(values)
  else:raise ValueError('Only Boolean literals, not, and, or and parentheses are supported')
  trace.append({'expression':ast.get_source_segment(expression,node),'value':value});return value
 return result('boolean-expression',str(visit(tree.body)),trace,'Exact Boolean evaluation of the supplied expression; no unstated propositions inferred.')

def arithmetic(text):
 match=re.fullmatch(r'(?:(?:evaluate|calculate|compute|what is)\s*:?\s*)?([\d.\s()+*/%\-]+?)\s*(?:=|\?)',text,re.I)
 if not match:return None
 from .exact_numbers import calculate
 report=calculate(match[1].strip())
 return result('exact-arithmetic',report['exact_result'],report,'Exact rational calculation from the supplied numeric expression, with recorded intermediate operations.')

def word_sort(text):
 match=re.fullmatch(r'sort the following words alphabetically:\s*(?:list:\s*)?([\s\S]+)',text,re.I)
 if not match:return None
 values=match[1].split()
 if not 1<=len(values)<=512 or any(len(v)>128 for v in values):return None
 from .reasoning_engine import pipeline
 report=pipeline(values,[{'op':'sort'},{'op':'join','separator':' '}])
 return result('word-ordering',report['result'],report,'Lexicographic sorting of the supplied word list only; case and repeated words are preserved.')

def ordering(text):
 from .ordering_language import solve
 return solve(text,options,result)
TIME=r'(\d{1,2})(?::(\d{2}))?(am|pm)'
def clock(text):
 match=re.fullmatch(TIME,text)
 if not match:raise ValueError('Use an explicit 12-hour clock time')
 hour,minute=int(match[1]),int(match[2] or 0)
 if not 1<=hour<=12 or minute>59:raise ValueError('Invalid clock time')
 return (hour%12+(12 if match[3]=='pm' else 0))*60+minute

def schedule(text):
 parsed=options(text)
 if not parsed:return None
 body,choices=parsed;wake=re.search(r'\n([A-Za-z]+) woke up at ('+TIME+r')\.',body)
 close=re.search(r'\nThe (.+?) was closed after ('+TIME+r')\.',body)
 if not wake or not close:return None
 name=wake[1];earliest=clock(wake[2]);latest=clock(close[2]);occupied=[];accounted=0
 for line in body.splitlines():
  if not line.strip() or line.startswith(('Today,','We know that:','Between what times')):continue
  if re.fullmatch(re.escape(name)+r' woke up at '+TIME+r'\.',line):accounted+=1;continue
  if re.fullmatch(r'The .+? was closed after '+TIME+r'\.',line):accounted+=1;continue
  observation=re.fullmatch(r'[A-Za-z]+ saw '+re.escape(name)+r' .+ from ('+TIME+r') to ('+TIME+r')\.',line)
  if not observation:return None
  start,end=clock(observation[1]),clock(observation[5])
  if start>=end:return None
  occupied.append((start,end));accounted+=1
 feasible=[]
 for letter,choice in choices:
  match=re.fullmatch(r'('+TIME+r') to ('+TIME+r')',choice)
  if not match:return None
  start,end=clock(match[1]),clock(match[5])
  if earliest<=start<end<=latest and all(max(start,a)>=min(end,b) for a,b in occupied):feasible.append(letter)
 if len(feasible)!=1:return {'status':'needs-clarification','answer':'The supplied intervals do not determine exactly one feasible option.','reasoning_family':'schedule','model_calls':0}
 return result('schedule','('+feasible[0]+')',{'available_bounds':[earliest,latest],'occupied_intervals':occupied},'Feasible interval under the explicitly supplied same-day observations and closing time; possibility does not establish what actually happened.')

def date_question(text):
 from .calendar_language import solve
 return solve(text,options,result)
def reference_question(text):
 from .reference_language import solve
 return solve(text,options,result)

def compositional_question(text):
 from .compositional_language import respond
 return respond(text,result)

def narrative_question(text):
 from .narrative_reasoning import solve
 return solve(text,result)
def respond(text,previous=None):
 if not isinstance(text,str) or not text.strip() or len(text)>16000:return None
 original=text;text=re.sub(r'^reason about:\s*','',text.strip(),flags=re.I)
 if previous and previous.get('reasoning_family')=='narrative-state':
  from .narrative_reasoning import followup
  answer=followup(text,previous,result)
  if answer is not None:return {**answer,'input_sha256':hashlib.sha256(original.encode()).hexdigest()}
 for solver in (boolean_expression,arithmetic,word_sort,ordering,schedule,date_question,reference_question,compositional_question,narrative_question):
  try:answer=solver(text)
  except (ValueError,SyntaxError,OverflowError) as exc:
   return {'status':'needs-clarification','answer':str(exc),'reasoning_family':solver.__name__,'model_calls':0,'input_sha256':hashlib.sha256(original.encode()).hexdigest()}
  if answer is not None:return {**answer,'input_sha256':hashlib.sha256(original.encode()).hexdigest()}
 return None
