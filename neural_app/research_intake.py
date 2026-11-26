"""Bounded public research metadata intake; external text is data, never code."""
import hashlib
import json
import threading
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

TOPICS = [
    ('virtue_primary','Primary sources: dignity, children, welfare and civilian protection'),
    ('energy_services','distributed energy storage AC efficiency resilient community microgrids'),
    ('isp_mesh','community networks offline low bandwidth mesh resilience accessibility'),
    ('gnostic_four','Apocryphon John Gospel Mary Thomas Dialogue Savior ethics'),
    ('discipline','Bushido Bagua embodied practice ethics'),
    ('iching','I Ching Book Changes Legge interpretation'),
    ('watts_study','Alan Watts philosophy self language interdependence'),
    ('wooden_cup', 'humility intrinsic value Christian ethics care dignity'),
    ('matter_spirit', 'antimatter philosophy religion shadow ethics Kabbalah fiction'),
    ('inference', 'distributed inference routing mesh networks'),
    ('learning', 'neural network online learning model evaluation'),
    ('signals', 'signal processing Fourier ternary computing'),
    ('care', 'animal welfare vulnerability resource allocation'),
    ('systems', 'distributed systems bounded scheduling resource efficiency'),
    ('space', 'hydrogen stellar physics biosphere'),
    ('ethics', 'comparative religion compassion moral development'),
    ('theology_unity', 'Islam Christianity divine unity Trinity revelation comparative theology'),
    ('theology_light', 'Islam Christianity Gnosticism divine light illumination'),
    ('theology_care', 'Islam Christianity mercy animal welfare vulnerable compassion'),
    ('theology_gnosis', 'Gnosticism Christianity Islam faith knowledge interreligious dialogue'),
    ('design_tesla', 'Nikola Tesla alternating current induction motor resonant transformer'),
    ('design_fuller', 'Buckminster Fuller geodesic tensegrity resource efficiency'),
    ('design_fresco', 'Jacque Fresco Venus Project resource based economy sustainable cities'),
    ('falun_plight', 'Falun Gong persecution human rights worldwide'),
]

def parse_news(raw):
    if len(raw)>262144 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('Unsupported or oversized news feed')
    rows=[]
    for item in ET.fromstring(raw).findall('./channel/item')[:3]:
        url=item.findtext('link','')
        if not url.startswith('https://news.google.com/'):continue
        rows.append({'title':item.findtext('title','')[:240],'url':url[:2000],
                     'published':item.findtext('pubDate','')[:100],'publisher':item.findtext('source','')[:120],
                     'reading_status':'Headline metadata; article not automatically read or verified.'})
    return rows

def fetch_plight():
    url='https://news.google.com/rss/search?'+urlencode({'q':'"Falun Gong" persecution human rights','hl':'en-GB','gl':'GB','ceid':'GB:en'})
    with build_opener(NoRedirect).open(Request(url,headers={'User-Agent':'NeuralAppResearch/1.0'}),timeout=8) as response:
        return parse_news(response.read(262145))

def research_input(topic,records):
    full='\n'.join(r['title'] for r in records)
    projection=full.encode('utf-8')[:480].decode('utf-8',errors='ignore')
    return {'text':projection or topic,'sections':['suite','unified','platform_alignment','karmic_welfare','virtue_text','reference','inference'],
            'research':{'topic':topic,'records':records,'source_digest':hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest(),
                        'projection_bytes':len(projection.encode()),'full_title_bytes':len(full.encode())}}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Research provider redirect refused; update its configured endpoint')


def fetch_metadata(query, abstracts_only=False):
    params={'query': query, 'rows': 3, 'select': 'DOI,title,URL,published,abstract'}
    if abstracts_only:params['filter']='has-abstract:true'
    url = 'https://api.crossref.org/works?' + urlencode(params)
    request = Request(url, headers={'User-Agent': 'NeuralAppResearch/1.0 (public bibliographic metadata)', 'Accept': 'application/json'})
    with build_opener(NoRedirect).open(request, timeout=8) as response:
        raw = response.read(262145)
    if len(raw) > 262144: raise ValueError('Research response exceeds 256 KiB')
    data = json.loads(raw)
    records = []
    for row in data.get('message', {}).get('items', [])[:3]:
        title = row.get('title', [])
        if isinstance(title, list) and title and isinstance(title[0], str):
            record={'title': title[0][:240], 'doi': str(row.get('DOI', ''))[:200], 'url': str(row.get('URL', ''))[:500], 'published':row.get('published',{})}
            abstract=row.get('abstract','')
            if isinstance(abstract,str) and abstract:
                parser=AbstractText();parser.feed(abstract[:20000]);record['abstract']=parser.text()[:4000]
                record['abstract_truncated']=len(abstract)>20000 or len(parser.text())>4000
            record['reading_status']='Publisher-deposited abstract, not full paper or independent verification.' if record.get('abstract') else 'Bibliographic metadata only; no abstract or paper read.'
            records.append(record)
    if not abstracts_only and records and not any(r.get('abstract') for r in records):
        try:
            substantive=fetch_metadata(query,True)
            if substantive:return substantive
        except (OSError,ValueError):pass  # Preserve successful metadata if the abstract-specific request fails.
    return records

