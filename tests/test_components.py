"""Shared section behavior, source graphics, learning and original model checks."""
import hashlib,json,sys,tempfile,threading,unittest,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runtime')]
from neural_app.runtime import Runtime
from neural_app.server import create_server
from neural_app.java_components import bridge

class ComponentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  bridge();cls.temp=tempfile.TemporaryDirectory();cls.runtime=Runtime(Path(cls.temp.name));cls.server=create_server(cls.runtime,0);threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.base='http://127.0.0.1:'+str(cls.server.server_address[1]);page=urllib.request.urlopen(cls.base).read().decode();cls.token=page.split("window.NEURAL_TOKEN='")[1].split("'")[0]
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.runtime.close();cls.temp.cleanup()
 def request(self,path,body=None):
  req=urllib.request.Request(self.base+'/api/components'+path,data=json.dumps(body).encode() if body is not None else None,headers={'X-Neural-Token':self.token,'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
 def test_all_45_sections_open_without_original_windows(self):
  index=self.request('');self.assertEqual(len(index),45)
  for row in index:
   with self.subTest(section=row['id']):
    result=self.request('/open?id='+row['id']);self.assertIsNone(result.get('failure'));self.assertEqual(result.get('windows',0),0)
 def test_neural_learning_control_updates_original_weights(self):
  before=self.request('/neural-lab/api/state')['steps'];result=self.request('/neural-lab/api/control',{'action':'step'});after=self.request('/neural-lab/api/state')['steps'];self.assertEqual(after,before+1);self.assertTrue(result['ok']);self.assertIn('shared_receipt',result)
 def test_named_section_features_and_feedback_survive_restart(self):
  ident=self.runtime.component_result('monad',{'test':'named features'},{'value':.7,'valid':True});before=self.runtime.get_model().supervised;self.runtime.feedback({'receipt':ident,'target':1,'note':'Verification label'});self.assertEqual(self.runtime.get_model().supervised,before+1);self.assertIn(('section/monad',3),self.runtime.get_model().groups);receipt=self.runtime.receipts(ident);self.assertEqual(receipt['result']['value'],.7)
  restored=Runtime(self.runtime.data,start=False)
  try:self.assertEqual(restored.get_model().supervised,before+1);self.assertIn(('section/monad',3),restored.get_model().groups)
  finally:restored.close()
 def test_all_original_graphic_files_are_exact_copies(self):
  inventory=json.loads((ROOT/'graphics-inventory.json').read_text(encoding='utf8'));self.assertEqual(inventory['original_files'],48)
  for row in inventory['files']:self.assertEqual(hashlib.sha256((ROOT/'assets'/row['asset']).read_bytes()).hexdigest(),row['sha256'])
 def test_sections_do_not_start_original_tcp_servers(self):
  import psutil
  try:ports={c.laddr.port for c in psutil.Process().net_connections(kind='tcp') if c.status==psutil.CONN_LISTEN}
  except (psutil.AccessDenied,RuntimeError):self.skipTest('OS connection-inspection API is unavailable in this environment')
  self.assertEqual(ports,{self.server.server_address[1]})
 def test_original_source_engine_constructor_and_method_calls(self):
  catalog=self.request('/inference/api/catalog');definition=next(m for m in catalog['modules'] if m['name']=='InferenceMeshNode')
  result=self.request('/inference/api/run',{'id':definition['id'],'init':{'node_id':'parity-node'},'calls':[{'method':'get_public_bytes','args':{}},{'method':'sign_inference_payload','args':{'workload_hash':{'$bytes':'ab'*32}}}]})
  self.assertTrue(result['ok'],result.get('error'));self.assertEqual(len(result['results']),2);self.assertEqual(result['results'][0]['result']['encoding'],'bytes');self.assertEqual(len(result['results'][0]['result']['hex']),64)
 def test_original_signed_payload_verifies(self):
  result=self.request('/inference/api/crypto',{'mode':'sign','text':'binary ternary qutrit'});self.assertTrue(result['verified']);self.assertIn('shared_receipt',result)
 def test_matrix_builtin_console_uses_shared_pipeline(self):
  result=self.request('/matrix/api/command',{'command':'pipeline known test input'});self.assertTrue(result['ok'])

 def test_inference_uses_original_observatory_contract_in_process(self):
  self.request('/inference/api/catalog')
  host=self.runtime.component_host;module=host.python.loaded['inference']['module']
  direct=module.obs_request('/api/state')
  self.assertIsInstance(direct,dict);self.assertIn('modules',direct)
  result=module.obs_request('/api/settings',{'cycle_seconds':10})
  self.assertIsInstance(result,dict)
  self.assertEqual(host.adapter('observatory')[2]['controller'].config['cycle_seconds'],10)
 def test_atelier_feedback_runs_without_a_worker_process(self):
  self.request('/open?id=atelier');host=self.runtime.component_host;c=host.python.loaded['atelier']['controller']
  c.add_worker('feedback_worker.py');before=c.engine.script_samples
  host.background.step();self.assertGreater(c.engine.script_samples,before)
  c.stop_workers();before=c.engine.script_samples;host.background.step();self.assertEqual(c.engine.script_samples,before)
 def test_native_open_controls_navigate_to_owned_sections(self):
  self.request('/open?id=hydrogen');host=self.runtime.component_host;c=host.python.loaded['hydrogen']['controller']
  c.launch_external('flux');self.assertEqual(host.python.navigation,'flux');host.python.navigation=None
  self.request('/open?id=dualrail');host.python.loaded['dualrail']['controller'].open_observatory();self.assertEqual(host.python.navigation,'observatory');host.python.navigation=None
 def test_scanned_original_entry_navigates_without_executing_it(self):
  self.request('/inference/api/catalog');host=self.runtime.component_host;module=host.python.loaded['inference']['module']
  panel=next(p for p in host.panels if p['id']=='hydrogen');path=self.runtime.data/'scanned'/panel['entry'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text('raise RuntimeError("Must not spawn the original app")')
  item={'id':'test-native-entry','path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};module.registry.append(item)
  try:
   result=module.script_run(item['id']);self.assertEqual(result['navigate'],'hydrogen');self.assertTrue(result['shared_process'])
  finally:module.registry.remove(item)
 def test_cooperative_prompt_cycle_preserves_execution(self):
  self.request('/inference/api/catalog');host=self.runtime.component_host;module=host.python.loaded['inference']['module'];loop=module.prompt_loop
  from neural_app.inference_scheduler import one_cycle
  import copy,time
  saved=copy.deepcopy(loop.prompts),copy.deepcopy(loop.settings),loop.process
  try:
   loop.prompts=[{'id':0,'enabled':True,'status':'ready','runs':0}];loop.settings.update(enabled=True,interval=120,cursor=0);loop.process=lambda row:{'execution':{'status':'complete'}}
   before=time.monotonic();one_cycle(loop.run)();self.assertLess(time.monotonic()-before,1);self.assertEqual(loop.prompts[0]['runs'],1);self.assertEqual(loop.prompts[0]['status'],'complete')
  finally:loop.prompts,loop.settings,loop.process=saved;loop.persist()

 def test_flux_original_pipeline_finishes_while_other_section_is_open(self):
  self.request('/open?id=flux');host=self.runtime.component_host;qt=host.qt
  # Keep this local acceptance check independent of configured research sources.
  qt.window.web_research.set_enabled(False)
  qt.window.pipeline.set_auto(False)
  result=qt.window.pipeline.submit('parity verification','shared-flux-queue',{'text':'binary ternary qutrit'},force=True,run_now=True)
  qt.active(False)
  import time
  until=time.monotonic()+15
  row=None
  while time.monotonic()<until:
   qt.pulse();rows=qt.window.pipeline.rows();row=next((r for r in rows if r.get('identity')=='shared-flux-queue'),None)
   if row and row.get('status') not in ('queued','QUEUED','pending','PENDING','RUNNING','running'):break
   time.sleep(.1)
  self.assertIsNotNone(row,rows)
  self.assertEqual(str(row['status']).upper(),'COMPLETE',row)

 def test_java_translation_copy_returns_real_clipboard_payload(self):
  descriptor=self.request('/open?id=beacon-runtranslator')
  def walk(node):
   if not isinstance(node,dict):return []
   return [node]+sum((walk(c) for c in node.get('children',[])),[])+sum((walk(t.get('body')) for t in node.get('tabs',[])),[])
  controls=walk(descriptor['ui']);field=next(n for n in controls if n.get('type')=='input')
  self.request('/action',{'section':'beacon-runtranslator','control':field['id'],'action':'set','value':'101001'})
  for label in ('Translate','Copy report'):
   button=next(n for n in controls if n.get('text')==label);result=self.request('/action',{'section':'beacon-runtranslator','control':button['id'],'action':'click'})
  self.assertTrue(result.get('clipboard'));self.assertIn('101001',result['clipboard']);self.assertIsNone(result.get('failure'))

 def test_training_controls_inside_scrollable_canvases_are_native(self):
  def walk(node):
   if not isinstance(node,dict):return []
   return [node]+sum((walk(c) for c in node.get('children',[])),[])+sum((walk(t.get('body')) for t in node.get('tabs',[])),[])
  for ident in ('godmind','unified-neural'):
   controls=walk(self.request('/open?id='+ident)['ui'])
   labels=[n.get('text','') for n in controls if n.get('type') in ('button','toggle')]
   self.assertTrue(any('step' in text.lower() or 'train' in text.lower() for text in labels),labels)
   self.assertGreaterEqual(len([n for n in controls if n.get('type') in ('select','range','number','input')]),2)

 def test_original_python_space_and_escape_shortcuts(self):
  descriptor=self.request('/open?id=unified-neural');host=self.runtime.component_host;c=host.python.loaded['unified-neural']['controller'];before=c.running
  self.request('/action',{'section':'unified-neural','control':descriptor['ui']['id'],'action':'key','value':json.dumps({'key':' '})});self.assertNotEqual(c.running,before)
  self.request('/action',{'section':'unified-neural','control':descriptor['ui']['id'],'action':'key','value':json.dumps({'key':'Escape'})});self.assertFalse(c.running)
 def test_original_java_command_history_shortcut(self):
  descriptor=self.request('/open?id=localbus')
  def walk(node):
   if not isinstance(node,dict):return []
   return [node]+sum((walk(c) for c in node.get('children',[])),[])+sum((walk(t.get('body')) for t in node.get('tabs',[])),[])
  field=next(n for n in walk(descriptor['ui']) if n.get('type')=='input')
  for action,value in [('set','101001'),('enter',''),('set',''),('key',json.dumps({'key':'ArrowUp'}))]:result=self.request('/action',{'section':'localbus','control':field['id'],'action':action,'value':value})
  restored=next(n for n in walk(result['ui']) if n.get('id')==field['id']);self.assertEqual(restored['value'],'101001')

 def test_ai_source_calls_and_linked_workflows_use_owned_logic(self):
  from neural_app.chat import Chat
  chat=Chat(self.runtime);source=next(r for r in chat.catalog['sources'] if r['path']=='HydrogenMesh/signals.py')
  plan={'id':source['id'],'target':'from_bits','init':{'text':'00101100'}}
  result=chat.write({'action':'run_source','args':plan});self.assertTrue(result['ok'],result);self.assertEqual(result['result']['bits'],'00101100');self.assertTrue(result['shared_process'])
  workflow={'input':{'bits':'00101100'},'steps':[{'id':source['id'],'target':'from_bits','init':{'text':'$input.bits'}},{'id':source['id'],'target':'from_bits','init':{'text':'$previous.bits'}}]}
  self.assertTrue(chat.write({'action':'save_workflow','args':workflow})['ok']);result=chat.write({'action':'run_workflow','args':workflow});self.assertTrue(result['ok'],result);self.assertEqual(result['results'][-1]['result']['bits'],'00101100')
  saved=chat.write({'action':'save_note','args':{'name':'parity-note.md','text':'Verified shared workflow'}});self.assertEqual(Path(saved['path']).read_text(),'Verified shared workflow')
 def test_ai_source_edits_require_current_hash_and_keep_revision(self):
  from neural_app.chat import Chat
  chat=Chat(self.runtime);source=next(r for r in chat.catalog['sources'] if r['path']=='HydrogenMesh/signals.py')
  with tempfile.TemporaryDirectory(dir=ROOT/'data') as folder:
   path=Path(folder)/'fixture.py';path.write_text('def value(): return 1')
   chat.workspace.active=lambda row:(path,None)
   before=chat.workspace.read(source['id'])
   with self.assertRaises(ValueError):chat.write({'action':'source_edit','args':{'id':source['id'],'text':'def value(): return 2','expected_sha256':'stale'}})
   result=chat.write({'action':'source_edit','args':{'id':source['id'],'text':'def value(): return 2','expected_sha256':before['sha256']}})
   self.assertEqual(Path(result['backup']).read_text(),'def value(): return 1');self.assertEqual(path.read_text(),'def value(): return 2')
 def test_ai_module_pause_stops_shared_training_until_resumed(self):
  from neural_app.chat import Chat
  self.request('/neural-lab/api/state');host=self.runtime.component_host;engine=host.python.loaded['neural-lab']['controller'];engine.running=True;chat=Chat(self.runtime)
  chat.write({'action':'module_stop','args':{'id':'neural-lab'}});before=engine.model.steps;host.background.step();self.assertEqual(engine.model.steps,before)
  chat.write({'action':'module_start','args':{'id':'neural-lab'}});host.background.step();self.assertGreater(engine.model.steps,before);engine.running=False

 def test_explicit_javascript_source_job_uses_bounded_common_runner(self):
  from neural_app.chat import Chat
  chat=Chat(self.runtime)
  with tempfile.TemporaryDirectory(dir=ROOT/'data') as folder:
   path=Path(folder)/'fixture.js';path.write_text("console.log('PARITY_SCRIPT_OK')")
   chat.workspace.active=lambda row:(path,None)
   result=chat.workspace.script({'id':'fixture-js','path':'fixture.js','language':'JavaScript'},{})
   self.assertTrue(result['ok'],result);self.assertIn('PARITY_SCRIPT_OK',result['stdout']);self.assertTrue(result['experimental_job'])

 def test_flux_provider_settings_and_editable_models_are_shared(self):
  from neural_app.chat import Chat
  self.request('/open?id=flux');qt=self.runtime.component_host.qt;chat=Chat(self.runtime);previous=chat.settings()['gemini'];key=chat.key('gemini')
  try:
   chat.save_settings({'provider':'gemini','model':previous['model'],'endpoint':previous['endpoint'],'key':'fixture-parity-key'})
   self.assertEqual(qt.window.key_vault.load('gemini'),'fixture-parity-key')
   def field():return qt.walk(qt.window.cloud_controls['gemini']['model'])
   model=qt.call(field);self.assertTrue(model['editable'])
   qt.action({'section':'flux','control':model['id'],'action':'set_text','value':'parity-test-model'})
   self.assertEqual(chat.settings()['gemini']['model'],'parity-test-model')
   self.assertTrue(qt.call(lambda:qt.walk(qt.window.cloud_controls['gemini']['key']))['password'])
  finally:chat.save_settings({'provider':'gemini','model':previous['model'],'endpoint':previous['endpoint'],'key':key,'clear_key':not bool(key)})

 def test_core_original_cycles_continue_without_drawing_requests(self):
  self.request('/open?id=core');host=self.runtime.component_host;c=host.python.loaded['core']['controller'];c.live.set(False);c.start();before=c.engine.cycle
  try:
   host.background.step();self.assertGreater(c.engine.cycle,before);self.assertTrue(any(r['section']=='section/core' for r in self.runtime.receipts()))
  finally:c.stop()
 def test_hydrogen_queue_processes_without_drawing_requests(self):
  self.request('/open?id=hydrogen');host=self.runtime.component_host;rt=host.python.loaded['hydrogen']['controller'].rt
  rt.work.put(('text','Background signal verification'));host.background.step()
  import time
  end=time.monotonic()+8
  while rt.work.unfinished_tasks and time.monotonic()<end:time.sleep(.05)
  self.assertEqual(rt.work.unfinished_tasks,0);self.assertTrue(any(r['section']=='section/hydrogen' for r in self.runtime.receipts()))

if __name__=='__main__':unittest.main()
