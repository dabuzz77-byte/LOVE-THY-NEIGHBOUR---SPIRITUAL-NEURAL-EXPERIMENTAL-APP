"""Tiny balanced computational waveform contributions; no audio playback."""
import json,math
from pathlib import Path
FREQUENCIES=(174,285,396,417,528,639,741,852,963)
class CoreModulators:
 def __init__(self):
  self.enabled=True;self.cmb_gain=.0001;self.ohm_gain=.0006;self.solfeggio_gain=.00005;self.ticks=0;self.cmb=[];self.source=None
  try:
   d=json.loads((Path(__file__).resolve().parents[1]/'assets/cmb_firas.json').read_text(encoding='utf-8'));rows=d.get('rows',[]);values=[float(row[1]) for row in rows];scale=max(abs(v) for v in values) or 1;self.cmb=[v/scale for v in values];self.source=d.get('source')
  except (OSError,ValueError,IndexError,TypeError):pass
 def configure(self,b):
  if 'enabled' in b:
   if type(b['enabled']) is not bool:raise ValueError('Modulator enabled must be boolean')
   self.enabled=b['enabled']
  for key,limit in [('cmb_gain',.002),('ohm_gain',.005),('solfeggio_gain',.001)]:
   if key in b:
    value=float(b[key])
    if not math.isfinite(value) or value<0:raise ValueError('Use finite nonnegative modulation weights')
    setattr(self,key,min(limit,value))
 def sample(self,depth=0):
  self.ticks+=1;t=self.ticks/8000.;cmb=self.cmb[(self.ticks-1)%len(self.cmb)] if self.cmb else 0;ohm=(math.sin(math.tau*136.1*t)+.3*math.sin(math.tau*272.2*t))/1.3;solf=sum(math.sin(math.tau*f*t) for f in FREQUENCIES)/len(FREQUENCIES);raw=self.cmb_gain*cmb+self.ohm_gain*ohm+self.solfeggio_gain*solf;raw=raw if self.enabled else 0
  return {'enabled':self.enabled,'cmb_component':self.cmb_gain*cmb if self.enabled else 0,'ohm_component':self.ohm_gain*ohm if self.enabled else 0,'solfeggio_component':self.solfeggio_gain*solf if self.enabled else 0,'positive':raw,'negative':-raw,'applied':raw*(1 if depth%2==0 else -1),'cmb_gain':self.cmb_gain,'ohm_gain':self.ohm_gain,'solfeggio_gain':self.solfeggio_gain,'frequencies_Hz':list(FREQUENCIES),'cmb_source':self.source,'cmb_kind':'archival FIRAS spectral envelope; not live radiation','ohm_kind':'synthetic Ohm-like harmonic reference; not a recorded chant','role':'tiny mirrored route/position bias; explicit classifications and action permissions unchanged','sample_clock_Hz':8000,'sample_index':self.ticks,'audio_playback':False}
