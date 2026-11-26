"""Desktop integration, source-compatibility, persistence and lifecycle tests."""
import ast
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import time
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from godmind_desktop import DesktopSession, GodmindDesktop
from neural_weight import StructuralStateLedger, BackgroundWeightOptimizer, ProductionNetworkGateway


def original_classes(filename):
    """Load original definitions without their broken top-level wiring."""
    path=ROOT/'source_originals'/'neural_weight'/filename
    tree=ast.parse(path.read_text())
    tree.body=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.ClassDef))]
    namespace={}
    exec(compile(tree,str(path),'exec'),namespace)
    return namespace


class IntegrationTests(unittest.TestCase):
    def test_original_optimizer_arithmetic_is_preserved(self):
        ledger=StructuralStateLedger()
        new=BackgroundWeightOptimizer(ledger)
        namespace=original_classes('BackgroundWeightOptimizer.py')
        namespace['time']=types.SimpleNamespace(sleep=lambda delay:None)
        old_ledger=StructuralStateLedger()
        old=namespace['BackgroundWeightOptimizer'](old_ledger)
        update=old_ledger.update_weights
        def one_update(weights,mean):
            update(weights,mean)
            old.running=False
        old_ledger.update_weights=one_update
        with redirect_stdout(io.StringIO()):old.run()
        new.step_once()
        self.assertEqual(ledger.get_weights(),old_ledger.get_weights())
        for actual,expected in zip(ledger.current_weights,[.235,.2375,.2325,.235,.2375]):
            self.assertAlmostEqual(actual,expected,places=12)

    def test_original_gate_rules_and_counter_updates_are_preserved(self):
        original_gateway=original_classes('ProductionNetworkGateway.py')['ProductionNetworkGateway']
        original_ledger=original_classes('StructuralStateLedger.py')['StructuralStateLedger']
        for mean,text in ((.2,'cooperation efficiency'),(.8,'cooperation efficiency'),(.8,'hoard monopolize'),
                          (.6,'protect floor hoard'),(.5999,'protect floor'),(.9,'cooperation hoard'),(.9,'sky-elevator')):
            with self.subTest(mean=mean,text=text):
                old_l,new_l=original_ledger(),StructuralStateLedger()
                old_l.update_weights([mean]*5,mean);new_l.update_weights([mean]*5,mean)
                request={'text':text,'bits':[0,1,0,1]}
                class Client:
                    response=None
                    def recv(self,count):return json.dumps(request).encode()
                    def send(self,data):self.response=json.loads(data)
                    def close(self):pass
                client=Client()
                original_gateway(old_l).handle_client_connection(client)
                new_response=ProductionNetworkGateway(new_l).process_payload(request)
                self.assertEqual(client.response,{key:new_response[key] for key in client.response})
                self.assertEqual(old_l.read_ledger(),new_l.read_ledger())

    def test_convergence_and_ledger_reference_are_shared(self):
        session=DesktopSession()
        try:
            before=session.optimizer.snapshot()['rmse']
            self.assertIs(session.gateway.ledger,session.optimizer.ledger)
            for _ in range(100):session.optimizer.step_once()
            self.assertLess(session.optimizer.snapshot()['rmse'],before*.01)
            response=session.gateway.process_payload({'text':'cooperation protect','bits':[1,0]})
            self.assertTrue(response['virtue_pass'])
            self.assertEqual(session.ledger.read_ledger()['lowest_floor_current'],250)
            self.assertEqual(session.ledger.read_ledger()['upper_floor_wealth'],1000)
        finally:session.close()

    def test_weight_validation_and_defensive_copies(self):
        ledger=StructuralStateLedger()
        values=[.5]*5
        ledger.update_weights(values,.5);values[0]=0
        self.assertEqual(ledger.current_weights[0],.5)
        for invalid in ([1]*4,[2]*5,[float('nan')]*5,[True]*5):
            with self.assertRaises(ValueError):ledger.set_targets(invalid)
        with self.assertRaises(ValueError):ledger.update_weights([.5]*5,.1)
        gateway=ProductionNetworkGateway(ledger)
        for bits in ([True],[2],'0101'):
            with self.assertRaises(ValueError):gateway.process_payload({'text':'protect','bits':bits})

    def test_pause_and_stop_end_worker_updates(self):
        ledger=StructuralStateLedger();optimizer=BackgroundWeightOptimizer(ledger,60)
        optimizer.start()
        try:
            optimizer.resume_engine()
            deadline=time.monotonic()+2
            while optimizer.steps<3 and time.monotonic()<deadline:time.sleep(.01)
            self.assertGreaterEqual(optimizer.steps,3)
            optimizer.pause_engine();steps=optimizer.steps
            time.sleep(.07)
            self.assertEqual(optimizer.steps,steps)
        finally:optimizer.stop_engine()
        self.assertFalse(optimizer.is_alive())

    def test_combined_session_save_load_and_invalid_load_is_atomic(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temp:
            self.assertEqual(Path(temp).resolve().parent,Path(__file__).resolve().parent)
            session=DesktopSession(temp);restored=DesktopSession(temp)
            try:
                session.neural.train_steps(40)
                for _ in range(30):session.optimizer.step_once()
                session.gateway.process_payload({'text':'cooperation protect floor','bits':[0,1]})
                saved=session.save()
                restored.load(saved)
                self.assertEqual(restored.ledger.to_dict(),session.ledger.to_dict())
                self.assertEqual(restored.optimizer.steps,30)
                self.assertEqual(restored.neural.model.steps,40)
                self.assertFalse(restored.optimizer.running)
                self.assertFalse(restored.neural.running)
                self.assertFalse(restored.gateway.running)
                before=restored.checkpoint()
                bad=copy.deepcopy(before);bad['ledger']['current_weights'][0]=float('nan')
                with self.assertRaises(ValueError):restored.load_data(bad)
                after=restored.checkpoint()
                before.pop('created');after.pop('created')
                self.assertEqual(before,after)
            finally:session.close();restored.close()

    def test_earlier_neural_checkpoint_can_be_imported(self):
        session=DesktopSession()
        try:
            session.neural.train_steps(25);saved=session.neural.checkpoint()
            session.neural.train_steps(10)
            session.optimizer.step_once();weights=session.ledger.get_weights()
            session.load_data(saved)
            self.assertEqual(session.neural.model.steps,25)
            self.assertEqual(session.ledger.get_weights(),weights)
        finally:session.close()


class NativeWidgetTests(unittest.TestCase):
    def test_native_tabs_draw_and_share_the_engines(self):
        app=GodmindDesktop(start_workers=False,restore_last=False,visible=False)
        try:
            app.update_idletasks()
            self.assertEqual(len(app.tabs.tabs()),3)
            self.assertIn('METAPHOR NODE',app.original_output.get('1.0','end'))
            self.assertGreater(len(app.network_canvas.find_all()),140)
            self.assertGreater(len(app.map_canvas.find_all()),1600)
            app.tabs.select(1);app.tick()
            self.assertGreater(len(app.weight_canvas.find_all()),20)
            app.session.optimizer.step_once();app.tick()
            self.assertEqual(app.weight_stats[2].get(),'1')
            app.process_request();app.tick()
            self.assertEqual(app.gate_title.get(),'INVERSION MODE')
            for _ in range(35):app.session.optimizer.step_once()
            app.process_request();app.tick()
            self.assertEqual(app.gate_title.get(),'PRESERVATION MODE')
            self.assertNotIn('Display update:',app.status.get())
        finally:
            app.autosave.set(False);app.on_close()


class TCPGatewayTests(unittest.TestCase):
    def setUp(self):
        self.gateway=ProductionNetworkGateway(StructuralStateLedger(),port=0)
        self.gateway.start_gateway()

    def tearDown(self):self.gateway.stop_gateway()

    def request(self,chunks):
        with socket.create_connection(('127.0.0.1',self.gateway.port),timeout=3) as client:
            for chunk in chunks:client.sendall(chunk)
            response=bytearray()
            while b'\n' not in response:
                part=client.recv(4096)
                if not part:break
                response.extend(part)
            return json.loads(response)

    def test_fragmented_json_and_legacy_request(self):
        request=json.dumps({'text':'cooperation café','bits':[0,1]},ensure_ascii=False).encode()
        result=self.request([request[:6],request[6:20],request[20:]+b'\n'])
        self.assertEqual(result['output_bits'],[1,0])
        result=self.request([request])
        self.assertEqual(result['transformation_state'],'INVERSION_MODE')

    def test_malformed_or_invalid_payload_returns_error(self):
        self.assertEqual(self.request([b'{bad}\n'])['status'],'ERROR')
        self.assertEqual(self.request([b'{"bits":[2]}\n'])['status'],'ERROR')
        self.assertEqual(self.request([b'[]\n'])['status'],'ERROR')

    def test_gateway_stop_closes_partial_connections_and_can_restart(self):
        client=socket.create_connection(('127.0.0.1',self.gateway.port),timeout=3)
        try:
            client.sendall(b'{"text":')
            self.gateway.stop_gateway()
            self.assertFalse(self.gateway.running)
            self.gateway.port=0
            self.gateway.start_gateway()
            self.assertEqual(self.request([b'{"bits":[1]}\n'])['output_bits'],[0])
        finally:client.close()


if __name__=='__main__':unittest.main(verbosity=2)
