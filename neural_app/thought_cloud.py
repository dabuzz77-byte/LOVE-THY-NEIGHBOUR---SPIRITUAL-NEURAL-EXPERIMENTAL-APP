"""Whole-app structured thought cloud, including silence and tiny waveform bias."""
import copy,math,random,threading,time
from .core_modulators import CoreModulators
from .action_ethics import study_frame
class ThoughtCloud:
 def __init__(self):
  self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.frame={};self.rng=random.Random();self.wave=CoreModulators();self.wave.configure({'cmb_gain':.0001,'solfeggio_gain':.0002,'ohm_gain':.0006});self.snippet_at=time.monotonic()+20;self.snippet_until=0;self.snippet_gain=1.;self.snippet_source=None
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  self.next_at=now+2;wall=time.time()
  with c.lock:sources=copy.deepcopy(list(c.sources.values()));layers=c.element_thinking.view()['layers'];goal=c.goal
  records=[]
  for source in sources:
   if source['source']=='overall-thought-cloud':continue
   facts=source.get('facts',[]);fact=facts[self.sequence%len(facts)] if facts else {};age=max(0,wall-source.get('time',wall));value=fact.get('value');number=type(value) in (int,float) and math.isfinite(value)
   records.append({'kind':'observation' if age<30 else 'inactivity-review','source':source['source'],'parent_event':source.get('parent_event'),'path':fact.get('path',[]),'value_preview':str(value)[:160],'seconds_since_event':round(age,2),'question':'What can be inferred and independently checked from this observation?' if age<30 else 'No recent event observed: should this source wait, refresh or be checked against its expected cadence?','candidate_interpretations':['Retain source-labelled observation','Check a competing explanation','Seek missing context'],'next_test':'Compare the next numeric capture with the recorded stage forecast.' if number else 'Check provenance, relevance and supported meaning before using this material.','meaning_of_silence':'Age threshold is a study cue, not evidence of an outage or hidden activity.'})
  with c.active_thought.lock:thought={key:{field:copy.deepcopy(value.get(field)) for field in ('focus','checks','alternatives','next_test','status')} for key,value in c.active_thought.stages.items()}
  for row in layers:
   review=thought.get(row['id'],{})
   records.append({'kind':'registered-thinking-layer','source':row['id'],'path':['thinking',row['id']],'parent_event':row.get('parent_event'),'question':row['question'],'status':row['status'],'received':row['received'],'predictions':row['predictions'],'review':{key:review.get(key) for key in ('focus','checks','alternatives','next_test','status')},'selection':c.potential_selection.stage(row['id']),'ethical_study':study_frame(row['id'],self.sequence)})
  if now>=self.snippet_at:
   self.snippet_until=now+self.rng.uniform(2,4);self.snippet_at=self.snippet_until+self.rng.uniform(25,85);self.snippet_gain=self.rng.uniform(.8,1.2);mods=[r['source'] for r in sources if any(w in r['source'] for w in ('modulat','audio','wave','noise'))];self.snippet_source=self.rng.choice(mods) if mods else 'configured core waveform references'
  active=now<self.snippet_until;sample=self.wave.sample();snippet_values=[fact['value'] for row in sources if row['source']==self.snippet_source for fact in row.get('facts',[])[:16] if type(fact.get('value')) in (int,float) and math.isfinite(fact['value'])];snippet_bias=(sum(max(-1,min(1,v)) for v in snippet_values)/len(snippet_values))*.00001*self.snippet_gain if active and snippet_values else 0;bias=sample['applied']*(self.snippet_gain if active else 1)+snippet_bias;particles=[]
  for i,record in enumerate(records[:192]):
   y=1-2*(i+.5)/max(1,min(192,len(records)));r=math.sqrt(max(0,1-y*y));angle=i*2.39996323
   particles.append({'id':'thought-cloud:'+str(i),'point':[r*math.cos(angle)+bias,y-bias,r*math.sin(angle)+bias],'phase':1.,'autonomy':0.,'selected':record.get('kind')!='inactivity-review','expression_type':record['kind'],'symbol':'?' if record['kind']=='inactivity-review' else '◇','value_preview':record['question'][:120],'source':record['source'],'path':record['path'],'parent_event':record.get('parent_event'),'record':record})
  self.sequence+=1;frame={'sequence':self.sequence,'particles':particles,'retained_sources':len(sources),'represented_values':len(particles),'received_events':self.sequence,'goal':goal,'selected_phases':[1.],'thought_trace':records[:192],'registered_thinking_types':[row['id'] for row in layers],'modulation':{**sample,'solfeggio_gain':.0002,'snippet_active':active,'snippet_gain':self.snippet_gain,'snippet_source':self.snippet_source,'snippet_observed_samples':len(snippet_values),'snippet_computational_bias':snippet_bias,'seconds_until_snippet':max(0,self.snippet_at-now),'remaining_snippet_seconds':max(0,self.snippet_until-now),'interval_policy':'Self-varied 25–85 seconds between 2–4 second snippets, gain 0.8–1.2','role':'Tiny coordinate bias; not a factual or ethical verdict'},'scope':'Structured observations, candidate interpretations, forecasts and next checks from retained app sources and registered thought stages. Silence is represented explicitly; this is not a fabricated private inner monologue.'}
  with self.lock:self.frame=frame
  c.bus.publish({'origin':'overall-thought-cloud','target':'all','kind':'stage-output','payload':{'cycle':self.sequence,'thought_records':len(particles),'inactive_sources':sum(r['kind']=='inactivity-review' for r in records),'provenance':'structured-whole-app-thought-cloud','predefined_text':True,'stochastic':False,'processing_receipt':True}})
 def view(self):
  with self.lock:return copy.deepcopy(self.frame) if self.frame else {'sequence':0,'particles':[]}
