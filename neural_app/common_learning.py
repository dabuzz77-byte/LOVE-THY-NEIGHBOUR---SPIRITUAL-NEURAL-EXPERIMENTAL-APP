"""Explainable common learning centre over public app topic definitions."""
import collections,re
THEMES={
 'causality':('Causal models and consequences','cause causal prediction consequence outcome action experiment model'.split()),
 'language':('Language memory and communication','language text character memory knowledge source meaning conversation'.split()),
 'measurement':('Measurement and reliable observation','measurement measured numeric data observation units source evidence'.split()),
 'verification':('Verification and useful learning','verify verified check test learning accuracy result contract'.split()),
 'ethics':('Welfare accountability and repair','welfare provision dignity protection repair harm ethical good'.split()),
 'resource-design':('Whole-system resource design','resource system infrastructure energy design dependency efficiency'.split())}
def common_learning():
 from .element_thinking import SPECS
 from .action_ethics import ASSESSMENT_LESSONS,PRINCIPLES
 from .free_learning import RESOURCES
 corpus=[]
 for key,(title,aliases,question) in SPECS.items():corpus.append(('stage:'+key,'engine',title+' '+question))
 for row in ASSESSMENT_LESSONS:corpus.append(('lesson:'+row['id'],'lesson',' '.join(str(v) for v in row.values())))
 for domain,rows in RESOURCES.items():
  for i,row in enumerate(rows):corpus.append(('learning:'+domain+':'+str(i),'source-catalogue',' '.join(row[:3])))
 themes=[]
 for domain,(title,words) in THEMES.items():
  matches=[];groups=set();terms=collections.Counter()
  for ident,kind,text in corpus:
   tokens=set(re.findall(r'[^\W_]+',text.casefold()));hit=[w for w in words if any(t==w or t.startswith(w) for t in tokens)]
   if hit:matches.append(ident);groups.add(kind);terms.update(hit)
  themes.append({'domain':domain,'title':title,'supporting_sections':len(matches),'supporting_groups':sorted(groups),'matching_terms':dict(terms.most_common()),'examples':matches[:8],'search_topic':title+' methods learning evaluation public reference'})
 themes.sort(key=lambda r:(-len(r['supporting_groups']),-r['supporting_sections'],r['domain']))
 roots=[]
 definitions=[
  ('purpose','Source, unity and purpose',['ethics','language'],'What is this for, and how does it serve living beings?','Author-defined spiritual and ethical root; empirical claims retain separate source and test status.','ethics','comparative ethics human flourishing meaning purpose learning'),
  ('representation','Information and representation',['language','measurement','verification'],'What is represented, in which language, encoding, units and context?','Shared foundation of text, code, bits, data, observations and communication.','language','information representation language measurement units computing foundations'),
  ('change','Cause and change',['causality','verification','resource-design'],'What action changes which state, through which dependencies, with what consequence?','Shared foundation of physics models, programs, plans, social interventions and feedback.','causality','causal models state transitions dependencies feedback learning foundations'),
  ('limits','Resources and limits',['resource-design','measurement','ethics'],'What is needed, available, lost, conserved or constrained?','Connects material needs, energy, computation, provision and economic transition.','resource-design','systems resources constraints energy human welfare design foundations'),
  ('experience','Living experience and welfare',['ethics','causality','resource-design'],'Who experiences the outcome, and what supports or harms their life?','Connects the app’s concern for people, animals, vulnerability, protection and repair.','ethics','welfare sentience human needs animal wellbeing ethical consequences foundations'),
  ('correction','Learning and correction',['verification','measurement','causality','language'],'How is a belief, prediction or action checked, revised and retained?','Connects memory, observation, independent testing, practical wisdom and accountable learning.','verification','learning prediction error correction independent verification foundations')]
 for ident,title,links,question,explanation,domain,query in definitions:
  supporting=[t for t in themes if t['domain'] in links]
  roots.append({'id':ident,'title':title,'domain':domain,'question':question,'explanation':explanation,'connected_themes':links,'theme_bridges':len(supporting),'supporting_section_mentions':sum(t['supporting_sections'] for t in supporting),'search_topic':query,'status':'Explicit conceptual model of shared prerequisites; support counts are topic mentions, not proof of a universal theory.'})
 branches=[]
 for ident,kind,text in corpus:
  if kind=='source-catalogue':continue
  words=set(re.findall(r'[^\W_]+',text.casefold()))
  ranked=sorted(((sum(any(t==w or t.startswith(w) for t in words) for w in terms),domain) for domain,(_,terms) in THEMES.items()),reverse=True)
  links=[domain for score,domain in ranked[:2] if score>0] or ['verification']
  branches.append({'id':ident,'level':'application-branch','domain':links[0],'title':ident.split(':',1)[1].replace('-',' '),'connected_themes':links,'root_ids':[r['id'] for r in roots if set(r['connected_themes'])&set(links)],'search_topic':text[:180]+' learning methods public reference','basis':'Public section question or lesson case linked by topic terms; this mapping is reviewable.'})
 tree={'direction':'roots → shared principles → section branches → practical checks → feedback to learning priorities','roots':[r['id'] for r in roots],'theme_edges':[{'from':r['id'],'to':domain} for r in roots for domain in r['connected_themes']],'branches':branches,'feedback':'Capability failures prioritise relevant source domains; source claims require independent checks before retention as reliable procedures.'}
 from .mind_workspace import CHAIN
 return {'guiding_framework':{'orientation':PRINCIPLES['orientation'],'cosmological_sequence':list(CHAIN),'status':'App-author spiritual and ethical framework; source observations and task verification retain their own labels.'},'tree':tree,'roots':roots,'themes':themes,'documents_considered':len(corpus),'basis':'Recurring public section questions, authored lesson topics and source-catalogue descriptions; no private account history or user text.','meaning':'Shared roots connect the purposes and prerequisites of topics; keyword coverage supplies examples. This is not a mathematical median or proof that every source agrees.'}
