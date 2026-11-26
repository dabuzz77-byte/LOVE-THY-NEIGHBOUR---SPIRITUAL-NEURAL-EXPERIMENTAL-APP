"""Bounded, source-traced public research shared by two welfare-first spheres."""
import copy, math, threading, time

DOMAINS = {
 'ethical-hacking-research': ('Ethical hacking research · Lord’s Prayer · four-way assessment', [
 ('DWP disclosure policy','https://www.gov.uk/guidance/report-a-vulnerability-on-a-dwp-system'),
 ('Public-interest disclosure','https://ico.org.uk/for-organisations/foi/guide-to-managing-an-foi-request/exemptions/public-interest-test/'),
 ('Incident response','https://csrc.nist.gov/pubs/sp/800/61/r3/final'),
 ('Benefit decision review','https://www.gov.uk/mandatory-reconsideration')]),
 'souls-digits-research': ('Souls Over Digits · welfare, history and labour motivation', [
 ('Global and regional social protection','https://webapps.ilo.org/static/english/reports/flagship/world_social_protection_report_2024-26/Executive%20Summary.html'),
 ('Regional social protection indicators','https://www.worldbank.org/en/data/datatopics/aspire'),
 ('Job quality and motivation','https://www.oecd.org/en/topics/policy-issues/job-quality.html'),
 ('Basic-income research','https://www.helsinki.fi/en/news/society-and-learning/universal-basic-income-experiment-finland-new-research-reveals-significant-diversity-participants-experience'),
 ('Paid and unpaid care','https://www.ilo.org/topics-and-sectors/care-economy'),
 ('Money as a means','https://www.bankofengland.co.uk/explainers/what-is-money'),
 ('Fuller design science','https://www.bfi.org/about-fuller/big-ideas/design-science/design-science-primer/'),
 ('Fresco resource-based proposal','https://www.thevenusproject.com/faq/what-is-a-resource-based-economy/')])}
DOMAINS['power-influence-research']=('Power, Wealth and Influence · Illuminati history and claims', [('Illuminati historical research','https://www.uni-erfurt.de/en/gotha-research-centre/research/working-groups-and-networks/illuminati-research-unit'),('Founding history','https://www.lmu.de/en/about-lmu/lmu-at-a-glance/history/1776/index.html'),('Lobbying and influence','https://www.oecd.org/en/topics/lobbying.html')])
DOMAINS['cosmic-emergence-research']=('Cosmic emergence · scientific roots and creation traditions', [('Universe chronology and evidence','https://science.nasa.gov/universe/overview/'),('Big Bang and atomic formation','https://science.nasa.gov/mission/hubble/science/science-behind-the-discoveries/hubble-big-bang/'),('Genesis creation text','https://www.biblegateway.com/passage/?search=Genesis%201&version=KJV')])
REGIONS = ['Sub-Saharan Africa','Europe and Central Asia','Middle East and North Africa','South Asia','East Asia and Pacific','Latin America and Caribbean','North America','Oceania']
TOPICS = ['income support and adequacy','healthcare and disability access','housing, food and child welfare','pensions and unemployment insurance','benefit take-up, sanctions and appeals','fair pay and labour motivation','autonomy, purpose and meaningful work','unpaid care, volunteering and disability','benefit withdrawal and effective marginal tax rates','automation, productivity and shared provision','history of poor relief and social insurance','UBI, guaranteed income and negative income tax','universal basic services and social dividends','automation transition, ownership and democratic accountability','energy, supply chains, maintenance and essential work']
LANE_TOPICS = {'ethical-hacking-research':['owner repair and modification','public-interest disclosure','benefits, essential services and incident response','costs of action, refusal and delay'], 'power-influence-research':['Illuminati historical documents','ownership and financial concentration','lobbying, transparency and regulatory capture','allegations, source provenance and alternative explanations'], 'cosmic-emergence-research':['cosmic microwave background observations','primordial nucleosynthesis and atomic formation','stellar element production and planetary formation','creation traditions and textual provenance','self-organisation, feedback, memory and prediction','physical vacuum versus metaphysical void']}
QUESTIONS = {
 'true_good':'Which people benefit, by what mechanism, and what supports that prediction?',
 'false_good':'Could apparently protective action, refusal or delay conceal coercion, deprivation or collateral harm?',
 'false_evil':'Could a condemned action instead be justified repair, owner modification, disclosure or necessary protection?',
 'true_evil':'Which concrete injuries, exploitation or deprivation remain after context and alternatives are examined?'}

