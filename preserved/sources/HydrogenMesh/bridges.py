"""Adapters for installed FluxBus and Observatory; originals are not modified."""
import base64
from contextlib import closing
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import threading
import time
from urllib.request import Request,urlopen
from mesh_bus import encoded

APPS=Path(r'C:\Users\USER\Desktop\CHAT GPT APPS')
class ReadConnection(sqlite3.Connection):
    """Allow the installed decoder's in-memory cache; database remains read-only."""
    pass
DEFAULTS=dict(apps_root=str(APPS),flux_source=str(APPS/'FluxBus-v2/source'),
              flux_database=str(APPS/'FluxBus-v2/FluxBus-data/world_grid_hub.db'),flux_port=9999,
              broadcast_port=8796,
              observatory_connection=str(APPS/'Postscarcity Observatory v4/graphical_app/data/connection.json'))

def publish_chunks(ledger,source,topic,data,route,identity,reply_to=None):
    raw=encoded(data)
    if len(raw)<170000:
        return ledger.publish(dict(id=identity,source=source,topic=topic,data=data,route=route,reply_to=reply_to))
    digest=hashlib.sha256(raw).hexdigest();size=96000
    for index,start in enumerate(range(0,len(raw),size)):
        ledger.publish(dict(id=f'{identity}.{index}',source=source,topic=topic+'.part',route=route,reply_to=reply_to,
            data=dict(transfer=identity,index=index,parts=(len(raw)+size-1)//size,sha256=digest,
                      encoding='base64-json',chunk=base64.b64encode(raw[start:start+size]).decode())))
    return {'accepted':True,'id':identity}

class Bridge:
    def __init__(self,ledger,name):
        self.ledger=ledger;self.name=name;self.stop=threading.Event();self.status='Waiting for app';self.received=0;self.sent=0;self.failures=0
        self.enabled=True;self.thread=None;self.last_seen=0
        self.cursor=ledger.cursor('bridge:'+name,ledger.latest())
    def start(self):
        self.thread=threading.Thread(target=self.loop,daemon=True,name=self.name);self.thread.start()
    def advance(self,event,status=None):
        self.cursor=event['seq'];self.ledger.advance('bridge:'+self.name,self.cursor,event['id'] if status else None,status or 'skipped')
    def pending(self):
        for event in self.ledger.read(self.cursor,40):
            if len(event['route'])>=12 or self.name in event['route'] or event['source']==self.name or event['target'] not in ('*',self.name) or event['topic'] in ('client.attached','process.inventory'):
                self.advance(event);continue
            yield event
    def close(self):self.stop.set()

class ObservatoryBridge(Bridge):
    def __init__(self,ledger,connection):
        super().__init__(ledger,'observatory');self.connection=Path(connection);self.sock=None;self.config=None;self.subscribed=False
    def send(self,event):
        raw=encoded(event);parts=[raw[i:i+6000] for i in range(0,len(raw),6000)]
        for index,chunk in enumerate(parts):
            data=dict(mesh_id=event['id'],route=event['route']+['observatory'],index=index,parts=len(parts),
                      sha256=hashlib.sha256(raw).hexdigest(),encoding='base64-json',chunk=base64.b64encode(chunk).decode())
            body=dict(pid=os.getpid(),name='Hydrogen Mesh',topic='hydrogen.mesh',data=data)
            req=Request(f"http://127.0.0.1:{self.config['port']}/api/bus/events",data=encoded(body),
                        headers={'Authorization':'Bearer '+self.config['token'],'Content-Type':'application/json'})
            with urlopen(req,timeout=3) as reply:accepted=json.load(reply)
            if accepted.get('accepted') is not True:raise ValueError('Observatory did not confirm acceptance')
        self.sent+=1;self.advance(event,'Observatory runtime accepted all parts')
    def loop(self):
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.sock.bind(('127.0.0.1',0));self.sock.settimeout(.12)
        renew=0
        while not self.stop.is_set():
            if not self.enabled:self.stop.wait(.5);continue
            try:
                if time.monotonic()>=renew:
                    config=json.loads(self.connection.read_text(encoding='utf-8-sig'))
                    if type(config.get('port')) is not int or not 1<=config['port']<=65535 or not isinstance(config.get('token'),str):raise ValueError('Invalid Observatory connection')
                    if config!=self.config:self.subscribed=False
                    self.config=config
                    self.sock.sendto(encoded(dict(type='subscribe',pid=os.getpid(),name='Hydrogen Mesh',token=config['token'])),('127.0.0.1',config['port']))
                    renew=time.monotonic()+5
                try:
                    raw,addr=self.sock.recvfrom(65535)
                    if addr!=('127.0.0.1',self.config['port']):continue
                    incoming=json.loads(raw);self.last_seen=time.time()
                    if incoming.get('type')=='attached':self.subscribed=True
                    kind=incoming.get('type');data=incoming.get('data',{})
                    if kind in ('module','inference-result','model-response','command','process-event','resource-receipt'):
                        topic=data.get('topic','') if isinstance(data,dict) else ''
                        # Our return echo is a receipt, not a new input. FluxBus publishes its own
                        # outputs into Observatory too; preserve that provenance to stop cycles.
                        if not (kind=='process-event' and (data.get('pid')==os.getpid() or topic=='hydrogen.mesh')):
                            route=['observatory']+(['fluxbus'] if topic.startswith('fluxbus.') else [])
                            identity='obs:'+str(self.config['port'])+':'+str(incoming.get('time'))+':'+str(incoming.get('seq',hashlib.sha256(raw).hexdigest()))
                            publish_chunks(self.ledger,'observatory','observatory.'+kind,incoming,route,identity);self.received+=1
                except socket.timeout:pass
                if self.subscribed:
                    self.status='Two-way · subscribed' if time.time()-self.last_seen<15 else 'Stale · waiting for Observatory'
                    # Four at a time keeps receiving responsive under load.
                    for index,event in enumerate(self.pending()):
                        self.send(event)
                        if index>=3:break
            except (OSError,ValueError,KeyError,TypeError) as e:
                self.failures+=1;self.status='Unavailable: '+str(e);self.subscribed=False;renew=0;self.stop.wait(2)
        self.sock.close()

