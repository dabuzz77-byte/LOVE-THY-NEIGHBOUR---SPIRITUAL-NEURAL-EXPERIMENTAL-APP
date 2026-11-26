"""Finite byte-rule induction from generated experiments; no dynamic code execution."""
import hashlib,random,json,os,uuid
from collections import OrderedDict
from .ambient_skill_composition import apply_program,skill_program,compose,trace_program

def apply(rule,value):
 kind,a,b=rule
 if kind=='affine':return (a*value+b)%256
 if kind=='xor':return value^a
 if kind=='rotate':return ((value<<a)|(value>>(8-a)))&255
 raise ValueError('Unknown byte rule')

def candidates():
 for a in (1,3,5,7,9,13):
  for b in range(256):yield ('affine',a,b)
 for a in range(256):yield ('xor',a,0)
 for shift in range(1,8):yield ('rotate',shift,0)

def infer(training,validation):
 if len(training)<4 or len(validation)<4:return {'status':'insufficient-examples'}
 if len({x for x,y in training})!=len(training) or set(x for x,y in training)&set(x for x,y in validation):return {'status':'invalid-split'}
 if any(type(x)is not int or type(y)is not int or not 0<=x<256 or not 0<=y<256 for x,y in training+validation):return {'status':'invalid-byte'}
 survivors=[];tested=0
 for rule in candidates():
  tested+=1
  if all(apply(rule,x)==y for x,y in training):survivors.append(rule)
 accepted=[r for r in survivors if all(apply(r,x)==y for x,y in validation)]
 behaviours={bytes(apply(r,x) for x in range(256)) for r in accepted}
 if not accepted:return {'status':'no-supported-rule','tested_candidates':tested,'training_survivors':len(survivors)}
 if len(behaviours)>1:return {'status':'ambiguous','tested_candidates':tested,'distinct_behaviours':len(behaviours)}
 rule=accepted[0];table=next(iter(behaviours))
 return {'status':'validated-candidate','rule':list(rule),'tested_candidates':tested,'equivalent_candidates':len(accepted),'validation_examples':len(validation),'behaviour_sha256':hashlib.sha256(table).hexdigest()}

