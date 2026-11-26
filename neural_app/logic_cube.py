"""Exact state encoding and stochastic hold/flip experiments on the shared learner."""
import hashlib,json,os,time
from pathlib import Path

RULES={'good':0,'evil':1,'unknown':0}
def transform(bits,labels,global_state='PASS'):
    if global_state not in ('PASS','FAIL'):raise ValueError('Choose PASS or FAIL')
    if not bits or any(b not in '01' for b in bits) or len(bits)!=len(labels):raise ValueError('Provide matching bits and classifications')
    if any(label not in RULES for label in labels):raise ValueError('Unknown classification')
    mask=''.join(str(RULES[label]) for label in labels)
    output=''.join(str(int(b)^int(m)) for b,m in zip(bits,mask))
    return {'input_bits':bits,'mask':mask,'output_bits':output,'flips':mask.count('1'),'holds':mask.count('0'),'unresolved':labels.count('unknown'),'global_state':global_state,'roundtrip':''.join(str(int(b)^int(m)) for b,m in zip(output,mask))==bits}

class LogicCube:
    def __init__(self,runtime):
        self.runtime=runtime;self.next_at=0;self.record_at=0;self.sweep_at=0;self.sweep=None;self.steps=0;self.last=None;self.receipt=None;self.enabled=True
        from .ambient_logic import AmbientLogic
        self.parallel_processors=[AmbientLogic() for _ in range(5)]
        self.bus_cursor=0;self.bus_received=0;self.bus_output=None;self.spectrum=None
        self.path=runtime.data/'logic-cube.json'
        if self.path.exists():self.enabled=json.loads(self.path.read_text()).get('enabled',True)
    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.enabled=enabled;self.path.write_text(json.dumps({'enabled':enabled}));return self.view()
    def tick(self):
        if not self.enabled or time.monotonic()<self.next_at:return
        self.step();self.next_at=time.monotonic()+10
    def step(self,global_state='PASS',record=False):
        raw=os.urandom(512);selector=os.urandom(512);bits=''.join(format(b,'08b') for b in raw)
        # Stochastic proposals are matched to explicit educational cases. A random
        # bit never determines a person's character or permission to act.
        from .gnostic_four import CHECKS,decide
        cases=[{'id':'protect','label':'Protect provision and preserve supplied content','benefit':.8,'need':1.,'confidence':.9,'cost':.1,'checks':dict.fromkeys(CHECKS,True)},
               {'id':'harm','label':'Cause needless harm','benefit':.9,'need':.5,'confidence':.9,'cost':.1,'checks':{**dict.fromkeys(CHECKS,True),'non_harm':False}},
               {'id':'false-good','label':'Claim benefit while concealing coercion','benefit':1.,'need':1.,'confidence':.9,'cost':.1,'checks':{**dict.fromkeys(CHECKS,True),'truthful':False,'consent':False}},
               {'id':'unresolved','label':'Unspecified consequences','benefit':.8,'need':1.,'confidence':.4,'cost':.1,'checks':dict.fromkeys(CHECKS,None)}]
        assessment=decide({'candidates':cases})
        classifications=['good' if row['eligible'] else 'unknown' if '0' in row['known_bits'] else 'evil' for row in assessment['actions']]
        labels=[classifications[b%4] for b in selector for _ in range(8)]
        result=transform(bits,labels,global_state)
        result['label_codes']=''.join({'good':'G','evil':'E','unknown':'?'}[s] for s in labels)
        result['case_legend']={'G':'Preserve content and protected provision','E':'Proposed needless harm or unapproved alteration','?':'Insufficient information; retain for review'}
        result['entropy_source']='Operating-system cryptographic random bytes; no fixed seed'
        result['shared_rule_assessment']=assessment
        result['forecast']={'expected_ones':len(bits)/2,'observed_ones':result['output_bits'].count('1'),'basis':'Expected count for independent uniform random input; not a forecast of individual bits'}
        result['steps']=self.steps+1;result['at']=time.time();result['input_sha256']=hashlib.sha256(raw).hexdigest()
        self.steps+=1;self.last=result
        bus=getattr(self.runtime,'ambient_cube_bus',None)
        if bus:
            batch=bus.view(self.bus_cursor);self.bus_cursor=batch['sequence']
            rows=[e for e in batch['events'] if e['origin']!='flux-cube-core']
            self.bus_received+=len(rows)
            # All retained input envelopes enter the digest; full originals stay on the bus.
            incoming=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
            digest=hashlib.sha256(incoming).digest()
            influence=''.join(format(v,'08b') for v in digest)
            deterministic=''.join(str(int(bits[i])^int(result['mask'][i])) for i in range(len(bits)))
            phases=[]
            for processor,level in zip(self.parallel_processors,(0,.15,.4,.7,1)):
                output=''.join(deterministic[i] if i/len(bits)<level else str(int(bits[i])^(int(influence[i%len(influence)]) if level else 0)) for i in range(len(bits)))
                processor.configure({'depth':level});analysis=processor.process([{'text':output[:512],'stochastic':True,'predefined_text':False,'contains_model_text':False}])
                phases.append({'logic_fraction':level,'bits':output[:1024],'ones':output[:1024].count('1'),'processor':analysis})
            self.spectrum={'phases':phases,'input_events':len(rows),'received_total':self.bus_received,'gap':batch['gap'],'input_sha256':hashlib.sha256(incoming).hexdigest(),'contract':'Pure random baseline; digest-influenced random; increasing deterministic hold/flip coverage; full declared logic. Every bus stage is eligible. No model call required.'}
            payload={'cube_spectrum':self.spectrum,'output_bits':phases[-1]['bits'],'scope':'registered app bus subscribers','hop_limit':1,'stochastic':False,'provenance':'derived-cube-logic'}
            self.bus_output=bus.publish({'target':'all','kind':'stage-output','origin':'flux-cube-core','payload':payload})['event']['sequence']

        if record or time.monotonic()>=self.record_at:
            summary={k:result[k] for k in ('steps','at','flips','holds','unresolved','roundtrip','input_sha256','forecast')}
            with self.runtime.lock:
                self.receipt=self.runtime.record('runinplace',{'operation':'stochastic-cube','global_state':global_state},summary,0)
                self.runtime.learn({'runinplace':summary},{'operation':'stochastic-cube'})
            self.record_at=time.monotonic()+60
        if time.monotonic()>=self.sweep_at:
            flow=self.runtime.automatic_flow()
            with self.runtime.db() as db:pending=db.execute("SELECT COUNT(*) FROM auto_inputs WHERE status!='complete'").fetchone()[0]
            if flow.config['enabled'] and pending<8:
                text=f"Stochastic logic cube: {result['flips']} flips; {result['holds']} holds. Preserve constructive states; invert working states assessed as harmful; retain unresolved inputs for review. Compare dignity, protection of children, animal welfare, restraint and repair through the shared app rules."
                self.sweep=flow.add(text,'Logic cube · shared ethical circuit')
            self.sweep_at=time.monotonic()+300
        return self.view()
    def view(self):
        rt=self.runtime
        with rt.lock:
            projection={'field':rt.field.snapshot(),'queue':rt.queue.qsize(),'learning_updates':rt.get_model().updates,'engine_receipts':{k:v.get('receipt') for k,v in rt.latest.items()},'delivery':dict(rt.delivery)}
        raw=json.dumps(projection,sort_keys=True,separators=(',',':')).encode()
        prayer=(Path(__file__).resolve().parents[1]/'references/user-prayer-intent.txt').read_text(encoding='utf-8')
        sources=json.loads((Path(__file__).resolve().parents[1]/'references/virtue-primary-sources.json').read_text(encoding='utf-8'))
        research=rt.research.view()
        return {'spectrum':self.spectrum,'bus_output_sequence':self.bus_output,'enabled':self.enabled,'steps':self.steps,'interval_seconds':10,'shared_receipt':self.receipt,'state_bits':''.join(format(b,'08b') for b in raw),'state_sha256':hashlib.sha256(raw).hexdigest(),'state_bytes':len(raw),'state_fields':list(projection),'prayer':prayer,'prayer_bits':''.join(format(b,'08b') for b in prayer.encode()),'stochastic':self.last,'primary_sources':sources,'research_context':{'completed_topics':research['completed_topics'],'checked_topics':list(research['topics']),'shared_assessment_engines':['virtue_text','gnostic_four','super_mesh','karmic_welfare']},'scope':'Exact selected app-state bytes and a separate stochastic educational circuit. Visual target blending does not alter computer permissions or external devices.'}
