"""Import Bus into a Python program, or run this file as a connected example."""
import json
import os
from pathlib import Path
import socket
import threading
import time

DEFAULT_CONNECTION = Path.home()/'Desktop'/'CHAT GPT APPS'/'Postscarcity Observatory v4'/'graphical_app'/'data'/'connection.json'

class Bus:
    def __init__(self, name='Python process', connection_file=DEFAULT_CONNECTION, on_event=None):
        self.name = name
        self.path = Path(connection_file)
        self.on_event = on_event or (lambda event:None)
        self.stopped = threading.Event()
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1',0))
        self.socket.settimeout(1)
        self.config = None
        self.thread = threading.Thread(target=self._listen,daemon=True)
        self.thread.start()

    def _send(self,payload):
        if not self.config: return False
        envelope = {'token':self.config['token'],'pid':os.getpid(),'name':self.name,**payload}
        encoded = json.dumps(envelope,allow_nan=False).encode()
        if len(encoded)>14000: raise ValueError('Bus events must fit in 14 KB')
        self.socket.sendto(encoded,('127.0.0.1',self.config['port']))
        return True

    def _listen(self):
        next_subscribe = 0
        while not self.stopped.is_set():
            try:
                if time.monotonic()>=next_subscribe:
                    self.config = json.loads(self.path.read_text(encoding='utf-8'))
                    self._send({'type':'subscribe'})
                    next_subscribe = time.monotonic()+5
                raw,addr = self.socket.recvfrom(65535)
                if self.config and addr==('127.0.0.1',self.config['port']):
                    self.on_event(json.loads(raw))
            except (OSError,ValueError): self.stopped.wait(.1)

    def publish(self,topic,data):
        return self._send({'type':'event','topic':topic,'data':data})

    def close(self):
        self.stopped.set()
        self.socket.close()
        self.thread.join(timeout=2)

    def __enter__(self): return self
    def __exit__(self,*args): self.close()

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--connection',default=str(DEFAULT_CONNECTION))
    parser.add_argument('--seconds',type=float,default=0)
    args=parser.parse_args()
    def show(event):
        if event['type']=='attached': print('Python connected to postscarcity bus',flush=True)
        elif event['type']=='pulse' and event['data']['pulses']%40==0:
            print('Carrier:',event['data']['measured_hz'],'Hz; neural output:',event['data']['neural_output'],flush=True)
    with Bus('Python bus example',args.connection,show) as bus:
        started=time.monotonic()
        try:
            while not args.seconds or time.monotonic()-started<args.seconds:
                bus.publish('python.activity',{'state':'listening','elapsed_seconds':round(time.monotonic()-started,1)})
                time.sleep(2)
        except KeyboardInterrupt: pass
