"""Typed UI control registry and authenticated transport-neutral command queue."""
import collections,copy,hashlib,json,math,re,threading,time,uuid

def encoded(value):return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')

class ControlBus:
 def __init__(self):self.lock=threading.RLock();self.controls=collections.OrderedDict();self.commands=collections.OrderedDict();self.sequence=0;self.clients=collections.OrderedDict()
 def register(self,body):
  if len(encoded(body))>200000:raise ValueError('Control registration batch exceeds 200 KB')
  client=body.get('client');section=body.get('section');rows=body.get('controls')
  if not isinstance(client,str) or not re.fullmatch(r'[\w-]{1,80}',client) or not isinstance(section,str) or len(section)>100 or not isinstance(rows,list) or len(rows)>128:raise ValueError('Use a client, section and at most 128 controls')
  result=[]
  for row in rows:
   if not isinstance(row,dict):raise ValueError('Control descriptors must be objects')
   ident=row.get('id');kind=row.get('kind')
   if not isinstance(ident,str) or len(ident)>400 or not ident.startswith(client+':') or kind not in ('text','number','checkbox','select','button','canvas','file','readonly'):raise ValueError('Invalid client-scoped control descriptor')
   options=row.get('options',[])
   if not isinstance(options,list) or len(options)>512 or any(not isinstance(v,str) or len(v)>500 for v in options):raise ValueError('Invalid select options')
   descriptor={'id':ident,'client':client,'section':section,'kind':kind,'label':str(row.get('label',''))[:160],'options':options,'max_length':max(0,min(16000,int(row.get('max_length',16000)))),'mounted':True,'updated':time.time(),'mode':'request' if kind in ('button','canvas','file') else 'readonly' if kind=='readonly' else 'set'}
   for key in ('min','max','step'):
    if row.get(key) is not None:
     v=row[key]
     if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('Numeric limits must be finite')
     descriptor[key]=v
   if 'value' in row:descriptor['value']=self.validate(descriptor,row['value']) if descriptor['mode']=='set' else None
   result.append(descriptor)
  with self.lock:
   self.clients[client]=time.time();self.clients.move_to_end(client)
   while len(self.clients)>128:self.clients.popitem(last=False)
   for row in result:
    previous=self.controls.get(row['id'],{})
    if 'value' not in row and 'value' in previous:row['value']=previous['value']
    self.controls[row['id']]=row;self.controls.move_to_end(row['id'])
   while len(self.controls)>12000:self.controls.popitem(last=False)
  return {'registered':len(result),'client':client,'section':section}
 def mounted(self,client,ids):
  if not isinstance(ids,list) or len(ids)>4096:raise ValueError('Use a bounded mounted-control list')
  with self.lock:
   active=set(ids)
   for row in self.controls.values():
    if row['client']==client:row['mounted']=row['id'] in active
  return {'mounted':len(active)}
 @staticmethod
 def validate(row,value):
  kind=row['kind']
  if len(encoded(value))>20000:raise ValueError('Control value exceeds 20 KB')
  if kind=='checkbox':
   if type(value)is not bool:raise ValueError('Checkbox requires a boolean')
  elif kind=='number':
   if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Control requires a finite number')
   if abs(value)>9007199254740991:raise ValueError('Value exceeds exact browser numeric range')
   if isinstance(value,float) and value.is_integer():value=int(value)
   if 'min' in row and value<row['min'] or 'max' in row and value>row['max']:raise ValueError('Value is outside this control range')
   step=row.get('step')
   if step and step>0:
    units=(value-row.get('min',0))/step
    if not math.isclose(units,round(units),abs_tol=1e-7,rel_tol=1e-9):raise ValueError('Value does not match this control step')
  elif kind in ('text','select'):
   if not isinstance(value,str) or len(value)>row['max_length']:raise ValueError('Use text within the declared length')
   if kind=='select' and value not in row['options']:raise ValueError('Choose a declared enabled option')
  else:raise ValueError('This control is not directly writable')
  return copy.deepcopy(value)
 def command(self,body):
  if not isinstance(body,dict):raise ValueError('Provide a control command')
  ident=body.get('id');action=body.get('action','set')
  with self.lock:
   row=self.controls.get(ident)
   if row is None:raise ValueError('Control is not registered; open its engine page first')
   if row['mode']=='readonly':raise ValueError('This is a read-only output control')
   value=body.get('value')
   if action=='bit':
    if row['mode']!='set' or 'value' not in row:raise ValueError('Bit updates require a known writable value')
    raw=bytearray(encoded(row['value']));offset=body.get('offset');bit=body.get('bit')
    if type(offset)is not int or not 0<=offset<len(raw)*8 or type(bit)is not int or bit not in (0,1):raise ValueError('Use an in-range bit offset and bit 0 or 1')
    index=offset//8;mask=1<<(7-offset%8);raw[index]=(raw[index]|mask) if bit else (raw[index]&~mask)
    try:value=json.loads(raw.decode('utf-8'))
    except (UnicodeError,ValueError):raise ValueError('Bit update would break the serialized value')
   elif action not in ('set','request'):raise ValueError('Use set, bit or request')
   request=row['mode']=='request' or action=='request'
   if not request:value=self.validate(row,value)
   self.sequence+=1;command={'command_id':str(uuid.uuid4()),'sequence':self.sequence,'id':ident,'client':row['client'],'action':'request' if request else 'set','value':copy.deepcopy(value) if not request else None,'status':'awaiting-local-action' if request else 'queued','created':time.time()}
   if action=='bit':command['previous_value']=copy.deepcopy(row['value'])
   self.commands[command['command_id']]=command
   while len(self.commands)>512:self.commands.popitem(last=False)
   return self.receipt(command)
 @staticmethod
 def receipt(command):return {k:copy.deepcopy(command.get(k)) for k in ('command_id','sequence','id','action','status','created','result')}
 def poll(self,client):
  with self.lock:
   if client in self.clients:self.clients[client]=time.time()
   return {'commands':[copy.deepcopy(c) for c in self.commands.values() if c['client']==client and c['status'] in ('queued','awaiting-local-action') and time.time()-c['created']<300][-64:]}
 def acknowledge(self,body):
  with self.lock:
   c=self.commands.get(body.get('command_id'))
   if not c or c['client']!=body.get('client'):raise ValueError('Unknown command for this client')
   if c['status'] not in ('queued','awaiting-local-action'):return self.receipt(c)
   status=body.get('status')
   if status not in ('applied','rejected','locally-activated'):raise ValueError('Invalid control acknowledgment')
   row=self.controls.get(c['id'])
   if not row:raise ValueError('Control registration is no longer retained')
   if status=='applied':
    if c['action']!='set':raise ValueError('Action controls require local activation')
    actual=self.validate(row,body.get('value'))
    if encoded(actual)!=encoded(c['value']):raise ValueError('Applied value differs from requested value')
    row['value']=actual
   c['status']=status;c['result']=str(body.get('result',''))[:250]
   return self.receipt(c)
 def observe(self,body):
  with self.lock:
   row=self.controls.get(body.get('id'))
   if not row or row['client']!=body.get('client'):raise ValueError('Unknown control')
   if row['mode']=='set':row['value']=self.validate(row,body.get('value'))
   row['updated']=time.time()
   raw=encoded(row['value']) if row['mode']=='set' and 'value' in row else b'';return {'id':row['id'],'section':row['section'],'kind':row['kind'],'bytes':len(raw),'bits':len(raw)*8,'value_sha256':hashlib.sha256(raw).hexdigest() if raw else None,'processing_receipt':True}
 def inspect(self,ident):
  with self.lock:
   row=self.controls.get(ident)
   if not row:raise ValueError('Unknown registered control')
   raw=encoded(row['value']) if row['mode']=='set' and 'value' in row else b''
   return {'id':ident,'kind':row['kind'],'value':copy.deepcopy(row.get('value')) if raw else None,'encoding':'UTF-8 compact JSON; bit offsets are most-significant-bit first within each byte','serialized_hex':raw.hex(),'bits':len(raw)*8,'scope':'Registered control value only; no process memory or credentials'}
 def view(self,offset=0,limit=128):
  offset=max(0,int(offset));limit=max(0,min(256,int(limit)))
  with self.lock:return {'registered':len(self.controls),'mounted':sum(r['mounted'] and time.time()-self.clients.get(r['client'],0)<15 for r in self.controls.values()),'sections':sorted({r['section'] for r in self.controls.values()}),'controls':[{k:copy.deepcopy(v) for k,v in r.items() if k not in ('value','mounted')}|{'mounted':r['mounted'] and time.time()-self.clients.get(r['client'],0)<15} for r in list(self.controls.values())[offset:offset+limit]],'offset':offset,'next_offset':offset+limit if limit and offset+limit<len(self.controls) else None,'commands':[self.receipt(c) for c in list(self.commands.values())[-32:]],'scope':'Registered app controls and their serialized values, not arbitrary process memory. Unopened pages register when mounted. Action controls require their normal local activation.'}
