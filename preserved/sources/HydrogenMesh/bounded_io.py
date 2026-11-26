"""Bounded diagnostic files; never targets exported documents or source files."""
from pathlib import Path
import threading
import time

def cap_directory(directory,max_bytes=8*1024*1024,max_files=64,age_seconds=86400):
    if Path(directory).is_symlink():return 0
    root=Path(directory).resolve()
    if not root.exists():return 0
    files=[]
    for path in root.iterdir():
        if path.is_file() and not path.is_symlink() and path.resolve().parent==root:
            try:files.append((path.stat().st_mtime,path.stat().st_size,path))
            except OSError:pass
    files.sort(reverse=True,key=lambda row:row[0]);used=0;removed=0;now=time.time()
    for index,(stamp,size,path) in enumerate(files):
        if index>=max_files or used+size>max_bytes or now-stamp>age_seconds:
            try:path.unlink();removed+=1
            except OSError:pass
        else:used+=size
    return removed

class RotatingSink:
    def __init__(self,path,limit=1024*1024,backups=2):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.limit=limit;self.backups=backups;self.lock=threading.Lock()
    def write(self,raw):
        with self.lock:
            for start in range(0,len(raw),min(16384,self.limit)):
                chunk=raw[start:start+min(16384,self.limit)]
                if self.path.exists() and self.path.stat().st_size+len(chunk)>self.limit:
                    for i in range(self.backups,0,-1):
                        dest=self.path.with_name(self.path.name+f'.{i}')
                        source=self.path if i==1 else self.path.with_name(self.path.name+f'.{i-1}')
                        if source.exists():source.replace(dest)
                with self.path.open('ab') as handle:handle.write(chunk)

def drain_process(child,path):
    sink=RotatingSink(path)
    try:
        while True:
            chunk=child.stdout.read1(16384)
            if not chunk:break
            sink.write(chunk)
    finally:
        child.stdout.close()
