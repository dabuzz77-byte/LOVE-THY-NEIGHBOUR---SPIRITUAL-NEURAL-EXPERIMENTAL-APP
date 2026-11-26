"""Read-only host counters; missing sensors remain unavailable."""
import os,platform,threading
_lock=threading.Lock();_nvml=None;_nvml_attempted=False;_cpu_previous=None
def windows_counters(value):
 global _cpu_previous
 if os.name!='nt':return
 try:
  import ctypes
  from ctypes import wintypes
  class Memory(ctypes.Structure):
   _fields_=[('length',wintypes.DWORD),('load',wintypes.DWORD)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
  memory=Memory();memory.length=ctypes.sizeof(memory)
  if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):value.update(memory_total=memory.total,memory_available=memory.available)
  idle=wintypes.FILETIME();kernel=wintypes.FILETIME();user=wintypes.FILETIME()
  if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle),ctypes.byref(kernel),ctypes.byref(user)):
   number=lambda f:(f.dwHighDateTime<<32)|f.dwLowDateTime
   sample=(number(idle),number(kernel)+number(user))
   if _cpu_previous and sample[1]>_cpu_previous[1]:value['cpu_percent']=max(0,min(100,100*(1-(sample[0]-_cpu_previous[0])/(sample[1]-_cpu_previous[1]))))
   _cpu_previous=sample
  class ProcessMemory(ctypes.Structure):
   _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak','working','pool_peak','pool','nonpaged_peak','nonpaged','page','page_peak')]
  process=ProcessMemory();process.cb=ctypes.sizeof(process);ctypes.windll.kernel32.GetCurrentProcess.restype=wintypes.HANDLE
  ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(ProcessMemory),wintypes.DWORD]
  if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(process),process.cb):value['process_rss']=process.working
 except (OSError,AttributeError):pass
def snapshot():
 global _nvml,_nvml_attempted
 value={'platform':platform.system(),'logical_cpus':os.cpu_count(),'cpu_percent':None,'memory_total':None,'memory_available':None,'process_rss':None,'gpus':[]}
 try:
  import psutil
  memory=psutil.virtual_memory();value.update(cpu_percent=psutil.cpu_percent(interval=None),memory_total=memory.total,memory_available=memory.available,process_rss=psutil.Process().memory_info().rss)
 except (ImportError,OSError):windows_counters(value)
 with _lock:
  if not _nvml_attempted:
   _nvml_attempted=True
   try:
    import pynvml
    pynvml.nvmlInit();_nvml=pynvml
   except Exception:pass
  if _nvml:
   try:
    for i in range(_nvml.nvmlDeviceGetCount()):
     handle=_nvml.nvmlDeviceGetHandleByIndex(i);name=_nvml.nvmlDeviceGetName(handle);memory=_nvml.nvmlDeviceGetMemoryInfo(handle);util=_nvml.nvmlDeviceGetUtilizationRates(handle)
     value['gpus'].append({'name':name.decode() if isinstance(name,bytes) else name,'utilization_percent':util.gpu,'memory_used':memory.used,'memory_total':memory.total})
   except Exception:value['gpu_sensor_status']='GPU utilization unavailable'
 if not value['gpus']:value['gpu_sensor_status']='No supported NVML counter; browser renderer reported separately'
 return value
