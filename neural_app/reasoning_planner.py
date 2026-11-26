"""Minimum-cost planning in an explicit finite transition model; no actions run."""
import heapq,itertools,time,math
from fractions import Fraction
from .symbolic_reasoning import literal,opposite

def labels(value,maximum=16):
 if not isinstance(value,list) or len(value)>maximum:raise ValueError('Use a bounded list of explicit fact labels')
 result=frozenset(literal(v) for v in value)
 if any(opposite(v) in result for v in result):raise ValueError('A fact list contains opposite assertions')
 return result

def plan(body):
 initial=labels(body.get('initial',[]),128);goals=labels(body.get('goals'));raw=body.get('actions')
 if not goals or not isinstance(raw,list) or not 1<=len(raw)<=64:raise ValueError('Supply goals and 1–64 model actions')
 actions=[];names=set();universe=set(initial)|set(goals)
 for row in raw:
  if not isinstance(row,dict):raise ValueError('Each model action needs a name, preconditions and effects')
  name=literal(row.get('name'));pre=labels(row.get('preconditions',[]));add=labels(row.get('add',[]));remove=labels(row.get('remove',[]));cost=row.get('cost',1)
  if name in names or add&remove or type(cost)not in (int,float) or not math.isfinite(cost) or not 0<cost<=1e6:raise ValueError('Use distinct action names, disjoint effects and positive finite costs')
  names.add(name);universe.update(pre|add|remove);actions.append({'name':name,'pre':pre,'add':add,'remove':remove,'cost':Fraction(str(cost))})
 if len({v[4:] if v.startswith('not ') else v for v in universe})>128:raise ValueError('Model exceeds 128 distinct fact variables')
 limit=body.get('state_limit',4096);depth_limit=body.get('max_steps',16)
 if type(limit)is not int or not 1<=limit<=10000 or type(depth_limit)is not int or not 1<=depth_limit<=32:raise ValueError('Use state_limit 1–10000 and max_steps 1–32')
 serial=itertools.count();root=(initial,0);queue=[(Fraction(0),next(serial),root)];costs={root:Fraction(0)};parents={};examined=0;target=None;deadline=time.monotonic()+1;complete=True;depth_pruned=0
 while queue:
  if examined>=limit or time.monotonic()>deadline:complete=False;break
  cost,_,key=heapq.heappop(queue)
  if costs[key]!=cost:continue
  state,depth=key;examined+=1
  if goals<=state:target=key;break
  if depth>=depth_limit:depth_pruned+=1;continue
  for index,action in enumerate(actions):
   if not action['pre']<=state:continue
   updated=(state-action['remove']-{opposite(v) for v in action['add']})|action['add'];following=(frozenset(updated),depth+1);candidate=cost+action['cost']
   if following in costs and costs[following]<=candidate:continue
   if len(costs)>=10000 or len(queue)>=10000:complete=False;break
   costs[following]=candidate;parents[following]=(key,index);heapq.heappush(queue,(candidate,next(serial),following))
  if not complete:break
 if target is None:return {'status':'no-plan-within-bounds' if complete else 'undetermined','plan':None,'states_examined':examined,'search_complete_within_bounds':complete,'max_steps':depth_limit,'depth_pruned':depth_pruned,'next_step':'Check missing action definitions, unknown preconditions or the search limits.','scope':'Explicit finite transition model only; no real action executed and no general impossibility established.'}
 path=[];cursor=target
 while cursor!=root:
  previous,index=parents[cursor];path.append(index);cursor=previous
 path.reverse();state=set(initial);verified_cost=Fraction(0);trace=[]
 # Replay the found route from its initial conditions before returning it.
 for index in path:
  action=actions[index]
  if not action['pre']<=state:raise ValueError('Plan replay failed a precondition')
  before=set(state)
  for item in action['remove']:state.discard(item)
  for item in action['add']:state.discard(opposite(item));state.add(item)
  verified_cost+=action['cost'];trace.append({'action':action['name'],'cost':float(action['cost']),'added':sorted(state-before),'removed':sorted(before-state)})
 if not goals<=state or verified_cost!=costs[target] or frozenset(state)!=target[0]:raise ValueError('Plan replay failed its goals, cost or predicted final state')
 return {'status':'planned','plan':trace,'total_cost':float(verified_cost),'initial':sorted(initial),'final':sorted(state),'goals':sorted(goals),'states_examined':examined,'plan_replayed':True,'minimum_cost_within_bounds_proven':True,'max_steps':depth_limit,'next_step':'Review whether the explicit preconditions, costs and effects describe the intended task before any real execution.','scope':'Minimum-cost route within the supplied finite model and step bound. Adding a fact replaces its explicit opposite; removing a fact leaves it unknown. No host, network or real-world action ran.'}
