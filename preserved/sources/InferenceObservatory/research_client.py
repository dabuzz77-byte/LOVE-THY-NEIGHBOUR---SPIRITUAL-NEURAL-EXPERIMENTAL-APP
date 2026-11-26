"""Local journal helper for the recurring, user-authorized Google AI Mode browser task."""
import argparse,json,pathlib,urllib.request
BASE='http://127.0.0.1:7865'
def request(path,data=None):
 with urllib.request.urlopen(BASE+'/api/session',timeout=5) as r:key=json.load(r)['key']
 req=urllib.request.Request(BASE+'/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'X-Observatory-Key':key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--next',action='store_true');p.add_argument('--ingest');p.add_argument('--status');p.add_argument('--retry');x=p.parse_args()
 if x.next:result=request('research/next')
 elif x.ingest:result=request('research/ingest',json.loads(pathlib.Path(x.ingest).read_text(encoding='utf-8-sig')))
 elif x.status:result=request('research/result?id='+x.status)
 elif x.retry:result=request('research/retry',{'id':x.retry})
 else:p.error('Choose --next, --ingest capture.json, --status ID or --retry ID')
 print(json.dumps(result,ensure_ascii=True,indent=2))
