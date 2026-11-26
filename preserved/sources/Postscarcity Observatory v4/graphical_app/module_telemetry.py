"""Per-invocation worker measurements and attributable output receipts."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
from types import SimpleNamespace
import psutil
from sources import now,save_json

class ModuleTelemetry:
    def __init__(self,rt):
        self.rt=rt;self.lock=threading.RLock();self.active={};self.history=[];self.last_save=0
        self.path=rt.data/'module-telemetry.json'
        try:self.history=json.loads(self.path.read_text(encoding='utf-8'))[-500:]
        except (OSError,ValueError):pass

    def snapshot(self):
        with self.rt.lock:field=self.rt.neural_output
        bus=self.rt.binary_bus.state()
        return {'field':field,'pending_bytes':bus['pending_bytes'],'processed_bytes':bus['processed_bytes'],'rejected_bytes':bus['rejected_bytes']}

    def execute(self,name,request,origin='module schedule'):
        request,primary=self.rt.primary.prepare(name,request,origin)
        key=uuid.uuid4().hex[:16];started=time.monotonic();before=self.snapshot()
        row={'id':key,'module':name,'origin':origin,'started':now(),'status':'starting','pid':None,'duration_ms':0,'cpu_seconds':0.,'peak_rss_bytes':0,'samples':0,
             'before':before,'primary_cascade':primary,'input_dictionaries':list(request.get('inputs',{})),'source_count':len(request.get('sources',[])),'definition_count':len(request.get('definitions',{}))}
        with self.lock:self.active[key]=row
        process=None
        try:
            process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('worker.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                text=True,encoding='utf-8',cwd=self.rt.root,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            monitor=psutil.Process(process.pid)
            with self.lock:row.update(pid=process.pid,status='running')
            payload=json.dumps(request)
            while True:
                try:
                    cpu=monitor.cpu_times();memory=monitor.memory_info().rss
                    with self.lock:row.update(cpu_seconds=round(cpu.user+cpu.system,4),peak_rss_bytes=max(row['peak_rss_bytes'],memory),samples=row['samples']+1,duration_ms=round((time.monotonic()-started)*1000))
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                try:output,error=process.communicate(payload,timeout=.2);break
                except subprocess.TimeoutExpired:
                    payload=None
                    if self.rt.stop.is_set() or time.monotonic()-started>25:raise TimeoutError('Worker stopped or exceeded 25 seconds')
            with self.lock:row.update(status='result processing',exit_code=process.returncode,duration_ms=round((time.monotonic()-started)*1000),stdout_bytes=len(output.encode()),stderr_bytes=len(error.encode()))
            if primary['status']=='held: target produced inside worker' and process.returncode==0:
                result=json.loads(output)
                if result.get('ok'):
                    _,observed=self.rt.primary.prepare(name,request,origin,observed=result.get('reports',{}))
                    result['primary_observed_output']=observed;output=json.dumps(result,ensure_ascii=True)
                    with self.lock:row['primary_observed_output']=observed
            return SimpleNamespace(returncode=process.returncode,stdout=output,stderr=error,telemetry_id=key)
        except Exception as exc:
            if process and process.poll() is None:
                try:
                    for child in psutil.Process(process.pid).children(recursive=True):
                        try:child.kill()
                        except psutil.Error:pass
                except psutil.Error:pass
                process.kill();process.communicate()
            with self.lock:row['duration_ms']=round((time.monotonic()-started)*1000)
            self.finish(key,{'ok':False,'error':str(exc)}, {},False)
            raise

    def finish(self,key,result,resolved,accepted,activation=None):
        after=self.snapshot()
        raw=json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8')
        with self.lock:
            row=self.active.pop(key,None)
            if not row:return
            row.update(status='complete' if result.get('ok') else 'error',finished=now(),error=str(result.get('error') or '')[:1500],
                result_sha256=hashlib.sha256(raw).hexdigest(),result_bytes=len(raw),result_bus_accepted=bool(accepted),
                reports=list(result.get('reports',{})),trit=resolved.get('trit'),gate=resolved.get('gate'),activation=activation,after=after,
                sampling_scope='Worker process only; memory is a sampled peak. Child-process activity is not included.',
                effect_scope='Outputs, bus receipt and node activation are direct effects. Before/after field and queue changes include other running work; no causal societal benefit is inferred.')
            self.history.append(row);self.history=self.history[-500:]
            if time.monotonic()-self.last_save>5:self.save()

    def save(self):
        with self.lock:save_json(self.path,self.history);self.last_save=time.monotonic()

    def view(self):
        with self.lock:active=copy.deepcopy(list(self.active.values()));history=copy.deepcopy(self.history[-150:])
        with self.rt.lock:
            modules=[{k:m.get(k) for k in ('id','title','status','runs','duration_ms','trit','gate','error','last_run')} for m in self.rt.modules.values()]
            processes=copy.deepcopy(self.rt.processes);clients=copy.deepcopy(list(self.rt.clients.values()))
        return {'active':active,'history':history,'modules':modules,'processes':processes,'clients':clients,'workers':16,
            'retained_runs':len(self.history),'bus':self.rt.binary_bus.state(),'field':self.rt.neural_output,
            'scope':'Actual module workers and cooperative bus/process telemetry. The system does not read private process memory or infer external outcomes from activity.'}
