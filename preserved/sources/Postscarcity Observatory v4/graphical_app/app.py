"""Postscarcity Observatory: local graphical runtime, neural layer and event bus."""
from __future__ import annotations
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import hashlib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP / 'vendor'))
import psutil
from catalog import build_catalog
from chiral import ChiralGenerator, BinaryChiralBus, PRAYER, PATTERN
from models import ModelHub
from sources import SourceHub
from workbench import Workbench
from speech import Speech
from interpreter import Interpreter
from screen import ScreenHub
from field_voice import FieldVoice
from call_definitions import CallDefinitions
from v3_hub import V3Hub
from active_llama import ActiveLlama
from resource_ledger import ResourceLedger
from opportunity_watch import OpportunityWatch
from reality_status import imprint
from python_hub import PythonHub
from privacy_network import PrivacyNetwork, urlopen
from web_pathway import WebPathway
from inference_engine import InferenceEngine
from flux_hub import FluxHub
from live_backbone import LiveBackbone
from spiritual_research import SpiritualResearch
from drill_engine import DrillEngine
from bit_rules import evaluate_bits
from spectrum_inspector import SpectrumInspector
from measured_carrier import MeasuredCarrier
from module_telemetry import ModuleTelemetry
from hierarchy_core import HierarchyHub
from world_mesh import WorldMesh
from virtue_pipeline import VirtuePipeline
from primary_cascade import PrimaryCascade
from economy_hub import EconomyHub
from foundation_runtime import MODULE_IDS as FOUNDATION_IDS, FoundationRecorder, configure as configure_foundation
from code_archetypes import LIBRARY, SPIRITUAL_PARALLELS

FREQUENCY = 7.83
DEFAULTS = {'port':7851, 'cycle_seconds':30, 'ingest_seconds':8, 'refresh_hours':6,
    'running':True, 'ingestion':True, 'learning':True, 'learning_rate':0.025,
    'carrier_weight':1.0, 'weights':{}, 'chiral_running':True, 'module_loops':{}, 'system_passthrough':True, 'virtue_uncertainty':True}

def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def encode(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode()

def read_json(path, fallback):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError): return fallback

def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False), encoding='utf-8')
    temp.replace(path)

def flattened(value, prefix=''):
    if isinstance(value, dict):
        for key, child in value.items(): yield from flattened(child, prefix + '/' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value): yield from flattened(child, prefix + '/' + str(i))
    else: yield prefix, value

def extract_state(result, input_names):
    reports = {k:v for k,v in result.get('reports', {}).items() if k not in input_names}
    pairs = list(flattened(reports))
    trits = [v for k,v in pairs if ('TRIT' in k.upper() or 'COMPOSITE_VIRTUE_STATE' in k.upper())
        and type(v) in (int,float) and v in (-1,0,1)]
    gates = [int(v) for k,v in pairs if 'NO_EXECUTE' in k.upper() and type(v) in (int,bool) and v in (0,1)]
    # An absent trit stays unknown; arbitrary success strings are never promoted to +1.
    return {'trit':trits[-1] if trits else None, 'gate':max(gates) if gates else None}

