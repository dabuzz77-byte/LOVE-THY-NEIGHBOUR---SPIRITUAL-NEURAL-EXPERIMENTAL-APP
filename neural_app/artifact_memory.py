"""Source-linked retrieval and versioned native procedure evidence."""
import copy,hashlib,json,re,time

def version(procedure):
 return hashlib.sha256(json.dumps({'steps':procedure['steps'],'source_output_sha256':procedure.get('source_output_sha256')},sort_keys=True,ensure_ascii=True).encode()).hexdigest()

def check_workflow(state,name,body):
 from .native_synthesis import bounded
 from .reasoning_engine import pipeline
 from .workflow_contracts import equivalent
 if not isinstance(body,dict) or 'input' not in body or 'expected' not in body:raise ValueError('Provide input and explicit expected output')
 row=state.get('workflow_library',{}).get(name)
 if row is None:raise ValueError('Unknown saved workflow')
 bounded(body['input']);bounded(body['expected'])
 if row.get('active') is False:raise ValueError('Workflow is revoked. Supply a corrected procedure with separate validation before reusing it.')
 try:actual=pipeline(copy.deepcopy(body['input']),row['steps'])['result'];passed=equivalent(actual,body['expected']);error=None
 except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:actual=None;passed=False;error=str(exc)[:200]
 evidence={'input_sha256':hashlib.sha256(json.dumps(body['input'],sort_keys=True,ensure_ascii=True).encode()).hexdigest(),'expected':copy.deepcopy(body['expected']),'actual':actual,'passed':passed,'error':error,'source':'explicit supplied expected-output check','time':time.time(),'version':version(row)}
 row['latest_check']=evidence;row['active']=passed
 if not passed:row['revocation']={'time':time.time(),'reason':'explicit counterexample','version':version(row)}
 return copy.deepcopy(evidence)

def index(state,memories=None):
 rows=[]
 opened=state.get('open_reasoning')
 if opened:rows.append({'kind':'open-reasoning','name':opened['question'][:160],'status':opened['status'],'summary':opened['kind']+'; '+opened['next_question'],'source':'explicit user-supplied reasoning workspace '+opened['id'],'scope':opened['scope']})
 for episode in state.get('general_reasoning_history',[])[-8:]:
  result=episode['result'];spec=episode['input']
  rows.append({'kind':'general-reasoning','name':str(spec.get('question',spec.get('query',result['mode'])))[:160],'status':result.get('status','complete'),'summary':result['mode']+'; '+str(result.get('next_step','Review assumptions')),'source':'retained explicit assumptions and bounded reasoning result '+result['input_sha256'],'scope':result.get('scope','Assumption-dependent model result; no external fact established')})
 for name,p in state.get('workflow_library',{}).items():rows.append({'kind':'workflow','name':name,'status':'active' if p.get('active',True) else 'revoked','version':version(p),'summary':' → '.join(s['op'] for s in p['steps']),'scope':p.get('scope'),'source':'saved native workflow','checks':len(p.get('validation',[])),'latest_check':{k:v for k,v in (p.get('latest_check') or {}).items() if k in ('passed','error','version','input_sha256','source')}})
 for name,r in state.get('rules',{}).items():rows.append({'kind':'numeric-rule','name':name,'status':'active' if r.get('active') else 'revoked','summary':'degree '+str(r.get('degree')),'scope':r.get('scope'),'source':'separately validated numeric examples'})
 for name,r in state.get('inquiries',{}).items():rows.append({'kind':'inquiry','name':name,'status':r['phase'],'summary':str(len(r['survivors']))+' candidate explanations; '+str(len(r['observations']))+' observations','source':'supplied observations and bounded candidate search','scope':r.get('scope')})
 for name,value in (memories or {}).items():rows.append({'kind':'user-memory','name':name,'status':'user-statement','summary':str(value)[:1000],'source':'explicit user memory','scope':'Saved statement, not independently verified'})
 goal=state.get('active_goal')
 if goal:rows.append({'kind':'goal','name':goal['name'],'status':goal['status'],'summary':str(goal['cursor'])+'/'+str(len(goal['stages']))+' stages','source':'actual native goal trace','scope':'Only committed results completed the full replay'})
 for r in state.get('relevant_experiments',[]):rows.append({'kind':'experiment','name':r['question'],'status':'failed' if r['revoked'] else 'passed','summary':r['workflow']+': '+str(r['passed'])+'/'+str(r['total'])+' supplied cases; baseline '+str(r['baseline_passed']),'source':r['source'],'scope':r['scope']})
 mission=state.get('sphere_mission')
 if mission:rows.append({'kind':'sphere-task','name':mission['name'],'status':mission['status'],'summary':'selected '+str(mission.get('selected'))+'; '+str(len(mission['trace']))+' role records; committed '+str(mission['committed']),'source':'actual choice/prediction/action/verification records','scope':'Bounded task operations and explicit expected outcomes'})
 return rows[:192]

def search(state,query,memories=None):
 terms=set(re.findall(r'\w+',query.casefold()))-{'the','a','my','about','and','of','what','do','you','know'}
 rows=index(state,memories);ranked=[]
 for row in rows:
  words=set(re.findall(r'\w+',row['name'].casefold()+' '+row.get('summary','').casefold()+' '+row['kind']))
  overlap=terms&words
  if overlap:ranked.append({**row,'matched_terms':sorted(overlap),'relevance':len(overlap)/max(1,len(terms))})
 return sorted(ranked,key=lambda r:(-r['relevance'],r['kind'],r['name']))[:12]
