"""Question-linked procedure experiments with explicit outcomes and a baseline."""
import copy,json,time
from .native_synthesis import bounded
from .workflow_contracts import equivalent
from .reasoning_engine import pipeline
from .artifact_memory import version,check_workflow

def run(state,body):
 if not isinstance(body,dict):raise ValueError('Provide workflow, question and cases')
 name=str(body.get('workflow','')).strip().casefold();question=body.get('question');cases=body.get('cases');procedure=state.get('workflow_library',{}).get(name)
 if not procedure or procedure.get('active') is False:raise ValueError('Choose an active saved workflow')
 if not isinstance(question,str) or not question.strip() or len(question)>500:raise ValueError('Provide a specific question under 500 characters')
 if not isinstance(cases,list) or not 2<=len(cases)<=20:raise ValueError('Provide 2–20 distinct input/expected cases')
 for case in cases:
  if not isinstance(case,dict) or 'input' not in case or 'expected' not in case:raise ValueError('Each case needs input and explicit expected output')
  bounded(case['input']);bounded(case['expected'])
 if len(json.dumps(cases,ensure_ascii=True))>32768:raise ValueError('Use a case set under 32 KB')
 if len({json.dumps(r['input'],sort_keys=True,ensure_ascii=True) for r in cases})!=len(cases):raise ValueError('Experiment inputs must be distinct')
 started=time.perf_counter();results=[]
 for case in cases:
  try:actual=pipeline(copy.deepcopy(case['input']),procedure['steps'])['result'];passed=equivalent(actual,case['expected']);error=None
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:actual=None;passed=False;error=str(exc)[:200]
  results.append({'actual':actual,'expected':copy.deepcopy(case['expected']),'passed':passed,'baseline_identity_passed':equivalent(case['input'],case['expected']),'error':error})
 failed=next((i for i,r in enumerate(results) if not r['passed']),None)
 if failed is not None:check_workflow(state,name,cases[failed])
 report={'question':question.strip(),'workflow':name,'procedure_version':version(procedure),'kind':'explicit-outcome-procedure-experiment','source':'supplied case protocol, copied native execution and explicit expected outputs','cases':results,'passed':sum(r['passed'] for r in results),'total':len(results),'baseline_passed':sum(r['baseline_identity_passed'] for r in results),'revoked':failed is not None,'elapsed_ms':round((time.perf_counter()-started)*1000,3),'time':time.time(),'model_calls':0,'scope':'Compares a fixed procedure with unchanged input on these supplied cases. No world outcome or unseen generalisation is established.'}
 state['relevant_experiments']=(state.get('relevant_experiments',[])+[report])[-8:]
 return report
