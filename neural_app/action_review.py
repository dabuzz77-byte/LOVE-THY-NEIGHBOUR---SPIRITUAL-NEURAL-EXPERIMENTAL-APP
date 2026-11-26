"""Source-attributed action/inaction reviews; no moral oracle or action executor."""
import copy,json,re

def review(body):
 if not isinstance(body,dict) or set(body)-{'goal','urgency','claims','options'} or len(json.dumps(body,allow_nan=False))>24000:raise ValueError('Supply a bounded goal, urgency, attributed claims and options')
 goal=body.get('goal');urgency=body.get('urgency','routine');claims=body.get('claims');options=body.get('options')
 if not isinstance(goal,str) or not 1<=len(goal)<=1000 or urgency not in ('immediate','time-sensitive','routine'):raise ValueError('Name the protective goal and immediate, time-sensitive or routine urgency')
 if not isinstance(claims,list) or not 1<=len(claims)<=24 or not isinstance(options,list) or not 2<=len(options)<=8:raise ValueError('Supply 1–24 attributed claims and 2–8 options including inaction')
 catalogue={}
 for claim in claims:
  if not isinstance(claim,dict) or set(claim)!={'id','text','source','status'}:raise ValueError('Each claim needs id, text, source and observed/reported/hypothesis/disputed status')
  if any(not isinstance(claim[k],str) or not 1<=len(claim[k])<=({'id':40,'text':1000,'source':200}[k]) for k in ('id','text','source')) or claim['status'] not in ('observed','reported','hypothesis','disputed') or claim['id'] in catalogue:raise ValueError('Use distinct short claim IDs, attributed text and a supported evidence status')
  catalogue[claim['id']]=copy.deepcopy(claim)
 names=set();rows=[];has_inaction=False
 for option in options:
  required={'name','kind','benefits','harms','required_claims','permission','reversible'}
  if not isinstance(option,dict) or set(option)!=required or option['kind'] not in ('action','inaction') or option['permission'] not in ('granted','needed','not-applicable') or type(option['reversible']) is not bool:raise ValueError('Each option needs name, action/inaction kind, benefits, harms, required_claims, permission and reversible')
  if not isinstance(option['name'],str) or not 1<=len(option['name'])<=100 or option['name'].casefold() in names:raise ValueError('Use distinct option names')
  names.add(option['name'].casefold());has_inaction|=option['kind']=='inaction'
  for key in ('benefits','harms'):
   if not isinstance(option[key],list) or len(option[key])>12 or any(not isinstance(v,str) or not 1<=len(v)<=600 for v in option[key]):raise ValueError('Describe up to twelve possible benefits and harms per option')
  ids=option['required_claims']
  if not isinstance(ids,list) or len(ids)>24 or any(not isinstance(v,str) or v not in catalogue for v in ids) or len(set(ids))!=len(ids):raise ValueError('Required claims must reference distinct supplied claim IDs')
  unresolved=[i for i in ids if catalogue[i]['status']!='observed']
  gaps=[]
  if not ids:gaps.append('No evidence dependency was declared; this is not proof that none exists.')
  if unresolved:gaps.append('Resolve or explicitly account for uncertain claims: '+', '.join(unresolved))
  if option['permission']=='needed':gaps.append('Identify the relevant permission or accountable emergency authority before execution.')
  if not option['reversible']:gaps.append('Describe stopping conditions, review and repair for irreversible consequences.')
  if not option['harms']:gaps.append('No harms were listed; check indirect, mistaken-target and displacement risks.')
  four_way={
   'true_good_test':{'intended_benefits':copy.deepcopy(option['benefits']),'question':'Which benefit is supported by outcomes, for whom, and against what baseline?'},
   'false_good_test':{'possible_harms':copy.deepcopy(option['harms']),'question':'Could this apparently protective choice conceal coercion, error or greater harm?'},
   'true_evil_test':{'claim_dependencies':copy.deepcopy(ids),'question':'What specific harmful conduct and causal effects are evidenced? Identity and conviction alone do not establish them.'},
   'false_evil_test':{'question':'Could a beneficial or harmless alternative be wrongly rejected? What interest does a challenged barrier protect, and what harm might it cause?'}
  }
  rows.append({'name':option['name'],'kind':option['kind'],'reversible':option['reversible'],'permission':option['permission'],'evidence_dependencies':[copy.deepcopy(catalogue[i]) for i in ids],'unresolved_claim_ids':unresolved,'review_gaps':gaps,'four_way':four_way,'status':'needs-clarification' if gaps else 'ready-for-human-review'})
 if not has_inaction:raise ValueError('Include an explicit inaction option with its own benefits and harms; delay is not presumed harmless')
 return {'status':'reviewed','goal':goal,'urgency':urgency,'options':rows,'claims':list(catalogue.values()),'next_questions':['Which action can protect affected people in time?','What does delay cost, and what alternatives could work with less harm?','How will success, stopping conditions, mistakes and repair be checked?'],'execution_authorized':False,'actions_executed':0,'model_calls':0,'scope':'Structured review of supplied statements, not independent verification, divine authority, a legal determination or a guarantee of safety. Observed is a supplied evidence label. No religious group is classified as guilty. Urgency is preserved without converting a review into technical access or execution.'}

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!')
 if key in ('show action review','explain action review'):
  row=work.state.get('action_review')
  if not row:return {'status':'needs-input','answer':'Supply assess proposed action: followed by the goal, claims and action/inaction options.','model_calls':0}
  from .native_work import digest
  if row['input_sha256']!=digest(row['input']):raise ValueError('Retained action-review source changed; submit it again')
  report=review(copy.deepcopy(row['input']))
  return {'status':'complete','answer':format_report(report),'action_review':report,'action_repeated':False,'model_calls':0}
 if not re.match(r'^assess proposed action:',text.strip(),re.I):return None
 body=json.loads(text.split(':',1)[1]);report=review(body)
 from .native_work import digest
 work.state['action_review']={'input':copy.deepcopy(body),'input_sha256':digest(body)};work.state['focus_kind']='action-review'
 return {'status':'complete','answer':format_report(report),'action_review':report,'model_calls':0}

def format_report(report):
 lines=['Goal: '+report['goal'],'Urgency: '+report['urgency']+'. Acting and inaction are both assessed.']
 for row in report['options']:
  lines+=['\n'+row['name']+' ('+row['kind']+'): '+row['status'], 'Intended benefits: '+'; '.join(row['four_way']['true_good_test']['intended_benefits']), 'Possible harms: '+'; '.join(row['four_way']['false_good_test']['possible_harms'])]
  lines.extend('- '+gap for gap in row['review_gaps'])
 lines+=['\nThis is a review, not an authorization or completed intervention.']
 return '\n'.join(lines)
