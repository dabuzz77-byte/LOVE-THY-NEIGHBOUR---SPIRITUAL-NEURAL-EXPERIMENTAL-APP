"""Bounded breadth-first composition of already verified pure byte skills."""
import hashlib,time

def apply_program(program,value):
 from .ambient_rule_lab import apply
 for rule in program:value=apply(tuple(rule),value)
 return value

def trace_program(program,value):
 from .ambient_rule_lab import apply
 rows=[]
 for index,rule in enumerate(program):
  before=value;value=apply(tuple(rule),value);rows.append({'step':index+1,'rule':list(rule),'input':before,'output':value})
 return {'input':rows[0]['input'] if rows else value,'output':value,'steps':rows}

def skill_program(skill):return skill.get('program') or [skill['rule']]

def compose(training,validation,atoms,max_depth=3,max_states=2048,budget_seconds=.025):
 from .ambient_rule_lab import apply
 if len(training)<4 or len(validation)<4:return {'status':'insufficient-examples'}
 if set(x for x,y in training)&set(x for x,y in validation):return {'status':'invalid-split'}
 if any(type(x)is not int or type(y)is not int or not 0<=x<256 or not 0<=y<256 for x,y in training+validation):return {'status':'invalid-byte'}
 atoms=list(dict.fromkeys(tuple(r) for r in atoms))[:12];inputs=tuple(x for x,y in training+validation);targets=tuple(y for x,y in training+validation)
 frontier=[([],inputs)];seen={inputs};tested=0;start=time.perf_counter()
 for depth in range(1,min(3,max_depth)+1):
  next_layer=[]
  for program,values in frontier:
   for rule in atoms:
    if tested>=max_states or time.perf_counter()-start>budget_seconds:return {'status':'search-budget-reached','tested_programs':tested,'depth':depth,'elapsed_ms':1000*(time.perf_counter()-start)}
    tested+=1;outputs=tuple(apply(rule,value) for value in values);candidate=program+[list(rule)]
    if outputs==targets:
     table=bytes(apply_program(candidate,x) for x in range(256))
     return {'status':'validated-candidate','program':candidate,'depth':depth,'tested_programs':tested,'tested_candidates':tested,'validation_examples':len(validation),'behaviour_sha256':hashlib.sha256(table).hexdigest(),'validation_used_for_selection':True,'scope':'A short plan from registered verified operations. Full-domain audit is separate from these search examples.'}
    if outputs not in seen:
     seen.add(outputs)
     if len(next_layer)<128:next_layer.append((candidate,outputs))
  frontier=next_layer
  if not frontier:break
 return {'status':'no-supported-composition','tested_programs':tested,'max_depth':min(3,max_depth)}
