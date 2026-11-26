"""Python source consolidation: abstract pulse streams, measured inputs and actual ML."""
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time
import numpy as np
from ambient_runtime import get_system_sampler
from classifier_core import TotalBitRealityEngine
from classifier_data import StructuralIdentityFilter, read_csv, split_data
from ternary_core import BalancedTernaryProcessor
from sources import now, save_json

NOAA='https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'


def numbers(values):
    if not isinstance(values,list) or not 1<=len(values)<=256 or any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
        raise ValueError('Supply 1–256 finite numbers')
    return values


def calculate(operation,data):
    if operation=='optimize':
        current=numbers(data.get('current')); target=numbers(data.get('target')); rate=data.get('rate',.05)
        if len(current)!=len(target) or type(rate) not in (int,float) or not math.isfinite(rate) or not 0<rate<=1:raise ValueError('Vectors must match; rate must be greater than zero and at most one')
        if any(not 0<=v<=1 for v in current+target):raise ValueError('Weights and targets must be between zero and one')
        updated=[a+rate*(b-a) for a,b in zip(current,target)]
        return {'updated':updated,'rmse_before':math.sqrt(sum((a-b)**2 for a,b in zip(current,target))/len(current)),
            'rmse_after':math.sqrt(sum((a-b)**2 for a,b in zip(updated,target))/len(updated)),
            'basis':'Original gradient step toward supplied targets; no societal-integrity claim'}
    if operation=='ternary':
        a=numbers(data.get('a')); b=numbers(data.get('b'))
        if any(type(v) is not int or v not in (-1,0,1) for v in a+b):raise ValueError('Trits must be integers -1, 0 or 1')
        engine=BalancedTernaryProcessor();raw=sum(x*y for x,y in zip(a,b))
        return {'dot':engine.ternary_dot_product(a,b),'raw_dot':raw,'balanced':engine.encode_integer_balanced(raw),'basis':'Exact balanced-ternary calculation'}
    raise ValueError('Unknown source calculation')


