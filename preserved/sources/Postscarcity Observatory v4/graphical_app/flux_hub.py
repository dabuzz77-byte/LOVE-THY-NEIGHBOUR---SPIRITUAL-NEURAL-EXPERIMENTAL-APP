"""Live observation of real chiral byte transforms and the manuscript's flux grid."""
import hashlib
import json
import threading
import time
import uuid
from collections import OrderedDict, deque
from alignment_core import AlignmentInvariant, BitVector, RegisterLoop, STAGES
from chiral import rotate_byte, apply_chiral_mask
from manuscript_sources import ALIGNMENT_TEXT, FLUX_TEXT, SOURCE_MANIFEST
from sources import now, save_json

SEED = ['10101010101010', '01010101010101'] * 3
HELP = ['SEND <text>', 'BITS <0 and 1>', 'SHIFT <-32..32>', 'MODE ICE|FIREICE',
        'PAUSE', 'RESUME', 'STEP', 'RESET', 'STATUS', 'RUN ALL', 'RUN <module-id>',
        'INGEST <public https URL>', 'DEFINE <term>', 'ASM 2', 'ASM 1 <RDX> <RBX>']


class FluxHub:
    """Observe every processed bus chunk; only a bounded window is drawn on screen.

    Observer takes this lock under the bus lock. Never call the bus/runtime while
    holding this lock. No observed output is recursively reinserted into the bus.
    """
    def __init__(self, runtime):
        self.rt = runtime
        self.lock = threading.RLock()
        self.rows = SEED[:]
        self.previous = SEED[:]
        self.running = True
        self.mode = 'fireice'
        self.influence = 1
        self.generation = 0
        self.shift = 0
        self.bytes = self.chunks = self.changed = self.up = self.down = 0
        self.pattern_accepted = self.pattern_rejected = 0
        self.input_hash = hashlib.sha256()
        self.output_hash = hashlib.sha256()
        self.streams = OrderedDict()
        self.commands = deque(maxlen=20)
        self.pending = {}
        self.latest_stream = None
        self.last_alignment = None
        self.folder = runtime.data/'work'/'flux'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = runtime.data/'flux.json'
        try:
            saved=json.loads(self.path.read_text(encoding='utf-8'))
            self.configure({k:saved[k] for k in ('mode','running','influence') if k in saved})
        except (OSError,ValueError,TypeError):pass
        runtime.binary_bus.observer = self.observe

    def install_sources(self):
        """Retain complete manuscripts as reference data, never executable scripts."""
        for key, title, text, target in (
            ('manuscript-alignment','Cognition alignment · complete source',ALIGNMENT_TEXT,'expanded/WholeTextAlignment'),
            ('manuscript-flux','Run in place / flux · complete source',FLUX_TEXT,'expanded/RunInPlaceFlux')):
            item = {'id':key,'title':title,'text':text,'kind':'manuscript','url':'','requested_url':'',
                    'status':'ready','automatic':False,'created':now(),'retrieved':now(),
                    'next_fetch':0,'attempts':0,'error':None,'targets':[target],
                    'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(), 'authority':'Reference data only'}
            with self.rt.source_hub.lock:
                self.rt.source_hub.items[key] = item
                self.rt.source_hub.save()
            self.rt.source_hub.attach(key,item)
            self.rt.binary_bus.feed(key,text.encode('utf-8'))

    def observe(self, stream, raw, output, shift, complete, mask=None):
        """Called on actual processed bytes, including chunks of large frames."""
        changed = sum((a^b).bit_count() for a,b in zip(raw,output))
        up = sum(((~a)&b).bit_count() for a,b in zip(raw,output))
        inverse = (apply_chiral_mask(output,mask) if mask is not None else bytes(rotate_byte(v,-shift) for v in output)) == raw
        with self.lock:
            self.bytes += len(raw); self.chunks += 1
            self.changed += changed; self.up += up; self.down += changed-up
            self.input_hash.update(raw); self.output_hash.update(output)
            entry = self.streams.pop(stream, {'bytes':0,'chunks':0})
            entry.update(bytes=entry['bytes']+len(raw), chunks=entry['chunks']+1,
                input_bits=''.join(f'{v:08b}' for v in raw[:32]),
                output_bits=''.join(f'{v:08b}' for v in output[:32]),
                chunk_bytes=len(raw), changed_bits=changed, shift=shift if mask is None else None, inverse_verified=inverse,
                operation='predictive remain/flip' if mask is not None else 'chiral rotation',
                received=now(), stream=stream)
            self.streams[stream] = entry
            while len(self.streams)>128: self.streams.popitem(last=False)
            self.latest_stream = stream
            job = self.pending.get(stream)
            if job:
                job['_hash'].update(output)
                job['processed_bytes'] += len(raw)
                job['inverse_verified'] &= inverse
                job['shifts'] = list(dict.fromkeys(job['shifts']+[shift]))
                job['output_hex'] = (job['output_hex']+output.hex())[:512]
                job['output_bits'] = (job['output_bits']+''.join(f'{v:08b}' for v in output))[:512]
                job['output_sha256'] = job['_hash'].hexdigest()
                job['status'] = 'complete' if complete else 'processing'
                if complete:
                    if job.get('_expected_sha256'):
                        job['prediction_verified']=job['output_sha256']==job['_expected_sha256'] and job['inverse_verified']
                        if not job['prediction_verified']:job['status']='verification failed'
                    self.pending.pop(stream,None)

    def compact(self):
        with self.lock:
            return {'mode':self.mode,'running':self.running,'generation':self.generation,
                    'shift':self.shift,'observed_bytes':self.bytes,'changed_bits':self.changed,
                    'rows':self.rows[:], 'output_sha256':self.output_hash.hexdigest()}

    def view(self, stream=None):
        with self.lock:
            chosen = stream if stream in self.streams else self.latest_stream
            result = {**self.compact(), 'influence':self.influence,'previous':self.previous[:],
                'chunks':self.chunks,'zero_to_one':self.up,'one_to_zero':self.down,
                'input_sha256':self.input_hash.hexdigest(),'preview':dict(self.streams.get(chosen,{})),
                'streams':[{'id':key,'bytes':value['bytes']} for key,value in reversed(self.streams.items())],
                'pattern_accepted':self.pattern_accepted,'pattern_rejected':self.pattern_rejected,
                'commands':[{k:v for k,v in item.items() if not k.startswith('_')} for item in self.commands],
                'help':HELP, 'last_alignment':self.last_alignment}
        # Release flux lock first: the chiral observer holds the bus lock.
        result['bus'] = self.rt.binary_bus.state()
        result['carrier'] = self.rt.carrier()
        result['chiral_running'] = self.rt.config['chiral_running']
        return result

    def tick(self, force=False):
        with self.rt.lock: neural_shift = self.rt.chiral.shift
        backbone=getattr(self.rt,'backbone',None)
        offset=backbone.signal()['flux_offset'] if backbone else 0
        with self.lock:
            if not force and not self.running: return None
            self.previous = self.rows[:]
            self.shift = neural_shift + self.influence + offset if self.mode=='fireice' else 0
            self.rows = [self.rotate(row,self.shift if i%2==0 else -self.shift) for i,row in enumerate(self.rows)]
            self.generation += 1
            raw,padding = BitVector.pack(''.join(self.rows))
        accepted = self.rt.binary_bus.feed('flux-pattern',raw)
        with self.lock:
            if accepted:self.pattern_accepted += 1
            else:self.pattern_rejected += 1
        return {'status':'queued' if accepted else 'rejected','bytes':len(raw),'padding_bits':padding}

    @staticmethod
    def rotate(row, amount):
        amount %= len(row)
        return row[-amount:]+row[:-amount] if amount else row

    def configure(self, body):
        mode=body.get('mode'); running=body.get('running'); influence=body.get('influence')
        if mode is not None and mode not in ('ice','fireice'):raise ValueError('Choose ice or fireice')
        if running is not None and type(running) is not bool:raise ValueError('Running must be boolean')
        if influence is not None and (type(influence) is not int or not -32<=influence<=32):raise ValueError('Shift influence must be an integer from -32 to 32')
        with self.lock:
            if mode is not None:self.mode=mode
            if running is not None:self.running=running
            if influence is not None:self.influence=influence
            if body.get('reset') is True:self.rows=SEED[:];self.previous=SEED[:];self.generation=0
            save_json(self.path,{'mode':self.mode,'running':self.running,'influence':self.influence})
        return self.compact()

    def inject(self, value, mode='text', label=None, approved_bits=None):
        vector=BitVector(value,mode);raw,padding=BitVector.pack(vector.bits)
        mask=None;expected=None
        if approved_bits is not None:
            if padding or len(approved_bits)!=len(vector.bits) or set(approved_bits)-{'0','1'}:
                raise ValueError('Approved output must preserve complete bytes and target width')
            expected,_=BitVector.pack(approved_bits)
            mask=bytes(a^b for a,b in zip(raw,expected))
        key=uuid.uuid4().hex[:12];stream='flux-command:'+key
        job={'id':key,'command':label or ('BITS ' if mode=='bits' else 'SEND ')+value[:120],
            'created':now(),'status':'queued','stream':stream,'input_bits':vector.bits[:512],
            'input_sha256':hashlib.sha256(raw).hexdigest(),'input_bytes':len(raw),
            'bit_count':len(vector.bits),'padding_bits':padding,'processed_bytes':0,
            'output_hex':'','output_bits':'','output_sha256':None,'inverse_verified':True,'shifts':[],
            '_hash':hashlib.sha256(),
            'operation':'predictive remain/flip' if mask is not None else 'chiral rotation',
            'prediction_verified':False if mask is not None else None,
            '_expected_sha256':hashlib.sha256(expected).hexdigest() if expected is not None else None}
        with self.lock:
            if len(self.pending)>=20:raise ValueError('20 commands are waiting; resume chiral processing first')
            self.commands.append(job);self.pending[stream]=job
        accepted=self.rt.binary_bus.feed(stream,raw,mask=mask)
        with self.lock:
            if not accepted:job['status']='rejected';self.pending.pop(stream,None)
            return {k:v for k,v in job.items() if not k.startswith('_')}

    def command_receipt(self, key):
        with self.lock:
            job=next((j for j in self.commands if j['id']==key),None)
            return {k:v for k,v in job.items() if not k.startswith('_')} if job else None

    def command(self, body):
        text=body.get('command','')
        if not isinstance(text,str) or not text.strip() or len(text.encode('utf-8'))>33000:raise ValueError('Enter a command up to 33,000 bytes')
        head,_,tail=text.strip().partition(' ');head=head.upper();tail=tail.strip()
        if head in ('SEND','BITS'):return self.inject(tail,'bits' if head=='BITS' else 'text')
        if head=='SHIFT':result=self.configure({'influence':int(tail)})
        elif head=='MODE':result=self.configure({'mode':tail.lower()})
        elif head in ('PAUSE','RESUME'):result=self.configure({'running':head=='RESUME'})
        elif head=='RESET':result=self.configure({'reset':True})
        elif head=='STEP':
            result=self.tick(force=True)
            self.rt.chiral_step()
            result={**result,'status':'stepped','scope':'One flux frame and one shared chiral step; inspect queue counters for backlog.'}
        elif head=='STATUS':result=self.compact()
        elif head=='RUN':
            names=list(self.rt.modules) if tail.upper()=='ALL' else [tail]
            if any(n not in self.rt.modules for n in names):raise ValueError('Use RUN ALL or an exact module ID from the library')
            result={'scheduled':sum(self.rt.schedule(n) for n in names),'requested':len(names)}
        elif head=='INGEST':result=self.rt.source_hub.add('website',url=tail)
        elif head=='DEFINE':
            if not 1<=len(tail)<=160:raise ValueError('Supply a definition term up to 160 characters')
            key=tail.casefold()
            with self.rt.lock:
                self.rt.definitions.setdefault(key,{'term':tail,'modules':['expanded/RunInPlaceFlux'],'status':'pending','attempts':0,'next_fetch':0})
                self.rt.node('definition:'+key,tail,'definition')
                self.rt.edges.setdefault('definition:'+key+'|module:expanded/RunInPlaceFlux',.1)
                result={'term':tail,'status':self.rt.definitions[key]['status'],'scope':'Web lookup uses the existing ingestion and private-connection controls.'}
        elif head=='ASM':
            parts=[int(x,0) for x in tail.split()]
            if len(parts) not in (1,3):raise ValueError('Use ASM 2 or ASM 1 <RDX> <RBX>')
            result=RegisterLoop().run(*parts)
        else:raise ValueError('Unknown local command. Use SEND followed by text, or one of the commands shown below.')
        job={'id':uuid.uuid4().hex[:12],'created':now(),'command':text[:160],'status':'executed','result':result}
        with self.lock:self.commands.append(job)
        self.rt.binary_bus.feed('flux-control',job)
        return job

    def alignment(self, body):
        result=AlignmentInvariant().evaluate({**body,'predictive_context':self.rt.virtue.receipts()})
        if body.get('apply') is True and not result['castback_allowed']:
            raise ValueError('Run this exact input through Predictive virtue first; only a resolved, rechecked result can be sent')
        receipt={'id':uuid.uuid4().hex[:12],'created':now(),**result,'sent':False}
        if body.get('apply') is True:
            receipt['bus_receipt']=self.inject(result['output_bits'],'bits','Alignment castback')
            receipt['sent']=receipt['bus_receipt']['status']!='rejected'
        save_json(self.folder/(receipt['id']+'.json'),receipt)
        with self.lock:self.last_alignment={k:v for k,v in receipt.items() if k not in ('input_bits','output_bits')}
        return receipt

    def manuscripts(self):
        return {'alignment':ALIGNMENT_TEXT,'flux':FLUX_TEXT,'manifest':SOURCE_MANIFEST,'stages':list(STAGES),
                'definitions':AlignmentInvariant().definitions,
                'scope':'Complete source preserved. Bit rules, local data transport and finite register arithmetic execute. Dimensional/ether language labels graphics; native injection and banking-breach directives remain non-executable source annotations.'}
