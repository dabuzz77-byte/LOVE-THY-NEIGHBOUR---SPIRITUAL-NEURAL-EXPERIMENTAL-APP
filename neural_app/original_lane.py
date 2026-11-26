"""Staggered original-section work on the existing compute lane, without painting."""
import json,math,time
from .runtime import ROOT

class OriginalLane:
 def __init__(self,host):
  self.host=host;self.cursor=0;self.next_at=0;self.path=host.runtime.data/'original-lane.json'
  self.enabled=json.loads(self.path.read_text()).get('enabled',True) if self.path.exists() else True
  self.initialized=set()
  self.panels=json.loads((ROOT/'original-panels.json').read_text(encoding='utf-8'))
  imported=ROOT/'references'/'desktop-java'/'panels.json'
  if imported.exists():
   additions=json.loads(imported.read_text(encoding='utf-8'));known={p['id'] for p in self.panels}
   self.panels.extend(p for p in additions if p['id'] not in known)
  self.retry_at={}
  self.rows={p['id']:{'name':p['name'],'status':'scheduled','cycles':0,'errors':0,'receipt':None,'milliseconds':0} for p in self.panels}
 def configure(self,enabled):
  if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
  self.enabled=enabled;self.path.write_text(json.dumps({'enabled':enabled}))
  for ident in self.rows:self.host.pause(ident,not enabled)
  return self.view()
 def view(self):
  item=self.host.python.loaded.get('observatory',{})
  controller=item.get('controller')
  internal=controller.shared_execution() if item.get('embedded_ready') else None
  return {'enabled':self.enabled,'total':len(self.rows),'visited':sum(v['cycles']>0 for v in self.rows.values()),'rows':self.rows,'internal_catalogue':internal,'policy':'One original section per shared slot. Existing native timers continue cooperatively. No hidden-page painting, automatic file import, external messaging or generated-code execution.'}
 def step(self,force=False):
  now=time.monotonic();rt=self.host.runtime
  if not self.enabled or (not force and now<self.next_at):return
  self.next_at=now+{'low':2,'medium':1,'high':.5}[rt.settings['pace']]
  ident=self.panels[self.cursor%len(self.panels)]['id'];self.cursor+=1;row=self.rows[ident]
  if ident in self.host.paused:row['status']='paused';return
  if now<self.retry_at.get(ident,0):return
  started=time.monotonic()
  try:
   host=self.host
   if ident in ('observatory','inference','neural-lab','carrier'):
    host.adapter(ident)
    if ident=='observatory':host.tick(ident,host.python.loaded[ident])
    value=host.invoke(ident,'/api/state')
   elif ident in ('ambient','injector'):value=host.invoke(ident,'/bridge/__telemetry')
   elif ident in ('genesis','matrix'):
    services=host.services_instance();value={'model':'ready for explicit question','shared_updates':rt.get_model().updates} if ident=='genesis' else services.snapshot()
   elif ident=='academy':value=rt.engine('academy',{})
   else:value=host.open(ident)
   if ident not in self.initialized and ident in host.python.loaded:
    c=host.python.loaded[ident]['controller']
    if ident=='neural-lab':c.running=True
    elif ident=='godmind':c.session.neural.running=True;c.session.optimizer.resume_engine()
    elif ident=='unified-neural':c.running=True
    elif ident=='core':c.engine.start()
    elif ident=='atelier':c.engine.running=True
    self.initialized.add(ident)
   # Only bounded numerical state feeds shared reconstruction; no UI trees,
   # account strings, file paths or credentials enter this background receipt.
   numbers={}
   def visit(v,path='',depth=0):
    if depth>6 or len(numbers)>=192:return
    if isinstance(v,(int,float)) and math.isfinite(v):numbers[path]=v
    elif isinstance(v,dict):
     for k,x in v.items():
      if str(k) in ('ui','messages','clipboard') or any(s in str(k).lower() for s in ('secret','password','token','credential','key')):continue
      visit(x,path+'.'+str(k),depth+1)
    elif isinstance(v,(list,tuple)):
     for i,x in enumerate(v[:32]):visit(x,path+'.'+str(i),depth+1)
   failure=value.get('failure') or value.get('error') if isinstance(value,dict) else None
   if failure:raise ValueError(str(failure)[:300])
   visit(value.get('engine_fields',value) if isinstance(value,dict) else value)
   receipt=rt.component_result(ident,{'source':'original cooperative lane'}, {'measurements':numbers,'sample':row['cycles']+1,'status':'COMPLETE'})
   self.retry_at.pop(ident,None)
   row.update(consecutive_errors=0,status='active',cycles=row['cycles']+1,receipt=receipt,milliseconds=round((time.monotonic()-started)*1000,2),last_error=None)
  except Exception as e:
   failures=row.get('consecutive_errors',0)+1
   delay=min(120,2**min(failures,7))
   self.retry_at[ident]=time.monotonic()+delay
   row.update(status='error',errors=row['errors']+1,consecutive_errors=failures,retry_seconds=delay,last_error=type(e).__name__+': '+str(e)[:300])
