"""Compile explicit arithmetic into example-checked pure Python functions."""
import ast,copy,json,keyword,math,re
from .function_testing import test_function

def respond(text,work):
 if not text.lower().startswith('write python expression:'):return None
 body=json.loads(text.split(':',1)[1])
 if not isinstance(body,dict) or set(body)-{'function','parameters','expression','cases','validation_cases'}:raise ValueError('Supply function, parameters, expression, cases and validation_cases')
 name=body.get('function');parameters=body.get('parameters');expression=body.get('expression')
 def identifier(value):return isinstance(value,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,31}',value) and not keyword.iskeyword(value)
 if not identifier(name) or not isinstance(parameters,list) or not 1<=len(parameters)<=8 or not all(identifier(v) for v in parameters) or len(set(parameters))!=len(parameters):raise ValueError('Use a function name and 1–8 distinct parameter identifiers')
 if not isinstance(expression,str) or len(expression)>1000:raise ValueError('Supply a short explicit arithmetic expression')
 tree=ast.parse(expression,mode='eval');nodes=list(ast.walk(tree))
 allowed=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Mod,ast.UAdd,ast.USub,ast.Name,ast.Load,ast.Constant)
 if len(nodes)>128 or any(not isinstance(n,allowed) for n in nodes):raise ValueError('Use only numbers, parameters and + - * / % arithmetic')
 for node in nodes:
  if isinstance(node,ast.Name) and node.id not in parameters:raise ValueError('Undeclared parameter: '+node.id)
  if isinstance(node,ast.Constant) and (type(node.value) not in (int,float) or not math.isfinite(node.value) or len(str(node.value))>100):raise ValueError('Use finite short numeric constants')
 groups=[];seen=set()
 for label in ('cases','validation_cases'):
  cases=body.get(label)
  if not isinstance(cases,list) or not 2<=len(cases)<=8:raise ValueError('Supply 2–8 training cases and 2–8 separate validation cases')
  for case in cases:
   if not isinstance(case,dict) or set(case)!={'args','expected'} or not isinstance(case['args'],list) or len(case['args'])!=len(parameters):raise ValueError('Each case needs args matching the parameters and an expected numeric value')
   values=case['args']+[case['expected']]
   if any(type(v) not in (int,float) or len(str(v))>100 or not math.isfinite(v) for v in values):raise ValueError('Use finite bounded numeric examples')
   key=json.dumps(case['args'],allow_nan=False)
   if key in seen:raise ValueError('Training and validation inputs must be distinct')
   seen.add(key)
  groups.append(cases)
 source='def '+name+'('+', '.join(parameters)+'):\n    return '+ast.unparse(tree.body)+'\n'
 training,validation=[test_function({'source':source,'function':name,'cases':cases}) for cases in groups]
 passed=training['all_passed'] and validation['all_passed']
 checks={'all_passed':passed,'passed':training['passed']+validation['passed'],'total':training['total']+validation['total']}
 scope='Explicit formula compiled before checking supplied examples. Validation inputs are separate; passing examples does not prove correctness for every input. No files, commands or network actions were executed.'
 if passed:
  from .native_work import digest
  work.state['last_generated_code']={'source':source,'function':name,'checks':checks,'source_sha256':digest(source),'extra_checks':[],'kind':'formula','parameters':parameters,'replay_cases':copy.deepcopy(groups[0]+groups[1])}
  work.state['last_code_review']={'checks':checks,'training':training,'validation':validation,'scope':scope}
  work.state['focus_kind']='code'
 return {'status':'complete' if passed else 'test-failed','answer':('Checked Python function:\n' if passed else 'Formula did not match its supplied examples:\n')+'```python\n'+source+'```','code':{'source':source,'function':name,'checks':checks},'training':training,'validation':validation,'scope':scope,'model_calls':0}
