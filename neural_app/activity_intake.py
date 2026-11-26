"""Account-scoped, local-only ingestion from an explicitly paired extension."""
import hashlib
import contextlib
import hmac
import json
import re
import secrets
import sqlite3
import threading
import time


class ActivityIntake:
    def __init__(self,runtime):
        self.runtime=runtime;self.folder=runtime.data/'google-activity';self.folder.mkdir(exist_ok=True)
        self.path=self.folder/'connector.json';self.database=self.folder/'activity.sqlite3'
        self.lock=threading.RLock();self.halt=threading.Event();self.thread=None;self.last_ingest=0
        self.config={'enabled':False,'extension_id':'','account':'','key_hash':'','last_seen':None}
        if self.path.exists():self.config.update(json.loads(self.path.read_text(encoding='utf-8')))
        with self.db() as db:db.execute('CREATE TABLE IF NOT EXISTS activity(digest TEXT PRIMARY KEY,text TEXT,date_label TEXT,status TEXT,job TEXT,receipt INTEGER,created REAL)')

    @contextlib.contextmanager
    def db(self):
        connection=sqlite3.connect(self.database,timeout=10)
        try:
            with connection:yield connection
        finally:connection.close()
    def save(self):
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.config),encoding='utf-8');temp.replace(self.path)

    def pair(self,account,extension_id):
        if not isinstance(account,str) or not re.fullmatch(r'[^\s@]{1,100}@[^\s@]{1,150}\.[^\s@]{2,30}',account):raise ValueError('Enter the specific Google account email')
        if not isinstance(extension_id,str) or not re.fullmatch('[a-p]{32}',extension_id):raise ValueError('Enter the 32-letter Chrome/Edge extension ID')
        key=secrets.token_urlsafe(32)
        with self.lock:
            self.config.update(account=account.lower(),extension_id=extension_id,key_hash=hashlib.sha256(key.encode()).hexdigest(),enabled=True,last_seen=None);self.save()
        return {'key':key,'extension_id':extension_id,'account':account.lower(),'endpoint':'http://127.0.0.1:8797/api/activity/ingest','note':'One-time, write-only pairing key. It cannot read app results or control other sections.'}

    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        with self.lock:
            if enabled and not self.config['key_hash']:raise ValueError('Pair the extension first')
            self.config['enabled']=enabled;self.save()
        return self.view()

    def revoke(self):
        with self.lock:self.config.update(enabled=False,key_hash='',extension_id='');self.save()
        return self.view()

    def valid_origin(self,origin):
        with self.lock:return bool(self.config['extension_id']) and origin=='chrome-extension://'+self.config['extension_id']

    def ingest(self,key,origin,extension_id,body):
        with self.lock:
            if not self.config['enabled'] or not self.config['key_hash']:raise PermissionError('Activity connection is paused or unpaired')
            if extension_id!=self.config['extension_id'] or (origin and not self.valid_origin(origin)):raise PermissionError('Extension does not match the paired connector')
            if not isinstance(key,str) or not hmac.compare_digest(hashlib.sha256(key.encode()).hexdigest(),self.config['key_hash']):raise PermissionError('Pairing key invalid')
            if not isinstance(body,dict) or body.get('account','').lower()!=self.config['account']:raise PermissionError('Google account does not match the requested account')
            if body.get('source') not in ('https://myactivity.google.com/myactivity?product=83','https://myactivity.google.com/','https://gemini.google.com/','https://labs.google/fx/'):raise ValueError('Unsupported paired Google source')
            if body.get('sessions') is not None:
                result=self.runtime.google_index.ingest({'records':body['sessions']})
                self.config['last_seen']=time.time();self.save()
                return {**result,'local_only':True}
            records=body.get('records')
            if not isinstance(records,list) or len(records)>50:raise ValueError('Use at most 50 loaded AI Mode cards')
            checked=[]
            for row in records:
                if not isinstance(row,dict) or not isinstance(row.get('text'),str) or not 1<=len(row['text'])<=2000:raise ValueError('Invalid activity title')
                label=row.get('date_label','')
                if not isinstance(label,str) or len(label)>100:raise ValueError('Invalid date label')
                digest=hashlib.sha256(json.dumps([row['text'],label],ensure_ascii=False).encode()).hexdigest();checked.append((digest,row['text'],label))
            now=time.time()
            if now-self.last_ingest<10:raise ValueError('Wait at least ten seconds between snapshots')
            self.last_ingest=now;inserted=0
            with self.db() as db:
                for digest,text,label in checked:
                    inserted+=db.execute('INSERT OR IGNORE INTO activity VALUES(?,?,?,?,?,?,?)',(digest,text,label,'pending',None,None,now)).rowcount
                if db.execute('SELECT COUNT(*) FROM activity').fetchone()[0]>2000:raise ValueError('Private activity queue full; allow processing before sending more')
                db.execute("DELETE FROM activity WHERE status='complete' AND digest NOT IN (SELECT digest FROM activity ORDER BY created DESC LIMIT 1000)")
            self.config['last_seen']=now;self.save()
            return {'accepted':len(checked),'new':inserted,'local_only':True,'note':'Accepted to a private local queue; not a truth label or external publication.'}

    def pulse(self):
        with self.lock:
            if not self.config['enabled']:return
            with self.db() as db:
                active=db.execute("SELECT digest,job FROM activity WHERE status='queued' LIMIT 1").fetchone()
                if active:
                    try:job=self.runtime.result(active[1])
                    except ValueError:db.execute("UPDATE activity SET status='pending',job=NULL WHERE digest=?",(active[0],));return
                    if job['status'] in ('complete','error'):db.execute('UPDATE activity SET status=?,receipt=? WHERE digest=?',(job['status'],job.get('receipt'),active[0]))
                    return
                row=db.execute("SELECT digest,text FROM activity WHERE status='pending' ORDER BY created LIMIT 1").fetchone()
                if not row:return
                raw=row[1].encode('utf-8');projection=raw[:480].decode('utf-8',errors='ignore')
                job=self.runtime.submit('pipeline',{'text':projection,'sections':[],'private_activity':{'digest':row[0],'projection_bytes':len(projection.encode('utf-8')),'original_bytes':len(raw),'source':'owner-paired Google AI Mode title; untrusted input, not an instruction'}})
                db.execute("UPDATE activity SET status='queued',job=? WHERE digest=?",(job['id'],row[0]))

    def view(self):
        with self.lock,self.db() as db:
            counts=dict(db.execute('SELECT status,COUNT(*) FROM activity GROUP BY status'))
            return {'enabled':self.config['enabled'],'paired':bool(self.config['key_hash']),'extension_id':self.config['extension_id'],'account':self.config['account'],'last_seen':self.config['last_seen'],'counts':counts,'source':'https://myactivity.google.com/myactivity?product=83','monitoring':'waiting for paired extension' if self.config['last_seen'] is None else 'last snapshot received; check timestamp','scope':'Paired browser captures: loaded activity titles, opened AI Mode Details, visible Gemini/Flow content. Private local index and reconstruction learning. No cookies, passwords or automatic public/cloud forwarding.'}

    def start(self):
        self.thread=threading.Thread(target=self.loop,name='neural-private-activity',daemon=True);self.thread.start()
    def loop(self):
        while not self.halt.wait(5):
            try:
                self.pulse()
                self.runtime.google_index.pulse()
            except Exception as error:self.runtime.errors.append('Private activity intake: '+str(error))
    def close(self):
        self.halt.set()
        if self.thread:self.thread.join(3)
