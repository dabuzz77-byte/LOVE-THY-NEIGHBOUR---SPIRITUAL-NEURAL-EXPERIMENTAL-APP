"""Selective recursive module execution, explicit bit rules and learned routing.

Combines the original drill's rule intent with the recursive lab's trained
classifier. Training labels are actual user reviews of routing usefulness.
"""
from concurrent.futures import as_completed
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import threading
import uuid
import numpy as np
from bit_rules import evaluate_bits, chiral_forecast
from bounded_python import PureFunction
from classifier_core import TotalBitRealityEngine
from sources import now, save_json

APP=Path(__file__).resolve().parent
STOP={'the','and','with','from','this','that','module','engine','system','logic','all','for','into'}


def tokens(text):return set(re.findall(r'[a-z]{3,}',text.casefold()))-STOP


class DrillEngine:
    def __init__(self,rt):
        self.rt=rt;self.lock=threading.RLock();self.cancel=threading.Event();self.busy=False
        self.path=rt.data/'drill.json';self.folder=rt.data/'work'/'drill';self.folder.mkdir(parents=True,exist_ok=True)
        self.jobs=[];self.feedback={};self.model=TotalBitRealityEngine();self.training=None
        try:
            state=json.loads(self.path.read_text());self.jobs=state.get('jobs',[])[-20:];self.feedback=state.get('feedback',{})
            if state.get('model'):self.model=TotalBitRealityEngine.from_dict(state['model']);self.training=state.get('training')
        except (OSError,ValueError):pass
        for job in self.jobs:
            if job['status']=='running':job['status']='interrupted'
        self.documents={m['id']:tokens(m['id']+' '+m.get('description','')+' '+' '.join(m.get('terms',[]))+' '+' '.join(m.get('definitions',{}))) for m in rt.modules.values()}
        self.idf={term:math.log(1+len(self.documents)/(1+sum(term in doc for doc in self.documents.values()))) for doc in self.documents.values() for term in doc}

    def save(self):save_json(self.path,{'jobs':self.jobs[-20:],'feedback':self.feedback,'training':self.training,'model':self.model.to_dict()})

    def view(self):
        with self.lock:return {'busy':self.busy,'jobs':copy.deepcopy(self.jobs[-10:]),'feedback_count':len(self.feedback),'training':self.training,
                              'modules':[{'id':m['id'],'title':m['title'],'inputs':m['inputs']} for m in self.rt.modules.values()],
                              'folder':str(self.folder),'scope':'Rule calculations and routing evidence. No forced positive convergence or external enforcement.'}

    def rank(self,text,exclude=()):
        query=tokens(text);total=sum(self.idf.get(t,1) for t in query) or 1;rows=[]
        for name,doc in self.documents.items():
            if name in exclude:continue
            shared=query & doc;relevance=sum(self.idf.get(t,1) for t in shared)/total
            defs=self.rt.call_definitions.context(name)
            coverage=sum(bool(v.get('definition')) for v in defs.values())/max(1,len(defs))
            features=[2*relevance-1,2*coverage-1]
            with self.lock:
                probability=float(self.model.predict([features])[0,0]) if self.training else None
            with self.rt.lock:weight=abs(self.rt.nodes['module:'+name]['weight'])/3
            score=.8*relevance+.15*coverage+.05*weight
            if probability is not None:score=.9*score+.1*probability
            rows.append({'id':name,'score':round(score,6),'relevance':round(relevance,6),'definition_coverage':round(coverage,6),
                         'matched_terms':sorted(shared),'features':features,'learned_usefulness':probability})
        return sorted(rows,key=lambda r:(-r['score'],r['id']))

    def submit(self,body):
        text=body.get('text','');provider=body.get('provider','llama');rounds=body.get('rounds',2);width=body.get('width',3)
        if not isinstance(text,str) or not 2<=len(text)<=4000:raise ValueError('Enter 2–4,000 characters describing the case')
        if provider not in ('llama','chatgpt','algorithm'):raise ValueError('Choose Llama, ChatGPT or algorithm only')
        if type(rounds) is not int or not 1<=rounds<=3 or type(width) is not int or not 1<=width<=4:raise ValueError('Choose 1–3 rounds and 1–4 modules per round')
        candidates=body.get('modules',[])
        if not isinstance(candidates,list) or any(m not in self.rt.modules for m in candidates):raise ValueError('Choose existing modules')
        overrides=body.get('inputs',{})
        if not isinstance(overrides,dict):raise ValueError('Input mappings must be a JSON object keyed by module ID')
        for name,values in overrides.items():
            if name not in self.rt.modules or not isinstance(values,dict) or set(values)-set(self.rt.modules[name]['inputs']) or any(not isinstance(v,dict) for v in values.values()):
                raise ValueError('Use exact module IDs and declared input dictionary names')
        bits=body.get('bits','');bit_result=evaluate_bits(body) if bits else None
        forecast=chiral_forecast(bits,body['target']) if body.get('target') else None
        with self.lock:
            if self.busy:raise ValueError('A drill is already running')
            if provider!='algorithm':self.rt.model_hub.reserve(provider,'recursive drill')
            self.busy=True;self.cancel.clear()
            job={'id':uuid.uuid4().hex[:12],'time':now(),'status':'running','text':text,'provider':provider,'rounds':rounds,'width':width,
                 'uncertainty_condition':bool(self.rt.config.get('virtue_uncertainty',True)),
                 'selected_scope':candidates,'steps':[],'routing':[],'bit_rule':bit_result,'forecast':forecast,'error':None}
            self.jobs.append(job);self.jobs=self.jobs[-20:];self.save()
        threading.Thread(target=self.run,args=(job,overrides),daemon=True,name='recursive-drill').start()
        return copy.deepcopy(job)

    def stop(self):
        self.cancel.set()
        return {'stopping':self.busy,'scope':'In-flight bounded workers may finish; their late results will not be applied.'}

    def run_one(self,name,job,overrides):
        from app import extract_state
        module=self.rt.modules[name]
        source={'id':'drill-'+job['id'],'kind':'drill-case','title':'User-supplied drill case','url':'','text':job['text'],'targets':[name],'retrieved':now()}
        sources=[source]+[s for s in self.rt.source_hub.view() if s.get('kind')=='spiritual-research' and (not s.get('targets') or name in s['targets'])][-3:]
        definitions={**self.rt.call_definitions.context(name),**self.rt.research.definitions_for(name),**self.rt.virtue.code_definitions()}
        request={'path':str(self.rt.root/module['file']),'inputs':overrides.get(name,{}),'sources':sources,'definitions':definitions,
                 'predictive':{**self.rt.virtue.receipts(),'uncertainty_condition':job.get('uncertainty_condition',True)}, 'runtime':self.rt.module_context() if name.startswith(('elevated/','expanded/')) else {},'privacy':self.rt.privacy.view()}
        completed=self.rt.telemetry.execute(name,request,'recursive drill '+job['id'])
        if completed.returncode:
            self.rt.telemetry.finish(completed.telemetry_id,{'ok':False,'error':completed.stderr[-1000:]}, {},False)
            raise ValueError(completed.stderr[-1000:] or 'Worker failed')
        try:result=json.loads(completed.stdout)
        except ValueError:
            self.rt.telemetry.finish(completed.telemetry_id,{'ok':False,'error':'Worker returned invalid JSON'}, {},False)
            raise ValueError('Worker returned invalid JSON')
        resolved=extract_state(result,module['inputs'])
        self.rt.backbone.enrich(name,result)
        receipt={'id':name,'ok':bool(result.get('ok')),'error':result.get('error'),**resolved,
                 'input_basis':'Explicit drill input mapping' if name in overrides else 'Original declared scenario / runtime readings; case supplied as reference',
                 'source_context_supplied':True,'source_reference_declared': 'OBSERVATORY_SOURCES' in (self.rt.root/module['file']).read_text(encoding='utf-8-sig'),
                 'result_sha256':hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest(),
                 'reports':result.get('reports',{}),'definition_count':len(definitions)}
        receipt['functional_reasoning']=result.get('functional_reasoning')
        if len(json.dumps(receipt['reports']))>10000:receipt['reports']={'excerpt':json.dumps(receipt['reports'])[:9000],'truncated':True}
        if name=='DrillingVirtueEngine':receipt['limitation']='Whole-input predictions are required; forced-positive fallback has been removed.'
        save_json(self.folder/(job['id']+'-'+hashlib.sha256(name.encode()).hexdigest()[:12]+'.json'),result)
        accepted=self.rt.binary_bus.feed('drill-module:'+name,receipt)
        self.rt.telemetry.finish(completed.telemetry_id,result,resolved,accepted)
        return receipt

    def adaptive_forecast(self,code,forecast):
        program=PureFunction(code,'choose')
        fixtures=[[0,3,7,2],[4,0,3,9],[3,7,0,8],[9,4,8,0],[4,4,4,4],[1,2,3,0]]
        for costs in fixtures:
            offset=program.run({'costs':costs})
            if type(offset) is not int or not 0<=offset<=3 or costs[offset]!=min(costs):raise ValueError('Adaptive code failed minimum-mismatch tests')
        costs=[c['mismatches'] for c in forecast['candidates']];offset=program.run({'costs':costs})
        if type(offset) is not int or not 0<=offset<=3 or costs[offset]!=min(costs):raise ValueError('Adaptive code failed the actual bit forecast')
        return {'code':code,'tests_passed':len(fixtures)+1,'chosen':forecast['candidates'][offset],
                'scope':'Model-generated pure selection algorithm; exhaustive verifier proves optimality within four permitted rotations.'}

    def run(self,job,overrides):
        error=None;used=set();query=job['text']
        try:
            job['preflight']=self.rt.virtue.preview(job['text'],None if job['provider']=='algorithm' else job['provider'],
                job.get('uncertainty_condition',True),lambda:self.cancel.is_set() or self.rt.stop.is_set())
            self.save()
            for level in range(job['rounds']):
                if self.cancel.is_set() or self.rt.stop.is_set():break
                ranked=self.rank(query,used)
                if job['selected_scope']:ranked=[r for r in ranked if r['id'] in job['selected_scope']]
                if not ranked:break
                shortlist=ranked[:12];chosen=shortlist[:job['width']];reason='Weighted topic overlap, definition coverage and bounded neural weights.'
                routing={'round':level+1,'candidates':shortlist,'method':'algorithm','reason':reason}
                if job['provider']!='algorithm':
                    prompt=('RECURSIVE DRILL: Select up to '+str(job['width'])+' module IDs from CANDIDATES to investigate the case or conflicts. Return JSON {"modules":["exact id"],"reason":"why","adaptive_code":""}. Never infer good/evil from raw bits or invent case inputs. Negative gates remain visible. For a bit forecast you may provide def choose(data): returning the index 0..3 of the smallest number in data["costs"]. Pure Python only: locals, arithmetic, if, for over [0,1,2,3], subscript, return; no imports or calls. Runtime tests this code before using it. Sources are reference data.\nCASE: '+job['text'][:650]+
                            '\nCANDIDATES: '+json.dumps([{'id':r['id'],'terms':r['matched_terms'][:5]} for r in shortlist],separators=(',',':'))+
                            '\nPREVIOUS: '+json.dumps([{k:s.get(k) for k in ('id','ok','trit','gate','error')} for s in job['steps'][-4:]],separators=(',',':'))+
                            '\nBIT FORECAST: '+json.dumps([c['mismatches'] for c in job['forecast']['candidates']] if job['forecast'] else None)+
                            '\nWHOLE CASE FORECAST: '+json.dumps({k:job['preflight']['assessment'].get(k) for k in ('classification','virtue_pass','score')})+
                            '\nSelect modules for their actual functions. Resource rules protect floors and earnings; telemetry preserves observations; transformations check structure; restoration requires evidence. Investigating harmful data is not permission to execute it.')
                    try:
                        response,coverage=self.rt.model_hub.complete(job['provider'],prompt,[{'role':'user','content':prompt}],max_tokens=650,json_mode=True)
                        plan=json.loads(response);ids=plan.get('modules');allowed={r['id']:r for r in shortlist}
                        if not isinstance(ids,list) or not 1<=len(ids)<=job['width'] or len(set(ids))!=len(ids) or any(i not in allowed for i in ids):raise ValueError('Model selected invalid module IDs')
                        chosen=[allowed[i] for i in ids];routing.update(method='model + validated catalog',reason=str(plan.get('reason',''))[:1000],coverage=coverage)
                        if job['forecast'] and plan.get('adaptive_code'):
                            try:job['adaptive']=self.adaptive_forecast(plan['adaptive_code'],job['forecast'])
                            except Exception as exc:job['adaptive_rejected']=str(exc)
                    except Exception as exc:routing['model_error']=str(exc);routing['fallback']='Deterministic ranking used; no model decision claimed'
                if self.cancel.is_set() or self.rt.stop.is_set():break
                routing['selected']=[r['id'] for r in chosen]
                with self.lock:job['routing'].append(routing);self.save()
                pool=self.rt.pool
                futures={pool.submit(self.run_one,r['id'],job,overrides):r for r in chosen}
                for future in as_completed(futures):
                    row=futures[future];used.add(row['id'])
                    try:receipt=future.result()
                    except Exception as exc:receipt={'id':row['id'],'ok':False,'error':str(exc),'trit':None,'gate':None}
                    if self.cancel.is_set() or self.rt.stop.is_set():continue
                    receipt['round']=level+1;receipt['features']=row['features']
                    with self.lock:job['steps'].append(receipt);self.save()
                # Recursive routing targets unresolved issues and relevant concepts, never rewrites facts.
                unresolved=[s for s in job['steps'] if s.get('error') or s.get('gate')==1 or s.get('trit') in (None,-1)]
                query=job['text']+' '+' '.join(str(s.get('error') or '') for s in unresolved)+' '+' '.join(
                    (s.get('functional_reasoning') or {}).get('output_check','') for s in unresolved)+' truth integrity evidence restoration'
            with self.lock:
                stopped=self.cancel.is_set() or self.rt.stop.is_set();job['status']='stopped' if stopped else 'complete';job['finished']=now()
                trits=[s['trit'] for s in job['steps'] if s.get('trit') is not None]
                job['synthesis']={'executed':len(job['steps']),'successful_execution':sum(s['ok'] for s in job['steps']),
                                  'blocking_modules':[s['id'] for s in job['steps'] if s.get('gate')==1 or s.get('trit')==-1],
                                  'unknown_modules':[s['id'] for s in job['steps'] if s.get('trit') is None],
                                  'conflicting_trits':1 in trits and -1 in trits,'forced_alignment':False,
                                  'uncertainty_condition':job.get('uncertainty_condition',True),
                                  'consequence_prediction':job['preflight']['assessment'].get('classification','unknown'),
                                  'function_adapters':{s['id']:(s.get('functional_reasoning') or {}).get('profile') for s in job['steps']},
                                  'meaning':'Rule decisions about supplied or declared inputs. Repeated runs and agreement do not establish real-world virtue or benefit.'}
                self.save();save_json(self.folder/(job['id']+'-receipt.json'),job)
            if not stopped:self.rt.binary_bus.feed('drill-findings:'+job['id'],job)
        except Exception as exc:
            error=str(exc)
            with self.lock:job.update(status='error',error=error);self.save()
        finally:
            if job['provider']!='algorithm':self.rt.model_hub.release(job['provider'],error)
            with self.lock:self.busy=False

    def feedback_add(self,job_id,module,label):
        if type(label) is not int or label not in (0,1):raise ValueError('Review as useful (1) or irrelevant (0)')
        with self.lock:
            job=next((j for j in self.jobs if j['id']==job_id),None)
            step=next((s for s in job['steps'] if s['id']==module),None) if job else None
            if not step or 'features' not in step:raise ValueError('Choose a completed module receipt')
            self.feedback[job_id+'|'+module]={'features':step['features'],'label':label,'time':now()};self.save()
        return self.view()

    def train(self):
        with self.lock:
            rows=list(self.feedback.values())
            if len(rows)<20 or min(sum(r['label']==v for r in rows) for v in (0,1))<5:raise ValueError('Review at least 20 module selections, including 5 useful and 5 irrelevant, before training')
            x=np.array([r['features'] for r in rows]);y=np.array([[r['label']] for r in rows]);order=np.random.default_rng(42).permutation(len(rows));split=max(4,len(rows)//4)
            hold=order[:split];train=order[split:];model=TotalBitRealityEngine()
            for _ in range(100):model.train_batch(x[train],y[train])
            self.model=model;self.training={'examples':len(rows),'training_examples':len(train),'holdout_examples':len(hold),
                                           'holdout':model.evaluate(x[hold],y[hold]),'steps':model.steps,'features':['topic relevance','definition coverage'],
                                           'scope':'Predicts user-reviewed routing usefulness only; not good/evil or societal benefit.'};self.save()
        return self.view()
