"""Automatic attributed definition research, feeding complete articles into the pipeline."""
import hashlib
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from hub import database
from library import API, DEFAULT_TOPICS, fetch_article, LICENSE_URL

# Public concepts detected locally. Personal messages, paths and credentials are
# never copied wholesale into a remote search query.
CONCEPTS = {
    'neural':'Artificial neural network','learning':'Machine learning','feedback':'Reinforcement learning',
    'ethic':'Ethics','virtue':'Virtue ethics','evil':'Good and evil','moral':'Morality',
    'binary':'Binary number','ternary':'Balanced ternary','boolean':'Boolean algebra',
    'resource':'Resource allocation','floor':'Social protection floor','geothermal':'Geothermal energy',
    'automation':'Automation','labor':'Technological unemployment','labour':'Technological unemployment',
    'reserve':'Fractional-reserve banking','interest':'Interest','scarcity':'Post-scarcity',
    'tesla':'Nikola Tesla','fuller':'Buckminster Fuller','fresco':'Jacque Fresco',
    'latency':'Latency (engineering)','vram':'Video random-access memory','python':'Python (programming language)',
    'java':'Java (programming language)','opera':'Opera (web browser)','cpu':'Central processing unit',
    'memory':'Computer memory','sqlite':'SQLite','hmac':'HMAC','privacy':'Information privacy',
    'quarantine':'Quarantine (computing)','token':'Access token','dividend':'Dividend',
    'energy':'Energy','hydrogen':'Hydrogen','silicon':'Silicon','network':'Computer network',
    'autoencoder':'Autoencoder','conservation':'Conservation law','human':'Human rights',
}


def discover_topics(payload):
    text=[]
    def read(item):
        if isinstance(item,str):text.append(item)
        elif isinstance(item,dict):
            for key in ('text','prompt','raw_input','raw_output','summary','title'):
                if key in item:read(item[key])
        elif isinstance(item,list):
            for child in item:read(child)
    read(payload)
    terms=set(re.findall(r'[a-z]+',' '.join(text).lower()))
    return sorted({topic for term,topic in CONCEPTS.items() if any(word.startswith(term) for word in terms)})


def research_article(topic):
    try:return fetch_article(topic)
    except ValueError:
        params={'action':'query','list':'search','srsearch':topic,'srlimit':1,'format':'json','formatversion':2}
        request=urllib.request.Request(API+'?'+urllib.parse.urlencode(params),headers={'User-Agent':'FluxBus/2.0 (personal reference research)','Accept':'application/json'})
        with urllib.request.urlopen(request,timeout=18) as response:result=json.load(response)
        if 'error' in result:raise RuntimeError(result['error'].get('info','Search unavailable'))
        rows=result.get('query',{}).get('search',[])
        if not rows:raise ValueError('No Wikipedia article found for '+topic)
        return fetch_article(rows[0]['title'])


