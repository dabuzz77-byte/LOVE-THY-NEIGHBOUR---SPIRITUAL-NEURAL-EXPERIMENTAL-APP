"""Curated public primary references, with bounded direct-source checks."""
import hashlib,json,time
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Source redirected; review the canonical address')
def fetch():
    root=Path(__file__).resolve().parents[1];rows=json.loads((root/'references/virtue-primary-sources.json').read_text(encoding='utf-8'))
    index=int(time.time()//300)%len(rows)
    records=[]
    for i,row in enumerate(rows):
        record={'title':row['title'],'url':row['url'],'summary':row['summary'],'reading_status':'Curated primary-source summary; checked 12 November 2026'}
        if i==index:
            try:
                with build_opener(NoRedirect).open(Request(row['url'],headers={'User-Agent':'NeuralAppResearch/1.0'}),timeout=5) as response:
                    raw=response.read(262144);record['live_check']={'status':response.status,'checked_at':time.time(),'sample_sha256':hashlib.sha256(raw).hexdigest(),'sample_bytes':len(raw)}
            except Exception as error:record['live_check']={'status':'unavailable','checked_at':time.time(),'error':str(error)[:200]}
        records.append(record)
    return records
