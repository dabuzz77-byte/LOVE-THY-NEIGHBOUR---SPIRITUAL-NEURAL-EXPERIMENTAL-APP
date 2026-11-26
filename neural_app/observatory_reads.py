"""Bounded, cached public reads for the legacy catalogue; no global monkeypatch."""
import io
import time
import urllib.request
from urllib.parse import urlsplit

CACHE={}
ALLOWED={'wikipedia.org','www.wikipedia.org','gnu.org','www.gnu.org','archive.org','www.archive.org','nytimes.com','www.nytimes.com','rss.nytimes.com'}

class Response(io.BytesIO):
    def __init__(self,raw,status,headers,url):
        super().__init__(raw);self.status=status;self.headers=headers;self.url=url
    def getcode(self):return self.status
    def geturl(self):return self.url

def read(request,timeout=2,observations=None,**kwargs):
    url=request.full_url if isinstance(request,urllib.request.Request) else str(request)
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname not in ALLOWED:
        raise ValueError('Automatic catalogue reads use the reviewed public-source hosts')
    if isinstance(request,urllib.request.Request) and (request.data or request.get_method()!='GET'):
        raise ValueError('Catalogue source reads are GET-only')
    now=time.monotonic();row=CACHE.get(url);cached=bool(row and now-row['at']<(30 if row.get('error') else 300))
    if not cached:
        started=time.monotonic()
        try:
            with urllib.request.urlopen(request,timeout=min(2,float(timeout))) as response:
                raw=response.read(262145)
                if len(raw)>262144:raise ValueError('Public response exceeds 256 KiB')
                row={'at':now,'raw':raw,'status':response.status,'headers':response.headers,'url':response.geturl(),'elapsed_ms':(time.monotonic()-started)*1000}
        except Exception as error:
            row={'at':now,'error':type(error).__name__+': '+str(error),'elapsed_ms':(time.monotonic()-started)*1000}
        CACHE[url]=row
    observation={'url':url,'cached':cached,'age_seconds':round(now-row['at'],2),'retrieval_ms':round(row['elapsed_ms'],2),'error':row.get('error'),'timing_scope':'Legacy elapsed values include cache lookup on a reused response; retrieval_ms describes the actual recorded request.'}
    if observations is not None:observations.append(observation)
    if row.get('error'):raise OSError(row['error'])
    return Response(row['raw'],row['status'],row['headers'],row['url'])
