"""Native formal-writing practice based on open office document structure."""
import html,re,time,collections,threading
GROUPS={
 'Correspondence':['Formal letter','Complaint','Appeal','Cover letter','Reference letter','Invitation','Thank you letter','Notice','Memorandum'],
 'Business':['Business report','Proposal','Business case','Executive brief','Project charter','Project plan','Progress report','Meeting agenda','Meeting minutes','Action register','Handover','Incident report'],
 'Policy and governance':['Policy','Procedure','Code of conduct','Consultation response','Governance report','Risk assessment','Audit report','Privacy notice'],
 'Research and education':['Research proposal','Research report','Literature review','Essay','Lesson plan','Study guide','Training manual','Technical specification','User manual','Experiment report'],
 'Community and personal':['Grant application','Fundraising proposal','Community plan','Volunteer handbook','Personal statement','CV','Biography','Press release','Newsletter','Book chapter']}
SOURCES=[{'title':'LibreOffice Writer and office documentation','url':'https://books.libreoffice.org/','purpose':'Styles, document structure, templates, editing and publication workflows.'},{'title':'OASIS OpenDocument 1.3','url':'https://docs.oasis-open.org/office/OpenDocument/v1.3/OpenDocument-v1.3-part1-introduction.html','purpose':'Open document format specification.'}]
def outline(kind):
 if kind not in sum(GROUPS.values(),[]):raise ValueError('Select a supported document type')
 special={'Meeting minutes':['Meeting details','Attendees and apologies','Decisions','Actions and owners','Next meeting'],'Meeting agenda':['Meeting purpose','Attendees','Agenda and timings','Required decisions','Preparation'],'CV':['Profile','Experience','Education','Skills','Additional information'],'Formal letter':['Sender and recipient','Subject','Purpose','Details','Requested action','Closing'],'Experiment report':['Question','Method','Results','Interpretation','Limitations','Next steps'],'Policy':['Purpose','Scope','Responsibilities','Requirements','Exceptions and appeals','Review schedule'],'Research report':['Abstract','Introduction','Methods','Results','Discussion','References']}
 return special.get(kind,['Purpose and audience','Context','Main information','Evidence and sources','Recommendations or actions','Next steps'])
def review(kind,text):
 headings=outline(kind);text=str(text)[:100000];words=re.findall(r"\b[\w’'-]+\b",text)
 missing=[h for h in headings if h.casefold() not in text.casefold()]
 return {'type':kind,'words':len(words),'missing_sections':missing,'checks':{'has_content':len(words)>25,'expected_sections_present':not missing,'unfilled_placeholders':bool(re.search(r'\[[^]\n]+\]',text))},'editorial_questions':['Is the purpose clear to this reader?','Are factual claims supported and sources identifiable?','Are names, dates, figures and commitments correct?','Does the conclusion state the required action?','Are headings and reading order accessible?'],'scope':'Structural checks and editorial prompts; not automatic factual, legal or professional certification.'}
def fodt(title,text):
 def esc(s):return html.escape(str(s),quote=True)
 paragraphs=''.join('<text:p text:style-name="Body">'+esc(line)+'</text:p>' for line in str(text).splitlines())
 return '<?xml version="1.0" encoding="UTF-8"?><office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text"><office:styles><style:style style:name="Title" style:family="paragraph"><style:text-properties fo:font-size="22pt" fo:font-weight="bold"/></style:style><style:style style:name="Body" style:family="paragraph"><style:paragraph-properties fo:margin-bottom="0.12in"/><style:text-properties fo:font-size="11pt"/></style:style></office:styles><office:body><office:text><text:p text:style-name="Title">'+esc(title)+'</text:p>'+paragraphs+'</office:text></office:body></office:document>'
class DocumentTrainer:
 def __init__(self):self.sequence=0;self.next_at=0;self.latest={};self.lock=threading.RLock();self.history=collections.deque(maxlen=24)
 def view(self):
  with self.lock:return {'groups':GROUPS,'sources':SOURCES,'sequence':self.sequence,'latest':self.latest,'recent':list(self.history),'basis':'Native trainer informed by LibreOffice documentation and OpenDocument; no office-suite source code bundled or separate office process required.'}
 def practice(self,b):
  kind=b.get('type','Formal letter');sections=outline(kind);text=str(b.get('text',''))[:100000];title=str(b.get('title',kind))[:200]
  return {'outline':sections,'scaffold':'\n\n'.join(h+'\n[Write verified information for this section.]' for h in sections),'review':review(kind,text),'export':fodt(title,text),'filename':'document.fodt'}
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  from .training_pace import interval
  self.next_at=time.monotonic()+interval(c)
  types=sum(GROUPS.values(),[]);kind=types[self.sequence%len(types)];sections=outline(kind)
  # Independent negative control: removing one required heading must be detected.
  complete='\n'.join(sections);partial='\n'.join(sections[1:]);passed=not review(kind,complete)['missing_sections'] and sections[0] in review(kind,partial)['missing_sections']
  with self.lock:self.sequence+=1;self.latest={'type':kind,'sections':sections,'test':'Required-section presence and omission negative control','passed':passed};self.history.append(self.latest.copy())
  c.bus.publish({'origin':'document-trainer','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'passed':passed,'types':len(types),'provenance':'native-document-structure-practice','predefined_text':True,'stochastic':False}})
