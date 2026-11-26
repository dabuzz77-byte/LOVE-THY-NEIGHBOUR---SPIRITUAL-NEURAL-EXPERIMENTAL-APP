"""Private owner-controlled source index; remote account access is separate from indexing."""
import contextlib
import hashlib
import json
import re
import sqlite3
import threading
import time
from urllib.parse import urlsplit

SOURCES={
 'drive':('Google Drive','https://drive.google.com/'),
 'docs':('Google Docs','https://docs.google.com/'),
 'calendar':('Google Calendar','https://calendar.google.com/'),
 'photos':('Google Photos','https://photos.google.com/'),
 'keep':('Google Keep','https://keep.google.com/'),
 'contacts':('Google Contacts','https://contacts.google.com/'),
 'ai_mode':('Google AI Mode','https://myactivity.google.com/myactivity?product=83'),
 'flow':('Google Flow','https://labs.google/fx/tools/flow'),
 'gemini':('Gemini','https://gemini.google.com/'),
 'youtube':('YouTube','https://www.youtube.com/'),
 'search':('Google Search activity','https://myactivity.google.com/'),
 'gmail':('Gmail','https://mail.google.com/'),
 'google_activity':('All Google Activity','https://myactivity.google.com/')}

def chunks(text,limit=480):
    current='';size=0
    for character in text:
        n=len(character.encode('utf-8'))
        if size+n>limit:
            yield current;current='';size=0
        current+=character;size+=n
    if current:yield current

