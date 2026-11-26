"""Exact register interpretation and an app-scoped, inspectable command language."""
import hashlib,json,re,shlex,time
from .runtime import ROOT
from .translation import translate_bits,encode,decode

SOURCE=ROOT/'references/runinplace-original.txt'
USES=[('Exact arithmetic','Trace 64-bit register operations and preserve every represented bit.'),('Teaching','Step through loops, registers and binary/ternary conversion.'),('Regression checks','Compare original routines with independently calculated sums.'),('Feedback design','Receive, inspect, process, review and return a bounded app result.'),('Neural learning','Feed measured execution features through the shared learner.'),('Engine orchestration','Queue registered app engines through one checked command interface.'),('Visual debugging','Observe register bits, loop position, feedback strength and receipts.'),('Resilience planning','Explore repair and protective routing using configured app models.'),('Research intake','Review the app’s existing public-source processing and provenance.'),('Accessible interfaces','Use plain requests, a command line or the graphical controls.'),('Lossless exchange','Export exact register bits and inspect the transport round trip.'),('Creative study','Keep the complete original notation beside a documented operational interpretation.')]

def reactor(body):
 def checked(key,default,maximum):
  value=body.get(key,default)
  if type(value) is not int or not 0<=value<=maximum:raise ValueError(key+' must be an integer in 0..'+str(maximum))
  return value
 incoming=checked('incoming_units',1000,1000000);release=checked('release_per_mille',420,1000);efficiency=checked('efficiency_per_mille',950,1000)
 retained=useful=cost=protected=circulated=0;trace=[]
 for step in range(12):
  received=incoming//12+(step<incoming%12);retained+=received
  circulated+=retained
  converted=retained*release//1000;retained-=converted
  delivered=converted*efficiency//1000;cost+=converted-delivered
  reserve=delivered*15//100;protected+=reserve;useful+=delivered-reserve
  trace.append({'step':step+1,'received':received,'retained':retained,'useful':useful,'protected':protected,'cost':cost})
 return {'model':'Ouroboros gathering → regulated reactor centre → protection and service','units':'Exact integer planning units','incoming':incoming,'retained':retained,'useful':useful,'protected':protected,'conversion_cost':cost,'conservation_error':incoming-retained-useful-protected-cost,'output_gate_per_mille':release,'efficiency_per_mille':efficiency,'trajectory':trace,'closed_loop_comparison':{'retained':incoming,'useful':0},'equation':'incoming = retained + useful + protected + conversion_cost','overunity_study':{'gross_circulated_units':circulated,'unique_input_units':incoming,'circulation_multiple_exact':str(circulated)+'/'+str(incoming) if incoming else '0/0 (no input)','meaning':'Repeated passages through the loop count as gross circulation; unique useful output is counted once in the resource budget.','process':['Gather','Recirculate','Stabilise','Open a purposeful output','Protect infrastructure','Serve life','Return information to the learner']}}

