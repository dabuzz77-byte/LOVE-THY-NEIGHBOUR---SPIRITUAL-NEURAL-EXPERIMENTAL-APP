"""Hydrogen's journal is local; delivery uses the common runtime."""
import importlib,json,time,types
from pathlib import Path
from .runtime import ROOT,clean

def integrate(module,runtime):
 from .engines.realistic_scenes import RealisticSceneRenderer
 module.SceneRenderer=RealisticSceneRenderer
 mesh=importlib.import_module(module.__package__+'.mesh_bus')
 class SharedMeshServer:
  def __init__(self,data_dir,port=0,broadcast_port=8799,storage=None):
   self.data=Path(data_dir);self.data.mkdir(parents=True,exist_ok=True);self.ledger=mesh.Ledger(self.data/'mesh.sqlite3',**(storage or {}));self.port=8797;self.udp=types.SimpleNamespace(port=8798,broadcast_port=8799);self.connection=self.data/'shared-connection.json';self.connection.write_text(json.dumps({'url':'http://127.0.0.1:8797','tcp_port':8798,'discovery_port':8799,'transport':'shared Neural App session'}))
  def close(self):pass
 module.BusServer=SharedMeshServer
 if not hasattr(module.Runtime,'_shared_original_init'):module.Runtime._shared_original_init=module.Runtime.__init__
 def initialize(rt,*args,**kwargs):
  module.Runtime._shared_original_init(rt,*args,**kwargs)
  rt.config['apps_root']=str(ROOT/'preserved'/'sources')
 module.Runtime.__init__=initialize
 for name in ('process','generate'):
  saved='_shared_original_'+name
  if not hasattr(module.Runtime,saved):setattr(module.Runtime,saved,getattr(module.Runtime,name))
  original=getattr(module.Runtime,saved)
  def calculation(rt,*args,_original=original,_name=name,**kwargs):
   result=_original(rt,*args,**kwargs);receipt=runtime.component_result('hydrogen',{'source':_name},result)
   if isinstance(result,dict):result['shared_receipt']=receipt
   return result
  setattr(module.Runtime,name,calculation)
 bridge_module=importlib.import_module(module.__package__+'.bridges')
 def start(bridge):bridge.status='Integrated · shared calculations';bridge.thread=None
 bridge_module.Bridge.start=start
 return module

def tick(controller,runtime):
 for bridge in controller.rt.bridges:
  if not bridge.enabled:continue
  for event in bridge.pending():
   text=str(event.get('data',''))[:2000]
   try:
    section='flux' if bridge.name=='fluxbus' else 'pipeline';result=runtime.engine('flux',{'text':text}) if section=='flux' else runtime.pipeline({'text':text[:200],'sections':[]})
    runtime.component_result('hydrogen',{'source':bridge.name,'message':event['id']},result);bridge.sent+=1;bridge.received+=1;bridge.status='Integrated · result received';bridge.advance(event,'shared calculation complete')
   except Exception as e:bridge.failures+=1;bridge.status=str(e);bridge.advance(event,'error')
   break
