"""Java calculation/drawing libraries in the existing Python process.

Controllers were converted from standalone frames to windowless section models.
Controls are returned as data for Neural App's DOM; custom drawing code emits live SVG vectors.
"""
import json,threading,shutil,sys
from pathlib import Path
from .runtime import ROOT

sys.path.insert(0,str(ROOT/'vendor-java'))
LOCK=threading.RLock();_bridge=None
def on_ui(fn,*args):
 import jpype
 result=[];errors=[]
 def run():
  try:result.append(fn(*args))
  except BaseException as error:errors.append(error)
 swing=jpype.JClass('javax.swing.SwingUtilities')
 if swing.isEventDispatchThread():run()
 else:swing.invokeAndWait(jpype.JProxy('java.lang.Runnable',dict(run=run)))
 if errors:raise errors[0]
 return result[0] if result else None
def bridge():
 global _bridge
 with LOCK:
  if _bridge is None:
   import jpype
   common=ROOT/'neural_app'/'java_library'/'common'
   if not jpype.isJVMStarted():
    candidates=sorted(Path('C:/Program Files/Java').glob('jdk-*/bin/server/jvm.dll'),reverse=True)
    jpype.startJVM(str(candidates[0]) if candidates else jpype.getDefaultJVMPath(),'-Djava.awt.headless=true','-Xms16m','-Xmx256m','-XX:ActiveProcessorCount=2','--enable-native-access=ALL-UNNAMED',classpath=[str(common),str(ROOT/'neural_app/java_library/dependencies/org.jfree.svg-5.0.7.jar')],convertStrings=True)
   _bridge=jpype.JClass('neural.studio.Bridge')
   model_dir=ROOT/'data'/'sections'/'localbus';model_dir.mkdir(parents=True,exist_ok=True);original=ROOT/'neural_app'/'java_library'/'family_3'/'classes'/'data'/'activity-model.bin'
   if original.is_file() and not (model_dir/original.name).exists():shutil.copy2(original,model_dir/original.name)
   jpype.JClass('java.lang.System').setProperty('bus.dataDir',str(model_dir))
   jpype.JClass('java.lang.System').setProperty('allprev.apps',str(ROOT/'preserved'/'sources'))
   for folder in (ROOT/'neural_app'/'java_library').glob('family_*'):
    _bridge.register(folder.name,str(folder/'classes'))
  return _bridge

class JavaSections:
 def __init__(self,runtime):
  self.runtime=runtime;self.index=json.loads((ROOT/'java-sections.json').read_text(encoding='utf8'))
  imported=ROOT/'references'/'desktop-java'/'panels.json'
  if imported.exists():self.index.update({p['id']:p for p in json.loads(imported.read_text(encoding='utf-8'))})
  import jpype
  def dispatch(section,payload):
   try:
    text=str(payload);section=str(section)
    if section not in ('flux','pipeline'):raise ValueError('Unknown shared Java calculation')
    result=runtime.pipeline({'text':text[:200],'sections':[]}) if section=='pipeline' else runtime.engine('flux',{'text':text[:4000]})
    result['shared_receipt']=runtime.component_result(str(bridge().scope.get()),{'section':section},result)
    return json.dumps(result)
   except Exception as error:return json.dumps({'status':'ERROR','error':str(error)})
  library=bridge();self.broker=jpype.JProxy('neural.studio.Broker',dict(apply=dispatch));library.broker=self.broker
 def open(self,ident):
  row=self.index.get(ident)
  if not row or not row['built']:raise ValueError('The Java section library is not compiled: '+str(ident))
  with LOCK:
   try:result=json.loads(str(on_ui(bridge().open,ident,row['family'],row['class'])))
   except Exception as error:
    detail=str(error)
    if hasattr(error,'stacktrace'):detail=str(error.stacktrace())
    raise ValueError(detail) from error
   if ident.startswith('desktop-java-'):
    field=self.runtime.field.snapshot();values=field['values'];signal=sum(values)/len(values);magnitude=sum(abs(v) for v in values)/len(values)
    coupled=int(on_ui(bridge().coupleRuntime,ident,signal,magnitude))
    if coupled:result=json.loads(str(on_ui(bridge().describe,ident)))
    result['shared_runtime_coupling']={'updated_drawings':coupled,'signal':signal,'magnitude':magnitude,'basis':'Actual shared 96-node field values; supported wave callback only.'}
   result['title']=row['name'];result['implementation']='Integrated windowless Java library';return result
 def action(self,b):
  ident=b['section'];self.open(ident)
  with LOCK:
   bridge().inputValue=b.get('input');bridge().confirmValue=0 if b.get('confirm') else 2
   value=str(b.get('value',''))
   if b.get('action')=='key':
    key=json.loads(value);name={'ArrowLeft':'LEFT','ArrowRight':'RIGHT','ArrowUp':'UP','ArrowDown':'DOWN',' ':'SPACE','Enter':'ENTER','Escape':'ESCAPE'}.get(key['key'],key['key'].upper())
    value=('ctrl ' if key.get('ctrl') else '')+('alt ' if key.get('alt') else '')+('shift ' if key.get('shift') else '')+name
   result=json.loads(str(on_ui(bridge().action,ident,b['control'],b.get('action','click'),value,b.get('path'))))
   result['receipt']=self.runtime.component_result(ident,{'control':b['control'],'action':b.get('action','click')},result)
   return result
 def graphic(self,ident,control,width=850,height=360):
  with LOCK:
   self.open(ident);return str(on_ui(bridge().graphicSvg,ident,control)).encode('utf-8')
 def close(self):
  if _bridge is not None:
   with LOCK:_bridge.close();_bridge.broker=None;self.broker=None
 def pause(self,ident,value):on_ui(bridge().setPaused,ident,bool(value))
 def tick_all(self):
  with LOCK:on_ui(bridge().tickAll)
 def stats(self):return json.loads(str(bridge().stats())) if _bridge else {'sections':0,'native_windows':0}
