"""Per-section native observation, prediction and attention layers."""
import collections,copy,math,time
from .mind_workspace import terms
SPECS={
 'expressioncanvas':('Experimental expression canvas','expression-canvas,potential-selection','Which isolated visual operators communicate current observations and preserve provenance?'),
 'financeindustry':('Financial sector and provision','financial-industry,source-study','Which financial dependencies support daily provision, and which conceal exclusion or exploitation?'),
 'techindustry':('Technology industry ecosystem','tech-industry,source-study','Which source-linked infrastructure dependencies and access changes affect end users?'),
 'platformtrainer':('Operating systems and consoles','platform-trainer','Which supported platform plans preserve informed owner choice, dependencies and result checks?'),
 'emailtrainer':('Email and etiquette practice','email-etiquette-trainer','Which drafts meet audience, clarity, honesty, privacy and four-way consequence checks?'),
 'painttrainer':('Paint drawing practice','paint-trainer','Which drawing parameters improve fixture agreement and preserve raster contracts?'),
 'periodicstudy':('Periodic table atomic study','periodic-study,scientific','Which atomic calculations match their stated model, units and independently sourced measurements?'),
 'documenttrainer':('Formal document trainer','document-trainer','Which document structures and revisions improve clarity and completeness?'),
 'arttrainer':('3D art trainer','art-trainer','Which scene transformations preserve geometric invariants and support the intended composition?'),
 'musictrainer':('Sound and music trainer','music-trainer','Which sequencing and sound transformations meet timing and signal contracts?'),
 'gametrainer':('Game creation trainer','game-trainer','Which gameplay rules produce reachable goals and predictable state transitions?'),
 'worldknowledge':('Industry society geography','world-knowledge,public-learning','Which sources and contextual checks improve understanding of welfare and dependencies?'),

 'softwaretheory':('Software library / theory prediction experiment','software-theory,public-learning,scientific','Which proposed explanations survive independent checks and improve useful software?'),
 'ethicalprojection':('Affected beings / ethical consequences','ethical-projection,world-karma','What happens to affected beings under action, delay, correction and repair?'),
 'soulsdigits':('Souls over digits / civilisation','souls-digits,public-learning,world-karma','Do monetary and institutional measures improve welfare, or conceal avoidable harm?'),
 'correctionprojection':('Four-way / bit correction projection','correction-projection,consequence-thought','Which proposed changes improve defined outcomes without violating protected services?'),
 'worldkarma':('World karma / consequence','world-karma,consequence-thought','How do needs, loss, survival, institutions and choices affect welfare, including digital consequences?'),
 'sciencelibrary':('Science library / Tesla research','science-library,public-learning,tesla','Which refreshed research sources or historical claims require a discriminating experiment?'),
 'symbolpotential':('Unicode potential bus','symbol-potential,native-matrix,ascii,unicode','Which generated character selections preserve origin and satisfy the current format contract?'),
 'expressionsphere':('Whole-engine expression sphere','intelligence-expression-sphere,cognitive-circuit','Which expressions preserve input lineage across phase and autonomy states?'),
 'particleflux':('Ambient field','ambient,particle,stochastic','Which generated features remain predictable across later captures?'),
 'ambientcombined':('Combined 3D cursor','ambient-combined,combined-cursor','Which combined paths preserve their source information?'),
 'atmosphere':('Global atmosphere','atmosphere,weather,ambience-dual-rail','Which measured values are changing, with what units and freshness?'),
 'animalcams':('Animal live cams','animal,webcam,zoo','Which supplied observations are available, rather than inferred from an unanalysed video?'),
 'solarobservatory':('Solar observatory','solar,sun,space-weather','Which source-labelled solar measurements changed?'),
 'routermonitor':('Router and Wi-Fi','router,wifi,wi-fi','Which connection measurements depart from their recent baseline?'),
 'systemfractal':('System fractal','system-fractal,process,os-learning','Which resource measurements explain current workload?'),
 'ambientflowsummary':('Ambient flow summary','ambient,parallel,flow','Which chain contributions are fresh, repeated or missing?'),
 'flowbackbone':('Flow backbone','flow-backbone,backbone','Which observer or action result confirms processing?'),
 'logiccube':('Flux cubes','logic-cube,flux,particle-flux','Which supplied state changes survive verification?'),
 'omnicube':('Omni Cube','omni-cube','Which incoming observations belong in current working memory?'),
 'tesseracts':('Tesseracts','tesseract','Which branch predictions match later results?'),
 'potentialsphere':('Potential sphere','potential-sphere,atomic','Which proposed experiments improve learned outcomes?'),
 'expressionfield':('Expression field','expression-field,thought-expression,recursive-manifest','Which expressed candidates retain provenance and task relevance?'),
 'recursivemind':('Recursive mind core','recursive-core,cognitive-circuit','Which investigation advances the active goal?'),
 'nativematrix':('Native intelligence','native-matrix,bit-command,native-trainer','Which native operation predicts or completes useful work?'),
 'generationthought':('Generation thought core','generation-cognition,cognitive-circuit,grounded-reasoner,native-workbench','Which candidates become verified procedures or better predictions?')}
