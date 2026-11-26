"""Small exact rational arithmetic, preserving decimal source tokens."""
import ast,re
from fractions import Fraction

def calculate(text):
 if not isinstance(text,str) or not 1<=len(text)<=1000:raise ValueError('Use a short arithmetic expression')
 tree=ast.parse(text,mode='eval')
 if len(list(ast.walk(tree)))>64:raise ValueError('Expression is too large')
 steps=[]
 def visit(node):
  if isinstance(node,ast.Constant) and type(node.value) in (int,float):
   token=ast.get_source_segment(text,node).replace('_','');exponent=re.search(r'[eE]([+-]?\d+)$',token)
   if exponent and (len(exponent[1].lstrip('+-'))>4 or abs(int(exponent[1]))>1024):raise ValueError('Decimal exponent exceeds the supported size')
   result=Fraction(token)
  elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):result=visit(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
  elif isinstance(node,ast.BinOp):
   a,b=visit(node.left),visit(node.right)
   if isinstance(node.op,ast.Add):result=a+b
   elif isinstance(node.op,ast.Sub):result=a-b
   elif isinstance(node.op,ast.Mult):result=a*b
   elif isinstance(node.op,ast.Div):result=a/b
   elif isinstance(node.op,ast.Mod):result=a%b
   else:raise ValueError('Use +, -, *, / or %')
   steps.append({'expression':ast.get_source_segment(text,node),'exact':str(result)})
  else:raise ValueError('Only arithmetic constants and supported operators are accepted')
  if max(result.numerator.bit_length(),result.denominator.bit_length())>8192:raise ValueError('Exact result exceeds the supported size')
  return result
 try:out=visit(tree.body)
 except ZeroDivisionError as exc:raise ValueError('Cannot divide by zero') from exc
 return {'exact_result':str(out),'numerator':str(out.numerator),'denominator':str(out.denominator),'steps':steps,'scope':'Exact rational value of the supplied arithmetic expression; decimal input tokens are preserved','model_calls':0}