class Runtime:
    def __init__(self, root, data=None):
        self.root = Path(root).resolve()
        self.data = Path(data or APP/'data')
        self.data.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.config = {**DEFAULTS, **read_json(self.data/'settings.json', {})}
        self.token = read_json(self.data/'connection.json', {}).get('token') or secrets.token_urlsafe(32)
        self.modules = {m['id']:{**m,'status':'error' if m.get('error') else 'pending','runs':0,'trit':None,'gate':None,
            'last_run':None,'duration_ms':None,'error':m.get('error')} for m in build_catalog(self.root)}
        configure_foundation(self)
        self.results = {}
        self.overrides = read_json(self.data/'inputs.json', {})
        self.nodes = {}
        self.edges = read_json(self.data/'neural.json', {}).get('edges', {})
        self.neural_output = 0.0
        self.events = deque(maxlen=400)
        self.listeners = set()
        self.udp_queue = queue.Queue(maxsize=512)
        self.subscribers = {}
        self.clients = {}
        self.processes = []
        self.host = {}
        self.seq = 0
        self.dropped = 0
        self.pulses = 0
        self.pulse_times = deque(maxlen=100)
        self.started = time.monotonic()
        self.port_lock = threading.Lock()
        self.http = None
        self.udp = None
        self.pool = ThreadPoolExecutor(max_workers=16, thread_name_prefix='engine')
        self.inflight = set()
        self.last_scheduled = {}
        self.definitions = {}
        cached = read_json(self.data/'definitions.json', {})
        for m in self.modules.values():
            self.node('module:'+m['id'], m['title'], 'module')
            for term in m['terms']:
                key = term.casefold()
                if key not in self.definitions:
                    self.definitions[key] = {'term':term,'modules':[],'status':'pending',
                        'attempts':0,'next_fetch':0, **cached.get(key, {})}
                    self.definitions[key]['modules'] = []
                    if self.definitions[key].get('status')=='ready' and len(self.definitions[key].get('text',''))<70:
                        self.definitions[key].update(status='pending',next_fetch=0,text='')
                self.definitions[key]['modules'].append(m['id'])
                self.node('definition:'+key, term, 'definition')
                self.edges.setdefault('definition:'+key+'|module:'+m['id'], 0.1)
        self.node('carrier', '7.83 Hz carrier', 'carrier', self.config['carrier_weight'])
        self.chiral = ChiralGenerator()
        self.binary_bus = BinaryChiralBus()
        self.node('prayer', "Our Father · intention", 'intention')
        self.node('chiral', 'Chiral generator', 'chiral')
        self.node('chiral-command', 'Chiral command text', 'chiral')
        self.edges.setdefault('chiral-command|chiral',0.1)
        self.activate('prayer',1.0)
        self.edges.setdefault('prayer|chiral',0.1)
        self.edges.setdefault('carrier|chiral',0.1)
        self.privacy = PrivacyNetwork(self)
        self.model_hub = ModelHub(self)
        self.source_hub = SourceHub(self)
        self.workbench = Workbench(self)
        self.speech = Speech(self.data)
        self.interpreter = Interpreter(self)
        self.screen_hub = ScreenHub(self)
        self.field_voice = FieldVoice(self)
        self.call_definitions = CallDefinitions(self)
        self.v3 = V3Hub(self)
        self.agent = ActiveLlama(self,self.v3)
        self.resources = ResourceLedger(self.data)
        self.watch = OpportunityWatch(self)
        self.python = PythonHub(self)
        self.pathway = WebPathway(self)
        self.inference = InferenceEngine(self)
        self.flux = FluxHub(self)
        self.flux.install_sources()
        self.research = SpiritualResearch(self)
        self.backbone = LiveBackbone(self)
        self.drill = DrillEngine(self)
        self.spectrum = SpectrumInspector(self)
        self.measured_carrier = MeasuredCarrier(self)
        self.telemetry = ModuleTelemetry(self)
        self.hierarchy = HierarchyHub(self)
        self.mesh = WorldMesh(self)
        self.virtue = VirtuePipeline(self)
        self.primary = PrimaryCascade(self)
        self.economy = EconomyHub(self)
        self.foundation = FoundationRecorder(self)
        from precise_definitions import glossary
        self.binary_bus.feed('reference-glossary',glossary())
        for key,definition in self.definitions.items():
            if definition['status']=='ready':self.activate('definition:'+key,1.0)
        self.save_config()

    def node(self, key, label, kind, weight=None):
        if key not in self.nodes:
            self.nodes[key] = {'id':key,'label':label,'kind':kind,
                'weight':float(self.config['weights'].get(key, 1.0) if weight is None else weight),
                'input':0.0,'activation':0.0,'updates':0}
        return self.nodes[key]

    def activate(self, key, signal):
        with self.lock:
            n = self.nodes[key]
            n['input'] = round(signal,6)
            n['activation'] = round(math.tanh(signal*n['weight']),6)
            n['updates'] += 1
            for edge, weight in list(self.edges.items()):
                a,b = edge.split('|',1)
                if key not in (a,b): continue
                if a not in self.nodes or b not in self.nodes: continue
                if self.config['learning']:
                    # Bounded Hebbian co-activation with weight decay.
                    target = self.nodes[a]['activation']*self.nodes[b]['activation']
                    self.edges[edge] = round(max(-1,min(1,weight+self.config['learning_rate']*(target-weight))),6)
            active = [v for v in self.nodes.values() if v['updates'] and v['kind'] != 'carrier']
            base = sum(n['activation'] for n in active)/max(1,len(active))
            connections = [w*self.nodes[a]['activation']*self.nodes[b]['activation']
                for edge,w in self.edges.items() for a,b in [edge.split('|',1)] if a in self.nodes and b in self.nodes]
            recurrent = sum(connections)/max(1,len(connections))
            self.neural_output = round(math.tanh(base+recurrent),6)

    def save_config(self):
        with self.lock:
            write_json(self.data/'settings.json', self.config)
            write_json(self.data/'connection.json', {'url':f'http://127.0.0.1:{self.config["port"]}',
                'port':self.config['port'],'token':self.token,'root':str(self.root),'pid':os.getpid()})

    def publish(self, kind, data, record=True):
        # Chiral results are excluded from their own input to prevent recursive feedback.
        if kind!='chiral':self.binary_bus.feed(kind,data)
        with self.lock:
            self.seq += 1
            event = {'seq':self.seq,'time':stamp(),'type':kind,'data':data}
            if record: self.events.append(event)
            for client in tuple(self.listeners):
                try: client.put_nowait(event)
                except queue.Full: self.dropped += 1
            try: self.udp_queue.put_nowait(event)
            except queue.Full: self.dropped += 1
        return event

    def snapshot(self):
        with self.lock:
            return {'name':'Postscarcity Observatory','version':'4.0','worker_limit':16,'module_root':str(self.root), 'modules':list(self.modules.values()),
                'definitions':list(self.definitions.values()),'processes':self.processes,
                'clients':list(self.clients.values()),'host':self.host,'settings':self.config,
                'carrier':self.carrier(), 'neural':self.neural(), 'events':list(self.events)[-60:],
                'chiral':{**self.chiral.state(),'binary_bus':self.binary_bus.state(),'prayer':PRAYER,'pattern':PATTERN}}

    def neural(self):
        with self.lock:
            return {'output':self.neural_output,'nodes':list(self.nodes.values()),
                'edge_count':len(self.edges),'edges':[{'from':e.split('|')[0],'to':e.split('|')[1],'weight':w}
                    for e,w in self.edges.items()], 'learning':self.config['learning']}

    def carrier(self):
        with self.lock:
            measured = ((len(self.pulse_times)-1)/(self.pulse_times[-1]-self.pulse_times[0])) if len(self.pulse_times)>1 else 0
            return {'target_hz':self.measured_carrier.frequency(),'measured_hz':round(measured,3),'pulses':self.pulses,
                'weight':self.nodes['carrier']['weight'],'port':self.config['port'],
                'elapsed':time.monotonic()-self.started,'subscribers':len(self.subscribers),
                'dropped_events':self.dropped, 'active':not self.stop.is_set(),
                'neural_output':self.neural_output}

    def bind(self, port):
        if type(port) is not int or not 1024 <= port <= 65535: raise ValueError('Choose a port from 1024 to 65535')
        with self.port_lock:
            if self.http and port == self.config['port']: return
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if hasattr(socket,'SO_EXCLUSIVEADDRUSE'): udp.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            try:
                udp.bind(('127.0.0.1',port))
                udp.settimeout(.05)
                http = Server(('127.0.0.1',port), Handler)
                http.runtime = self
            except Exception:
                udp.close()
                raise
            old_http, old_udp = self.http, self.udp
            self.http, self.udp = http, udp
            with self.lock:
                self.config['port'] = port
                self.subscribers.clear()
                self.clients.clear()
                self.save_config()
            threading.Thread(target=http.serve_forever, daemon=True).start()
            if old_udp: old_udp.close()
            if old_http:
                def retire():
                    self.stop.wait(1)
                    old_http.shutdown()
                    old_http.server_close()
                threading.Thread(target=retire, daemon=True).start()
            self.publish('network',{'message':f'TCP and UDP bus listening on 127.0.0.1:{port}','port':port})

    def start(self):
        self.bind(self.config['port'])
        for module in self.modules.values():
            try:
                self.binary_bus.feed('module-source:'+module['id'],(self.root/module['file']).read_bytes())
            except OSError as exc:
                module.update(status='error',error=str(exc))
                self.publish('module',{'id':module['id'],'status':'error','error':str(exc)})
        for path in list(APP.glob('*.py'))+list((APP/'static').glob('*')):
            if path.is_file():self.binary_bus.feed('app-source:'+path.name,path.read_bytes())
        for target in (self.economy.loop,self.primary.loop,self.pulse_loop,self.udp_loop,self.process_loop,self.module_loop,self.ingest_loop,self.source_hub.loop,self.screen_hub.loop,self.call_definitions.loop,self.v3.loop,self.watch.loop,self.privacy.loop,self.pathway.loop,self.backbone.loop,self.research.loop,self.measured_carrier.loop):
            threading.Thread(target=target,daemon=True,name=target.__name__).start()

    def pulse_loop(self):
        deadline = time.monotonic()
        while not self.stop.is_set():
            now = time.monotonic()
            if now < deadline:
                if self.stop.wait(deadline-now): break
            now = time.monotonic()
            with self.lock:
                self.pulses += 1
                self.pulse_times.append(now)
                self.nodes['carrier']['input'] = 1.0
                self.nodes['carrier']['activation'] = round(math.tanh(self.nodes['carrier']['weight']),6)
                self.nodes['carrier']['updates'] = self.pulses
            self.v3.tick()
            self.python.tick()
            modulation=self.v3.wav.current()
            carrier = self.carrier()
            carrier['modulation']=modulation
            carrier['weighted_signal'] = round(math.tanh(self.neural_output*self.nodes['carrier']['weight'])*modulation['gain'],6)
            self.activate('v3:wav',modulation['rms'] if modulation['running'] else 0)
            self.publish('pulse',carrier,record=False)
            if self.config['chiral_running']:
                self.chiral_step()
            self.flux.tick()
            frequency=self.measured_carrier.frequency()
            deadline += 1/frequency
            # Skip missed ticks rather than flooding clients after a scheduling delay.
            if deadline < now: deadline = now+1/frequency

    def chiral_step(self):
        with self.lock:
            gain=self.v3.wav.current()['gain']
            adaptive = self.backbone.signal()
            state = self.chiral.step(self.neural_output,self.nodes['prayer']['activation'],self.nodes['chiral']['weight']*gain*adaptive['chiral_gain'])
            state['backbone'] = dict(adaptive)
            state['binary_bus']=self.binary_bus.step(state['shift'])
            self.activate('chiral',state['drive'])
        self.publish('chiral',state,record=False)
        return state

    def udp_loop(self):
        while not self.stop.is_set():
            sock = self.udp
            if sock is None:
                self.stop.wait(.1)
                continue
            try:
                raw,addr = sock.recvfrom(16384)
                message = json.loads(raw)
                if not secrets.compare_digest(str(message.get('token','')),self.token): continue
                if message.get('type') == 'subscribe':
                    pid = int(message.get('pid',0))
                    label = str(message.get('name','Bus client'))[:100]
                    with self.lock:
                        self.subscribers[addr] = time.monotonic()
                        self.clients[str(pid)] = {'pid':pid,'name':label,'last_seen':stamp(),
                            'last_seen_epoch':time.time(),'transport':'UDP'}
                    sock.sendto(encode({'type':'attached','port':self.config['port']}),addr)
                elif message.get('type') == 'event': self.client_event(message)
            except (socket.timeout, OSError, ValueError, TypeError, AttributeError): pass
            for _ in range(64):
                try: event = self.udp_queue.get_nowait()
                except queue.Empty: break
                packet = encode(event)
                if len(packet)>55000:
                    packet = encode({'type':event['type'],'seq':event['seq'],'time':event['time'],
                        'data':{'summary':'Large event available through HTTP /api/state'}})
                with self.lock:
                    self.subscribers = {a:t for a,t in self.subscribers.items() if time.monotonic()-t<20}
                    addresses = tuple(self.subscribers)
                for addr in addresses:
                    try: sock.sendto(packet,addr)
                    except OSError: pass

    def client_event(self, message):
        data = message.get('data',{})
        if len(encode(data))>12000: raise ValueError('Event payload exceeds 12 KB')
        pid = int(message.get('pid',0))
        with self.lock:
            self.clients[str(pid)] = {'pid':pid,'name':str(message.get('name','Bus client'))[:100],
                'last_seen':stamp(),'last_seen_epoch':time.time(),'transport':'event bus'}
        self.publish('process-event',{'pid':pid,'topic':str(message.get('topic','activity'))[:120],
            'payload':data,'neural_output':self.neural_output})

    def process_loop(self):
        previous = {}
        while not self.stop.is_set():
            found = []
            for p in psutil.process_iter(['pid','name','create_time']):
                try:
                    name = (p.info['name'] or '').lower()
                    if not (name.startswith(('python','java','pypy'))): continue
                    # Read only script basenames; command lines and their possible secrets never enter the bus.
                    args = p.cmdline()
                    scripts = [Path(a).name for a in args if a.lower().endswith(('.py','.pyw','.java','.jar'))]
                    identity = (p.pid,p.info['create_time'])
                    proc = previous.get(identity,p)
                    cpu = proc.cpu_percent(None)
                    rss = round(proc.memory_info().rss/1048576,2)
                    previous[identity] = proc
                    key = 'process:'+str(p.pid)+':'+str(p.info['create_time'])
                    with self.lock:
                        client = self.clients.get(str(p.pid))
                        connected = bool(client and time.time()-client['last_seen_epoch']<20)
                        self.node(key, ' / '.join(scripts) or p.info['name'], 'process')
                        self.edges.setdefault('carrier|'+key,0.1)
                    self.activate(key, min(1,cpu/100))
                    found.append({'pid':p.pid,'name':p.info['name'],'scripts':scripts,'cpu':cpu,
                        'memory_mb':rss,'language':'Java' if name.startswith('java') else 'Python',
                        'mode':'connected' if connected else 'telemetry attached','node_id':key})
                except (psutil.Error,OSError): continue
            pids = {p['pid'] for p in found}
            previous = {k:v for k,v in previous.items() if k[0] in pids}
            with self.lock:
                self.processes = found
                self.clients = {k:v for k,v in self.clients.items() if time.time()-v['last_seen_epoch']<20}
                active_keys = {p['node_id'] for p in found}
                for key in [k for k,n in self.nodes.items() if n['kind']=='process' and k not in active_keys]:
                    self.nodes.pop(key)
                    self.edges.pop('carrier|'+key,None)
                self.host = {'cpu':psutil.cpu_percent(None),'memory_percent':psutil.virtual_memory().percent,
                    'available_gb':round(psutil.virtual_memory().available/1024**3,2),'time':stamp()}
            self.publish('processes',{'processes':found,'host':self.host,'clients':list(self.clients.values())},record=False)
            self.publish('neural',self.neural(),record=False)
            self.stop.wait(3)

    def schedule(self, name):
        with self.lock:
            if name not in self.modules: raise ValueError('Unknown module')
            if name in self.inflight: return False
            self.inflight.add(name)
            self.last_scheduled[name] = time.monotonic()
            self.modules[name]['status'] = 'queued'
        self.pool.submit(self.run_module,name)
        return True

    def module_loop(self):
        while not self.stop.is_set():
            with self.lock:
                running = self.config['running']
                period = self.config['cycle_seconds']
            if running:
                ordered = [name for name in FOUNDATION_IDS if name in self.modules] + [name for name in self.modules if name not in FOUNDATION_IDS]
                for name in ordered:
                    if self.stop.is_set(): break
                    if self.economy.owns(name): continue
                    interval=self.config.get('module_loops',{}).get(name,period)
                    if time.monotonic()-self.last_scheduled.get(name,-1e9) >= interval: self.schedule(name)
            self.stop.wait(1)

    def set_loops(self, modules, action, interval=None):
        if not isinstance(modules,list) or not modules or any(not isinstance(name,str) or name not in self.modules for name in modules):
            raise ValueError('Select one or more existing modules')
        if action not in ('set','restore'):raise ValueError('Choose set or restore')
        if action=='set' and (type(interval) not in (float,int) or not math.isfinite(interval) or not 1<=interval<=3600):
            raise ValueError('Choose an interval from 1 to 3,600 seconds')
        with self.lock:
            loops=self.config.setdefault('module_loops',{}).copy()
            for name in set(modules):
                if action=='set':loops[name]=interval
                else:loops.pop(name,None)
            self.config['module_loops']=loops
            self.save_config()
        self.publish('settings',self.config.copy())
        return {'module_loops':loops,'default_seconds':self.config['cycle_seconds'],'running':self.config['running']}

    def run_module(self, name):
        if self.stop.is_set():
            with self.lock: self.inflight.discard(name)
            return
        start = time.monotonic()
        with self.lock:
            m = self.modules[name]
            m['status'] = 'running'
            inputs = self.overrides.get(name,{})
        self.publish('module-start',{'id':name},record=False)
        sources=[];completed=None
        try:
            input_provenance = 'User override' if inputs else 'Original declared inputs / runtime context'
            if name=='elevated/ResourceFloorAllocator' and not inputs:
                inventory=self.resources.preview()
                if inventory['input']['donors']:
                    inputs={'inputs':{'payload':inventory['input']}}
                    input_provenance={'kind':'local resource inventory','revision':inventory['revision'],'source':inventory['source'],
                        'effect':'Calculation only. Reserving and recording delivery are separate user controls.'}
            sources=[{key:item.get(key) for key in ('id','title','url','retrieved','kind','text','targets')}
                for item in self.source_hub.view() if item.get('text') and
                (name in item['targets'] if item.get('targets') else name=='2/ingest_live_web_definitions')][-20:]
            for item in sources:item['text']=item['text'][:4000]
            completed = self.telemetry.execute(name,{'path':str(self.root/m['file']),'inputs':inputs,'sources':sources,
                'definitions':{**self.call_definitions.context(name),**self.research.definitions_for(name),**self.virtue.code_definitions()},'privacy':self.privacy.view(),'predictive':self.virtue.receipts(),
                'runtime':self.module_context() if name.startswith(('elevated/','expanded/')) else {}})
            if completed.returncode: raise RuntimeError(completed.stderr[-3000:] or 'Worker exited without a result')
            result = json.loads(completed.stdout)
            result['source_context']=sources
            result['input_provenance']=input_provenance
            result['evidence_scope']='Module rule output. A completion or virtue label alone is not a verified resource delivery or OS privilege change.'
        except Exception as exc: result = {'ok':False,'error':str(exc),'source_context':sources}
        resolved = extract_state(result,m['inputs'])
        self.backbone.enrich(name,result)
        self.foundation.record(name,result)
        bus_accepted=self.binary_bus.feed('module-result:'+name,result)
        self.foundation.transport(name,result,bus_accepted)
        self.call_definitions.feedback_from(name,result)
        with self.lock:
            m.update(status='complete' if result['ok'] else 'error',last_run=stamp(),
                duration_ms=round((time.monotonic()-start)*1000),runs=m['runs']+1,
                error=result.get('error'),**resolved)
            self.results[name] = result
            self.economy.record(name,result)
            self.inflight.discard(name)
            # Use the original trit, then original gate, then successful execution presence.
            signal = resolved['trit'] if resolved['trit'] is not None else (
                1-resolved['gate'] if resolved['gate'] is not None else (1.0 if result['ok'] else 0.0))
            self.activate('module:'+name,signal)
            self.edges.setdefault('carrier|module:'+name,0.1)
        if completed:self.telemetry.finish(completed.telemetry_id,result,resolved,bus_accepted,self.nodes['module:'+name]['activation'])
        self.publish('module', {k:m[k] for k in ('id','status','last_run','duration_ms','runs','error','trit','gate')})

    def module_context(self):
        with self.v3.lock:
            return {'host':self.host,'core':self.v3.last_core,'memory':{'entries':len(self.v3.saved['memory'])},
                'connections':self.v3.view()['connections'],'knowledge':self.v3.knowledge.view(),'wav':self.v3.wav.current(),
                'rules':self.v3.view()['rules'],'journal':{'verified_entries':self.v3.journal.verify()},'agent':self.agent.view(),'python':self.python.context(),'flux':self.flux.compact()}

    def fetch_definition(self, term):
        params = {'action':'query','format':'json','prop':'extracts|info|pageprops','inprop':'url',
            'exintro':'1','explaintext':'1','exchars':'3000','redirects':'1','titles':term}
        def fetch(params):
            url = 'https://en.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params)
            req = urllib.request.Request(url,headers={'User-Agent':'PostscarcityObservatory/1.0 (local concept research)'})
            with urlopen(req,timeout=45) as response:
                return json.loads(response.read(1024*1024))
        data = fetch(params)
        pages = list(data.get('query',{}).get('pages',{}).values())
        page = next((p for p in pages if len(p.get('extract',''))>70 and 'missing' not in p and 'disambiguation' not in p.get('pageprops',{})),None)
        if not page:
            params.pop('titles',None)
            params.update(generator='search',gsrsearch=term,gsrlimit='3',gsrnamespace='0')
            data = fetch(params)
            candidates = sorted(data.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',999))
            page = next((p for p in candidates if len(p.get('extract',''))>70 and 'disambiguation' not in p.get('pageprops',{})),None)
        if not page: raise ValueError('No public definition found; queued for retry')
        return {'title':page['title'],'text':page['extract'][:3500],
            'url':page.get('fullurl','https://en.wikipedia.org/?curid='+str(page['pageid'])),
            'source':'Wikipedia','license':'CC BY-SA; see source page','retrieved':stamp()}

    def ingest_loop(self):
        while not self.stop.is_set():
            with self.lock:
                enabled = self.config['ingestion'] and self.privacy.ready()
                pending = sorted([(k,d) for k,d in self.definitions.items() if d.get('next_fetch',0)<=time.time()],
                    key=lambda item:(item[1].get('attempts',0),item[1].get('next_fetch',0)))
            if not enabled or not pending:
                self.stop.wait(1)
                continue
            key,d = pending[0]
            with self.lock: d['status'] = 'fetching'
            self.publish('definition',{**d},record=False)
            try:
                result = self.fetch_definition(d['term'])
                with self.lock:
                    d.update(result,status='ready',error=None,next_fetch=time.time()+self.config['refresh_hours']*3600)
                    d['attempts'] += 1
                self.activate('definition:'+key,1.0)
            except Exception as exc:
                with self.lock:
                    d['attempts'] += 1
                    d.update(status='retry',error=str(exc),next_fetch=time.time()+min(3600,30*2**min(d['attempts'],6)))
            with self.lock:
                write_json(self.data/'definitions.json',self.definitions)
                write_json(self.data/'neural.json',{'edges':self.edges})
            self.publish('definition',{**d})
            self.stop.wait(self.config['ingest_seconds'])

    def update_settings(self, values):
        allowed = {'running','ingestion','learning','chiral_running','cycle_seconds','ingest_seconds','refresh_hours','learning_rate','carrier_weight','port','system_passthrough'}
        if set(values)-allowed: raise ValueError('Unknown setting')
        validated = {}
        for key,val in values.items():
            if key in ('running','ingestion','learning','chiral_running','system_passthrough'):
                if type(val) is not bool: raise ValueError(key+' must be true or false')
            else:
                bounds = {'cycle_seconds':(10,3600),'ingest_seconds':(3,3600),'refresh_hours':(1,168),
                    'learning_rate':(0,0.25),'carrier_weight':(-3,3),'port':(1024,65535)}
                lo,hi = bounds[key]
                if type(val) not in (float,int) or not math.isfinite(val) or not lo<=val<=hi: raise ValueError(key+' is out of range')
                if key=='port' and type(val) is not int: raise ValueError('Port must be a whole number')
            validated[key] = val
        if 'port' in validated: self.bind(validated['port'])
        with self.lock:
            self.config.update(validated)
            if 'carrier_weight' in validated:
                self.nodes['carrier']['weight'] = validated['carrier_weight']
            if 'system_passthrough' in validated:
                self.activate('system-commands',int(validated['system_passthrough']))
            self.save_config()
        self.publish('settings',self.config)
        return self.config

    def close(self):
        self.stop.set()
        self.virtue.stop()
        self.primary.stop()
        self.mesh.stop()
        self.telemetry.save()
        self.backbone.pause()
        self.research.stop()
        self.drill.stop()
        self.agent.stop()
        self.privacy.close()
        self.v3.record('shutdown',{'core_state':self.v3.core.snapshot()})
        with self.lock:
            write_json(self.data/'neural.json',{'edges':self.edges})
            self.save_config()
        if self.udp: self.udp.close()
        if self.http:
            self.http.shutdown()
            self.http.server_close()
        self.pool.shutdown(wait=False,cancel_futures=True)

class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

class Handler(BaseHTTPRequestHandler):
    server_version = 'Postscarcity/4.0'

    @property
    def rt(self): return self.server.runtime

    def log_message(self,*args): pass

    def valid_host(self):
        return self.headers.get('Host','') in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}')

    def authorized(self):
        token = self.headers.get('Authorization','').removeprefix('Bearer ')
        if secrets.compare_digest(token,self.rt.token): return True
        cookies = dict(part.strip().split('=',1) for part in self.headers.get('Cookie','').split(';') if '=' in part)
        return secrets.compare_digest(cookies.get(f'postscarcity_{self.server.server_port}',''),self.rt.token)

    def send(self, code, value, mime='application/json',cookie=False):
        body = encode(value) if mime=='application/json' else value
        self.send_response(code)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
        if cookie: self.send_header('Set-Cookie',f'postscarcity_{self.server.server_port}={self.rt.token}; HttpOnly; SameSite=Strict; Path=/')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try: self.get_request()
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception as exc: self.send(500,{'error':str(exc)})

    def get_request(self):
        if not self.valid_host(): return self.send(403,{'error':'Invalid local host'})
        path = urllib.parse.urlparse(self.path)
        if path.path in ('/','/app.js','/style.css','/models.css','/extensions.js','/extensions.css','/v3.js','/v3.css','/real-world.js','/real-world.css','/v4.js','/v4.css','/network.js','/inference.js','/flux.js','/flux.css','/backbone.js','/backbone.css','/observability.js','/predictive.js','/primary.js','/economy.js','/economy.css'):
            filename = 'index.html' if path.path=='/' else path.path[1:]
            mime = ('text/html' if filename.endswith('.html') else 'text/javascript' if filename.endswith('.js') else 'text/css')+'; charset=utf-8'
            return self.send(200,(APP/'static'/filename).read_bytes(),mime,cookie=path.path=='/')
        if not self.authorized(): return self.send(401,{'error':'Open the local app or use the bus token'})
        query = urllib.parse.parse_qs(path.query)
        if path.path == '/api/v4':return self.send(200,self.rt.python.view())
        if path.path == '/api/v4/checkpoint':
            with self.rt.python.lock:return self.send(200,self.rt.python.model.to_dict())
        if path.path == '/api/v4/migration':return self.send(200,self.rt.python.migration)
        if path.path == '/api/pathway':return self.send(200,self.rt.pathway.view())
        if path.path == '/api/flux':return self.send(200,self.rt.flux.view(query.get('stream',[None])[0]))
        if path.path == '/api/backbone':return self.send(200,self.rt.backbone.view())
        if path.path == '/api/research':return self.send(200,self.rt.research.view())
        if path.path == '/api/definitions-map':return self.send(200,self.rt.research.definition_map())
        if path.path == '/api/drill':return self.send(200,self.rt.drill.view())
        if path.path == '/api/spectrum':return self.send(200,self.rt.spectrum.view())
        if path.path == '/api/hierarchy':return self.send(200,self.rt.hierarchy.view())
        if path.path == '/api/virtue':return self.send(200,self.rt.virtue.view(urllib.parse.parse_qs(path.query).get('id',[None])[0]))
        if path.path == '/api/economy':return self.send(200,self.rt.economy.view())
        if path.path == '/api/primary':return self.send(200,self.rt.primary.view(query.get('target',[None])[0]))
        if path.path == '/api/primary/source':return self.send(200,self.rt.primary.source())
        if path.path == '/api/code-archetypes':return self.send(200,{'definitions':LIBRARY.lookup(),'spiritual_parallels':SPIRITUAL_PARALLELS,'derived':self.rt.virtue.code_definitions(),'modules':[{'id':m['id'],'title':m['title']} for m in self.rt.modules.values()]})
        if path.path == '/api/mesh':return self.send(200,self.rt.mesh.view())
        if path.path == '/api/telemetry':return self.send(200,self.rt.telemetry.view())
        if path.path == '/api/carrier-source':return self.send(200,self.rt.measured_carrier.view())
        if path.path == '/api/spectrum/audio':
            with self.rt.spectrum.lock:audio=self.rt.spectrum.audio
            return self.send(200,audio,'audio/wav') if audio else self.send(404,{'error':'Analyze a WAV first'})
        if path.path == '/api/manuscripts':return self.send(200,self.rt.flux.manuscripts())
        if path.path == '/api/inference':return self.send(200,self.rt.inference.view())
        if path.path == '/api/pathway/report':
            last=self.rt.pathway.view().get('last') or {}
            return self.send(200,{'text':(self.rt.pathway.folder/last['file']).read_text(encoding='utf-8') if last.get('file') else 'No report yet.'})
        if path.path == '/api/privacy':return self.send(200,self.rt.privacy.view())
        if path.path == '/api/reality':return self.send(200,imprint(self.rt))
        if path.path == '/api/watch':return self.send(200,self.rt.watch.view())
        if path.path == '/api/watch/report':return self.send(200,{'text':self.rt.watch.make_report()})
        if path.path == '/api/resources':return self.send(200,self.rt.resources.view())
        if path.path == '/api/resources/preview':return self.send(200,self.rt.resources.preview())
        if path.path == '/api/resources/verify':return self.send(200,self.rt.resources.verify())
        if path.path == '/api/v3':return self.send(200,self.rt.v3.view())
        if path.path == '/api/v3/agent':return self.send(200,self.rt.agent.view())
        if path.path == '/api/v3/migration':
            query_text=query.get('q',[''])[0].casefold()
            migration=self.rt.v3.migration
            records=[r for r in migration['definitions'] if query_text in (str(r.get('name'))+' '+str(r.get('path'))+' '+str(r.get('signature'))).casefold()]
            return self.send(200,{'summary':migration['summary'],'definitions':records[:150],'matches':len(records),'network':migration['network'],'graphics':migration['graphics']})
        if path.path == '/api/state': return self.send(200,self.rt.snapshot())
        if path.path == '/api/sources': return self.send(200,self.rt.source_hub.view())
        if path.path == '/api/work': return self.send(200,self.rt.workbench.view())
        if path.path == '/api/commands': return self.send(200,self.rt.interpreter.view())
        if path.path == '/api/field-voice': return self.send(200,self.rt.field_voice.view())
        if path.path == '/api/call-definitions': return self.send(200,self.rt.call_definitions.view())
        if path.path == '/api/loops': return self.send(200,{'module_loops':self.rt.config.get('module_loops',{}),'default_seconds':self.rt.config['cycle_seconds'],'running':self.rt.config['running']})
        if path.path == '/api/screen': return self.send(200,self.rt.screen_hub.view())
        if path.path == '/api/screen/windows': return self.send(200,self.rt.screen_hub.list_windows())
        if path.path == '/api/work/file':
            try: result=self.rt.workbench.file(query.get('id',[''])[0])
            except (ValueError,OSError) as exc: return self.send(404,{'error':str(exc)})
            if query.get('download')==['1']:
                content=result['text'].encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type','application/octet-stream')
                self.send_header('Content-Disposition','attachment; filename="'+result['name']+'"')
                self.send_header('Content-Length',str(len(content)))
                self.send_header('X-Content-Type-Options','nosniff')
                self.send_header('Cache-Control','no-store')
                self.end_headers();self.wfile.write(content);return
            return self.send(200,result)
        if path.path == '/api/models': return self.send(200,self.rt.model_hub.view())
        if path.path == '/api/models/context':
            context,coverage = self.rt.model_hub.context(query.get('question',[''])[0])
            return self.send(200,{'context':context,'coverage':coverage})
        if path.path == '/api/module':
            name = query.get('id',[''])[0]
            if name not in self.rt.modules: return self.send(404,{'error':'Unknown module'})
            with self.rt.lock:
                return self.send(200,{'module':self.rt.modules[name],'result':self.rt.results.get(name),
                    'inputs':self.rt.overrides.get(name,self.rt.modules[name]['inputs'])})
        if path.path == '/api/source':
            name = query.get('id',[''])[0]
            if name not in self.rt.modules: return self.send(404,{'error':'Unknown module'})
            return self.send(200,{'source':(self.rt.root/self.rt.modules[name]['file']).read_text(encoding='utf-8-sig')})
        if path.path == '/api/events': return self.stream()
        return self.send(404,{'error':'Not found'})

    def stream(self):
        client = queue.Queue(maxsize=256)
        with self.rt.lock: self.rt.listeners.add(client)
        self.send_response(200)
        self.send_header('Content-Type','text/event-stream')
        self.send_header('Cache-Control','no-cache')
        self.send_header('Connection','keep-alive')
        self.end_headers()
        self.connection.settimeout(5)
        try:
            self.wfile.write(b': connected\n\n')
            self.wfile.flush()
            while not self.rt.stop.is_set() and self.server is self.rt.http:
                try:
                    event = client.get(timeout=2)
                    self.wfile.write(b'data: '+encode(event)+b'\n\n')
                except queue.Empty: self.wfile.write(b': heartbeat\n\n')
                self.wfile.flush()
        except (OSError,ConnectionError): pass
        finally:
            with self.rt.lock: self.rt.listeners.discard(client)
            self.close_connection = True

    def do_POST(self):
        try:
            if not self.valid_host() or not self.authorized(): return self.send(403,{'error':'Local bus authentication required'})
            origin = self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
                return self.send(403,{'error':'Origin rejected'})
            length = int(self.headers.get('Content-Length','0'))
            path = urllib.parse.urlparse(self.path).path
            if path == '/api/v3/wav-upload':
                if not 44<=length<=24*1024*1024:return self.send(413,{'error':'WAV limit is 24 MB'})
                self.connection.settimeout(30)
                raw=self.rfile.read(length)
                result=self.rt.v3.wav.load(raw,urllib.parse.unquote(self.headers.get('X-Filename','audio.wav')))
                # Bounded frames keep every accepted WAV byte visible to the same chiral queue.
                def route_audio():
                    for offset in range(0,len(raw),65536):
                        while not self.rt.stop.is_set():
                            with self.rt.binary_bus.lock:
                                room=self.rt.binary_bus.pending_bytes<6*1024*1024 and len(self.rt.binary_bus.pending)<1800
                                if room and self.rt.binary_bus.feed('wav-input',raw[offset:offset+65536]):break
                            if self.rt.stop.wait(.15):return
                threading.Thread(target=route_audio,daemon=True,name='wav-chiral-input').start()
                self.rt.v3.record('wav-load',{k:v for k,v in result.items() if k!='waveform'})
                return self.send(200,result)
            if not 0<length<=262144: return self.send(413,{'error':'Payload must be between 1 and 262144 bytes'})
            self.connection.settimeout(5)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body,dict): raise ValueError('Expected an object')
            path = urllib.parse.urlparse(self.path).path
            if path.startswith('/api/v4/'):return self.send(200,self.rt.python.dispatch(path.removeprefix('/api/v4/'),body))
            if path == '/api/pathway/configure':return self.send(200,self.rt.pathway.configure(body))
            if path == '/api/flux/command':return self.send(200,self.rt.flux.command(body))
            if path == '/api/hierarchy/compare':return self.send(200,self.rt.hierarchy.compare(body))
            if path == '/api/virtue/run':return self.send(202,self.rt.virtue.submit(body))
            if path == '/api/economy':return self.send(200,self.rt.economy.command(body))
            if path == '/api/primary/configure':return self.send(200,self.rt.primary.configure(body))
            if path == '/api/virtue/configure':return self.send(200,self.rt.virtue.configure(body))
            if path == '/api/virtue/resume':return self.send(202,self.rt.virtue.resume(body.get('id')))
            if path == '/api/virtue/stop':return self.send(200,self.rt.virtue.stop())
            if path == '/api/virtue/cast':return self.send(200,self.rt.virtue.cast(body.get('id')))
            if path == '/api/virtue/observe':return self.send(200,self.rt.virtue.observe(body))
            if path == '/api/code-archetypes/inspect':
                name=body.get('module')
                if name not in self.rt.modules:raise ValueError('Choose an existing module')
                source=(self.rt.root/self.rt.modules[name]['file']).read_text(encoding='utf-8-sig')
                return self.send(200,{'module':name,**LIBRARY.inspect(source)})
            if path == '/api/mesh/configure':return self.send(200,self.rt.mesh.configure(body))
            if path == '/api/mesh/start':return self.send(200,self.rt.mesh.start())
            if path == '/api/mesh/stop':return self.send(200,self.rt.mesh.stop())
            if path == '/api/mesh/send':return self.send(200,self.rt.mesh.queue(body.get('text')))
            if path == '/api/mesh/key':return self.send(200,{'key':self.rt.mesh.key})
            if path == '/api/backbone/configure':return self.send(200,self.rt.backbone.configure(body))
            if path == '/api/backbone/start':return self.send(200,self.rt.backbone.start())
            if path == '/api/backbone/pause':return self.send(200,self.rt.backbone.pause())
            if path == '/api/backbone/review':return self.send(200,self.rt.backbone.review())
            if path == '/api/backbone/rollback':return self.send(200,self.rt.backbone.rollback(body.get('id')))
            if path == '/api/research/configure':return self.send(200,self.rt.research.configure(body))
            if path == '/api/research/search':return self.send(200,self.rt.research.search(body.get('topic')))
            if path == '/api/research/run':return self.send(200,self.rt.research.submit(body))
            if path == '/api/research/source':return self.send(200,self.rt.research.submit_source(body.get('id')))
            if path == '/api/research/stop':return self.send(200,self.rt.research.stop())
            if path == '/api/drill/run':return self.send(200,self.rt.drill.submit(body))
            if path == '/api/drill/stop':return self.send(200,self.rt.drill.stop())
            if path == '/api/drill/feedback':return self.send(200,self.rt.drill.feedback_add(body.get('id'),body.get('module'),body.get('label')))
            if path == '/api/drill/train':return self.send(200,self.rt.drill.train())
            if path == '/api/spectrum/analyze':return self.send(200,self.rt.spectrum.inspect(body))
            if path == '/api/spectrum/theory':return self.send(200,self.rt.spectrum.ingest_theory())
            if path == '/api/carrier-source/configure':return self.send(200,self.rt.measured_carrier.configure(body))
            if path == '/api/carrier-source/refresh':return self.send(200,self.rt.measured_carrier.refresh())
            if path == '/api/carrier-source/reading':return self.send(200,self.rt.measured_carrier.accept(body))
            if path == '/api/drill/bits':
                result=evaluate_bits(body)
                if body.get('cast_back') is True:
                    raise ValueError('The manual eight-case table is a reference calculator. Use Predictive virtue to assess whole-candidate effects before cast-back.')
                return self.send(200,result)
            if path == '/api/flux/configure':return self.send(200,self.rt.flux.configure(body))
            if path == '/api/flux/alignment':return self.send(200,self.rt.flux.alignment(body))
            if path == '/api/inference/run':return self.send(202,self.rt.inference.submit(body))
            if path == '/api/pathway/run':
                findings=self.rt.watch.view()['findings']
                if not findings:raise ValueError('Read public sources or add relevant text first')
                return self.send(200,self.rt.pathway.enqueue(self.rt.watch.make_report(),[{k:f.get(k) for k in ('url','title','retrieved','sha256')} for f in findings]))
            if path == '/api/vpn/refresh':return self.send(200,self.rt.privacy.vpn.refresh())
            if path == '/api/vpn/add':return self.send(200,self.rt.privacy.vpn.add(body))
            if path == '/api/vpn/connect':return self.send(200,self.rt.privacy.vpn.connect(body.get('name')))
            if path == '/api/vpn/settings':return self.send(200,self.rt.privacy.vpn.open_settings())
            if path == '/api/privacy/configure':return self.send(200,self.rt.privacy.configure(body))
            if path == '/api/privacy/start':
                self.rt.privacy.configure({'automatic':True})
                return self.send(200,self.rt.privacy.start())
            if path == '/api/privacy/check':return self.send(200,self.rt.privacy.check())
            if path == '/api/watch/configure':return self.send(200,self.rt.watch.configure(body))
            if path == '/api/watch/review':return self.send(200,self.rt.watch.review(body))
            if path == '/api/watch/scan':return self.send(200,self.rt.watch.scan())
            if path.startswith('/api/resources/'):
                result=self.rt.resources.mutate(path.removeprefix('/api/resources/'),body)
                self.rt.publish('resource-receipt',result)
                return self.send(200,result)
            if path == '/api/v3/agent/start':return self.send(200,self.rt.agent.start(body.get('goal'),body.get('cycles',8)))
            if path == '/api/v3/agent/stop':return self.send(200,self.rt.agent.stop())
            if path.startswith('/api/v3/'):return self.send(200,self.rt.v3.dispatch(path.removeprefix('/api/v3/'),body))
            if path == '/api/speech':
                content = self.rt.speech.render(body.get('text'), body.get('rate', 1))
                self.rt.publish('speech', {'status':'generated', 'bytes':len(content)})
                return self.send(200, content, 'audio/wav')
            if path == '/api/commands/prepare': return self.send(200,self.rt.interpreter.prepare(body.get('text'),body.get('provider','llama')))
            if path == '/api/loops': return self.send(200,self.rt.set_loops(body.get('modules'),body.get('action'),body.get('interval')))
            if path == '/api/field-voice/send': return self.send(200,self.rt.field_voice.submit(body.get('text'),body.get('provider','llama'),body.get('source_ids')))
            if path == '/api/field-voice/clear': return self.send(200,self.rt.field_voice.clear())
            if path == '/api/commands/run': return self.send(200,self.rt.interpreter.execute(body.get('id')))
            if path == '/api/screen/pick': return self.send(200,self.rt.screen_hub.pick())
            if path == '/api/screen/command': return self.send(200,self.rt.screen_hub.command_input(body))
            if path == '/api/screen/inspect': return self.send(200,self.rt.screen_hub.inspect(body.get('mode'),body.get('handle'),body.get('tab','')))
            if path == '/api/screen/ingest': return self.send(200,self.rt.screen_hub.ingest(body.get('handle'),body.get('tab',''),body.get('element',''),body.get('automatic',False),body.get('targets')))
            if path == '/api/screen/stop': return self.send(200,self.rt.screen_hub.stop_capture())
            if path.startswith('/api/models/'):
                hub = self.rt.model_hub
                provider = body.get('provider')
                if path=='/api/models/configure': result = hub.configure(provider,body.get('model'),body.get('key'))
                elif path=='/api/models/check': result = hub.connection(provider)
                elif path=='/api/models/send': result = hub.submit(provider,body.get('message'),body.get('source_ids'))
                elif path=='/api/models/clear': result = hub.clear(provider)
                else: return self.send(404,{'error':'Unknown model action'})
                return self.send(200,result)
            if path == '/api/sources/add':
                return self.send(200,self.rt.source_hub.add(body.get('kind'),body.get('title',''),body.get('url',''),body.get('text',''),body.get('automatic',True)))
            if path == '/api/sources/control':
                return self.send(200,self.rt.source_hub.control(body.get('id'),body.get('action')))
            if path == '/api/work/create':
                return self.send(200,self.rt.workbench.create(body.get('title'),body.get('instruction'),body.get('provider','llama'),body.get('filename','result.md'),body.get('source_ids')))
            if path == '/api/work/start': return self.send(200,self.rt.workbench.start(body.get('id')))
            if path == '/api/work/action': return self.send(200,self.rt.workbench.action(body.get('id'),body.get('action'),body.get('value')))
            if path == '/api/settings':
                config = self.rt.update_settings(body)
                return self.send(200,{'settings':config,'url':f'http://127.0.0.1:{config["port"]}'})
            if path == '/api/run':
                names = list(self.rt.modules) if body.get('id')=='all' else [body.get('id')]
                count = sum(self.rt.schedule(n) for n in names)
                return self.send(200,{'scheduled':count})
            if path == '/api/inputs':
                name = body.get('id')
                if name not in self.rt.modules: raise ValueError('Unknown module')
                values = body.get('inputs')
                if not isinstance(values,dict) or set(values)-set(self.rt.modules[name]['inputs']): raise ValueError('Use declared input dictionary names')
                if not all(isinstance(v,dict) for v in values.values()): raise ValueError('Each input must be a dictionary')
                encode(values)
                with self.rt.lock:
                    self.rt.overrides[name] = values
                    write_json(self.rt.data/'inputs.json',self.rt.overrides)
                return self.send(200,{'saved':True,'scheduled':self.rt.schedule(name)})
            if path == '/api/weight':
                key = body.get('id')
                weight = body.get('weight')
                if key not in self.rt.nodes: raise ValueError('Unknown neural node')
                if type(weight) not in (int,float) or not math.isfinite(weight) or not -3<=weight<=3: raise ValueError('Weight must be between -3 and +3')
                with self.rt.lock:
                    self.rt.nodes[key]['weight'] = weight
                    self.rt.config['weights'][key] = weight
                    if key=='carrier': self.rt.config['carrier_weight'] = weight
                    self.rt.activate(key,self.rt.nodes[key]['input'])
                    self.rt.save_config()
                return self.send(200,{'saved':True})
            if path == '/api/ingest':
                with self.rt.lock:
                    for d in self.rt.definitions.values(): d['next_fetch'] = 0
                with self.rt.call_definitions.lock:
                    for page in self.rt.call_definitions.pages.values():page['next_fetch']=0
                return self.send(200,{'queued':len(self.rt.definitions)})
            if path == '/api/chiral':
                if body.get('action')=='text':
                    with self.rt.lock:
                        self.rt.chiral.load_text(body.get('text'))
                        raw=self.rt.chiral.command_input
                        self.rt.activate('chiral-command',sum(value.bit_count() for value in raw)/(4*len(raw))-1)
                        self.rt.binary_bus.feed('text-command',raw)
                    state=self.rt.chiral_step()
                elif body.get('action')=='clear-text':
                    with self.rt.lock:
                        self.rt.chiral.clear_text();self.rt.activate('chiral-command',0)
                        state={**self.rt.chiral.state(),'binary_bus':self.rt.binary_bus.state()}
                    self.rt.publish('chiral',state,record=False)
                elif body.get('action')=='reset':
                    with self.rt.lock:
                        self.rt.chiral.reset()
                        state = {**self.rt.chiral.state(),'binary_bus':self.rt.binary_bus.state()}
                    self.rt.publish('chiral',state,record=False)
                elif body.get('action')=='step': state = self.rt.chiral_step()
                else: raise ValueError('Choose text, clear-text, reset or step')
                return self.send(200,state)
            if path == '/api/bus/events':
                self.rt.client_event(body)
                return self.send(200,{'accepted':True})
            if path == '/api/stop':
                self.send(200,{'stopping':True})
                threading.Thread(target=self.rt.close,daemon=True).start()
                return
            return self.send(404,{'error':'Not found'})
        except (ValueError,TypeError,KeyError,OSError) as exc:
            self.send(400,{'error':str(exc)})
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception as exc:
            self.send(400,{'error':str(exc)})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modules',default=str(APP.parent))
    parser.add_argument('--data')
    parser.add_argument('--port',type=int)
    parser.add_argument('--no-browser',action='store_true')
    args = parser.parse_args()
    runtime = Runtime(args.modules,args.data)
    if args.port: runtime.config['port'] = args.port
    try: runtime.start()
    except OSError as exc:
        print(f'Cannot open port {runtime.config["port"]}: {exc}. Change --port or close the existing app.',flush=True)
        return 1
    url = f'http://127.0.0.1:{runtime.config["port"]}'
    print(f'Postscarcity Observatory running at {url}',flush=True)
    if not args.no_browser: webbrowser.open(url)
    try:
        while not runtime.stop.wait(1): pass
    except KeyboardInterrupt: runtime.close()
    return 0

if __name__ == '__main__': raise SystemExit(main())
