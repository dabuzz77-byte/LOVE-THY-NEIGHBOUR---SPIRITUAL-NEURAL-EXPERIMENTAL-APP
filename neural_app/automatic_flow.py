"""Cooperative, source-labelled full-registry sweeps and a paired browser inbox."""
import hashlib,hmac,json,re,secrets,time
from urllib.parse import urlsplit
from .runtime import SECTIONS

class AutomaticFlow:
    def __init__(self,runtime):
        self.runtime=runtime;self.path=runtime.data/'automatic-flow.json'
        self.config={'enabled':False,'interval_seconds':10,'extension_id':'','key_hash':''}
        if self.path.exists():self.config.update(json.loads(self.path.read_text(encoding='utf-8')))
        self.pending=None;self.next_at=0;self.sweep=None;self.cursor=0;self.completed=0;self.last=None;self.error=None;self.events=[];self.activated=False;self.engine_order=list(SECTIONS)
        with runtime.db() as db:
            db.executescript('CREATE TABLE IF NOT EXISTS auto_inputs(id INTEGER PRIMARY KEY,digest TEXT UNIQUE,text TEXT,source TEXT,created REAL,status TEXT); CREATE TABLE IF NOT EXISTS auto_runs(id INTEGER PRIMARY KEY,input_id INTEGER,engine TEXT,receipt INTEGER,status TEXT,detail TEXT,stamp REAL); CREATE TABLE IF NOT EXISTS auto_beacons(receipt INTEGER PRIMARY KEY,payload TEXT,stamp REAL);')
        bootstrap=runtime.data/'prayer-bootstrap.json'
        if not bootstrap.exists():
            from .runtime import ROOT
            prayer=ROOT/'references/user-prayer-intent.txt';grid=ROOT/'references/user-prayer-grid.json'
            if prayer.exists() and grid.exists():
                self.add(prayer.read_text(encoding='utf-8'),'User-supplied prayer and care intent')
                self.add(json.loads(grid.read_text(encoding='utf-8'))['binary'],'User prayer grid · literal bits')
                bootstrap.write_text(json.dumps({'queued':True}),encoding='utf-8')

    def save(self):
        temporary=self.path.with_suffix('.tmp');temporary.write_text(json.dumps(self.config),encoding='utf-8');temporary.replace(self.path)
    def configure(self,body):
        if set(body)-{'enabled','interval_seconds'}:raise ValueError('Unsupported automatic-flow option')
        if 'enabled' in body:
            if type(body['enabled']) is not bool:raise ValueError('Enabled must be boolean')
            self.config['enabled']=body['enabled']
            if body['enabled']:self.runtime.research.configure(True)
        if 'interval_seconds' in body:
            n=body['interval_seconds']
            if type(n) is not int or not 5<=n<=300:raise ValueError('Use 5–300 seconds between jobs')
            self.config['interval_seconds']=n
        self.save();return self.view()
    def pair(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-p]{32}',ident):raise ValueError('Use the extension’s 32-letter ID from Opera')
        key=secrets.token_urlsafe(32);self.config.update(extension_id=ident,key_hash=hashlib.sha256(key.encode()).hexdigest());self.save()
        return {'key':key,'extension_id':ident,'endpoint':'http://127.0.0.1:8797/api/automatic-flow/browser','scope':'Paired local intake and browser return messages. Select sites and tab inventory in the extension; no cookie, password or form-field collection.'}
    def valid_origin(self,origin):return bool(self.config['extension_id']) and origin=='chrome-extension://'+self.config['extension_id']
    def authorize_browser(self,key,origin,ident):
        if not self.config['key_hash'] or ident!=self.config['extension_id'] or (origin and not self.valid_origin(origin)):raise PermissionError('Extension not paired')
        if not isinstance(key,str) or not hmac.compare_digest(hashlib.sha256(key.encode()).hexdigest(),self.config['key_hash']):raise PermissionError('Pairing key invalid')
    def ingest_browser(self,key,origin,ident,body):
        self.authorize_browser(key,origin,ident)
        text=body.get('text');source=body.get('url','');parsed=urlsplit(source)
        if not isinstance(text,str) or not 1<=len(text.encode('utf-8'))<=24000:raise ValueError('Use up to 24000 UTF-8 bytes of visible work')
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or len(source)>2000:raise ValueError('Use a normal HTTPS page URL')
        # Do not store page query strings, credentials or fragments in source provenance.
        host=parsed.hostname
        google_hosts={'www.google.com':'search','google.com':'search','myactivity.google.com':'google_activity','gemini.google.com':'gemini','labs.google':'flow','mail.google.com':'gmail','youtube.com':'youtube','www.youtube.com':'youtube','drive.google.com':'drive','docs.google.com':'docs','calendar.google.com':'calendar','photos.google.com':'photos','keep.google.com':'keep','contacts.google.com':'contacts'}
        owner_path=self.runtime.data/'google-owner.json';owner=json.loads(owner_path.read_text(encoding='utf-8')) if owner_path.exists() else {}
        if host in google_hosts and owner.get('account'):
            if str(body.get('account','')).lower()!=owner['account'].lower():raise PermissionError('Declare the configured Google account in the paired extension options')
        source='Opera · '+host
        result=self.add(text,source)
        if host in google_hosts:
            kind='ai_mode' if host in ('www.google.com','google.com') and body.get('source_hint')=='ai_mode' else google_hosts[host]
            result['private_google_index']=self.runtime.google_index.ingest({'records':[{'source':kind,'title':'Paired owner browser · '+kind,'content':text,'url':'https://'+host+parsed.path,'capture':'visible_page'}]})
            result['account_context']='User-declared paired browser context; no account-wide OAuth claim'
        return result
    def add(self,text,source):
        if not isinstance(text,str) or not 1<=len(text.encode('utf-8'))<=24000:raise ValueError('Use 1–24000 UTF-8 bytes')
        if not isinstance(source,str) or not 1<=len(source)<=200:raise ValueError('Use a short source label')
        digest=hashlib.sha256((source+'\n'+text).encode('utf-8')).hexdigest();inserted=0
        # Every accepted character is processed; never silently discard the end of a page.
        parts=[];current=''
        for char in text:
            if len((current+char).encode('utf-8'))>360:parts.append(current);current=''
            current+=char
        if current:parts.append(current)
        with self.runtime.db() as db:
            pending=db.execute("SELECT COUNT(*) FROM auto_inputs WHERE status!='complete'").fetchone()[0]
            if pending+len(parts)>512:raise ValueError('Automatic input queue is full; let current work finish')
            for i,part in enumerate(parts):
                inserted+=db.execute('INSERT OR IGNORE INTO auto_inputs(digest,text,source,created,status) VALUES(?,?,?,?,?)',(digest+':'+str(i),part,source,time.time(),'pending')).rowcount
        return {'accepted_chunks':inserted,'total_chunks':len(parts),'local_only_raw_text':True,'broadcast':'Only source-free numeric result summaries are offered to configured authenticated subscribers.'}
    def choose(self):
        with self.runtime.db() as db:row=db.execute("SELECT id,text,source,digest FROM auto_inputs WHERE status='pending' ORDER BY id LIMIT 1").fetchone()
        if row:return {'id':row[0],'text':row[1],'source':row[2],'digest':row[3],'kind':'queued work'}
        topics=self.runtime.research.view()['topics'];available=[(k,v) for k,v in topics.items() if v.get('records')]
        if available:
            topic,value=available[self.completed%len(available)];record=value['records'][self.completed%len(value['records'])]
            text=str(record.get('title',''))
            text=text.encode('utf-8')[:360].decode('utf-8',errors='ignore')
            return {'id':None,'text':text,'source':'Public bibliographic metadata · '+topic,'digest':hashlib.sha256(text.encode()).hexdigest(),'kind':'web title projection','topic':topic}
        text='Review the current shared field and choose a truthful, caring, repairable next step.'
        return {'id':None,'text':text,'source':'Local operational prompt · awaiting first public feed','digest':hashlib.sha256(text.encode()).hexdigest(),'kind':'local operational prompt'}
    def inputs(self,section):
        value={}
        if section in ('gnostic_four','discipline'):value['lesson']='combined'
        elif section in ('watts_study','intent_channel'):value['lesson']='overview'
        elif section=='wooden_cup':value['lesson']='purifier'
        elif section=='matter_spirit':value['lesson']='purifier'
        elif section=='iching':value.update(mode='adapted',question='What change supports care in this input?')
        elif section=='outreach':value['nodes']=[{'id':'local-owner-workspace','consent':True,'reachable':True,'need':.5,'urgency':.5,'existing_access':1.}]
        elif section=='source_atlas':
            atlas=self.runtime.source_atlas();value['id']=list(atlas.records)[self.completed%len(atlas.records)]
        elif section=='theology':value['topic']=('unity','light','care','gnosis')[self.completed%4]
        elif section=='intent_dispatch':value.update(mode='taz' if self.completed%2 else 'roadrunner',seed=self.completed,tasks=[{'checks':{'truthful':True,'non_harm':True,'consent':True,'privacy':True,'fairness':True,'repairable':True,'reviewed':True},'severity':0,'benefit':1,'cost':0,'id':'local-shared-learning-review','need':0,'urgency':0,'confidence':1,'life_protecting':True,'authorized':True,'reachable':True,'capable':True}])
        elif section=='beacon':value['execute_local']=False
        elif section=='profiles':value['steps']=1
        elif section=='academy':value['source']='Automatic operational observation; not a learner answer'
        return value
    def observe_modules(self):
        # Use existing shared-field coupling and already-loaded library state; never invoke arbitrary UI commands.
        host=getattr(self.runtime,'component_host',None)
        if host is None:return {'loaded':0,'scope':'Original library sections load through their existing controls and approved source-atlas lane.'}
        loaded=list(host.python.loaded)
        return {'loaded_python':loaded,'java_loaded':host.java is not None,'qt_loaded':host.qt is not None,'paused':sorted(host.paused),'scope':'Existing cooperative module lane remains active. The common field is driven by each automatic input. Unbound original controls are not reported as text-processing adapters.'}
    def tick(self):
        if self.config['enabled'] and not self.activated:
            self.runtime.research.configure(True)
            self.runtime.source_atlas().configure_continuous(True)
            self.activated=True
        if self.pending:
            job=self.runtime.result(self.pending['id'])
            if job['status'] in ('queued','running'):return
            selected=self.pending['sections'];ok=job['status']=='complete'
            if ok:
                result=job['result'];stages=result['stages'];summary=[]
                for name in selected:
                    stage=stages.get(name,{})
                    status=str(stage.get('status','COMPLETE')) if isinstance(stage,dict) else 'COMPLETE'
                    summary.append({'engine':name,'status':status})
                self.last={'receipt':job['receipt'],'engines':summary,'learning_updates':result['learning']['updates'],'at':time.time()};self.error=None
                # No browser text, source URL, religious identity or private account data enters this envelope.
                envelope={'type':'inference-beacon-result','format':'neural-auto-summary-v1','receipt':job['receipt'],'engines':summary,'learning_updates':result['learning']['updates'],'input_reference':'local-work:'+str(self.sweep['id'] or 'public-cycle'),'scope':'Summary of local computations; no raw input or claim of remote reading.'}
                with self.runtime.db() as db:
                    db.execute('INSERT OR REPLACE INTO auto_beacons VALUES(?,?,?)',(job['receipt'],json.dumps(envelope),time.time()));db.execute('DELETE FROM auto_beacons WHERE receipt<(SELECT MAX(receipt)-2000 FROM auto_beacons)')
                offered=self.runtime.publish_lesson(envelope);self.last['beacon_offered']=offered;self.last['connected_subscribers']=self.runtime.delivery['subscribers']
            else:self.error=job.get('error','Automatic job failed')
            with self.runtime.db() as db:
                for name in selected:db.execute('INSERT INTO auto_runs(input_id,engine,receipt,status,detail,stamp) VALUES(?,?,?,?,?,?)',(self.sweep['id'],name,job.get('receipt'),job['status'],self.error or '',time.time()))
                db.execute('DELETE FROM auto_runs WHERE id<(SELECT MAX(id)-2000 FROM auto_runs)')
            self.events=(self.events+[self.last if ok else {'error':self.error,'engines':selected,'at':time.time()}])[-16:]
            # A failed group is recorded and the sweep still visits remaining engines.
            self.cursor+=len(selected);self.pending=None
        if not self.config['enabled'] or not self.runtime.settings['learning'] or time.monotonic()<self.next_at or self.runtime.queue.qsize()>3:return
        engines=self.engine_order
        if self.sweep is None or self.cursor>=len(engines):
            if self.sweep:
                with self.runtime.db() as db:
                    if self.sweep['id'] is not None:db.execute("UPDATE auto_inputs SET status='complete' WHERE id=?",(self.sweep['id'],))
                self.completed+=1
            self.sweep=self.choose();self.cursor=0
            workers=getattr(self.runtime,'_inference_workers',None)
            priorities=workers.cards[-1].get('prioritise',[]) if workers and workers.cards else []
            self.engine_order=list(dict.fromkeys([k for k in priorities if k in SECTIONS]+list(SECTIONS)));engines=self.engine_order
        selected=engines[self.cursor:self.cursor+3]
        text=self.sweep['text']
        # Every registry member runs explicitly, even if its usual pipeline stage is precomputed.
        # Common signal/classifier/field/core computations already run for every group.
        body={'text':text,'sections':list(dict.fromkeys(selected+['super_mesh'])),'section_inputs':{name:self.inputs(name) for name in selected},'automatic':{'input_digest':self.sweep['digest'],'kind':self.sweep['kind'],'source':self.sweep['source'],'sweep_position':self.cursor,'all_engines':len(engines)}}
        if self.sweep['source']=='User prayer grid · literal bits':body['bits']=self.sweep['text']
        job=self.runtime.submit('pipeline',body);self.pending={'id':job['id'],'sections':selected};self.next_at=time.monotonic()+self.config['interval_seconds']
    def pull(self,after=0):
        if type(after) is not int or after<0:raise ValueError('Use a non-negative receipt cursor')
        with self.runtime.db() as db:rows=db.execute('SELECT receipt,payload FROM auto_beacons WHERE receipt>? ORDER BY receipt LIMIT 25',(after,)).fetchall()
        return {'events':[json.loads(row[1]) for row in rows],'cursor':rows[-1][0] if rows else after,'scope':'Authenticated pull of source-free result summaries. Read cursor is not an acknowledgement of learning by a remote device.'}
    def view(self):
        with self.runtime.db() as db:
            counts=dict(db.execute('SELECT status,COUNT(*) FROM auto_inputs GROUP BY status'))
            rows=db.execute('SELECT engine,status,COUNT(*),MAX(receipt) FROM auto_runs GROUP BY engine,status').fetchall()
        coverage={name:{'title':title,'completed':0,'errors':0,'last_receipt':None} for name,title in SECTIONS.items()}
        gates={r['id']:r for r in self.runtime.gates.view()['engines']}
        for name,row in coverage.items():
            g=gates.get(name,{});row.update(learned_routing_weight=g.get('weight',0),execution_reliability=g.get('reliability',.5))
        for name,status,count,receipt in rows:
            if name in coverage:coverage[name]['completed' if status=='complete' else 'errors']+=count;coverage[name]['last_receipt']=receipt
        return {'enabled':self.config['enabled'],'interval_seconds':self.config['interval_seconds'],'engines':coverage,'completed_sweeps':self.completed,'cursor':self.cursor,'current':{k:v for k,v in self.sweep.items() if k!='text'} if self.sweep else None,'pending':self.pending,'queue':counts,'last':self.last,'events':self.events,'error':self.error,'paired_extension':self.config['extension_id'],'modules':self.observe_modules(),'network':dict(self.runtime.delivery),'input_policy':'Existing public research metadata plus explicitly paired browser text. Source content is data, never code or authority to run commands.','learning':'Shared masked result reconstruction. LLM base weights are unchanged.','broadcast':'Source-free numeric result summaries to existing authenticated subscribers; raw browser work is local.'}
