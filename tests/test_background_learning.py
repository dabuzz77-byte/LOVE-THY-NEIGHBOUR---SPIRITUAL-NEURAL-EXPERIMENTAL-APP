import tempfile,time,unittest
from pathlib import Path
from neural_app.runtime import Runtime
from neural_app.component_host import ComponentHost
class BackgroundLearningTests(unittest.TestCase):
 def test_learning_continues_without_open_section_requests(self):
  with tempfile.TemporaryDirectory() as folder:
   runtime=Runtime(Path(folder));host=ComponentHost(runtime);runtime.component_host=host;runtime.settings['pace']='high'
   try:
    _,_,item=host.adapter('neural-lab');engine=item['controller'];engine.command('pause',{});before=engine.model.steps;engine.command('start',{})
    deadline=time.monotonic()+3
    while time.monotonic()<deadline and engine.model.steps==before:time.sleep(.05)
    self.assertGreater(engine.model.steps,before)
    engine.command('pause',{});paused=engine.model.steps;time.sleep(.4);self.assertEqual(engine.model.steps,paused)
   finally:runtime.close()

class FiniteTaskTests(unittest.TestCase):
 def test_named_worker_executes_once_without_polling(self):
  from neural_app import section_threads
  import threading
  section_threads.ensure_pool();done=threading.Event();values=[]
  def worker():values.append('completed');done.set()
  count=len(section_threads.scheduled);task=section_threads.Thread(target=worker);task.start()
  self.assertTrue(done.wait(2));task.join(2);self.assertEqual(values,['completed']);self.assertEqual(len(section_threads.scheduled),count)
