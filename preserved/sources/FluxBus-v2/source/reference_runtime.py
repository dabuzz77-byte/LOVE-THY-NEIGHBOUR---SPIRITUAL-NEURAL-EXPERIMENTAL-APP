"""Durable reference engines. Text is data, never dynamically executed code."""
from copy import deepcopy
import inspect
import json
import math
import secrets
import time
import reference_calculators as calc
import reference_crypto as crypto
import reference_custom as custom
from reference_catalog import ENGINE_NAMES, source_entry
from continuous_module import ContinuousInputModule
from routing import balanced_ternary


class AlignmentEngine:
    def evaluate(self,intent_index,delivers_human_utility):return {'aligned':calc.evaluate_systemic_alignment(intent_index,delivers_human_utility),'supplied_intent_index':intent_index}


CLASSES={name:getattr(calc,name) for name in ENGINE_NAMES if hasattr(calc,name) and isinstance(getattr(calc,name),type)}
CLASSES.update({name:getattr(custom,name) for name in ENGINE_NAMES if hasattr(custom,name)})
CLASSES.update({name:getattr(crypto,name) for name in ENGINE_NAMES if hasattr(crypto,name) and isinstance(getattr(crypto,name),type)})
CLASSES.update(derive_skeleton_key=crypto.KeyDerivationEngine,evaluate_systemic_alignment=AlignmentEngine)
# Explicit public API only; no document-supplied imports, expressions or host commands.
METHODS={name:{n for n,method in inspect.getmembers(cls,inspect.isfunction) if not n.startswith('_') and n!='snapshot'} for name,cls in CLASSES.items()}
METHODS['FractalFluxDispatcher'].discard('register_store_pipeline')


def clean(value):
    if value is None or isinstance(value,(str,bool,int)):return value
    if isinstance(value,float):return value if math.isfinite(value) else str(value)
    if isinstance(value,bytes):return value.hex()
    if isinstance(value,(list,tuple,set)):return [clean(v) for v in value]
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items() if not str(k).startswith('_') and not any(s in str(k).lower() for s in ('secret','private_key','revoked_tokens'))}
    return type(value).__name__


def validate_numbers(value,key=''):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('Numbers must be finite')
    if isinstance(value,(int,float)) and not isinstance(value,bool) and value<0 and key not in ('shift','observed_sensor_coords'):
        raise ValueError(key+' must be nonnegative')
    if isinstance(value,dict):
        for k,v in value.items():validate_numbers(v,k)
    elif isinstance(value,(list,tuple)):
        for v in value:validate_numbers(v,key)


def execute_one(name,config,stop_event=None):
    if name not in CLASSES:raise ValueError('Unknown reference engine: '+name)
    if not isinstance(config,dict):raise ValueError('Engine configuration must be an object')
    cls=CLASSES[name];init=deepcopy(config.get('init',{}));validate_numbers(init)
    for parameter in inspect.signature(cls).parameters.values():
        if parameter.name not in init and ('secret' in parameter.name or parameter.name.endswith('_key')):
            init[parameter.name]=secrets.token_bytes(32)
    engine=cls(**init);raw=[];receipts=[];started=time.perf_counter()
    for action in config.get('calls',[]):
        if stop_event and stop_event.is_set():raise InterruptedError()
        method=action['method']
        if method not in METHODS[name]:raise ValueError('Unknown engine operation: '+method)
        def resolve(item):
            if isinstance(item,dict) and set(item)=={'$result'}:
                index=item['$result']
                if type(index) is not int or index<0 or index>=len(raw):raise ValueError('Result reference is out of range')
                return deepcopy(raw[index])
            if isinstance(item,list):return [resolve(x) for x in item]
            if isinstance(item,dict):return {k:resolve(v) for k,v in item.items()}
            return item
        args=resolve(action.get('args',[]));kwargs=resolve(action.get('kwargs',{}))
        function=getattr(engine,method);bound=inspect.signature(function).bind(*args,**kwargs)
        for key,value in bound.arguments.items():validate_numbers(value,key)
        # Self-transfers made the original dividend logic inconsistent.
        a=bound.arguments
        for left,right in (('sender','receiver'),('sender_id','receiver_id'),('source_shard','target_shard')):
            if left in a and a[left]==a.get(right):raise ValueError('Transfer endpoints must be different')
        output=function(*args,**kwargs);raw.append(output)
        exposed=clean(output)
        if method.startswith(('issue_','generate_signed')):exposed={'issued':bool(output),'signature_recorded':bool(output)}
        receipts.append({'operation':method,'output':exposed})
    state=clean(engine.snapshot() if hasattr(engine,'snapshot') else vars(engine))
    entry=source_entry(name)
    return {'status':'COMPLETE','engine':name,'actions':receipts,'state':state,
            'milliseconds':round((time.perf_counter()-started)*1000,3),'source_line':entry['line'] if entry else None,
            'basis':'Executed local algorithms on supplied values. Named remote systems, hardware and global activation declarations are reference labels.'}


def execute_reference(payload,stop_event=None):
    started=time.perf_counter()
    if isinstance(payload,str):
        try:payload=json.loads(payload)
        except ValueError:payload={'text':payload}
    texts=[]
    def content(value):
        if isinstance(value,str):texts.append(value)
        elif isinstance(value,list):
            for item in value:content(item)
        elif isinstance(value,dict):
            for key in ('text','prompt','summary','raw_input','raw_output','article','title'):
                if key in value:content(value[key])
    content(payload);text='\n'.join(texts)
    configs=payload.get('reference_engines',{}) if isinstance(payload,dict) else {}
    if not isinstance(configs,dict):raise ValueError('reference_engines must map engine names to configurations')
    results={};stages=[]
    if text and 'ReferenceGoalsEngine' not in configs:
        results['ReferenceGoalsEngine']=custom.ReferenceGoalsEngine().assess(str(text))
        stages.append({'engine':'ReferenceGoalsEngine','status':'COMPLETE'})
    for name,config in configs.items():
        if stop_event and stop_event.is_set():raise InterruptedError()
        try:results[name]=execute_one(name,config,stop_event)
        except InterruptedError:raise
        except Exception as error:results[name]={'status':'ERROR','error':str(error),'engine':name}
        stages.append({'engine':name,'status':results[name]['status']})
    bits=[int(r['status']=='COMPLETE') for r in results.values()]
    return {'status':('PARTIAL' if 0 in bits else 'COMPLETE') if bits else 'AWAITING_INPUT',
            'engines':results,'stages':stages,'binary':bits,'balanced_ternary':balanced_ternary(int(''.join(map(str,bits)) or '0',2)),
            'milliseconds':round((time.perf_counter()-started)*1000,3)}


class ContinuousReferenceModule(ContinuousInputModule):
    prefix='reference';engine_names=ENGINE_NAMES;worker_name='Reference studio'
    execute=staticmethod(execute_reference)

    @staticmethod
    def summary(result):
        return {**{k:result.get(k) for k in ('job_id','status','source','binary','balanced_ternary','milliseconds','error')},
                'engines':{name:{'status':r['status'],'milliseconds':r.get('milliseconds'),'source_line':r.get('source_line'),
                    'actions':len(r.get('actions',[])),'error':r.get('error')} for name,r in result.get('engines',{}).items()}}
