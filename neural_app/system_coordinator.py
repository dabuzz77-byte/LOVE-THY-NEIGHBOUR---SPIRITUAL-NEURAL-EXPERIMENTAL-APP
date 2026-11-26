"""Shared typed coordinator for current-account PC, files, desktop and public web.

Reads produce receipts. Mutations produce reviewed proposals, never self-approval.
"""
import hashlib,json,os,re,tempfile,time,uuid
from pathlib import Path

TOOLS={
 'system_snapshot':'OS, CPU and memory measurements',
 'processes':'Bounded running-process inventory',
 'disks':'Mounted-disk capacity and free space',
 'network':'Adapter status and aggregate traffic counters',
 'workspace_list':'List app workspace files',
 'workspace_read':'Read a named workspace file',
 'public_search':'Public scholarly search with source links',
 'public_page':'Read one public HTTPS text page',
 'desktop_windows':'List selectable desktop windows',
 'desktop_read':'Inspect the selected window’s accessible controls',
 'desktop_select':'Select a previously enumerated window',
 'desktop_action':'Propose typing, clicking, focusing or scrolling a selected control',
 'command':'Propose a current-account PowerShell or cmd command',
 'file_write':'Propose a text-file write with source-version protection'}
WRITES={'desktop_action','command','file_write'}

