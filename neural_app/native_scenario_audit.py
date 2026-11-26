"""End-to-end native regression audit using isolated files and no model calls."""
import json,tempfile,time,types
from pathlib import Path

def evaluate_scenarios(data):
 from .grounded_reasoner import GroundedReasoner
 from .central_mind import CentralMind
 from .ambient_bus import AmbientBus
 start=time.monotonic();rows=[]
 folder=Path(data)/'native-audits';folder.mkdir(parents=True,exist_ok=True)
 def check(name,area,run,expected):
  try:
   actual=run();passed=bool(expected(actual));detail=str(actual)[:350]
  except Exception as e:passed=False;detail=type(e).__name__+': '+str(e)[:300]
  rows.append({'name':name,'area':area,'passed':passed,'observed':detail})
 with tempfile.TemporaryDirectory(dir=folder,ignore_cleanup_errors=True) as tmp:
  rt=types.SimpleNamespace(data=Path(tmp));mind=GroundedReasoner(rt,CentralMind(Path(tmp)),AmbientBus(),start=False)
  def ask(text):return mind.request({'text':text,'allow_model':False})
  check('common file-list phrasing','conversation',lambda:ask('show me my files'),lambda r:r.get('task_id') and mind.s['tasks'][-1]['operation']=='list_files')
  check('capability question','conversation',lambda:ask('what can you help me with?'),lambda r:'calculate' in r['answer'])
  check('greeting','conversation',lambda:ask('hello'),lambda r:'Hello' in r['answer'])
  check('typo asks instead of executing','conversation',lambda:ask('sttaus'),lambda r:'status' in r.get('suggestions',[]) and 'nothing was executed' in r['answer'])
  check('unknown wording acknowledged','conversation',lambda:ask('please build an unspecified thing'),lambda r:'do not yet understand' in r['answer'])
  check('question-mark payload preserved','work',lambda:ask('sort lines\nz?'),lambda r:r['answer']=='z?')
  check('line endings preserved','work',lambda:ask('unique lines\na?\na?\n'),lambda r:r['answer']=='a?\n')
  check('JSON Unicode roundtrip','work',lambda:ask('format json {"name":"éclair?"}'),lambda r:json.loads(r['answer'])=={'name':'éclair?'})
  ask('calculate 6 + 2')
  check('multiply numeric context','logic',lambda:ask('multiply that by 3'),lambda r:json.loads(r['answer'])['result']==24)
  check('subtract numeric context','logic',lambda:ask('subtract 4 from that'),lambda r:json.loads(r['answer'])['result']==20)
  check('divide numeric context','logic',lambda:ask('divide the result by 5'),lambda r:json.loads(r['answer'])['result']==4)
  ask('remember solar = hydrogen evidence')
  check('ranked memory retrieval','work',lambda:ask('search memory hydrogen'),lambda r:any(v['type']=='memory' for v in json.loads(r['answer'])))
  tools=mind.work_tools();tools.write({'path':'code/broken.py','text':'if True\n    print(1)\n'})
  check('syntax error is not success','logic',lambda:ask('check file code/broken.py'),lambda r:json.loads(r['answer'])['check']['passed'] is False)
  proposal=json.loads(ask('repair file code/broken.py')['answer'])
  check('repair remains a preview','work',lambda:tools.read({'path':'code/broken.py'})['text'],lambda t:'if True:' not in t)
  applied=json.loads(ask('apply preview '+proposal['id'])['answer'])
  check('apply verified and checkpointed','work',lambda:applied,lambda r:r['verified'] and bool(r['undo_id']))
  check('undo restores previous content','work',lambda:ask('undo change '+applied['undo_id']),lambda r:json.loads(r['answer'])['verified'])
  ask('plan:\ncalculate: 4 + 8\ncalculate: {{previous}} * 3')
  check('resume phrasing','coordinator',lambda:ask('resume plan'),lambda r:json.loads(r['answer'])['status']=='running')
  for _ in range(2):mind.workbench.last_tick=0;mind.workbench.tick()
  check('linked plan result','coordinator',lambda:mind.workbench.s['plans'][-1],lambda p:p['status']=='complete' and p['steps'][-1]['result']==36)
  ask('plan:\nread: absent.txt\ncalculate: 1 + 2');ask('continue plan');mind.workbench.last_tick=0;mind.workbench.tick()
  check('failed dependency stops next step','coordinator',lambda:mind.workbench.s['plans'][-1],lambda p:p['status']=='failed' and p['steps'][1]['status']=='pending')
  check('shell command requires explicit review','coordinator',lambda:ask('cmd: echo hello'),lambda r:r['proposal']['status']=='awaiting-confirmation' and not any(t['operation']=='shell' for t in mind.s['tasks']))
  for kind,name in [('graphics','test.svg'),('sound','test.wav'),('music','test.wav'),('video','test.html'),('midi','test.mid')]:
   check(kind+' export',kind if kind in ('graphics','video') else 'sound',lambda k=kind,n=name:ask('create '+k+' as '+n),lambda r:json.loads(r['answer'])['verified'])
  check('all native, no model calls','conversation',lambda:mind.s['model_calls'],lambda v:v==0)
  long=mind.reply('large output probe','Q?'*5000,{'model_used':False})
  check('long reply retrievable without loss','work',lambda:mind.output(long['output_id'])['text'],lambda t:t=='Q?'*5000)
  mind.close()
 groups={}
 for row in rows:
  group=groups.setdefault(row['area'],{'passed':0,'total':0});group['total']+=1;group['passed']+=int(row['passed'])
 priorities={k:1-v['passed']/v['total'] for k,v in groups.items() if v['passed']<v['total']}
 return {'time':time.time(),'passed':sum(r['passed'] for r in rows),'total':len(rows),'areas':groups,'cases':rows,'improvement_priorities':priorities,'seconds':round(time.monotonic()-start,3),'model_calls':0,'scope':'Isolated native workflow regression audit; no network connection, external shell execution or personal files','remaining_gaps':['General open-ended conversation still needs language assistance','Goal decomposition uses explicit typed steps','Script generation and deterministic repairs have finite supported templates','Public source agreement is not automatically fact verification','Media aesthetics and live FL Studio control are not established by these checks']}
