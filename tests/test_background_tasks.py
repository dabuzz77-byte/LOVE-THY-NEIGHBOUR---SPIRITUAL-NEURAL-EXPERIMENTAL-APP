import threading,time,unittest
from neural_app.cooperative_cycle import LoopCycle
from neural_app.task_pool import TaskPool

class CounterLoop:
 def __init__(self):self.stop=threading.Event();self.wake=threading.Event();self.values=[]
 def loop(self):
  sequence=0
  for _shared_tick in range(1):
   self.values.append(sequence);sequence+=1
   self.wake.wait(30);self.wake.clear()

class BackgroundTaskTests(unittest.TestCase):
 def test_loop_retains_state_and_waits_without_holding_a_worker(self):
  owner=CounterLoop();cycle=LoopCycle(owner.loop);before=time.monotonic();cycle();self.assertLess(time.monotonic()-before,.2);self.assertEqual(owner.values,[0]);self.assertFalse(cycle.ready())
  owner.wake.set();self.assertTrue(cycle.ready());cycle();cycle();self.assertEqual(owner.values,[0,1]);owner.stop.set();cycle();self.assertTrue(cycle.closed)
 def test_waiting_io_does_not_delay_calculation_lane(self):
  io=TaskPool(1,'test-io');compute=TaskPool(1,'test-compute');release=threading.Event();started=threading.Event()
  def waiting():started.set();release.wait(3)
  try:
   blocked=io.submit(waiting);self.assertTrue(started.wait(1));self.assertEqual(compute.submit(lambda:21*2).result(1),42);self.assertFalse(blocked.done())
  finally:release.set();io.shutdown(wait=True,cancel_futures=True);compute.shutdown(wait=True,cancel_futures=True)
