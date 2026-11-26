"""Bounded compositional arithmetic language, with complete input accounting.

This is a transparent grammar, not a general language model. It translates only
explicit requests; leftover prose never disappears into a guessed calculation.
"""
import re
from .exact_numbers import calculate

SMALL=dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(),range(20)))
TENS=dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(),range(20,100,10)))
LEX=re.compile(r'\d+(?:\.\d+)?|\.\d+|[a-z]+|[()+*/%\-,]')

class LanguageError(ValueError):pass

class Parser:
 def __init__(self,tokens):self.tokens=tokens;self.i=0;self.nodes=0
 def peek(self):return self.tokens[self.i] if self.i<len(self.tokens) else ''
 def take(self,word=None):
  if self.i>=len(self.tokens):raise LanguageError('A number or closing part is missing.')
  value=self.peek()
  if word is not None and value!=word:raise LanguageError('Expected “'+word+'” here, rather than “'+value+'”.')
  self.i+=1;return value
 def atom(self,depth):
  self.nodes+=1
  if depth>16 or self.nodes>48:raise LanguageError('Please split this calculation into smaller steps.')
  token=self.peek()
  if token in ('-','negative','minus','positive','+'):
   sign=self.take();return ('-' if sign in ('-','negative','minus') else '+')+'('+self.atom(depth+1)+')'
  if token=='(':
   self.take();value=self.expression(depth+1);self.take(')');return '('+value+')'
  if token in ('sum','product','difference','quotient'):
   operation=self.take();self.take('of');a=self.atom(depth+1);self.take('and');b=self.atom(depth+1)
   if self.peek() in ('plus','minus','times','multiplied','divided','+','-','*','/'):
    raise LanguageError('The grouping of that named operation is ambiguous. Put each intended group in parentheses, for example “(sum of 3 and 4) times 5” or “sum of 3 and (4 times 5)”.')
   return '('+a+{'sum':'+','product':'*','difference':'-','quotient':'/'}[operation]+b+')'
  if token in ('double','triple','half'):
   modifier=self.take()
   if self.peek()=='of':self.take()
   value=self.atom(depth+1)
   if self.peek() in ('plus','minus','times','multiplied','divided','+','-','*','/'):
    raise LanguageError('Please put the scope of “'+modifier+'” in parentheses, for example “half of (2 plus 3)” or “(half of 2) plus 3”.')
   return '('+value+{'double':'*2','triple':'*3','half':'/2'}[modifier]+')'
  if re.fullmatch(r'\d+(?:\.\d+)?|\.\d+',token):return self.take()
  if token in SMALL or token in TENS:
   first=self.take();number=SMALL.get(first,TENS.get(first))
   if first in TENS:
    if self.peek() in SMALL and 0<SMALL[self.peek()]<10:number+=SMALL[self.take()]
   return str(number)
  raise LanguageError('I could not identify the number or grouped operation at “'+(token or 'the end')+'”. Use explicit numbers and parentheses.')
 def expression(self,depth=0,minimum=0):
  left=self.atom(depth)
  while True:
   token=self.peek();op={'plus':'+','minus':'-','times':'*','multiplied':'*','divided':'/','modulo':'%','+':'+','-':'-','*':'*','/':'/','%':'%'}.get(token)
   precedence=1 if op in ('+','-') else 2
   if op is None or precedence<minimum:break
   self.take()
   if token in ('multiplied','divided'):self.take('by')
   right=self.expression(depth+1,precedence+1);left='('+left+op+right+')'
  return left

def respond(text,make_result):
 original=text.strip();body=original.lower().replace('−','-').replace('×','*').replace('÷','/')
 # Strip only recognised request wrappers, never numbers, units or other payload.
 body=re.sub(r'^(?:(?:please|could you|can you|would you)\s+)+','',body)
 match=re.match(r'^(?:what is|what\'s|how much is|work out|calculate|compute|evaluate|find the value of)\s*:?[ \t]*',body)
 if not match:return None
 body=body[match.end():].strip();body=re.sub(r'\s*(?:please)?[?!.]*$','',body).strip()
 body=re.sub(r'^the value of\s+','',body)
 body=re.sub(r'\b('+'|'.join(TENS)+r')-('+'|'.join(k for k,v in SMALL.items() if 0<v<10)+r')\b',r'\1 \2',body)
 # Existing symbolic and other reasoning adapters own their request forms.
 if not re.match(r'(?:\d|\.\d|\(|[-+]|'+ '|'.join(SMALL|TENS)+r'\b|sum\b|product\b|difference\b|quotient\b|double\b|triple\b|half\b|negative\b|positive\b)',body):return None
 if len(body)>1000:return {'status':'needs-clarification','answer':'Please split this calculation into smaller steps.','reasoning_family':'compositional-arithmetic','model_calls':0}
 try:
  tokens=LEX.findall(body)
  if re.sub(r'\s+','',''.join(tokens))!=re.sub(r'\s+','',body):raise LanguageError('Some notation is unsupported. Use explicit numbers, arithmetic words and parentheses.')
  if len(tokens)>128:raise LanguageError('Please split this calculation into smaller steps.')
  parser=Parser(tokens);expression=parser.expression()
  if parser.i!=len(tokens):raise LanguageError('I have not accounted for “'+' '.join(tokens[parser.i:])+'”. Please clarify its role; no part of the request was silently ignored.')
  computed=calculate(expression)
 except (ValueError,SyntaxError,OverflowError) as exc:
  return {'status':'needs-clarification','answer':str(exc),'reasoning_family':'compositional-arithmetic','source_request':original,'model_calls':0}
 report=make_result('compositional-arithmetic',computed['exact_result'],{'source_request':original,'interpreted_expression':expression,'calculation':computed},'Exact arithmetic under the displayed interpretation. Number words zero–ninety-nine, named binary operations and explicit grouping are supported; no missing quantities or world facts are inferred.')
 report['answer']=computed['exact_result']+'\n\nInterpreted as: '+expression+'\n\n'+report['scope']
 return report
