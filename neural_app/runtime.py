"""One owner for computation, state, learning and durable receipts.

No original application entry point, server, embedded window or launcher runs.
The bounded command queue and one scheduler replace per-application workers.
"""
from __future__ import annotations
import collections, contextlib, hashlib, importlib, json, math, os, queue, random, sqlite3, threading, time, uuid
from dataclasses import asdict
from pathlib import Path
from . import translation as btq
from .engines import classifier, signals, field, flux, core
from .engines.profiles.ledger import StructuralStateLedger
from .engines.profiles.optimizer import BackgroundWeightOptimizer
from .gates import EngineWeights

ROOT=Path(__file__).resolve().parents[1]
SECTIONS={
 'focus_study':'Focused workshop · faith, design and care',
 'runinplace':'Run in place · exact register and feedback engine',
 'infrastructure':'Energy and ISP overlay · protected resource planning',
 'matrix_study':'The Matrix · recognition and care',
 'super_mesh':'Super-mesh · needs-first care policy',
 'x4_economy':'Resource economy · resilience and care',
 'watts_study':'Alan Watts · listening and care',
 'intent_channel':'Prayer-led intention channel',
 'iching':'Book of Changes · traditional and adapted readings',
 'gnostic_four':'Four voices · knowledge into life',
 'living_circuit':'Living Circuit · order, chaos and renewal',
 'discipline':'Bushido, Bagua and contemplative practice',
 'wooden_cup':'The wooden cup · true value',
 'matter_spirit':'Matter, spirit and the way of life',
 'source_atlas':'Desktop Java · unique code and graphics',
 'signals':'Hydrogen signal packets', 'translation':'Binary · ternary · qutrit',
 'classifier':'Neural classifier', 'field':'Recurrent field', 'core':'Core interaction',
 'flux':'Flux core', 'suite':'Register engine suite', 'unified':'Unified infrastructure',
 'platform_alignment':'Platform alignment','karmic_welfare':'Welfare models',
 'virtue_text':'Text transforms','reference':'Reference engines','profiles':'Profile optimizer',
 'sovereign':'Hydrogen · stellar · biosphere','scenario':'Scenario neural forecast',
 'alignment':'Whole-input alignment','dualrail':'Parallel dual-rail engine','inference':'Inference engine collection',
 'outreach':'Humane network and need-first outreach',
 'theology':'Theology research and Gnostic bridge',
 'beacon':'Inference beacon and route planner',
 'intent_dispatch':'Road Runner and Taz · need-first routing strategies',
 'care':'Care for all life · practical planning','academy':'Learning curriculum evidence','causal':'Redemption of Islam / Muslims · active lessons'}

def model_groups():
    panels=json.loads((ROOT/'original-panels.json').read_text(encoding='utf8'))
    imported=ROOT/'references'/'desktop-java'/'panels.json'
    if imported.exists():panels+=json.loads(imported.read_text(encoding='utf-8'))
    return [(s,3) for s in SECTIONS]+[('section/'+p['id'],3) for p in panels]

def clean(value):
    if hasattr(type(value),'tolist'):return value.tolist()
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(tuple,list,collections.deque)):return [clean(v) for v in value]
    if isinstance(value,complex):return {'real':value.real,'imag':value.imag}
    if isinstance(value,bytes):return {'hex':value.hex()}
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('Engine produced a nonfinite result')
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return str(value)

