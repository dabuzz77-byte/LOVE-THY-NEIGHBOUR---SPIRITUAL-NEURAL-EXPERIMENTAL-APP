"""Welfare-first institutional inquiry and exact small resource-allocation experiments."""
import collections,copy,itertools,json,math,threading,time
SOURCES=[
 ('UNDP · Human development','https://hdr.undp.org/about/human-development','Human development considers people’s capabilities and opportunities beyond economic output.'),
 ('UNDP · Human Development Index','https://hdr.undp.org/data-center/human-development-index','The index combines health, education and income; it is not a complete account of welfare.'),
 ('OECD · Beyond GDP','https://www.oecd.org/en/topics/well-being-and-beyond-gdp.html','Economic, social and environmental outcomes supplement output measures.'),
 ('UN · Universal Declaration of Human Rights','https://www.un.org/en/about-us/universal-declaration-of-human-rights','Dignity, social security and an adequate standard of living provide a rights-based reference.'),
 ('ILO · Profits and poverty','https://www.ilo.org/publications/major-publications/profits-and-poverty-economics-forced-labour','The report examines profits generated through forced labour and exploitation.'),
 ('WHO · Financial protection','https://www.who.int/health-topics/financial-protection','Financial protection examines hardship caused by healthcare payments.'),
 ('National Archives · Abolition','https://www.archives.gov/milestone-documents/13th-amendment','The 1865 amendment abolished slavery and involuntary servitude with its stated criminal-punishment exception.'),
 ('UK Parliament · Poor Law reform','https://www.parliament.uk/about/living-heritage/transformingsociety/livinglearning/19thcentury/overview/poorlaw/','Historical material for examining relief, workhouse policy and institutional incentives.')]
DOMAINS=[
 ('essential-needs','Food, water, housing and healthcare','Who loses access because of inability to pay, scarcity or exclusion?'),
 ('labour','Labour and exploitation','Are people coerced, injured or denied the benefits of their work?'),
 ('finance','Money, credit and debt','Does finance enable provision, or extract returns while shifting risks onto others?'),
 ('public-services','Public services and budgets','Do budgets sustain reliable services while meeting urgent needs?'),
 ('metrics','Targets, scores and automation','Does optimising the score worsen the outcome the score was meant to measure?'),
 ('digital','Digital infrastructure','Do access, privacy, security and resilience serve people, including those with few resources?'),
 ('ecology','Ecological and intergenerational costs','Who bears pollution, depletion and costs displaced into the future?'),
 ('power','Power and accountability','Can affected people challenge decisions and obtain repair?'),
 ('transition','Transition and unintended consequences','Could an intended reform interrupt food, wages, healthcare or essential infrastructure?')]
DEFAULT={'budget':4,'parties':[{'id':'vulnerable-household','need':3,'unit_cost':1,'payment':0,'vulnerable':True},{'id':'higher-income-household','need':3,'unit_cost':1,'payment':8,'vulnerable':False}]}
def experiment(spec=None):
 spec=copy.deepcopy(DEFAULT if spec is None else spec);budget=spec.get('budget');parties=spec.get('parties',[])
 if type(budget)is not int or not 0<=budget<=64 or not isinstance(parties,list) or not 1<=len(parties)<=4:raise ValueError('Use budget 0–64 and 1–4 parties')
 ids=set()
 for p in parties:
  if not isinstance(p,dict) or not isinstance(p.get('id'),str) or not 0<len(p['id'])<=100 or p['id'] in ids:raise ValueError('Use unique party identifiers')
  ids.add(p['id'])
  for k,lo,hi in [('need',0,8),('unit_cost',1,16),('payment',0,100)]:
   if type(p.get(k))is not int or not lo<=p[k]<=hi:raise ValueError('Invalid '+k)
  if type(p.get('vulnerable'))is not bool:raise ValueError('Vulnerable must be boolean')
 feasible=[]
 for allocation in itertools.product(*(range(p['need']+1) for p in parties)):
  cost=sum(a*p['unit_cost'] for a,p in zip(allocation,parties))
  if cost>budget:continue
  unmet=[p['need']-a for a,p in zip(allocation,parties)]
  feasible.append({'allocation':dict(zip((p['id'] for p in parties),allocation)),'unmet':dict(zip((p['id'] for p in parties),unmet)),'vulnerable_unmet':sum(u for u,p in zip(unmet,parties) if p['vulnerable']),'total_unmet':sum(unmet),'cost':cost,'remaining':budget-cost,'revenue':sum(a*p['payment'] for a,p in zip(allocation,parties))})
 welfare=min(feasible,key=lambda r:(r['vulnerable_unmet'],r['total_unmet'],r['cost']));revenue=max(feasible,key=lambda r:(r['revenue'],-r['cost']))
 def compare(candidate,baseline,claimed):
  gains=[k for k in candidate['unmet'] if candidate['unmet'][k]<baseline['unmet'][k]];losses=[k for k in candidate['unmet'] if candidate['unmet'][k]>baseline['unmet'][k]]
  # Declared priority favours urgent vulnerable need; distributional losses stay visible.
  cv=(candidate['vulnerable_unmet'],candidate['total_unmet']);bv=(baseline['vulnerable_unmet'],baseline['total_unmet'])
  good=cv<bv;bad=cv>bv
  category=('true good' if claimed=='good' else 'false evil') if good else ('false good' if claimed=='good' else 'true evil') if bad else 'unresolved / equivalent on selected welfare measures'
  return {'claimed':claimed,'category':category,'gains':gains,'losses':losses,'tradeoff':bool(gains and losses),'basis':'Explicit lexicographic priority: vulnerable unmet need, then total unmet need; not a claim of universal empirical certainty.'}
 return {'model':spec,'feasible_allocations':len(feasible),'welfare_first':welfare,'revenue_first':revenue,'four_way':[{'choice':'welfare-first','relative_to':'revenue-first',**compare(welfare,revenue,'good')},{'choice':'welfare-first dismissed as bad','relative_to':'revenue-first',**compare(welfare,revenue,'evil')},{'choice':'revenue-first praised as good','relative_to':'welfare-first',**compare(revenue,welfare,'good')},{'choice':'revenue-first criticised as bad','relative_to':'welfare-first',**compare(revenue,welfare,'evil')}],'conservation':'Every allocation stays within the supplied finite budget. Human needs and distribution remain visible beside monetary results.','limitations':['Illustrative allocation model, not a calibrated economy','Revenue is not profit and no future production is modelled','Needs and vulnerability are supplied assumptions','Transition, corruption, incentive and ecological effects require further models'],'bit_parallel':'Changing an eligibility, price or priority value can change access. Trace actual code, dependency and service outcomes before changing a live system.'}
