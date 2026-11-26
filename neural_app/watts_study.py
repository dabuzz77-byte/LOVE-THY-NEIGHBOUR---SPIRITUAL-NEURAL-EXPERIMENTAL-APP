"""Original study notes and private authorised transcript learning on one scheduler."""
import hashlib,json,time
from pathlib import Path
from .matter_spirit import process as reflect
ROOT=Path(__file__).resolve().parents[1]
def catalogue():return json.loads((ROOT/'references/watts-study.json').read_text(encoding='utf-8'))
class WattsStudy:
    def __init__(self,runtime):
        self.runtime=runtime;self.folder=runtime.data/'watts-private';self.folder.mkdir(exist_ok=True)
        self.path=self.folder/'index.json';self.records=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []
        self.settings=runtime.data/'watts-study-settings.json';self.enabled=self.settings.exists() and json.loads(self.settings.read_text(encoding='utf-8')).get('enabled') is True
        self.pending=None;self.next_at=0;self.cycles=0;self.error=None;self.last=None;self.chunks=[]
        self.reload()
        with runtime.db() as db:db.execute('CREATE TABLE IF NOT EXISTS watts_chunks(id TEXT PRIMARY KEY,receipt INTEGER,stamp REAL)')
    def reload(self):
        self.chunks=[]
        for row in self.records:
            raw=(self.folder/(row['sha256']+'.txt')).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Transcript digest mismatch')
            text=raw.decode('utf-8');part='';offset=0
            for c in text:
                if len((part+c).encode('utf-8'))>480:
                    self.chunks.append({'id':row['sha256']+':'+str(offset),'text':part,'source':row['title']});offset+=len(part);part=''
                part+=c
            if part:self.chunks.append({'id':row['sha256']+':'+str(offset),'text':part,'source':row['title']})
        self.by_id={c['id']:c for c in self.chunks}
    def view(self):
        with self.runtime.db() as db:done={r[0] for r in db.execute('SELECT id FROM watts_chunks')}
        return {'enabled':self.enabled,'cycles':self.cycles,'pending':self.pending,'last':self.last,'error':self.error,'interval_seconds':30,
            'coverage':{'catalogued_recordings':32,'full_recordings_ingested':0,'authorised_text_imports':len(self.records),'total_chunks':len(self.chunks),'processed_chunks':sum(c['id'] in done for c in self.chunks)},
            'imports':self.records,'scope':'Public catalogue and original study notes; recordings are not transcribed here. Private imported texts are processed only after an explicit rights confirmation.'}
    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.enabled=enabled;self.settings.write_text(json.dumps({'enabled':enabled}),encoding='utf-8');return self.view()
    def reading(self,position=0):
        if type(position) is not int or not 0<=position<=1000000:raise ValueError('Invalid reading position')
        if self.chunks:
            chunk=self.chunks[position%len(self.chunks)]
            return {'kind':'User-imported transcript excerpt','title':chunk['source'],'text':chunk['text'],'chunk':chunk['id'],'position':position,'total':len(self.chunks),'attribution_status':'User-supplied attribution; not independently authenticated'}
        if position%3==0:
            return {'kind':'Short attributed quotation · source linked','title':'Alan Watts · stillness and clarity','text':'“Muddy water is best cleared by leaving it alone.”','position':position,'total':len(catalogue()['chapters'])+1,'source_url':'https://www.azquotes.com/quote/357795','attribution_status':'Quotation as displayed by the linked quotation collection; complete original lecture not ingested.'}
        notes=catalogue()['chapters'];row=notes[position%len(notes)]
        return {'kind':'Original app study note · not a quotation','title':row['title'],'text':' '.join(row['paragraphs']),'position':position,'total':len(notes)}
    def ingest(self,body):
        title=body.get('title');text=body.get('text');rights=body.get('rights_confirmed')
        if rights is not True:raise ValueError('Confirm permission to use this transcript')
        if not isinstance(title,str) or not 1<=len(title)<=180:raise ValueError('Use a title of 1–180 characters')
        if not isinstance(text,str) or not 1<=len(text.encode('utf-8'))<=500000:raise ValueError('Use a UTF-8 text file up to 500000 bytes')
        raw=text.encode('utf-8');digest=hashlib.sha256(raw).hexdigest()
        if not any(r['sha256']==digest for r in self.records):
            if len(self.records)>=256 or sum(r['bytes'] for r in self.records)+len(raw)>16000000:raise ValueError('Private transcript library capacity reached')
            (self.folder/(digest+'.txt')).write_bytes(raw)
            self.records.append({'title':title,'sha256':digest,'bytes':len(raw),'rights_confirmed':True,'imported_at':time.time(),'verification':'User-supplied; attribution and transcription not independently verified'})
            temporary=self.path.with_suffix('.tmp');temporary.write_text(json.dumps(self.records,ensure_ascii=False),encoding='utf-8');temporary.replace(self.path);self.reload()
        return self.view()
    def process(self,body):
        if body.get('mode')=='ingest':
            chunk=self.by_id.get(body.get('chunk'))
            if chunk is None or body.get('text')!=chunk['text']:raise ValueError('Transcript chunk identity mismatch')
            return {'status':'COMPLETE','mode':'Authorised private transcript study','chunk':chunk['id'],'title':chunk['source'],'excerpt':chunk['text'],'external_delivery':False}
        return reflect({'lesson':'overview',**body},catalogue())
    def tick(self):
        if not self.enabled:return
        if self.pending:
            result=self.runtime.result(self.pending['job'])
            if result['status'] in ('queued','running'):return
            if result['status']=='complete':
                self.last={'receipt':result['receipt'],'at':time.time()};self.error=None
                if self.pending.get('chunk'):
                    with self.runtime.db() as db:db.execute('INSERT OR IGNORE INTO watts_chunks VALUES(?,?,?)',(self.pending['chunk'],result['receipt'],time.time()))
            else:self.error=result.get('error')
            self.pending=None
        now=time.monotonic()
        if now<self.next_at or not self.runtime.settings['learning'] or self.runtime.queue.qsize()>3:return
        self.next_at=now+30
        with self.runtime.db() as db:done={r[0] for r in db.execute('SELECT id FROM watts_chunks')}
        chunk=next((c for c in self.chunks if c['id'] not in done),None)
        if chunk:
            payload={'text':chunk['text'],'sections':['watts_study','virtue_text','reference'],'section_inputs':{'watts_study':{'mode':'ingest','chunk':chunk['id']}}}
        else:
            chapter=catalogue()['chapters'][self.cycles%len(catalogue()['chapters'])]
            payload={'text':chapter['paragraphs'][0].encode('utf-8')[:480].decode('utf-8',errors='ignore'),'sections':['watts_study','gnostic_four','inference'],'section_inputs':{'watts_study':{'lesson':chapter['id']},'gnostic_four':{'lesson':'truevirtue'}}}
        job=self.runtime.submit('pipeline',payload);self.pending={'job':job['id'],'chunk':chunk['id'] if chunk else None};self.cycles+=1
