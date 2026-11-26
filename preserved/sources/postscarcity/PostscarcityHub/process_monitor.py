"""Read-only Windows process observer. Never injects, imports, kills or alters apps."""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import re
import subprocess
import time

RUNTIME = re.compile(r"^(python(?:w|\d+(?:\.\d+)*)?|py|javaw?)\.exe$", re.I)


def source_label(name, command):
    """Keep only a source/class label; never retain whole command lines or secrets."""
    if not command:
        return name
    python_path = re.search(r'"([^"\r\n]+\.py)"|(?:^|\s)([^\s"]+\.py)(?:\s|$)', command, re.I)
    if python_path:
        return Path(python_path.group(1) or python_path.group(2)).name
    jar = re.search(r'(?:^|\s)-jar\s+(?:"([^"\r\n]+)"|(\S+))', command)
    if jar:
        return Path(jar.group(1) or jar.group(2)).name
    tokens = re.findall(r'"([^"]*)"|(\S+)', command)
    flat = [a or b for a,b in tokens][1:]
    if name.lower().startswith("java"):
        skip = False
        for token in flat:
            if skip:
                skip = False
                continue
            if token in ("-cp","-classpath","--class-path","--module-path","-p","--add-modules"):
                skip = True
                continue
            if token.startswith("-"):
                continue
            if re.fullmatch(r"[\w.$-]+",token):
                return token[:120]
            break
    return name


class ProcessMonitor:
    def __init__(self):
        self.previous = {}
        self.labels = {}
        self.label_status = "Executable names; source labels are being checked."
        self.metadata_checked = False
        if os.name != "nt":
            return
        class Entry(C.Structure):
            _fields_ = [("dwSize",W.DWORD),("cntUsage",W.DWORD),("pid",W.DWORD),
                        ("heap",C.c_size_t),("module",W.DWORD),("threads",W.DWORD),
                        ("parent",W.DWORD),("priority",W.LONG),("flags",W.DWORD),("exe",W.WCHAR*260)]
        class Memory(C.Structure):
            _fields_ = [("cb",W.DWORD),("faults",W.DWORD),("peak",C.c_size_t),("working",C.c_size_t),
                        ("peakPaged",C.c_size_t),("paged",C.c_size_t),("peakNonpaged",C.c_size_t),
                        ("nonpaged",C.c_size_t),("pagefile",C.c_size_t),("peakPagefile",C.c_size_t)]
        self.Entry,self.Memory = Entry,Memory
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.ps = C.WinDLL("psapi", use_last_error=True)
        self.k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD]
        self.k.CreateToolhelp32Snapshot.restype=W.HANDLE
        for name in ("Process32FirstW","Process32NextW"):
            fn=getattr(self.k,name);fn.argtypes=[W.HANDLE,C.POINTER(Entry)];fn.restype=W.BOOL
        self.k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];self.k.OpenProcess.restype=W.HANDLE
        self.k.CloseHandle.argtypes=[W.HANDLE];self.k.CloseHandle.restype=W.BOOL
        self.k.GetProcessTimes.argtypes=[W.HANDLE]+[C.POINTER(W.FILETIME)]*4
        self.k.GetProcessTimes.restype=W.BOOL
        self.k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)]
        self.k.QueryFullProcessImageNameW.restype=W.BOOL
        self.ps.GetProcessMemoryInfo.argtypes=[W.HANDLE,C.POINTER(Memory),W.DWORD]
        self.ps.GetProcessMemoryInfo.restype=W.BOOL

    def refresh_labels(self):
        """Optional metadata; lack of CIM access never stops native discovery."""
        command = r"$ErrorActionPreference='Stop'; Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(python(w|[0-9.]+)?|py|javaw?)\.exe$'} | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
        try:
            run = subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",command],
                     capture_output=True,text=True,timeout=6,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            if run.returncode:
                raise OSError("Process command metadata unavailable")
            rows=json.loads(run.stdout) if run.stdout.strip() else []
            if isinstance(rows,dict): rows=[rows]
            labels={int(row["ProcessId"]):source_label(row["Name"],row.get("CommandLine")) for row in rows}
            self.labels=labels
            self.label_status="Source labels resolved where Windows provides command metadata."
        except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):
            self.label_status="Command details unavailable; displaying executable names and process IDs."
        self.metadata_checked=True

    def snapshot(self):
        now=time.monotonic()
        if os.name!="nt":
            return {"status":"unavailable","note":"Automatic process observation requires Windows.","processes":[],"total_visible_processes":0}
        snapshot=self.k.CreateToolhelp32Snapshot(2,0)
        if snapshot==C.c_void_p(-1).value:
            return {"status":"unavailable","note":"Windows denied process enumeration.","processes":[],"total_visible_processes":0}
        entry=self.Entry();entry.dwSize=C.sizeof(entry)
        processes=[];total=0;current={}
        try:
            valid=self.k.Process32FirstW(snapshot,C.byref(entry))
            while valid:
                total+=1
                if RUNTIME.fullmatch(entry.exe):
                    row={"pid":entry.pid,"parent_pid":entry.parent,"executable":entry.exe,
                         "language":"Java" if entry.exe.lower().startswith("java") else "Python",
                         "label":self.labels.get(entry.pid,entry.exe),"cpu_percent":None,"memory_mb":None,
                         "path":None,"started_filetime":None,"access":"limited","mode":"observed"}
                    handle=self.k.OpenProcess(0x1010,False,entry.pid) or self.k.OpenProcess(0x1000,False,entry.pid)
                    if handle:
                        try:
                            created,exited,kernel,user=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
                            if self.k.GetProcessTimes(handle,C.byref(created),C.byref(exited),C.byref(kernel),C.byref(user)):
                                stamp=(created.dwHighDateTime<<32)|created.dwLowDateTime
                                cpu=((kernel.dwHighDateTime<<32)|kernel.dwLowDateTime)+((user.dwHighDateTime<<32)|user.dwLowDateTime)
                                row["started_filetime"]=stamp
                                key=(entry.pid,stamp)
                                old=self.previous.get(key)
                                if old and now>old[0]:
                                    row["cpu_percent"]=max(0,min(100,(cpu-old[1])/1e7/(now-old[0])*100/(os.cpu_count() or 1)))
                                current[key]=(now,cpu)
                            buf=C.create_unicode_buffer(32768);length=W.DWORD(len(buf))
                            if self.k.QueryFullProcessImageNameW(handle,0,buf,C.byref(length)):
                                row["path"]=buf.value
                            mem=self.Memory();mem.cb=C.sizeof(mem)
                            if self.ps.GetProcessMemoryInfo(handle,C.byref(mem),mem.cb):
                                row["memory_mb"]=mem.working/(1024*1024)
                            row["access"]="read"
                        finally:
                            self.k.CloseHandle(handle)
                    row["id"]=f"process-{entry.pid}-{row['started_filetime'] or 0}"
                    if entry.pid==os.getpid():row["label"]="Postscarcity Hub (this process)"
                    processes.append(row)
                valid=self.k.Process32NextW(snapshot,C.byref(entry))
        finally:
            self.k.CloseHandle(snapshot)
        self.previous=current
        return {"status":"observing","sample_monotonic":now,"total_visible_processes":total,
                "note":"Windows-visible programs only; permissions can limit visibility. "+self.label_status,
                "processes":sorted(processes,key=lambda row:(row["language"],row["label"],row["pid"]))}
