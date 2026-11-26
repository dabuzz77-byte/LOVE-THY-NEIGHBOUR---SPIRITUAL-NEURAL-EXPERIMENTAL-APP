"""Deterministic native skills shared by conversation and generated exercises."""
import ast,collections,json,operator,re,random
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod}
def calculate(text):
 tree=ast.parse(text,mode='eval')
 if len(list(ast.walk(tree)))>64:raise ValueError('Expression is too large')
 def visit(n):
  if isinstance(n,ast.Constant) and type(n.value) in (int,float) and abs(n.value)<1e12:return n.value
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):return visit(n.operand)*(1 if isinstance(n.op,ast.UAdd) else -1)
  if isinstance(n,ast.BinOp) and type(n.op) in OPS:
   v=OPS[type(n.op)](visit(n.left),visit(n.right))
   if abs(v)>1e15:raise ValueError('Result is too large')
   return v
  raise ValueError('Use numbers, parentheses and + - * / %')
 value=visit(tree.body)
 from .arithmetic_contract import verify_expression
 if not verify_expression(text,value):raise ValueError('Arithmetic result failed the independent rational check')
 return value
def respond(text):
 from .data_skills import respond as data_respond
 expanded=data_respond(text)
 if expanded is not None:return expanded
 lower=text.lower()
 natural=re.fullmatch(r"(?:what is|what's|work out)\s+(.+?)[?]?",text,re.I)
 if natural:
  expression=natural[1].rstrip('?').strip().lower()
  for word,op in [('multiplied by','*'),('divided by','/'),('plus','+'),('minus','-'),('times','*')]:expression=re.sub(r'\b'+word+r'\b',op,expression)
  if re.fullmatch(r'[0-9.()+*/%\s-]+',expression):return {'skill':'arithmetic','result':calculate(expression)}
 for prefix in ('calculate ','compute '):
  if lower.startswith(prefix):return {'skill':'arithmetic','result':calculate(text[len(prefix):])}
 if lower.startswith('format json '):return {'skill':'json-format','result':json.dumps(json.loads(text[12:]),indent=2,ensure_ascii=False)}
 if lower.startswith('count words '):
  words=re.findall(r"[^\W_]+",text[12:].lower());return {'skill':'word-count','result':{'words':len(words),'unique':len(set(words)),'frequencies':collections.Counter(words).most_common(40)}}
 if lower.startswith('sort lines\n'):return {'skill':'line-sort','result':'\n'.join(sorted(text.split('\n')[1:]))}
 if lower.startswith('unique lines\n'):return {'skill':'line-deduplicate','result':'\n'.join(dict.fromkeys(text.split('\n')[1:]))}
 if lower in ('thanks','thank you','thanks very much','thank you very much'):return {'skill':'conversation','result':'You’re welcome.'}
 if lower in ('hello','hi','hello there'):return {'skill':'conversation','result':'Hello. What would you like to discuss or work on?'}
 if lower in ('what can you do','what can you do?'):return {'skill':'conversation','result':'I can calculate and follow numeric results, summarise numeric data, convert CSV and JSON, transform Unicode text, sort or deduplicate lines, retrieve selected lessons with sources, remember and forget named information, inspect engine quality and carry out supported workspace plans. PC and network tools are available through the reviewed work interface.'}
 return None
def exercise(seed):
 rng=random.Random(int.from_bytes(seed,'big'));cases=[]
 for i in range(16):
  a,b,c=[rng.randrange(-1000,1000) for _ in range(3)];cases.append((f'calculate ({a} + {b}) * {c}',(a+b)*c))
 values=[str(rng.randrange(100)) for _ in range(12)]
 cases.extend([('sort lines\n'+'\n'.join(values),'\n'.join(sorted(values))),('unique lines\n'+'\n'.join(values),'\n'.join(dict.fromkeys(values))),('format json '+json.dumps({'values':values}),json.dumps({'values':values},indent=2))])
 rows=[{'input':q,'expected':e,'actual':respond(q)['result'],'passed':respond(q)['result']==e} for q,e in cases]
 return {'training_passed':all(x['passed'] for x in rows[:8]),'validation_passed':all(x['passed'] for x in rows[8:]),'lesson':'native arithmetic and data transforms','training_cases':rows[:8],'fresh_validation_cases':rows[8:],'retained':False,'scope':'Generated exact-answer exercises of installed native functions; validation measures correctness, not new model weights.'}
