"""Checked practical arithmetic, current-work summaries and pure function use."""
import copy,json,re
from fractions import Fraction

NUMBER=r'([+-]?\d+(?:\.\d+)?)'

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!')
 from .action_review import respond as action_review_respond
 action_review=action_review_respond(text,work)
 if action_review is not None:return action_review
 from .goal_workspace import respond as goal_respond
 goal=goal_respond(text,work)
 if goal is not None:return goal
 from .shared_controller import respond as controller_respond
 controller=controller_respond(text,work)
 if controller is not None:return controller
 from .proportional_reasoning import respond as proportion_respond
 proportion=proportion_respond(text,work)
 if proportion is not None:return proportion
 from .category_reasoning import respond as category_respond
 category=category_respond(text,work)
 if category is not None:return category
 from .reusable_tasks import respond as tasks_respond
 tasks=tasks_respond(text,work)
 if tasks is not None:return tasks
 from .table_work import respond as table_respond
 table=table_respond(text,work)
 if table is not None:return table
 from .checked_function_library import respond as library_respond
 library=library_respond(text,work)
 if library is not None:return library
 from .calculation_comparison import respond as comparison_respond
 comparison=comparison_respond(text,work)
 if comparison is not None:return comparison
 from .exact_work import respond as exact_respond
 exact=exact_respond(text,work)
 if exact is not None:return exact
 from .function_batch_work import respond as batch_respond
 batch=batch_respond(text,work)
 if batch is not None:return batch
 if key in ('summarize current work','summarise current work','where are we'):
  state=work.state;focus=state.get('focus_kind','none');lines=['Current focus: '+focus+'.']
  if focus=='general-reasoning':
   result=state.get('general_reasoning_result',{});lines+=['Reasoning mode: '+str(result.get('mode','unknown'))+'.','Recorded status: '+str(result.get('status','unknown'))+'.']
   if result.get('next_step'):lines.append(result['next_step'])
  if focus=='code':
   code=state.get('last_generated_code',{});lines.append('Function: '+str(code.get('function','none'))+'.')
   lines.append('Recorded checks: '+('passing' if code.get('usable',code.get('checks',{}).get('all_passed',False)) else 'not passing')+'.')
  if focus=='category-reasoning' and state.get('category_reasoning'):lines.append('Category conclusion: '+state['category_reasoning']['status']+'. Ask explain category reasoning for model evidence.')
  if focus=='table' and state.get('study_table'):lines.append('Retained table: '+str(len(state['study_table']['rows']))+' source rows. Latest result: '+state.get('table_result',{}).get('exact_result','not queried')+'.')
  if focus=='calculation-comparison' and state.get('calculation_comparison'):lines.append('Selected alternatives: '+', '.join(state['calculation_comparison']['selected'])+'.')
  if state.get('saved_task_bundles'):lines.append('Saved tasks: '+', '.join(state['saved_task_bundles'])+'.')
  if state.get('last_saved_task_attempt'):lines.append('Latest saved-task attempt: '+state['last_saved_task_attempt']['name']+' · '+state['last_saved_task_attempt']['status']+'.')
  if state.get('checked_functions'):lines.append('Saved functions: '+', '.join(state['checked_functions'])+'.')
  if focus=='exact-work' and state.get('exact_work'):lines.append('Exact retained result: '+state['exact_work']['exact_result']+'.')
  if state.get('reasoning_workspaces'):lines.append('Saved reasoning: '+', '.join(state['reasoning_workspaces'])+'.')
  if focus=='function-batch' and state.get('last_function_batch'):lines.append('Completed function batch: '+str(len(state['last_function_batch']['rows']))+' inputs.')
  if state.get('last_function_call'):lines.append('Latest pure function result: '+json.dumps(state['last_function_call']['value'],ensure_ascii=False)+'.')
  return {'status':'complete','answer':'\n\n'.join(lines),'action_repeated':False,'model_calls':0}
 if key.startswith('run this function on:'):
  from .function_testing import FunctionTest,data_budget
  from .native_work import digest
  code=work.state.get('last_generated_code')
  if not code or not code.get('usable',code.get('checks',{}).get('all_passed',False)) or code.get('counterexample_found'):return {'status':'needs-input','answer':'Generate a function with passing retained checks before invoking it.','model_calls':0}
  if digest(code['source']) in work.state.get('invalidated_function_sources',[]):raise ValueError('This source has an unresolved failed check; generate and check a corrected function')
  if code.get('source_sha256')!=digest(code['source']):raise ValueError('Generated source differs from its checked receipt; regenerate and test it')
  args=json.loads(text.split(':',1)[1])
  if not isinstance(args,list) or len(json.dumps(args,allow_nan=False))>8192:raise ValueError('Supply a JSON argument list up to 8 KB')
  data_budget(args);runner=FunctionTest(code['source']);value=runner.invoke(code['function'],copy.deepcopy(args));data_budget(value)
  receipt={'function':code['function'],'source_sha256':digest(code['source']),'args_sha256':digest(args),'value':copy.deepcopy(value),'value_sha256':digest(value),'steps':runner.steps}
  work.state['previous']=copy.deepcopy(work.state.get('last'));work.state['last']=copy.deepcopy(value);work.state['has_last']=True;work.state['last_function_call']=receipt;work.state['focus_kind']='code'
  return {'status':'complete','answer':json.dumps(value,ensure_ascii=False),'value':value,'function_call':receipt,'model_calls':0,'host_access':False}
 patterns=[(rf'(?:what is )?{NUMBER}% of {NUMBER}',lambda a,b:a*b/100,'percent of'),(rf'(?:increase|raise) {NUMBER} by {NUMBER}%',lambda a,b:a*(1+b/100),'percentage increase'),(rf'(?:decrease|reduce) {NUMBER} by {NUMBER}%',lambda a,b:a*(1-b/100),'percentage decrease'),(rf'(?:what is the )?percentage change from {NUMBER} to {NUMBER}',lambda a,b:(b-a)/abs(a)*100,'percentage change')]
 for pattern,operation,label in patterns:
  match=re.fullmatch(pattern,key)
  if not match:continue
  a,b=map(Fraction,match.groups())
  if label=='percentage change' and a==0:raise ValueError('Percentage change from zero has no finite baseline percentage')
  value=operation(a,b);exact=str(value);display=str(value.numerator) if value.denominator==1 else exact
  from .exact_work import finish
  result=finish(work,value,[{'instruction':key,'exact':exact}],text)
  return {**result,'answer':display+('%' if label=='percentage change' else ''),'calculation':label,'inputs':[str(a),str(b)],'scope':'Exact arithmetic on the supplied numbers; percentages are relative, not percentage-point differences.'}
 return None