class AbstractText(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.hidden+=1
        elif tag in ('p','jats:p','sec','jats:sec','br'):self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.hidden=max(0,self.hidden-1)
        elif tag in ('p','jats:p','sec','jats:sec'):self.parts.append(' ')
    def handle_data(self,text):
        if not self.hidden:self.parts.append(text)
    def text(self):return ' '.join(''.join(self.parts).split())

def review_records(query,records):
    from .evidence_workbench import prepare,analyse
    sources=[]
    for i,row in enumerate(records[:16]):
        passage=row.get('abstract') or row.get('summary')
        if not passage:continue  # A headline is not evidence for the article's claims.
        source={'id':'R'+str(i+1),'title':row['title'],'text':passage[:4000], 'url':row.get('url',''),'date':str(row.get('published','undated'))[:80]}
        sources.append(source)
    if not sources:return {'status':'metadata-only','passages':[],'source_count':0,'model_calls':0,'scope':'No substantive abstract or supplied source summary was available. No conclusion was inferred from titles.'}
    report=analyse(prepare({'question':'What evidence is reported about '+query[:800]+'?','sources':sources}))
    report['source_count']=len(sources);report['source_scope']='Publisher abstracts or explicitly curated summaries; not full-paper review. Check original methods and applicability.'
    report['truncated_source_ids']=['R'+str(i+1) for i,row in enumerate(records[:16]) if row.get('abstract_truncated')]
    return report


class ResearchIntake:
    def __init__(self, runtime):
        self.runtime = runtime; self.path = runtime.data/'research-intake.json'
        self.lock = threading.RLock(); self.halt = threading.Event(); self.enabled = False
        self.index = 0; self.topics = {}; self.pending = None; self.thread = None
        if self.path.exists():
            try:self.enabled = json.loads(self.path.read_text(encoding='utf-8')).get('enabled') is True
            except (OSError, ValueError):pass

    def configure(self, enabled):
        if type(enabled) is not bool: raise ValueError('Enabled must be boolean')
        with self.lock:
            self.enabled = enabled
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps({'enabled': enabled}), encoding='utf-8'); temporary.replace(self.path)
        return self.view()

    def start(self):
        self.thread = threading.Thread(target=self.loop, name='neural-public-research', daemon=True); self.thread.start()

    def cycle(self):
        # Never acquire the runtime lock while holding the research lock.
        with self.lock:
            if not self.enabled:return
            pending=self.pending.copy() if self.pending else None
            if not pending:topic,query=TOPICS[self.index%len(TOPICS)];self.index+=1
        if pending:
            try:job=self.runtime.result(pending['job'])
            except ValueError:job={'status':'error','error':'Research job expired; next cycle will retry'}
            if job['status'] in ('queued','running'):return
            with self.lock:
                self.topics[pending['topic']].update(processing=job['status'],receipt=job.get('receipt'),error=job.get('error'));self.pending=None
            return
        try:
            if topic=='virtue_primary':
                from .primary_research import fetch
                records=fetch()
            else:records=fetch_plight() if topic=='falun_plight' else fetch_metadata(query)
            digest=hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()
            with self.lock:
                if not self.enabled:return
                previous=self.topics.get(topic)
                if previous and previous.get('digest')==digest:previous['checked_at']=time.time();return
                record={'query':query,'checked_at':time.time(),'records':records,'digest':digest,'source':'Curated primary summaries and bounded source checks' if topic=='virtue_primary' else 'Google News headline metadata' if topic=='falun_plight' else 'Crossref public bibliographic metadata','processing':'empty' if not records else 'ready'}
                self.topics[topic]=record
            if not records:return
            evidence_review=review_records(query,records)
            with self.lock:record['evidence_review']=evidence_review
            full='\n'.join(r['title'] for r in records);projection=full.encode('utf-8')[:480].decode('utf-8',errors='ignore')
            if topic in ('gnostic_four','discipline','iching','watts_study','wooden_cup','matter_spirit'):
                lesson={'wooden_cup':'value','matter_spirit':'study','gnostic_four':'combined','discipline':'combined'}.get(topic,'overview')
                body=research_input(topic,records);body['sections'].append(topic);body['section_inputs']={topic:{'lesson':lesson}}
            elif topic.startswith('theology_'):body={'text':projection,'topic':topic,'records':records}
            elif topic.startswith('design_') or topic in ('falun_plight','virtue_primary'):body=research_input(topic,records)
            else:body={'text':projection,'sections':[],'research':{'topic':topic,'source_digest':digest,'projection_bytes':len(projection.encode()),'full_title_bytes':len(full.encode())}}
            body.setdefault('research',{})['evidence_review']=evidence_review
            job=self.runtime.submit('theology' if topic.startswith('theology_') else 'pipeline',body)
            with self.lock:self.pending={'topic':topic,'job':job['id']};record.update(processing='queued',job=job['id'])
        except Exception as error:
            with self.lock:self.topics[topic]={'query':query,'checked_at':time.time(),'processing':'error','error':str(error)[:300]}

    def loop(self):
        # One shared request every 30 seconds at most; topic groups reuse metadata.
        while not self.halt.wait(5):
            if self.enabled:
                self.cycle()
                if self.halt.wait(25):break

    def view(self):
        with self.lock:
            complete = [v for v in self.topics.values() if v.get('processing') == 'complete']
            return {'enabled': self.enabled, 'provider': 'Crossref / Google News public metadata', 'interval_seconds': 30,
                    'queries': dict(TOPICS), 'topics': json.loads(json.dumps(self.topics)),
                    'completed_topics': len(complete), 'pending': self.pending.copy() if self.pending else None,
                    'scope': 'Public research metadata search, not validation of the papers or proof of theological claims. Generic topic queries contain no private source accounts. Pipeline receipts are available to existing authenticated result subscribers; no new external recipient is configured.'}

    def close(self):
        self.halt.set()
        if self.thread:self.thread.join(10)