class SoulsDigits:
 def __init__(self,data):
  self.path=data/'souls-digits-experiments.json';self.lock=threading.RLock();self.next_at=0;self.sequence=0;self.latest={};self.history=collections.deque(maxlen=24);self.intake=None;self.research=None;self.next_research=0;self.research_index=0
  try:
   saved=json.loads(self.path.read_text(encoding='utf-8'));self.sequence=saved.get('sequence',0);self.history.extend(saved.get('history',[])[-24:])
  except (OSError,ValueError):pass
 def calculate(self,spec=None):
  result=experiment(spec)
  result['transition_sweep']=transition_sweep(spec)
  a=result['welfare_first'];b=result['revenue_first']
  result['thought_trace']=[
   {'stage':'observe','finding':str(result['feasible_allocations'])+' feasible allocations meet the same resource constraint.'},
   {'stage':'compare','finding':'Need-first leaves '+str(a['vulnerable_unmet'])+' vulnerable need units unmet; revenue-first leaves '+str(b['vulnerable_unmet'])+'.'},
   {'stage':'distribution','finding':'Keep each household’s allocation and unmet need visible, including any losses when priority changes.'},
   {'stage':'counterfactual','finding':'Payment is changed only in the ranking objective; resources, supplied needs and unit costs stay identical.'},
   {'stage':'hypothesis','finding':'Test whether separating access to essential provision from payment reduces deprivation under these assumptions.'},
   {'stage':'challenge','finding':'Test future supply, operating costs, corruption, exclusion, appeals and transition disruption in additional models before generalising.'},
   {'stage':'authority','finding':'Public discovery and local simulation may proceed; changing an external system requires relevant authority and an operation-specific consequence model.'},
   {'stage':'urgent-protection','finding':'Compare delay with interventions that can actually protect the threatened person in time. Information delivery has no assumed violence-prevention success rate.'}]
  with self.lock:
   self.sequence+=1;result.update(sequence=self.sequence,time=time.time());self.latest=result;self.history.append(result)
   temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'sequence':self.sequence,'history':list(self.history)},ensure_ascii=True),encoding='utf-8');temp.replace(self.path)
  return copy.deepcopy(result)
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+30
  if self.research and time.monotonic()>=self.next_research:
   from .money_knowledge import USES
   queries=[topic+' money welfare access evidence' for topic in USES]+['social protection poverty inequality','forced labour exploitation economic incentives','universal health coverage financial hardship','wellbeing beyond GDP public policy','automated welfare eligibility exclusion','resource allocation essential services resilience']
   self.research.request(queries[self.research_index%len(queries)]);self.research_index+=1;self.next_research=time.monotonic()+900
  # Sweep scarcity levels; these are sensitivity experiments, not claims about countries.
  spec=copy.deepcopy(DEFAULT);spec['budget']=self.sequence%7;r=self.calculate(spec)
  c.bus.publish({'origin':'souls-digits','target':'all','kind':'stage-output','payload':{'sequence':r['sequence'],'budget':spec['budget'],'welfare_unmet':r['welfare_first']['total_unmet'],'revenue_unmet':r['revenue_first']['total_unmet'],'vulnerable_unmet':r['welfare_first']['vulnerable_unmet'],'provenance':'controlled-welfare-allocation-experiment','stochastic':False,'predefined_text':True}})
 def view(self):
  reports=[]
  if self.intake:
   for term in ('poverty','debt','forced labour','healthcare','exploitation'):
    try:reports.extend(r for r in self.intake.retrieve(term) if not r.get('private'))
    except Exception:pass
  reports=list({r.get('url','')+r.get('title',''):r for r in reports}.values())[:16]
  from .money_knowledge import knowledge
  with self.lock:return {'money_knowledge':knowledge(),'sequence':self.sequence,'latest':copy.deepcopy(self.latest),'recent':copy.deepcopy(list(self.history)[-8:]),'learning':{'retained_trials':len(self.history),'welfare_reduced_vulnerable_unmet':sum(r['welfare_first']['vulnerable_unmet']<r['revenue_first']['vulnerable_unmet'] for r in self.history),'equal_vulnerable_unmet':sum(r['welfare_first']['vulnerable_unmet']==r['revenue_first']['vulnerable_unmet'] for r in self.history),'scope':'Observed outcomes of supplied synthetic models; not causal estimates for real populations.'},'default_model':DEFAULT,'sources':[{'title':t,'url':u,'summary':s} for t,u,s in SOURCES],'domains':[{'id':i,'title':t,'question':q} for i,t,q in DOMAINS],'reports':reports,'framework':{'souls_over_digits':'People’s welfare, dignity and essential needs take priority; numbers are accountable tools.','digits_over_souls':'A target, payment, quota or valuation is pursued despite avoidable human harm.','four_way':'Evaluate genuine benefit, concealed harm, wrongly condemned benefit and genuine harm. Intent and institutional labels do not settle outcomes.','prayer':'Provision, protection from evil, forgiveness, repair and accountable power.','zeitgeist':'Treat Zeitgeist: Addendum as a critical viewpoint: separate its financial claims, causal explanations and proposed reforms; compare each with primary evidence and transition consequences.'},'discovery':[{'domain':i,'question':q,'method':['Search public sources','Record competing explanations and affected parties','Compare action, inaction and reform','Specify a testable dependency or allocation model','Check outcomes and revise'],'authority':'An ethical assessment of an access rule does not grant credentials or permit private-device intrusion.'} for i,t,q in DOMAINS]}


