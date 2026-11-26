"""Consume complete controlled-language causal models without guessing a graph."""
import ast,re

def expression(text):
 text=re.sub(r'\b(and|or|not|true|false)\b',lambda m:{'true':'True','false':'False'}.get(m[0].lower(),m[0].lower()),text,flags=re.I)
 tree=ast.parse(text.strip(),mode='eval')
 if sum(1 for _ in ast.walk(tree))>128:raise ValueError('Causal expression exceeds the syntax budget')
 def visit(node,depth=0):
  if depth>12:raise ValueError('Causal expression is too deeply nested')
  if isinstance(node,ast.Constant) and type(node.value)is bool:return node.value
  if isinstance(node,ast.Name) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,31}',node.id):return node.id.lower()
  if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):return {'not':visit(node.operand,depth+1)}
  if isinstance(node,ast.BoolOp) and isinstance(node.op,(ast.And,ast.Or)):return {'all' if isinstance(node.op,ast.And) else 'any':[visit(n,depth+1) for n in node.values]}
  raise ValueError('Use named Boolean factors, and, or, not and parentheses only')
 return visit(tree.body)

def parse(text):
 source=re.sub(r'^(?:think causally:|causal assumptions:)\s*','',text.strip(),flags=re.I)
 if not re.search(r'\bis true exactly when\b',source,re.I):return None
 parts=[p.strip() for p in re.split(r'\.\s+|;|\n',source) if p.strip()]
 if not 2<=len(parts)<=32:return None
 question=re.fullmatch(r'would ([a-z]\w*) be (true|false) if ([a-z]\w*) (?:were|was|is) (true|false)\??',parts[-1],re.I)
 if not question:return None
 values={};equations={};provenance=[]
 for part in parts[:-1]:
  original=part;part=re.sub(r'^assume\s+','',part,flags=re.I)
  definition=re.fullmatch(r'([a-z]\w*) is true exactly when (.+)',part,re.I)
  observation=re.fullmatch(r'([a-z]\w*) is (true|false)',part,re.I)
  if definition:
   name=definition[1].lower()
   if name in equations or name in values:raise ValueError('A causal variable has multiple definitions; specify one current model')
   equations[name]=expression(definition[2]);provenance.append({'text':original,'kind':'assumed-equation','variable':name})
  elif observation:
   name=observation[1].lower()
   if name in equations or name in values:raise ValueError('A causal input has conflicting or duplicate assignments')
   values[name]=observation[2].lower()=='true';provenance.append({'text':original,'kind':'supplied-input','variable':name})
  else:raise ValueError('A causal clause was not interpreted: '+original[:160]+'. State every equation and input explicitly; no clause was discarded')
 outcome=question[1].lower();setting={question[3].lower():question[4].lower()=='true'}
 return {'mode':'counterfactual','values':values,'equations':equations,'outcome':outcome,'interventions':[{'name':'question','set':setting}],'question_expected_value':question[2].lower()=='true','source_clauses':provenance,'question':parts[-1]}
