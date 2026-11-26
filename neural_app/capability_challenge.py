"""Fresh-input checks for the expanded coding, recovery and evidence capabilities."""
import collections,json,math,random,threading,time,types

def challenge(seed=0):
 from .function_testing import test_function
 from .cognitive_executive import CognitiveExecutive
 from .evidence_review import review as evidence
 from .prediction_review import review as prediction
 from .native_language import canonical_request
 from .task_reflection import reflect
 rng=random.Random(seed);rows=[]
 def check(domain,name,fn):
  start=time.perf_counter()
  try:passed=fn() is True;error=None
  except Exception as e:passed=False;error=type(e).__name__+': '+str(e)[:200]
  rows.append({'domain':domain,'name':name,'passed':passed,'error':error,'elapsed_ms':round((time.perf_counter()-start)*1000,3)})
 fixtures=[
 ('indexed weighted sum','def f(xs):\n    total=0\n    for i, x in enumerate(xs, 1):\n        total += i*x\n    return total\n',lambda xs:sum((i+1)*v for i,v in enumerate(xs))),
 ('dictionary iteration','def f(xs):\n    d={}\n    for x in xs:\n        d[x]=d.get(x,0)+1\n    out=[]\n    for k,v in d.items():\n        out.append([k,v])\n    return out\n',lambda xs:[[k,v] for k,v in collections.Counter(xs).items()]),
 ('break and continue','def f(xs):\n    result=[]\n    for x in xs:\n        if x < 0:\n            break\n        if x == 0:\n            continue\n        result.append(x*2)\n    return result\n',lambda xs:[2*v for v in xs[:next((i for i,v in enumerate(xs) if v<0),len(xs))] if v!=0]),
 ('unpacking comprehension','def f(xs):\n    return [i*x for i,x in enumerate(xs) if i%2 == 0]\n',lambda xs:[i*v for i,v in enumerate(xs) if i%2==0]),
 ('zip and reverse','def f(xs):\n    out=[]\n    for a,b in zip(xs,reversed(xs)):\n        out.append(a-b)\n    return out\n',lambda xs:[a-b for a,b in zip(xs,reversed(xs))]),
 ('descending sort','def f(xs):\n    return sorted(xs,reverse=True)\n',lambda xs:sorted(xs,reverse=True))]
 for name,source,oracle in fixtures:
  for i in range(3):
   data=[rng.randint(-5,9) for _ in range(rng.randint(0,15))]
   check('coding-transfer',name+' '+str(i),lambda source=source,data=data,oracle=oracle:test_function({'source':source,'function':'f','cases':[{'args':[data],'expected':oracle(data)}]})['all_passed'])
 check('coding-validation','break outside loop is syntax failure',lambda:test_function({'source':'def f():\n    break\n','function':'f','cases':[{'args':[],'expected':None}]})['status']=='invalid-syntax')
 check('coding-validation','huge iterable expansion rejected',lambda:not test_function({'source':'def f():\n    return list(range(1000000000))\n','function':'f','cases':[{'args':[],'expected':None}]})['all_passed'])
 def make():
  r=types.SimpleNamespace(s={},user_active=False,controller=types.SimpleNamespace(save=lambda:None));w=types.SimpleNamespace(r=r,lock=threading.RLock(),record=lambda *a:None,context=lambda:{})
  r.workbench=w;return CognitiveExecutive(w),w
 def recovery():
  e,w=make();g=e.submit('calculate 6+3 then multiply that by 4');e.tick(force=True);e.control('pause');assert e.tick(force=True) is None and g['steps'][0]['result']==9
  e2=CognitiveExecutive(w);assert e2.s['goals'][-1]['status']=='paused';e2.control('resume');e2.tick(force=True)
  return g['status']=='complete' and g['steps'][-1]['result']==36 and g['steps'][0]['attempts']==1
 check('work-recovery','pause, restart, resume retains prior verified result',recovery)
 def failure_revision():
  e,w=make();g=e.submit('calculate 8+1 then divide that by 0 then add 2 to the result');e.tick(force=True);e.tick(force=True)
  assert g['status']=='needs-input';e.revise(1,'calculate {{previous}} / 3');e.tick(force=True);e.tick(force=True)
  return g['status']=='complete' and g['steps'][-1]['result']==5 and g['steps'][0]['attempts']==1
 check('work-recovery','failed dependency revised without repeating finished work',failure_revision)
 def cancelled():
  e,w=make();g=e.submit('calculate 1+2 then multiply that by 4');e.tick(force=True);e.control('cancel');e.tick(force=True)
  return g['status']=='cancelled' and g['steps'][1]['attempts']==0
 check('work-recovery','cancel stops pending work',cancelled)
 def procedure_reuse():
  e,w=make();g=e.submit('calculate 3+4 then multiply that by 5 then subtract 2 from the result')
  for _ in range(3):e.tick(force=True)
  cloned=e.reuse({'input':'11+2','goal_id':g['id']})
  for _ in range(3):e.tick(force=True)
  return cloned['status']=='complete' and cloned['steps'][-1]['result']==63 and g['steps'][-1]['result']==33 and all(s['attempts']==1 for s in cloned['steps'])
 check('learning','reuse completed procedure on held-out input',procedure_reuse)
 base={'claim':'Reported coverage','metric':'coverage','population':'adults','period':'2025','unit':'percent','method':'survey','source':'https://example.org/a','value':40}
 check('research-review','shared study is not independent confirmation',lambda:evidence({'claims':[{**base,'id':'a','study_id':'s'},{**base,'id':'b','source':'https://another.example/a','study_id':'s'}]})['comparisons'][0]['shared_source_or_study'])
 check('research-review','different population is not labelled a conflict',lambda:not evidence({'claims':[base,{**base,'population':'children','value':90}]})['comparisons'][0]['comparable_as_declared'])
 check('research-review','different units not directly compared',lambda:not evidence({'claims':[base,{**base,'unit':'fraction','value':.4}]})['comparisons'][0]['comparable_as_declared'])
 check('research-review','matching conditions expose numeric disagreement',lambda:evidence({'claims':[base,{**base,'source':'https://other.example/a','value':60}]})['comparisons'][0]['numeric_difference']==20)
 check('research-review','missing method remains explicit',lambda:'method' in evidence({'claims':[{**base,'method':''},base]})['comparisons'][0]['missing_context'])
 for i in range(4):
  actual=[rng.randint(-20,20) for _ in range(8)]
  check('prediction-review','unseen numerical outcomes '+str(i),lambda actual=actual:prediction({'observations':[{'predicted':a+1,'actual':a,'baseline':a+3} for a in actual]})['metrics']['mae']==1)
 check('prediction-review','probability calibration includes endpoint one',lambda:prediction({'kind':'probability','observations':[{'predicted':1,'actual':1,'baseline':.5}]*3})['calibration_bins'][-1]['count']==3)
 check('prediction-review','bad predictor fails its baseline comparison',lambda:not prediction({'observations':[{'predicted':10,'actual':a,'baseline':a} for a in (1,2,3)]})['metrics']['beats_baseline_mae'])
 for typo,correct in [('calcluate','calculate'),('statistcs','statistics'),('upppercase','uppercase'),('lowecase','lowercase')]:
  check('conversation',typo+' changes prefix only',lambda typo=typo,correct=correct:canonical_request(typo+' payload calcluate?')==correct+' payload calcluate?')
 check('conversation','code payload remains literal',lambda:canonical_request('debug python: {"source":"calcluate"}')=='debug python: {"source":"calcluate"}')
 body=prediction({'observations':[{'predicted':a,'actual':a,'baseline':0} for a in (1,2,3)]})
 check('conversation','reflection uses latest record without replay',lambda:reflect('how accurate were those predictions?', [{'answer':json.dumps(body)}])['action_repeated'] is False)
 from .personal_context import respond as personal,conversational_only
 history=[{'request':'My project is named First Light.'},{'request':'Actually, my project is named River Lantern.'}]
 check('conversation','latest explicit name correction wins',lambda:personal('What is the name of my project?',history)['answer']=='River Lantern')
 check('conversation','unrelated named entity not substituted',lambda:personal('What is the name of my dog?',history) is None)
 check('conversation','sensitive claim not stored as name',lambda:personal('My password is named example.',[]) is None)
 check('conversation','explanation does not become a file action',lambda:conversational_only('Explain why my project needs tests'))
 check('conversation','native name acknowledgement no model',lambda:personal('My project is named River Lantern. Reply briefly.',[])['model_calls']==0)
 def spectrum_contract():
  from .spectrum_deliberation import SpectrumDeliberation
  spec={'examples':[{'input':2,'output':5},{'input':5,'output':11}],'holdout':[{'input':9,'output':19},{'input':12,'output':25}],'operations':['double','increment'],'max_depth':2}
  c=types.SimpleNamespace(investigations=types.SimpleNamespace(view=lambda:{'items':[{'id':'finite-check','question':'2x+1','experiment_spec':spec}]}),bus=types.SimpleNamespace(publish=lambda _:None))
  engine=SpectrumDeliberation();engine.tick(c,[{'bits':'0'*128}]);view=engine.view()
  return view['latest']['status']=='contract-verified' and engine.use({'id':view['retained_procedures'][0]['id'],'input':17,'expected':35})['matches_supplied_expected']
 check('learning','spectrum and ordered proposals checked on later examples',spectrum_contract)
 def spectrum_bits():
  from .spectrum_logic_sphere import SpectrumLogicSphere
  engine=SpectrumLogicSphere();engine.observe({'source':'finite-check','digest':'source','facts':[{'value':'ABCD'}],'parent_event':7,'provenance':'test fixture'}, {})
  engine.tick(types.SimpleNamespace(bus=types.SimpleNamespace(publish=lambda _:None)))
  return engine.frames[0]['phase']==0 and engine.frames[1]['original_unchanged'] and all(f['result']['bit_filter']['roundtrip'] for f in engine.frames)
 check('reasoning-validation','spectrum endpoints and copied bit invariants',spectrum_bits)
 return rows
