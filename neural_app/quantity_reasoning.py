"""Exact, bounded quantity arithmetic with explicit dimensions and conversions."""
import ast,re
from fractions import Fraction
from .linear_reasoning import rational,checked

BASE=('m','s','kg','byte')
UNITS={
 'm':('1',(1,0,0,0)),'km':('1000',(1,0,0,0)),'cm':('1/100',(1,0,0,0)),'mm':('1/1000',(1,0,0,0)),
 's':('1',(0,1,0,0)),'ms':('1/1000',(0,1,0,0)),'min':('60',(0,1,0,0)),'h':('3600',(0,1,0,0)),'d':('86400',(0,1,0,0)),
 'kg':('1',(0,0,1,0)),'g':('1/1000',(0,0,1,0)),
 'byte':('1',(0,0,0,1)),'bit':('1/8',(0,0,0,1)),'kB':('1000',(0,0,0,1)),'MB':('1000000',(0,0,0,1)),
 'KiB':('1024',(0,0,0,1)),'MiB':('1048576',(0,0,0,1)),
 'Hz':('1',(0,-1,0,0)),'N':('1',(1,-2,1,0)),'J':('1',(2,-2,1,0)),'W':('1',(2,-3,1,0)),'Pa':('1',(-1,-2,1,0))}

def evaluate(source):
 if not isinstance(source,str) or not source.strip() or len(source)>2000:raise ValueError('Use a quantity expression up to 2000 characters')
 if re.search(r'(?<![\w.])\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\s+[A-Za-z]',source):raise ValueError('Parenthesize fractional magnitudes, for example (1/2) m or 1/(2 s), to make unit grouping explicit')
 # A number and adjacent unit form one quantity, including in a denominator.
 # Keep a unit power with the unit: 2 m**2 means 2*(m**2), not (2*m)**2.
 source=re.sub(r'(?<![\w.])((?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s+([A-Za-z]\w*(?:\s*\*\*\s*[+-]?\d+)?)',r'(\1 * \2)',source.strip())
 source=re.sub(r'(?<=\))\s+(?=[A-Za-z])',' * ',source)
 try:tree=ast.parse(source,mode='eval')
 except SyntaxError:raise ValueError('Use explicit arithmetic with supported unit symbols') from None
 if sum(1 for _ in ast.walk(tree))>128:raise ValueError('Quantity expression exceeds 128 syntax nodes')
 trace=[]
 def visit(node,depth=0):
  if depth>16:raise ValueError('Quantity expression is too deeply nested')
  if isinstance(node,ast.Constant) and type(node.value) in (int,float):result=(rational(ast.get_source_segment(source,node)),(0,0,0,0))
  elif isinstance(node,ast.Name) and node.id in UNITS:
   value,dimension=UNITS[node.id];result=(rational(value),dimension)
  elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
   value,dimension=visit(node.operand,depth+1);result=(value if isinstance(node.op,ast.UAdd) else -value,dimension)
  elif isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):
   a,da=visit(node.left,depth+1);b,db=visit(node.right,depth+1)
   if isinstance(node.op,(ast.Add,ast.Sub)):
    if da!=db:raise ValueError('Cannot add or subtract quantities with different dimensions')
    result=(checked(a+b if isinstance(node.op,ast.Add) else a-b),da)
   elif isinstance(node.op,ast.Mult):result=(checked(a*b),tuple(x+y for x,y in zip(da,db)))
   elif isinstance(node.op,ast.Div):
    if not b:raise ValueError('Cannot divide by a zero quantity')
    result=(checked(a/b),tuple(x-y for x,y in zip(da,db)))
   else:
    if any(db) or b.denominator!=1 or abs(b)>8:raise ValueError('Powers need a dimensionless integer exponent from -8 to 8')
    if not a and b<0:raise ValueError('Zero cannot have a negative power')
    result=(checked(a**int(b)),tuple(x*int(b) for x in da))
  else:raise ValueError('Use numbers, supported unit symbols and arithmetic only; no functions, variables or commands')
  if any(abs(d)>32 for d in result[1]):raise ValueError('Dimension exponent budget exceeded')
  trace.append({'expression':ast.get_source_segment(source,node),'base_value':str(result[0]),'dimensions':dict(zip(BASE,result[1]))})
  return result
 value,dimension=visit(tree.body)
 return value,dimension,trace

def solve(body):
 expression=body.get('expression');value,dimension,trace=evaluate(expression);target=body.get('target');scale=Fraction(1)
 if target is not None:
  scale,target_dimension,_=evaluate(target)
  if not scale or scale<0:raise ValueError('The target unit must have a positive nonzero scale')
  if target_dimension!=dimension:raise ValueError('The target unit has different dimensions from the result')
 display=checked(value/scale)
 canonical=' * '.join(name+('**'+str(power) if power!=1 else '') for name,power in zip(BASE,dimension) if power) or '1'
 return {'status':'calculated','complete':True,'expression':expression,'exact_value':str(display),'unit':target or canonical,'base_value':str(value),'dimensions':dict(zip(BASE,dimension)),'trace':trace,'next_step':'Check that the supplied quantities, dimensions and unit symbols describe the intended problem.','scope':'Exact arithmetic over supplied quantities and a fixed unit catalogue; dimensional consistency is checked. No missing measurements, temperature offsets, currency rates or empirical predictions are inferred.'}

def parse(text):
 parts=re.split(r'\s+to\s+',text.strip(),flags=re.I)
 if len(parts)>2:raise ValueError('Provide one expression and at most one target unit after to')
 return {'mode':'units','expression':parts[0],**({'target':parts[1]} if len(parts)==2 else {})}
