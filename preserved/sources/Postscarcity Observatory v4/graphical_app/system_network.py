"""Explicit Windows/VPN route. No app proxy or background Tor process."""
import http.client
import ipaddress
import json
import socket
import ssl
import threading
import time
import urllib.parse
import urllib.request
from vpn_manager import VpnManager

class SystemNetwork:
    mode='system-vpn'
    def __init__(self,runtime):
        self.rt=runtime;self.lock=threading.RLock();self.path=runtime.data/'privacy.json';self.vpn=VpnManager()
        self.busy=False;self.error=None;self.exit_ip=None;self.last_check=None
        try:saved=json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError,ValueError):saved={}
        current=saved if saved.get('mode')==self.mode else {}
        self.auto=bool(current.get('automatic',True));self.require_vpn=bool(current.get('require_vpn',False));self.profile=str(current.get('profile',''))
        from privacy_network import install
        install(self)
    def ready(self):return bool(self.auto and (not self.require_vpn or self.vpn.connected(self.profile)))
    def view(self):
        with self.lock:return {'mode':self.mode,'automatic':self.auto,'busy':self.busy,'running':self.ready(),'verified':False,'vpn_connected':self.vpn.connected(self.profile),'vpn_required':self.require_vpn,'profile':self.profile,'public_web_paused':not self.ready(),'tor_running':False,'proxy_port':None,'installed':False,'last_check':self.last_check,'exit_ip':self.exit_ip,'error':self.error,'vpn':self.vpn.view(),'scope':'Requests follow Windows routing and your connected VPN. No Tor or app proxy.','limits':'A public IP check does not verify VPN protection. Third-party clients are managed in their own app. The optional profile gate controls new app requests, not all computer traffic.'}
    def configure(self,body):
        auto=body.get('automatic',self.auto);required=body.get('require_vpn',self.require_vpn);profile=body.get('profile',self.profile)
        if type(auto) is not bool or type(required) is not bool:raise ValueError('Network controls must be boolean')
        if not isinstance(profile,str) or len(profile)>256:raise ValueError('Choose a Windows VPN profile')
        if required and not profile:raise ValueError('Choose a Windows VPN profile before requiring it')
        with self.lock:
            self.auto=auto;self.require_vpn=required;self.profile=profile
            self.path.write_text(json.dumps({'mode':self.mode,'automatic':auto,'require_vpn':required,'profile':profile}),encoding='utf-8')
        return self.view()
    def start(self):return self.configure({'automatic':True})
    def check(self):
        from privacy_network import urlopen
        with self.lock:
            if self.busy:raise ValueError('A connection check is already running')
            self.busy=True
        try:
            self.vpn.refresh()
            with urlopen('https://api.ipify.org?format=json',timeout=20) as response:result=json.loads(response.read(4096))
            address=ipaddress.ip_address(result.get('ip',''))
            if not address.is_global:raise ConnectionError('Public IP check returned an invalid address')
            with self.lock:self.exit_ip=str(address);self.last_check=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());self.error=None
        except Exception as exc:
            with self.lock:self.exit_ip=None;self.error=str(exc)[:500]
        finally:
            with self.lock:self.busy=False
        return self.view()
    def loop(self):
        while not self.rt.stop.is_set():
            self.vpn.refresh()
            if self.rt.stop.wait(10):break
    def close(self):self.auto=False

def ensure_ready(manager):
    if not manager or not manager.ready():raise ConnectionError('Public web is paused. Enable it in VPN & network; connect the required Windows VPN profile if one is selected.')

def connection(manager,host,port=443,timeout=45):
    """TLS over the OS route, resolving and pinning public addresses per connection."""
    from privacy_network import public_host
    public_host(host);ensure_ready(manager)
    conn=http.client.HTTPSConnection(host,port,timeout=timeout,context=ssl.create_default_context())
    def create(address,timeout,source_address=None):
        ensure_ready(manager);candidates=socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)
        if not candidates or any(not ipaddress.ip_address(item[4][0]).is_global for item in candidates):raise ValueError('Public source resolved to a private or reserved address')
        last=None
        for family,kind,proto,_,target in candidates:
            sock=socket.socket(family,kind,proto)
            try:sock.settimeout(timeout);sock.connect(target);return sock
            except OSError as exc:last=exc;sock.close()
        raise last or ConnectionError('No public address could be reached')
    conn._create_connection=create;return conn

def urlopen(manager,request,timeout=45):
    from privacy_network import local_host,LocalHTTP,SafeRedirect
    url=request.full_url if isinstance(request,urllib.request.Request) else request;parsed=urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http','https') or parsed.username or parsed.password:raise ValueError('Use HTTP(S) without embedded credentials')
    if not local_host(parsed.hostname):ensure_ready(manager)
    class SystemHTTPS(urllib.request.HTTPSHandler):
        def https_open(self,req):
            def create(host,**kwargs):
                target=urllib.parse.urlsplit('https://'+host)
                if local_host(target.hostname):return http.client.HTTPSConnection(host,**kwargs)
                return connection(manager,target.hostname,target.port or 443,kwargs.get('timeout',45))
            return self.do_open(create,req)
    # Ignore proxy environment variables so a leftover SOCKS setting cannot select Tor.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),LocalHTTP(),SystemHTTPS(),SafeRedirect()).open(request,timeout=timeout)