class PrincipleResearch:
 def __init__(self):
  self.lock=threading.RLock();self.closed=False;self.busy=False;self.next_at=0;self.next_read=0;self.next_discovery=0;self.cursor=0;self.sequence=0;self.history=[];self.discovery={};self.worker=None;self.read_cursor=0
 def tick(self,c):
  now=time.monotonic()
  if self.closed or now<self.next_at:return
  self.next_at=now+5;self.sequence+=1
  lane=list(DOMAINS)[self.cursor%len(DOMAINS)];i=self.cursor//len(DOMAINS);self.cursor+=1
  topics=LANE_TOPICS.get(lane,TOPICS)
  row={'domain':lane,'cycle':self.sequence,'time':time.time(),'region':REGIONS[i%len(REGIONS)],'topic':topics[(i//len(REGIONS))%len(topics)],'questions':QUESTIONS,'status':'research-question','evidence_roots':['original observation or attributed text','measurement method and date','inference and assumptions','independent replication or alternative reading','testable learning mechanism for the app'],'welfare_priority':1.0,'revenue_as_intrinsic_end':0.0,'scope':'Welfare is the normative priority. Financial capacity matters through provision, livelihoods and sustainability. Questions are not findings.'}
  with self.lock:self.history=(self.history+[row])[-64:]
  c.bus.publish({'origin':lane,'target':'all','kind':'stage-output','payload':{**row,'predefined_text':True,'stochastic':False,'provenance':'public-research-study'}})
  if not self.busy and now>=self.next_read:
   self.next_read=now+300;self.busy=True
   lane=list(DOMAINS)[self.read_cursor%len(DOMAINS)];i=self.read_cursor//len(DOMAINS);self.read_cursor+=1
   self.worker=threading.Thread(target=self.read,args=(c,lane,i),daemon=True,name='principle-public-research');self.worker.start()
 def read(self,c,lane,i):
  title,url=DOMAINS[lane][1][i%len(DOMAINS[lane][1])]
  record={'domain':lane,'title':title,'url':url,'time':time.time()}
  try:
   try:
    result=c.capability_validation.read_source(c,url,title)
    record.update(status='retrieved',**result)
   except Exception as e:record.update(status='unavailable',error=type(e).__name__+': '+str(e)[:240])
   research=getattr(getattr(c,'software_theory',None),'research',None)
   now=time.monotonic()
   if research and now>=self.next_discovery:
    self.next_discovery=now+900
    query=('cosmology cosmic microwave background primordial nucleosynthesis emergence information theory creation traditions primary sources' if lane=='cosmic-emergence-research' else ('historical Illuminati documentary evidence lobbying ownership influence transparency' if lane=='power-influence-research' else REGIONS[i%len(REGIONS)]+' social protection labour motivation policy evaluation' if lane=='souls-digits-research' else 'vulnerability disclosure public interest essential services incident response'))
    research.request(query);found=research.retrieve(query)
    with c.source_study.lock:
     for ref in found[:8]:
      link=ref.get('url','')
      if link.startswith('https://'):
       c.source_study.discovered[link]={'domain':lane,'title':ref.get('title','Public research'),'url':link,'summary':ref.get('summary',''),'provenance':ref.get('source'),'discovered':time.time()}
     while len(c.source_study.discovered)>128:c.source_study.discovered.pop(next(iter(c.source_study.discovered)))
    with self.lock:self.discovery[lane]={'query':query,'submitted':time.time(),'metadata_matches':len(found),'scope':'Discovery metadata; source text is read separately.'}
  except Exception as e:
   with self.lock:self.discovery[lane]={'status':'discovery-error','error':type(e).__name__+': '+str(e)[:240],'time':time.time()}
  finally:
   with self.lock:self.history=(self.history+[record])[-64:];self.busy=False
 def view(self,lane):
  with self.lock:return {'title':DOMAINS[lane][0],'sequence':self.sequence,'busy':self.busy,'recent':copy.deepcopy([r for r in self.history if r['domain']==lane]),'discovery':copy.deepcopy(self.discovery.get(lane,{})),'sources':[{'title':a,'url':b} for a,b in DOMAINS[lane][1]],'regions':REGIONS,'topics':LANE_TOPICS.get(lane,TOPICS),'questions':QUESTIONS,'refresh_seconds':300,'scope':'Public-source research and questions; no automatic verdict, credentials or external action.'}
 def sphere(self,lane):
  state=self.view(lane);records=state['recent']+state['sources'];particles=[]
  for i,row in enumerate(records):
   y=1-2*(i+.5)/max(1,len(records));a=i*2.399963;r=math.sqrt(max(0,1-y*y))
   particles.append({'id':lane+':'+str(i),'point':[r*math.cos(a),y,r*math.sin(a)],'phase':1,'autonomy':0,'selected':row.get('status')=='retrieved','symbol':'◇','expression_type':'research-evidence','source':row.get('url',lane),'path':[],'value_preview':row.get('title',row.get('topic','Research')),'record':row})
  return {'sequence':state['sequence'],'particles':particles,'received_events':len(state['recent']),'retained_sources':len(state['sources']),'represented_values':len(particles),'selected_phases':[1],'thought_trace':records,'network_intake':state,'research_review':state,'scope':state['scope']}
 def close(self):self.closed=True
