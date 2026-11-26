"""Causal same-target feature comparison; model choice precedes current test."""
from collections import OrderedDict
from .ambient_temporal_models import solve

NAMES=('raw-polynomial','delay-memory','cosmic-simulated-memory')
DIMS=(6,6,8)

def rows(raw):
 values=[v/127.5-1 for v in bytes(raw[:513])];hydrogen=star=earth=0.;out=[]
 for i in range(1,len(values)):
  u=values[i-1];hydrogen=.5*hydrogen+.5*u;star=.85*star+.15*hydrogen;earth=.95*earth+.05*star
  if i<8:continue
  b=values[i-2];out.append((values[i],[[1.,u,b,u*u,u*b,b*b],[1.,u,b,values[i-4],values[i-8],u*values[i-4]],[1.,u,hydrogen,star,earth,hydrogen*hydrogen,hydrogen*star,star*earth]],u))
 return out

def model(d):return {'matrix':[[0.]*d for _ in range(d)],'vector':[0.]*d,'weights':[0.]*d}

def train(models,data):
 for target,features,_ in data:
  for m,x in zip(models,features):
   for j,a in enumerate(x):
    m['vector'][j]+=a*target
    for k,b in enumerate(x):m['matrix'][j][k]+=a*b
 for m in models:m['weights']=solve(m['matrix'],m['vector'])

def predict(weights,features):return max(-1.,min(1.,sum(a*b for a,b in zip(weights,features))))

class RepresentationLearning:
 def __init__(self):self.sources=OrderedDict()
 def observe(self,source,raw):
  captured=bytes(raw[:512]);data=rows(captured)
  if len(data)<88:return {'status':'insufficient-sample'}
  state=self.sources.setdefault(source,{'models':[model(d) for d in DIMS],'captures':0,'losses':{name:0. for name in (*NAMES,'mean','persistence')},'tested':0,'sum':0.,'count':0.})
  self.sources.move_to_end(source)
  while len(self.sources)>32:self.sources.popitem(last=False)
  prior=state['captures'];chosen=min(state['losses'],key=lambda name:(state['losses'][name]/max(1,state['tested']),name)) if prior else 'mean'
  cut=0 if prior else int(len(data)*.6)
  if not prior:
   train(state['models'],data[:cut]);state['sum']=sum(r[0] for r in data[:cut]);state['count']=cut
  mean=state['sum']/max(1,state['count']);losses={name:0. for name in state['losses']};frozen=[m['weights'][:] for m in state['models']]
  for target,features,previous in data[cut:]:
   predictions={name:predict(w,x) for name,w,x in zip(NAMES,frozen,features)};predictions.update(mean=mean,persistence=previous)
   for name,value in predictions.items():losses[name]+=(value-target)**2
  tested=len(data)-cut;mse={name:value/tested for name,value in losses.items()};baseline=min(mse['mean'],mse['persistence']);selected_gain=(baseline-mse[chosen])/baseline if baseline>1e-12 else None
  for name in losses:state['losses'][name]=state['losses'][name]*.8+losses[name]
  state['tested']=state['tested']*.8+tested
  if prior:
   for m in state['models']:
    m['matrix']=[[v*.9 for v in row] for row in m['matrix']];m['vector']=[v*.9 for v in m['vector']]
   state['sum']*=.9;state['count']*=.9
  training=data if prior else data[cut:];train(state['models'],training)
  state['sum']+=sum(r[0] for r in training);state['count']+=len(training);state['captures']+=1
  next_choice=min(state['losses'],key=lambda name:(state['losses'][name]/state['tested'],name))
  next_features=rows(captured+b'\0')[-1][1]
  forecast=state['sum']/max(1,state['count']) if next_choice=='mean' else captured[-1]/127.5-1 if next_choice=='persistence' else predict(state['models'][NAMES.index(next_choice)]['weights'],next_features[NAMES.index(next_choice)])
  return {'forecast_normalized_byte':forecast,'status':'cross-capture-evaluated' if prior else 'chronological-heldout','prior_captures':prior,'selected_before_test':chosen,'next_selected':next_choice,'test_samples':tested,'same_prediction_target':True,'no_future_input_features':True,'prediction_target':'next normalized byte in the original captured source','mse':mse,'selected_gain_over_best_baseline':selected_gain,'cosmic_gain_over_raw':(mse[NAMES[0]]-mse[NAMES[2]])/mse[NAMES[0]] if mse[NAMES[0]]>1e-12 else None,'evaluation_weights_frozen':True,'scope':'Software feature-map ablation. The cosmic-labelled model is a three-timescale leaky-memory simulation driven only by earlier source bytes. It is not a physical zero-point, atom, star or Earth sensor, and an improvement does not establish cosmic causation.'}
