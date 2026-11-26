import threading,time,unittest
from neural_app.command_console import CommandConsole
class RuntimeStub:
 def component_result(self,*args,**kwargs):return 1
class ApprovedConsoleTests(unittest.TestCase):
 def setUp(self):self.events=[];self.console=CommandConsole(RuntimeStub(),lambda kind,value:self.events.append((kind,value)))
 def tearDown(self):self.console.close()
 def wait(self,ident,seconds=15):
  deadline=time.monotonic()+seconds
  while time.monotonic()<deadline:
   if ident in self.console.completed:return self.console.completed[ident]
   time.sleep(.025)
  self.fail('Console did not finish')
 def test_powershell_unicode_output_and_session(self):
  job=self.console.start("Write-Output ('console-'+[char]0x03BB); Write-Output (Get-Location).Path")['id'];result=self.wait(job)
  self.assertEqual(result['exit_code'],0);text=''.join(v.get('text','') for k,v in self.events);self.assertIn('console-λ',text);self.assertIn('Neural App',text);self.assertEqual([v['state'] for k,v in self.events if v['id']==job][0],'start');self.assertEqual(self.events[-1][1]['state'],'end')
 def test_error_stream_and_exit_code(self):
  job=self.console.start("Write-Error 'expected-verification-error'")['id'];result=self.wait(job);self.assertNotEqual(result['exit_code'],0);self.assertTrue(any(v.get('type')=='stderr' for k,v in self.events))
 def test_cancel_owns_only_current_job(self):
  job=self.console.start('Start-Sleep -Seconds 30')['id']
  with self.assertRaises(ValueError):self.console.start('Write-Output second')
  self.console.cancel(job);result=self.wait(job);self.assertTrue(result['cancelled']);self.assertIsNone(self.console.active)
 def test_output_limit(self):
  self.console.output_limit=1024;job=self.console.start("Write-Output ('x'*100000)")['id'];result=self.wait(job);self.assertTrue(result['output_limited']);self.assertLessEqual(result['output_bytes'],1024)
 def test_timeout(self):
  self.console.timeout=.3;job=self.console.start('Start-Sleep -Seconds 30')['id'];result=self.wait(job);self.assertTrue(result['cancelled'])
