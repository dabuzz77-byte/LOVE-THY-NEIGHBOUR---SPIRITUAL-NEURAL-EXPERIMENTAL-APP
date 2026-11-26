"""App-scoped Tor transport. Public traffic has no direct fallback or local DNS.

This is routing for cooperative Python code, not an OS firewall or a sandbox for
arbitrary native executables. The Tor daemon itself makes the network connection.
"""
import http.client
import ipaddress
import json
import socket
import ssl
import struct
import subprocess
import sys
from neural_app import section_threads as threading
import time
import urllib.request
from pathlib import Path
CHECK_URL = 'https://check.torproject.org/api/ip'
_manager = None
_guard_installed = False

def local_host(host):
    return str(host).strip('[]').lower() in ('localhost', '127.0.0.1', '::1')

def public_host(host):
    host = str(host).encode('idna').decode('ascii').lower().rstrip('.')
    if not host or any((ord(c) < 33 for c in host)):
        raise ValueError('Invalid public hostname')
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError('Private addresses are not public sources')
    except ValueError as exc:
        if 'Private addresses' in str(exc):
            raise
        if '.' not in host or host.endswith(('.local', '.localhost', '.internal', '.home', '.lan')):
            raise ValueError('Choose a public hostname') from None
    return host

def _audit(event, args):
    if _manager is None:
        return
    if getattr(_manager, 'mode', None) == 'system-vpn' and _manager.ready():
        return
    if event == 'socket.getaddrinfo':
        host = args[0]
        if host is not None and (not local_host(host)):
            raise PermissionError('Public web is paused by the Observatory network control')
    elif event in ('socket.connect', 'socket.sendto'):
        address = args[1] if event == 'socket.connect' else args[-1]
        if isinstance(address, tuple) and (not local_host(address[0])):
            raise PermissionError('Public web is paused by the Observatory network control')

def install(manager):
    global _manager, _guard_installed
    _manager = manager
    if not _guard_installed:
        sys.addaudithook(_audit)
        _guard_installed = True

def read_exact(sock, count):
    result = bytearray()
    while len(result) < count:
        part = sock.recv(count - len(result))
        if not part:
            raise ConnectionError('Tor closed the proxy connection')
        result.extend(part)
    return bytes(result)

def socks_connect(host, port, timeout, checking=False):
    manager = _manager
    if manager is None:
        raise ConnectionError('Private web transport is not configured')
    if not checking and (not manager.ready()):
        raise ConnectionError('Public web activity is paused until Tor is verified')
    host = public_host(host)
    sock = socket.create_connection(('127.0.0.1', manager.port), timeout)
    try:
        sock.sendall(b'\x05\x01\x00')
        if read_exact(sock, 2) != b'\x05\x00':
            raise ConnectionError('Proxy is not a SOCKS5 service')
        encoded = host.encode('idna')
        if len(encoded) > 255:
            raise ValueError('Hostname is too long')
        sock.sendall(b'\x05\x01\x00\x03' + bytes([len(encoded)]) + encoded + struct.pack('!H', port))
        version, status, reserved, kind = read_exact(sock, 4)
        if version != 5 or status:
            raise ConnectionError('Tor could not connect to this destination (code ' + str(status) + ')')
        if kind == 1:
            read_exact(sock, 4)
        elif kind == 4:
            read_exact(sock, 16)
        elif kind == 3:
            read_exact(sock, read_exact(sock, 1)[0])
        else:
            raise ConnectionError('Invalid SOCKS5 response')
        read_exact(sock, 2)
        return sock
    except Exception:
        sock.close()
        raise

def connection(host, port=443, timeout=45, checking=False):
    if getattr(_manager, 'mode', None) == 'system-vpn':
        from ..graphical_app.system_network import connection as system_connection
        return system_connection(_manager, host, port, timeout)
    public_host(host)
    conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=ssl.create_default_context())
    conn._create_connection = lambda address, timeout, source_address=None: socks_connect(host, port, timeout, checking)
    return conn

class TorHTTPS(urllib.request.HTTPSHandler):

    def __init__(self, checking=False):
        super().__init__()
        self.checking = checking

    def https_open(self, request):

        def create(host, **kwargs):
            parsed = urllib.parse.urlsplit('https://' + host)
            if local_host(parsed.hostname):
                return http.client.HTTPSConnection(host, **kwargs)
            return connection(parsed.hostname, parsed.port or 443, kwargs.get('timeout', 45), self.checking)
        return self.do_open(create, request)

class LocalHTTP(urllib.request.HTTPHandler):

    def http_open(self, request):
        if not local_host(urllib.parse.urlsplit(request.full_url).hostname):
            raise ValueError('Public sources require HTTPS when privacy is enabled')
        return self.do_open(http.client.HTTPConnection, request)

class SafeRedirect(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = (urllib.parse.urlsplit(req.full_url), urllib.parse.urlsplit(newurl))
        if not local_host(old.hostname) and local_host(new.hostname):
            raise ValueError('Public sources cannot redirect to local services')
        if old.scheme == 'https' and new.scheme != 'https':
            raise ValueError('HTTPS downgrade redirect refused')
        if old.hostname != new.hostname and (any((k.lower() in ('authorization', 'x-goog-api-key', 'x-api-key', 'cookie') for k in req.headers)) or req.data is not None):
            raise ValueError('Credential-bearing cross-host redirect refused')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def urlopen(request, timeout=45, checking=False):
    if getattr(_manager, 'mode', None) == 'system-vpn':
        from ..graphical_app.system_network import urlopen as system_urlopen
        return system_urlopen(_manager, request, timeout)
    url = request.full_url if isinstance(request, urllib.request.Request) else request
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http', 'https') or parsed.username or parsed.password:
        raise ValueError('Use HTTP(S) without embedded credentials')
    if checking and url != CHECK_URL:
        raise ValueError('Only the Tor check may bypass the readiness gate')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), LocalHTTP(), TorHTTPS(checking), SafeRedirect())
    return opener.open(request, timeout=timeout)