class Runtime:
    def __init__(self,data=None,start=True):
        self.data=Path(data or ROOT/'data');self.data.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.halt=threading.Event();self.queue=queue.Queue(maxsize=16)
        self.jobs=collections.OrderedDict();self.latest={};self.history=collections.deque(maxlen=160)
        self.rng=random.Random(19);self.started=time.time();self.listeners=[];self.errors=collections.deque(maxlen=20)
        self.settings={'pace':'low','learning':True,'field':False,'synthetic_training':False,'profiles':False,'lan':False,
                       'goal':'Integrate local engines, preserve exact data, learn from measured results and reviewed feedback.'}
        self.net=classifier.NeuralNetwork();self.dataset='XOR';self.rate=.08
        self.field=field.Engine();self.core=core.CoreEngine();self.core.start()
        self.ledger=StructuralStateLedger();self.optimizer=BackgroundWeightOptimizer(self.ledger)
        self.research_public={};self.delivery={'subscribers':0,'events':0,'peer_writes':0,'bytes_written':0};self.theology_public=None;self.instances={};self.model=None;self.original_model=None;self.original_baseline=0;self.last_reconstruction=None;self.utility={s:{'positive':1.,'negative':1.,'reviews':0} for s in SECTIONS}
        self.gates=EngineWeights(self.data,SECTIONS)
        from .process_observatory import ProcessObservatory
        self.process_observatory=ProcessObservatory()
        self.db_path=self.data/'neural.sqlite3'
        with self.db() as db:
            db.executescript('PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY,stamp REAL,section TEXT,input TEXT,result TEXT,transport TEXT,latency REAL); CREATE TABLE IF NOT EXISTS causal_receipts(receipt INTEGER PRIMARY KEY,trace TEXT NOT NULL); CREATE TABLE IF NOT EXISTS examples(receipt INTEGER PRIMARY KEY,target REAL,note TEXT,stamp REAL); CREATE TABLE IF NOT EXISTS training_drafts(id INTEGER PRIMARY KEY,prompt TEXT,answer TEXT,approved INTEGER DEFAULT 0,stamp REAL);')
        from .active_lesson import ActiveLesson
        from .device_hub import DeviceHub
        self.device_hub=DeviceHub(self)
        self.lesson_delivery=None
        self.causal=ActiveLesson(self.data,on_packet=self.publish_lesson)
        self.restore();self.worker=threading.Thread(target=self.loop,name='neural-shared-scheduler',daemon=True)
        from .research_intake import ResearchIntake
        self.research=ResearchIntake(self)
        from .activity_intake import ActivityIntake
        self.activity=ActivityIntake(self)
        from .google_index import GoogleIndex
        self.google_index=GoogleIndex(self)
        from .opera_workspace import OperaWorkspace
        self.opera_workspace=OperaWorkspace(self.data)
        if (self.data/'matrix-study-settings.json').exists():self.matrix_study()
        if (self.data/'x4-economy-settings.json').exists():self.economy()
        if (self.data/'inference-workers.json').exists():self.inference_workers()
        if (self.data/'automatic-flow.json').exists():self.automatic_flow()
        if (self.data/'watts-study-settings.json').exists():self.watts_study()
        if (self.data/'iching-settings.json').exists():self.changes()
        if (self.data/'four-texts-settings.json').exists():self.four_texts()
        if (self.data/'living-circuit.json').exists():self.living_circuit()
        if start:self.runinplace();self.focus_study();self.logic_cube()
        if start:self.causal.start();self.worker.start();self.research.start();self.activity.start()
        atlas_settings=self.data/'source-atlas-settings.json'
        if start and atlas_settings.exists() and json.loads(atlas_settings.read_text(encoding='utf-8')).get('process_on_start') is True:self.source_atlas().start_batch()

    @contextlib.contextmanager
    def db(self):
        db=sqlite3.connect(self.db_path,timeout=10)
        try:
            with db:yield db
        finally:db.close()

    def restore(self):
        path=self.data/'checkpoint.json';imported=False
        if not path.exists():path=ROOT/'preserved'/'data'/'checkpoint.json';imported=True
        if not path.exists():return
        try:
            b=json.loads(path.read_text(encoding='utf8'));self.net=classifier.NeuralNetwork.from_dict(b['network']);self.dataset=b.get('dataset','XOR')
            if self.dataset not in classifier.DATASETS:raise ValueError('Unknown dataset')
            self.rate=float(b.get('rate',.08))
            if not .001<=self.rate<=.5:raise ValueError('Invalid learning rate')
            if not imported:
                self.research_public=b.get('public_research',{})
                self.theology_public=b.get('public_theology')
                self.settings.update(b.get('settings',{}));self.settings['lan']=False
                self.ledger.restore(b['ledger']);self.optimizer.restore(b['optimizer'])
                if b.get('learner'):
                    from .engines.flux_library.neural_model import NeuralModel
                    self.model=NeuralModel.from_state(b['learner'])
                    self.model=self.model.expanded(model_groups())
                self.utility.update({k:v for k,v in b.get('utility',{}).items() if k in SECTIONS})
                if b.get('original_learner'):
                    from .engines.flux_library.neural_model import NeuralModel
                    self.original_model=NeuralModel.from_state(b['original_learner']).expanded();self.original_baseline=b.get('original_baseline',0)
            f=b.get('field',{})
            for name in ('noise','bias','feedback_gain'):
                if name in f:self.field.command(('feedback' if name=='feedback_gain' else name)+' '+str(f[name]))
            self.imported_checkpoint=imported
        except Exception as e:self.errors.append('Checkpoint not restored: '+str(e))

    def checkpoint(self):
        with self.lock:
            b={'format':'neural-app-v1','network':self.net.to_dict(),'dataset':self.dataset,'rate':self.rate,
               'settings':self.settings,'ledger':self.ledger.to_dict(),'optimizer':self.optimizer.snapshot(),
               'field':{k:getattr(self.field,k) for k in ('noise','bias','feedback_gain')},'learner':self.model.state() if self.model else None,'utility':self.utility,
               'original_learner':self.original_model.state() if self.original_model else None,'original_baseline':self.original_baseline,
               'public_research':self.research_public,'public_theology':self.theology_public}
            self.causal.save()
            path=self.data/'checkpoint.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(b,allow_nan=False),encoding='utf8');tmp.replace(path);self.gates.save()
        return {'saved':True,'network_updates':self.net.updates,'learned_updates':self.model.updates if self.model else 0}

    def submit(self,section,body):
        if section not in SECTIONS and section!='pipeline':raise ValueError('Unknown section')
        if not isinstance(body,dict):raise ValueError('Input must be an object')
        # All jobs cross the same lossless BTQ contract before execution.
        packet=btq.envelope(body);decoded=json.loads(btq.decode(packet))
        ident=uuid.uuid4().hex
        with self.lock:
            job={'id':ident,'section':section,'status':'queued','created':time.time()}
            self.jobs[ident]=job
            try:self.queue.put_nowait((ident,section,decoded))
            except queue.Full:self.jobs.pop(ident);raise ValueError('The 16-item queue is full; wait for a result')
            while len(self.jobs)>128:
                key=next(iter(self.jobs))
                if self.jobs[key]['status'] in ('queued','running'):break
                self.jobs.pop(key)
        return dict(job)

    def result(self,ident):
        with self.lock:
            if ident not in self.jobs:raise ValueError('Job not found')
            return dict(self.jobs[ident])

    def engine(self,section,b):
        text=b.get('text','')
        if not isinstance(text,str) or len(text)>10000:raise ValueError('Use at most 10,000 text characters')
        if section=='focus_study':return self.focus_study().process(b)
        if section=='runinplace':return self.runinplace().process(b)
        if section=='infrastructure':
            from .infrastructure_lab import process
            return process(self,b)
        if section=='matrix_study':return self.matrix_study().process(b)
        if section=='super_mesh':
            from .super_mesh import resolve
            return resolve(self,b)
        if section=='x4_economy':return self.economy().measure(b)
        if section=='gnostic_four':return self.four_texts().process(b)
        if section=='living_circuit':return self.living_circuit().measure(b)
        if section=='watts_study':return self.watts_study().process(b)
        if section=='iching':return self.changes().process(b)
        if section=='intent_channel':
            from .intent_channel import process
            return process(b)
        if section=='discipline':
            from .discipline import process
            return process(b)
        if section=='wooden_cup':
            from .wooden_cup import process
            return process(b)
        if section=='matter_spirit':
            from .matter_spirit import process
            return process(b)
        if section=='source_atlas':return self.source_atlas().measure(b)
        if section=='outreach':
            from .outreach_plan import plan_outreach
            return plan_outreach(b)
        if section=='theology':
            from .theology import compare
            value=compare(b);value['neural_routing_signal']=self.net.predict(value['routing_features']);return value
        if section=='intent_dispatch':
            from .intent_dispatch import resolve
            return resolve(b)
        if section=='beacon':
            from .inference_beacon import resolve
            value=resolve(b)
            if value['route']==['local'] and b.get('execute_local') is True:
                value['local_result']=self.engine('inference',{'text':text})
                value['local_executed']=True
            else:value['local_executed']=False
            return value
        if section=='care':
            from .care_plan import plan
            value=plan(b)
            from .care_audit import audit_care
            value['audit']=audit_care(b,value)
            bits=b.get('bits') or '01'*64
            if not isinstance(bits,str) or len(bits)>4096:raise ValueError('Use up to 4096 bits')
            value['causal']=self.causal.evaluate(bits,parameters={'repair':value['coverage'],'gain':.5*value['coverage']})
            effective=value['causal']['working_bits'];x=[effective.count('1')/len(effective)*2-1,0.]
            value['classifier']={'features':x,'probability':self.net.predict(x),'input_basis':'care plan working bits'}
            return value
        if section=='causal':
            bits=b.get('bits') or ''.join(f'{byte:08b}' for byte in text.encode('utf8')) or '01'*32
            options=b.get('lesson',{})
            if not isinstance(options,dict):raise ValueError('Lesson options must be an object')
            return self.causal.evaluate(bits,parameters=options.get('parameters'),events=options.get('events'))
        if section=='signals':
            return signals.from_bits(b['bits']) if b.get('bits') else signals.generate(b.get('mode','Seeded test'),int(b.get('size',64)),b.get('seed','neural-app'),int(b.get('step',0)))
        if section=='translation':
            bits=b.get('bits') or ''.join(f'{byte:08b}' for byte in text.encode('utf8')) or '0'
            return btq.translate_bits(bits)
        if section=='classifier':
            if b.get('dataset'):
                if b['dataset'] not in classifier.DATASETS:raise ValueError('Unknown dataset')
                self.dataset=b['dataset']
            if 'target' in b:
                x=b.get('features',[0,0]);target=b['target']
                if len(x)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not -1<=v<=1 for v in x) or target not in (0,1):raise ValueError('Use two features from -1 to 1 and a binary target')
                self.net.train_batch([(x,target)],self.rate)
            batches=b.get('batches',0)
            if type(batches) is not int or not 0<=batches<=200:raise ValueError('Use 0–200 batches')
            data=classifier.make_dataset(self.dataset)
            for _ in range(batches):self.net.train_batch(self.rng.sample(data,24),self.rate)
            loss,accuracy=self.net.evaluate(classifier.make_dataset(self.dataset,96,104))
            self.history.append({'step':self.net.updates,'loss':loss,'accuracy':accuracy})
            return {'dataset':self.dataset,'updates':self.net.updates,'loss':loss,'accuracy':accuracy,'scope':'Synthetic classification; distinct from language-model learning'}
        if section=='field':
            self.field.command(b.get('command','pulse'));self.field.step();return self.field.snapshot()
        if section=='core':
            if b.get('framework'):self.core.stop();self.core.configure(core.Framework.parse(json.dumps(b['framework'])));self.core.start()
            self.core.enqueue('shared-input',text or 'Shared engine input',b.get('signal'))
            return asdict(self.core.tick())
        if section=='flux':return flux.execute_master_runall(b.get('options',{}))
        if section=='profiles':
            if 'targets' in b:self.ledger.set_targets(b['targets'])
            if b.get('action')=='elevator':return {'result':self.ledger.execute_sky_elevator(),'ledger':self.ledger.to_dict()}
            steps=b.get('steps',1)
            if type(steps) is not int or not 0<=steps<=200:raise ValueError('Use 0–200 steps')
            for _ in range(steps):self.optimizer.step_once()
            return {'ledger':self.ledger.to_dict(),'optimizer':self.optimizer.snapshot()}
        if section=='sovereign':
            if section not in self.instances:
                from .engines.hydrogen.sovereign import SovereignEngine
                self.instances[section]=SovereignEngine()
            return self.instances[section].process(text or 'Neural App shared input')
        if section=='scenario':
            if section not in self.instances:
                from .engines.scenario import NeuralEngine
                self.instances[section]=NeuralEngine(ROOT/'preserved'/'sources'/'postscarcity'/'PostscarcityHub'/'models')
            return self.instances[section].infer(b.get('scenario',{'access':50,'comfort':50,'transition':50,'automation':50,'valve':True,'gate':True}))
        if section=='alignment':
            from .engines.observatory.alignment_core import AlignmentInvariant
            return AlignmentInvariant().evaluate({'input':text,**b.get('options',{})})
        if section=='dualrail':
            from .engines.observatory.parallel_dual_rail import ParallelDualRailEngine
            if section not in self.instances:self.instances[section]=ParallelDualRailEngine()
            return self.instances[section].execute_synchronized_runall(text)
        if section=='inference':
            from .engines.observatory.resident_engines import ResidentEngines
            if section not in self.instances:self.instances[section]=ResidentEngines()
            return self.instances[section].process({'id':uuid.uuid4().hex,'producer':'neural-app','source':'integrated-section','text':text,'data':b.get('options',{})})
        if section=='academy':return {'status':'recorded','evidence':b,'scope':'Curriculum interaction evidence; this is not an automatic semantic or skill-quality label.'}
        lib='.engines.flux_library.'
        if section=='suite':
            m=importlib.import_module(lib+'engines',__package__);return {'engines':m.run_engine_suite(payload={'text':text,**b.get('options',{})})}
        if section=='unified':
            m=importlib.import_module(lib+'unified_runtime',__package__);return m.execute_unified_engines({'text':text,**b.get('options',{})},self.halt)
        if section=='platform_alignment':
            m=importlib.import_module(lib+section,__package__);return m.PlatformAlignmentEngine().execute({'text':text,**b.get('options',{})},self.halt)
        if section=='karmic_welfare':
            m=importlib.import_module(lib+section,__package__);return m.KarmicWelfareEngine().execute({'text':text,**b.get('options',{})},self.halt)
        if section=='virtue_text':
            m=importlib.import_module(lib+section,__package__);return m.VirtueTextEngine().execute({'text':text,**b.get('options',{})},self.halt)
        if section=='reference':
            m=importlib.import_module(lib+'reference_runtime',__package__);return m.execute_reference({'text':text,**b.get('options',{})},self.halt)
        raise ValueError('Section has no integrated operation')

    def matrix_study(self):
        if not hasattr(self,'_matrix_study'):
            from .matrix_study import MatrixStudy
            self._matrix_study=MatrixStudy(self)
        return self._matrix_study

    def economy(self):
        if not hasattr(self,'_economy'):
            from .x4_economy import Economy
            self._economy=Economy(self)
        return self._economy

    def logic_cube(self):
        if not hasattr(self,'_logic_cube'):
            from .logic_cube import LogicCube
            self._logic_cube=LogicCube(self)
        return self._logic_cube

    def focus_study(self):
        if not hasattr(self,'_focus_study'):
            from .focus_study import FocusStudy
            self._focus_study=FocusStudy(self)
        return self._focus_study

    def runinplace(self):
        if not hasattr(self,'_runinplace'):
            from .runinplace import RunInPlace
            self._runinplace=RunInPlace(self)
        return self._runinplace

    def inference_workers(self):
        if not hasattr(self,'_inference_workers'):
            from .inference_workers import InferenceWorkers
            self._inference_workers=InferenceWorkers(self)
        return self._inference_workers

    def automatic_flow(self):
        if not hasattr(self,'_automatic_flow'):
            from .automatic_flow import AutomaticFlow
            self._automatic_flow=AutomaticFlow(self)
        return self._automatic_flow

    def watts_study(self):
        if not hasattr(self,'_watts_study'):
            from .watts_study import WattsStudy
            self._watts_study=WattsStudy(self)
        return self._watts_study

    def changes(self):
        if not hasattr(self,'_changes'):
            from .iching import Changes
            self._changes=Changes(self)
        return self._changes

    def four_texts(self):
        if not hasattr(self,'_four_texts'):
            from .gnostic_four import FourTexts
            self._four_texts=FourTexts(self)
        return self._four_texts

    def living_circuit(self):
        if not hasattr(self,'_living_circuit'):
            from .living_circuit import LivingCircuit
            self._living_circuit=LivingCircuit(self)
        return self._living_circuit

    def source_atlas(self):
        if not hasattr(self,'_source_atlas'):
            from .source_atlas import SourceAtlas
            self._source_atlas=SourceAtlas(self)
        return self._source_atlas

    def transport_result(self,value):
        raw=json.dumps(clean(value),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        if len(raw)>2_000_000:raise ValueError('Engine result exceeds 2 MB')
        packets=[btq.encode(raw[i:i+btq.MAX_BYTES]) for i in range(0,len(raw),btq.MAX_BYTES)]
        if b''.join(btq.decode(p) for p in packets)!=raw:raise RuntimeError('Result transport failed')
        return {'format':'neural-btq-multipart-v1','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'packets':packets}

    def record(self,section,body,result,elapsed):
        result=clean(result);transport=self.transport_result(result)
        with self.db() as db:
            ident=db.execute('INSERT INTO receipts(stamp,section,input,result,transport,latency) VALUES(?,?,?,?,?,?)',
                (time.time(),section,json.dumps(body),json.dumps(result,ensure_ascii=False),json.dumps(transport),elapsed)).lastrowid
            trace=self.causal.observe(section,transport['sha256'])
            db.execute('INSERT INTO causal_receipts VALUES(?,?)',(ident,json.dumps(trace)))
            with self.field.lock:
                contribution=trace['signal']*trace['neural_weight']*trace['parameters']['influence']
                self.field.script_signal=max(-1,min(1,.9*self.field.script_signal+.1*contribution));self.field.script_at=time.monotonic();self.field.script_samples+=1
            # Keep bounded active receipts; preserved original histories are separate.
            db.execute('DELETE FROM receipts WHERE id < (SELECT MAX(id)-2000 FROM receipts) AND id NOT IN (SELECT receipt FROM examples)')
            db.execute('DELETE FROM causal_receipts WHERE receipt NOT IN (SELECT id FROM receipts)')
        if section=='theology':self.theology_public={**result['compact_public'],'receipt':ident}
        if section=='pipeline' and isinstance(body.get('research'),dict):
            research=body['research'];topic=research.get('topic')
            if topic in ('design_tesla','design_fuller','design_fresco','study_zhuan_falun','falun_plight'):
                self.research_public[topic]={'topic':topic,'receipt':ident,'source_digest':hashlib.sha256(body.get('text','').encode()).hexdigest(),
                    'stages':list(result.get('stages',{})),'learned_updates':result.get('learning',{}).get('updates',0),
                    'records':[{k:str(v)[:2000] for k,v in row.items() if k in ('title','url','published','publisher','doi','reading_status')} for row in research.get('records',[])[:3] if isinstance(row,dict)],
                    'meaning':'Public research metadata processed through shared engines; numerical reconstruction learning.'}
        self.process_observatory.observe(section,transport['sha256'],elapsed,ident)
        self.latest[section]={'receipt':ident,'result':result,'latency_ms':elapsed}
        core=getattr(self,'language_learning_core',None)
        if core:core.observe_runtime(section,ident,transport['sha256'],elapsed,result)
        return ident

    def pipeline(self,b):
        text=b.get('text','');bits=b.get('bits')
        if not isinstance(text,str) or not isinstance(bits,(str,type(None))):raise ValueError('Text and bits must be strings')
        bits=bits or ''.join(f'{byte:08b}' for byte in text.encode('utf8')) or '0'
        if len(bits)>4096:raise ValueError('The combined pipeline accepts up to 4096 input bits (512 UTF-8 bytes)')
        stages={};transfers=[]
        def relay(name,value):
            t=self.transport_result(value);restored=json.loads(b''.join(btq.decode(p) for p in t['packets']))
            transfers.append({'stage':name,'bytes':t['bytes'],'sha256':t['sha256'],'round_trip':True});return restored
        packet=relay('signals',self.engine('signals',{'bits':bits}));stages['signals']=packet
        stages['translation']=self.engine('translation',{'bits':bits})
        if not b.get('full_trace',False):
            # Retain every trit and its exact phase basis once, rather than
            # repeating identical amplitude dictionaries thousands of times.
            tr=stages['translation'];tr.pop('qutrits',None)
            tr['qutrit_encoding']={'phase_indices':tr['ternary'],'basis':[btq.fourier(i) for i in range(3)],'encoding':'Each phase index selects its orthonormal Fourier basis state.'}
        options=b.get('lesson',{})
        if not isinstance(options,dict):raise ValueError('Lesson options must be an object')
        lesson=self.causal.evaluate(bits,parameters=options.get('parameters'),events=options.get('events'));stages['causal']=lesson
        effective=signals.from_bits(lesson['working_bits'])
        x=[effective['ones']/effective['bit_length']*2-1,min(1,len(text)/1000)]
        lesson['counterfactual']['classifier_without_lesson']=self.net.predict([packet['ones']/packet['bit_length']*2-1,x[1]])
        probability=self.net.predict(x);stages['classifier']={'probability':probability,'features':x,'dataset':self.dataset,'input_basis':'active-lesson working bits'}
        lesson['counterfactual']['classifier_with_lesson']=probability
        stages['flux']=self.engine('flux',{'options':{'features':x,'input_mask':int(bits[:32],2),'max_depth':3}})
        stages['core']=self.engine('core',{'text':text or bits,'signal':probability*2-1})
        self.field.script_signal=stages['core']['output'];self.field.script_at=time.monotonic();self.field.script_samples+=1
        self.field.stimulus=stages['core']['output']*.25;self.field.step();stages['field']=self.field.snapshot()
        requested=b.get('sections',['suite','unified','platform_alignment','karmic_welfare','virtue_text','reference'])
        if not isinstance(requested,list) or len(requested)>10 or any(s not in SECTIONS for s in requested):raise ValueError('Invalid pipeline section selection')
        selected=requested[:]
        if b.get('adaptive') and len(selected)>4:
            def rank(name):
                u=self.utility[name];quality=u['positive']/(u['positive']+u['negative'])
                latency=self.latest.get(name,{}).get('latency_ms',0)
                return quality/(1+latency/500)
            selected=sorted(selected,key=rank,reverse=True)[:3]
            exploration=min((s for s in requested if s not in selected),key=lambda s:self.utility[s]['reviews'])
            selected.append(exploration)
        for name in selected:
            if name not in stages:stages[name]=self.engine(name,{'text':text,**b.get('section_inputs',{}).get(name,{})})
        for name,value in stages.items():
            if name!='signals':stages[name]=relay(name,value)
            status=value.get('status','') if isinstance(value,dict) else ''
            if str(status).startswith(('AWAITING','awaiting')):continue
            success=not (isinstance(value,dict) and value.get('status') in ('ERROR','PARTIAL'))
            self.gates.observe({'module':name,'status':'processed' if success else 'error','result':value})
        self.learn(stages,b)
        return {'stages':stages,'learning':self.learning_view(),'input_transport':btq.encode(text.encode()),'transfers':transfers,
                'routing':{'adaptive':bool(b.get('adaptive')),'requested':requested,'selected':selected,'basis':'Reviewed usefulness and recent latency, with one exploration section. Whole-run feedback credits contributing sections equally.'},
                'scope':'Shared local calculations and learned reconstruction. Execution success is not semantic correctness.'}

    def get_model(self):
        groups=model_groups()
        if self.model is None:
            from .engines.flux_library.neural_model import NeuralModel
            # One named feature schema for every integrated section; no missing-engine zero labels.
            self.model=NeuralModel(groups=groups)
        elif self.model.groups!=groups:self.model=self.model.expanded(groups)
        return self.model

    def feature_vector(self,stages):
        from .engines.flux_library.neural_model import result_features
        x=[];mask=[]
        for section,_ in self.get_model().groups:
            value=clean(stages.get(section));status=value.get('status','COMPLETE') if isinstance(value,dict) else 'COMPLETE'
            if str(status).lower().startswith('awaiting'):status='AWAITING_INPUT'
            a,m=result_features(value,status);x.extend(a);mask.extend(m)
        return x,mask

    def component_result(self,ident,body,result,elapsed=0):
        if isinstance(result,dict) and 'ui' in result:
            result={k:result[k] for k in ('engine_fields','output','failure','messages') if k in result}
        def public(value):
            if isinstance(value,dict):return {str(k):('[excluded from shared receipts]' if any(word in str(k).lower() for word in ('password','passphrase','private_key','secret','api_key','authorization','access_token')) else public(v)) for k,v in value.items()}
            if isinstance(value,(list,tuple)):return [public(v) for v in value]
            return value
        value=clean(public(result));body=public(body)
        if isinstance(value,dict) and (value.get('error') or value.get('failure')):value['status']='ERROR'
        with self.lock:
            receipt=self.record('section/'+ident,clean(body),value,elapsed)
            self.learn({'section/'+ident:value},body)
        return receipt

    def original_features(self,stages,payload=None):
        from .engines.flux_library.neural_model import NeuralModel,build_features
        if self.original_model is None:
            path=ROOT/'preserved'/'database-weights'/'flux-model-1.json'
            self.original_model=NeuralModel.from_state(json.loads(path.read_text(encoding='utf8'))).expanded() if path.exists() else NeuralModel()
            self.original_baseline=self.original_model.updates
        reports={k:clean(stages[k]) for k in ('unified','platform_alignment','karmic_welfare','virtue_text','reference') if k in stages}
        x,mask,observed=build_features(payload or {},reports,pipeline_result=stages.get('suite'))
        return x,mask

    def learn(self,stages,payload=None):
        if not self.settings['learning']:return
        x,mask=self.feature_vector(stages);model=self.get_model()
        before,after=model.train(x,mask)
        self.last_reconstruction={'before':before['loss'],'after':after['loss'],'score':after['score'],'observed':sum(mask)}
        if any(s in stages for s in ('suite','unified','platform_alignment','karmic_welfare','virtue_text','reference')):
            x,mask=self.original_features(stages,payload)
            if any(mask):self.original_model.train(x,mask)

    def feedback(self,b):
        receipt=b.get('receipt');target=b.get('target');note=b.get('note','')
        if type(receipt) is not int or type(target) not in (int,float) or not 0<=target<=1 or not isinstance(note,str) or len(note)>4000:raise ValueError('Choose a receipt and a score from 0 to 1')
        with self.lock,self.db() as db:
            row=db.execute('SELECT section,result,input FROM receipts WHERE id=?',(receipt,)).fetchone()
            if not row:raise ValueError('Receipt not found')
            if db.execute('SELECT 1 FROM examples WHERE receipt=?',(receipt,)).fetchone():raise ValueError('This receipt already has reviewed feedback')
            result=json.loads(row[1]);stages=result['stages'] if row[0]=='pipeline' else {row[0]:result}
            x,mask=self.feature_vector(stages);model=self.get_model();old=model.state()
            before,after=model.train(x,mask,target)
            try:db.execute('INSERT INTO examples VALUES(?,?,?,?)',(receipt,target,note,time.time()))
            except Exception:
                from .engines.flux_library.neural_model import NeuralModel
                self.model=NeuralModel.from_state(old);raise
            for section in stages:
                if section in self.utility:
                    row=self.utility[section];row['positive']+=target;row['negative']+=1-target;row['reviews']+=1
            if any(s in stages for s in ('suite','unified','platform_alignment','karmic_welfare','virtue_text','reference')):
                fx,fm=self.original_features(stages,json.loads(db.execute('SELECT input FROM receipts WHERE id=?',(receipt,)).fetchone()[0]));self.original_model.train(fx,fm,target)
            lesson=stages.get('causal')
            if not lesson:
                saved_trace=db.execute('SELECT trace FROM causal_receipts WHERE receipt=?',(receipt,)).fetchone()
                lesson=json.loads(saved_trace[0]) if saved_trace else None
            if lesson:self.causal.review(lesson['features'],target)
            self.checkpoint()
            self.process_observatory.review(target)
            return {'reviewed':True,'before_score':before['score'],'after_score':after['score'],'supervised_updates':model.supervised}

    def learning_view(self):
        return {'enabled':self.settings['learning'],'updates':self.model.updates if self.model else 0,
                'reviewed_updates':self.model.supervised if self.model else 0,'latest':self.last_reconstruction,
                'routing_utilities':{k:{'usefulness':v['positive']/(v['positive']+v['negative']),'reviews':v['reviews']} for k,v in self.utility.items()},
                'original_flux_learner':{'loaded':self.original_model is not None,'preserved_updates':self.original_baseline,'current_updates':self.original_model.updates if self.original_model else 0,'new_updates':self.original_model.updates-self.original_baseline if self.original_model else 0},
                'scope':'Masked engine-result reconstruction plus a preference head trained only by explicit reviewed feedback. No LLM base weights are modified.'}

    def publish_lesson(self,packet):
        if self.halt.is_set() or not self.listeners:return False
        if self.lesson_delivery is not None and not self.lesson_delivery.done():return False
        from . import section_threads
        section_threads.ensure_pool()
        listeners=list(self.listeners)
        def deliver():
            for listener in listeners:
                try:listener(packet)
                except Exception as error:self.errors.append('Lesson transmission: '+str(error))
        self.lesson_delivery=section_threads.pool.submit(deliver);return True

    def lesson_action(self,b):
        with self.lock:
            action=b.get('action','evaluate')
            if action=='configure':self.causal.configure(b.get('parameters',{}))
            elif action=='events':self.causal.set_events(b.get('events',[]))
            elif action=='activate':self.causal.configure({'activation':min(1,self.causal.parameters['activation']+.125)})
            elif action=='transmit':
                packet=self.causal.transmission();return {'queued':self.publish_lesson(packet),'packet':packet}
            else:raise ValueError('Choose configure, events or transmit')
            return self.causal.view()

    def configure(self,b):
        with self.lock:
            for key in ('learning','field','synthetic_training','profiles'):
                if key in b:
                    if type(b[key]) is not bool:raise ValueError(key+' must be true or false')
                    self.settings[key]=b[key]
            if 'pace' in b:
                if b['pace'] not in ('low','medium','high'):raise ValueError('Choose low, medium or high')
                self.settings['pace']=b['pace']
            if 'goal' in b:
                if not isinstance(b['goal'],str) or len(b['goal'])>2000:raise ValueError('Goal must be text under 2000 characters')
                self.settings['goal']=b['goal']
            self.checkpoint();return self.settings.copy()

    def loop(self):
        next_tick=next_save=time.monotonic()
        while not self.halt.is_set():
            try:item=self.queue.get(timeout=.25)
            except queue.Empty:item=None
            if item:
                ident,section,b=item;t=time.perf_counter()
                with self.lock:self.jobs[ident]['status']='running'
                try:
                    with self.lock:
                        value=self.pipeline(b) if section=='pipeline' else self.engine(section,b)
                        if section!='pipeline':self.learn({section:value},b)
                        receipt=self.record(section,b,value,(time.perf_counter()-t)*1000)
                        self.jobs[ident].update(status='complete',receipt=receipt,result=clean(value))
                    for fn in self.listeners:
                        try:fn({'type':'result','job':ident,'section':section,'receipt':receipt})
                        except Exception:pass
                except Exception as e:
                    self.process_observatory.fail(section)
                    with self.lock:self.jobs[ident].update(status='error',error=str(e));self.errors.append(section+': '+str(e))
                finally:self.queue.task_done()
            for attribute in ('_logic_cube','_focus_study','_runinplace','_four_texts','_living_circuit','_changes','_watts_study','_automatic_flow','_inference_workers','_economy','_matrix_study'):
                service=getattr(self,attribute,None)
                if service:
                    try:
                        with self.lock:service.step() if attribute in ('_living_circuit','_economy') else service.tick()
                    except Exception as error:self.errors.append(attribute+': '+str(error))
            if hasattr(self,'component_host'):
                try:self.component_host.background.pulse()
                except Exception as error:self.errors.append('Section scheduling: '+str(error))
            now=time.monotonic()
            if now>=next_tick:
                try:
                    with self.lock:
                        if self.settings['field'] and self.field.running:self.field.step()
                        if self.settings['profiles']:self.optimizer.step_once()
                        if self.settings['synthetic_training']:self.engine('classifier',{'batches':1})
                    next_tick=now+{'low':2,'medium':.5,'high':.1}[self.settings['pace']]
                except Exception as e:self.errors.append(str(e));next_tick=now+5
            if now>=next_save:
                try:self.checkpoint()
                except Exception as e:self.errors.append('Save: '+str(e))
                next_save=now+30

    def metrics(self):
        try:
            import psutil
            p=psutil.Process();return {'pid':os.getpid(),'rss_mb':round(p.memory_info().rss/1024**2,1),'threads':p.num_threads(),'child_processes':len(p.children(recursive=True)),'cpu_seconds':round(sum(p.cpu_times()[:2]),3)}
        except ImportError:return {'pid':os.getpid(),'rss_mb':None,'threads':threading.active_count(),'child_processes':None}

    def snapshot(self,visuals=True):
        research=self.research.view()
        with self.lock:
            loss,accuracy=self.net.evaluate(classifier.make_dataset(self.dataset,96,104))
            result={'settings':self.settings.copy(),'metrics':self.metrics(),'learning':self.learning_view(),'gates':self.gates.view(),
                    'delivery':dict(self.delivery),'inference_context':{'theology':self.theology_public,'design_research':dict(self.research_public)},'observatory':self.process_observatory.view(),'research':research,'active_lesson':{'active':not self.causal.halt.is_set(),'ticks':self.causal.ticks,'reviews':self.causal.reviews},'queue':self.queue.qsize(),'sections':SECTIONS,'errors':list(self.errors),'field':self.field.snapshot(),
                    'network':{'layers':self.net.layers,'weights':self.net.weights,'updates':self.net.updates,'loss':loss,'accuracy':accuracy,'dataset':self.dataset,'history':list(self.history)},
                    'profiles':self.ledger.to_dict(),'latest':{k:{'receipt':v['receipt'],'latency_ms':v['latency_ms']} for k,v in self.latest.items()}}
            if visuals:result['network']['grid']=[[self.net.predict([x/10-1,y/10-1]) for x in range(21)] for y in range(21)]
            return result

    def receipts(self,ident=None):
        with self.db() as db:
            if ident is not None:
                row=db.execute('SELECT id,section,input,result,transport,latency FROM receipts WHERE id=?',(ident,)).fetchone()
                if not row:raise ValueError('Receipt not found')
                return {'id':row[0],'section':row[1],'input':json.loads(row[2]),'result':json.loads(row[3]),'transport':json.loads(row[4]),'latency_ms':row[5],'causal':json.loads(trace[0]) if (trace:=db.execute('SELECT trace FROM causal_receipts WHERE receipt=?',(ident,)).fetchone()) else None}
            return [dict(zip(('id','stamp','section','latency_ms'),r)) for r in db.execute('SELECT id,stamp,section,latency FROM receipts ORDER BY id DESC LIMIT 100')]

    def close(self):
        self.halt.set();self.activity.close();self.research.close();self.device_hub.close();self.causal.close()
        if hasattr(self,'component_host'):self.component_host.close()
        if self.worker.is_alive():self.worker.join(10)
        self.field.close();self.optimizer.stop_engine();self.checkpoint()
