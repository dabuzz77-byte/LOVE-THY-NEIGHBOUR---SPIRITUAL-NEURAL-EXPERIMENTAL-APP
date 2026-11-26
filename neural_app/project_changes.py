"""Staged multi-file edits with source snapshots and recoverable commits.

Only bounded pure-function tests run; project imports and startup do not run.
"""
import ast,copy,difflib,hashlib,json,os,tempfile,time,types,uuid
from pathlib import Path
from .work_tools import WorkTools
from .project_function_testing import test_project

def digest(raw):return hashlib.sha256(raw).hexdigest()

class ProjectChanges:
 def __init__(self,workbench):
  self.w=workbench;self.rows=workbench.s.setdefault('change_sets',[])
 def summary(self,row):
  return {k:copy.deepcopy(v) for k,v in row.items() if k not in ('replacements','originals')}
 def prepare(self,body):
  if not isinstance(body,dict):raise ValueError('Supply a project change object')
  tools=self.w.tools();folder=body.get('folder');root=tools.path(folder)
  if not root.is_dir() or root.is_symlink():raise ValueError('Choose an existing workspace project folder')
  changes=body.get('changes');tests=body.get('tests')
  if not isinstance(changes,list) or not 1<=len(changes)<=12:raise ValueError('Supply 1 to 12 text file changes')
  if not isinstance(tests,list) or not 1<=len(tests)<=12:raise ValueError('Supply 1 to 12 independent pure-function test groups')
  originals={};replacements={};diffs={};size=0;ident=uuid.uuid4().hex
  for change in changes:
   if not isinstance(change,dict) or not isinstance(change.get('path'),str) or not isinstance(change.get('text'),str):raise ValueError('Each change needs path and text')
   name=change['path'];path=tools.path(str(Path(folder)/name))
   if Path(name).is_absolute() or not path.is_relative_to(root) or path==root or path.is_symlink():raise ValueError('Changed file must remain within the selected project')
   key=str(path.relative_to(tools.root))
   if key in replacements:raise ValueError('Duplicate changed file')
   old=tools.read({'path':key}) if path.exists() else None
   if old:old['raw_text']=path.read_bytes().decode('utf-8')
   if (old['sha256'] if old else None)!=change.get('expected_sha256'):raise ValueError('Read each existing changed file and provide its expected_sha256')
   text=change['text'];size+=len(text.encode())+(len(old['text'].encode()) if old else 0)
   if size>262144:raise ValueError('Change-set text budget reached')
   if path.suffix=='.py':ast.parse(text,filename=key)
   originals[key]=old;replacements[key]=text
   diffs[key]='\n'.join(difflib.unified_diff((old['text'] if old else '').splitlines(),text.splitlines(),fromfile=key+' before',tofile=key+' proposed',lineterm=''))
  snapshots={};copied=0
  with tempfile.TemporaryDirectory(dir=self.w.r.runtime.data) as tmp:
   staged=WorkTools(types.SimpleNamespace(data=Path(tmp)));stage_root=staged.root/'code';stage_root.mkdir(exist_ok=True)
   for parent,dirs,files in os.walk(root,followlinks=False):
    dirs[:]=[d for d in dirs if d not in ('.git','node_modules','__pycache__','.venv','venv') and not (Path(parent)/d).is_symlink()]
    for filename in files:
     p=Path(parent)/filename
     if p.is_symlink():raise ValueError('Project snapshot cannot include symbolic links')
     if p.suffix not in ('.py','.json','.txt','.md','.toml','.cfg','.ini'):continue
     p=tools.path(str(p.relative_to(tools.root)));raw=p.read_bytes();copied+=len(raw)
     if len(snapshots)>=128 or copied>1048576:raise ValueError('Project snapshot budget reached')
     key=str(p.relative_to(tools.root));snapshots[key]=digest(raw);dest=stage_root/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
   for key,text in replacements.items():
    target=stage_root/tools.path(key).relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
   results=[]
   for test in tests:
    if not isinstance(test,dict):raise ValueError('Each test group needs module, function and cases')
    result=test_project(staged,{**test,'folder':'code'});results.append(result)
    if not result.get('all_passed'):return {'status':'tests-failed','tests':results,'source_files_changed':False,'proposal_retained':False}
  row={'id':ident,'folder':folder,'status':'prepared','created':time.time(),'replacements':replacements,'originals':originals,'snapshot':snapshots,'diffs':diffs,'tests':results,'files':list(replacements),'source_files_changed':False,'scope':'Staged pure local-function tests only; not full application validation. Apply rechecks every snapshotted source.'}
  self.rows.append(row);self.rows[:]=self.rows[-4:];self.w.r.controller.save();return self.summary(row)
 def apply(self,ident):
  with self.w.lock:
   row=next((r for r in self.rows if r['id']==ident),None)
   if row is None or row['status']!='prepared':raise ValueError('Choose a prepared change-set ID')
   tools=self.w.tools();written=[]
   # Check all known project dependencies, not only the files being edited.
   for key,expected in row['snapshot'].items():
    path=tools.path(key)
    if not path.is_file() or digest(path.read_bytes())!=expected:raise ValueError('Project changed since testing: '+key)
   for key,original in row['originals'].items():
    path=tools.path(key)
    if original is None and path.exists():raise ValueError('A proposed new file already exists: '+key)
   row['status']='applying';self.w.r.controller.save()
   try:
    for key,text in row['replacements'].items():
     original=row['originals'][key]
     # Track an attempted write too, so post-write errors can be repaired.
     written.append(key)
     row['attempted']=list(written);self.w.r.controller.save()
     tools.write({'path':key,'text':text,'expected_sha256':original['sha256'] if original else None})
     if tools.read({'path':key})['text']!=text:raise ValueError('Written-file verification failed: '+key)
    row.update(status='applied',source_files_changed=True,verified_hashes={key:digest(text.encode()) for key,text in row['replacements'].items()})
   except Exception as exc:
    row['error']=str(exc)[:240];self.rollback(row,tools,written)
   self.w.r.controller.save();return self.summary(row)
 def rollback(self,row,tools,written):
  recovery=[]
  for key in reversed(written):
   path=tools.path(key);original=row['originals'][key];expected=digest(row['replacements'][key].encode())
   try:
    current=digest(path.read_bytes()) if path.exists() else None
    if current==(original['sha256'] if original else None):continue
    if current!=expected:raise ValueError('Concurrent change preserved; manual recovery required')
    if original:tools.write({'path':key,'text':original['raw_text'],'expected_sha256':current})
    else:path.unlink()
    recovery.append({'path':key,'restored':True})
   except Exception as failure:recovery.append({'path':key,'restored':False,'error':str(failure)[:160]})
  row.update(status='rolled-back' if all(r['restored'] for r in recovery) else 'needs-recovery',recovery=recovery,source_files_changed=any(not r['restored'] for r in recovery))
 def recover(self,ident):
  with self.w.lock:
   row=next((r for r in self.rows if r['id']==ident),None)
   if row is None or row['status']!='needs-recovery':raise ValueError('Choose a change set awaiting recovery')
   self.rollback(row,self.w.tools(),row.get('attempted',[]));self.w.r.controller.save();return self.summary(row)
