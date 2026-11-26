"""Compile checked data workflows into self-contained, create-only Python projects."""
import ast,copy,hashlib,json,re,uuid
from .function_testing import test_function

def function_source(steps):
 helpers=[]
 if any(s['op']=='unique' for s in steps):helpers.append('''def same_value(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, float) and isinstance(b, float) and str(a) == str(b)
    if isinstance(a, list) or isinstance(b, list):
        if not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b):
            return False
        for i in range(len(a)):
            if not same_value(a[i], b[i]):
                return False
        return True
    if isinstance(a, dict) or isinstance(b, dict):
        if not isinstance(a, dict) or not isinstance(b, dict) or len(a) != len(b):
            return False
        for key in a:
            if key not in b or not same_value(a[key], b[key]):
                return False
        return True
    return a == b
''')
 if any(s['op'] in ('sum','mean') for s in steps):helpers.append('''def compensated_sum(values):
    total = 0.0
    correction = 0.0
    for value in values:
        following = total + value
        if abs(total) >= abs(value):
            correction += (total - following) + value
        else:
            correction += (value - following) + total
        total = following
    return total + correction
''')
 lines=['def transform(value):']
 for step in steps:
  op=step['op'];literal=lambda key:repr(step[key])
  if op in ('strip','upper','lower'):code=['value = value.'+op+'()']
  elif op=='reverse':code=['value = value[::-1]']
  elif op=='lines':code=['value = value.splitlines()']
  elif op=='sort':
   if step.get('field') is not None:raise ValueError('Project compiler currently sorts scalar lists; extract the field first')
   code=['value = sorted(value)']+(['value = value[::-1]'] if step.get('descending') else [])
  elif op=='unique':code=['unique = []','for item in value:','    found = False','    for previous in unique:','        if same_value(item, previous):','            found = True','    if not found:','        unique.append(item)','value = unique']
  elif op in ('add','scale','divide'):
   symbol={'add':'+','scale':'*','divide':'/'}[op];expression='item '+symbol+' '+literal('value');code=['value = ['+expression+' for item in value] if isinstance(value, list) else value '+symbol+' '+literal('value')]
  elif op=='take':code=['value = value[:'+literal('count')+']']
  elif op=='field':code=['value = [item['+literal('name')+'] for item in value] if isinstance(value, list) else value['+literal('name')+']']
  elif op=='numbers':code=['value = [float(item) for item in value]']
  elif op=='join':code=['value = '+repr(str(step.get('separator','\n'))[:100])+'.join([str(item) for item in value])']
  elif op=='replace':code=['value = value.replace('+literal('old')+', '+literal('new')+')']
  elif op=='frequencies':code=['counts = {}','for item in value:','    key = str(item)','    counts[key] = counts.get(key, 0) + 1','value = counts']
  elif op in ('sum','mean','minimum','maximum','count'):
   expression={'sum':'compensated_sum(value)','mean':'compensated_sum(value) / len(value)','minimum':'min(value)','maximum':'max(value)','count':'len(value)'}[op];code=['value = '+expression]
  elif op=='median':code=['ordered = sorted(value)','n = len(ordered)','value = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2']
  elif op=='filter':
   relation=step.get('relation','equal');item='item['+repr(step['field'])+']' if step.get('field') is not None else 'item';target=literal('value');symbols={'equal':'==','greater':'>','less':'<','at_least':'>=','at_most':'<='}
   condition=target+' in '+item if relation=='contains' else item+' '+symbols[relation]+' '+target;code=['value = [item for item in value if '+condition+']']
  else:raise ValueError('Standalone project compilation is not yet available for operation '+op)
  lines.extend('    '+line for line in code)
 lines.append('    return value');return '\n'.join(helpers+['\n'.join(lines)])+'\n'

