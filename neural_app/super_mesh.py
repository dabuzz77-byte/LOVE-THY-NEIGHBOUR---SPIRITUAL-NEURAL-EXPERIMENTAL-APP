"""A shared, inspectable routing policy; humanitarian priority is not access authority."""
import os
from .gnostic_four import CHECKS,decide
from .inference_beacon import resolve as route
def resolve(runtime,body):
    text=body.get('text') or 'Choose care and practical provision through an authorised route.'
    workers=runtime.inference_workers()
    def healthy(name):
        state=workers.states[name]
        return state['received']>0 and bool(state.get('last')) and not state['last'].get('error')
    available={'local':True,'gemma':workers.config['gemma']['enabled'] and healthy('gemma')}
    for name in ('gemini','palantir'):
        c=workers.config[name];available[name]=bool(c['enabled'] and workers.credential(name) and healthy(name))
    target=body.get('target','local')
    if target not in available:raise ValueError('Choose local, gemma, gemini or palantir')
    selected=target if available[target] else 'local'
    topology={'nodes':[{'id':name,'capabilities':['inference'],'enabled':enabled} for name,enabled in available.items()],
              'bridges':[{'from':'local','to':name,'cost':1,'allowed':enabled} for name,enabled in available.items() if name!='local']}
    decision=decide({'candidates':[{'id':'care_route','label':'A bounded, inspectable route with meaningful participation and a local fallback','benefit':.8,'need':1.,'confidence':.8,'cost':.2,'checks':dict.fromkeys(CHECKS,True)}]})
    return {'status':'COMPLETE','model':'Shared care-oriented super-mesh route policy','policy':decision,
        'route':route({'text':text,'target':selected,'topology':topology}),
        'requested_target':target,'selected_target':selected,'conflict_resolution':'Requested route available' if selected==target else 'External access is not established; continue local processing and retain the access request.',
        'principles':{'daily_bread':'Practical provision and useful knowledge','souls_over_digits':'Dignity and urgent need before prestige or revenue','robin_hood_orientation':'Correct exclusion through accessible design, voluntary support and fair allocation of resources actually available to the project','tesla_fuller_fresco':'Resource accounting, efficient shared infrastructure, repair, reduced waste and accessible design; an authored synthesis, not a claim that their ideas are identical','priority':'Most vulnerable and least connected upwards, including children in remote African communities; use explicit needs and access constraints, not inferred ethnicity, religion, location or account authority','delivery_design':['Offline-first reading packs','Small resumable messages','Low-bandwidth interfaces','Community-controlled participation','No collection of a child’s identity or precise location for ranking']},
        'scope':'Routing and planning inside the configured app. Neither spiritual intent nor a priority score creates an external credential, transfers ownership, reallocates third-party funds, or proves aid delivery.'}
