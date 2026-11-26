"""Hypothetical system-wide communication review; no network or execution adapter."""
import copy,json
from .decision_framework import operation_review,SYSTEM_REVIEW

def review(body):
 if not isinstance(body,dict) or len(json.dumps(body))>24000:raise ValueError('Provide a bounded hypothetical case object')
 extent=body.get('extent','combined');description=body.get('description');nodes=body.get('nodes',[]);record=body.get('operation_record',{})
 if extent not in ('local','external','combined') or not isinstance(description,str) or not 1<=len(description)<=4000:raise ValueError('Describe the hypothetical case and choose local, external or combined scope')
 if not isinstance(nodes,list) or len(nodes)>32:raise ValueError('Use up to 32 declared dependency nodes')
 allowed={'local-device','external-device','service','account','data','person','essential-service'}
 for node in nodes:
  if not isinstance(node,dict) or node.get('kind') not in allowed or not isinstance(node.get('name'),str) or not 1<=len(node['name'])<=120:raise ValueError('Each declared node needs a short name and supported kind')
 checked=operation_review(record)
 return {'hypothetical':True,'extent':extent,'description':description,'declared_nodes':copy.deepcopy(nodes),'four_way':{key:copy.deepcopy(SYSTEM_REVIEW[key]) for key in ('emergency-protection','information','privacy','device-autonomy')},'operation_record_review':checked,'outcome_chain':['Receipt','Attention','Understanding','Changed conduct in time','Observed protection'],'questions':['What specific harm and time window are stated, and what is their source?','What follows from acting, refusing and delaying?','What would make this delivery effective rather than merely forceful?','Who else and which essential services depend on these systems?','Which supported route can carry it and who controls that route?','What observation would disprove the expected benefit, and how would mistakes be repaired?'],'execution_authorized':False,'external_connection_created':False,'model_calls':0,'scope':'Reviews supplied hypothetical records and dependencies under the app framework. No device access, delivery, installation or system changes are executed.'}