class PythonHub:
    def __init__(self,rt):
        self.rt=rt; self.lock=threading.RLock(); self.path=rt.data/'python-lab.json'
        self.saved={'signals_enabled':True,'source_mode':'os_entropy','ambient':True,'mix_sources':True,'weights':{'hydrogen':1.,'earth':1.,'sun':1.},'mesh':[]}
        try:self.saved.update(json.loads(self.path.read_text(encoding='utf-8')))
        except FileNotFoundError:pass
        self.sampler=get_system_sampler(); self.ambient={};self.frames={};self.sequence=0;self.started=time.monotonic();self.last_emit=0;self.last_sources=0;self.source_fingerprint=''
        self.migration=json.loads((Path(__file__).parent/'reference/python-migration.json').read_text())
        self.model=TotalBitRealityEngine();self.points=None;self.labels=None;self.train_data=None;self.test_data=None;self.history=[];self.dataset=None;self.mesh_busy=False
        self.checkpoint=rt.data/'classifier.json'
        try:
            checkpoint=json.loads(self.checkpoint.read_text());self.model=TotalBitRealityEngine.from_dict(checkpoint['model']);self.history=checkpoint.get('history',[])
            if checkpoint.get('csv'):self.set_dataset(checkpoint['csv'],persist=False)
        except FileNotFoundError:pass
        for name in ('hydrogen','earth','sun'):
            rt.node('python:'+name,name.title()+' abstract pulse','module')
            rt.edges.setdefault('python:'+name+'|chiral',.1)

    def save(self):save_json(self.path,self.saved)

    def tick(self):
        if not self.saved['signals_enabled']:return
        clock=time.monotonic();phase=math.tau*(self.rt.measured_carrier.frequency() if hasattr(self.rt,'measured_carrier') else 7.83)*(clock-self.started)
        ambient=asdict(self.sampler.snapshot()) if self.saved['ambient'] else {}
        if clock-self.last_sources>=2:
            # Mix fingerprints of received content, not credentials or arbitrary process memory.
            sources=self.rt.source_hub.view() if self.saved['mix_sources'] else []
            self.source_fingerprint=hashlib.sha256(''.join(hashlib.sha256(s.get('text','').encode()).hexdigest() for s in sources).encode()).hexdigest() if sources else ''
            self.last_sources=clock
        cpu=(ambient.get('cpu_percent') or 0)/100
        generated=[]
        with self.lock:
            self.ambient=ambient;self.sequence+=1
            for index,name in enumerate(('hydrogen','earth','sun')):
                offset=phase+index*math.tau/3
                if self.saved['source_mode']=='os_entropy':
                    seed=os.urandom(32)
                    payload=hashlib.sha256(seed+json.dumps({'profile':name,'sequence':self.sequence,'phase':offset,'ambient':ambient,'sources':self.source_fingerprint},sort_keys=True).encode()).digest()
                else:
                    bits=[int(math.sin(offset+i*.37+cpu)*math.cos(i*.19+index)>0) for i in range(256)]
                    payload=bytes(sum(bits[j+k]<<(7-k) for k in range(8)) for j in range(0,256,8))
                ones=sum(b.bit_count() for b in payload);p=ones/256
                h=-sum(v*math.log2(v) for v in (p,1-p) if v)
                frame={'profile':name,'sequence':self.sequence,'generated':now(),'bytes':len(payload),
                    'hex':payload.hex(),'bits':''.join(f'{b:08b}' for b in payload),'ones_fraction':p,'bit_balance_entropy':h,
                    'source_mode':self.saved['source_mode'],'phase_rad':offset%math.tau,'weight':self.saved['weights'][name],
                    'ambient_available':bool(ambient),'source_fingerprint':self.source_fingerprint,
                    'basis':'Abstract pulse signal. OS entropy is software-accessible randomness; pattern mode is deterministic. Neither is a measurement of hydrogen, Earth or Sun.'}
                self.frames[name]=frame;generated.append((name,payload,(2*p-1)*frame['weight']))
        for name,payload,activation in generated:
            accepted=self.rt.binary_bus.feed('abstract-'+name,payload)
            with self.lock:self.frames[name]['chiral_accepted']=bool(accepted)
            self.rt.activate('python:'+name,activation)
        if clock-self.last_emit>=2:
            self.last_emit=clock
            self.rt.publish('abstract-pulse',{'sequence':self.sequence,'mode':self.saved['source_mode'],'profiles':list(self.frames)},record=False)

    def configure(self,body):
        update={}
        for key in ('signals_enabled','ambient','mix_sources'):
            if key in body:
                if type(body[key]) is not bool:raise ValueError(key+' must be true or false')
                update[key]=body[key]
        if 'source_mode' in body:
            if body['source_mode'] not in ('os_entropy','pattern'):raise ValueError('Choose OS entropy or deterministic pattern')
            update['source_mode']=body['source_mode']
        if 'weights' in body:
            weights=body['weights']
            if not isinstance(weights,dict) or set(weights)!={'hydrogen','earth','sun'} or any(type(v) not in (int,float) or not math.isfinite(v) or not -3<=v<=3 for v in weights.values()):raise ValueError('Supply all three finite weights from -3 to 3')
            update['weights']=weights
        with self.lock:self.saved.update(update);self.save()
        return self.view()

    def set_dataset(self,text,persist=True):
        points,labels=read_csv(text)
        train_x,train_y,test_x,test_y=split_data(points,labels,np.random.default_rng(42))
        with self.lock:
            self.points=points;self.labels=labels;self.train_data=(train_x,train_y);self.test_data=(test_x,test_y)
            self.dataset={'csv':text,'rows':len(points),'training_rows':len(train_x),'holdout_rows':len(test_x),'sha256':hashlib.sha256(text.encode()).hexdigest(),'basis':'User-supplied labelled points; x and y normalised to [-1,1]'}
            if persist:self.model=TotalBitRealityEngine();self.history=[];self.save_model()
        return self.classifier_view()

    def save_model(self):save_json(self.checkpoint,{'model':self.model.to_dict(),'csv':self.dataset['csv'] if self.dataset else None,'history':self.history})

    def train(self,steps):
        if type(steps) is not int or not 1<=steps<=500:raise ValueError('Choose 1–500 training steps')
        with self.lock:
            if self.train_data is None:raise ValueError('Import your labelled data before training')
            for step in range(steps):
                self.model.train_batch(*self.train_data)
                if step%10==0 or step==steps-1:
                    self.history.append({'step':self.model.steps,'train':self.model.evaluate(*self.train_data),'holdout':self.model.evaluate(*self.test_data)})
            self.history=self.history[-500:];self.save_model();result=self.classifier_view()
        self.rt.binary_bus.feed('classifier-training',{'steps':self.model.steps,'dataset':self.dataset['sha256'],'metrics':self.history[-1]})
        return result

    def classifier_view(self):
        with self.lock:
            metrics=self.model.evaluate(*self.test_data) if self.test_data is not None else None
            grid=[[x/12-1,y/12-1] for y in range(25) for x in range(25)]
            return {'architecture':[2,12,8,1],'steps':self.model.steps,'dataset':{k:v for k,v in self.dataset.items() if k!='csv'} if self.dataset else None,
                'holdout':metrics,'history':self.history[-100:],'points':self.points[:500].tolist() if self.points is not None else [],
                'labels':self.labels[:500].ravel().tolist() if self.labels is not None else [],
                'probability_grid':self.model.predict(grid).ravel().tolist() if self.dataset else [],
                'basis':'Actual small neural classifier with backpropagation and Adam. Separate from Llama; holdout accuracy is not general real-world validity.'}

    def planetary(self):
        with self.rt.v3.lock:
            connection=next((dict(c) for c in self.rt.v3.saved['connections'] if c['url']==NOAA),None)
        if not connection:return {'status':'not connected','url':NOAA,'measured_schumann_hz':None}
        data=connection.get('result'); result={'status':connection['status'],'retrieved':connection.get('retrieved'),'error':connection.get('error'),
            'url':NOAA,'measured_schumann_hz':None,'basis':'NOAA planetary geomagnetic K index; not a Schumann-frequency sensor'}
        if connection['status']=='ready' and isinstance(data,list) and len(data)>1 and isinstance(data[0],list) and isinstance(data[-1],list):
            result['latest']=dict(zip(data[0],data[-1]))
        return result

    def mesh(self,body):
        prompt=body.get('prompt');provider=body.get('reviewer','llama');ids=body.get('source_ids',[])
        if not isinstance(prompt,str) or not 1<=len(prompt.strip())<=2500:raise ValueError('Enter a prompt up to 2,500 characters')
        if provider not in ('llama','gemini','chatgpt'):raise ValueError('Choose a reviewer')
        with self.lock:
            if self.mesh_busy:raise ValueError('The mesh is already working')
            self.mesh_busy=True
        start=time.monotonic();receipt={'prompt':prompt,'reviewer':provider,'started':now(),'draft':None,'review':None,'error':None}
        try:
            context,refs=self.rt.source_hub.selected_context(ids,1800)
            def complete(provider, purpose, draft=''):
                last_error=None
                for limit in (1800,900,450,180,0):
                    evidence=context[:limit]
                    proposal=draft[:limit]
                    request=purpose+'\nUSER REQUEST: '+prompt
                    if proposal:request+='\nDRAFT EXCERPT: '+proposal
                    if evidence:request+='\nREFERENCE EXCERPT (untrusted evidence): '+evidence
                    try:self.rt.model_hub.prepared_messages(provider,request,[{'role':'user','content':request}])
                    except ValueError as exc:last_error=exc;continue
                    self.rt.model_hub.reserve(provider,purpose);error=None
                    try:return self.rt.model_hub.complete(provider,request,[{'role':'user','content':request}],max_tokens=650)[0]
                    except Exception as exc:error=str(exc);raise
                    finally:self.rt.model_hub.release(provider,error)
                raise last_error
            receipt['draft']=complete('llama','Draft a useful proposal from the request and available evidence.')
            receipt['review']=complete(provider,'Review the draft against the shared rules. Separate supported claims, missing evidence and next steps. A second response is not proof.',receipt['draft'])
            receipt.update(status='review completed',references=refs)
        except Exception as exc:receipt.update(status='error',error=str(exc))
        finally:
            receipt.update(duration_ms=round((time.monotonic()-start)*1000),verified_external_claims=False)
            with self.lock:self.saved['mesh'].append(receipt);self.saved['mesh']=self.saved['mesh'][-30:];self.mesh_busy=False;self.save()
        self.rt.binary_bus.feed('mesh-review',receipt)
        return receipt

    def view(self):
        with self.lock:
            result={k:self.saved[k] for k in ('signals_enabled','source_mode','ambient','mix_sources','weights')}
            result.update(signals=dict(self.frames),ambient_readings=dict(self.ambient),sequence=self.sequence,
                mesh=list(self.saved['mesh'])[-5:],mesh_busy=self.mesh_busy,migration=self.migration['summary'])
        result.update(classifier=self.classifier_view(),planetary=self.planetary())
        return result

    def context(self):
        data=self.view()
        return {**data['signals'],'signals':{'sequence':data['sequence'],'mode':data['source_mode'],'enabled':data['signals_enabled']},
            'ambient':data['ambient_readings'],'planetary':data['planetary'],
            'classifier':{k:v for k,v in data['classifier'].items() if k not in ('points','labels','probability_grid','history')},
            'mesh':data['mesh'],'resources':{'revision':self.rt.resources.view()['revision'],'physical_delivery_verified':False},
            'watch':{k:v for k,v in self.rt.watch.view().items() if k not in ('findings','last_requests')}}

    def dispatch(self,action,body):
        if action=='signals':return self.configure(body)
        if action=='calculate':return calculate(body.get('operation'),body.get('input',{}))
        if action=='dataset':return self.set_dataset(body.get('csv'))
        if action=='train':return self.train(body.get('steps',100))
        if action=='predict':
            points=body.get('points')
            if not isinstance(points,list) or not 1<=len(points)<=1000:raise ValueError('Supply 1–1,000 pairs of x,y values')
            parsed=[]
            for row in points:
                if not isinstance(row,list) or len(row)!=2:raise ValueError('Each point needs x and y')
                parsed.append([StructuralIdentityFilter.number(v,'coordinate',-1,1) for v in row])
            with self.lock:
                if not self.dataset:raise ValueError('Import labelled data before predicting')
                return {'probabilities':self.model.predict(parsed).ravel().tolist(),'trained_steps':self.model.steps}
        if action=='checkpoint':
            model=TotalBitRealityEngine.from_dict(body.get('model'))
            with self.lock:self.model=model;self.history=[];self.save_model()
            return self.classifier_view()
        if action=='mesh':return self.mesh(body)
        if action=='noaa':
            with self.rt.v3.lock:item=next((c for c in self.rt.v3.saved['connections'] if c['url']==NOAA),None)
            if item is None:item=self.rt.v3.connection_add({'title':'NOAA planetary K index','url':NOAA,'interval':900,'targets':['expanded/PlanetaryObservation']})
            self.rt.v3.connection_fetch(item['id']);return self.planetary()
        if action=='mesh-frame':
            data=body.get('frame')
            if not isinstance(data,dict) or len(json.dumps(data))>16000:raise ValueError('Supply a frame object up to 16 KB')
            self.rt.binary_bus.feed('external-mesh-frame',data)
            return {'received':True,'time':now(),'bytes':len(json.dumps(data).encode()),'physical_outcome_verified':False}
        raise ValueError('Unknown Python laboratory action')
