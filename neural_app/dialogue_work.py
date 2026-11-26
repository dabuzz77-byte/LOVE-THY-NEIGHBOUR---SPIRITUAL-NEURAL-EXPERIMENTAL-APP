"""Typed dialogue continuity for pure results. Never replays host or network actions."""
import copy,json,re,time

def numeric_operation(instruction):
 match=re.fullmatch(r'(multiply(?: (?:that|it|the result))? by|divide(?: (?:that|it|the result))? by|add|subtract)\s+(-?\d+(?:\.\d+)?)',instruction,re.I)
 if not match:return None
 verb=match[1].lower();operand=float(match[2]);op='scale' if verb.startswith('multiply') else 'divide' if verb.startswith('divide') else 'add'
 return {'op':op,'value':-operand if verb=='subtract' else operand}

def previous_result(history):
 if not history:return None,None
 row=history[-1]
 try:body=row.get('work_result') or json.loads(str(row.get('answer','')))
 except (ValueError,TypeError):return None,None
 if type(body) in (int,float) and row.get('native_skill')=='arithmetic':return {'result':body,'trace':[]},row
 if isinstance(body,dict) and body.get('status')=='complete' and 'value' in body and isinstance(body.get('function_batch'),dict):return {'result':copy.deepcopy(body['value']),'trace':[]},row
 if isinstance(body,dict) and body.get('status')=='complete' and 'value' in body and isinstance(body.get('function_call'),dict):return {'result':copy.deepcopy(body['value']),'trace':[]},row
 if isinstance(body,dict) and body.get('status')=='complete' and 'value' in body and isinstance(body.get('code'),dict) and body['code'].get('checks',{}).get('all_passed') is True:
  return {'result':copy.deepcopy(body['value']),'trace':[]},row
 if isinstance(body,dict) and body.get('action_repeated') is False and 'steps' in body and 'result' in body:
  return {'result':body['result'],'trace':body['steps'],**({'input':body['input']} if 'input' in body else {})},row
 if isinstance(body,dict) and 'result' in body and (body.get('trace') or body.get('reused_workflow')):return body,row
 return None,None

