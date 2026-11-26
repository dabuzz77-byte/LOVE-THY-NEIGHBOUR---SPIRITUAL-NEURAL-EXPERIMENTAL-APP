"""Drop-in bidirectional Python adapter. No third-party dependencies."""
import json
import os
from pathlib import Path
import threading
import time
import uuid
from urllib.request import Request,urlopen
from urllib.parse import urlencode

class MeshClient:
    def __init__(self,name,connection=None,on_event=None,replay=False):
        self.name=name;self.path=Path(connection or os.environ.get('HYDROGEN_MESH_CONNECTION',Path(__file__).parent/'data/connection.json'))
        self.on_event=on_event;self.stop=threading.Event();self.after=0;self.status='Connecting';self.replay=replay
        self.thread=None
        if on_event:
            self.thread=threading.Thread(target=self._loop,daemon=True);self.thread.start()
    def request(self,path,data=None):
        config=json.loads(self.path.read_text(encoding='utf-8-sig'))
        from urllib.parse import urlsplit
        url=urlsplit(config['url'])
        if url.scheme!='http' or url.hostname!='127.0.0.1': raise ValueError('Only loopback HTTP supported')
        req=Request(config['url']+path,data=None if data is None else json.dumps(data,allow_nan=False).encode(),
                    headers={'Authorization':'Bearer '+config['token'],'Content-Type':'application/json'})
        with urlopen(req,timeout=5) as response:return json.load(response)
    def publish(self,topic,data,target='*',route=None,identity=None,reply_to=None):
        return self.request('/publish',dict(id=identity or uuid.uuid4().hex,source=self.name,target=target,topic=topic,data=data,route=route or [self.name],reply_to=reply_to))
    def _loop(self):
        initialized=False
        while not self.stop.is_set():
            try:
                if not initialized:
                    if not self.replay:self.after=self.request('/status')['messages']
                    initialized=True
                    self.publish('client.attached',{'pid':os.getpid(),'language':'Python'})
                events=self.request('/events?'+urlencode({'after':self.after}))['events']
                for event in events:
                    if event['source']!=self.name and (self.name not in event['route'] or event.get('reply_to')==self.name or event['target']==self.name) and event['target'] in ('*',self.name):
                        self.on_event(event)
                        self.request('/receipt',dict(client=self.name,seq=event['seq'],id=event['id'],status='callback completed'))
                    self.after=event['seq']
                self.status='Connected'
            except Exception as e:self.status=str(e)
            self.stop.wait(.2)
    def close(self):
        self.stop.set()
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=6)

if __name__=='__main__':
    def show(event):print(json.dumps(event,ensure_ascii=False),flush=True)
    client=MeshClient('python-example-'+str(os.getpid()),on_event=show)
    try:
        while True:
            client.publish('example.heartbeat',{'seconds':time.time()});time.sleep(5)
    except KeyboardInterrupt:client.close()
