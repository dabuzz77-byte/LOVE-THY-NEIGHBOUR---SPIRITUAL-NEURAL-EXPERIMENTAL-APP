"""Four public-domain texts, resumable shared learning and inspectable policy bits."""
import hashlib,json,math,re,time
from pathlib import Path
from . import translation as btq
from .matter_spirit import process as reflect

ROOT=Path(__file__).resolve().parents[1]
CHECKS=('truthful','non_harm','consent','privacy','fairness','repairable','reviewed')

def catalogue():
    return json.loads((ROOT/'references/four-voices.json').read_text(encoding='utf-8'))

def scalar(value,name,maximum=1):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=maximum:
        raise ValueError(name+' is outside its finite range')
    return float(value)

def presets():
    def candidate(ident,label,benefit,need,cost,**overrides):
        return {'id':ident,'label':label,'benefit':benefit,'need':need,'confidence':.8,'cost':cost,
                'checks':{**dict.fromkeys(CHECKS,True),**overrides}}
    return {
      'knowledge':{'title':'Knowledge access and respectful outreach','candidates':[
        candidate('forced','Impressive reach through unsolicited device takeover',1,1,1,consent=False,privacy=False,non_harm=False),
        candidate('offline','Opt-in offline library for low-bandwidth readers',.85,1,2),
        candidate('display','Prestige display with little practical access',.2,.1,2)]},
      'resources':{'title':'Community resource priorities','candidates':[
        candidate('vanity','Publicity-first project hiding its costs',.95,.1,2,truthful=False),
        candidate('repair','Repair a shared resource with affected users',.8,.95,2),
        candidate('listen','Listen and document needs before spending',.55,.9,1)]},
      'work':{'title':'Fair work and accountable systems','candidates':[
        candidate('extract','Reward output while concealing worker harm',1,.8,1,non_harm=False,fairness=False),
        candidate('fair','Accessible process with fair terms and appeal',.8,.9,2),
        candidate('unknown','Promising proposal with unreviewed effects',.95,1,1,reviewed=None)]}}

