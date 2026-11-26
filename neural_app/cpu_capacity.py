"""Read-only CPU clock/capacity telemetry with explicitly labelled estimates."""
import os,time,ctypes as C
class CpuCapacity:
 def __init__(self):self.last=None;self.updated=0;self.snapshot={};self.clock=None;self.physical=None
 def sample(self):
  if time.monotonic()-self.updated<1:return self.snapshot
  logical=os.cpu_count() or 1;clock=None;physical=None;clock_source='unavailable';busy=None
  try:
   import psutil
   frequency=psutil.cpu_freq();clock=frequency.current*1e6 if frequency else None;physical=psutil.cpu_count(logical=False);clock_source='OS-reported current frequency'
  except (ImportError,OSError):pass
  if os.name=='nt':
   try:
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
     if not clock:clock=winreg.QueryValueEx(key,'~MHz')[0]*1e6;clock_source='Windows nominal registry frequency'
   except OSError:pass
   try:
    kernel=C.WinDLL('kernel32',use_last_error=True);size=C.c_ulong(0);kernel.GetLogicalProcessorInformationEx(0,None,C.byref(size));buf=C.create_string_buffer(size.value)
    if size.value and kernel.GetLogicalProcessorInformationEx(0,buf,C.byref(size)):
     import struct
     offset=0;count=0
     while offset+8<=size.value:
      relation,length=struct.unpack_from('<II',buf.raw,offset)
      if length<8 or offset+length>size.value:break
      count+=relation==0;offset+=length
     physical=count or physical
    from ctypes import wintypes as W
    idle=W.FILETIME();k=W.FILETIME();user=W.FILETIME()
    if kernel.GetSystemTimes(C.byref(idle),C.byref(k),C.byref(user)):
     value=lambda x:(x.dwHighDateTime<<32)|x.dwLowDateTime
     current=(value(idle),value(k)+value(user))
     if self.last and current[1]>self.last[1]:busy=max(0,min(1,1-(current[0]-self.last[0])/(current[1]-self.last[1])))
     self.last=current
   except (OSError,ValueError,AttributeError):pass
  capacity=clock*physical if clock and physical else None;self.updated=time.monotonic();self.snapshot={'time':time.time(),'logical_processors':logical,'physical_cores':physical,'reported_clock_hz':clock,'clock_source':clock_source,'aggregate_cpu_busy_fraction':busy,'nominal_physical_core_clock_sum_hz':capacity,'estimated_busy_clock_equivalent_hz':capacity*busy if capacity and busy is not None else None,'scope':'Clock-sum and busy-cycle equivalents are capacity estimates, not completed app operations or guaranteed instruction throughput'};return self.snapshot