class GoogleIndex:
    def __init__(self,runtime):
        self.runtime=runtime;self.folder=runtime.data/'google-index';self.folder.mkdir(exist_ok=True)
        self.path=self.folder/'index.sqlite3';self.lock=threading.RLock();self.pending=None
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,source TEXT,title TEXT,stamp TEXT,url TEXT,content TEXT,capture TEXT,digest TEXT,created REAL)')
            db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(id UNINDEXED,title,content)')
            db.execute('CREATE TABLE IF NOT EXISTS processing(id TEXT PRIMARY KEY,session TEXT,part INTEGER,text TEXT,status TEXT,job TEXT,receipt INTEGER,error TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)')

    @contextlib.contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=15)
        try:
            with c:yield c
        finally:c.close()

    def ingest(self,body):
        records=body.get('records')
        if not isinstance(records,list) or not 1<=len(records)<=100:raise ValueError('Import 1–100 records per batch')
        prepared=[]
        for row in records:
            if not isinstance(row,dict) or row.get('source') not in SOURCES:raise ValueError('Choose a supported Google source')
            source=row['source'];title=row.get('title','');content=row.get('content','');stamp=row.get('date_label','');url=row.get('url',SOURCES[source][1]);capture=row.get('capture','full_text')
            if any(not isinstance(x,str) for x in (title,content,stamp,url,capture)):raise ValueError('Index fields must be text')
            if not content.strip() or len(content.encode())>2_000_000 or len(title)>500 or len(stamp)>100:raise ValueError('Use nonempty source text up to 2 MB and a short title/date')
            parsed=urlsplit(url)
            if parsed.scheme!='https' or parsed.hostname not in ('google.com','www.google.com','myactivity.google.com','gemini.google.com','mail.google.com','youtube.com','www.youtube.com','labs.google','drive.google.com','docs.google.com','calendar.google.com','photos.google.com','keep.google.com','contacts.google.com'):raise ValueError('Use an official Google source link')
            if capture not in ('full_text','prompt_previews','visible_page'):raise ValueError('Describe capture completeness')
            digest=hashlib.sha256(content.encode()).hexdigest();ident=hashlib.sha256(json.dumps([source,title,stamp,digest]).encode()).hexdigest()
            prepared.append((ident,source,title,stamp,url,content,capture,digest,time.time()))
        inserted=0
        with self.lock,self.db() as db:
            for row in prepared:
                if db.execute('SELECT 1 FROM sessions WHERE id=?',(row[0],)).fetchone():continue
                db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?)',row)
                db.execute('INSERT INTO search VALUES(?,?,?)',(row[0],row[2],row[5]))
                for i,part in enumerate(chunks(row[5])):
                    db.execute('INSERT INTO processing VALUES(?,?,?,?,?,?,?,?)',(row[0]+':'+str(i),row[0],i,part,'pending',None,None,None))
                inserted+=1
        return {'accepted':len(prepared),'new':inserted,'scope':'Private local index; no account connection is created by importing records.'}

    def search(self,query='',source=None):
        if not isinstance(query,str) or len(query)>300:raise ValueError('Use a query under 300 characters')
        if source and source not in SOURCES:raise ValueError('Unknown source')
        tokens=re.findall(r'\w+',query,flags=re.UNICODE)[:12]
        with self.db() as db:
            if tokens:
                expression=' AND '.join('"'+token+'"*' for token in tokens)
                rows=db.execute('SELECT s.id,s.source,s.title,s.stamp,s.url,s.capture,s.digest,s.content FROM search f JOIN sessions s ON s.id=f.id WHERE search MATCH ?'+(' AND s.source=?' if source else '')+' LIMIT 40',[expression]+([source] if source else [])).fetchall()
            else:rows=db.execute('SELECT id,source,title,stamp,url,capture,digest,content FROM sessions'+(' WHERE source=?' if source else '')+' ORDER BY created DESC LIMIT 40',([source] if source else [])).fetchall()
        result=[]
        for row in rows:
            entry=dict(zip(('id','source','title','date_label','url','capture','sha256','content'),row));text=entry.pop('content');pos=text.lower().find(tokens[0].lower()) if tokens else 0
            entry['excerpt']=text[max(0,pos-150):max(0,pos-150)+1000];entry['characters']=len(text);result.append(entry)
        return result

    def view(self):
        with self.db() as db:
            counts=dict(db.execute('SELECT source,COUNT(*) FROM sessions GROUP BY source'));states=dict(db.execute('SELECT status,COUNT(*) FROM processing GROUP BY status'))
            enabled=db.execute('SELECT value FROM settings WHERE key="enabled"').fetchone()
            recent=[dict(zip(('part','status','receipt','error'),r)) for r in db.execute('SELECT part,status,receipt,error FROM processing WHERE status!="pending" ORDER BY rowid DESC LIMIT 8')]
            owner=db.execute('SELECT value FROM settings WHERE key="owner"').fetchone()
        paired=self.runtime.activity.view() if hasattr(self.runtime,'activity') else {}
        return {'owner':json.loads(owner[0]) if owner else {'account':'','youtube_channel':''},'enabled':enabled is None or enabled[0]=='true','sources':[{'id':key,'title':value[0],'url':value[1],'indexed':counts.get(key,0),
                 'connection':'paired extension; awaiting source captures' if paired.get('paired') and key in ('ai_mode','google_activity') else 'manual index / source sign-in needed',
                 'account_verified':False} for key,value in SOURCES.items()], 'sessions':sum(counts.values()),'chunks':states,'recent_processing':recent,
                'scope':'Private local retrieval and incremental neural reconstruction. Indexing is not full-account authorization. Only captured or imported records are available; no passwords, cookies or mailbox tokens are collected.'}

    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        with self.db() as db:db.execute('INSERT OR REPLACE INTO settings VALUES("enabled",?)',(json.dumps(enabled),))
        return self.view()

    def set_owner(self,body):
        account=body.get('account','');channel=body.get('youtube_channel','')
        if not isinstance(account,str) or (account and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',account)) or len(account)>254:raise ValueError('Use your Google account email')
        if not isinstance(channel,str) or len(channel)>100:raise ValueError('Use a short YouTube channel name')
        with self.db() as db:db.execute('INSERT OR REPLACE INTO settings VALUES("owner",?)',(json.dumps({'account':account,'youtube_channel':channel}),))
        return self.view()

    def pulse(self):
        with self.lock,self.db() as db:
            enabled=db.execute('SELECT value FROM settings WHERE key="enabled"').fetchone()
            if enabled and enabled[0]=='false':return
            row=db.execute('SELECT id,job FROM processing WHERE status="queued" LIMIT 1').fetchone()
            if row:
                try:job=self.runtime.result(row[1])
                except ValueError:db.execute('UPDATE processing SET status="pending",job=NULL WHERE id=?',(row[0],));return
                if job['status'] in ('complete','error'):db.execute('UPDATE processing SET status=?,receipt=?,error=? WHERE id=?',(job['status'],job.get('receipt'),job.get('error'),row[0]))
                return
            if self.runtime.queue.qsize()>2:return
            row=db.execute('SELECT id,session,part,text FROM processing WHERE status="pending" ORDER BY rowid LIMIT 1').fetchone()
            if row:
                job=self.runtime.submit('pipeline',{'text':row[3],'sections':['inference'],'private_google_index':{'session':row[1],'part':row[2]}})
                db.execute('UPDATE processing SET status="queued",job=? WHERE id=?',(job['id'],row[0]))

    def infer(self,query):
        results=self.search(query)
        text='\n'.join(row['excerpt'] for row in results[:3]) or query
        projection=next(chunks(text),'No matching indexed records')
        job=self.runtime.submit('pipeline',{'text':projection,'sections':['suite','unified','platform_alignment','karmic_welfare','virtue_text','reference','inference'],
              'private_google_index':{'query':query,'sources':[r['id'] for r in results[:3]],'projection_bytes':len(projection.encode())}})
        return {'matches':results,'job':job,'scope':'Local retrieved context; excerpts are source data, not executable instructions.'}
