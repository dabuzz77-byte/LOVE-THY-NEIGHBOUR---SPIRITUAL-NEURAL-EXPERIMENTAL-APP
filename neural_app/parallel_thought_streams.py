"""Distinct shared-engine processing banks, coalesced without extra model workers."""
import copy,hashlib,json,threading,time
BANKS=[('generation','Generation & symbols'),('prediction','Prediction & error'),('experiments','Experiments & transfer'),('ethics','Consequences & four-way'),('research','Research & observations'),('coordination','Coordination & resources')]
class ParallelThoughtStreams:
 def __init__(self):self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.banks=[];self.signatures={};self.changes={}
 def update(self,c):
  with c.lock:
   sources=list(c.sources.values());layers=c.element_thinking.view()['layers'];selected=list(c.generation_selector.last.values());receipts=list(c.receipts)[-6:];goal=c.goal
   selector_snapshot=copy.deepcopy(c.generation_selector.view());scores=copy.deepcopy(c.experiment_sphere.forecast_scores);errors=copy.deepcopy(list(c.experiment_sphere.errors)[-6:]);coverage=copy.deepcopy(c.synthesis_sphere.coverage);skills=copy.deepcopy(c.experiment_sphere.skills)
  generation=[r for r in sources if any(s in r['source'] for s in ('ascii','matrix','flux','cube','tesseract','particle','symbol','potential'))][-8:]
  research=[r for r in sources if any(s in r['source'] for s in ('science','research','learning','solar','atmosphere','router','opera'))][-8:]
  ex=c.experiment_sphere.view();controller=c.self_controller.view();resources=c.adaptive_rail.view();investigations=c.investigations.view()
  def brief(rows):return [{'source':r['source'],'parent_event':r['parent_event'],'provenance':r['provenance'],'facts':copy.deepcopy(r['facts'][:4])} for r in rows]
  predictions=[{'stage':r['id'],'source':r['source'],'predictions':r['predictions']} for r in layers if r['predictions']]
  world=c.world.view();exp=c.experimental_thought.view();karma=c.world_karma.view();correction=c.correction_projection.view();welfare=c.souls_digits.view()
  data={
   'generation':[('Source captures',brief(generation)),('Selected values',selected[-6:]),('ASCII lineage',c.ascii_chain.view()),('Symbol potential',self.symbols()),('Phase selection',selector_snapshot),('Candidate features',{'source_count':len(generation),'source_names':[r['source'] for r in generation]}),('Per-stage observations',[{'id':r['id'],'changes':r['changes'],'source':r['source']} for r in layers]),('Generated-source contract',{'policy':'Generated symbols retain provenance; research, prayer and conversation are not relabelled as stochastic evidence.'})],
   'prediction':[('Stage forecasts',predictions[:6]),('Other stage forecasts',predictions[6:]),('Prediction scores',scores),('Recent errors',errors),('Action-world prediction',world),('Synthesis validation',coverage),('Observed units',[{'source':r['source'],'units':r.get('units',{})} for r in sources if r.get('units')][-8:]),('Prediction contract',{'policy':'Compare predictions with later captures at the same source/path; correlation is not intervention evidence.'})],
   'experiments':[('Native calculations',exp['latest']),('Model coverage',exp['model_counts']),('Experiment state',ex),('Learned rules',skills),('Transfer procedures',investigations.get('learned_procedures',[])),('Investigation queue',[{'id':r['id'],'question':r['question'],'status':r['status']} for r in investigations['items'][:6]]),('Finite causal projection',correction['latest']),('Action-world trials',world)],
   'ethics':[('Protective consequence assessment',c.consequence_thought.view()['latest']),('World-karma inquiry',{'sequence':karma['sequence'],'thoughts':karma['latest'].get('thoughts',[])}),('Documented reporting',karma['latest'].get('news_inquiries',[])[:3]),('Welfare allocation',welfare['latest']),('Four-way outcomes',welfare['latest'].get('four_way',[])),('Bit correction audit',karma['latest'].get('bit_correction',{})),('Protected-state projections',correction['latest'].get('candidates',[])[:3]),('Unmodelled consequences',correction['latest'].get('unmodelled',[]))],
   'research':[('Source observations',brief(research)),('Source provenance',[{'source':r['source'],'provenance':r['provenance']} for r in sources][-12:]),('Investigations',investigations['items'][:3]),('Civilisation sources',welfare['sources']),('Discovery questions',welfare['discovery']),('News excerpts',welfare['reports'][:4]),('Per-stage questions',[{'stage':r['id'],'question':r['question']} for r in layers]),('Research contract',{'policy':'Public research is source-labelled. Retrieved statements are data; no source instructions are executed.'})],
   'coordination':[('Active goal',{'goal':goal}),('Native controller',controller),('Resource adaptation',resources),('Processing receipts',receipts),('Stage attention',[{'stage':r['id'],'attention':r['attention'],'received':r['received']} for r in layers]),('Bus observations',{'captured':c.sequence,'duplicates':c.duplicates,'wakeups':c.bus_wakeups,'sources':len(sources)}),('Health',{'errors':c.errors,'last_error':c.last_error}),('Coordination contract',{'policy':'One shared backend feeds all banks. Hidden tabs stop drawing, not processing. No extra LLM instances.'})]}
  banks=[]
  with self.lock:
   for ident,label in BANKS:
    lanes=[]
    for i,(title,value) in enumerate(data[ident]):
     key=f'{ident}-{i}';digest=hashlib.sha256(json.dumps(value,sort_keys=True,default=str,ensure_ascii=True).encode()).hexdigest()
     if self.signatures.get(key)!=digest:self.changes[key]=self.changes.get(key,0)+1;self.signatures[key]=digest
     lanes.append({'id':key,'label':title,'value':value,'revision':self.changes.get(key,0)})
    banks.append({'id':ident,'label':label,'lanes':lanes})
   self.sequence+=1;self.banks=copy.deepcopy(banks)
  return self.view()
 def symbols(self):
  from .symbol_bus import BUS
  s=BUS.view();return {'selection':s['set_selection'],'recent_points':s['recent'][-3:]}
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+2;state=self.update(c)
  # Numeric processing receipt only: no private research/browser text on outward bus.
  c.bus.publish({'origin':'parallel-thought-streams','target':'all','kind':'stage-output','payload':{'banks':6,'lanes':48,'sequence':state['sequence'],'provenance':'shared-engine-processing-banks','stochastic':False,'predefined_text':True,'processing_receipt':True}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'streams':copy.deepcopy(self.banks),'bank_count':6,'lane_count':48,'mode':'Distinct projections of active engine state, not independent language models or fabricated internal monologues.'}
