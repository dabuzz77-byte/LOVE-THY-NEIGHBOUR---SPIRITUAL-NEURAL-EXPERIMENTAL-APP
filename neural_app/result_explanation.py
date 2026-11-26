"""Plain explanations of recorded results; no fresh inference or action replay."""
import json

def explain_attempt(record):
 if not isinstance(record,dict) or record.get('committed') is not False:return None
 if record.get('last_attempt_summary'):return {**record,'action_repeated':False,'model_calls':0}
 lines=['The latest task attempt stopped at '+str(record.get('failed_task','an unresolved task'))+'. Its outputs were not committed; the previous completed result is retained.']
 if not record.get('outputs') and record.get('answer'):lines.append(record['answer'][:600])
 for output in record.get('outputs',[])[-1:]:
  validation=output.get('validation')
  if validation:
   lines+=['Fresh validation: '+str(validation['passed'])+'/'+str(validation['total'])+' native cases passed.']
   for case in [r for r in validation.get('cases',[]) if not r['passed']][:3]:lines+=['Case '+str(case['case'])+': '+(case.get('error') or 'expected '+str(case.get('expected'))[:200]+', obtained '+str(case.get('actual'))[:200])+'.']
  elif output.get('answer'):lines.append(output['answer'][:600])
 return {'status':record.get('status','blocked'),'answer':'\n\n'.join(lines),'committed':False,'failed_task':record.get('failed_task'),'last_attempt_summary':True,'action_repeated':False,'model_calls':0}

def explain(report):
 mode=report.get('mode');status=report.get('status','unknown');lines=[]
 if mode=='deduction':
  descriptions={'entailed':'The query follows from the supplied premises.','refuted':'The negation of the query follows from the supplied premises.','contingent':'The premises permit both the query and its negation.','inconsistent-premises':'The supplied premises conflict; they do not certify a conclusion.'}
  lines=[descriptions.get(status,'The bounded logical search did not settle the query.')]
  if report.get('counterexample_world') is not None:lines+=['A recorded counterexample is '+json.dumps(report['counterexample_world'],ensure_ascii=False)+'.']
 elif mode=='equations':
  values=report.get('determined_values',{});lines=['The equations determine: '+(', '.join(k+' = '+str(v) for k,v in values.items()) or 'no unique numeric values')+'.']
  if report.get('free_variables'):lines+=['Still free: '+', '.join(report['free_variables'])+'.']
  if report.get('certificate'):lines=['The equations conflict. Their checked combination gives 0 = '+str(report['certificate']['zero_equals'])+'.']
 elif mode in ('units','written_quantities'):
  lines=[report['exact_value']+' '+report['unit']+'. The dimensions were checked before conversion.']
  if mode=='written_quantities':lines += [report['formula_origin'],'Used quantities: '+', '.join(report['used_quantities'])+'.','Unused quantities: '+(', '.join(report['unused_quantities']) or 'none')+'.']
 elif mode in ('reading','relations'):
  answers=[', '.join(row['bindings'].values()) or 'the queried statement' for row in report.get('answers',[])];lines=['Under the supplied statements, the result is '+status+'.']
  if answers:lines+=['Supported: '+ '; '.join(answers)+'.']
  if report.get('counter_supporting_fact_ids'):lines+=['Explicit counter-support is also recorded.']
  if report.get('conflicts'):lines+=['Some supplied statements conflict; review the proof and counter-proof together.']
 elif mode=='robustness':lines=['The assumption audit is '+status+'.','Changed variants: '+(', '.join(report['changed_variants']) or 'none among the tested variants')+'.','Unresolved variants: '+(', '.join(report['unresolved_variants']) or 'none')+'.']
 elif mode=='causal_probability':
  lines=['The prior outcome probability is '+report['prior_outcome_probability']+'.','After the supplied observations it is '+str(report['posterior_outcome_probability'])+'.'] if status=='updated' else ['The evidence is impossible under the supplied model; no posterior was calculated.']
  for row in report.get('interventions',[]):
   observed=row['observational_probability_given_same_setting'];comparison=str(observed) if observed is not None else 'no defined probability, because that observation is impossible in this model'
   lines+=[row['name']+': intervening gives '+row['counterfactual_probability_given_evidence']+'; merely observing the same setting gives '+comparison+'.']
 elif mode=='counterfactual':
  lines=['The baseline modeled outcome is '+str(report['baseline_outcome'])+'.']
  if 'answer_to_question' in report:lines+=['The answer under these assumptions is '+('yes' if report['answer_to_question'] else 'no')+'.']
  lines += [row['name']+' gives '+str(row['outcome'])+'.' for row in report.get('interventions',[])]
 elif mode=='decision':lines=['Complete undominated options: '+(', '.join(report.get('pareto_frontier',[])) or 'none established')+'.','Robustly preferred under the declared criteria: '+(', '.join(report.get('robust_best_under_declared_criteria',[])) or 'no single preference established')+'.']
 elif mode=='scenarios':lines=['Smallest worst-case regret: '+', '.join(report.get('minimax_regret_options',[]))+'.','Best expected outcome under supplied probabilities: '+(', '.join(report.get('expected_outcome_options',[])) or 'not established')+'.']
 else:lines=['The recorded '+str(mode)+' calculation ended with status '+status+'.']
 lines += [report.get('next_step','Review the supplied inputs.'),report.get('scope','')]
 return {'status':status,'answer':'\n\n'.join(lines),'action_repeated':False,'model_calls':0}
