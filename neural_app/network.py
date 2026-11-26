"""Authenticated TCP events and UDP discovery for the single shared runtime."""
import hmac,json,secrets,socket,socketserver,threading,time

class Bus:
    def __init__(self,runtime,port=8798,discovery_port=8799,lan=False):
        self.runtime=runtime;self.port=port;self.discovery_port=discovery_port;self.lan=lan
        self.halt=threading.Event();self.peers=set();self.lock=threading.Lock();self.clients=threading.BoundedSemaphore(8)
        keyfile=runtime.data/'bus-key.txt'
        if not keyfile.exists():keyfile.write_text(secrets.token_urlsafe(32),encoding='utf8')
        self.key=keyfile.read_text(encoding='utf8').strip();self.errors=[]
        owner=self
        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                if not owner.clients.acquire(blocking=False):return
                self.connection.settimeout(5)
                try:
                    raw=self.rfile.readline(65537)
                    if len(raw)>65536:raise ValueError('Frame too large')
                    b=json.loads(raw)
                    if not hmac.compare_digest(str(b.get('token','')),owner.key):
                        self.wfile.write(b'{"error":"Authentication required"}\n');return
                    if b.get('op')=='subscribe':
                        with owner.lock:owner.peers.add(self.connection)
                        owner.runtime.delivery['subscribers']=len(owner.peers)
                        self.wfile.write(b'{"type":"subscribed"}\n');self.wfile.flush()
                        while not owner.halt.wait(1):
                            # Event delivery owns this connection until shutdown.
                            pass
                    elif b.get('op')=='reasoning_episode':
                        value=owner.runtime.ambient_cube_bus.publish({'target':b.get('target','reasoning-episode'),'kind':'input','origin':'authenticated-tcp-client','payload':{'command_id':b.get('command_id'),'reasoning_episode':b.get('command',{})}})
                        self.wfile.write((json.dumps(value)+'\n').encode())
                    elif b.get('op')=='control':
                        value=owner.runtime.ambient_cube_bus.publish({'target':'engine-controls','kind':'control','origin':'authenticated-tcp-client','payload':b.get('command',{})})
                        self.wfile.write((json.dumps(value)+'\n').encode())
                    elif b.get('op')=='control_value':
                        self.wfile.write((json.dumps(owner.runtime.engine_control_bus.inspect(b.get('id')),ensure_ascii=False)+'\n').encode())
                    elif b.get('op')=='control_list':
                        self.wfile.write((json.dumps(owner.runtime.engine_control_bus.view(b.get('offset',0),b.get('limit',128)))+'\n').encode())
                    elif b.get('op')=='lesson':
                        self.wfile.write((json.dumps(owner.runtime.causal.transmission())+'\n').encode())
                    elif b.get('op')=='publish':
                        value=owner.runtime.submit(b.get('section','pipeline'),b.get('data',{}))
                        self.wfile.write((json.dumps({'type':'accepted','job':value})+'\n').encode())
                    elif b.get('op')=='mesh_push':
                        value=owner.runtime.automatic_flow().add(b.get('text'),'Authenticated mesh peer')
                        self.wfile.write((json.dumps({'type':'mesh-input-accepted',**value})+'\n').encode())
                    elif b.get('op')=='mesh_pull':
                        self.wfile.write((json.dumps(owner.runtime.automatic_flow().pull(b.get('after',0)))+'\n').encode())
                    elif b.get('op')=='result':
                        self.wfile.write((json.dumps(owner.runtime.result(b['id']))+'\n').encode())
                    else:self.wfile.write(b'{"error":"Use publish, result, lesson, subscribe, mesh_push, mesh_pull, reasoning_episode, control, control_list or control_value"}\n')
                except Exception as e:
                    try:self.wfile.write((json.dumps({'error':str(e)})+'\n').encode())
                    except OSError:pass
                finally:
                    with owner.lock:owner.peers.discard(self.connection)
                    owner.runtime.delivery['subscribers']=len(owner.peers)
                    owner.clients.release()
        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address=False;daemon_threads=True
        self.server=Server(('0.0.0.0' if lan else '127.0.0.1',port),Handler)
        self.port=self.server.server_address[1]
        self.udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.udp.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        self.udp.bind(('0.0.0.0' if lan else '127.0.0.1',discovery_port));self.discovery_port=self.udp.getsockname()[1];self.udp.settimeout(.5)
        runtime.listeners.append(self.broadcast)
        self.thread=threading.Thread(target=self.server.serve_forever,name='neural-tcp-listener',daemon=True)
        self.discovery=threading.Thread(target=self.discover,name='neural-discovery',daemon=True)
        self.thread.start();self.discovery.start()

    def info(self):
        return {'tcp_host':'0.0.0.0' if self.lan else '127.0.0.1','tcp_port':self.port,'discovery_port':self.discovery_port,
                'scope':'LAN' if self.lan else 'This computer','subscribers':len(self.peers),'errors':self.errors[-3:],
                'protocol':'Newline-delimited JSON. token + op: publish, result, lesson, subscribe, mesh_push, mesh_pull, reasoning_episode, control, control_list or control_value. Discovery contains no private engine results or token.'}

    def broadcast(self,item):
        context=self.runtime.theology_public
        research=dict(self.runtime.research_public)
        if context or research:item={**item,'inference_context':{'theology':dict(context) if context else None,'design_research':research}}
        raw=(json.dumps(item)+'\n').encode()
        with self.lock:
            self.runtime.delivery['events']+=1
            for peer in list(self.peers):
                try:
                    peer.sendall(raw)
                    self.runtime.delivery['peer_writes']+=1;self.runtime.delivery['bytes_written']+=len(raw)
                except OSError:self.peers.discard(peer)
            self.runtime.delivery['subscribers']=len(self.peers)

    def announcement(self):return {'app':'Neural App','protocol':'neural-btq-v1','tcp_port':self.port,'authentication':True,'type':'neural-discovery'}

    def discover(self):
        next_send=0
        while not self.halt.is_set():
            if time.monotonic()>=next_send:
                try:self.udp.sendto(json.dumps(self.announcement()).encode(),('255.255.255.255' if self.lan else '127.255.255.255',self.discovery_port))
                except OSError as e:self.errors.append(str(e));self.errors=self.errors[-3:]
                next_send=time.monotonic()+10
            try:
                raw,addr=self.udp.recvfrom(1024)
                if raw.strip()==b'NEURAL_DISCOVER':self.udp.sendto(json.dumps(self.announcement()).encode(),addr)
            except socket.timeout:pass
            except OSError:break

    def close(self):
        self.halt.set();self.server.shutdown();self.server.server_close();self.udp.close()
        with self.lock:
            for peer in self.peers:
                try:peer.shutdown(socket.SHUT_RDWR);peer.close()
                except OSError:pass
            self.peers.clear()
            self.runtime.delivery['subscribers']=0
        if self.broadcast in self.runtime.listeners:self.runtime.listeners.remove(self.broadcast)
        self.discovery.join(2)
