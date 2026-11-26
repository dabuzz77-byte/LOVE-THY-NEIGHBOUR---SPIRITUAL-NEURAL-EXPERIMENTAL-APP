"""Small delay-coordinate polynomial readout with chronological evaluation."""
from collections import OrderedDict
import math

def features(a,b):return [1.,a,b,a*a,a*b,b*b]

def solve(matrix,vector,ridge=.001):
 n=len(vector);rows=[[float(matrix[i][j])+(ridge if i==j else 0.) for j in range(n)]+[float(vector[i])] for i in range(n)]
 for col in range(n):
  pivot=max(range(col,n),key=lambda i:abs(rows[i][col]));rows[col],rows[pivot]=rows[pivot],rows[col]
  scale=rows[col][col]
  if abs(scale)<1e-12:return [0.]*n
  rows[col]=[v/scale for v in rows[col]]
  for i in range(n):
   if i==col:continue
   scale=rows[i][col];rows[i]=[a-scale*b for a,b in zip(rows[i],rows[col])]
 return [row[-1] for row in rows]

class TemporalModels:
 def __init__(self):self.sources=OrderedDict()
 def observe(self,source,raw):
  values=[v/127.5-1 for v in bytes(raw[:1024])]
  if len(values)<96:return {'status':'insufficient-sample'}
  state=self.sources.setdefault(source,{'matrix':[[0.]*6 for _ in range(6)],'vector':[0.]*6,'weights':[0.]*6,'sum':0.,'count':0.,'captures':0})
  self.sources.move_to_end(source)
  while len(self.sources)>32:self.sources.popitem(last=False)
  prior=state['captures'];start=2 if prior else max(2,int(len(values)*.6))
  def update(begin,end):
   for i in range(begin,end):
    row=features(values[i-1],values[i-2]);target=values[i]
    for j in range(6):
     state['vector'][j]+=row[j]*target
     for k in range(6):state['matrix'][j][k]+=row[j]*row[k]
    state['sum']+=target;state['count']+=1
   state['weights']=solve(state['matrix'],state['vector'])
  if not prior:update(2,start)
  weights=state['weights'][:];mean=state['sum']/max(1,state['count']);loss=constant=persistence=0.
  for i in range(start,len(values)):
   predicted=max(-1.,min(1.,sum(a*b for a,b in zip(weights,features(values[i-1],values[i-2])))))
   loss+=(predicted-values[i])**2;constant+=(mean-values[i])**2;persistence+=(values[i-1]-values[i])**2
  n=len(values)-start;baseline=min(constant,persistence)/n;error=loss/n
  if prior:
   state['matrix']=[[v*.9 for v in row] for row in state['matrix']];state['vector']=[v*.9 for v in state['vector']];state['sum']*=.9;state['count']*=.9
   update(2,len(values))
  else:update(start,len(values))
  state['captures']+=1
  forecast=max(-1.,min(1.,sum(a*b for a,b in zip(state['weights'],features(values[-1],values[-2])))))
  return {'status':'cross-capture-evaluated' if prior else 'within-capture-heldout','prior_captures':prior,'test_samples':n,'model_mse':error,'mean_baseline_mse':constant/n,'persistence_baseline_mse':persistence/n,'gain_over_best_baseline':baseline-error,'relative_error_reduction':(baseline-error)/baseline if baseline>1e-12 else None,'forecast_normalized_byte':forecast,'feature_values':features(values[-1],values[-2]),'readout_coefficients':state['weights'][:],'evaluation_model_frozen':True,'prediction_before_current_test_training':True,'training_after_evaluation':True,'scope':'Software delay-coordinate polynomial readout of normalized byte amplitudes. First capture uses chronological training/test split; later captures use earlier-capture weights. Not a measurement of vacuum fluctuations or proof of consciousness.'}
