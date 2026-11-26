import contextlib,copy,hashlib,json,math,os,random,re,socket,sys,tempfile,threading,time,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'runtime'))
from neural_app import translation as btq
from neural_app.runtime import Runtime,SECTIONS
from neural_app.network import Bus
from neural_app.server import create_server

WORK=ROOT.parents[1]/'work'/'verification';WORK.mkdir(parents=True,exist_ok=True)

class TransportTests(unittest.TestCase):
    def test_round_trip_exact_bytes(self):
        for raw in (b'',b'\0\0hello\0',bytes(range(256)),os.urandom(16384),'Neural 🌍 · 三進数'.encode()):
            self.assertEqual(btq.decode(btq.encode(raw)),raw)
    def test_fourier_states_and_orthogonality(self):
        for i in range(3):
            self.assertEqual(btq.inverse_fourier(btq.fourier(i)),i)
            for j in range(3):
                overlap=sum(complex(a['real'],-a['imag'])*complex(b['real'],b['imag']) for a,b in zip(btq.fourier(i),btq.fourier(j)))
                self.assertAlmostEqual(abs(overlap)**2,1 if i==j else 0,places=10)
    def test_leading_zeroes_and_full_width(self):
        for bits in ('0','0000','001011','0'*4096,'1'*4096,'01'*2048):
            result=btq.translate_bits(bits);self.assertEqual(result['recovered_binary'],bits)
            self.assertEqual(''.join(str(btq.inverse_fourier(q['amplitudes'])) for q in result['qutrits']),result['ternary'])
    def test_corruption_rejected(self):
        original=btq.encode(b'\0Neural App')
        for change in ('checksum','balanced','qutrit','size'):
            value=copy.deepcopy(original)
            if change=='checksum':value['sha256']='0'*64
            if change=='balanced':value['blocks'][0]['balanced']='0'
            if change=='qutrit':value['qutrit_basis'][1][0]['real']=100
            if change=='size':value['bytes']+=1
            with self.assertRaises(ValueError):btq.decode(value)

class RuntimeTests(unittest.TestCase):
    def setUp(self):self.folder=tempfile.TemporaryDirectory(dir=WORK);self.r=Runtime(self.folder.name,start=False)
    def tearDown(self):self.r.close();self.folder.cleanup()
    def test_combined_pipeline_and_stage_transport(self):
        before=self.r.get_model().state();value=self.r.pipeline({'text':'Measured local processing; keep evidence and privacy.'})
        self.assertGreater(self.r.model.updates,before['updates']);self.assertNotEqual(before['w'],self.r.model.w)
        self.assertEqual(set(value['stages']),{x['stage'] for x in value['transfers']})
        self.assertTrue(all(x['round_trip'] for x in value['transfers']))
        ident=self.r.record('pipeline',{'text':'measured'},value,1);saved=self.r.receipts(ident)
        raw=b''.join(btq.decode(p) for p in saved['transport']['packets'])
        self.assertEqual(json.loads(raw),saved['result'])
    def test_no_self_generated_preference_labels(self):
        self.r.pipeline({'text':'Unlabelled input'})
        self.assertEqual(self.r.model.supervised,0)
        with self.r.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM examples').fetchone()[0],0)
    def test_original_flux_weights_resume_without_reset(self):
        path=ROOT/'preserved'/'database-weights'/'flux-model-1.json'
        if not path.exists():self.skipTest('No prior Flux model supplied')
        original=json.loads(path.read_text(encoding='utf8'))
        self.r.pipeline({'text':'Resume the supplied learned engine parameters'})
        self.assertEqual(self.r.original_baseline,original['updates'])
        self.assertGreater(self.r.original_model.updates,original['updates'])
        self.assertEqual(self.r.original_model.n,sum(size for _,size in self.r.original_model.groups))
    def test_review_learns_and_cannot_double_count(self):
        result=self.r.engine('flux',{});ident=self.r.record('flux',{},result,1)
        learned=self.r.feedback({'receipt':ident,'target':1,'note':'Reviewed actual result'})
        self.assertGreater(learned['after_score'],learned['before_score'])
        with self.assertRaises(ValueError):self.r.feedback({'receipt':ident,'target':1})
        self.assertEqual(self.r.model.supervised,1);self.assertEqual(self.r.utility['flux']['reviews'],1)
    def test_missing_observations_are_masked(self):
        x,mask=self.r.feature_vector({'karmic_welfare':{'status':'AWAITING_INPUT'}})
        self.assertEqual(sum(mask),0)
    def test_weights_survive_restart(self):
        self.r.pipeline({'text':'persistent engine results'});expected=self.r.model.state();self.r.checkpoint()
        restored=Runtime(self.folder.name,start=False)
        try:self.assertEqual(restored.model.state(),expected)
        finally:restored.close()
    def test_all_integrated_sections_execute(self):
        for name in SECTIONS:
            with self.subTest(section=name):
                body={'text':'Human wellbeing and measured evidence','batches':1}
                if name=='outreach':body['nodes']=[{'id':'test-node','need':1,'consent':False}]
                value=self.r.engine(name,body)
                self.r.transport_result(value)
    def test_reference_examples_execute(self):
        from neural_app.engines.flux_library.reference_catalog import examples
        from neural_app.engines.flux_library.reference_runtime import execute_one
        for name,config in examples().items():
            with self.subTest(engine=name):self.assertEqual(execute_one(name,config)['status'],'COMPLETE')
    def test_neural_training_reduces_validation_loss(self):
        from neural_app.engines.classifier import NeuralNetwork,make_dataset
        net=NeuralNetwork();train=make_dataset('XOR');held=make_dataset('XOR',96,104);before=net.evaluate(held)[0];rng=random.Random(7)
        for _ in range(800):net.train_batch(rng.sample(train,24),.08)
        loss,accuracy=net.evaluate(held);self.assertLess(loss,before*.5);self.assertGreater(accuracy,.85)
    def test_queue_bounded_and_no_legacy_workers(self):
        count=threading.active_count()
        for _ in range(16):self.r.submit('flux',{})
        with self.assertRaises(ValueError):self.r.submit('flux',{})
        self.assertEqual(threading.active_count(),count)

