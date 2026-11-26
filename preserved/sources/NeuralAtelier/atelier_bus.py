"""Authenticated loopback UDP bus for scripts and app adapters."""
import json,os,socket,threading,time,secrets,math
from pathlib import Path
class LocalBus:
    def __init__(self,engine,data):
        self.engine=engine; self.stop=threading.Event(); self.clients={}; self.rx=0; self.tx=0
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); self.socket.bind(('127.0.0.1',0)); self.socket.settimeout(.1)
        self.token=secrets.token_hex(32); self.path=Path(data)/'atelier-connection.json'
        self.path.write_text(json.dumps(dict(port=self.socket.getsockname()[1],token=self.token,pid=os.getpid())),encoding='utf-8')
        self.thread=threading.Thread(target=self.loop,daemon=True); self.thread.start()
    def loop(self):
        next_publish=0
        while not self.stop.is_set():
            try:
                raw,addr=self.socket.recvfrom(14000); message=json.loads(raw)
                if not isinstance(message,dict) or not secrets.compare_digest(str(message.get('token','')),self.token): continue
                if message.get('type')=='subscribe' and (addr in self.clients or len(self.clients)<128): self.clients[addr]=time.monotonic()
                if message.get('type')=='signal':
                    value=message.get('value')
                    if type(value) in (int,float) and math.isfinite(value):
                        with self.engine.lock:
                            self.engine.script_signal=max(-1,min(1,value)); self.engine.script_at=time.monotonic(); self.engine.script_samples+=1
                        self.rx+=1
            except (OSError,ValueError,AttributeError): pass
            now=time.monotonic()
            if now>=next_publish:
                next_publish=now+.25
                self.clients={a:t for a,t in self.clients.items() if now-t<15}
                packet=json.dumps(dict(type='field',data=self.engine.snapshot()),allow_nan=False).encode()
                for addr in self.clients:
                    try: self.socket.sendto(packet,addr); self.tx+=1
                    except OSError: pass
    def close(self):
        self.stop.set(); self.thread.join(1); self.socket.close()
        try:
            if json.loads(self.path.read_text()).get('token')==self.token: self.path.unlink()
        except (OSError,ValueError): pass

class Client:
    def __init__(self,name='Python worker',connection=None):
        self.name=name; self.path=Path(connection or os.environ.get('NEURAL_ATELIER_CONNECTION',Path(__file__).parent/'data/atelier-connection.json'))
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); self.socket.bind(('127.0.0.1',0)); self.socket.settimeout(1)
        self.next_subscribe=0
    def send(self,kind,**data):
        self.config=json.loads(self.path.read_text(encoding='utf-8'))
        self.address=('127.0.0.1',int(self.config['port']))
        self.socket.sendto(json.dumps(dict(token=self.config['token'],type=kind,name=self.name,**data)).encode(),self.address)
    def signal(self,value): self.send('signal',value=value)
    def receive(self):
        if time.monotonic()>=self.next_subscribe:
            self.send('subscribe'); self.next_subscribe=time.monotonic()+5
        raw,addr=self.socket.recvfrom(14000)
        if addr!=self.address: raise ValueError('Unexpected sender')
        return json.loads(raw)['data']
    def close(self): self.socket.close()
