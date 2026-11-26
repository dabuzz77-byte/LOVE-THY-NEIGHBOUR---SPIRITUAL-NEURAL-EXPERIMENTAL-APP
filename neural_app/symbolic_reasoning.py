"""Finite explicit-premise inference with provenance, contradictions and unknowns."""
import collections,re,json

def literal(text):
 if not isinstance(text,str) or not 1<=len(text)<=160 or '\n' in text:raise ValueError('Use short single-line fact labels')
 value=' '.join(text.casefold().split());return value

def opposite(value):return value[4:] if value.startswith('not ') else 'not '+value

def infer(body):
 facts=body.get('facts',[]);rules=body.get('rules',[]);query=literal(body.get('query',''))
 if not isinstance(facts,list) or not isinstance(rules,list) or len(facts)>128 or len(rules)>64:raise ValueError('Use up to 128 facts and 64 rules')
 proofs={};clean=[]
 for i,f in enumerate(facts):proofs.setdefault(literal(f),{'kind':'given','source_fact':i+1,'statement':f})
 for i,rule in enumerate(rules):
  if not isinstance(rule,dict):raise ValueError('Each rule must be an object')
  premises=rule.get('if');conclusion=rule.get('then')
  if not isinstance(premises,list) or not 1<=len(premises)<=8:raise ValueError('Each rule needs 1 to 8 premises')
  clean.append({'id':i+1,'if':[literal(p) for p in premises],'then':literal(conclusion)})
 changed=True;rounds=0
 while changed:
  changed=False;rounds+=1
  for rule in clean:
   if rule['then'] not in proofs and all(p in proofs for p in rule['if']):proofs[rule['then']]={'kind':'derived','rule':rule['id'],'premises':rule['if']};changed=True
  if rounds>65:raise ValueError('Inference did not converge')
 yes=query in proofs;no=opposite(query) in proofs
 status='conflict' if yes and no else 'supported' if yes else 'refuted' if no else 'unknown'
 contradictions=sorted(v for v in proofs if not v.startswith('not ') and opposite(v) in proofs)
 def support(goal):
  todo=[goal];seen=set();out=[]
  while todo:
   item=todo.pop()
   if item in seen or item not in proofs:continue
   seen.add(item);entry=proofs[item];out.append({'fact':item,**entry});todo.extend(entry.get('premises',[]))
  return out
 result={'query':query,'status':status,'support':support(query),'counter_support':support(opposite(query)),'contradictions':contradictions,'derived_count':sum(v['kind']=='derived' for v in proofs.values()),'rounds':rounds,'model_calls':0,'scope':'Logical consequences of the supplied premises. Unknown is not false; contradiction does not prove unrelated claims.'}
 if body.get('include_conclusions') is True:result['conclusions']=sorted(proofs)
 return result

def category_reasoning(text):
 statements=[s.strip().rstrip('.') for s in re.split(r';|\n',text) if s.strip()]
 if not statements or len(statements)>64:raise ValueError('Use up to 64 semicolon-separated statements, ending with a question')
 facts=[];relations=[];entities=set();query=None
 def singular(s):
  s=s.casefold().strip();return s[:-1] if s.endswith('s') and not s.endswith(('ss','us','is')) else s
 for statement in statements:
  all_rule=re.fullmatch(r'all ([\w-]+) are ([\w-]+)',statement,re.I)
  fact=re.fullmatch(r'([\w-]+) is (not )?(?:a |an )?([\w-]+)',statement,re.I)
  question=re.fullmatch(r'is ([\w-]+) (?:a |an )?([\w-]+)\??',statement,re.I)
  if all_rule:relations.append((singular(all_rule[1]),singular(all_rule[2])))
  elif fact:
   name=fact[1].casefold();entities.add(name);f=name+' is '+singular(fact[3]);facts.append(('not ' if fact[2] else '')+f)
  elif question:query=question[1].casefold()+' is '+singular(question[2]);entities.add(question[1].casefold())
  else:raise ValueError('Use “All cats are mammals; Luna is a cat; Is Luna a mammal?” or explicit JSON rules')
 if not query:raise ValueError('End with an explicit question')
 rules=[{'if':[name+' is '+a],'then':name+' is '+b} for name in sorted(entities) for a,b in relations]
 return infer({'facts':facts,'rules':rules,'query':query})

def what_if(body):
 facts=body.get('facts',[]);remove=body.get('remove',[]);add=body.get('add',[])
 if not all(isinstance(v,list) for v in (facts,remove,add)) or len(remove)+len(add)>64:raise ValueError('Use lists of facts to add and remove, up to 64 changes')
 removed={literal(v) for v in remove};altered=[v for v in facts if literal(v) not in removed]+add
 before=infer(body);after=infer({**body,'facts':altered})
 return {'query':before['query'],'baseline':before,'alternative':after,'status_changed':before['status']!=after['status'],'removed_facts':remove,'added_facts':add,'scope':'Logical counterfactual under supplied rules, not a prediction of external events','model_calls':0}

def sufficient_facts(body):
 original=infer(body);facts=body.get('facts',[])
 if not isinstance(facts,list) or len(facts)>16:raise ValueError('Use at most 16 given facts for bounded premise minimisation')
 if original['status'] not in ('supported','refuted','conflict'):return {'status':'unknown','sufficient_facts':None,'checks':0,'scope':'No settled conclusion was available to minimise'}
 selected=list(facts);checks=0
 for fact in facts:
  candidate=list(selected)
  if fact not in candidate:continue
  candidate.remove(fact);out=infer({**body,'facts':candidate});checks+=1
  if out['status']==original['status']:selected=candidate
 return {'status':original['status'],'query':original['query'],'sufficient_facts':selected,'removed_as_unnecessary':[f for f in facts if f not in selected],'checks':checks,'proof':infer({**body,'facts':selected}),'scope':'An inclusion-minimal sufficient subset under the supplied rules; not necessarily the unique or smallest-cardinality subset','model_calls':0}

def smallest_facts(body):
 import itertools
 original=infer(body);facts=body.get('facts',[])
 if len(facts)>10:raise ValueError('Exact smallest-premise search supports at most 10 facts')
 if original['status']=='unknown':return {'status':'unknown','sufficient_facts':None,'checks':0}
 checks=0
 for size in range(len(facts)+1):
  for subset in itertools.combinations(facts,size):
   proof=infer({**body,'facts':list(subset)});checks+=1
   if proof['status']==original['status']:return {'status':original['status'],'query':original['query'],'sufficient_facts':list(subset),'minimum_cardinality':size,'checks':checks,'proof':proof,'scope':'Exact minimum-cardinality subset of supplied facts; one solution returned if several tie','model_calls':0}
 raise ValueError('No matching subset found')

def respond(text):
 if text.lower().startswith('smallest premises:'):
  body=json.loads(text.split(':',1)[1])
  if not isinstance(body,dict):raise ValueError('Provide a JSON object')
  return smallest_facts(body)
 for prefix,operation in [('reason what if:',what_if),('minimise premises:',sufficient_facts),('minimize premises:',sufficient_facts)]:
  if text.lower().startswith(prefix):
   body=json.loads(text[len(prefix):])
   if not isinstance(body,dict):raise ValueError('Provide a JSON object')
   return operation(body)
 if text.lower().startswith('reason from:'):return category_reasoning(text.split(':',1)[1])
 if text.lower().startswith('reason:'):
  body=json.loads(text.split(':',1)[1])
  if not isinstance(body,dict):raise ValueError('Provide a JSON object')
  return infer(body)
 return None
