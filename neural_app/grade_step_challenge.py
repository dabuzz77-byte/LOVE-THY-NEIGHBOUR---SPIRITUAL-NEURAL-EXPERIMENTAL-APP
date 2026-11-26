"""Acceptance evidence for the next assessed capability step."""
import json,math,random,threading,time,types

def challenge(seed):
 from .reasoning_engine import ReasoningEngine,pipeline
 from .dialogue_work import resolve
 from .empirical_learning import fit,predict,sensitivity
 from .memory_revisions import update,respond
 from .evidence_index import retrieve
 from .native_skills import calculate
 from .arithmetic_contract import verify_expression
 rng=random.Random(seed);rows=[]
 def check(domain,name,call):
  started=time.perf_counter()
  try:passed=call() is True;error=None
  except Exception as exc:passed=False;error=type(exc).__name__+': '+str(exc)[:180]
  rows.append({'domain':domain,'name':name,'passed':passed,'elapsed_ms':round((time.perf_counter()-started)*1000,3),'error':error})
 for i in range(6):
  a,b,c=[rng.randrange(1,100) for _ in range(3)]
  check('numeric-integrity','independent rational reference '+str(i),lambda a=a,b=b,c=c:verify_expression(f'({a}+{b})/{c}',calculate(f'({a}+{b})/{c}')))
 def bad_arithmetic():return not verify_expression('18/3',7)
 check('numeric-integrity','wrong arithmetic rejected',bad_arithmetic)
 for i in range(5):
  slope=rng.randrange(1,9);intercept=rng.randrange(-20,20);xs=list(range(16));ys=[slope*x+intercept for x in xs]
  def measured(slope=slope,intercept=intercept,xs=xs,ys=ys):
   model=fit({'x':xs,'y':ys});return model['validated_against_baseline'] and math.isclose(model['slope'],slope) and math.isclose(predict(model,17)['result'],slope*17+intercept) and predict(model,17)['extrapolation']
  check('measured-modelling','chronological affine validation '+str(i),measured)
 def bad_fit():return fit({'x':list(range(12)),'y':[3*i+2 for i in range(9)]+[-100,-200,-300]})['validated_against_baseline'] is False
 check('self-assessment','failed held-out model remains failed',bad_fit)
 for i in range(4):
  weight=-rng.randrange(1,10);low=rng.randrange(1,8);high=low+rng.randrange(1,8)
  check('causal-sensitivity','negative coefficient range '+str(i),lambda weight=weight,low=low,high=high:sensitivity({'values':{'x':low},'equations':{'y':{'bias':3,'weights':{'x':weight}}},'ranges':{'x':[low,high]}})['ranges']['y']==[3+weight*high,3+weight*low])
 def memory_revisions():
  s={};update(s,'colour','blue');update(s,'Colour','green');update(s,'colour','green');r=respond('what was my colour?',s);return r['current']['value']=='green' and len(r['previous'])==1 and r['previous'][0]['value']=='blue'
 check('memory-continuity','current versus previous report',memory_revisions)
 check('memory-continuity','related-term retrieval',lambda:retrieve('budget',[{'title':'Finance','text':'Money supports provision.'}])[0]['title']=='Finance')
 def multi_turn():
  engine=ReasoningEngine({});first=engine.plan_and_run('extract field score then sort descending then take first 2: [{"score":4},{"score":9},{"score":2}]');h=[{'request':'original','answer':json.dumps(first)}]
  return resolve('now get mean',h,engine)['result']==6.5 and resolve('do the same with: [{"score":1},{"score":5},{"score":8}]',h,engine)['result']==[8,5]
 check('dialogue-continuity','typed follow-up and exact parameter reuse',multi_turn)
 check('dialogue-continuity','topic change does not reuse stale data',lambda:resolve('now sort',[{'request':'hello','answer':'hello'}],ReasoningEngine({}))['status']=='needs-input')
 def auto_measurements():
  engine=ReasoningEngine({})
  for i in range(8):engine.learn_observed_pair({'source':'fixture','parent_event':i,'observations':[{'path':['samples','x'],'value':i},{'path':['samples','y'],'value':i*4+1}]})
  models=engine.view()['measured_relationships'];return len(models)==1 and next(iter(models.values()))['validated_against_baseline']
 check('automatic-learning','paired observations fit without manual form',auto_measurements)
 def scheduler(which):
  engine=ReasoningEngine({});c=types.SimpleNamespace(r=types.SimpleNamespace(user_active=False),lock=threading.RLock(),element_thinking=types.SimpleNamespace(view=lambda:{'layers':[]}),bus=types.SimpleNamespace(publish=lambda _:None))
  def submit(b):return engine.submit_workflow(b)['job_id']
  def tick():engine.next_at=0;engine.tick(c)
  if which=='priority':
   low=submit({'input':[1,2],'steps':[{'op':'count'}],'priority':0});high=submit({'input':[3,4],'steps':[{'op':'count'}],'priority':5});tick();j={r['id']:r for r in engine.view()['jobs']};return j[high]['status']=='complete' and j[low]['status']=='queued'
  first=submit({'input':[3,1,2] if which=='dependency' else 'bad','steps':[{'op':'sort'}] if which=='dependency' else [{'op':'sum'}]});second=submit({'input_from':first,'steps':[{'op':'median'}]});tick();tick();j={r['id']:r for r in engine.view()['jobs']}
  return j[second]['output']['result']==2 if which=='dependency' else j[second]['status']=='blocked'
 for which in ('priority','dependency','failure'):check('work-orchestration',which+' handling',lambda which=which:scheduler(which))
 from .symbolic_reasoning import what_if,sufficient_facts
 def logical_change():
  result=what_if({'facts':['p'],'rules':[{'if':['p'],'then':'q'}],'query':'q','remove':['p']})
  return result['baseline']['status']=='supported' and result['alternative']['status']=='unknown' and result['status_changed']
 check('logical-auditing','premise removal changes conclusion',logical_change)
 def minimal():
  result=sufficient_facts({'facts':['p','r','unused'],'rules':[{'if':['p'],'then':'q'},{'if':['r'],'then':'q'}],'query':'q'})
  return result['status']=='supported' and len(result['sufficient_facts'])==1 and 'unused' in result['removed_as_unnecessary']
 check('logical-auditing','redundant premises removed with checks',minimal)
 from .language_workflow import execute as execute_language_workflow
 check('language-bridge','proposal binds current request data',lambda:execute_language_workflow('arrange these names: b\na','{"steps":[{"op":"lines"},{"op":"sort"},{"op":"join"}]}')['result']=='a\nb')
 def invented_input():
  try:execute_language_workflow('arrange: b\na','{"input":"invented","steps":[{"op":"upper"}]}');return False
  except ValueError:return True
 check('language-bridge','model cannot replace supplied data',invented_input)
 def numeric_dialogue():
  h=[{'request':'calculate 4+6','answer':'10','native_skill':'arithmetic'}];out=resolve('now multiply by 3',h,ReasoningEngine({}));return out['result']==30 and out['trace'][0]['independent_check']
 check('dialogue-continuity','numeric follow-up remains independently checked',numeric_dialogue)
 from .empirical_learning import intervention_study
 def experiment_test():
  out=intervention_study({'treated':[7,8,9,10],'control':[1,2,3,4],'design':'declared-randomized'})
  return out['exact'] and out['difference_in_means']==6 and math.isclose(out['permutation_p_value'],2/70) and out['causal_status'].startswith('conditional')
 check('experimental-causal-reasoning','exact randomized-group comparison',experiment_test)
 check('experimental-causal-reasoning','observational difference is not causal identification',lambda:intervention_study({'treated':[7,8,9,10],'control':[1,2,3,4]})['causal_status'].startswith('not identified'))
 from .model_selection import stratified_comparison
 def nonlinear():
  xs=list(range(25));m=fit({'family':'auto','x':xs,'y':[3*x*x-2*x+4 for x in xs]})
  return m['family']=='quadratic' and math.isclose(predict(m,26)['result'],1980,rel_tol=1e-8)
 check('measured-modelling','nonlinear family transfer',nonlinear)
 def confounding():
  out=stratified_comparison({'strata':[{'treated':[2]*9,'control':[1]},{'treated':[10],'control':[9]*9}]})
  return out['direction_reversal'] and out['standardized_difference']==1
 check('experimental-causal-reasoning','pooled direction reversal detected',confounding)
 def explanation_continuity():
  engine=ReasoningEngine({});out=engine.plan_and_run('sort ascending: [5,2,8]');h=[{'request':'sort','answer':json.dumps(out)}];explained=resolve('which steps did you use?',h,engine);h.append({'request':'explain','answer':json.dumps(explained)})
  return resolve('now get mean',h,engine)['result']==5
 check('dialogue-continuity','explanation retains typed context',explanation_continuity)
 return rows
