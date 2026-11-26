"""Immediate parallel structure compiler for explicitly stochastic bus data."""
import ast,collections,copy,hashlib,json,math,operator,re,threading,time,warnings

def arithmetic(text):
 if len(text)>256:return None
 try:
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',SyntaxWarning);root=ast.parse(text,mode='eval')
 except (SyntaxError,ValueError):return None
 if sum(1 for _ in ast.walk(root))>64:return None
 def visit(node,depth=0):
  if depth>12:raise ValueError()
  if isinstance(node,ast.Constant) and type(node.value) in (int,float):value=node.value
  elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):value=visit(node.operand,depth+1)*(1 if isinstance(node.op,ast.UAdd) else -1)
  elif isinstance(node,ast.BinOp) and type(node.op) in (ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Mod):value={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod}[type(node.op)](visit(node.left,depth+1),visit(node.right,depth+1))
  else:raise ValueError()
  if not math.isfinite(value) or abs(value)>1e12:raise ValueError()
  return value
 try:return {'kind':'arithmetic-expression','syntax':ast.dump(root,include_attributes=False),'value':visit(root.body),'status':'evaluated bounded arithmetic; no task-specific expected output supplied'}
 except (ValueError,TypeError,OverflowError,ZeroDivisionError):return None

def compile_text(text):
 raw=text.encode('utf-8',errors='surrogatepass');literal_bits=bool(re.fullmatch(r'[01\s]+',text));bits=''.join(text.split())[:128] if literal_bits else ''.join(format(b,'08b') for b in raw[:64]);symbols=[{'kind':'symbol','value':t,'codepoints':[ord(c) for c in t[:32]]} for t in re.findall(r'\w+|[^\w\s]',text,flags=re.UNICODE)[:96]]
 groups=[]
 for i in range(0,min(128,len(bits))-3,4):
  a,b=bits[i]=='1',bits[i+1]=='1';op=('and','or','xor','not')[int(bits[i+2:i+4],2)]
  result=(a and b) if op=='and' else (a or b) if op=='or' else (a!=b) if op=='xor' else not a
  table=[{'a':x,'b':y,'result':(x and y) if op=='and' else (x or y) if op=='or' else (x!=y) if op=='xor' else not x} for x in (False,True) for y in (False,True)]
  groups.append({'kind':'boolean-expression','operator':op,'operands':[a] if op=='not' else [a,b],'value':result,'truth_table':table,'source_bit_offset':i})
 parsed=arithmetic(text.strip());json_value=None
 try:
  value=json.loads(text)
  if len(text)<=4096:json_value={'kind':'json-data','value':value,'status':'parsed data; instructions are not executed'}
 except (ValueError,RecursionError):pass
 return {'kind':'parallel-logic-structure','source_sha256':hashlib.sha256(raw).hexdigest(),'input_characters':len(text),'bit_interpretation':'literal-binary' if literal_bits else 'UTF-8 encoded bytes','typed_sequence':symbols,'boolean_expressions':groups,'arithmetic':parsed,'json_data':json_value,'status':'constructed syntax and evaluated finite Boolean expressions; source meaning remains unverified'}

class StochasticStructure:
 def __init__(self):self.lock=threading.RLock();self.sources=collections.OrderedDict();self.sequence=0;self.pending=[];self.captured=0;self.duplicates=0
 def observe(self,event):
  if event.get('origin')=='stochastic-logic-structure':return
  payload=event.get('payload')
  if not isinstance(payload,dict) or payload.get('processing_receipt'):return
  candidates=[];stack=[(payload,[],False)];visited=0
  while stack and visited<256 and len(candidates)<16:
   value,path,inherited=stack.pop();visited+=1
   if len(path)>6:continue
   if isinstance(value,dict):
    stochastic=inherited or value.get('stochastic') is True or value.get('influenced_random') is True
    if value.get('contains_model_text') is True or value.get('predefined_text') is True:continue
    for key,child in list(value.items())[:48]:
     if any(s in str(key).casefold() for s in ('password','secret','token','authorization')):continue
     if stochastic and key in ('text','bits','binary','output_bits','ascii','characters','value','state') and isinstance(child,str):candidates.append((path+[key],child))
     elif stochastic and key in ('value','state','sample') and type(child) in (int,float,bool):
      if not isinstance(child,float) or math.isfinite(child):candidates.append((path+[key],json.dumps(child)))
     elif stochastic and key in ('ascii_codes','unicode_codes','output_bytes') and isinstance(child,list):candidates.append((path+[key],''.join(chr(x) for x in child[:1024] if type(x)is int and 0<=x<=0x10ffff and not 0xd800<=x<=0xdfff)))
     elif isinstance(child,(dict,list)):stack.append((child,path+[str(key)],stochastic))
   elif isinstance(value,list):
    for i,child in enumerate(value[:32]):
     if isinstance(child,(dict,list)):stack.append((child,path+[i],inherited))
  budget=4096
  for path,text in candidates:
   if not text or budget<=0:continue
   original_length=len(text);text=text[:min(1024,budget)];budget-=len(text);result=compile_text(text)
   name=str(event.get('origin','unknown'))[:100]+':'+json.dumps(path,ensure_ascii=True);digest=result['source_sha256']
   with self.lock:
    self.captured+=1
    if self.sources.get(name,{}).get('source_sha256')==digest:self.duplicates+=1;continue
    self.sequence+=1;row={**result,'source':str(event.get('origin','unknown'))[:100],'path':path,'parent_event':event.get('sequence'),'sequence':self.sequence,'original_characters':original_length,'truncated':original_length!=len(text),'compiled_at':time.time()};self.sources[name]=row;self.sources.move_to_end(name)
    while len(self.sources)>64:self.sources.popitem(last=False)
    self.pending=(self.pending+[{'origin':'stochastic-logic-structure','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'stochastic':False,'source':row['source'],'path':path,'parent_event':event.get('sequence'),'sequence':self.sequence,'source_sha256':digest,'logic_structure':copy.deepcopy(result),'provenance':'parallel structure derived from explicit stochastic data; syntax is not evidence of source meaning'}}])[-32:]
 def drain(self):
  with self.lock:events=self.pending;self.pending=[];return events
 def view(self,summary=False):
  with self.lock:
   if summary:return {'sequence':self.sequence,'retained_sources':len(self.sources),'captured_chunks':self.captured,'duplicate_chunks':self.duplicates,'recent':[{'source':r['source'],'path':r['path'],'parent_event':r['parent_event'],'source_sha256':r['source_sha256'],'typed_symbols':len(r['typed_sequence']),'boolean_expressions':len(r['boolean_expressions']),'arithmetic':r['arithmetic'],'truncated':r['truncated'],'status':r['status']} for r in list(self.sources.values())[-6:]],'scope':'Parallel structured candidates; not verified source meaning or executable instructions'}
   return {'sequence':self.sequence,'retained_sources':len(self.sources),'captured_chunks':self.captured,'duplicate_chunks':self.duplicates,'recent':copy.deepcopy(list(self.sources.values())[-6:]),'scope':'Parallel, source-preserving compilation on the registered bus. Bounded rotating event coverage, not unobserved process memory. No generated instruction executes.'}

