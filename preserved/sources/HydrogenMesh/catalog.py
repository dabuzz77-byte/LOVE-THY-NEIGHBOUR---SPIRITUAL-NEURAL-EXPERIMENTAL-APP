"""Bounded application discovery and honest runtime inventory."""
import ast
import ctypes
from ctypes import wintypes
import os
from pathlib import Path

SKIP={'data','work','_internal','node_modules','.git','venv','.venv','__pycache__','reference','licenses','assets','site-packages','target','build','dist'}

def discover(root,max_files=12000):
    root=Path(root);items=[];visited=0;truncated=False
    for folder,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d.lower() not in SKIP and not d.lower().endswith('-data') and not Path(folder,d).is_symlink())
        if len(Path(folder).relative_to(root).parts)>5:dirs[:]=[]
        for name in sorted(files):
            visited+=1
            if visited>max_files:truncated=True;break
            path=Path(folder,name);ext=path.suffix.lower()
            if ext not in ('.py','.pyw','.java','.jar','.exe'):continue
            if name.startswith(('test_','verify_')):continue
            kind={'.py':'Python','.pyw':'Python','.java':'Java source','.jar':'Java archive','.exe':'Application'}[ext]
            entry=ext not in ('.py','.pyw','.java');problem=''
            if ext in ('.py','.pyw','.java'):
                try:
                    if path.stat().st_size>2000000:continue
                    source=path.read_text(encoding='utf-8-sig',errors='replace')
                    if ext=='.java':entry='static void main' in source
                    else:
                        ast.parse(source);entry='__main__' in source
                except (OSError,SyntaxError) as e:problem=str(e).splitlines()[0]
            if entry or problem:items.append(dict(name=name,app=path.relative_to(root).parts[0],path=str(path),kind=kind,error=problem))
        if truncated:break
    return dict(items=items,visited=visited,truncated=truncated,excluded=sorted(SKIP))

def processes():
    """Toolhelp names/PIDs only, without command lines or private process memory."""
    if os.name!='nt':return []
    class Entry(ctypes.Structure):
        _fields_=[('dwSize',wintypes.DWORD),('cntUsage',wintypes.DWORD),('th32ProcessID',wintypes.DWORD),
                  ('th32DefaultHeapID',ctypes.c_size_t),('th32ModuleID',wintypes.DWORD),('cntThreads',wintypes.DWORD),
                  ('th32ParentProcessID',wintypes.DWORD),('pcPriClassBase',wintypes.LONG),('dwFlags',wintypes.DWORD),('szExeFile',wintypes.WCHAR*260)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
    kernel.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.CreateToolhelp32Snapshot(2,0)
    if handle==ctypes.c_void_p(-1).value:return []
    result=[];entry=Entry();entry.dwSize=ctypes.sizeof(entry)
    try:
        ok=kernel.Process32FirstW(handle,ctypes.byref(entry))
        while ok:
            name=entry.szExeFile
            if name.lower().startswith(('python','java','pypy')) or any(word in name.lower() for word in ('fluxbus','observatory')):
                result.append(dict(pid=entry.th32ProcessID,name=name,status='Detected; adapter connection tracked separately'))
            ok=kernel.Process32NextW(handle,ctypes.byref(entry))
    finally:kernel.CloseHandle(handle)
    return result
