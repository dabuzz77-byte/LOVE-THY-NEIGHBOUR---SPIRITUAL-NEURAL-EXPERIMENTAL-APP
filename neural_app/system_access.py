"""OS-supported diagnostics and explicit routing to existing reviewed PC tools."""
import ctypes,os,platform,time
from .cpu_capacity import CpuCapacity
class SystemAccess:
 def __init__(self,runtime):self.runtime=runtime;self.cpu=CpuCapacity()
 def view(self):
  admin=False
  if os.name=='nt':
   try:admin=bool(ctypes.WinDLL('shell32').IsUserAnAdmin())
   except OSError:pass
  return {'time':time.time(),'os':platform.system(),'kernel_release':platform.release(),'kernel_version':platform.version(),'current_process_elevated':admin,'cpu':self.cpu.sample(),'capabilities':[{'name':'Kernel identity, system time and processor topology','state':'OS-supported read-only API'},{'name':'Processes, adapters and connections','state':'Available where the current OS account permits; system-fractal view'},{'name':'Services, drivers and event-log inspection','state':'Existing reviewed PC-command tool; availability depends on OS rights'},{'name':'Administrative changes','state':'Exact-operation review and current OS/UAC permissions'},{'name':'Raw kernel memory access / arbitrary driver execution','state':'not implemented'}],'execution_path':'Talk & Work reviewed pc_command tool; training never approves its own requests','scope':'Current-account OS-supported access, not a blanket kernel privilege grant'}