def resolve(text,history,engine):
 lower=text.casefold().strip();previous,row=previous_result(history)
 exact_follow=re.fullmatch(r'(?:now|then) (multiply by|divide by|add|subtract) (-?\d+(?:\.\d+)?)',text,re.I)
 if exact_follow and history:
  try:exact_previous=history[-1].get('work_result') or json.loads(str(history[-1].get('answer','')))
  except ValueError:exact_previous={}
  if isinstance(exact_previous,dict) and isinstance(exact_previous.get('exact_result'),str):
   from .exact_numbers import calculate
   operator={'multiply by':'*','divide by':'/','add':'+','subtract':'-'}[exact_follow[1].lower()]
   return {**calculate('('+exact_previous['exact_result']+')'+operator+exact_follow[2]),'context_used':'exact rational result of the immediately preceding answer'}
 if lower in ('why this choice','why this choice?') and history:
  try:choice=history[-1].get('work_result') or json.loads(str(history[-1].get('answer','')))
  except ValueError:choice={}
  if isinstance(choice,dict) and 'scenario_ranges' in choice:return {'answer':'The robust choices win at every tested root-box corner. The maximin choices have the highest worst-case score. These answer different questions; neither is a probability of success.','robust_winning_indices':choice['robust_winning_indices'],'maximin_selected_indices':choice['maximin_selected_indices'],'scenario_ranges':choice['scenario_ranges'],'corners_examined':choice['corners_examined'],'scope':choice['scope'],'action_repeated':False,'model_calls':0}
  if isinstance(choice,dict) and 'selected_under_supplied_weights' in choice:return {**copy.deepcopy(choice),'answer':'The selected alternatives have the largest weighted change from the supplied baseline. Each contribution is its outcome change multiplied by your declared weight.','action_repeated':False}
 select=re.fullmatch(r'(?:use|select) alternative (.+)',text,re.I)
 if select:
  try:body=(history[-1].get('work_result') or json.loads(str(history[-1].get('answer','')))) if history else {}
  except ValueError:body={}
  choices=body.get('alternatives',[]) if isinstance(body,dict) else [];matches=[v for v in choices if str(v.get('name','')).casefold()==select[1].strip().casefold()]
  if len(matches)!=1 or not matches[0].get('verified'):return {'status':'needs-input','question':'Choose one uniquely named, verified alternative from the latest comparison.','executed':False}
  chosen=copy.deepcopy(matches[0]);chosen['selected_alternative']=chosen.pop('name');chosen['context_used']='retained checked result; no operation replayed';return chosen
 replacement=re.fullmatch(r'(?:replace|change) (?:the )?last (?:data )?step (?:with|to) (.+)',text,re.I)
 if replacement:
  if previous is None or not previous.get('trace') or 'input' not in previous:return {'status':'needs-input','question':'No recorded pure data step is available to replace.','executed':False}
  instruction=replacement[1]
  if ':' in instruction:return {'status':'needs-input','question':'Give only the replacement operation; the retained input will be used.','executed':False}
  prefix=copy.deepcopy(previous['trace'][:-1]);value=prefix[-1]['result'] if prefix else previous['input'];raw=json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value
  numeric=numeric_operation(instruction)
  if numeric:
   from .reasoning_engine import pipeline
   result=pipeline(value,[numeric])
  else:result=engine.plan_and_run(instruction+': '+raw)
  if result is None:return {'status':'needs-input','question':'Which supported data operation should replace the last step?','executed':False}
  if result.get('status')=='needs-input':return result
  combined=prefix+result['trace']
  if len(combined)>12:raise ValueError('The revised workflow exceeds 12 steps')
  for i,entry in enumerate(combined):entry['step']=i+1
  result.update(input=previous['input'],trace=combined,replaced_step=previous['trace'][-1]['operation'],context_used='replaced the final pure transformation on its retained input');return result
 if lower in ('what changed','what changed?') and previous is not None and previous.get('trace') and 'input' in previous:
  before=previous['input'];after=previous['result'];change={'input_type':type(before).__name__,'output_type':type(after).__name__}
  if type(before) in (int,float) and type(after) in (int,float):change['numeric_difference']=after-before
  if isinstance(before,(str,list,dict)) and isinstance(after,(str,list,dict)):change['size_difference']=len(after)-len(before)
  return {**copy.deepcopy(previous),'change_summary':change,'answer':'Compared the retained input with the checked output.','action_repeated':False}
 if lower in ('undo last data step','undo the last data step'):
  if previous is None or not previous.get('trace') or 'input' not in previous:return {'status':'needs-input','question':'No reversible data workflow is available in the latest answer.','executed':False}
  trace=previous['trace'][:-1];value=copy.deepcopy(trace[-1]['result'] if trace else previous['input'])
  return {'result':value,'input':previous['input'],'trace':trace,'reused_workflow':True,'verified':True,'data_step_undone':previous['trace'][-1]['operation'],'scope':'Restored a retained pure data value, not a host or network action','model_calls':0}
 if lower in ('what data did you use','what data did you use?','which steps did you use','which steps did you use?'):
  if previous is None:return {'status':'needs-input','question':'Which completed workflow do you mean?','executed':False}
  return {'source_request':row.get('request'),'steps':previous.get('trace',[]),'result':previous['result'],**({'input':previous['input']} if 'input' in previous else {}),'answer':'These are the recorded operations for the most recent workflow.','action_repeated':False}
 same=re.fullmatch(r'(?:do (?:the )?same|repeat (?:that|the workflow)) (?:with|on):\s*([\s\S]+)',text,re.I)
 follow=re.fullmatch(r'(?:now|then)\s+([\s\S]+)',text,re.I)
 if not same and not follow:return None
 if previous is None:return {'status':'needs-input','question':'What data or completed workflow should I use? The latest answer was not a reusable data result.','executed':False}
 from .reasoning_engine import pipeline
 if same:
  raw=same[1]
  try:value=json.loads(raw)
  except ValueError:value=raw
  steps=[{'op':r['operation'],**r.get('parameters',{})} for r in previous.get('trace',[])]
  if not steps:return {'status':'needs-input','question':'No reusable operation sequence was recorded for that result.','executed':False}
  result=pipeline(value,steps);result['context_used']='operations from the immediately preceding pure workflow';result['source_request']=row.get('request');return result
 instruction=follow[1].strip()
 numeric=numeric_operation(instruction)
 if numeric and type(previous['result']) in (int,float):
  result=pipeline(previous['result'],[numeric]);result['context_used']='numeric result of the immediately preceding answer';result['source_request']=row.get('request');return result
 if ':' in instruction:return {'status':'needs-input','question':'For a follow-up using the previous result, give the next operation without replacing its data. Or send a new explicit request.','executed':False}
 # Only compile native pure transformations; the previous value is serialized as data.
 value=previous['result'];raw=json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value
 from .native_work import parse_steps
 steps=parse_steps(instruction)
 result=pipeline(copy.deepcopy(value),steps) if steps else engine.plan_and_run(instruction+': '+raw)
 if result is None:return {'status':'needs-input','question':'Which supported data transformation should I apply to that result?','executed':False}
 result['context_used']='result of the immediately preceding pure workflow';result['source_request']=row.get('request');return result