def decide(body):
    rows=body.get('candidates',presets()[body.get('scenario','knowledge')]['candidates'] if body.get('scenario','knowledge') in presets() else None)
    if not isinstance(rows,list) or not 1<=len(rows)<=16:raise ValueError('Use 1–16 proposed actions or a supported scenario')
    budget=scalar(body.get('budget',3),'budget',10000);ids=set();evaluated=[]
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Actions must be objects')
        ident=row.get('id');label=row.get('label',ident)
        if not isinstance(ident,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,40}',ident) or ident in ids:raise ValueError('Use unique short action identifiers')
        if not isinstance(label,str) or len(label)>240:raise ValueError('Action label too long')
        ids.add(ident);checks=row.get('checks',{})
        if not isinstance(checks,dict) or set(checks)-set(CHECKS):raise ValueError('Unsupported policy check')
        for value in checks.values():
            if value is not None and type(value) is not bool:raise ValueError('Checks must be true, false or unknown')
        bits=''.join('1' if checks.get(k) is True else '0' for k in CHECKS)
        known=''.join('1' if type(checks.get(k)) is bool else '0' for k in CHECKS)
        benefit=scalar(row.get('benefit',0),'benefit');need=scalar(row.get('need',0),'need')
        confidence=scalar(row.get('confidence',0),'confidence');cost=scalar(row.get('cost',0),'cost',10000)
        reasons=[k+(': unknown' if checks.get(k) is None else ': failed') for k in CHECKS if checks.get(k) is not True]
        if cost>budget:reasons.append('Outside declared budget')
        if benefit<=0:reasons.append('No positive benefit declared')
        if confidence<.5:reasons.append('Impact review confidence below 0.5')
        score=(.6*benefit+.4*need)*confidence
        evaluated.append({'id':ident,'label':label,'check_bits':bits,'known_bits':known,'eligible':not reasons,
            'reasons':reasons,'benefit':benefit,'need':need,'confidence':confidence,'cost':cost,'score':round(score,8)})
    eligible=[x for x in evaluated if x['eligible']]
    selected=max(eligible,key=lambda x:(x['score'],-x['cost'],x['id']))['id'] if eligible else None
    bits=''.join('1' if r['id']==selected else '0' for r in evaluated)
    counterfactual=[]
    for i,row in enumerate(evaluated):
        # Actual single-gate perturbation, holding all other inputs constant.
        for j,key in enumerate(CHECKS):
            flags=list(row['check_bits']);flags[j]='0' if flags[j]=='1' else '1'
            possible=''.join(flags)=='1'*len(CHECKS) and row['cost']<=budget and row['benefit']>0 and row['confidence']>=.5
            choices=[r for n,r in enumerate(evaluated) if (possible if n==i else r['eligible'])]
            alternative=max(choices,key=lambda x:(x['score'],-x['cost'],x['id']))['id'] if choices else None
            if alternative!=selected:counterfactual.append({'action':row['id'],'check_flipped':key,'selection_before':selected,'selection_after':alternative})
    packet=btq.encode(bits.encode('ascii'))
    return {'status':'COMPLETE' if selected else 'NEEDS_REVIEW','checks':list(CHECKS),'actions':evaluated,
        'selected':selected,'selection_bits':bits,'eligibility_bits':''.join('1' if r['eligible'] else '0' for r in evaluated),
        'budget':budget,'counterfactual_changes':counterfactual,'decision_transport':packet,
        'round_trip':btq.decode(packet).decode('ascii')==bits,
        'rule':'All seven checks pass AND positive benefit AND reviewed impact confidence ≥ 0.5 AND affordable; then rank by declared benefit/need. Prestige is not a feature.',
        'scope':'Inspectable ethical proposal filter using supplied assessments; not divine judgment or independent verification. No external action is executed.'}