class ElementThinking:
 def __init__(self,saved=None):
  self.layers={};saved=saved or {}
  for key,(title,aliases,question) in SPECS.items():
   self.layers[key]={'id':key,'title':title,'question':question,'received':0,'changes':0,'goal':'','attention':0,'status':'waiting for relevant input','source':None,'parent_event':None,'observations':[],'predictions':{},'lessons':collections.deque(saved.get(key,{}).get('lessons',[])[-8:],maxlen=8),'models':saved.get(key,{}).get('models',{}),'digests':{},'updated':None}
 def observe(self,row,event):
  p=event.get('payload') or {};p=p if isinstance(p,dict) else {};explicit=p.get('thinking_layers',[]);explicit=explicit if isinstance(explicit,list) else []
  topic=(row['source']+' '+str(p.get('source',''))+' '+str(p.get('section',''))).lower()
  user_input=event.get('kind')=='input' and not p.get('stochastic')
  for key,(_,aliases,_) in SPECS.items():
   if not (key in explicit or 'all' in explicit or user_input or event.get('target')=='all' or event.get('target')==key or any(alias in topic for alias in aliases.split(','))):continue
   layer=self.layers[key];layer['received']+=1
   if layer['digests'].get(row['source'])==row['digest']:continue
   layer['digests'][row['source']]=row['digest']
   while len(layer['digests'])>64:layer['digests'].pop(next(iter(layer['digests'])))
   layer.update(changes=layer['changes']+1,source=row['source'],parent_event=row['parent_event'],updated=time.time(),status='observed; awaiting subsequent evidence')
   layer['observations']=copy.deepcopy(row['facts'][:12]);predictions={}
   for fact in row['facts']:
    if type(fact['value']) not in (int,float):continue
    value=fact['value']
    if abs(value)>1e15:continue
    path='/'.join(map(str,fact['path']));identity=row['source']+':'+path
    model=layer['models'].setdefault(identity,{'last':None,'delta':0.,'tested':0,'last_error':0.,'trend_error':0.})
    if model['last'] is not None:
     a=abs(value-model['last']);b=abs(value-(model['last']+model['delta']));model['tested']+=1;model['last_error']+=a;model['trend_error']+=b
     if model['tested']==8:layer['lessons'].append({'source':row['source'],'path':path,'finding':'compare persistence and linear-trend forecasts','tested':8,'persistence_MAE':model['last_error']/8,'trend_MAE':model['trend_error']/8,'scope':'Observed numeric series only; not a causal proof'})
     model['delta']=value-model['last']
    model['last']=value
    method='trend' if model['tested']>=8 and model['trend_error']<model['last_error'] else 'persistence'
    predictions[path]={'next':value+(model['delta'] if method=='trend' else 0),'method':method,'tested':model['tested'],'source':row['source'],'validation':'compare with next capture at same source/path'}
    if len(predictions)>=8:break
   while len(layer['models'])>64:layer['models'].pop(next(iter(layer['models'])))
   layer['predictions']=predictions
 def focus(self,goal):
  q=terms(goal)
  for layer in self.layers.values():
   layer['goal']=goal;overlap=len(q&terms(layer['title']+' '+str(layer['observations'])))
   layer['attention']=overlap/max(1,len(q))+(0.1 if layer['updated'] and time.time()-layer['updated']<10 else 0)
 def checkpoint(self):return {key:{'models':copy.deepcopy(row['models']),'lessons':list(row['lessons'])} for key,row in self.layers.items()}
 def view(self,key=None):
  def clean(row):return {k:copy.deepcopy(list(v) if k=='lessons' else v) for k,v in row.items() if k not in ('models','digests')}
  if key:
   if key not in self.layers:raise ValueError('Choose a registered Intelligence Engine element')
   return clean(self.layers[key])
  return {'layers':[clean(v) for v in self.layers.values()],'count':len(self.layers),'scope':'Native per-element evidence and numeric prediction layers; no separate language models or invented observations'}