def assembly(source,initial_rdx=0):
 if type(initial_rdx) is not int or not 0<=initial_rdx<2**64:raise ValueError('RDX must be an unsigned 64-bit integer')
 blocks=re.findall(r'(?is)main\s+PROC\b(.*?)main\s+ENDP',source);results=[]
 for number,block in enumerate(blocks):
  code=[];labels={}
  for line in block.splitlines():
   line=line.split(';')[0].strip().lower()
   if not line:continue
   if line.endswith(':'):labels[line[:-1].strip()]=len(code);continue
   parts=line.replace(',',' ').split()
   if parts[0] not in ('xor','mov','inc','add','dec','jnz','ret'):raise ValueError('Unsupported instruction: '+parts[0])
   code.append(parts)
  registers=dict.fromkeys(('rax','rbx','rcx','rdx'),0);registers['rdx']=initial_rdx;pc=steps=0;zero=False;trace=[];loops=0
  def get(v):return registers.get({'eax':'rax','ebx':'rbx','ecx':'rcx','edx':'rdx'}.get(v,v),int(v) if v.isdigit() else 0)
  while pc<len(code):
   if steps>=100000:raise ValueError('The routine exceeded its instruction budget')
   ins=code[pc];op=ins[0];pc+=1;steps+=1
   if op=='ret':break
   if op=='jnz':
    if not zero:
     if ins[1] not in labels:raise ValueError('Unknown loop label')
     pc=labels[ins[1]]
    continue
   dest=ins[1];reg={'eax':'rax','ebx':'rbx','ecx':'rcx','edx':'rdx'}.get(dest,dest)
   if reg not in registers:raise ValueError('Unsupported register')
   width=32 if dest.startswith('e') else 64;a=get(dest)
   value=(a^get(ins[2])) if op=='xor' else get(ins[2]) if op=='mov' else a+get(ins[2]) if op=='add' else a+1 if op=='inc' else a-1
   registers[reg]=value&((1<<width)-1)
   if op!='mov':zero=registers[reg]==0
   if op=='add':
    loops+=1
    if len(trace)<24 or loops%max(1,11111//48)==0:trace.append({'iteration':loops,'rax':str(registers['rax']),'rdx':str(registers['rdx']),'rcx':str(registers['rcx'])})
  results.append({'block':number+1,'steps':steps,'iterations':loops,'registers':{k:str(v) for k,v in registers.items()},'trace':trace[-72:],'transport':translate_bits(format(registers['rax'],'064b')),'initial_rdx':str(initial_rdx),'register_width':64})
 return results

class RunInPlace:
 def __init__(self,runtime):
  self.runtime=runtime;self.source=SOURCE.read_text(encoding='utf-8');self.digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest();self.enabled=True;self.next_at=0;self.cycles=0;self.receipt=None;self.last=None;self.commands=[]
  self.original=assembly(self.source)
 def process(self,body):
  initial=body.get('initial_rdx',0)
  if isinstance(initial,str):
   if not initial.isdigit():raise ValueError('Use an unsigned decimal integer')
   initial=int(initial)
  routines=assembly(self.source,initial)
  text=body.get('text') or 'Receive · examine · choose care · process · learn · return'
  if not isinstance(text,str) or len(text.encode('utf-8'))>360:raise ValueError('Use at most 360 UTF-8 bytes per interpreted input')
  raw=text.encode('utf-8');packet=encode(raw)
  packet.update(round_trip=decode(packet)==raw,bit_width=len(raw)*8)
  field=self.runtime.field.snapshot();values=field['values'];signal=sum(values)/len(values);magnitude=sum(abs(v) for v in values)/len(values)
  result={'status':'COMPLETE','source_sha256':self.digest,'routines':routines,'input':text,'transport':packet,'feedback':{'field_tick':field.get('ticks',self.runtime.field.ticks),'signal':signal,'magnitude':magnitude,'receive':True,'process':True,'learn':self.runtime.settings['learning'],'return':'Configured authenticated app channels'},'interpretation':['Receive an explicit input','Preserve its integer and byte representation','Run the documented register routines','Consult shared field and care-oriented app logic','Record the result and feed shared learning','Offer the configured source-free inference summary'],'notation':{'loop_markers':len(re.findall(r'LOOP START',self.source)),'send_markers':len(re.findall(r'\bSEND\b',self.source)),'receive_markers':len(re.findall(r'\bREC[EI]+VE\b',self.source))},'scope':'Original assembly instructions execute in an app-owned 64-bit register interpreter. The remaining original notation is preserved as source text; it is not an operating-system shell.'}
  result['reactor']=reactor(body)
  self.last=result;return result
 def tick(self):
  if not self.enabled or time.monotonic()<self.next_at or self.runtime.queue.qsize()>2:return
  self.next_at=time.monotonic()+30
  self.runtime.submit('pipeline',{'text':'Receive, preserve exact bits, choose care, learn and return.','sections':['runinplace','super_mesh','inference','beacon']});self.cycles+=1
 def view(self):return {'source':self.source,'sha256':self.digest,'source_bytes':len(SOURCE.read_bytes()),'enabled':self.enabled,'cycles':self.cycles,'last':self.last,'original':self.original,'uses':[{'title':a,'detail':b} for a,b in USES],'commands':self.commands[-16:]}
 def command(self,text):
  if not isinstance(text,str) or not 1<=len(text)<=4096:raise ValueError('Enter a command or short request')
  words=shlex.split(text);cmd=words[0].lower();args=words[1:];reason='Explicit app command'
  if cmd not in ('help','status','binary','original','reactor','interpret','engine','pause','resume'):
   lower=text.lower();reason='Plain-language request matched to an app operation'
   if any(x in lower for x in ('status','happening','running','activity')):cmd='status';args=[]
   elif any(x in lower for x in ('reactor','ouroboros')):cmd='reactor';args=[]
   elif any(x in lower for x in ('original','register','assembly')):cmd='original';args=[]
   elif any(x in lower for x in ('help','possible','uses','commands')):cmd='help';args=[]
   else:cmd='interpret';args=[text]
  if cmd=='help':output={'commands':['status','binary <unsigned integer> [width]','original [initial RDX]','reactor [incoming units] [release per mille] [efficiency per mille]','interpret <text>','engine <registered ID> <text>','pause','resume'],'uses':USES}
  elif cmd=='status':output={'cycles':self.cycles,'enabled':self.enabled,'learning_updates':self.runtime.get_model().updates,'queue':self.runtime.queue.qsize(),'originals':self.runtime.component_host.original_lane.view() if hasattr(self.runtime,'component_host') else None,'delivery':dict(self.runtime.delivery)}
  elif cmd=='binary':
   n=int(args[0]);width=int(args[1]) if len(args)>1 else max(1,n.bit_length())
   if n<0 or not 1<=width<=4096 or n.bit_length()>width:raise ValueError('Use a fitting unsigned integer and 1–4096 bits')
   output=translate_bits(format(n,'0'+str(width)+'b'))
  elif cmd=='original':output={'routines':assembly(self.source,int(args[0]) if args else 0)}
  elif cmd=='reactor':
   output=reactor(dict(zip(('incoming_units','release_per_mille','efficiency_per_mille'),map(int,args))))
   with self.runtime.lock:
    receipt=self.runtime.record('runinplace',{'command':'reactor'},output,0);self.runtime.learn({'runinplace':output})
   output={**output,'shared_receipt':receipt}
  elif cmd in ('pause','resume'):self.enabled=cmd=='resume';output={'enabled':self.enabled}
  else:
   section=args.pop(0) if cmd=='engine' and args else 'runinplace'
   from .runtime import SECTIONS
   if section not in SECTIONS:raise ValueError('Choose a registered engine ID')
   payload=' '.join(args) or text
   output={'job':self.runtime.submit('pipeline',{'text':payload[:360],'sections':list(dict.fromkeys([section,'super_mesh','inference','beacon']))}),'engine':section}
  value={'command':text,'resolved':cmd,'reason':reason,'output':output,'at':time.time()};self.commands.append(value);self.commands=self.commands[-16:];return value
