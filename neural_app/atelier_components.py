"""Atelier's adapters share calculations without their old UDP/socket workers."""
import json,time,threading
from pathlib import Path
from .runtime import ROOT

def integrate(module,runtime):
 class SharedLocalBus:
  def __init__(self,engine,data):
   self.engine=engine;self.stop=threading.Event();self.clients={'shared-neural-core':time.monotonic()};self.rx=0;self.tx=0;folder=runtime.data/'sections'/'atelier';folder.mkdir(parents=True,exist_ok=True);self.path=folder/'shared-connection.json';self.path.write_text(json.dumps({'http_port':8797,'tcp_port':8798,'discovery_port':8799,'transport':'Neural App shared session'}))
  def close(self):self.stop.set()
 module.LocalBus=SharedLocalBus
 def loop(bus):
  now=time.monotonic()
  if not bus.pending.is_set() and now-getattr(bus,'last_shared',0)<5:return
  bus.last_shared=now;bus.pending.clear();packet=bus.engine.snapshot();result=runtime.engine('core',{'text':json.dumps(packet)[:4000]});receipt=runtime.component_result('atelier',{'source':'shared field adapter'},result)
  with bus.engine.lock:bus.engine.script_signal=max(-1,min(1,result.get('output',0)));bus.engine.script_at=now;bus.engine.script_samples+=1
  bus.tx+=1;bus.rx+=1;bus.status.update(flux='ACK received',observatory='Live');bus.log('SHARED','Integrated calculation receipt '+str(receipt))
 module.Bridge.loop=loop
 return module