class FourTexts:
    def __init__(self,runtime):
        self.runtime=runtime;self.folder=ROOT/'references/four-texts'
        self.manifest=json.loads((self.folder/'manifest.json').read_text(encoding='utf-8'));self.texts={};self.chunks=[]
        extra=ROOT/'references/discipline/sources.json'
        if extra.exists():
            book=json.loads(extra.read_text(encoding='utf-8'))['bushido']
            self.manifest['records'].append({'id':'bushido','title':book['title'],'url':book['url'],'translator':book['author'],'file':'../discipline/bushido-nitobe.txt','sha256':book['sha256'],'bytes':(ROOT/'references/discipline/bushido-nitobe.txt').stat().st_size,'license':book['license'],'reading_scope':'Additional historical study book; separate from the four Gospel texts.'})
        book_path=ROOT/'references/iching/legge-complete.txt'
        if book_path.exists():
            book=json.loads((ROOT/'references/iching/source.json').read_text(encoding='utf-8'))
            self.manifest['records'].append({'id':'iching','title':'I Ching · complete selected Legge translation','url':book['url'],'translator':'James Legge','file':'../iching/legge-complete.txt','sha256':hashlib.sha256(book_path.read_bytes()).hexdigest(),'bytes':book_path.stat().st_size,'license':'Public-domain translation','reading_scope':'Complete local text, appendices and notes; plate images are not bundled.'})
        for source in self.manifest['records']:
            raw=(self.folder/source['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('Source digest mismatch: '+source['id'])
            text=raw.decode('utf-8');self.texts[source['id']]=text;current='';offset=0
            for char in text:
                if len((current+char).encode('utf-8'))>480:
                    self.chunks.append(self.chunk(source,current,offset));offset+=len(current);current=''
                current+=char
            if current:self.chunks.append(self.chunk(source,current,offset))
        self.by_id={x['id']:x for x in self.chunks};self.pending=None;self.next_at=0;self.error=None
        self.settings=runtime.data/'four-texts-settings.json';self.enabled=self.settings.exists() and json.loads(self.settings.read_text(encoding='utf-8')).get('enabled') is True
        with runtime.db() as db:db.execute('CREATE TABLE IF NOT EXISTS four_text_chunks(id TEXT PRIMARY KEY,receipt INTEGER,stamp REAL)')
    @staticmethod
    def chunk(source,text,offset):
        return {'id':source['id']+':'+str(offset)+':'+source['sha256'][:12], 'source':source['id'],
                'offset':offset,'text':text,'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest()}
    def view(self):
        with self.runtime.db() as db:processed={r[0] for r in db.execute('SELECT id FROM four_text_chunks')}
        return {'enabled':self.enabled,'total_chunks':len(self.chunks),'processed_chunks':sum(c['id'] in processed for c in self.chunks),
            'pending':self.pending,'error':self.error,'sources':self.manifest['records'],'interval_seconds':2,
            'scope':'Four local public-domain English editions plus the separately identified Nitobe and Legge study books. Every UTF-8 character is included in a checked ≤480-byte chunk. Shared numerical learning; LLM base weights unchanged.'}
    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.enabled=enabled;self.settings.write_text(json.dumps({'enabled':enabled}),encoding='utf-8');return self.view()
    def source(self,ident,query=''):
        if ident not in self.texts:raise ValueError('Unknown source')
        if not isinstance(query,str) or len(query)>160:raise ValueError('Search query too long')
        text=self.texts[ident];hits=[]
        if query:
            for match in re.finditer(re.escape(query),text,re.I):
                hits.append({'offset':match.start(),'excerpt':text[max(0,match.start()-80):match.end()+170]})
                if len(hits)>=20:break
        return {'id':ident,'text':text,'hits':hits,'source':next(s for s in self.manifest['records'] if s['id']==ident)}
    def input(self,chunk):
        return {'text':chunk['text'],'sections':['gnostic_four','virtue_text','reference','inference'],
            'section_inputs':{'gnostic_four':{'mode':'ingest','chunk':chunk['id']}}}
    def tick(self):
        if not self.enabled or time.monotonic()<self.next_at:return
        self.next_at=time.monotonic()+2
        if self.pending:
            value=self.runtime.result(self.pending['job'])
            if value['status'] in ('queued','running'):return
            if value['status']=='complete':
                with self.runtime.db() as db:db.execute('INSERT OR IGNORE INTO four_text_chunks VALUES(?,?,?)',(self.pending['chunk'],value['receipt'],time.time()))
                self.error=None
            else:self.error=value.get('error','Processing failed');self.next_at=time.monotonic()+30
            self.pending=None;return
        with self.runtime.db() as db:done={r[0] for r in db.execute('SELECT id FROM four_text_chunks')}
        chunk=next((c for c in self.chunks if c['id'] not in done),None)
        if chunk and self.runtime.queue.qsize()<8 and self.runtime.settings['learning']:
            job=self.runtime.submit('pipeline',self.input(chunk));self.pending={'job':job['id'],'chunk':chunk['id']}
    def process(self,body):
        if body.get('mode')=='ingest':
            chunk=self.by_id.get(body.get('chunk'))
            if chunk is None or body.get('text')!=chunk['text']:raise ValueError('Chunk text/identity mismatch')
            return {'status':'COMPLETE','source':chunk['source'],'chunk':chunk['id'],'source_excerpt':chunk['text'],
                'sha256':chunk['sha256'],'utf8_bytes':len(chunk['text'].encode('utf-8')),'characters':len(chunk['text']),
                'mode':'Public-domain source reconstruction, not a truth label'}
        value=reflect({'lesson':'combined',**body},catalogue());value['decision']=decide(body)
        value['model']='Four-text reflection and explicit good-action policy gates'
        value['scope']='Source study, declared ethical criteria, local decision bits and shared numerical learning.'
        return value
