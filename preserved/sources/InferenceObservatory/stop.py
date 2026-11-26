import json,pathlib,urllib.request,os,signal
root=pathlib.Path(__file__).resolve().parent
runtime=json.loads((root/'data/runtime.json').read_text())
url='http://127.0.0.1:'+str(runtime['port'])
with urllib.request.urlopen(url+'/api/session',timeout=3) as r:key=json.load(r)['key']
req=urllib.request.Request(url+'/api/state',headers={'X-Observatory-Key':key})
with urllib.request.urlopen(req,timeout=3) as r:state=json.load(r)
if state['pid']!=runtime['pid']:raise SystemExit('Runtime identity mismatch; no process stopped')
os.kill(runtime['pid'],signal.SIGTERM)
