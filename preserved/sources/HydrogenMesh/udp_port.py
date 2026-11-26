"""Loopback UDP ingress, fixed-port broadcast, and renewable subscribers.

UDP packets are best effort. Use the HTTP bus for durable acknowledged ingress.
Large events use numbered fragments, each under 12 KiB, with a full hash.
"""
import base64
import hashlib
import hmac
import json
import socket
import threading
import time
from mesh_bus import encoded

def frames(event):
    raw=encoded(event)
    if len(raw)<=11000:return [raw]
    size=7200;digest=hashlib.sha256(raw).hexdigest();count=(len(raw)+size-1)//size
    return [encoded(dict(type='mesh.fragment',id=event['id'],index=i,parts=count,sha256=digest,
                         encoding='base64-json',chunk=base64.b64encode(raw[start:start+size]).decode()))
            for i,start in enumerate(range(0,len(raw),size))]

class UDPPort:
    def __init__(self,ledger,token,port,broadcast_port=8796):
        self.ledger=ledger;self.token=token;self.stop=threading.Event();self.broadcast_port=int(broadcast_port)
        if not 0<=self.broadcast_port<=65535:raise ValueError('Broadcast port must be 0 (off) or 1–65535')
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        if hasattr(socket,'SIO_UDP_CONNRESET'):
            self.socket.ioctl(socket.SIO_UDP_CONNRESET,False)
        try:self.socket.bind(('127.0.0.1',port))
        except Exception:self.socket.close();raise
        self.port=self.socket.getsockname()[1];self.socket.settimeout(.1)
        self.subscribers={};self.cursor=ledger.latest();self.received=0;self.sent=0;self.rejected=0;self.errors=0
        self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()
    def send(self,data,addr):
        self.socket.sendto(data,addr);self.sent+=1
    def loop(self):
        while not self.stop.is_set():
            try:
                try:
                    raw,addr=self.socket.recvfrom(16000)
                    value=json.loads(raw)
                    if not isinstance(value,dict) or not hmac.compare_digest(str(value.pop('token','')),self.token):
                        self.rejected+=1;continue
                    kind=value.pop('type','publish')
                    if kind=='subscribe':
                        self.subscribers[addr]=time.monotonic()
                        self.send(encoded(dict(type='attached',port=self.port,broadcast_port=self.broadcast_port)),addr)
                    elif kind=='publish':
                        receipt=self.ledger.publish(value);self.received+=1
                        self.send(encoded(dict(type='accepted',**receipt)),addr)
                    else:raise ValueError('Use subscribe or publish')
                except socket.timeout:pass
                self.subscribers={addr:stamp for addr,stamp in self.subscribers.items() if time.monotonic()-stamp<20}
                destinations=set(self.subscribers)
                if self.broadcast_port:destinations.add(('127.0.0.1',self.broadcast_port))
                for event in self.ledger.read(self.cursor,40):
                    for packet in frames(event):
                        for addr in destinations:
                            # Never reflect broadcasts into the ingress socket.
                            if addr!=('127.0.0.1',self.port):
                                try:self.send(packet,addr)
                                except OSError:self.errors+=1
                    self.cursor=event['seq']
            except (ValueError,TypeError,OSError):self.errors+=1
        self.socket.close()
    def close(self):
        self.stop.set();self.thread.join(timeout=2)