class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(dir=WORK);self.r=Runtime(self.folder.name);self.bus=Bus(self.r,port=0,discovery_port=0)
        self.http=create_server(self.r,port=0,bus=self.bus);self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.http.server_address[1]);html=urlopen(self.base,timeout=5).read().decode();self.token=re.search("window.NEURAL_TOKEN='([^']+)'",html).group(1)
    def tearDown(self):self.http.shutdown();self.http.server_close();self.bus.close();self.r.close();self.folder.cleanup()
    def request(self,path,body=None,token=True):
        req=Request(self.base+'/api/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'X-Neural-Token':self.token if token else '', 'Content-Type':'application/json'})
        with urlopen(req,timeout=10) as response:return json.load(response)
    def test_http_auth_and_real_command(self):
        with self.assertRaises(HTTPError) as err:self.request('state',token=False)
        self.assertEqual(err.exception.code,403)
        j=self.request('run',{'section':'translation','input':{'bits':'000110'}})
        for _ in range(100):
            result=self.request('job?id='+j['id'])
            if result['status'] in ('complete','error'):break
            time.sleep(.02)
        self.assertEqual(result['status'],'complete');self.assertEqual(result['result']['recovered_binary'],'000110')
    def tcp(self,payload):
        with socket.create_connection(('127.0.0.1',self.bus.port),timeout=5) as conn:
            conn.sendall((json.dumps(payload)+'\n').encode());return json.loads(conn.makefile('rb').readline())
    def test_tcp_auth_publish_and_subscription(self):
        self.assertIn('error',self.tcp({'op':'publish','token':'wrong','data':{}}))
        with socket.create_connection(('127.0.0.1',self.bus.port),timeout=5) as subscriber:
            subscriber.sendall((json.dumps({'op':'subscribe','token':self.bus.key})+'\n').encode());stream=subscriber.makefile('rb');self.assertEqual(json.loads(stream.readline())['type'],'subscribed')
            accepted=self.tcp({'op':'publish','token':self.bus.key,'section':'flux','data':{}})
            self.assertEqual(accepted['type'],'accepted');event=json.loads(stream.readline());self.assertEqual(event['job'],accepted['job']['id'])
            result=self.tcp({'op':'result','token':self.bus.key,'id':event['job']});self.assertEqual(result['status'],'complete')
    def test_udp_discovery_no_private_content(self):
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as conn:
            conn.settimeout(5);conn.sendto(b'NEURAL_DISCOVER',('127.0.0.1',self.bus.discovery_port));data=json.loads(conn.recvfrom(4096)[0])
        self.assertEqual(data['tcp_port'],self.bus.port);self.assertNotIn('token',data);self.assertNotIn('result',data)
    def test_scenes_and_saved_history(self):
        req=Request(self.base+'/api/scene?preset=Earth',headers={'X-Neural-Token':self.token})
        with urlopen(req,timeout=10) as response:self.assertEqual(response.headers['Content-Type'],'image/jpeg');self.assertGreater(len(response.read()),10000)
        created=self.request('chat/new',{'provider':'llama'});self.assertEqual(self.request('chat/history?thread='+created['id'])['items'],[])

if __name__=='__main__':unittest.main(verbosity=2)
