import threading,types,unittest
from unittest.mock import patch
from neural_app.fair_slices import FairSlices,refresh_root_spheres
from neural_app.sphere_functions import SphereFunctions,PROFILES

class FairScheduling(unittest.TestCase):
    def test_every_role_gets_a_turn_even_if_every_callback_exceeds_budget(self):
        scheduler=FairSlices();clock=[0.];seen=[];items=[(str(i),None) for i in range(33)]
        def visit(name,_):seen.append(name);clock[0]+=.1
        with patch('neural_app.fair_slices.time.perf_counter',lambda:clock[0]):
            for _ in range(33):scheduler.run(items,visit,limit=8,budget_seconds=.04)
        self.assertEqual(seen,[str(i) for i in range(33)])
    def test_fast_callbacks_use_bounded_batches(self):
        s=FairSlices();seen=[];s.run([(str(i),None) for i in range(50)],lambda name,_:seen.append(name),limit=8,budget_seconds=1)
        self.assertEqual(len(seen),8);self.assertEqual(s.cursor,8)
    def test_exception_advances_turn_instead_of_restarting_first_role(self):
        s=FairSlices()
        with self.assertRaises(ValueError):s.run([('bad',None),('good',None)],lambda *_:(_ for _ in ()).throw(ValueError()),limit=1)
        seen=[];s.run([('bad',None),('good',None)],lambda name,_:seen.append(name),limit=1)
        self.assertEqual(seen,['good'])

class SphereSchedule(unittest.TestCase):
    def test_single_view_requests_do_not_copy_sibling_frames(self):
        from neural_app.sphere_functions import snapshot
        seen=[];provider=types.SimpleNamespace(view=lambda lane:seen.append(lane) or {'sequence':1})
        c=types.SimpleNamespace(plane_orientations=provider,neural_topology_views=provider)
        snapshot(c,'neural-inverse');snapshot(c,'plane-rotated-positive')
        self.assertEqual(seen,['neural-inverse','plane-rotated-positive'])
    def test_whole_mind_function_snapshot_omits_unneeded_large_payload(self):
        from neural_app.sphere_functions import snapshot
        class Unneeded:
            def __deepcopy__(self,memo):raise AssertionError('Unneeded payload copied')
        service=types.SimpleNamespace(lock=threading.RLock(),frame={'sequence':3,'irrelevant':Unneeded(),'particles':[{'id':'a','point':[0,0,1],'record':Unneeded()}]})
        result=snapshot(types.SimpleNamespace(whole_mind_study=service),'whole-mind-study')
        self.assertEqual(result['particles'],[{'id':'a','point':[0,0,1]}])
    def circuit(self):return types.SimpleNamespace(lock=threading.RLock(),sources={},sphere_workspace=types.SimpleNamespace(view=lambda:{}))
    def test_all_registered_functions_covered_in_three_fast_slices(self):
        s=SphereFunctions();seen=[];s.process=lambda lane,*_:seen.append(lane)
        with patch('neural_app.sphere_functions.snapshot',return_value={'sequence':1}):
            for _ in range(3):s.next_at=0;s.tick(self.circuit())
        self.assertEqual(set(seen),set(PROFILES));self.assertLessEqual(len(seen),36)
    def test_fast_studies_are_updated_by_sphere_worker(self):
        s=SphereFunctions();c=self.circuit();ticks=[]
        c.choice_action_study=types.SimpleNamespace(tick=lambda owner:ticks.append(owner))
        s.process=lambda *_:None
        with patch('neural_app.sphere_functions.snapshot',return_value={}):
            for _ in range(3):s.next_at=0;s.tick(c)
        self.assertEqual(len(ticks),4);self.assertTrue(all(owner is c for owner in ticks))
    def test_one_failing_snapshot_does_not_starve_other_roles(self):
        s=SphereFunctions();seen=[];s.process=lambda lane,*_:seen.append(lane)
        def snapshot(_,lane):
            if lane=='original':raise ValueError('fixture failure')
            return {'sequence':1}
        with patch('neural_app.sphere_functions.snapshot',snapshot):
            for _ in range(3):s.next_at=0;s.tick(self.circuit())
        self.assertEqual(set(seen),set(PROFILES)-{'original'});self.assertEqual(s.view('original')['status'],'error')
        self.assertGreater(s.view('original')['scheduler_health']['retry_in_seconds'],0)
    def test_numeric_source_sampling_covers_later_sources(self):
        s=SphereFunctions();c=self.circuit();c.sources={str(i):{'parent_event':1,'facts':[{'path':['x'],'value':i}]} for i in range(100)}
        s.process=lambda *_:None
        with patch('neural_app.sphere_functions.snapshot',return_value={}):
            for _ in range(4):s.next_at=0;s.next_observe=0;s.tick(c)
        self.assertEqual({ch['source'] for ch in s.channels.values()},set(c.sources))
    def test_conversation_refresh_updates_roots_and_is_rate_limited(self):
        class Projection:
            def __init__(self):self.calls=[];self.latest={};self.unmodulated={}
            def step(self,*args):self.calls.append(args);self.latest={'sequence':len(self.calls)}
        c=types.SimpleNamespace(lock=threading.RLock(),sphere_next=0,goal='g',sources={},sphere_modulators=types.SimpleNamespace(sample=lambda:{}),generation_selector=types.SimpleNamespace(last={}),expression_sphere=Projection(),selection_sphere=Projection(),system_flux_sphere=Projection())
        self.assertTrue(refresh_root_spheres(c));self.assertFalse(refresh_root_spheres(c))
        self.assertEqual(len(c.expression_sphere.calls),1);self.assertEqual(len(c.system_flux_sphere.calls),1)
