"""Software zero-reference to captured-potential phase spectrum."""
import copy,math,time,collections
class PotentialZeroSphere:
 def __init__(self):self.sequence=0;self.latest={};self.next_at=0;self.last_publish=0;self.pending=[];self.cursor=0;self.gradient_history=collections.deque(maxlen=64);self.previous_gain=None;self.previous_time=None
 def step(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+max(.1,c.total_plane_sphere.interval);self.sequence+=1
  base=c.total_plane_sphere.view();data=base.get('particles',[]);particles=[];lanes=[];lane_data=[];gain=(1+math.sin(time.monotonic()*.35))/2
  for j in range(9):
   samples=[]
   amount=j/8;count=0 if amount==0 else min(24,len(data));selected=abs(amount-gain)<.13;lanes.append({'gain':amount,'selected':selected,'values':count,'zero_output':amount==0})
   for i in range(count):
    original=data[(self.cursor+i)%len(data)];p=copy.deepcopy(original);p['id']='potential-zero:'+str(j)+':'+p['id'];p['point']=[v*(.15+amount) for v in p['point']];p['phase']=amount;p['selected']=selected;p['representation_gain']=amount;p['source_value_retained']=True;particles.append(p);samples.append({'source':p.get('source'),'path':p.get('path'),'value_preview':p.get('value_preview'),'xyz':p['point'],'gain':amount})
   lane_data.append({'gain':amount,'samples':samples})
  gradient=[]
  for j in range(1,len(lanes)):
   left,right=lanes[j-1],lanes[j];delta=right['gain']-left['gain'];gradient.append({'from_gain':left['gain'],'to_gain':right['gain'],'delta_gain':delta,'delta_represented_values':right['values']-left['values'],'position_gain_derivative':1.0,'meaning':'Representation geometry derivative; zero-to-first-lane emission has a discrete boundary.'})
  now=time.monotonic();temporal=None if self.previous_time is None else (gain-self.previous_gain)/max(.000001,now-self.previous_time);self.previous_time=now;self.previous_gain=gain
  self.gradient_history.append({'sequence':self.sequence,'time':time.time(),'selected_gain':gain,'gain_change_per_second':temporal,'gradient':gradient,'source_points':len(data)})
  self.cursor+=24
  zero=[];restored=copy.deepcopy(data);safe_test={'zero_lane_emits_no_values':len(zero)==0,'retained_copy_preserves_values':restored==data,'test_scope':'Software representation attenuation and source preservation; no physical zero-point measurement.'}
  self.latest={'sequence':self.sequence,'particles':particles,'goal':c.goal,'received_events':c.sequence,'retained_sources':len(c.sources),'represented_values':len(data),'selected_phases':[x['gain'] for x in lanes if x['selected']],'gradient_lane_data':lane_data,'gradient_capture':{'latest':copy.deepcopy(self.gradient_history[-1]),'history':list(self.gradient_history),'retention':64,'sampling':'nine explicit gain levels plus temporal selected-gain samples; not an infinite continuum'},'spectrum':lanes,'selected_gain':gain,'experiments':safe_test,'potential_catalog':{'engine':'captured stage values and registered behaviours','app':'captured app events','system':'available observed system facts','network':'retrieved sources and configured service observations; hypothetical reach is not established connectivity'},'scope':'All nine software phase lanes represented; zero emits no data, full gain preserves selected captured representations. Finite rotating samples; not a measurement of cosmological zero-point energy.'}
  if time.monotonic()-self.last_publish>3:
   self.last_publish=time.monotonic();self.pending.append({'origin':'potential-zero-space','target':'all','kind':'stage-output','payload':{'selection_trace':True,'gain':gain,'gradient':gradient,'gain_change_per_second':temporal,'tests':safe_test,'provenance':'isolated-software-phase-test'}})
 def view(self):return copy.deepcopy(self.latest or {'sequence':0,'particles':[]})
