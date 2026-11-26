import tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from neural_app.runtime import Runtime
from neural_app.component_host import ComponentHost
from neural_app.section_background import SectionBackground

class StartupLifecycleTests(unittest.TestCase):
 def test_scheduler_survives_slow_component_host_initialization(self):
  with tempfile.TemporaryDirectory() as folder:
   runtime=Runtime(Path(folder))
   original=SectionBackground.__init__
   def delayed(background,host):time.sleep(.2);original(background,host)
   try:
    with patch.object(SectionBackground,'__init__',delayed):ComponentHost(runtime)
    job=runtime.submit('flux',{'text':'startup verification'})
    end=time.monotonic()+5
    while time.monotonic()<end and runtime.result(job['id'])['status'] in ('queued','running'):time.sleep(.02)
    self.assertTrue(runtime.worker.is_alive());self.assertEqual(runtime.result(job['id'])['status'],'complete')
   finally:runtime.close()
