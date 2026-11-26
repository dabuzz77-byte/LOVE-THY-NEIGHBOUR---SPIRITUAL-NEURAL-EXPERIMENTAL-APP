"""Bounded bidirectional local feedback, explicit inputs and a two-mesh model."""
import collections,json,math,time
from .gnostic_four import CHECKS,decide,scalar

class LivingCircuit:
    def __init__(self,runtime):
        self.runtime=runtime;self.path=runtime.data/'living-circuit.json'
        self.config={'enabled':False,'order':.65,'chaos':.35,'temperature':15.,'feedback':.04}
        if self.path.exists():self.config.update(json.loads(self.path.read_text(encoding='utf-8')))
        self.values=[0.]*96;self.ticks=0;self.last=0;self.next_learn=0;self.pending=None
        self.inbox=collections.deque(maxlen=64);self.outbox=collections.deque(maxlen=64)
        self.received=0;self.expired=0;self.learning_jobs=0;self.last_result=None;self.last_policy=None
        self.remote_temperature=None;self.last_source='local recurrent field';self.ripple=0.;self.known_inputs=0
        self.cpu_seconds=0.;self.last_error=None
    def configure(self,body):
        if not isinstance(body,dict):raise ValueError('Configuration must be an object')
        if set(body)-set(self.config):raise ValueError('Unsupported setting')
        new=dict(self.config)
        for key,value in body.items():
            if key=='enabled':
                if type(value) is not bool:raise ValueError('Enabled must be boolean')
            elif key=='temperature':
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not -40<=value<=120:raise ValueError('Use −40 to 120 Celsius for the water model')
            else:scalar(value,key,.1 if key=='feedback' else 1)
            new[key]=value
        self.config=new;self.path.write_text(json.dumps(new),encoding='utf-8');return self.view()
    @staticmethod
    def phase(temperature):
        if temperature<0:return 'ice'
        if temperature==0:return 'freezing/melting boundary'
        if temperature<100:return 'liquid water'
        if temperature==100:return 'boiling/condensing boundary'
        return 'water vapour'
    def receive(self,body):
        if not self.config['enabled']:raise ValueError('Enable the receiver first')
        if not isinstance(body,dict) or set(body)-{'source','value','temperature','kind'}:raise ValueError('Use source, kind, value and optional temperature')
        source=body.get('source','authenticated client')
        if not isinstance(source,str) or not 1<=len(source)<=120:raise ValueError('Use a short source label')
        value=body.get('value',0)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not -1<=value<=1:raise ValueError('Input signal must be finite and between −1 and 1')
        temperature=body.get('temperature')
        if temperature is not None and (isinstance(temperature,bool) or not isinstance(temperature,(int,float)) or not math.isfinite(temperature) or not -273.15<=temperature<=1000):raise ValueError('Temperature outside supported range')
        kind=body.get('kind','signal')
        if kind not in ('signal','water','intent'):raise ValueError('Use signal, water or intent')
        self.inbox.append({'source':source,'kind':kind,'value':float(value),'temperature':temperature,'received_at':time.time()})
        self.received+=1;return {'accepted':True,'pending':len(self.inbox),'scope':'Authenticated app input, not independently verified sensor data.'}
    def drop(self):
        self.ripple=min(1,self.ripple+.5);return self.view()
    def proposal(self):
        return decide({'budget':1,'candidates':[{'id':'care_feedback','label':'Bounded, inspectable feedback inside this local app',
            'benefit':.7,'need':.7,'confidence':.8,'cost':.1,
            'checks':dict.fromkeys(CHECKS,True)}]})
    def step(self):
        now=time.monotonic()
        if not self.config['enabled'] or now-self.last<1:return
        self.last=now;started=time.process_time();field=self.runtime.field.snapshot();raw=field.get('values',[])
        if not raw:raw=getattr(self.runtime.field,'values',[0.]*96)
        raw=[float(x) for x in raw[:96]] if isinstance(raw,(list,tuple)) else [0.]*96
        if not raw:raw=[0.]*96
        source_mean=sum(raw)/len(raw);external=0;count=0;clock=time.time()
        while self.inbox:
            packet=self.inbox.popleft()
            if clock-packet['received_at']>120:self.expired+=1;continue
            external+=packet['value'];count+=1;self.last_source=packet['source'];self.known_inputs+=1
            if packet['temperature'] is not None:self.remote_temperature={'celsius':packet['temperature'],'source':packet['source'],'received_at':packet['received_at']}
        if count:external/=count
        if self.remote_temperature and clock-self.remote_temperature['received_at']>120:self.remote_temperature=None
        old=self.values;order=self.config['order'];chaos=self.config['chaos'];self.ticks+=1
        # Deterministic disturbance is a simulation, with an actual recurrent-field input.
        self.values=[max(-1,min(1,.88*old[i]+.12*math.tanh(
            order*(old[(i-1)%96]+old[(i+1)%96])*.5+chaos*math.sin(self.ticks*.37+i*2.399)
            +.4*source_mean+.3*external+self.ripple*math.cos(i*.23)))) for i in range(96)]
        self.ripple*=.92;self.last_policy=self.proposal()
        record=self.runtime.latest.get('pipeline',{}).get('result',{})
        teaching=record.get('stages',{}).get('gnostic_four',{}).get('decision')
        teaching_gate=1 if teaching is None or teaching.get('selected') else 0
        # The fixed local feedback proposal passes explicit conditions; unsafe external proposals remain proposals only.
        influence=sum(self.values)/96*self.config['feedback'] if self.last_policy['selected'] and teaching_gate else 0
        self.runtime.field.script_signal=max(-1,min(1,.96*self.runtime.field.script_signal+influence))
        self.runtime.field.script_at=now;self.runtime.field.script_samples+=1
        self.outbox.append({'sequence':self.ticks,'at':clock,'signal':influence,'decision_bits':self.last_policy['selection_bits'],
            'teaching_gate':teaching_gate,'kind':'local feedback','destination':'shared recurrent field','external_delivery':False})
        if self.pending:
            job=self.runtime.result(self.pending)
            if job['status']=='complete':self.last_result={'receipt':job['receipt'],'at':clock};self.pending=None
            elif job['status']=='error':self.last_error=job.get('error');self.pending=None
        if now>=self.next_learn and self.pending is None and self.runtime.settings['learning'] and self.runtime.queue.qsize()<4:
            self.next_learn=now+30
            text='Living circuit: receive, choose care, process, return feedback. '+''.join('1' if x>=0 else '0' for x in self.values)
            job=self.runtime.submit('pipeline',{'text':text,'sections':['living_circuit','gnostic_four','inference'],
                'section_inputs':{'gnostic_four':{'lesson':'engine'}}})
            self.pending=job['id'];self.learning_jobs+=1
        self.cpu_seconds+=time.process_time()-started
    def measure(self,body=None):
        return {'status':'COMPLETE','ticks':self.ticks,'mean':sum(self.values)/96,
            'variance':sum((v-sum(self.values)/96)**2 for v in self.values)/96,
            'values':list(self.values),'binary':''.join('1' if v>=0 else '0' for v in self.values),
            'water':{'model_celsius':self.config['temperature'],'model_phase':self.phase(self.config['temperature']),
                'assumptions':'Pure water, approximate equilibrium at one atmosphere; temperature alone does not determine phase fraction at transition points.',
                'remote':self.remote_temperature,'remote_state':'received' if self.remote_temperature else 'awaiting configured sender'},
            'resource_cost':{'process_cpu_seconds_observed':self.cpu_seconds,'power_meter':'not connected','joules':None},
            'policy':self.last_policy,'scope':'Finite 96-node two-mesh simulation and bounded local feedback. Imagery of infinity is visual; material presence is not connectivity.'}
    def view(self):
        return {'config':dict(self.config),**self.measure(),'received':self.received,'expired':self.expired,'known_inputs':self.known_inputs,
            'pending_packets':len(self.inbox),'outbox':list(self.outbox)[-8:],'learning_jobs':self.learning_jobs,
            'last_learning':self.last_result,'last_error':self.last_error,'ripple':self.ripple,
            'receiver':'Existing authenticated local API /api/living-circuit/input; same app token and origin policy.',
            'silicon_link':'Sand/silica → purified silicon → manufactured chips → configured inputs → processing → feedback.',
            'open':self.config['enabled'],'expecting':self.config['enabled'] and not self.inbox}
