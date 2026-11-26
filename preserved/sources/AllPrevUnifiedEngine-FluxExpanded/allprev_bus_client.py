"""Cooperative two-way client for an existing Python app (standard library only)."""
import json
import os
import urllib.request

class AllPrevBusClient:
    def __init__(self, name, base='http://127.0.0.1:48763'):
        self.name, self.base, self.pid, self.cursor = name, base, os.getpid(), 0

    def _request(self, path, body=None):
        raw=None if body is None else json.dumps(body).encode('utf-8')
        request=urllib.request.Request(self.base+path,data=raw,headers={'Content-Type':'application/json'})
        # Local adapters never route their messages through configured web proxies.
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=3) as response:
            return json.load(response)

    def send(self, topic, data, target='all'):
        return self._request('/api/events',{'source':self.name,'pid':self.pid,'target':str(target),'topic':topic,'data':data})

    def receive(self):
        result=self._request(f'/api/events?pid={self.pid}&after={self.cursor}')
        self.cursor=result['cursor']
        # Only return messages, never evaluate or execute received text.
        return result['events']


class AllPrevUdpClient:
    """Push broadcasts on local UDP port 48763. Refresh subscribe every 10 seconds.
    UDP can lose packets; use AllPrevBusClient when cursor-based delivery matters.
    """
    def __init__(self, name, port=48763):
        import socket
        self.name, self.pid = name, os.getpid()
        self.address = ('127.0.0.1', port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', 0))
        self.subscribe()

    def _send(self, body):
        self.socket.sendto(json.dumps(body).encode('utf-8'), self.address)

    def subscribe(self):
        self._send({'type':'subscribe','pid':self.pid,'source':self.name})

    def send(self, topic, data, target='all'):
        self._send({'type':'event','pid':self.pid,'source':self.name,
                    'target':str(target),'topic':topic,'data':data})

    def receive(self, timeout=3):
        self.socket.settimeout(timeout)
        while True:
            raw, address = self.socket.recvfrom(65535)
            if address == self.address:
                return json.loads(raw)

    def close(self):
        self.socket.close()
