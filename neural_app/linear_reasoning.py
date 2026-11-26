"""Exact bounded linear equations and inspectable contradiction certificates."""
import ast,re,math
from fractions import Fraction

def rational(value):
 if type(value)not in (str,int,float) or isinstance(value,str) and len(value)>256 or type(value)is float and not math.isfinite(value):raise ValueError('Use bounded finite numbers or rational strings')
 text=str(value).replace('_','');exponent=re.search(r'[eE]([+-]?\d+)$',text)
 if exponent and (len(exponent[1].lstrip('+-'))>4 or abs(int(exponent[1]))>1000):raise ValueError('Numeric exponent exceeds the exact arithmetic budget')
 try:result=Fraction(text)
 except (ValueError,ZeroDivisionError):raise ValueError('Use a number or a rational such as 3/2')
 return checked(result)

def checked(value):
 if value.numerator.bit_length()>4096 or value.denominator.bit_length()>4096:raise ValueError('Exact arithmetic precision budget reached')
 return value

def solve(body):
 names=body.get('variables');rows=body.get('equations')
 if not isinstance(names,list) or not 1<=len(names)<=8 or any(not isinstance(n,str) or not n.isidentifier() or len(n)>32 for n in names) or len(set(names))!=len(names) or not isinstance(rows,list) or not 1<=len(rows)<=16:raise ValueError('Use 1–8 distinct variable names and 1–16 equations')
 requested=body.get('requested_variables',names)
 if not isinstance(requested,list) or not requested or any(not isinstance(n,str) or n not in names for n in requested) or len(set(requested))!=len(requested):raise ValueError('Requested variables must uniquely name declared variables')
 original=[]
 for row in rows:
  if not isinstance(row,dict) or not isinstance(row.get('terms'),dict) or not set(row['terms'])<=set(names) or 'equals' not in row:raise ValueError('Each equation needs declared variable terms and equals')
  original.append([rational(row['terms'].get(n,0)) for n in names]+[rational(row['equals'])])
 matrix=[list(row) for row in original];count=len(rows);transform=[[Fraction(int(i==j)) for j in range(count)] for i in range(count)];pivots=[];cursor=0
 for column in range(len(names)):
  selected=next((i for i in range(cursor,count) if matrix[i][column]),None)
  if selected is None:continue
  matrix[cursor],matrix[selected]=matrix[selected],matrix[cursor];transform[cursor],transform[selected]=transform[selected],transform[cursor]
  divisor=matrix[cursor][column];matrix[cursor]=[checked(v/divisor) for v in matrix[cursor]];transform[cursor]=[checked(v/divisor) for v in transform[cursor]]
  for i in range(count):
   if i==cursor or not matrix[i][column]:continue
   factor=matrix[i][column];matrix[i]=[checked(a-factor*b) for a,b in zip(matrix[i],matrix[cursor])];transform[i]=[checked(a-factor*b) for a,b in zip(transform[i],transform[cursor])]
  pivots.append(column);cursor+=1
  if cursor==count:break
 conflict=next((i for i,row in enumerate(matrix) if not any(row[:-1]) and row[-1]),None)
 if conflict is not None:
  certificate=transform[conflict];combined=[sum((certificate[i]*original[i][j] for i in range(count)),Fraction(0)) for j in range(len(names)+1)]
  if any(combined[:-1]) or not combined[-1]:raise ValueError('Contradiction certificate verification failed')
  return {'status':'inconsistent','rank':len(pivots),'solution':None,'certificate':{'equation_multipliers':[str(v) for v in certificate],'zero_equals':str(combined[-1]),'verified':True},'next_step':'Check the equations involved in the nonzero contradiction certificate.','scope':'Exact algebra over supplied equations; inconsistency concerns this model, not the truth of a real-world claim.'}
 free=[j for j in range(len(names)) if j not in pivots];solution={names[j]:{'constant':'0','free_terms':{names[j]:'1'}} for j in free}
 for i,column in enumerate(pivots):solution[names[column]]={'constant':str(matrix[i][-1]),'free_terms':{names[j]:str(-matrix[i][j]) for j in free if matrix[i][j]}}
 # Substitute the complete symbolic family back into every original equation.
 for row in original:
  constant=sum((row[j]*Fraction(solution[n]['constant']) for j,n in enumerate(names)),Fraction(0))
  coefficients={names[f]:sum((row[j]*Fraction(solution[n]['free_terms'].get(names[f],'0')) for j,n in enumerate(names)),Fraction(0)) for f in free}
  if constant!=row[-1] or any(coefficients.values()):raise ValueError('Symbolic substitution check failed')
 determined={n:row['constant'] for n,row in solution.items() if not row['free_terms']}
 return {'status':'unique-solution' if not free else 'underdetermined','rank':len(pivots),'solution':solution,'free_variables':[names[j] for j in free],'determined_values':determined,'requested_variables':requested,'requested_values_resolved':all(n in determined for n in requested),'all_equations_substitution_checked':True,'next_step':'Use the exact values under the supplied equations.' if not free else 'Supply independent equations or retain the free parameters; no missing value was guessed.','scope':'Exact rational linear algebra over supplied equations. Variable labels do not establish units, causal relationships or applicability of the equations to the world.'}

def parse(text):
 if not isinstance(text,str) or not text.strip() or len(text)>8000:raise ValueError('Supply up to 8000 characters of linear equations')
 names=set()
 def expression(source):
  source=source.strip();tree=ast.parse(source,mode='eval')
  if len(list(ast.walk(tree)))>128:raise ValueError('Equation expression is too large')
  def visit(node):
   if isinstance(node,ast.Constant) and type(node.value)in (int,float):return {},rational(ast.get_source_segment(source,node))
   if isinstance(node,ast.Name):names.add(node.id);return {node.id:Fraction(1)},Fraction(0)
   if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
    terms,constant=visit(node.operand);sign=-1 if isinstance(node.op,ast.USub) else 1
    return {n:sign*v for n,v in terms.items()},sign*constant
   if isinstance(node,ast.BinOp):
    a,x=visit(node.left);b,y=visit(node.right)
    if isinstance(node.op,(ast.Add,ast.Sub)):
     sign=-1 if isinstance(node.op,ast.Sub) else 1;keys=a.keys()|b.keys();terms={n:checked(a.get(n,0)+sign*b.get(n,0)) for n in keys}
     return {n:v for n,v in terms.items() if v},checked(x+sign*y)
    if isinstance(node.op,ast.Mult) and not (a and b):
     return ({n:checked(v*y) for n,v in a.items()},checked(x*y)) if a else ({n:checked(v*x) for n,v in b.items()},checked(y*x))
    if isinstance(node.op,ast.Div) and not b and y:return {n:checked(v/y) for n,v in a.items()},checked(x/y)
   raise ValueError('Use linear sums, constant multiplication and nonzero constant division; no calls or nonlinear terms')
  return visit(tree.body)
 equations=[]
 for line in re.split(r';|\n',text):
  if not line.strip():continue
  if line.count('=')!=1:raise ValueError('Each equation needs exactly one equals sign')
  left,right=line.split('=');a,x=expression(left);b,y=expression(right)
  equations.append({'terms':{n:str(a.get(n,0)-b.get(n,0)) for n in a.keys()|b.keys()},'equals':str(y-x)})
 return {'mode':'equations','variables':sorted(names),'equations':equations,'source_equations':text}