class SystemCoordinator:
 def __init__(self,reasoner):
  self.r=reasoner;self.state=reasoner.s.setdefault('system_coordinator',{'receipts':[],'windows':[],'selected':None})
 def view(self):return {'tools':TOOLS,'selected_window':self.state.get('selected'),'recent':self.state['receipts'][-8:],'scope':'Current OS account, selected app controls and public HTTPS sources. Remote accounts and paid services need their own configured connections.'}
 def desktop(self):
  from desktop_control import DesktopControl
  from .runtime import ROOT
  return DesktopControl(ROOT)
 def propose(self,tool,args):
  if tool=='command':
   command=args.get('command');shell=args.get('shell','powershell')
   if not isinstance(command,str) or not command.strip() or len(command)>12000 or shell not in ('powershell','cmd'):raise ValueError('Provide a command and powershell or cmd interpreter')
   operation='shell';payload={**args,'shell':shell}
  elif tool=='desktop_action':
   target=self.state.get('selected')
   if not target:raise ValueError('List and select a desktop window first')
   action=args.get('action');control=args.get('control')
   if action not in ('click','set_text','invoke','focus','scroll') or not isinstance(control,str) or not control or len(str(args.get('text','')))>12000:raise ValueError('Choose a selected control and a supported desktop action')
   operation='desktop';payload={**args,'target':target}
  else:
   path=Path(str(args.get('path',''))).expanduser();text=args.get('text')
   if not path.is_absolute():path=self.r.work_tools().path(str(path))
   if str(path).startswith(('\\\\','//')) or not isinstance(text,str) or len(text.encode())>250000:raise ValueError('Choose a local text-file path and contents below 250 KB')
   path=path.resolve()
   if path.exists() and not path.is_file():raise ValueError('Choose a file, not a directory')
   raw=path.read_bytes() if path.exists() else None
   if raw is not None and len(raw)>250000:raise ValueError('Existing file exceeds edit-preview budget')
   operation='coordinator_file';payload={'path':str(path),'text':text,'expected_sha256':hashlib.sha256(raw).hexdigest() if raw is not None else None}
  proposal={'id':uuid.uuid4().hex,'operation':operation,'text':json.dumps(payload,ensure_ascii=False),'source':'system-coordinator','status':'awaiting-confirmation'}
  self.r.s['pending_proposals']={**dict(list(self.r.s['pending_proposals'].items())[-15:]),proposal['id']:proposal}
  return {'answer':'Review the proposed '+tool.replace('_',' ')+' action and its exact target before running it.','proposal':proposal,'executed':False}
 def read(self,tool,args):
  if tool=='workspace_list':return self.r.work_tools().view()
  if tool=='workspace_read':return self.r.work_tools().read(args)
  if tool=='public_page':
   from .reviewed_web import read_page
   return read_page(args.get('url',''))
  if tool=='public_search':
   from .research_intake import fetch_metadata
   query=args.get('query','')
   if not isinstance(query,str) or not query.strip() or len(query)>300:raise ValueError('Provide a public search query up to 300 characters')
   return {'query':query,'sources':fetch_metadata(query),'scope':'Live public scholarly metadata search; results are not full-page readings'}
  if tool=='desktop_windows':
   result=self.desktop().windows();self.state['windows']=result.get('windows',[])[:100];return result
  if tool=='desktop_select':
   target=next((w for w in self.state['windows'] if str(w['handle'])==str(args.get('handle'))),None)
   if not target:raise ValueError('Select a handle from a fresh desktop-window list')
   self.state['selected']=target;return {'selected':target,'action_executed':False}
  if tool=='desktop_read':
   if not self.state.get('selected'):raise ValueError('Select a desktop window first')
   return self.desktop().read(self.state['selected'])
  import psutil
  if tool=='system_snapshot':
   import platform
   memory=psutil.virtual_memory()
   return {'os':platform.system(),'cpu_percent':psutil.cpu_percent(interval=None),'logical_cpus':os.cpu_count(),'memory_total_bytes':memory.total,'memory_available_bytes':memory.available,'memory_percent':memory.percent,'scope':'OS-reported measurements; instantaneous CPU percentage may need a later comparison'}
  if tool=='processes':
   rows=[]
   for process in psutil.process_iter(['pid','name','memory_info']):
    try:info=process.info;rows.append({'pid':info['pid'],'name':info['name'],'memory_bytes':info['memory_info'].rss if info['memory_info'] else None})
    except (psutil.Error,OSError):continue
   rows.sort(key=lambda r:r['memory_bytes'] or 0,reverse=True);return {'total_observed':len(rows),'processes':rows[:100],'scope':'Current-account process names and resident memory; no command-line secrets collected'}
  if tool=='disks':
   rows=[]
   for partition in psutil.disk_partitions(all=False):
    try:usage=psutil.disk_usage(partition.mountpoint);rows.append({'mountpoint':partition.mountpoint,'total_bytes':usage.total,'free_bytes':usage.free,'percent_used':usage.percent})
    except OSError:continue
   return {'disks':rows}
  if tool=='network':
   counters=psutil.net_io_counters();return {'adapters':{name:{'up':row.isup,'speed_mbps':row.speed,'mtu':row.mtu} for name,row in psutil.net_if_stats().items()},'traffic':{'sent_bytes':counters.bytes_sent,'received_bytes':counters.bytes_recv} if counters else None,'scope':'Local interface counters, not packet contents or remote access'}
  raise ValueError('Unknown coordinator tool')
 def run(self,body):
  steps=body.get('steps') if isinstance(body,dict) else None
  if not isinstance(steps,list) or not 1<=len(steps)<=8:raise ValueError('Provide 1 to 8 typed coordinator steps')
  results=[]
  for index,step in enumerate(steps):
   if not isinstance(step,dict) or step.get('tool') not in TOOLS or not isinstance(step.get('args',{}),dict):raise ValueError('Each step needs a registered tool and an args object')
   tool=step['tool'];args=step.get('args',{})
   if tool in WRITES:
    proposal=self.propose(tool,args);return {**proposal,'completed_reads':results,'pending_step':index+1,'remaining_steps':steps[index+1:],'scope':'Remaining steps have not run; follow up after the reviewed action completes'}
   started=time.monotonic()
   try:value=self.read(tool,args);status='observed';error=None
   except Exception as exc:value=None;status='failed';error=str(exc)[:300]
   receipt={'id':uuid.uuid4().hex,'tool':tool,'status':status,'elapsed_ms':round((time.monotonic()-started)*1000,2),'time':time.time(),'error':error};self.state['receipts']=(self.state['receipts']+[receipt])[-32:];results.append({**receipt,'result':value})
   self.r.bus.publish({'origin':'system-coordinator','target':'all','kind':'stage-output','payload':{**receipt,'result_sha256':hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest(),'provenance':'actual coordinator tool outcome','stochastic':False}})
   if error:return {'answer':'The '+tool.replace('_',' ')+' step failed: '+error,'status':'failed','results':results,'model_calls':0}
  lines=['Completed '+str(len(results))+' coordinator step'+('s' if len(results)!=1 else '')+'.']
  for row in results:
   value=row['result'];lines.append('\n**'+row['tool'].replace('_',' ').title()+'**')
   if row['tool']=='public_page':lines.append('Source: ['+value['url']+']('+value['url']+')\n\n'+value['text'][:6000])
   elif row['tool']=='public_search':lines.extend('- ['+v.get('title','Source')+']('+v.get('url',v.get('URL',''))+')' for v in value['sources'])
   else:lines.append('```json\n'+json.dumps(value,ensure_ascii=False,indent=2,default=str)[:10000]+'\n```')
  return {'answer':'\n'.join(lines),'status':'complete','results':results,'model_calls':0,'source':'actual coordinator tool receipts'}
 def handle(self,text):
  value=text.strip();key=value.casefold().rstrip('?.!')
  if key in ('coordinator capabilities','system coordinator','system coordinator capabilities'):return {'answer':'Available coordinator tools:\n\n'+'\n'.join('- **'+k.replace('_',' ')+':** '+v for k,v in TOOLS.items()),**self.view()}
  if value.casefold().startswith('coordinate:'):return self.run(json.loads(value.split(':',1)[1]))
  exact={'system overview':'system_snapshot','system status':'system_snapshot','show system status':'system_snapshot','show running processes':'processes','list processes':'processes','what is using memory':'processes','disk usage':'disks','show disk space':'disks','network status':'network','desktop windows':'desktop_windows','list desktop windows':'desktop_windows','inspect selected window':'desktop_read'}
  if key in exact:return self.run({'steps':[{'tool':exact[key]}]})
  if re.search(r'\b(inspect|check|show|report)\b',key) and re.search(r'\b(cpu|memory|ram)\b',key):return self.run({'steps':[{'tool':'system_snapshot'}]})
  if re.search(r'\b(inspect|check|show|list)\b',key) and re.search(r'\bprocesses\b',key):return self.run({'steps':[{'tool':'processes'}]})
  match=re.fullmatch(r'(?:create|write|save) (?:a |an )?(?:text )?file (?:named |called )?("[^"]+"|\S+)(?: in (?:the )?workspace)? (?:containing|with (?:content|text))\s*:?\s*([\s\S]+)',value,re.I)
  if match:return self.run({'steps':[{'tool':'file_write','args':{'path':match[1].strip('"'),'text':match[2]}}]})
  match=re.fullmatch(r'(?:search (?:the )?web for|research online)\s+([\s\S]+)',value,re.I)
  if match:return self.run({'steps':[{'tool':'public_search','args':{'query':match[1]}}]})
  match=re.fullmatch(r'(?:read|open|inspect)\s+(https://\S+)',value,re.I)
  if match:return self.run({'steps':[{'tool':'public_page','args':{'url':match[1]}}]})
  match=re.fullmatch(r'select window (\d+)',value,re.I)
  if match:return self.run({'steps':[{'tool':'desktop_select','args':{'handle':match[1]}}]})
  return None
 def execute_file(self,body):
  path=Path(body['path']).resolve();raw=path.read_bytes() if path.exists() else None
  if (hashlib.sha256(raw).hexdigest() if raw is not None else None)!=body['expected_sha256']:raise ValueError('Target file changed after review; prepare a fresh proposal')
  if not path.parent.is_dir():raise ValueError('The destination folder does not exist')
  revisions=self.r.runtime.data/'talk-work/revisions';revisions.mkdir(parents=True,exist_ok=True)
  if raw is not None:(revisions/(uuid.uuid4().hex+'-'+path.name)).write_bytes(raw)
  new=body['text'].encode('utf-8');temporary=None
  try:
   with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.neural-write-',suffix='.tmp',delete=False) as stream:temporary=Path(stream.name);stream.write(new);stream.flush();os.fsync(stream.fileno())
   current=path.read_bytes() if path.exists() else None
   if (hashlib.sha256(current).hexdigest() if current is not None else None)!=body['expected_sha256']:raise ValueError('Target changed while preparing its replacement')
   os.replace(temporary,path)
  finally:
   if temporary is not None and temporary.is_file():temporary.unlink()
  return {'written':str(path),'bytes':len(new),'sha256':hashlib.sha256(new).hexdigest(),'verified':path.read_bytes()==new,'executed':True}
