"""Checked native dataflow plans with dependencies, branches and acceptance tests."""
import copy,json,time,hashlib
from .reasoning_engine import pipeline
from .workflow_contracts import equivalent
from .native_synthesis import bounded

def run_plan(spec):
 if not isinstance(spec,dict):raise ValueError('Provide a plan object')
 encoded=json.dumps(spec,sort_keys=True,allow_nan=False)
 if len(encoded)>65536:raise ValueError('Plan specification exceeds 64 KB')
 plan_sha256=hashlib.sha256(encoded.encode()).hexdigest()
 nodes=spec.get('nodes');original=bounded(spec.get('input'));checks=spec.get('assertions',[])
 if not isinstance(nodes,list) or not 1<=len(nodes)<=16 or not isinstance(checks,list) or len(checks)>32:raise ValueError('Use 1–16 nodes and at most 32 assertions')
 ids=[n.get('id') for n in nodes if isinstance(n,dict)]
 if len(ids)!=len(nodes) or any(not isinstance(k,str) or not k.isidentifier() or len(k)>40 or k=='input' for k in ids) or len(set(ids))!=len(ids):raise ValueError('Nodes need unique identifier names other than input')
 allowed=set(ids)|{'input'};dependencies={}
 for node in nodes:
  from .native_operations import validate_steps
  for arm in ('steps','then','else'):
   if arm in node and (not isinstance(node[arm],list) or len(node[arm])>12 or any(not isinstance(s,dict) or not isinstance(s.get('op'),str) for s in node[arm])):raise ValueError('Every plan arm requires 0–12 typed operation objects')
   if arm in node:validate_steps(node[arm],allow_empty=True)
  refs=node.get('combine') if 'combine' in node else [node.get('from','input')]
  if not isinstance(refs,list) or not 1<=len(refs)<=8 or any(ref not in allowed for ref in refs):raise ValueError('Use known node references')
  if node.get('when'):
   condition=node['when']
   if not isinstance(condition,dict) or condition.get('from') not in allowed or condition.get('relation') not in ('equal','greater','less','at_least','at_most'):raise ValueError('Provide a typed branch condition on a known node')
   refs=refs+[condition['from']]
  dependencies[node['id']]=set(refs)-{'input'}
 output=spec.get('output',ids[-1])
 if output not in allowed:raise ValueError('Unknown output node')
 # Reject invalid graphs before running even their independent prefixes.
 schedule=[];remaining=set(ids);completed=set()
 while remaining:
  layer=[ident for ident in ids if ident in remaining and dependencies[ident]<=completed]
  if not layer:raise ValueError('Plan contains a dependency cycle')
  schedule.append(layer);completed.update(layer);remaining.difference_update(layer)
 for check in checks:
  if not isinstance(check,dict) or check.get('node') not in allowed or 'expected' not in check:raise ValueError('Assertions require a known node and expected value')
  bounded(check['expected'])
 values={'input':copy.deepcopy(original)};pending=list(nodes);trace=[];started=time.perf_counter()
 while pending:
  if time.perf_counter()-started>1:raise ValueError('Plan computation budget exhausted')
  ready=next((node for node in pending if dependencies[node['id']]<=values.keys()),None)
  if ready is None:raise ValueError('Plan contains a dependency cycle')
  node=ready;pending.remove(node);value=[copy.deepcopy(values[k]) for k in node['combine']] if 'combine' in node else copy.deepcopy(values[node.get('from','input')]);branch=None
  steps=node.get('steps',[])
  try:
   if node.get('when'):
    condition=node['when'];left=values[condition['from']];right=condition.get('value');relation=condition['relation']
    branch=left==right if relation=='equal' else left>right if relation=='greater' else left<right if relation=='less' else left>=right if relation=='at_least' else left<=right
    steps=node.get('then',[]) if branch else node.get('else',[])
   result=pipeline(value,steps) if steps else {'result':bounded(value),'verified':True,'trace':[]}
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:
   return {'status':'failed','failed_node':node['id'],'error':str(exc),'trace':trace,'output':None,'committed':False,'model_calls':0,'blocked_nodes':[n['id'] for n in pending],'schedule':schedule,'plan_sha256':plan_sha256,'next_step':'Correct the failed node or its input and rerun the copied plan; no final result was committed.'}
  values[node['id']]=copy.deepcopy(result['result']);trace.append({'node':node['id'],'dependencies':sorted(dependencies[node['id']]),'branch':branch,'steps':copy.deepcopy(steps),'result':copy.deepcopy(result['result']),'verified':result['verified'],'checks':result['trace']})
 assertions=[]
 for check in checks:
  if not isinstance(check,dict) or check.get('node') not in values or 'expected' not in check:raise ValueError('Assertions require a known node and expected value')
  actual=values[check['node']];assertions.append({'node':check['node'],'actual':copy.deepcopy(actual),'expected':copy.deepcopy(check['expected']),'passed':equivalent(actual,check['expected'])})
 passed=all(row['passed'] for row in assertions)
 return {'status':'complete' if passed else 'acceptance-failed','output':copy.deepcopy(values[output]) if passed else None,'trace':trace,'assertions':assertions,'verified_operations':True,'task_acceptance_verified':bool(assertions) and passed,'committed':passed,'input_unchanged':True,'model_calls':0,'plan_sha256':plan_sha256,'schedule':schedule,'elapsed_ms':round((time.perf_counter()-started)*1000,3),'scope':'Copied pure dataflow with explicit branches; schedule groups independent nodes but execution remains sequential. No shell, file, model or network calls. Task correctness requires supplied assertions.'}

