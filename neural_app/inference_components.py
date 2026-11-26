"""Inference engines use direct resident objects instead of worker processes."""
import importlib,json,time,types
from pathlib import Path
from .runtime import ROOT,clean

def initialize(module,runtime,host=None):
 module.APPS=ROOT/'preserved'/'sources'
 package=module.__package__;load=lambda name:importlib.import_module(package+'.'+name)
 source=Path(module.__file__).parent
 from .section_storage import section_data
 root=runtime.data/'sections'/'inference'
 section_data(runtime,'inference/data',source/'data')
 for name in ('catalog.json','manuscript.txt'):
  destination=root/name
  if not destination.exists():destination.write_bytes((source/name).read_bytes())
 module.DATA=root/'data';module.DB=module.DATA/'observatory.sqlite3'
 resident=load('resident_engines').ResidentEngines(root)
 def flux(payload):return runtime.engine('flux',{'text':str(payload)[:4000]})
 def publish(topic,payload):
  recorded=module.event(topic,payload)
  if host:
   rt=host.adapter('observatory')[2]['controller'];rt.publish(topic,payload)
  return {'receipt':runtime.record('inference:'+topic,{},clean(payload),0),'status':'sent_unconfirmed','shared_process':True,'event':recorded['id']}
 module.bus=types.SimpleNamespace(send=publish);module.flux=flux
 module.obs_request=lambda path,data=None:host.invoke('observatory',path,data) if host else runtime.snapshot(False) if data is None else publish(path,data)
 module.autonomous=load('autonomous').AutoRuntime(root,module.CAT,module.event,module.obs_request)
 auto=module.autonomous;auto.status='shared resident engines ready';auto.settings['web_enabled']=False;auto.settings['bus_enabled']=True
 def engine_tick():
  if not auto.settings['enabled']:return
  with auto.db() as c:row=c.execute('SELECT * FROM inputs WHERE status="pending" ORDER BY id LIMIT 1').fetchone()
  if not row:return
  item=dict(row);envelope={'id':item['id'],'source':item['source'],'title':item['title'],'text':item['text'],'data':json.loads(item['data'])}
  result=resident.process(envelope)
  with auto.db() as c:
   c.execute('INSERT INTO executions(input_id,trigger,created,result) VALUES(?,?,?,?)',(item['id'],'shared_input',time.time(),json.dumps(result)))
   c.execute('UPDATE inputs SET status="complete",passes=passes+1 WHERE id=?',(item['id'],))
  auto.engine_rows={m['id']:m for m in result['engines']};auto.last_output=result;auto.status='shared resident engines ready'
 auto.engine_loop=engine_tick
 def source_run(req):
  from .capture_output import redirect_stdout
  import io
  runner=load('runner');output=io.StringIO();results=[]
  try:
   definition=next((m for m in resident.catalog if m['id']==req.get('id')),None)
   if definition is None:raise ValueError('Unknown built-in inference module')
   namespace=dict(vars(runner));namespace['__name__']='__main__'
   with redirect_stdout(output):
    exec(compile(definition['source'],'manuscript:'+str(definition['line']),'exec'),namespace)
    target=namespace[definition['name']]
    if definition['kind']=='class':
     target=target(**runner.decode(req.get('init',{})));allowed={m['name'] for m in definition['methods'] if not m['name'].startswith('_')}
     calls=req.get('calls',[{'method':req['method'],'args':req.get('args',{})}] if req.get('method') else [])
     for call in calls:
      if call['method'] not in allowed:raise ValueError('Choose a listed public method')
      results.append({'method':call['method'],'result':getattr(target,call['method'])(**runner.decode(call.get('args',{})))})
     state={k:v for k,v in vars(target).items() if not any(s in k.lower() for s in ('secret','key','password'))}
    else:results=target(**runner.decode(req.get('init',req.get('args',{}))));state={}
   result={'ok':True,'results':results,'state':state,'stdout':output.getvalue(),'basis':'Executed retained source in the shared process','shared_process':True}
   result=json.loads(json.dumps(result,default=runner.encode,allow_nan=False))
  except Exception as error:result={'ok':False,'error':type(error).__name__+': '+str(error),'results':results,'stdout':output.getvalue(),'shared_process':True}
  publish('engine.result',result);return result

 module.source_run=source_run
 module.prompt_loop=load('prompt_loop').PromptLoop(root,module.event,publish,flux,source_run,module.CAT)
 module.federation=load('federation').Federation(root,auto,publish,flux)
 if host:
  original_refresh=module.federation.refresh_catalog
  def refresh_catalog():
   original_refresh()
   for row in module.federation.catalog:
    sections=[p['id'] for p in host.panels if str(p['entry']).replace('\\','/').split('/')[0]==row['name']]
    row['section_ids']=sections;row['connection']='Built-in shared sections: '+', '.join(sections) if sections else 'App-owned calculation library'
  module.federation.refresh_catalog=refresh_catalog;refresh_catalog()
 module.native_research=load('native_research').NativeResearch(root,module.federation,module.event)
 # Preserve original background behaviours on bounded, shared task lanes.
 from .inference_scheduler import InferenceScheduler
 scheduler=InferenceScheduler(module,runtime,host,engine_tick,publish)
 module._shared_tick=scheduler.pulse
 module._shared_scheduler=scheduler
 return module