class WebResearch:
    def __init__(self,store,pipeline,fetcher=research_article):
        self.store=store;self.pipeline=pipeline;self.fetcher=fetcher
        self.stop_event=threading.Event();self.wake=threading.Event();self.lock=threading.RLock();self.thread=None
        self.enabled=store.setting('research_enabled','true')=='true'
        self.interval=float(store.setting('research_interval','60'));self.next_request=0
        self.status='Ready';self.current='';self.error=''
        with database(pipeline.db_path) as conn:cursor=conn.execute('SELECT COALESCE(MAX(rowid),0) FROM pipeline_jobs').fetchone()[0]
        with store.connect() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS research_cursor(id INTEGER PRIMARY KEY,cursor INTEGER);
                CREATE TABLE IF NOT EXISTS research_topics(topic TEXT PRIMARY KEY,origin TEXT,manual INTEGER,due REAL,attempts INTEGER DEFAULT 0);
                CREATE INDEX IF NOT EXISTS research_due ON research_topics(manual DESC,due);
                CREATE TABLE IF NOT EXISTS research_history(id INTEGER PRIMARY KEY,topic TEXT,created REAL,status TEXT,url TEXT,revision TEXT,job_id TEXT,error TEXT);
            ''')
            conn.execute('INSERT OR IGNORE INTO research_cursor VALUES(1,?)',(cursor,))
            for topic in (*DEFAULT_TOPICS,'Artificial neural network','Autoencoder','Resource allocation'):
                conn.execute('INSERT OR IGNORE INTO research_topics(topic,origin,manual,due) VALUES(?,?,0,0)',(topic,'Initial definition library'))

    def set_enabled(self,value):
        self.enabled=bool(value);self.store.set_setting('research_enabled',str(self.enabled).lower());self.wake.set()

    def set_interval(self,value):
        if not 10<=int(value)<=3600:raise ValueError('Choose 10–3600 seconds')
        self.interval=int(value);self.store.set_setting('research_interval',self.interval)

    def request(self,topic,origin='Manual topic',manual=True):
        topic=str(topic).strip()
        if not topic:raise ValueError('Enter a research topic')
        with self.store.connect() as conn:
            if manual:
                conn.execute('INSERT INTO research_topics(topic,origin,manual,due) VALUES(?,?,1,0) ON CONFLICT(topic) DO UPDATE SET manual=1,due=0,origin=excluded.origin',(topic,origin))
            else:conn.execute('INSERT OR IGNORE INTO research_topics(topic,origin,manual,due) VALUES(?,?,0,0)',(topic,origin))
        self.wake.set()

    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stop_event.clear();self.thread=threading.Thread(target=self._loop,name='Automatic web research',daemon=True);self.thread.start()

    def stop(self):
        self.stop_event.set();self.wake.set()
        if self.thread:self.thread.join(1)

    def discover(self):
        if not self.enabled:return
        with self.store.connect() as conn:cursor=conn.execute('SELECT cursor FROM research_cursor WHERE id=1').fetchone()[0]
        with database(self.pipeline.db_path) as conn:
            rows=conn.execute('SELECT rowid AS seq,id,source,input_json,result_json FROM pipeline_jobs WHERE rowid>? ORDER BY rowid LIMIT 40',(cursor,)).fetchall()
        for row in rows:
            if row['source'].lower() not in ('definitions','web research','telemetry'):
                payload=json.loads(row['input_json'])
                if isinstance(payload,str):
                    try:payload=json.loads(payload)
                    except ValueError:pass
                topics=discover_topics(payload)
                if row['result_json']:
                    report=json.loads(row['result_json'])
                    for engine in report.get('engines',[]):
                        topics+=discover_topics({'text':re.sub(r'([a-z])([A-Z])',r'\1 \2',engine['engine'])})
                for topic in set(topics):self.request(topic,'Input '+row['id'],False)
            with self.store.connect() as conn:conn.execute('UPDATE research_cursor SET cursor=? WHERE id=1',(row['seq'],))

    def process_next(self):
        self.discover()
        with self.store.connect() as conn:
            row=conn.execute('SELECT * FROM research_topics WHERE manual=1 OR (? AND due<=?) ORDER BY manual DESC,due,topic LIMIT 1',(int(self.enabled),time.time())).fetchone()
        if not row:return False
        if not row['manual'] and time.time()<self.next_request:return False
        self.current=row['topic'];self.status='Researching '+self.current
        article=None;job=None;error='';status='FETCHED'
        try:
            article=self.fetcher(row['topic'])
            if self.stop_event.is_set():return False
            self.store.save(article)
            stable={k:v for k,v in article.items() if k!='fetched_at'}
            job=self.pipeline.submit('web research',article['title'],{'article':stable,'license':LICENSE_URL},force=False)
            self.status=('Ingested ' if job else 'Unchanged reference: ')+article['title'];self.error=''
        except Exception as failure:
            error=str(failure);status='ERROR';self.error=error;self.status='Retry scheduled: '+row['topic']
        finally:self.current=''
        with self.store.connect() as conn:
            conn.execute('INSERT INTO research_history(topic,created,status,url,revision,job_id,error) VALUES(?,?,?,?,?,?,?)',
                (row['topic'],time.time(),status,(article or {}).get('url',''),(article or {}).get('revision',''),job,error))
            conn.execute('UPDATE research_topics SET manual=0,due=?,attempts=attempts+1 WHERE topic=?',(time.time()+(21600 if not error else 3600),row['topic']))
        self.next_request=time.time()+self.interval
        return True

    def snapshot(self):
        return dict(enabled=self.enabled,running=bool(self.thread and self.thread.is_alive()),status=self.status,error=self.error,
                    current=self.current,interval_seconds=self.interval,refresh_hours=6,
                    source='Wikipedia introductory articles, attributed by URL and revision',
                    discovery='Public concept names matched locally in inputs and engine names; manual topics are also supported')

    def history(self):
        with self.store.connect() as conn:return [dict(r) for r in conn.execute('SELECT * FROM research_history ORDER BY id DESC LIMIT 100')]

    def topics(self):
        with self.store.connect() as conn:return [dict(r) for r in conn.execute('SELECT * FROM research_topics ORDER BY manual DESC,due,topic')]

    def _loop(self):
        while not self.stop_event.is_set():
            try:self.process_next()
            except Exception as error:self.error=str(error)
            self.wake.wait(2);self.wake.clear()
