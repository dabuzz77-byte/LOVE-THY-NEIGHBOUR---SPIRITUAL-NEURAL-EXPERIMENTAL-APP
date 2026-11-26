"""Explicit effect assessment. Source declarations and measured facts stay distinct."""
import copy,math

def assess(action):
 if isinstance(action.get("consequences"),list):return detailed(action)
 effects=action.get('effects',{});known=action.get('evidence')=='observed-test';benefit=effects.get('benefit');harm=effects.get('harm');claimed=action.get('claimed','good')
 valid=lambda n:type(n) in (int,float) and math.isfinite(n) and n>=0
 concerns=[k for k in ('irreversible_harm','essential_service_loss','deception','unconsented_exposure') if effects.get(k) is True]
 if not known or not valid(benefit) or not valid(harm) or benefit==harm:return {'category':'unresolved','decision':'project-and-test','concerns':concerns,'reason':'Finite effect measurements and a justified comparison are required; ties remain open.'}
 good=benefit>harm and not concerns
 category=('true good' if claimed=='good' else 'false evil') if good else ('false good' if claimed=='good' else 'true evil')
 return {'category':category,'decision':'hold' if good else 'propose-correction','effects':copy.deepcopy(effects),'concerns':concerns,'scope':'Conditional assessment of supplied effects; evidence labels are declarations, not independently certified facts. No automatic host action.'}

def compare(action):
 alternatives=[{'choice':'act','effects':copy.deepcopy(action.get('effects',{})),'status':action.get('evidence','projected'),'assessment':assess(action)},{'choice':'wait','effects':copy.deepcopy(action.get('inaction_effects',{})),'status':'projected unless independently tested','assessment':assess(action.get('wait_scenario',{}))},{'choice':'correct','effects':copy.deepcopy(action.get('correction_effects',{})),'status':'proposed alternative; not automatically executed','assessment':assess(action.get('correction_scenario',{}))}]
 return {'assessment':assess(action),'alternatives':alternatives,'evil_flip_rule':'Hold verified beneficial states. For harmful effects propose an alternative, compare action and inaction, test it, and retain only verified improvements. Bit inversion alone does not certify goodness.','prayer_tests':['essential needs','protection from harm','forgiveness and repair','avoid deception and domination','accountable use of power'],'required_evidence':['source and units','affected parties','severity and duration','distribution of effects','failure conditions','reversibility','external dependencies','actual test result'],'world_scope':'Local and remote systemic effects may be modelled; unobserved effects remain projections.'}


def detailed(action):
 rows=action.get('consequences',[])
 if not 1<=len(rows)<=32:return {'category':'unresolved','decision':'define-affected-parties','reason':'Provide 1 to 32 explicit consequence records'}
 benefit=[0.,0.];harm=[0.,0.];concerns=[];distribution=[];missing=[]
 for i,r in enumerate(rows):
  if not isinstance(r,dict) or r.get('kind') not in ('benefit','harm'):raise ValueError('Consequence kind must be benefit or harm')
  low=r.get('severity_low');high=r.get('severity_high');prob=r.get('probability',1);hours=r.get('duration_hours',1);people=r.get('people',1)
  if any(type(v) not in (int,float) or not math.isfinite(v) for v in (low,high,prob,hours,people)):raise ValueError('Consequence values must be finite numbers')
  if not 0<=low<=high<=10 or not 0<=prob<=1 or not 0<=hours<=1e9 or not 1<=people<=1e9:raise ValueError('Consequence values outside defined ranges')
  if not r.get('party'):missing.append('affected party for record '+str(i))
  if not r.get('source'):missing.append('effect source for record '+str(i))
  if r.get('evidence')!='observed-test':missing.append('observed outcome for record '+str(i))
  factor=prob*people*(1+min(10,math.log1p(hours)))*(2 if r.get('vulnerable') else 1)
  score=[low*factor,high*factor];totals=benefit if r['kind']=='benefit' else harm
  totals[0]+=score[0];totals[1]+=score[1]
  floor=r['kind']=='harm' and (r.get('essential_service_loss') or high>=7 and r.get('reversible') is False)
  if floor:concerns.append({'party':r.get('party'),'concern':'severe irreversible harm or essential-service loss; aggregate benefit cannot conceal this'})
  distribution.append({'party':r.get('party'),'kind':r['kind'],'severity_interval':[low,high],'duration_hours':hours,'people':people,'vulnerable':bool(r.get('vulnerable')),'reversible':r.get('reversible'),'score_interval':score,'source':r.get('source')})
 positive=benefit[0]>harm[1] and not concerns;negative=harm[0]>benefit[1] or bool(concerns)
 category='unresolved'
 if not missing and positive:category='true good' if action.get('claimed','good')=='good' else 'false evil'
 elif not missing and negative:category='false good' if action.get('claimed','good')=='good' else 'true evil'
 return {'category':category,'decision':'hold' if category in ('true good','false evil') else 'propose-correction' if category in ('false good','true evil') else 'project-and-test','benefit_interval':benefit,'harm_interval':harm,'distribution':distribution,'concerns':concerns,'missing_evidence':missing,'prayer_application':{'provision':'essential-service loss explicitly examined','protection':'severity, duration and vulnerable parties retained','repair':'reversibility retained for each effect','humility':'overlapping or unsupported estimates remain unresolved'},'scope':'Conditional normative scoring with declared weights and supplied evidence. Not an objective universal morality meter; sources and evidence labels require independent review.'}
