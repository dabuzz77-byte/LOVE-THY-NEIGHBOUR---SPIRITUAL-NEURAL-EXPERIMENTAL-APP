"""Original passage graph and summary algorithms, with direct shared calls."""
import importlib,json,sqlite3,time,types,threading
from pathlib import Path
from .runtime import ROOT
from . import component_ui as ui

class KnowledgeBridge:
 def __init__(self,package,runtime):
  self.module=importlib.import_module(package+'.backbone');self.worker=importlib.import_module(package+'.knowledge_worker');self.path=runtime.data/'sections'/'backbone'/'knowledge.sqlite3';self.path.parent.mkdir(parents=True,exist_ok=True);self.count=0
  knowledge=self.module.Knowledge(self.path);knowledge.close()
 def knowledge(self):
  k=object.__new__(self.module.Knowledge);k.db=sqlite3.connect(self.path,check_same_thread=False);return k
 def graph(self):
  k=self.knowledge();nodes={};edges=[];offset=0
  try:
   while True:
    page=k.graph(offset);nodes.update((n['id'],n) for n in page['nodes']);edges.extend(page['edges'])
    if page['next_offset'] is None:return {'nodes':list(nodes.values()),'edges':edges,'note':page['note']}
    offset=page['next_offset']
  finally:k.close()
 def put(self,passage):
  k=self.knowledge()
  try:return k.put(passage)
  finally:k.close()
 def summary(self,task_id='shared-summary'):return self.worker.summarize(self,{'action':'map-summary','task_id':task_id})
 def tick(self,desktop):
  self.count+=1
  while not desktop.commands.empty():
   kind,data=desktop.commands.get_nowait()
   if kind=='import':
    for passage in data:self.put(passage)
    desktop.events.put(('notice',f'Imported {len(data)} passages.'))
  desktop.events.put(('graph',self.graph()));desktop.events.put(('pulse',{'sent_monotonic_ns':time.monotonic_ns()}));desktop.events.put(('status',{'measured_hz':None,'pulse_count':self.count,'skipped_ticks':0,'services':[{'id':'shared-text-map','topics':['knowledge.updated','workflow.request']}] }));desktop.poll()

class TextWorkerPanel(ui.Frame):
 def __init__(self,bridge):
  super().__init__();self.bridge=bridge;self.input=ui.Text(self);self.input.insert('end','{"task_id":"shared-summary","action":"map-summary"}');ui.Button(self,text='Summarize shared passage map',command=self.summarize).pack();self.output=ui.Text(self,state='disabled')
 def summarize(self):
  result=self.bridge.summary(json.loads(self.input.get()).get('task_id','shared-summary'));self.output.value=json.dumps(result,indent=2);return result

class ScannerPanel(ui.Frame):
 def __init__(self,module,runtime):
  super().__init__();self.module=module;self.runtime=runtime;self.folder=ROOT/'data'/'sections'/'scanner';self.folder.mkdir(parents=True,exist_ok=True);self.stop=threading.Event();self.capture=None;self.capture_state='Stopped';self.input=ui.Text(self);self.input.value='{"id":"activity-1","timestamp":"","timezone":"Europe/London","messages":[{"role":"user","text":"Enter an activity capture here"}]}';ui.Label(self,text='AI activity capture · deduplication and shared delivery').pack();ui.Button(self,text='Import and route activity',command=self.ingest).pack();ui.Button(self,text='Show retained events',command=self.events).pack();self.config=ui.Text(self)
  config_path=Path(module.__file__).parent/'scanner_config.json';cfg=json.loads(config_path.read_text(encoding='utf8')) if config_path.exists() else {'browser_mode':'opera','poll_seconds':60,'timezone':'Europe/London','account_namespace':'my-ai-mode'};cfg['handlers']=[];self.config.value=json.dumps(cfg,indent=2)
  ui.Button(self,text='Capture once from connected browser',command=lambda:self.start_capture('once')).pack();ui.Button(self,text='Start continuous capture',command=self.start_capture).pack();ui.Button(self,text='Stop capture',command=self.stop_capture).pack();self.output=ui.Text(self,state='disabled')
 def store(self):return self.module.Store(self.folder/'activity.sqlite3')
 def ingest(self):
  activity=json.loads(self.input.get());store=self.store()
  try:
   count=store.ingest(activity,[]);rows=[json.loads(r[0]) for r in store.db.execute('SELECT payload FROM events ORDER BY rowid DESC LIMIT 20')]
   receipts=[self.runtime.record('scanner',{},row,0) for row in rows if row['activity_id']==activity['id']];result={'new_events':count,'receipts':receipts};self.output.value=json.dumps(result,indent=2);return result
  finally:store.db.close()
 def events(self):
  store=self.store()
  try:rows=[json.loads(r[0]) for r in store.db.execute('SELECT payload FROM events ORDER BY rowid DESC LIMIT 100')];self.output.value=json.dumps(rows,indent=2);return rows
  finally:store.db.close()
 def start_capture(self,mode='run'):
  if self.capture and self.capture.is_alive():raise ValueError('Capture is already active')
  cfg=json.loads(self.config.get());cfg.update(base=self.folder,data_dir='browser-data',handlers=[]);cfg.setdefault('poll_seconds',60);cfg.setdefault('timezone','Europe/London');cfg.setdefault('account_namespace','my-ai-mode');self.stop.clear();self.capture_state='Connecting to browser';module=self.module;runtime=self.runtime
  class SharedStore(module.Store):
   def ingest(store,activity,handlers):
    before=set(r[0] for r in store.db.execute('SELECT id FROM events'));count=super().ingest(activity,[])
    for row in store.db.execute('SELECT id,payload FROM events'):
     if row[0] not in before:runtime.component_result('scanner',{'source':'browser capture'},json.loads(row[1]))
    return count
  def run():
   store=SharedStore(self.folder/'activity.sqlite3')
   try:self.capture_state='Capturing';module.browser_run(cfg,store,mode,self.stop);self.capture_state='Stopped'
   except Exception as error:self.capture_state='Capture stopped: '+str(error)
   finally:store.db.close();self.output.value=self.capture_state
  self.capture=threading.Thread(target=run,name='neural-activity-capture',daemon=True);self.capture.start();return {'status':self.capture_state,'mode':mode}
 def stop_capture(self):self.stop.set();self.capture_state='Stopping';return {'status':self.capture_state}
 def close(self):self.stop_capture()
