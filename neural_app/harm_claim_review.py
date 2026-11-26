"""Structured hypothetical harm claims; no intrusion, cracking or execution facilities."""
import copy,json
from .decision_framework import SYSTEM_REVIEW,CONDITIONAL_STANDARD

CASES={
 'owner-modification':{'sectors':['device-autonomy','privacy'],'context':'An owner wants repair, customization or jailbreaking. Separate owner choice, third-party data, device stability and effects on others.'},
 'urgent-protection':{'sectors':['emergency-protection','information','privacy'],'context':'A particular threatened person needs protection. Compare useful communication, urgent practical help, delay and displaced harm. Threat evidence concerns conduct, not religious identity.'},
 'financial-relief':{'sectors':['public-support','payments','credit'],'context':'Examine hardship and essential provision, wages and benefits, exploitation, institutional control, relief and downstream consequences. Neither revenue nor a benevolent label settles the case.'},
 'creative-access':{'sectors':['creative-work'],'context':'A poor child wants to play. Include hardship, joy, access and creator sustenance. A developer may welcome giving access; retain their actual stated wishes separately from hypothetical or inferred feelings.'}}

def review(body):
 if not isinstance(body,dict) or len(json.dumps(body))>24000:raise ValueError('Provide a bounded harm-claim case')
 case=body.get('case');claims=body.get('claims',[])
 if case not in CASES or not isinstance(claims,list) or len(claims)>32:raise ValueError('Choose owner-modification, urgent-protection, financial-relief or creative-access, with up to 32 claims')
 rows=[]
 for claim in claims:
  if not isinstance(claim,dict) or not isinstance(claim.get('description'),str) or not 1<=len(claim['description'])<=2000:raise ValueError('Each claim needs a short description')
  status=claim.get('status','reported');kind=claim.get('kind','human-welfare')
  if status not in ('observed','reported','predicted','hypothetical') or kind not in ('human-welfare','bodily-safety','essential-provision','privacy','device-stability','creator-livelihood','revenue','institutional-control'):raise ValueError('Use a supported claim status and kind')
  missing=[key for key in ('affected','mechanism','source','verification') if not claim.get(key)]
  rows.append({'description':claim['description'],'kind':kind,'declared_status':status,'affected':copy.deepcopy(claim.get('affected',[])),'mechanism':copy.deepcopy(claim.get('mechanism')),'source':copy.deepcopy(claim.get('source')),'verification':copy.deepcopy(claim.get('verification')),'unresolved':missing,'independently_authenticated':False,'human_effect_needed':kind in ('revenue','institutional-control'),'review_note':'Trace the claimed financial/control change to its effects on beings; do not assume either that all lost revenue is harm or that all revenue is irrelevant.' if kind in ('revenue','institutional-control') else 'Consider concrete benefits, harms, uncertainty and effects on others.'})
 return {'case':case,'context':CASES[case]['context'],'orientation':'Lord’s Prayer: provision, forgiveness, protection and accountable power; souls over digits.','four_way':{sector:copy.deepcopy(SYSTEM_REVIEW[sector]) for sector in CASES[case]['sectors']},'conditional_standard':dict(CONDITIONAL_STANDARD),'claims':rows,'unresolved_claims':sum(bool(r['unresolved']) for r in rows),'questions':['What follows from acting, refusing or delaying?','What does the barrier protect and what injustice might it conceal?','What does the proposed intervention achieve and what other harms might it create?','Are feelings, consent and future outcomes stated, inferred or merely stipulated?','Which effective alternatives, stop conditions and repairs are available?'],'execution_authorized':False,'scope':'Structured ethical inquiry under the user’s framework, not an automatic divine verdict, authenticated preference, credential or permission to alter another system. No operations are executed.'}
