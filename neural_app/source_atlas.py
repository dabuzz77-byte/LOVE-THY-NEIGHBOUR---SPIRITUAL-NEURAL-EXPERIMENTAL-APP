"""Deduplicated Desktop/java source and procedural-graphics catalogue."""
import hashlib,json,re,threading,time
from pathlib import Path

class SourceAtlas:
    def __init__(self,runtime):
        self.runtime=runtime;self.root=Path(__file__).resolve().parents[1];self.ref=self.root/'references'/'desktop-java'
        self.manifest=json.loads((self.ref/'manifest.json').read_text(encoding='utf-8'))
        self.records={}
        for row in self.manifest['records']:
            if row['id'] not in self.records:self.records[row['id']]={**row,'aliases':[]}
            self.records[row['id']]['aliases'].append(row['path'])
        self.projects={r['name']:r for r in self.manifest['projects']}
        self.panels=json.loads((self.ref/'panels.json').read_text(encoding='utf-8'))
        self.batch=None;self.batch_lock=threading.Lock()
        self.continuous={'enabled':False,'loaded':0,'native_entries':len(self.panels),'observations':0,'analysis_jobs':0,'errors':[]}
        self.loaded_native=set();self.native_cursor=0;self.analysis_cursor=0;self.analysis_at=0
        with runtime.db() as db:db.execute('CREATE TABLE IF NOT EXISTS source_atlas_processed(source TEXT PRIMARY KEY,receipt INTEGER,stamp REAL)')

    def catalogue(self):
        summary=json.loads((self.ref/'summary.json').read_text(encoding='utf-8'))
        graphics=self.ref/'rendered-graphics.json'
        return {'summary':summary,'graphics':json.loads(graphics.read_text(encoding='utf-8')) if graphics.exists() else [],'records':[{k:v for k,v in r.items() if k!='object'} for r in self.records.values()],
                'projects':[{k:v for k,v in p.items() if k!='diagnostics'} for p in self.projects.values()],
                'panels':self.panels,'batch':self.batch,'continuous':dict(self.continuous)}

    def configure_continuous(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.continuous['enabled']=enabled
        path=self.runtime.data/'source-atlas-settings.json'
        settings=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        settings['continuous']=enabled;path.write_text(json.dumps(settings,indent=2),encoding='utf-8')
        if enabled and not hasattr(self.runtime,'component_host'):
            from .component_host import ComponentHost
            ComponentHost(self.runtime)
        if not enabled and hasattr(self.runtime,'component_host'):
            for panel in self.panels:self.runtime.component_host.pause(panel['id'],True)
        return dict(self.continuous)

    def background_step(self,host):
        if not self.continuous['enabled'] or self.runtime.halt.is_set() or not self.panels:return
        panel=self.panels[self.native_cursor%len(self.panels)];self.native_cursor+=1
        try:
            host.pause(panel['id'],False)
            value=host.open(panel['id'])
            self.loaded_native.add(panel['id']);self.continuous['loaded']=len(self.loaded_native)
            self.runtime.component_result(panel['id'],{'source':'continuous shared Java state observation'},value)
            self.continuous['observations']+=1
        except Exception as error:self.continuous['errors']=(self.continuous['errors']+[str(error)[:300]])[-5:]
        # Revisit source analysis while native state uses the existing shared timer lane.
        if time.monotonic()-self.analysis_at>=30 and self.runtime.queue.qsize()<2:
            ids=list(self.records);ident=ids[self.analysis_cursor%len(ids)];self.analysis_cursor+=1
            self.runtime.submit('pipeline',self.input(ident));self.analysis_at=time.monotonic();self.continuous['analysis_jobs']+=1

    def source(self,ident):
        if ident not in self.records:raise ValueError('Choose a catalogued source ID')
        row=self.records[ident];path=(self.root/row['object']).resolve()
        if not path.is_relative_to((self.root/'preserved'/'desktop-java').resolve()):raise ValueError('Invalid source boundary')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ident:raise ValueError('Preserved source digest changed')
        from nexus_conversations import scrub
        text=scrub(raw.decode('utf-8-sig',errors='replace'))
        return {'record':{k:v for k,v in row.items() if k!='object'},'text':text[:120000],'total_characters':len(text),
                'project':self.projects.get(row['project']),'panels':[p for p in self.panels if p['source']==ident]}

    def measure(self,body):
        row=self.records.get(body.get('id'))
        if not row:
            if body.get('id') is None:return {'status':'AWAITING_INPUT','required':'Select a catalogued source ID','available_versions':len(self.records)}
            raise ValueError('Choose a source from the Java source atlas')
        project=self.projects.get(row['project'],{})
        return {'status':'COMPLETE','source_id':row['id'],'source_bytes':row['bytes'],'aliases':row['aliases'],
                'drawing_operations':row['drawing_operations'],'compiled':project.get('compiled',False),'flags':row['flags'],
                'actual_runtime':self.runtime.metrics(),'shared_field_ticks':self.runtime.field.ticks,
                'routing_features':[min(1,row['bytes']/100000),min(1,sum(row['drawing_operations'].values())/100)],
                'scope':'Source structure and current runtime measurements. This analysis does not execute the preserved program or verify its authored real-world claims.'}

    def input(self,ident):
        row=self.records.get(ident)
        if not row:raise ValueError('Unknown source')
        # No source code, private literals or executable instructions enter inference here.
        # Compact routing label; the complete ID and measured source features remain in the structured stage.
        text='source:'+ident[:12]
        return {'text':text,'sections':['source_atlas','suite','unified','platform_alignment','karmic_welfare','virtue_text','reference','inference'],
                'section_inputs':{'source_atlas':{'id':ident}},'source_atlas':{'id':ident}}

    def start_batch(self):
        if not self.batch_lock.acquire(False):raise ValueError('A source-atlas batch is already running')
        with self.runtime.db() as db:processed={row[0] for row in db.execute('SELECT source FROM source_atlas_processed')}
        ids=[r['id'] for r in self.records.values() if r['kind']=='code' and r['id'] not in processed]
        self.batch={'total':len(ids),'completed':0,'failed':0,'status':'running','last_receipt':None,'errors':[]}
        def run():
            try:
                for ident in ids:
                    if self.runtime.halt.is_set():self.batch['status']='stopped';break
                    try:
                        while self.runtime.queue.qsize()>2 and not self.runtime.halt.wait(.25):pass
                        if self.runtime.halt.is_set():break
                        job=self.runtime.submit('pipeline',self.input(ident))
                        while not self.runtime.halt.wait(.05):
                            result=self.runtime.result(job['id'])
                            if result['status'] not in ('queued','running'):break
                        if self.runtime.halt.is_set():break
                        if result['status']=='error':raise ValueError(result.get('error','Processing error'))
                        self.batch['completed']+=1;self.batch['last_receipt']=result['receipt']
                        with self.runtime.db() as db:db.execute('INSERT OR REPLACE INTO source_atlas_processed VALUES(?,?,?)',(ident,result['receipt'],time.time()))
                    except Exception as error:self.batch['failed']+=1;self.batch['errors']=(self.batch['errors']+[str(error)[:300]])[-5:]
                if self.batch['status']=='running':self.batch['status']='complete' if not self.runtime.halt.is_set() else 'stopped'
            finally:
                (self.runtime.data/'source-atlas-batch.json').write_text(json.dumps(self.batch,indent=2),encoding='utf-8');self.batch_lock.release()
        threading.Thread(target=run,name='neural-source-atlas-batch',daemon=True).start()
        return dict(self.batch)
