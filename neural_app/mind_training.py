"""Outcome-trained arithmetic procedure search with fresh validation inputs."""
import math,random
from .branch_reasoning import arithmetic,equivalent
TASKS={
 'sum':(['a+b','a-b','a*b','a/b'],lambda a,b:a+b),
 'product':(['a*b','a+b','a-b','a/b'],lambda a,b:a*b),
 'difference':(['a-b','a+b','a*b','b-a'],lambda a,b:a-b),
 'sum_then_double':(['(a+b)*2','a+b*2','a*b*2','a+b'],lambda a,b:(a+b)*2),
 'mean':(['(a+b)/2','a+b/2','a/b','a+b'],lambda a,b:(a+b)/2),
 'remainder':(['a%b','a/b','a-b','a+b'],lambda a,b:a%b)}
PHASES=(0.,.25,.5,.75,1.)
def trial(seed,step,state):
 rng=random.Random(int.from_bytes(seed,'big')+step);store=state.setdefault('mind_curriculum',{'sequence':0,'concepts':{},'phase_scores':{},'retained':{},'history':[]});sequence=store['sequence'];concept=list(TASKS)[(sequence//5)%len(TASKS)];depth=PHASES[sequence%5];templates,expected=TASKS[concept];record=store['concepts'].setdefault(concept,{'attempts':0,'arms':{}})
 for t in templates:record['arms'].setdefault(t,{'attempts':0,'passed':0})
 def score(t):
  arm=record['arms'][t];return (arm['passed']+1)/(arm['attempts']+2)+math.sqrt(math.log(record['attempts']+2)/(arm['attempts']+1))
 template=rng.choice(templates) if depth==0 or rng.random()>depth else max(templates,key=score)
 def cases(offset):
  rows=[]
  for _ in range(4):
   a=rng.randrange(2+offset,50+offset);b=rng.randrange(2,19);expr=template.replace('a',str(a)).replace('b',str(b));value=arithmetic(expr);want=expected(a,b);rows.append({'input':[a,b],'actual':value,'expected':want,'passed':equivalent(value,want)})
  return rows
 train=cases(0);validation=cases(100);ok=all(v['passed'] for v in train);valid=all(v['passed'] for v in validation);arm=record['arms'][template];arm['attempts']+=1;arm['passed']+=int(ok);record['attempts']+=1
 phase=store['phase_scores'].setdefault(str(depth),{'attempts':0,'validation_passes':0});phase['attempts']+=1;phase['validation_passes']+=int(valid)
 if arm['passed']>=3 and arm['passed']==arm['attempts'] and valid:store['retained'][concept]={'template':template,'training_successes':arm['passed'],'fresh_validation_cases':4,'parameters':['a','b'],'scope':'Validated arithmetic curriculum procedure; not general task mastery'}
 row={'concept':concept,'depth':depth,'template':template,'passed':ok,'validation':valid};store['history']=(store['history']+[row])[-32:];store['sequence']+=1
 return {'training_passed':ok,'validation_passed':valid,'lesson':'phase-conditioned procedure discovery: '+concept,'phase':depth,'template':template,'training_cases':train,'fresh_validation_cases':validation,'retained':concept in store['retained'],'scope':'Six explicit arithmetic concepts, candidate search, phase-separated outcomes and fresh held-out inputs; random exploration is allowed to fail'}
def execute(state,concept,a,b):
 lesson=state.get('mind_curriculum',{}).get('retained',{}).get(concept)
 if not lesson:raise ValueError('This procedure has not yet passed retention checks')
 if any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>100000 for v in (a,b)):raise ValueError('Use finite numeric inputs within 100000')
 expr=lesson['template'].replace('a','('+str(a)+')').replace('b','('+str(b)+')')
 return {'concept':concept,'expression':expr,'result':arithmetic(expr),'lesson':lesson}
