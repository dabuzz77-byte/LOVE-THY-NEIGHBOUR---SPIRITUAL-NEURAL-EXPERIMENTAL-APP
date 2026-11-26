"""Explain the latest recorded assessment without rerunning any action."""
import json

def reflect(text,history):
 if text.casefold().strip().rstrip('?') not in ('what evidence supports this','what remains uncertain','what are the limitations','how accurate were those predictions'):return None
 if not history:return {'status':'needs-input','question':'Which result should I review?','action_repeated':False}
 try:body=history[-1].get('work_result') or json.loads(str(history[-1].get('answer','')))
 except (TypeError,ValueError):body=None
 if not isinstance(body,dict):return {'status':'needs-input','question':'The latest answer has no structured evidence record. Which result do you mean?','action_repeated':False}
 if isinstance(body.get('claims'),list) and 'comparisons' in body:
  return {'answer':'These are the supplied source attributions and unresolved comparison questions. They have not been independently authenticated.','evidence':[{'claim':r['claim'],'source':r['source'],'missing_context':r['missing_context']} for r in body['claims']],'open_questions':body['open_questions'],'scope':body['scope'],'action_repeated':False,'model_calls':0}
 if 'metrics' in body and 'evidence_status' in body:
  return {'answer':'Accuracy was measured against the supplied outcomes and declared baseline. This does not establish causation or future performance.','metrics':body['metrics'],'calibration_bins':body.get('calibration_bins',[]),'evidence_status':body['evidence_status'],'scope':body['scope'],'action_repeated':False,'model_calls':0}
 return {'answer':'The recorded scope is shown below. I have not rerun the task or independently expanded its verification.','scope':body.get('scope','No explicit verification scope was recorded.'),'verified':body.get('verified'),'action_repeated':False,'model_calls':0}
