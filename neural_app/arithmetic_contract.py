"""Independent rational reference for bounded native arithmetic."""
import ast,math
from fractions import Fraction

def verify_expression(text,value):
 tree=ast.parse(text,mode='eval')
 if len(list(ast.walk(tree)))>64:return False
 def visit(node):
  if isinstance(node,ast.Constant) and type(node.value) in (int,float):return Fraction(str(node.value))
  if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):return visit(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
  if isinstance(node,ast.BinOp):
   a,b=visit(node.left),visit(node.right)
   if isinstance(node.op,ast.Add):return a+b
   if isinstance(node.op,ast.Sub):return a-b
   if isinstance(node.op,ast.Mult):return a*b
   if isinstance(node.op,ast.Div):return a/b
   if isinstance(node.op,ast.Mod):return a%b
  raise ValueError('Expression is outside the arithmetic checking contract')
 try:expected=float(visit(tree.body));return type(value) in (int,float) and math.isfinite(value) and math.isfinite(expected) and math.isclose(value,expected,rel_tol=1e-12,abs_tol=1e-12)
 except (ValueError,ZeroDivisionError,OverflowError):return False
