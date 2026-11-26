"""Consume complete named-quantity problems and compile checked unit arithmetic."""
import ast,re
from .quantity_reasoning import evaluate,solve as quantity_solve,UNITS

def solve(body):
 text=body.get('text');overrides=body.get('overrides',{})
 if not isinstance(text,str) or not text.strip() or len(text)>12000 or not isinstance(overrides,dict):raise ValueError('Provide a written quantity problem up to 12000 characters')
 parts=[v.strip().rstrip('.') for v in re.split(r'\.\s+|;|\n',text.strip()) if v.strip()]
 if not 2<=len(parts)<=9:raise ValueError('Supply 1–8 quantity declarations followed by one calculation question')
 question=re.fullmatch(r'(?:what is|calculate) (.+?)(?: in (.+?))?\??',parts[-1],re.I)
 if not question:raise ValueError('End with What is EXPRESSION in UNIT? or Calculate EXPRESSION')
 values={};sources={};dimensions={}
 for part in parts[:-1]:
  match=re.fullmatch(r'([a-z][a-z0-9_]{0,31})\s*(?:is|=)\s*(.+)',part,re.I)
  if not match:raise ValueError('Uninterpreted quantity clause: '+part[:160])
  name=match[1].lower()
  if name in values or name in UNITS:raise ValueError('Use distinct quantity names that do not shadow unit symbols')
  if len(match[2])>300:raise ValueError('Use a short quantity value')
  values[name]=match[2];sources[name]=part
 if not set(overrides)<=set(values):raise ValueError('A quantity correction names an undeclared variable')
 for name,value in overrides.items():
  if not isinstance(value,str) or not value.strip() or len(value)>300:raise ValueError('A corrected quantity needs short explicit text with units')
  values[name]=value
 for name,value in values.items():_,dimensions[name],_=evaluate(value)
 expression=question[1].strip();formula_origin='Explicit expression in the supplied question.';required_dimension=None
 definitions={'average speed':(('distance','duration'),'distance / duration',(1,-1,0,0)), 'rectangular area':(('length','width'),'length * width',(2,0,0,0)), 'rectangular volume':(('length','width','height'),'length * width * height',(3,0,0,0)), 'density':(('mass','volume'),'mass / volume',(-3,0,1,0))}
 if expression.lower() in definitions:
  required,expression,required_dimension=definitions[expression.lower()]
  if not set(required)<=set(values):raise ValueError('The named definition needs quantities: '+', '.join(required))
  expected={'distance':(1,0,0,0),'duration':(0,1,0,0),'length':(1,0,0,0),'width':(1,0,0,0),'height':(1,0,0,0),'mass':(0,0,1,0),'volume':(3,0,0,0)}
  if any(dimensions[n]!=expected[n] for n in required):raise ValueError('Each named quantity must have the dimensions required by the selected definition')
  if any(evaluate(values[n])[0]<0 for n in required):raise ValueError('Named geometric and physical definitions require nonnegative supplied quantities')
  formula_origin='Named mathematical definition: '+expression+'. No empirical relation was learned.'
 try:tree=ast.parse(re.sub(r'(?<=\d)\s+(?=[A-Za-z])',' * ',expression),mode='eval')
 except SyntaxError:raise ValueError('Use explicit arithmetic between declared quantity names') from None
 if sum(1 for _ in ast.walk(tree))>128:raise ValueError('The written expression exceeds its syntax budget')
 used={n.id if n.id in UNITS else n.id.lower() for n in ast.walk(tree) if isinstance(n,ast.Name)}
 if not used<=set(values)|set(UNITS):raise ValueError('Define these quantities or supply their mathematical relationship: '+', '.join(sorted(used-set(values)-set(UNITS))))
 substituted=re.sub(r'\b[A-Za-z][A-Za-z0-9_]*\b',lambda m:'('+values[m[0].lower()]+')' if m[0].lower() in values else m[0],expression)
 target=body.get('target',question[2]);task={'expression':substituted,**({'target':target} if target is not None else {})};report=quantity_solve(task)
 if required_dimension is not None and tuple(report['dimensions'].values())!=required_dimension:raise ValueError('The quantities have incompatible dimensions for the named definition')
 return {**report,'question':parts[-1],'formula_origin':formula_origin,'declarations':[{'name':n,'original_statement':sources[n],'current_quantity':values[n],'explicitly_corrected':n in overrides} for n in values],'used_quantities':sorted(used&set(values)),'unused_quantities':sorted(set(values)-used),'substituted_expression':substituted,'next_step':'Check the interpreted declarations, selected definition, unused quantities and unit assumptions. Unknown clauses and relations are not guessed.','scope':'Exact arithmetic compiled from a finite written-quantity grammar and explicit unit catalogue. Named definitions are mathematical conventions, not learned causal or empirical laws.'}

def parse(text):
 original=text.strip();explicit=re.match(r'^solve written problem:\s*(.+)',original,re.I|re.S)
 if explicit:return {'mode':'written_quantities','text':explicit[1]}
 if re.match(r'^[a-z][a-z0-9_]*\s+is\s+[+-]?\d',original,re.I) and re.search(r'\b(?:what is|calculate)\b',original,re.I):return {'mode':'written_quantities','text':original}
 return None