def prepare(body):
 from .reasoning_engine import pipeline
 from .workflow_contracts import equivalent
 name=body.get('name');steps=body.get('steps');cases=body.get('cases')
 if steps is None and isinstance(body.get('goal'),str):
  from .native_task_planner import compile_goal
  plan=compile_goal(body['goal'])
  if not plan or plan.get('status')!='planned':raise ValueError('The goal needs a supported explicit data workflow')
  steps=plan['steps']
 if not isinstance(name,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,40}',name):raise ValueError('Use a simple project name, up to 41 characters')
 if not isinstance(cases,list) or not 3<=len(cases)<=16:raise ValueError('Provide 3 to 16 input/expected acceptance cases')
 for case in cases:
  if not isinstance(case,dict) or 'input' not in case or 'expected' not in case:raise ValueError('Each case needs input and expected')
  result=pipeline(copy.deepcopy(case['input']),steps)
  if not equivalent(result['result'],case['expected']):raise ValueError('The requested workflow does not match an acceptance example')
 source=function_source(steps);tests=test_function({'source':source,'function':'transform','cases':[{'args':[case['input']],'expected':case['expected']} for case in cases]})
 if not tests['all_passed']:raise ValueError('Generated function failed its acceptance checks: '+json.dumps(tests)[:1200])
 main='import json\nimport sys\n\n'+source+'\nif __name__ == "__main__":\n    sys.stdin.reconfigure(encoding="utf-8")\n    sys.stdout.reconfigure(encoding="utf-8")\n    value = json.load(sys.stdin)\n    print(json.dumps(transform(value), ensure_ascii=False, allow_nan=False))\n'
 test='import math\nimport unittest\nfrom main import transform\n\ndef matches(a, b):\n    if type(a) in (int, float) and type(b) in (int, float):\n        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)\n    if type(a) is not type(b):\n        return False\n    if isinstance(a, list):\n        return len(a) == len(b) and all(matches(x, y) for x, y in zip(a, b))\n    if isinstance(a, dict):\n        return a.keys() == b.keys() and all(matches(a[k], b[k]) for k in a)\n    return a == b\n\nclass AcceptanceTests(unittest.TestCase):\n    def test_examples(self):\n        for case in '+repr(cases)+':\n            with self.subTest(input=case["input"]):\n                self.assertTrue(matches(transform(case["input"]), case["expected"]))\n\nif __name__ == "__main__":\n    unittest.main()\n'
 ast.parse(main);ast.parse(test)
 files={'main.py':main,'test_main.py':test,'README.md':'# '+name+'\n\nStandalone Python data-workflow utility. No Neural App dependency.\n\nRun `python main.py` with one JSON value on standard input.\nRun `python -m unittest -v` from this directory for acceptance tests.\n\nThe generated function passed '+str(tests['total'])+' cases in the app\'s bounded AST interpreter. The CLI wrapper and unittest runner were syntax checked but not invoked during preparation. Supported inputs are the workflow\'s typed domain; examples are not a proof for arbitrary input.\n'}
 hashes={name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()};manifest={'project':name,'steps':steps,'acceptance_cases':cases,'sha256':hashes,'function_test':tests,'host_code_executed':False};files['project.json']=json.dumps(manifest,indent=2,ensure_ascii=False)
 return {'id':uuid.uuid4().hex,'name':name,'status':'prepared','files':files,'hashes':{name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()},'tests':tests,'scope':'Create-only project proposal. Function tested in memory; full CLI wrapper not executed.'}

def summary(project):
 return {'id':project['id'],'name':project['name'],'status':project['status'],'files':{name:{'bytes':len(text.encode()),'sha256':project['hashes'][name]} for name,text in project['files'].items()},'tests':{k:project['tests'][k] for k in ('passed','total','all_passed')},'scope':project['scope']}

def install(project,tools):
 if project.get('status')!='prepared':raise ValueError('Choose a prepared project')
 if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,40}',str(project.get('name',''))):raise ValueError('Invalid prepared project name')
 target=tools.path('projects/'+project['name'])
 if target.exists():raise ValueError('Project directory already exists; choose a new name to preserve it')
 target.parent.mkdir(parents=True,exist_ok=True);stage=target.parent/('.build-'+uuid.uuid4().hex);stage.mkdir();written=[]
 try:
  for name,text in project['files'].items():
   if name not in ('main.py','test_main.py','README.md','project.json'):raise ValueError('Unexpected generated project filename')
   path=stage/name;path.write_bytes(text.encode());written.append(path)
   if hashlib.sha256(path.read_bytes()).hexdigest()!=project['hashes'][name]:raise ValueError('Generated-file verification failed')
  stage.rename(target);project['status']='created';project['path']=str(target)
  return {'project_created':project['name'],'path':str(target),'files':list(project['files']),'verified_hashes':True,'tests':{k:project['tests'][k] for k in ('passed','total','all_passed')},'scope':'New local project created; existing files preserved and project code not launched'}
 finally:
  if stage.exists() and stage.resolve().parent==target.parent.resolve():
   for path in written:
    if path.resolve().parent==stage.resolve() and path.is_file():path.unlink()
   stage.rmdir()