class FluxBridge(Bridge):
    def __init__(self,ledger,config):
        super().__init__(ledger,'fluxbus');self.config=config;self.decoder=None
        self.scan_time,self.scan_id=ledger.setting('flux.scan_cursor',default=[time.time(),'']);self.return_available=False
    def send(self,event):
        node='mesh:'+event['id']
        body=dict(node_id=node,context=encoded(event).decode(),state='unassessed')
        with socket.create_connection(('127.0.0.1',int(self.config['flux_port'])),timeout=2) as client:
            client.settimeout(3);client.sendall(encoded(body));raw=bytearray()
            while len(raw)<1048576:
                part=client.recv(8192)
                if not part:break
                raw.extend(part)
                try:reply=json.loads(raw);break
                except (ValueError,UnicodeDecodeError):continue
            else:raise ValueError('Flux ACK too large')
        reply=json.loads(raw)
        if reply.get('status')!='ACK' or reply.get('node',{}).get('node_id')!=node or reply['node'].get('context_anchor')!=body['context']:
            raise ValueError('Flux did not acknowledge this exact input')
        self.sent+=1;self.advance(event,'Flux hub committed exact context; processing is separate')
    def poll(self):
        path=Path(self.config['flux_database']);source=Path(self.config['flux_source'])
        if not path.is_file():raise FileNotFoundError('Flux return database not found')
        if not self.decoder:
            spec=importlib.util.spec_from_file_location('hydrogen_flux_storage',source/'payload_storage.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);self.decoder=module.unpack_text
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=2,factory=ReadConnection)) as db:
            # Inclusive boundary and deterministic IDs handle rows sharing a timestamp.
            rows=db.execute("SELECT id,identity,result_json,updated_at FROM pipeline_jobs WHERE (updated_at>? OR (updated_at=? AND id>?)) AND status IN ('COMPLETE','ERROR') ORDER BY updated_at,id LIMIT 40",(self.scan_time,self.scan_time,self.scan_id)).fetchall()
            self.return_available=True
            for identity,origin,result,stamp in rows:
                event_id='flux:'+identity+':'+str(stamp)
                value=json.loads(self.decoder(db,result))
                parent=self.ledger.find(origin[5:]) if origin.startswith('mesh:') else None
                if parent is None and origin.startswith('mesh:'):
                    try:
                        anchor=value.get('input',{}).get('context_anchor')
                        recovered=json.loads(anchor) if isinstance(anchor,str) else None
                        if isinstance(recovered,dict) and isinstance(recovered.get('route'),list):parent=recovered
                    except (ValueError,TypeError):pass
                route=list(parent['route']) if parent else []
                if origin.startswith('mesh:') and parent is None:
                    # An expired parent must never turn an old mesh result into a new input.
                    route=['hydrogen','observatory']
                if 'fluxbus' not in route:route.append('fluxbus')
                publish_chunks(self.ledger,'fluxbus','fluxbus.pipeline.result',value,route,event_id)
                self.received+=1;self.last_seen=time.time()
                self.scan_time,self.scan_id=stamp,identity
                self.ledger.setting('flux.scan_cursor',[stamp,identity])
            if rows:
                self.scan_time,self.scan_id=rows[-1][3],rows[-1][0]
    def loop(self):
        while not self.stop.is_set():
            if not self.enabled:self.stop.wait(.5);continue
            try:
                self.poll()
                for index,event in enumerate(self.pending()):
                    self.send(event)
                    if index>=3:break
                self.status='Two-way traffic observed' if self.last_seen and self.sent else 'Return reader ready · awaiting two-way traffic'
            except (OSError,ValueError,sqlite3.Error,ImportError) as e:
                self.failures+=1;self.status='Unavailable: '+str(e)
            self.stop.wait(1)
