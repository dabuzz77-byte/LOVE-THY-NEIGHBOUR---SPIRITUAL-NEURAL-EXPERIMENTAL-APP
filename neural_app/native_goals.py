"""Resumable native goal execution with per-stage acceptance and private results."""
import copy,time
from .native_synthesis import bounded
from .workflow_contracts import equivalent

def create(spec,library=None):
 from .native_work import parse_steps
 if not isinstance(spec,dict):raise ValueError('Provide a goal object')
 name=spec.get('name');stages=spec.get('stages')
 if not isinstance(name,str) or not name.strip() or len(name)>100 or not isinstance(stages,list) or not 1<=len(stages)<=12:raise ValueError('Use a name and 1–12 ordered stages')
 value=bounded(spec.get('input'));compiled=[]
 for stage in stages:
  if not isinstance(stage,dict) or not isinstance(stage.get('instruction'),str):raise ValueError('Each stage needs an instruction')
  steps=parse_steps(stage['instruction'])
  learned=(library or {}).get(stage['instruction'].strip().casefold())
  if learned:
   if learned.get('active') is False:raise ValueError('Goal references a revoked workflow: '+stage['instruction'])
   steps=copy.deepcopy(learned['steps'])
  if not steps:raise ValueError('Unsupported stage instruction: '+stage['instruction'][:100])
  if 'expected' in stage:bounded(stage['expected'])
  from .artifact_memory import version
  compiled.append({'dependency_name':stage['instruction'].strip().casefold() if learned else None,'dependency_version':version(learned) if learned else None,'instruction':stage['instruction'],'steps':steps,'has_expected':'expected' in stage,'expected':copy.deepcopy(stage.get('expected')),'procedure_source':learned.get('source_input_sha256') if learned else 'registered-native-operations'})
 if sum(len(s['steps']) for s in compiled)>12:raise ValueError('Use at most 12 total transformations in a goal')
 return {'name':name.strip(),'input':copy.deepcopy(value),'value':copy.deepcopy(value),'stages':compiled,'cursor':0,'status':'running','trace':[],'created':time.time(),'model_calls':0,'committed':False}

def advance(goal,work):
 from .reasoning_engine import pipeline
 if goal['status']!='running':return False
 # Recheck every dependency, including earlier stages, before advancing/committing.
 for dependency in goal['stages']:
  name=dependency.get('dependency_name')
  if name:
   from .artifact_memory import version
   current=work.state.get('workflow_library',{}).get(name)
   if not current or current.get('active') is False or version(current)!=dependency.get('dependency_version'):
    goal.update(status='dependency-invalidated',error='Saved procedure '+name+' was revoked, replaced or removed; revise the goal before retrying');return True
 stage=goal['stages'][goal['cursor']]
 try:result=pipeline(copy.deepcopy(goal['value']),stage['steps'])
 except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:
  goal.update(status='failed',error=str(exc)[:400]);return True
 actual=result['result'];accepted=not stage['has_expected'] or equivalent(actual,stage['expected'])
 goal['trace'].append({'stage':goal['cursor'],'instruction':stage['instruction'],'actual':copy.deepcopy(actual),'expected':stage['expected'],'acceptance_checked':stage['has_expected'],'passed':accepted,'operation_checks':result['trace']})
 if not accepted:goal.update(status='acceptance-failed',error='Stage output differs from the supplied expected value');return True
 goal['value']=copy.deepcopy(actual);goal['cursor']+=1
 if goal['cursor']==len(goal['stages']):
  steps=[s for stage in goal['stages'] for s in stage['steps']]
  # Recheck the entire composed workflow before making its result current.
  checked=pipeline(copy.deepcopy(goal['input']),steps)
  if not equivalent(checked['result'],goal['value']):goal.update(status='failed',error='Composed replay differs from staged output');return True
  receipt=work.commit('Native goal: '+goal['name'],goal['value'],steps,checked)
  goal.update(status='complete',committed=True,receipt_id=receipt['receipt']['id']);work.state['focus_kind']='goal'
 return True

def summary(goal):
 if not goal:return 'No native goal is retained. Use work toward: with an input and ordered stages.'
 text='**'+goal['name']+'**\n\n'+goal['status']+': '+str(goal['cursor'])+'/'+str(len(goal['stages']))+' stages completed.'
 if goal['status']=='running':text+=' Next: '+goal['stages'][goal['cursor']]['instruction']+'. Intermediate results remain private until the whole goal passes.'
 if goal.get('error'):text+=' '+goal['error']+'. Previous completed work is retained.'
 if goal['committed']:text+=' The complete workflow was replayed and its result committed.'
 return text
