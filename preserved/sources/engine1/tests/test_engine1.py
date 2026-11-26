"""Behavioral and mathematical checks for the upgraded local neural lab."""
import copy
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from drillscript import RecursiveDrillEngine, inputs, make_handler, ThreadingHTTPServer
from module2 import TotalBitRealityEngine


class NeuralTests(unittest.TestCase):
    def test_gradients_match_finite_differences(self):
        model = TotalBitRealityEngine(7)
        x = np.array([[.2, -.3], [-.7, .8], [.9, .4]])
        y = np.array([[0.], [1.], [1.]])
        _, gradients = model.loss_and_gradients(x, y)
        for parameter, gradient in zip(model.parameters, gradients):
            for index in np.ndindex(parameter.shape):
                before = parameter[index]
                parameter[index] = before + 1e-5
                plus = model.evaluate(x, y)['loss']
                parameter[index] = before - 1e-5
                minus = model.evaluate(x, y)['loss']
                parameter[index] = before
                self.assertAlmostEqual((plus-minus)/2e-5, gradient[index], places=7)

    def test_all_presets_learn_held_out_data(self):
        for dataset in inputs.DATASETS:
            with self.subTest(dataset=dataset):
                engine = RecursiveDrillEngine(dataset)
                before = engine.metrics['test_loss']
                engine.train_steps(1000)
                engine.record_metrics()
                print(dataset, engine.metrics)
                self.assertLess(engine.metrics['test_loss'], before*.3)
                self.assertGreaterEqual(engine.metrics['test_accuracy'], .93)

    def test_deterministic_and_exact_checkpoint_resume(self):
        a, b = RecursiveDrillEngine(), RecursiveDrillEngine()
        a.train_steps(31)
        b.train_steps(31)
        np.testing.assert_array_equal(a.model.predict(a.test_x), b.model.predict(b.test_x))
        a.active = True
        a.reveal()
        checkpoint = json.loads(json.dumps(a.checkpoint()))
        b.load(checkpoint)
        a.train_steps(100)
        b.train_steps(100)
        self.assertEqual(a.model.steps, b.model.steps)
        for first, second in zip(a.model.parameters, b.model.parameters):
            np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(a.train_x, b.train_x)

    def test_active_learning_preserves_holdout_and_labels(self):
        engine = RecursiveDrillEngine()
        old_x, old_y = engine.test_x.copy(), engine.test_y.copy()
        uncertainty = np.abs(engine.model.predict(engine.pool_x).ravel() - .5)
        selected = np.argsort(uncertainty, kind='stable')[:16]
        expected_x, expected_y = engine.pool_x[selected].copy(), engine.pool_y[selected].copy()
        self.assertEqual(engine.reveal(), 16)
        np.testing.assert_array_equal(engine.train_x[-16:], expected_x)
        np.testing.assert_array_equal(engine.train_y[-16:], expected_y)
        np.testing.assert_array_equal(engine.test_x, old_x)
        np.testing.assert_array_equal(engine.test_y, old_y)
        for _ in range(50):
            engine.reveal()
        self.assertEqual(engine.queried, 640)
        self.assertEqual(engine.reveal(), 0)

    def test_invalid_checkpoint_is_atomic(self):
        engine = RecursiveDrillEngine()
        engine.train_steps(20)
        checkpoint = engine.checkpoint()
        broken = copy.deepcopy(checkpoint)
        broken['model']['weights'][0][0][0] = float('nan')
        with self.assertRaises(ValueError):
            engine.load(broken)
        np.testing.assert_array_equal(engine.model.weights[0], checkpoint['model']['weights'][0])
        broken = copy.deepcopy(checkpoint)
        broken['test_x'][0] = broken['train_x'][0]
        with self.assertRaises(ValueError):
            engine.load(broken)
        self.assertEqual(engine.model.steps, 20)

    def test_csv_split_save_restore_manual_example(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            engine = RecursiveDrillEngine(checkpoint_path=Path(directory)/'latest.json')
            csv = 'x,y,label\n' + '\n'.join(f'{(i-20)/21},{i/45},{i%2}' for i in range(40))
            engine.command('import', {'csv': csv})
            self.assertEqual((len(engine.train_x),len(engine.test_x)), (32,8))
            self.assertEqual(engine.dataset,'custom')
            self.assertFalse(engine.active)
            self.assertEqual(len(set(map(tuple,engine.train_x)) & set(map(tuple,engine.test_x))),0)
            engine.command('sample', {'x':-.5,'y':-.3,'label':1})
            engine.train_steps(15)
            engine.command('save', {})
            engine.reset('rings',2)
            engine.command('restore', {})
            self.assertEqual(engine.model.steps,15)
            self.assertEqual(len(engine.train_x),33)
            self.assertEqual(engine.dataset,'custom')
            self.assertFalse(engine.running)

    def test_invalid_user_inputs(self):
        engine=RecursiveDrillEngine()
        for row in ({'x':2,'y':0,'label':1},{'x':0,'y':float('nan'),'label':1},
                    {'x':0,'y':0,'label':.3},{'x':True,'y':0,'label':1}):
            with self.assertRaises(ValueError): engine.command('sample',row)
        with self.assertRaises(ValueError): engine.command('configure',{'learning_rate':0})
        with self.assertRaises(ValueError): inputs.read_csv('x,y,label\n0,0,0')
        with self.assertRaises(ValueError): engine.reset('moons',-1)
        with self.assertRaises(ValueError): engine.command('sample',dict(zip(('x','y','label'),[*engine.test_x[0],int(engine.test_y[0,0])])))
        self.assertEqual(engine.model.steps,0)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=RecursiveDrillEngine()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(cls.engine,'test-token'))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.port=cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(3)

    def call(self,path,body=None,token='test-token',extra=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        headers={'Content-Type':'application/json','X-Mesh-Token':token}
        headers.update(extra or {})
        connection.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers)
        response=connection.getresponse()
        data=response.read()
        connection.close()
        return response.status,data

    def test_live_routes_and_controls(self):
        status,body=self.call('/')
        self.assertEqual(status,200)
        self.assertIn(b'const TOKEN=\'test-token\'',body)
        self.assertNotIn(b'__MESH_TOKEN__',body)
        status,body=self.call('/api/state')
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(body)['grid']),41*41)
        self.assertEqual(self.call('/api/control',{'action':'step'})[0],200)
        self.assertEqual(self.call('/api/probe',{'x':.25,'y':.25})[0],200)
        self.assertEqual(self.call('/api/control',{'action':'sample','x':2,'y':0,'label':1})[0],400)
        self.assertEqual(self.call('/api/checkpoint')[0],200)
        self.assertEqual(self.call('/api/examples')[0],200)

    def test_loopback_origin_token_guards(self):
        self.assertEqual(self.call('/api/control',{'action':'start'},token='bad')[0],403)
        self.assertEqual(self.call('/api/control',{'action':'start'},extra={'Origin':'https://example.com'})[0],403)
        self.assertEqual(self.call('/api/state',extra={'Host':'example.com'})[0],403)
        self.assertEqual(self.call('/missing')[0],404)

    def test_original_logic_route_keeps_neural_state(self):
        previous_steps=self.engine.model.steps
        status,body=self.call('/api/original-logic')
        self.assertEqual(status,200)
        data=json.loads(body)
        self.assertTrue(data['all_sources_unchanged'])
        self.assertEqual(data['recursive_drill']['initial_state']['system_status'],'HARMONIZED')
        self.assertIn('METAPHOR NODE',data['console'])
        self.assertEqual(self.engine.model.steps,previous_steps)
        self.assertEqual(self.call('/api/original-logic',extra={'Host':'example.com'})[0],403)


if __name__=='__main__': unittest.main(verbosity=2)

