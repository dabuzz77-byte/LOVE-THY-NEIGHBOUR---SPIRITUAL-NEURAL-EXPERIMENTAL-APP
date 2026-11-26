"""Bounded regression evidence for coding work and paired observation handling."""
import json,time

def challenge(seed=0):
 from .function_testing import test_function
 from .tested_repairs import repair
 from .workflow_projects import prepare
 from .cognitive_executive import split_steps
 from .paired_observations import compare
 rows=[]
 def check(domain,name,fn):
  started=time.perf_counter()
  try:passed=fn() is True;error=None
  except Exception as exc:passed=False;error=type(exc).__name__+': '+str(exc)[:200]
  rows.append({'domain':domain,'name':name,'passed':passed,'error':error,'elapsed_ms':round((time.perf_counter()-started)*1000,3)})
 def pure():
  source='def total(values):\n    result = 0\n    for value in values:\n        if value > 0:\n            result += value\n    return result\n';a=seed%10+1
  return test_function({'source':source,'function':'total','cases':[{'args':[[a,-2,3]],'expected':a+3}]})['all_passed']
 check('coding-execution','pure function with loop and condition',pure)
 def fix():
  body={'source':'def combine(a, b):\n    return a - b\n','function':'combine','cases':[{'args':v,'expected':sum(v)} for v in [[3,1],[7,2],[9,4]]]};out=repair(body)
  return out['status']=='validated-proposal' and out['validation']['all_passed'] and out['source_changed'] is False
 check('debugging','test-selected operator repair with separate validation',fix)
 def overfit():
  out=repair({'source':'def f(x):\n    return x - 1\n','function':'f','cases':[{'args':[1],'expected':2},{'args':[2],'expected':3},{'args':[4],'expected':999}]})
  return out['status']=='validation-failed' and out['source_changed'] is False
 check('debugging','overfit repair rejected',overfit)
 def blocked():
  out=test_function({'source':'def f(x):\n    return open(x)\n','function':'f','cases':[{'args':['not-opened'],'expected':None}]})
  return not out['all_passed'] and out['host_access'] is False
 check('coding-execution','host file call unavailable to function tests',blocked)
 def cycle():
  out=test_function({'source':'def f(x):\n    x.append(x)\n    return str(x)\n','function':'f','cases':[{'args':[[]],'expected':'[]'}]})
  return not out['all_passed'] and 'Cyclic' in out['cases'][0]['error']
 check('coding-execution','cyclic expansion rejected before string conversion',cycle)
 def defaults():
  out=test_function({'source':'def f(x: int = 2) -> int:\n    return x + 1\n','function':'f','cases':[{'args':[],'expected':3},{'args':[4],'expected':5}]})
  return out['all_passed']
 check('coding-execution','typed arguments and literal defaults',defaults)
 def annotation():
  out=test_function({'source':'def f(x: open("not-opened")):\n    return x\n','function':'f','cases':[{'args':[1],'expected':1}]})
  return out['status']=='unsupported-source' and out['program_executed'] is False
 check('coding-execution','active annotation not silently treated as a pure definition',annotation)
 def helper_alias():
  values=[];out=test_function({'source':'def push(values):\n    values.append(1)\ndef f(values):\n    push(values)\n    return values\n','function':'f','cases':[{'args':[values],'expected':[1]}]})
  return out['all_passed'] and values==[]
 check('coding-execution','helper mutations preserve local aliasing without changing test fixtures',helper_alias)
 def isolated():
  source='# Preserve licence.\nimport os\nraise RuntimeError("not executed")\ndef f(a, b):\n    return a - b\n';out=repair({'source':source,'isolate_module':True,'function':'f','cases':[{'args':v,'expected':sum(v)} for v in [[1,2],[4,3],[8,9]]]})
  return out['status']=='validated-proposal' and out['source'].startswith('# Preserve licence.\nimport os\nraise RuntimeError') and out['training']['isolated_module'] is True
 check('debugging','isolated module repair preserves surrounding code and licence',isolated)
 def project():
  out=prepare({'name':'challenge','steps':[{'op':'unique'},{'op':'sort'}],'cases':[{'input':v,'expected':sorted(set(v))} for v in [[3,1,3],[5,2,4],[]]]})
  return out['tests']['all_passed'] and set(out['files'])=={'main.py','test_main.py','README.md','project.json'}
 check('software-projects','standalone package and acceptance artifacts',project)
 def quoted():
  payload=json.dumps({'source':'def f(x):\n    return "then"\n','function':'f','cases':[{'args':[1],'expected':'then'}]})
  return len(split_steps('test_python '+payload+' then calculate 2+2'))==2
 check('task-understanding','quoted code delimiter preserved',quoted)
 check('causal-reasoning','within-unit changes preserve mixed directions',lambda:compare({'before':[1,100,4],'after':[3,99,4]})['mean_change']==1/3)
 def emergency():
  from .emergency_review import review
  out=review({'description':'Imagined urgent life-saving communication across declared devices','extent':'combined','nodes':[{'kind':'external-device','name':'hypothetical recipient'}]})
  return out['hypothetical'] and out['execution_authorized'] is False and out['external_connection_created'] is False and out['operation_record_review']['missing'] and len(out['four_way'])==4
 check('ethical-review','hypothetical emergency review does not assert access',lambda:bool(emergency()))
 def symmetric_review():
  from .decision_framework import assess,SYSTEM_REVIEW
  return all('refusal' in assess('study/'+area)['conditional_standard']['symmetry'] and 'conditional protective justification' in assess('study/'+area)['conditional_standard']['hypothetical'] for area in SYSTEM_REVIEW)
 check('ethical-review','conditional consequence review shared across system sectors',symmetric_review)
 def harm_claims():
  from .harm_claim_review import review
  out=review({'case':'creative-access','claims':[{'description':'The child finds joy in the game','status':'hypothetical'},{'description':'Reduced sales are harmful','kind':'revenue','status':'predicted'}]})
  return out['execution_authorized'] is False and out['claims'][1]['human_effect_needed'] is True and out['claims'][0]['declared_status']=='hypothetical' and out['unresolved_claims']==2
 check('ethical-review','joy and revenue claims retain their distinct evidence status',harm_claims)
 return rows
