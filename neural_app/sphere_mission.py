"""Outcome-driven role pipeline for choice, prediction, action and consequence spheres."""
import copy,hashlib,json,time,math
from .artifact_memory import version
from .native_synthesis import bounded
from .reasoning_engine import pipeline
from .workflow_contracts import equivalent

PHASES=('compare','validate','predict','act','verify','retain')
def create(body,state):
 if not isinstance(body,dict):raise ValueError('Provide a sphere task object')
 name=body.get('name');candidates=body.get('workflows');train=body.get('examples');validation=body.get('validation')
 if not isinstance(name,str) or not name.strip() or len(name)>100:raise ValueError('Use a short task name')
 if not isinstance(candidates,list) or not 1<=len(candidates)<=12 or any(not isinstance(n,str) for n in candidates):raise ValueError('Choose 1–12 saved workflow names')
 if not isinstance(train,list) or not 2<=len(train)<=8 or not isinstance(validation,list) or not 2<=len(validation)<=8:raise ValueError('Supply two or more training and separate validation cases')
 for row in train+validation:
  if not isinstance(row,dict) or 'input' not in row or 'expected' not in row:raise ValueError('Cases require input and expected output')
  bounded(row['input']);bounded(row['expected'])
 if len({json.dumps(r['input'],sort_keys=True) for r in train+validation})!=len(train+validation):raise ValueError('Training and validation inputs must differ')
 if 'input' not in body or 'expected' not in body:raise ValueError('Provide the actual action input and expected result')
 bounded(body['input']);bounded(body['expected'])
 if len(json.dumps(body,ensure_ascii=True))>40000:raise ValueError('Task exceeds 40 KB')
 choices=[]
 for n in dict.fromkeys(candidates):
  key=n.strip().casefold();p=state.get('workflow_library',{}).get(key)
  if not p or p.get('active') is False:raise ValueError('Workflow is missing or revoked: '+key)
  choices.append({'name':key,'version':version(p),'steps':copy.deepcopy(p['steps'])})
 return {'name':name.strip(),'phase':'compare','status':'running','choices':choices,'examples':copy.deepcopy(train),'validation':copy.deepcopy(validation),'input':copy.deepcopy(body['input']),'expected':copy.deepcopy(body['expected']),'trace':[],'sequence':0,'created':time.time(),'committed':False,'model_calls':0}

def run_cases(steps,cases):
 rows=[]
 for case in cases:
  try:actual=pipeline(copy.deepcopy(case['input']),steps)['result'];ok=equivalent(actual,case['expected']);error=None
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:actual=None;ok=False;error=str(exc)[:180]
  rows.append({'passed':ok,'actual_preview':str(actual)[:256],'expected_preview':str(case['expected'])[:256],'actual_sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,ensure_ascii=True).encode()).hexdigest(),'error':error})
 return rows

def advance(m,work):
 if m['status']!='running':return False
 phase=m['phase'];record={'phase':phase,'time':time.time()}
 try:
  for choice in m['choices']:
   p=work.state.get('workflow_library',{}).get(choice['name'])
   if not p or p.get('active') is False or version(p)!=choice['version']:raise ValueError('Candidate dependency changed or was revoked: '+choice['name'])
  if phase=='compare':
   comparisons=[{'name':c['name'],'steps':c['steps'],'checks':run_cases(c['steps'],m['examples'])} for c in m['choices']]
   eligible=[r for r in comparisons if all(c['passed'] for c in r['checks'])]
   if not eligible:raise ValueError('No candidate satisfies the training cases')
   selected=min(eligible,key=lambda r:(len(r['steps']),r['name']));m['selected']=selected['name'];record.update(alternatives=comparisons,selected=selected['name'],basis='All training cases pass; shortest procedure then name. Validation is not used for selection.')
  else:
   selected=next(c for c in m['choices'] if c['name']==m['selected']);steps=selected['steps']
   if phase=='validate':
    checks=run_cases(steps,m['validation']);record['checks']=checks
    if not all(r['passed'] for r in checks):raise ValueError('Chosen candidate failed untouched validation. No replacement selected from those answers.')
   elif phase=='predict':
    m['prediction']=pipeline(copy.deepcopy(m['input']),steps)['result'];m['prediction_at']=time.time();record['prediction']=copy.deepcopy(m['prediction']);record['scope']='Copied native dry run before action; not an independently measured world prediction'
   elif phase=='act':
    m['action']=pipeline(copy.deepcopy(m['input']),steps);m['action_at']=time.time();record.update(actual=copy.deepcopy(m['action']['result']),operation_checks=m['action']['trace'],scope='Actual registered pure-data computation; no host or network side effect')
   elif phase=='verify':
    actual=m['action']['result'];checks={'matches_prediction':equivalent(actual,m['prediction']),'matches_expected':equivalent(actual,m['expected']),'operations_verified':m['action']['verified'],'prediction_recorded_before_action':m['prediction_at']<=m['action_at']};record['checks']=checks
    if not checks['matches_expected']:
     from .artifact_memory import check_workflow
     check_workflow(work.state,m['selected'],{'input':m['input'],'expected':m['expected']})
    if not all(checks.values()):raise ValueError('Actual result failed its prediction or explicit expected-output check')
   elif phase=='retain':
    reply=work.commit('Sphere task: '+m['name'],m['action']['result'],steps,m['action']);m.update(committed=True,receipt_id=reply['receipt']['id']);work.state['focus_kind']='sphere-mission';record.update(receipt_id=m['receipt_id'],retained_procedure=m['selected'])
  record['passed']=True;m['trace'].append(record);m['sequence']+=1
  if phase=='retain':m['status']='complete'
  else:m['phase']=PHASES[PHASES.index(phase)+1]
 except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:
  record.update(passed=False,error=str(exc)[:400]);m['trace'].append(record);m.update(status='failed',error=record['error']);m['sequence']+=1
 return True

def summary(m):
 if not m:return None
 return {k:copy.deepcopy(m.get(k)) for k in ('name','phase','status','selected','prediction','trace','sequence','committed','receipt_id','error','model_calls')}

def frames(m):
 if not m:return {}
 roles={'choice-study':['compare','validate'],'action-study':['act'],'consequence-study':['predict','verify'],'choice-action-consequence':list(PHASES)};out={}
 for lane,phases in roles.items():
  rows=[r for r in m['trace'] if r['phase'] in phases];points=[]
  for i,phase in enumerate(phases):
   row=next((r for r in rows if r['phase']==phase),None);state=1 if row and row['passed'] else -1 if row else 0
   points.append({'id':'mission:'+lane+':'+phase,'point':[.85*math.cos(i*2.399),.2*i,.85*math.sin(i*2.399)],'phase':(state+1)/2,'selected':bool(row),'symbol':str(state),'source':'sphere-mission','expression_type':'executed-role-check','value_preview':phase+' · '+('passed' if state==1 else 'failed' if state==-1 else 'pending'),'record':copy.deepcopy(row),'task':m['name']})
  out[lane]={'sequence':m['sequence'],'particles':points,'thought_trace':rows,'role_task':summary(m),'retained_sources':len(m['choices']),'represented_values':len(points),'goal':m['name'],'scope':'Actual bounded task-role pipeline; phase nodes show recorded checks, not hypothetical world actions'}
 return out