def export_plan(spec,report):
 if report.get('status')!='complete':raise ValueError('Only a completed checked plan can be exported')
 from .native_work import python_export,digest
 from .function_testing import test_function
 replay=run_plan(spec)
 if replay.get('status')!='complete' or report.get('plan_sha256')!=replay['plan_sha256'] or not equivalent(report.get('output'),replay['output']) or not equivalent(report.get('trace'),replay['trace']):raise ValueError('Plan or recorded results changed; run and verify the current plan before export')
 helpers=[];main=['def transform(value):',"    values = {'input': value}"];values={'input':copy.deepcopy(spec.get('input'))};lookup={node['id']:node for node in spec['nodes']}
 for index,row in enumerate(report['trace']):
  node=lookup[row['node']];value=[copy.deepcopy(values[k]) for k in node['combine']] if 'combine' in node else copy.deepcopy(values[node.get('from','input')])
  main.append('    current = ['+', '.join('values['+repr(k)+']' for k in node['combine'])+']' if 'combine' in node else '    current = values['+repr(node.get('from','input'))+']')
  arms=[('then',node.get('then',[])),('else',node.get('else',[]))] if node.get('when') else [('steps',node.get('steps',[]))]
  for arm,steps in arms:
   expected=pipeline(copy.deepcopy(value),steps)['result'] if steps else copy.deepcopy(value)
   source=python_export(steps,value,expected)['source'];helpers.append(source.replace('def transform(value):','def node_'+str(index)+'_'+arm+'(value):',1))
  if node.get('when'):
   condition=node['when'];operator={'equal':'==','greater':'>','less':'<','at_least':'>=','at_most':'<='}[condition['relation']]
   main+=['    if values['+repr(condition['from'])+'] '+operator+' '+repr(condition.get('value'))+':','        values['+repr(node['id'])+'] = node_'+str(index)+'_then(current)','    else:','        values['+repr(node['id'])+'] = node_'+str(index)+'_else(current)']
  else:main.append('    values['+repr(node['id'])+'] = node_'+str(index)+'_steps(current)')
  values[node['id']]=copy.deepcopy(row['result'])
 for assertion in spec.get('assertions',[]):main.append('    assert values['+repr(assertion['node'])+'] == '+repr(assertion['expected']))
 main.append('    return values['+repr(spec.get('output',spec['nodes'][-1]['id']))+']')
 source='\n\n'.join(helpers+['\n'.join(main)+'\n']);cases=[{'args':[spec.get('input')],'expected':report['output']}]
 for value in spec.get('validation_inputs',[])[:8]:
  result=run_plan({**spec,'input':value})
  if result['status']!='complete':raise ValueError('A supplied validation input fails the plan; source withheld instead of dropping that test')
  cases.append({'args':[value],'expected':result['output']})
 checks=test_function({'source':source,'function':'transform','cases':cases})
 if not checks['all_passed']:raise ValueError('Plan export failed bounded function checks; source withheld')
 return {'source':source,'source_sha256':digest(source),'checks':checks,'scope':'Standalone pure Python plan checked on these explicit inputs; original task assertions are included. No full program or host command ran.'}