class RuleLab:
 def __init__(self,path=None):
  self.path=path;self.skills=OrderedDict();self.tasks=0;self.successes=0;self.reuses=0;self.compositions=0;self.active_questions=0;self.active_resolved=0;self.storage_error=None
  if path and path.exists():
   try:
    if path.stat().st_size>100000:raise ValueError('Skill file exceeds budget')
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('version') not in (1,2):raise ValueError('Unknown skill format')
    for ident,skill in list(data.get('skills',{}).items())[:64]:
     program=skill_program(skill)
     if not 1<=len(program)<=3 or any(tuple(rule) not in set(candidates()) for rule in program):raise ValueError('Unregistered byte program')
     actual=hashlib.sha256(bytes(apply_program(program,x) for x in range(256))).hexdigest()
     if actual!=ident or skill.get('verified_domain')!=256:raise ValueError('Skill checksum mismatch')
     self.skills[ident]={**({'rule':list(program[0])} if len(program)==1 else {'program':program}),'uses':max(0,min(1000000000,int(skill.get('uses',0)))),'verified_domain':256}
   except (ValueError,TypeError,KeyError,OSError) as exc:self.skills.clear();self.storage_error=str(exc)[:180]
 def flush(self):
  if self.path is None:return
  temporary=self.path.with_name(self.path.name+'.'+uuid.uuid4().hex+'.tmp')
  try:
   self.path.parent.mkdir(parents=True,exist_ok=True);temporary.write_text(json.dumps({'version':2,'skills':self.skills}),encoding='utf-8');os.replace(temporary,self.path);self.storage_error=None
  except OSError as exc:self.storage_error=str(exc)[:180]
  finally:
   if temporary.exists():temporary.unlink()
 def study(self,source,raw):
  raw=bytes(raw[:256])
  if not raw:return {'status':'waiting-for-input'}
  digest=hashlib.sha256(raw).hexdigest();rng=random.Random(int(digest[:16],16));family=rng.randrange(3)
  # The experiment generator knows the environment. infer() receives only examples.
  hidden=('affine',rng.choice((1,3,5,7,9,13)),rng.randrange(256)) if family==0 else ('xor',rng.randrange(256),0) if family==1 else ('rotate',rng.randrange(1,8),0)
  atoms=[skill['rule'] for skill in list(self.skills.values()) if 'rule' in skill][-12:]
  hidden_program=[list(hidden)]
  if self.tasks%4==3 and len(atoms)>=2:hidden_program=[list(rng.choice(atoms)),list(rng.choice(atoms))]
  points=rng.sample(range(256),16);training=[(x,apply_program(hidden_program,x)) for x in points[:8]];validation=[(x,apply_program(hidden_program,x)) for x in points[8:]]
  retrieved=[(ident,skill) for ident,skill in self.skills.items() if all(apply_program(skill_program(skill),x)==y for x,y in training+validation)]
  if len(retrieved)==1:
   ident,skill=retrieved[0];learned={'status':'validated-candidate','program':skill_program(skill),'behaviour_sha256':ident,'tested_candidates':0,'retrieved_procedure':True,'validation_examples':len(validation)}
  else:
   from .ambient_active_experiments import identify
   hypotheses=[[list(rule)] for rule in candidates()]+[skill_program(skill) for skill in self.skills.values()]+[[list(a),list(b)] for a in atoms for b in atoms]
   active=identify(hypotheses,lambda x:apply_program(hidden_program,x),points[:1],points[8:])
   self.active_questions+=len(active.get('queries',[]))
   if active['status']=='validated-candidate':learned=active;training=active['examples']
   else:
    learned=infer(training,validation);learned['active_attempt']=active
    if learned['status']!='validated-candidate' and atoms:
     learned=compose(training,validation,atoms);learned['active_attempt']=active
  self.tasks+=1
  report={'source':source,'source_sha256':digest,'task_kind':'composed' if len(hidden_program)>1 else 'single-operation','training_examples':training,'validation_examples':validation,'discovery':learned,'scope':'Source-seeded synthetic byte experiments. The learner searches registered pure functions using examples; no claim that the source contained these meanings and no generated code is executed.'}
  if learned['status']!='validated-candidate':return report
  program=learned.get('program') or [learned['rule']];passed=sum(apply_program(program,x)==apply_program(hidden_program,x) for x in range(256));report['full_domain_check']={'passed':passed,'total':256,'scope':'Exhaustive finite-domain comparison with the isolated experiment environment, after induction.'}
  if passed!=256:report['status']='counterexample-found';return report
  if learned.get('active_experiment'):self.active_resolved+=1
  ident=learned['behaviour_sha256'];known=ident in self.skills
  if known:self.reuses+=1
  if len(program)>1:self.compositions+=1
  self.skills[ident]={**({'rule':list(program[0])} if len(program)==1 else {'program':program}),'uses':self.skills.get(ident,{}).get('uses',0)+1,'verified_domain':256};self.skills.move_to_end(ident)
  while len(self.skills)>64:self.skills.popitem(last=False)
  self.successes+=1;probe=rng.randrange(256)
  report.update(status='verified-procedure-reused' if known else 'verified-procedure-retained',skill_id=ident,retained_skills=len(self.skills),plan_depth=len(program),application={**trace_program(program,probe),'matched_expected':apply_program(program,probe)==apply_program(hidden_program,probe)})
  return report
 def view(self):return {'completed_experiments':self.tasks,'verified_experiments':self.successes,'reused_procedure_tasks':self.reuses,'retained_procedures':len(self.skills),'candidate_space':1799,'verified_composed_tasks':self.compositions,'maximum_program_depth':3,'active_questions':self.active_questions,'actively_resolved_tasks':self.active_resolved,'storage_error':self.storage_error,'persistent':self.path is not None,'scope':'Finite native byte transformations; not unrestricted programming or general intelligence.'}