class PrivacyNetwork:

    def __new__(cls, runtime):
        from ..graphical_app.system_network import SystemNetwork
        return SystemNetwork(runtime)

    def __init__(self, runtime):
        self.rt = runtime
        self.lock = threading.RLock()
        self.port = 17851
        self.path = runtime.data / 'privacy.json'
        self.home = runtime.data / 'tor'
        self.home.mkdir(exist_ok=True)
        self.executable = Path(__file__).parent / 'vendor' / 'tor' / 'tor' / 'tor.exe'
        self.process = None
        self.log_file = None
        self.verified_until = 0
        self.last_check = None
        self.exit_ip = None
        self.error = None
        self.progress = 0
        self.busy = False
        try:
            saved = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            saved = {}
        self.auto = bool(saved.get('automatic', True))
        install(self)

    def ready(self):
        return bool(self.process and self.process.poll() is None and (time.monotonic() < self.verified_until))

    def view(self):
        with self.lock:
            return {'installed': self.executable.is_file(), 'automatic': self.auto, 'busy': self.busy, 'running': bool(self.process and self.process.poll() is None), 'bootstrap_percent': self.progress, 'verified': self.ready(), 'public_web_paused': not self.ready(), 'direct_fallback': False, 'last_check': self.last_check, 'exit_ip': self.exit_ip if self.ready() else None, 'error': self.error, 'proxy_port': self.port, 'mode': 'app-only Tor', 'scope': 'Observatory HTTP(S) reads and cloud model requests; local Llama and local bus stay local.', 'limits': 'Does not cover your browser, other apps, native commands or arbitrary generated code. Accounts and submitted content can identify you. No untraceability guarantee.'}

    def configure(self, body):
        value = body.get('automatic')
        if type(value) is not bool:
            raise ValueError('Automatic connection must be true or false')
        with self.lock:
            self.auto = value
            self.path.write_text(json.dumps({'automatic': value}), encoding='utf-8')
        if not value:
            self.close()
        return self.view()

    def start(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                return self.view()
            if not self.executable.is_file():
                raise ValueError('The official Tor client is missing from this package')
            self.verified_until = 0
            self.progress = 0
            self.error = None
            config = self.home / 'torrc'
            quote = lambda p: '"' + str(p.resolve()).replace('\\', '/') + '"'
            config.write_text('\n'.join(['ClientOnly 1', 'SocksPort 127.0.0.1:' + str(self.port), 'SocksPolicy accept 127.0.0.1', 'SocksPolicy reject *', 'SafeSocks 1', 'ClientRejectInternalAddresses 1', 'AvoidDiskWrites 1', 'DataDirectory ' + quote(self.home), 'GeoIPFile ' + quote(self.executable.parent.parent / 'data' / 'geoip'), 'GeoIPv6File ' + quote(self.executable.parent.parent / 'data' / 'geoip6'), 'Log notice stdout']), encoding='utf-8')
            if self.log_file:
                self.log_file.close()
            self.log_file = (self.home / 'connection.log').open('wb')
            self.process = subprocess.Popen([str(self.executable), '-f', str(config)], stdin=subprocess.DEVNULL, stdout=self.log_file, stderr=subprocess.STDOUT, cwd=self.executable.parent, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return self.view()

    def check(self):
        with self.lock:
            if self.busy:
                raise ValueError('A connection check is already running')
            self.busy = True
        try:
            if not self.process or self.process.poll() is not None:
                raise ConnectionError('Start the Tor connection first')
            with urlopen(CHECK_URL, timeout=45, checking=True) as response:
                result = json.loads(response.read(4096))
            if result.get('IsTor') is not True:
                raise ConnectionError('The independent endpoint did not confirm Tor')
            address = ipaddress.ip_address(result.get('IP', ''))
            if not address.is_global:
                raise ConnectionError('The endpoint returned an invalid exit address')
            with self.lock:
                self.exit_ip = str(address)
                self.last_check = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                self.verified_until = time.monotonic() + 300
                self.progress = 100
                self.error = None
        except Exception as exc:
            with self.lock:
                self.verified_until = 0
                self.error = str(exc)[:500]
        finally:
            with self.lock:
                self.busy = False
        return self.view()

    def loop(self):
        import re
        next_check = 0
        for _shared_tick in range(1):
            if not self.auto:
                continue
            try:
                self.start()
                log = (self.home / 'connection.log').read_text(encoding='utf-8', errors='replace')[-12000:]
                values = re.findall('Bootstrapped (\\d+)%', log)
                if values:
                    self.progress = int(values[-1])
                if self.progress == 100 and time.monotonic() >= next_check:
                    self.check()
                    next_check = time.monotonic() + (120 if self.ready() else 30)
            except Exception as exc:
                self.error = str(exc)[:500]
                self.verified_until = 0
                self.rt.stop.wait(15)

    def close(self):
        with self.lock:
            self.verified_until = 0
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self.process = None
            if self.log_file:
                self.log_file.close()
                self.log_file = None

class WorkerRoute:

    def __init__(self, state):
        self.mode = state.get('mode')
        self.enabled = self.mode == 'system-vpn' and (not state.get('public_web_paused', True))
        self.port = state.get('proxy_port', 17851)
        self.expires = time.monotonic() + 25 if self.enabled or state.get('verified') else 0

    def ready(self):
        return time.monotonic() < self.expires

def install_worker(state):
    install(WorkerRoute(state))
    urllib.request.urlopen = urlopen