def transition_sweep(spec=None):
 """Finite objective sensitivity, not a forecast or production-economic policy."""
 from fractions import Fraction
 validated=experiment(spec);model=validated['model'];parties=model['parties'];rows=[]
 for allocation in itertools.product(*(range(p['need']+1) for p in parties)):
  cost=sum(a*p['unit_cost'] for a,p in zip(allocation,parties))
  if cost>model['budget']:continue
  unmet=[p['need']-a for a,p in zip(allocation,parties)]
  rows.append({'allocation':dict(zip((p['id'] for p in parties),allocation)),'cost':cost,'revenue':sum(a*p['payment'] for a,p in zip(allocation,parties)),'vulnerable_unmet':sum(u for u,p in zip(unmet,parties) if p['vulnerable']),'total_unmet':sum(unmet)})
 max_revenue=max(1,max(r['revenue'] for r in rows));total_need=sum(p['need'] for p in parties);vneed=sum(p['need'] for p in parties if p['vulnerable']);points=[]
 for step in range(11):
  weight=Fraction(step,10)
  def utility(r):
   welfare=1-Fraction(r['vulnerable_unmet']*(total_need+1)+r['total_unmet'],max(1,vneed*(total_need+1)+total_need))
   return weight*welfare+(1-weight)*Fraction(r['revenue'],max_revenue)
  chosen=max(rows,key=lambda r:(utility(r),-r['vulnerable_unmet'],-r['total_unmet'],-r['cost']))
  previous=points[-1] if points else None
  points.append({**chosen,'welfare_weight':str(weight),'revenue_weight':str(1-weight),'objective':str(utility(chosen)),'changed_allocation':previous is not None and chosen['allocation']!=previous['allocation']})
 return {'points':points,'weights':'Exact rational arithmetic at 11 supplied sensitivity points','assumptions':'Normalised revenue vs declared lexicographic welfare loss; finite budget unchanged. No transfers or system changes executed.','limitations':'Not a real economy forecast; future supply, jobs, consent, ecology and operating costs require separate models.','four_way':'Assess access gains alongside losses, dependencies, delay, verification and repair.'}
