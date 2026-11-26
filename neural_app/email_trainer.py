"""Local email drafting fixtures and etiquette study; no mail transport."""
import copy,math,re,threading,time
from .action_ethics import study_frame
SOURCES=[{'title':'Purdue OWL email etiquette','url':'https://owl.purdue.edu/owl/general_writing/academic_writing/email_etiquette.html','note':'Use an informative subject, an appropriate greeting, readable concise paragraphs and a professional closing.'},{'title':'Waterloo professional email guidance','url':'https://uwaterloo.ca/writing-and-communication-centre/writing-professional-emails-workplace','note':'Match the audience and purpose; make the subject and requested next step clear.'}]
MODES=['request','follow-up','apology','firm boundary','thanks','urgent concern']
TOPICS=['accessibility review','community food delivery','drawing workshop','software repair','meeting arrangements','public learning resource','invoice correction','safety inspection']
FOUR={'true_good':'Clear truthful requests, respect, timely protection and practical assistance.','false_good':'Pleasant language concealing coercion, false promises or an ignored urgent need.','false_evil':'Calling firm boundaries or legitimate criticism impolite merely because they challenge power.','true_evil':'Deception, humiliation, threats, harassment or exposure of private information.'}
def review(subject,body):
 subject=str(subject)[:200];body=str(body)[:12000];words=body.split()
 checks={'specific_subject':3<=len(subject.strip())<=100,'greeting':bool(re.match(r'(?i)\s*(hello|dear|hi|good morning|good afternoon)\b',body)),'concise':0<len(words)<=250,'closing':bool(re.search(r'(?i)(kind regards|best regards|thank you|thanks|sincerely)',body)),'readable_paragraphs':all(len(p.split())<=100 for p in body.split('\n\n')),'no_secret_markers':not bool(re.search(r'(?i)(password|api.?key|token)\s*[:=]',body)),'not_all_caps':not(body.isupper() and len(words)>4)}
 return {'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'word_count':len(words),'four_way':FOUR,'questions':['Is every claim supported?','Is the recipient appropriate?','Is the request clear and proportionate?','Could courtesy conceal harm, or firmness be mistaken for harm?','What information can be omitted to preserve privacy?'],'scope':'Structural heuristics; factual accuracy, cultural appropriateness and moral consequences require contextual review. Nothing sent.'}
def draft(mode,topic):
 texts={'request':f'I am writing about {topic}. Please let me know the next available step and any information you need from me.','follow-up':f'I am following up on {topic}. Could you confirm whether there is an update? If another person handles this, please point me to the appropriate contact.','apology':f'I am sorry for the confusion concerning {topic}. I would like to correct the mistake. Please confirm what needs changing so I can provide an accurate revision.','firm boundary':f'Regarding {topic}, I cannot agree to the current proposal. Please provide an alternative that respects the people affected and states the practical consequences clearly.','thanks':f'Thank you for your help with {topic}. Your time and practical assistance are appreciated. Please let me know if anything remains outstanding.','urgent concern':f'I am raising a time-sensitive concern about {topic}. Please confirm who can assess it and what immediate protective steps are available. This practice example does not establish an actual emergency.'}
 return {'subject':mode.capitalize()+': '+topic,'body':'Hello,\n\n'+texts[mode]+'\n\nKind regards,\nPractice writer'}
class EmailTrainer:
 def __init__(self):self.sequence=0;self.next_at=0;self.lock=threading.RLock();self.latest={};self.streams={}
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  from .training_pace import interval
  self.next_at=time.monotonic()+interval(c,.5);index=self.sequence%6;mode=MODES[index];topic=TOPICS[(self.sequence//6)%len(TOPICS)];d=draft(mode,topic);checked=review(d['subject'],d['body']);negative=review('',d['body'].upper())
  self.sequence+=1;record={'stream':index,'mode':mode,'cycle':self.sequence,'scenario':topic,'draft':d,'review':checked,'negative_control':{'omitted_subject_and_all_caps_score':negative['passed_checks'],'detected':negative['passed_checks']<checked['passed_checks']},'ethical_study':study_frame('etiquette',self.sequence),'test':'Structural completeness exceeds deliberately degraded draft','passed':negative['passed_checks']<checked['passed_checks'],'learning':'Template-based native practice and checks; no LLM weight update or automatic sending.'}
  with self.lock:self.latest=record;self.streams[index]=record
  c.bus.publish({'origin':'email-etiquette-trainer','target':'all','kind':'stage-output','payload':{'cycle':self.sequence,'stream':index,'passed':record['passed'],'checked_fields':checked['total_checks'],'provenance':'local-email-etiquette-practice','predefined_text':True,'stochastic':False}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'latest':copy.deepcopy(self.latest),'streams':copy.deepcopy(list(self.streams.values())),'sources':SOURCES,'four_way':FOUR,'scope':'Local drafting practice, structural review and ethical inquiry; no email account or sending capability.'}
 def sphere(self,c):
  with c.lock:sources=copy.deepcopy(list(c.sources.values()));goal=c.goal
  state=self.view();records=[{'source':'email-etiquette-trainer','path':['stream',r['stream']],'parent_event':r['cycle'],'record':r} for r in state['streams']]
  for source in sources:
   if source.get('facts'):records.append({'source':source['source'],'path':source['facts'][0].get('path',[]),'parent_event':source.get('parent_event'),'record':{'observation':source['facts'][0],'question':'How should an accurate, respectful and appropriately firm message communicate this observation?','four_way':FOUR,'next_check':'Identify audience, supported claims, actual need and privacy before drafting.'}})
  particles=[]
  for i,r in enumerate(records):
   y=1-2*(i+.5)/max(1,len(records));radius=math.sqrt(max(0,1-y*y));a=i*2.39996323
   particles.append({'id':'etiquette:'+str(i),'point':[radius*math.cos(a),y,radius*math.sin(a)],'phase':1.,'autonomy':0.,'selected':True,'expression_type':'etiquette-study','symbol':'✉','value_preview':r['source'],'source':r['source'],'path':r['path'],'parent_event':r['parent_event'],'record':r['record']})
  return {'sequence':state['sequence'],'particles':particles,'retained_sources':len(sources),'represented_values':len(records),'received_events':state['sequence'],'goal':goal,'selected_phases':[1.],'thought_trace':records,'scope':'Whole-engine retained observations and six etiquette practice streams. Local study only; no external messages sent.'}
