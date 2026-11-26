"""Curated free learning entry points and original concise study notes."""
RESOURCES={
 'security':[(t,u,'Defensive security study: scope, protect, detect, respond and recover. Test on synthetic or explicitly authorized assets.','Public primary guidance; source terms apply.') for t,u in __import__(__package__+'.system_shield',fromlist=['SOURCES']).SOURCES],
 'email':[('Purdue OWL email etiquette','https://owl.purdue.edu/owl/general_writing/academic_writing/email_etiquette.html','Meaningful subjects, audience-appropriate greetings, concise paragraphs and professional closings.','Free public guidance; practice drafts are original.')],
 'paint':[('Microsoft Paint drawing concepts','https://www.microsoft.com/en-us/windows/paint','Study brushes, shape tools, colour and layers; reproduce basic operations in the native raster workspace.','Free public overview; proprietary Paint internals are not ingested.')],
 'document':[('OpenLearn essay and report writing','https://www.open.edu/openlearn/mod/oucontent/view.php?id=4398&section=0','Interpret the task, plan a structure and revise for the intended reader.','Free course; provider licence applies.'),('LibreOffice Bookshelf','https://books.libreoffice.org/en/','Use styles and structured documents; study office guides alongside native document exercises.','Free online guides; individual document licences apply.')],
 'art':[('Blender tutorials','https://www.blender.org/support/tutorials/','Follow the official learning entry points for modelling, transforms and animation.','Free tutorial directory; linked offerings vary.'),('Blender manual','https://docs.blender.org/manual/en/latest/','Study scene organisation, meshes, shading, animation and rendering; compare concepts with the native workspace.','Free reference; provider licence applies.')],
 'music':[('Ableton Learning Music','https://learningmusic.ableton.com/','Practise beats, pitch, scales, chords, basslines, melody and song structure.','Free browser lessons; not a licence to redistribute music.'),('Ableton Learning Synths','https://learningsynths.ableton.com/','Interactive synthesis resource; requires a compatible JavaScript browser.','Free browser resource; lesson body not ingested here.'),('FL Studio manual','https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_workflow.htm','Separate patterns, instruments, arrangement and mixer routing; practise sequencing in the native studio.','Free documentation; FL Studio itself is proprietary.')],
 'game':[('Godot step by step','https://docs.godotengine.org/en/stable/getting_started/step_by_step/index.html','Progress from nodes and scenes to scripts and signals.','Free documentation.'),('GDQuest GDScript from zero','https://github.com/GDQuest/learn-gdscript','Interactive programming exercises support game logic fundamentals.','Free open-source course; preserve repository licences.'),('GDQuest free tutorials','https://www.gdquest.com/tutorial/godot/','Choose free lessons suited to the engine version and reproduce a small testable mechanic.','Free collection; paid courses are separate.')]}
def resources(kind):return [{'title':t,'url':u,'summary':s,'access':a,'ingested':'Original concise study note and source metadata, not the complete course'} for t,u,s,a in RESOURCES.get(kind,[])]

from .platform_trainer import PLATFORMS
RESOURCES["platform"]=[(name+" system reference",url,note,"Public reference; proprietary SDKs and restricted material are not imported.") for name,(url,note,command) in PLATFORMS.items()]

from .tech_industry import SOURCES as INDUSTRY_SOURCES
RESOURCES["industry"]=[(r["title"],r["url"],r["note"],"Public source overview; source material retains its own terms.") for r in INDUSTRY_SOURCES]

from .finance_industry import SOURCES as FINANCE_SOURCES
RESOURCES["finance"]=[(r["title"],r["url"],r["note"],"Public reference; source terms apply.") for r in FINANCE_SOURCES]

from .mustard_seed import SOURCES as MUSTARD_SOURCES
RESOURCES['belief-learning']=[(r['title'],r['url'],r['summary'],'Source-linked study; provider terms apply.') for r in MUSTARD_SOURCES]

RESOURCES['reasoning']=[
 ('Python CSV reference','https://docs.python.org/3/library/csv.html','Structured data, quoting, readers and writers.','Public official documentation; source terms apply.'),
 ('Python statistics reference','https://docs.python.org/3/library/statistics.html','Statistical summaries and numeric interpretation.','Public official documentation; source terms apply.'),
 ('scikit-learn model evaluation','https://scikit-learn.org/stable/modules/model_evaluation.html','Independent evaluation, metrics and model selection.','Public official documentation; source terms apply.')]
RESOURCES['humanitarian']=[
 ('UNHCR humanitarian principles','https://emergency.unhcr.org/protection/protection-principles/humanitarian-principles','Humanity, need-based provision and protection of affected people.','Public guidance; source terms apply.'),
 ('WHO AI ethics and governance','https://www.who.int/publications/i/item/9789240029200','Public benefit, accountability and human welfare in AI use.','Public guidance; source terms apply.')]

RESOURCES['causality']=[('NIST experimental design','https://www.itl.nist.gov/div898/handbook/pri/section3/pri33.htm','Compare factors and outcomes through designed experiments.','Public primary guidance.')]
RESOURCES['language']=[('Unicode standard overview','https://www.unicode.org/standard/standard.html','Character encoding, text representation and language processing.','Public primary reference.')]
RESOURCES['measurement']=[('NIST measurement uncertainty','https://www.nist.gov/pml/nist-technical-note-1297','Measurement models, uncertainty and reported results.','Public primary guidance.')]
RESOURCES['verification']=[('Python unit testing','https://docs.python.org/3/library/unittest.html','Test fixtures, assertions, failure reporting and independent expected results.','Public official documentation.')]
RESOURCES['ethics']=[('ICRC fundamental principles','https://www.icrc.org/en/our-fundamental-principles','Humanity, dignity, aid and accountability.','Public primary guidance.')]
RESOURCES['resource-design']=[('Fuller design science','https://www.bfi.org/about-fuller/big-ideas/design-science/design-science-primer/','Whole-system design and resource responsibility.','Public primary perspective; evaluate proposed outcomes independently.')]
