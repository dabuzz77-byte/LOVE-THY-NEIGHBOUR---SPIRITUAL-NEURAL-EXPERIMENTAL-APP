"""On-demand local knowledge with visible scope, bounded reads and credential exclusions."""
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import threading
import time
import psutil
from sources import now, save_json

def redact(text):
    text=re.sub(r'\b(?:sk-[A-Za-z0-9_-]{12,}|AIza[A-Za-z0-9_-]{20,})','[REDACTED]',text)
    return re.sub(r'''(?im)^(.*(?:api.?key|password|secret|token|authorization)["']?\s*[:=]).+$''',r'\1 [REDACTED]',text)

def redact_tree(value):
    if isinstance(value,dict):return {str(k):'[REDACTED]' if re.search(r'(?i)(api.?key|password|secret|token|authorization)',str(k)) else redact_tree(v) for k,v in value.items()}
    if isinstance(value,list):return [redact_tree(v) for v in value]
    return redact(value) if isinstance(value,str) else value

class LocalKnowledge:
    def __init__(self,rt):
        self.rt=rt;self.lock=threading.RLock();self.path=rt.data/'knowledge.json'
        try:self.state=json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError,ValueError):self.state={'roots':[str(rt.root),str(Path.home()/'Desktop'/'java'),str(Path.home()/'Desktop'/'python')],'files':[],'updated':None,'errors':[]}
        self.scanning=False

    def system(self):
        disks=[]
        for p in psutil.disk_partitions():
            try:
                d=psutil.disk_usage(p.mountpoint);disks.append({'mount':p.mountpoint,'total_gb':round(d.total/2**30,2),'free_gb':round(d.free/2**30,2)})
            except OSError:pass
        return {'os':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),
                'logical_cpus':psutil.cpu_count(),'physical_cpus':psutil.cpu_count(logical=False),'memory_gb':round(psutil.virtual_memory().total/2**30,2),
                'available_gb':round(psutil.virtual_memory().available/2**30,2),'disks':disks,'python':sys.version.split()[0],
                'tools':{n:shutil.which(n) for n in ('python','java','javac','git','node','ollama')},
                'processes':[{'pid':p.info['pid'],'name':p.info['name']} for p in psutil.process_iter(['pid','name'])],
                'observed':now(),'scope':'Metadata for accessible local processes and devices. Files only in indexed roots.'}

    def allowed(self,path):
        bad=('.git','.aws','.ssh','.codex','node_modules','vendor','data','__pycache__','.venv')
        return not any(p.lower() in bad for p in path.parts) and not re.search(r'(?i)(secret|password|credential|api.?key|\.env|token|connection\.json)',path.name)

    def index(self,roots=None):
        with self.lock:
            if self.scanning:raise ValueError('Indexing is already running')
            self.scanning=True
        try:
            if roots is None:roots=self.state['roots']
            if not isinstance(roots,list) or not 1<=len(roots)<=12:raise ValueError('Choose 1–12 folders')
            roots=[str(Path(r).expanduser().resolve()) for r in roots]
            files=[];errors=[];truncated=False
            for root in roots:
                if not Path(root).is_dir():errors.append({'path':root,'error':'Folder is unavailable'});continue
                for directory,subdirs,names in os.walk(root,followlinks=False):
                    subdirs[:]=[d for d in subdirs if self.allowed(Path(directory)/d) and not (Path(directory)/d).is_symlink() and not os.path.isjunction(Path(directory)/d)]
                    for name in names:
                        p=Path(directory)/name
                        if p.suffix.lower() not in ('.py','.java','.md','.txt','.json','.csv','.html','.js','.css') or not self.allowed(p):continue
                        try:
                            if p.is_symlink() or not p.resolve().is_relative_to(Path(root)):continue
                            stat=p.stat()
                            if stat.st_size>1024*1024:continue
                            files.append({'path':str(p),'relative':str(p.relative_to(root)),'root':root,'bytes':stat.st_size,'modified':stat.st_mtime})
                        except OSError as exc:errors.append({'path':str(p),'error':str(exc)[:120]})
                        if len(files)>=20000:truncated=True;break
                    if truncated:break
                if truncated:break
            with self.lock:
                self.state={'roots':roots,'files':files,'errors':errors[:100],'updated':now(),'truncated':truncated}
                save_json(self.path,self.state)
            self.rt.publish('knowledge',{'indexed':len(files),'errors':len(errors),'truncated':truncated})
            return self.view()
        finally:
            with self.lock:self.scanning=False

    def view(self):
        with self.lock:return {k:v for k,v in self.state.items() if k!='files'}|{'count':len(self.state['files']),'scanning':self.scanning}

    def read(self,path,feed=True):
        p=Path(path).resolve()
        with self.lock:known={f['path'] for f in self.state['files']};roots=list(self.state['roots'])
        if str(p) not in known or not self.allowed(p) or not any(p.is_relative_to(Path(r)) for r in roots):raise ValueError('Select a file in the current index')
        raw=p.read_bytes()
        if len(raw)>1024*1024:raise ValueError('File exceeds the reading limit')
        text=redact(raw.decode('utf-8-sig',errors='replace'))
        result={'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'text':text[:16000],'truncated':len(text)>16000}
        if feed:self.rt.binary_bus.feed('local-file',result)
        return result

    def search(self,query):
        words=set(re.findall(r'\w+',str(query).lower()))
        if not words:return []
        with self.lock:files=list(self.state['files'])
        ranked=sorted(files,key=lambda f:sum(w in f['relative'].lower() for w in words),reverse=True)
        matches=[]
        for f in ranked[:1500]:
            score=sum(w in f['relative'].lower() for w in words)*5
            try:
                text=self.read(f['path'],feed=False)['text']
                score+=sum(text.lower().count(w) for w in words)
                if score:
                    lines=[l[:260] for l in text.splitlines() if any(w in l.lower() for w in words)][:3]
                    matches.append({**f,'score':score,'excerpts':lines})
            except OSError:continue
        return sorted(matches,key=lambda f:f['score'],reverse=True)[:12]
