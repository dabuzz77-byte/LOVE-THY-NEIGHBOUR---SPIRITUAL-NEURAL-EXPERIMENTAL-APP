"""Neural Atelier - native Python desktop field and app bus."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math, random, threading, time, json, socket, os, queue, subprocess, sys, struct
from pathlib import Path
from collections import deque
from atelier_bus import LocalBus
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
APPS=Path.home()/'Desktop/CHAT GPT APPS'
BG='#080d19'; PANEL='#0d1626'; CYAN='#59e6db'; GOLD='#e5b777'; TEXT='#dce8f4'; MUTED='#73899f'

class Engine:
    def __init__(self):
        self.lock=threading.RLock(); self.stop=threading.Event(); self.running=True
        self.mode='perimeter'; self.depth=5; self.force_true=False; self.ticks=0; self.stimulus=0.; self.ms=0.
        self.feedback_gain=.35; self.effective_bias=.5; self.script_signal=0.; self.script_at=0.; self.script_samples=0; self.external_signal=0.; self.external_at=0.; self.feedback_terms={}
        self.rng=random.Random(int.from_bytes(os.urandom(32),'big')); self.bit_source=os.urandom; self.window_ones=0; self.noise=.22; self.bias=.5; self.stochastic=True; self.bits=[0]*96; self.bit_history=deque(maxlen=8192); self.walk=0.; self.ones=0; self.generated=0; self.entropy=0.; self.binary_signal=0.
        self.values=[0.]*96; self.history=deque([0.]*160,maxlen=160)
        r=random.Random(7854); self.weights=[[r.uniform(-.45,.45) for _ in range(8)] for _ in range(96)]
        self.thread=threading.Thread(target=self.loop,daemon=True)
    def region(self):
        return [(x,y) for y in range(32) for x in range(32) if self.mode=='field'
            or (self.mode=='core' and (x-15.5)**2+(y-15.5)**2<=self.depth**2)
            or (self.mode=='perimeter' and min(x,y,31-x,31-y)<self.depth)]
    def step(self):
        t=time.perf_counter()
        with self.lock:
            old=self.values
            if self.stochastic:
                # Feedback changes probabilities, never substitutes a fixed bit value.
                now=time.monotonic()
                network=sum(old)/96
                external=self.external_signal if now-self.external_at<15 else 0.
                script=self.script_signal if now-self.script_at<15 else 0.
                self.feedback_terms=dict(network=network,observatory=external,scripts=script,walk=self.walk)
                drive=self.feedback_gain*(.50*math.tanh(network*3)+.25*external+.20*script+.05*self.walk)
                probabilities=[max(.01,min(.99,self.bias+drive+self.feedback_gain*.12*old[i])) for i in range(96)]
                self.effective_bias=sum(probabilities)/96
                # One OS entropy request per batch rather than 96 separate requests.
                random_words=struct.unpack('<96I',self.bit_source(384))
                self.bits=[int(word/4294967296<p) for word,p in zip(random_words,probabilities)]
                for bit in self.bits:
                    if len(self.bit_history)==self.bit_history.maxlen: self.window_ones-=self.bit_history[0]
                    self.bit_history.append(bit); self.window_ones+=bit
                self.ones+=sum(self.bits); self.generated+=96
                self.binary_signal=sum(self.bits)/48-1
                self.walk=max(-1.,min(1.,self.walk*.97+self.rng.gauss(0,.045)))
                p=self.window_ones/len(self.bit_history)
                self.entropy=-(p*math.log2(p)+(1-p)*math.log2(1-p)) if 0<p<1 else 0.
            else:
                self.binary_signal=0.; self.walk=0.
            self.values=[math.tanh(sum(w*old[(i+j*11+1)%96] for j,w in enumerate(self.weights[i]))+.24*math.sin(self.ticks*.07+i*.31)+self.stimulus+(self.noise*(self.rng.gauss(0,.45)+(self.bits[i]*2-1)*.3+self.walk*.4) if self.stochastic else 0)) for i in range(96)]
            self.stimulus*=.96; self.ticks+=1; self.history.append(sum(abs(v) for v in self.values)/96)
            self.ms=(time.perf_counter()-t)*1000
    def loop(self):
        while not self.stop.is_set():
            if self.running: self.step()
            self.stop.wait(.05)
    def snapshot(self):
        with self.lock:
            return dict(ticks=self.ticks,mode=self.mode,depth=self.depth,running=self.running,values=self.values[:],history=list(self.history),nodes=len(self.region()),ms=self.ms,force_true=self.force_true,noise=self.noise,bias=self.bias,stochastic=self.stochastic,bits=self.bits[:],entropy=self.entropy,generated=self.generated,binary_signal=self.binary_signal,walk=self.walk,effective_bias=self.effective_bias,feedback_gain=self.feedback_gain,feedback_terms=self.feedback_terms.copy(),script_samples=self.script_samples)
    def command(self,text):
        c=text.strip().lower()
        with self.lock:
            if c in ('pause','stop','pause engine'): self.running=False
            elif c in ('resume','start','run','run all','resume engine'): self.running=True
            elif c in ('core','runall at core','run at core','mode core'): self.mode='core'
            elif c in ('perimeter','run at depth of perimeter','runall at perimeter','mode perimeter'): self.mode='perimeter'
            elif c in ('field','mode field'): self.mode='field'
            elif c.startswith('depth '):
                d=int(c.split()[1])
                if not 1<=d<=15: raise ValueError('Depth must be 1 to 15')
                self.depth=d
            elif c in ('true on','true off'): self.force_true=c.endswith('on')
            elif c in ('stochastic on','stochastic off'): self.stochastic=c.endswith('on')
            elif c.startswith(('noise ','bias ','feedback ')):
                key,value=c.split(); value=float(value)
                if not math.isfinite(value) or not 0<=value<=1: raise ValueError('Use a number between 0 and 1')
                setattr(self,'feedback_gain' if key=='feedback' else key,value)
            elif c=='pulse': self.stimulus=.9
            else: raise ValueError('Try core, perimeter, field, depth 5, pulse, pause, resume, true on/off, sync, scan, noise 0.3, bias 0.5, feedback 0.35, stochastic on/off.')
        return 'Applied: '+text
    def close(self):
        self.stop.set()
        if self.thread.is_alive(): self.thread.join(2)

class Bridge:
    def __init__(self,engine):
        self.engine=engine; self.stop=threading.Event(); self.pending=threading.Event(); self.events=queue.Queue(maxsize=512)
        self.status={'observatory':'Waiting','flux':'Waiting'}; self.tx=0; self.rx=0; self.last_obs=0
        self.thread=threading.Thread(target=self.loop,daemon=True)
    def log(self,kind,text):
        try: self.events.put_nowait((kind,text))
        except queue.Full: pass
    def loop(self):
        connection=APPS/'Postscarcity Observatory v4/graphical_app/data/connection.json'
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.bind(('127.0.0.1',0)); sock.settimeout(.15)
        next_send=0; config={}
        try:
            while not self.stop.is_set():
                now=time.monotonic()
                if now>=next_send or self.pending.is_set():
                    self.pending.clear(); next_send=now+5
                    packet={k:v for k,v in self.engine.snapshot().items() if k not in ('values','history')}
                    packet['processed_state']=True if packet['force_true'] else packet['running']
                    try:
                        config=json.loads(connection.read_text(encoding='utf-8')); port=int(config['port'])
                        if not 1<=port<=65535: raise ValueError('Invalid port')
                        base=dict(token=config['token'],pid=os.getpid(),name='Neural Atelier')
                        for p in (dict(type='subscribe'),dict(type='event',topic='neural_atelier.field',data=packet)):
                            sock.sendto(json.dumps({**base,**p}).encode(),('127.0.0.1',port)); self.tx+=1
                        self.status['observatory']='Live' if now-self.last_obs<12 else 'Awaiting reply'
                    except (OSError,ValueError,KeyError,TypeError): self.status['observatory']='Offline'
                    try:
                        p=dict(node_id='neural-atelier-field',context=json.dumps(packet),state='good')
                        with socket.create_connection(('127.0.0.1',9999),timeout=.6) as tcp:
                            tcp.sendall(json.dumps(p).encode()+b'\n'); raw=b''
                            while b'\n' not in raw and len(raw)<65536:
                                chunk=tcp.recv(4096)
                                if not chunk: break
                                raw+=chunk
                            reply=json.loads(raw)
                            if reply.get('status')!='ACK' or reply.get('node',{}).get('node_id')!=p['node_id']: raise ValueError('Unconfirmed receipt')
                            self.tx+=1; self.rx+=1; self.status['flux']='ACK received'; self.log('FLUX','Field delivered; committed ledger receipt received')
                    except (OSError,ValueError,KeyError,TypeError): self.status['flux']='Offline'
                try:
                    raw,addr=sock.recvfrom(65535)
                    if addr!=('127.0.0.1',config.get('port')): continue
                    event=json.loads(raw); self.last_obs=time.monotonic(); self.rx+=1; self.status['observatory']='Live'
                    kind=event.get('type','event')
                    if kind in ('attached','module','command','error'): self.log('OBS',str(kind)+' received')
                    data=event.get('data',{}); v=data.get('neural_output') if isinstance(data,dict) else None
                    if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v):
                        with self.engine.lock:
                            self.engine.stimulus=max(-1,min(1,v))*.15
                            self.engine.external_signal=max(-1,min(1,v)); self.engine.external_at=time.monotonic()
                except (OSError,ValueError,AttributeError): pass
        finally: sock.close()
    def close(self):
        self.stop.set()
        if self.thread.is_alive(): self.thread.join(3)

class LayerCanvas(tk.Canvas):
    def _create(self,itemType,args,kw):
        if 'tags' not in kw: kw['tags']='dynamic'
        return super()._create(itemType,args,kw)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('NEURAL ATELIER | Living field studio'); self.geometry('1500x940'); self.minsize(1180,760); self.configure(bg=BG)
        self.engine=Engine(); self.bus=Bridge(self.engine); self.local_bus=LocalBus(self.engine,DATA); self.children_processes=[]; self.frame_id=0; self.last_ui=0.; self.last_graphics=0.; self.frame_ms=0.; self.graphics_fps=20; self._last_grid=None; self.view='portal'; self.logs=deque(maxlen=7)
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.portal_cache=None; self.portal_size=None; self.build(); self.scan(); self.engine.thread.start(); self.bus.thread.start()
        self.log('SYSTEM','96-node recurrent engine started | 20 updates / second')
        self.log('GUIDE','Try: runall at core  /  depth 8  /  pulse')
        self.after(40,self.animate)
    def button(self,parent,text,fn,accent=False):
        return tk.Button(parent,text=text,command=fn,bg='#153a40' if accent else '#152237',fg=CYAN if accent else TEXT,activebackground='#24515c',activeforeground='white',relief='flat',bd=0,padx=14,pady=9,font=('Segoe UI',10),cursor='hand2')
    def build(self):
        header=tk.Frame(self,bg=BG); header.pack(fill='x',padx=25,pady=(18,12))
        tk.Label(header,text='◉',fg=CYAN,bg=BG,font=('Segoe UI',29)).pack(side='left',padx=(0,12))
        brand=tk.Frame(header,bg=BG); brand.pack(side='left')
        tk.Label(brand,text='N E U R A L   A T E L I E R',fg=TEXT,bg=BG,font=('Segoe UI',18,'bold')).pack(anchor='w')
        tk.Label(brand,text='LIVING FIELD STUDIO   /   PYTHON DESKTOP',fg=MUTED,bg=BG,font=('Consolas',9)).pack(anchor='w')
        self.runlabel=tk.Label(header,text='● ENGINE RUNNING',fg=CYAN,bg=BG,font=('Consolas',10)); self.runlabel.pack(side='right',padx=15)
        self.button(header,'Pause / resume',self.toggle).pack(side='right')
        body=tk.Frame(self,bg=BG); body.pack(fill='both',expand=True,padx=25)
        side=tk.Frame(body,bg=PANEL,width=240); side.pack(side='left',fill='y',padx=(0,14)); side.pack_propagate(False)
        tk.Label(side,text='WORKSPACE',bg=PANEL,fg=MUTED,font=('Consolas',10)).pack(anchor='w',padx=18,pady=(20,12))
        for title,view in [('01   Portal observatory','portal'),('02   Neural field','field'),('03   Spatial matrix','matrix'),('04   App constellation','apps')]:
            self.button(side,title,lambda v=view:self.set_view(v)).pack(fill='x',padx=12,pady=3)
        tk.Label(side,text='DISCOVERED APPLICATIONS',bg=PANEL,fg=MUTED,font=('Consolas',9)).pack(anchor='w',padx=18,pady=(24,10))
        self.appslist=tk.Listbox(side,bg=PANEL,fg='#a8bbce',selectbackground='#1b434c',selectforeground=CYAN,relief='flat',highlightthickness=0,font=('Segoe UI',10),exportselection=False)
        self.appslist.pack(fill='both',expand=True,padx=12)
        self.button(side,'Open selected app folder',self.open_app).pack(fill='x',padx=12,pady=6)
        self.button(side,'Start feedback worker',lambda:self.add_worker(str(ROOT/'feedback_worker.py'))).pack(fill='x',padx=12,pady=4)
        self.button(side,'Add Python worker…',self.add_worker).pack(fill='x',padx=12,pady=6)
        self.button(side,'Stop my workers',self.stop_workers).pack(fill='x',padx=12,pady=(0,15))
        main=tk.Frame(body,bg=BG); main.pack(side='left',fill='both',expand=True)
        stats=tk.Frame(main,bg=BG); stats.pack(fill='x',pady=(0,12))
        self.cards=[]
        for title in ['ENGINE CYCLES','ACTIVE SPATIAL CELLS','BUS EXCHANGE','BINARY ENTROPY']:
            card=tk.Frame(stats,bg=PANEL); card.pack(side='left',fill='x',expand=True,padx=(0,8))
            tk.Label(card,text=title,bg=PANEL,fg=MUTED,font=('Consolas',9)).pack(anchor='w',padx=15,pady=(12,3))
            value=tk.Label(card,text='—',bg=PANEL,fg=TEXT,font=('Segoe UI',22)); value.pack(anchor='w',padx=15,pady=(0,10)); self.cards.append(value)
        bar=tk.Frame(main,bg=PANEL); bar.pack(fill='x')
        self.viewlabel=tk.Label(bar,text='THE PORTAL OBSERVATORY',bg=PANEL,fg=TEXT,font=('Segoe UI',13,'bold')); self.viewlabel.pack(side='left',padx=18,pady=12)
        for mode in ('perimeter','core','field'):
            self.button(bar,mode.title(),lambda m=mode:self.execute(m)).pack(side='right',padx=3,pady=5)
        self.canvas=LayerCanvas(main,bg='#090f1d',highlightthickness=0); self.canvas.pack(fill='both',expand=True)
        controls=tk.Frame(main,bg=PANEL); controls.pack(fill='x')
        tk.Label(controls,text='BOUNDARY DEPTH',fg=MUTED,bg=PANEL,font=('Consolas',9)).pack(side='left',padx=15)
        self.depth=tk.Scale(controls,from_=1,to=15,orient='horizontal',length=200,bg=PANEL,fg=CYAN,troughcolor='#203249',highlightthickness=0,command=lambda x:self.change_depth(x)); self.depth.set(5); self.depth.pack(side='left')
        self.button(controls,'Inject pulse',lambda:self.execute('pulse'),True).pack(side='right',padx=12,pady=8)
        stoch=tk.Frame(main,bg=PANEL); stoch.pack(fill='x',pady=(2,0))
        tk.Label(stoch,text='STOCHASTIC SOURCE',fg=GOLD,bg=PANEL,font=('Consolas',9)).pack(side='left',padx=15)
        self.button(stoch,'On / off',lambda:self.execute('stochastic off' if self.engine.stochastic else 'stochastic on')).pack(side='right',padx=10,pady=5)
        for name,default in [('noise',.22),('bias',.5),('feedback',.35)]:
            tk.Label(stoch,text=name.upper(),fg=MUTED,bg=PANEL,font=('Consolas',9)).pack(side='left',padx=(10,4))
            slider=tk.Scale(stoch,from_=0,to=1,resolution=.01,orient='horizontal',length=85,bg=PANEL,fg=CYAN,troughcolor='#203249',highlightthickness=0,command=lambda x,n=name:self.set_stochastic(n,x)); slider.set(default); slider.pack(side='left')
        self.bitlabel=tk.Label(main,text='',fg=GOLD,bg=BG,font=('Consolas',9)); self.bitlabel.pack(anchor='w',pady=(6,0))
        self.connection=tk.Label(main,text='',fg=MUTED,bg=BG,font=('Consolas',10)); self.connection.pack(anchor='w',pady=9)
        foot=tk.Frame(self,bg=PANEL); foot.pack(fill='x',padx=25,pady=(12,20))
        tk.Label(foot,text='PROMPT → COMMAND',fg=CYAN,bg=PANEL,font=('Consolas',10,'bold')).pack(anchor='w',padx=15,pady=(12,5))
        row=tk.Frame(foot,bg=PANEL); row.pack(fill='x',padx=15)
        self.entry=tk.Entry(row,bg='#080f1b',fg=TEXT,insertbackground=CYAN,relief='flat',font=('Consolas',12)); self.entry.pack(side='left',fill='x',expand=True,ipady=10); self.entry.bind('<Return>',lambda e:self.submit())
        self.button(row,'Execute ↵',self.submit,True).pack(side='left',padx=(10,0))
        self.loglabel=tk.Label(foot,text='',justify='left',anchor='nw',fg=MUTED,bg=PANEL,font=('Consolas',9),height=4); self.loglabel.pack(fill='x',padx=15,pady=10)
    def set_stochastic(self,name,value):
        with self.engine.lock: setattr(self.engine,'feedback_gain' if name=='feedback' else name,float(value))
    def change_depth(self,x):
        if hasattr(self,'engine'):
            with self.engine.lock: self.engine.depth=int(float(x))
    def scan(self):
        self.apps=[p for p in sorted(APPS.iterdir()) if p.is_dir()] if APPS.exists() else []
        self.appslist.delete(0,'end')
        for p in self.apps: self.appslist.insert('end','  '+p.name)
        self.log('SCAN',str(len(self.apps))+' applications discovered; integrations shown by measured status')
    def open_app(self):
        selection=self.appslist.curselection()
        if selection: os.startfile(str(self.apps[selection[0]]))
    def set_view(self,v): self.view=v; self.viewlabel.config(text={'portal':'THE PORTAL OBSERVATORY','field':'THE LIVING FIELD','matrix':'SPATIAL PROCESSING MATRIX','apps':'APPLICATION CONSTELLATION'}[v])
    def toggle(self): self.execute('pause' if self.engine.running else 'resume')
    def submit(self):
        text=self.entry.get().strip()
        if text: self.execute(text); self.entry.delete(0,'end')
    def execute(self,text):
        try:
            if text.lower()=='sync': self.bus.pending.set(); result='Bus synchronization requested'
            elif text.lower()=='scan': self.scan(); result='Application catalog refreshed'
            else: result=self.engine.command(text)
            self.log('COMMAND',result)
            with (DATA/'commands.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(dict(time=time.time(),command=text,result=result))+'\n')
        except (ValueError,IndexError,OSError) as exc: self.log('NOTICE',str(exc))
    def log(self,kind,text):
        self.logs.append(time.strftime('%H:%M:%S')+'  '+kind.ljust(8)+' '+text)
        if hasattr(self,'loglabel'): self.loglabel.config(text='\n'.join(list(self.logs)[-4:]))
    def add_worker(self,path=None):
        path=path or filedialog.askopenfilename(title='Select a Python worker to run continuously',initialdir=str(ROOT),filetypes=[('Python scripts','*.py')])
        if not path: return
        output=(DATA/('worker-'+str(time.time_ns())+'.log')).open('w',encoding='utf-8')
        try:
            env=os.environ.copy(); env['NEURAL_ATELIER_CONNECTION']=str(self.local_bus.path); env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
            process=subprocess.Popen([sys.executable,path],cwd=str(Path(path).parent),env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            threading.Thread(target=self.read_worker,args=(process,output,Path(path).name),daemon=True).start()
            self.children_processes.append((process,output,Path(path).name)); self.log('WORKER','Started '+Path(path).name+' | PID '+str(process.pid))
        except OSError as exc: output.close(); self.log('ERROR',str(exc))
    def read_worker(self,process,output,name):
        import hashlib
        try:
            while True:
                raw=process.stdout.read1(4096)
                if not raw: break
                text=raw.decode('utf-8',errors='replace')
                output.write(text); output.flush()
                # Numerical output drives the signal directly; other output uses
                # a stable bounded fingerprint. Neither path executes text.
                try:
                    value=float(text.strip().splitlines()[-1])
                    signal=math.tanh(value) if math.isfinite(value) else 0.
                except (ValueError,IndexError):
                    digest=hashlib.blake2s(raw,digest_size=4).digest()
                    signal=int.from_bytes(digest,'big')/(2**32-1)*2-1
                with self.engine.lock:
                    self.engine.script_signal=.8*self.engine.script_signal+.2*signal
                    self.engine.script_at=time.monotonic(); self.engine.script_samples+=1
        except (OSError,ValueError): pass
        finally:
            if process.stdout: process.stdout.close()
    def stop_workers(self):
        for p,f,name in self.children_processes:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=2)
                except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=2)
            f.close()
        self.children_processes=[]; self.log('WORKER','Selected workers stopped')
    def project(self,x,y,z,w,h,t):
        a=t*.13; x,z=x*math.cos(a)+z*math.sin(a),z*math.cos(a)-x*math.sin(a)
        b=.35; y,z=y*math.cos(b)-z*math.sin(b),z*math.cos(b)+y*math.sin(b)
        scale=min(w,h)*.31/(1+z*.22)
        return w*.5+x*scale,h*.47+y*scale,z
    def draw_field(self,w,h,s,t):
        c=self.canvas; cx=w/2; cy=h*.47; radius=min(w,h)*.36
        for r in (1.08,1.18,1.25):
            c.create_oval(cx-radius*r,cy-radius*r*.46,cx+radius*r,cy+radius*r*.46,outline='#192f43')
        for a in range(0,360,5):
            rad=math.radians(a); r=radius*1.19; r2=r+(7 if a%30==0 else 3)
            c.create_line(cx+math.cos(rad)*r,cy+math.sin(rad)*r*.46,cx+math.cos(rad)*r2,cy+math.sin(rad)*r2*.46,fill='#3c5a65')
        points=[]
        for i in range(96):
            a=i*math.pi*(3-math.sqrt(5)); y=1-2*(i+.5)/96; r=math.sqrt(1-y*y)
            pulse=1+s['values'][i]*.09
            points.append(self.project(math.cos(a)*r*pulse,y*pulse,math.sin(a)*r*pulse,w,h,t))
        for i,p in enumerate(points):
            for j in ((i+8)%96,(i+13)%96):
                q=points[j]
                if (p[0]-q[0])**2+(p[1]-q[1])**2<(radius*.75)**2:
                    c.create_line(p[0],p[1],q[0],q[1],fill='#224656' if p[2]<0 else '#152b3d')
        for i in sorted(range(96),key=lambda k:points[k][2],reverse=True):
            x,y,z=points[i]; r=2.2+(1-z)*1.2; v=abs(s['values'][i]); color=GOLD if v>.25 else CYAN
            c.create_oval(x-r*2.6,y-r*2.6,x+r*2.6,y+r*2.6,fill='#143040',outline='')
            c.create_oval(x-r,y-r,x+r,y+r,fill=color if z<.2 else '#356a78',outline='')
        for k in range(3):
            coords=[]
            for i in range(181):
                a=i*math.tau/180; b=a*3+t*.5+k*2.1
                x=(.68+.12*math.cos(b))*math.cos(a); z=(.68+.12*math.cos(b))*math.sin(a); y=.12*math.sin(b)
                px,py,_=self.project(x,y,z,w,h,t); coords.extend((px,py))
            c.create_line(*coords,fill=['#59e6db','#367d8c','#d2a368'][k],width=1.3,smooth=True)
        c.create_text(22,22,text='RECURRENT NETWORK  /  96 NODES · 768 WEIGHTS',anchor='nw',fill=MUTED,font=('Consolas',9))
        c.create_text(22,44,text='LOCAL COMPUTATION + LIVE BUS TELEMETRY',anchor='nw',fill='#3b6578',font=('Consolas',8))
        c.create_text(w-22,22,text=s['mode'].upper()+' / DEPTH '+str(s['depth']),anchor='ne',fill=GOLD,font=('Consolas',10))
        self.wave(w,h,s)
    def draw_portal(self,w,h,s,t):
        from PIL import Image, ImageTk, ImageEnhance
        c=self.canvas
        if self.portal_size!=(w,h):
            source=Image.open(ROOT/'portal-reference.jpg').convert('RGB')
            # The supplied JPEG contains a white page margin to the right.
            source=source.crop((0,0,round(source.width*.599),source.height))
            source.thumbnail((int(w*.8),h),Image.Resampling.LANCZOS)
            bg=Image.new('RGB',(w,h),'#090f1d')
            bg.paste(source,(max(0,int(w*.32-source.width/2)),int((h-source.height)/2)))
            veil=Image.new('RGBA',(w,h),(5,13,26,0))
            from PIL import ImageDraw
            draw=ImageDraw.Draw(veil)
            for x in range(w):
                alpha=int(40+155*max(0,(x/w-.35)/.65))
                draw.line((x,0,x,h),fill=(5,13,26,alpha))
            bg=Image.alpha_composite(bg.convert('RGBA'),veil)
            self.portal_cache=ImageTk.PhotoImage(bg); self.portal_size=(w,h)
        if not c.find_withtag('portal_background'):
            c.create_image(0,0,image=self.portal_cache,anchor='nw',tags=('grid','portal_background'))
        else:
            c.itemconfigure('portal_background',image=self.portal_cache)
        c.tag_lower('portal_background')
        rng=random.Random(41)
        for i in range(65):
            x=rng.random()*w; y=rng.random()*h*.85; r=.7+1.2*(.5+.5*math.sin(t*.6+i))
            c.create_oval(x-r,y-r,x+r,y+r,fill='#8aa4ad' if i%5 else GOLD,outline='')
        cx=w*.72; cy=h*.43; radius=min(w*.2,h*.28)
        for k in range(4):
            r=radius*(1+k*.14)
            c.create_oval(cx-r,cy-r*.4,cx+r,cy+r*.4,outline=['#294450','#3a6871','#223949','#20313e'][k])
        points=[]
        for i in range(96):
            a=i*math.pi*(3-math.sqrt(5))+t*.09; z=1-2*(i+.5)/96; rr=math.sqrt(1-z*z)
            x=cx+math.cos(a)*rr*radius; y=cy+z*radius*.85+math.sin(a)*rr*radius*.12
            points.append((x,y))
        for i,(x,y) in enumerate(points):
            xx,yy=points[(i+13)%96]
            if (x-xx)**2+(y-yy)**2<radius**2*.6: c.create_line(x,y,xx,yy,fill='#244954')
            r=1.4+abs(s['values'][i])*4
            c.create_oval(x-r,y-r,x+r,y+r,fill=CYAN if i%5 else GOLD,outline='')
        c.create_text(24,22,text='P O R T A L   /   L I V E   O B S E R V A T O R Y',fill=TEXT,anchor='nw',font=('Consolas',11))
        c.create_text(24,46,text='STONE · LIGHT · SIGNAL',fill=GOLD,anchor='nw',font=('Consolas',9))
        c.create_text(cx,cy+radius+32,text=s['mode'].upper()+'  /  DEPTH '+str(s['depth']),fill=GOLD,font=('Consolas',11))
        c.create_text(cx,cy+radius+55,text='96 recurrent nodes · 768 weights',fill=MUTED,font=('Consolas',9))
        if s['stochastic']:
            for i,bit in enumerate(s['bits'][:42]):
                x=w*.46+(i%14)*w*.037; y=75+((i//14)*67+t*(13+i%5))%max(80,h-180)
                c.create_text(x,y,text=str(bit),fill='#37636b' if bit else '#263949',font=('Consolas',9))
        self.wave(w,h,s)
    def wave(self,w,h,s):
        c=self.canvas; base=h-24
        for y in (base-40,base-20,base): c.create_line(22,y,w-22,y,fill='#152435')
        coords=[]
        for i,v in enumerate(s['history']): coords.extend((22+i*(w-44)/159,base-v*120))
        c.create_line(*coords,fill=CYAN,width=1.5)
        c.create_text(23,base-60,text='MEAN NETWORK ACTIVATION',fill=MUTED,anchor='nw',font=('Consolas',8))
    def draw_matrix(self,w,h,s):
        size=min(w-200,h-100)/32; ox=(w-size*32)/2; oy=45
        active=set(self.engine.region())
        for y in range(32):
            for x in range(32):
                v=abs(s['values'][(x+y*3)%96]); col=('#327b80' if v<.2 else '#62dacc') if (x,y) in active else '#122236'
                self.canvas.create_rectangle(ox+x*size,oy+y*size,ox+(x+1)*size-2,oy+(y+1)*size-2,fill=col,outline='')
        self.canvas.create_text(w/2,h-24,text=f"{s['mode'].upper()}  ·  {s['nodes']} selected cells  ·  32 × 32 spatial field",fill=GOLD,font=('Consolas',11))
    def draw_apps(self,w,h,s,t):
        c=self.canvas; cx=w/2; cy=h/2; r=min(w,h)*.35; n=max(1,len(self.apps))
        for i,p in enumerate(self.apps):
            a=i*math.tau/n-math.pi/2; x=cx+math.cos(a)*r*1.22; y=cy+math.sin(a)*r
            live=('FluxBus' in p.name and self.bus.status['flux']=='ACK received') or ('Observatory v4' in p.name and self.bus.status['observatory']=='Live')
            col=CYAN if live else '#284054'; c.create_line(cx,cy,x,y,fill=col)
            c.create_oval(x-4,y-4,x+4,y+4,fill=col,outline='')
            c.create_text(x,y+(13 if y>cy else -13),text=p.name[:24],fill=TEXT if live else MUTED,font=('Segoe UI',8))
        c.create_oval(cx-48,cy-48,cx+48,cy+48,fill='#15313b',outline=CYAN,width=2)
        c.create_text(cx,cy,text='ATELIER\nLOCAL BUS',fill=CYAN,font=('Consolas',11),justify='center')
        c.create_text(20,20,text='CYAN = CONFIRMED EXCHANGE   /   DIM = DISCOVERED ONLY',fill=MUTED,anchor='nw',font=('Consolas',9))
    def animate(self):
        # Minimized windows skip graphics; the engine and bus continue independently.
        if self.state()=='iconic':
            self.after(250,self.animate); return
        started=time.perf_counter()
        s=self.engine.snapshot(); self.frame_id+=1
        if started-self.last_ui>=.25:
            self.update_status(s)
            self.last_ui=started
        for _ in range(3):
            try: kind,text=self.bus.events.get_nowait(); self.log(kind,text)
            except queue.Empty: break
        for p,f,name in self.children_processes[:]:
            if p.poll() is not None:
                self.log('WORKER',name+' exited: '+str(p.returncode)); f.close(); self.children_processes.remove((p,f,name))
        self.render(s,started)
        self.frame_ms=(time.perf_counter()-started)*1000
        self.after(max(10,int(1000/self.graphics_fps-self.frame_ms)),self.animate)
    def update_status(self,s):
        self.cards[0].config(text=f"{s['ticks']:,}"); self.cards[1].config(text=str(s['nodes']))
        self.cards[2].config(text=f'{self.bus.tx} ↑  {self.bus.rx} ↓'); self.cards[3].config(text=f"{s['entropy']:.3f} H")
        self.bitlabel.config(text=(''.join(map(str,s['bits'][:56]))+f"   {s['generated']:,} bits · p(1)={s['effective_bias']:.3f} · feedback={s['feedback_gain']:.2f}") if s['stochastic'] else 'STOCHASTIC SOURCE PAUSED')
        self.runlabel.config(text='● ENGINE RUNNING' if s['running'] else '○ ENGINE PAUSED',fg=CYAN if s['running'] else GOLD)
        self.connection.config(text=f"FLUXBUS  {self.bus.status['flux']}    ↔    OBSERVATORY V4  {self.bus.status['observatory']}    |    {len(self.local_bus.clients)} local clients · {len(self.apps)} apps found")
    def render(self,s,t):
        c=self.canvas; w=c.winfo_width(); h=c.winfo_height(); c.delete('dynamic')
        if w<10 or h<10:
            return
        if self._last_grid!=(w,h,self.view):
            c.delete('grid'); self._last_grid=(w,h,self.view)
            if self.view!='portal':
                for x in range(0,w,40): c.create_line(x,0,x,h,fill='#0e1b2b',tags='grid')
                for y in range(0,h,40): c.create_line(0,y,w,y,fill='#0e1b2b',tags='grid')
        t=time.monotonic()
        if self.view=='portal': self.draw_portal(w,h,s,t)
        elif self.view=='field': self.draw_field(w,h,s,t)
        elif self.view=='matrix': self.draw_matrix(w,h,s)
        else: self.draw_apps(w,h,s,t)
    def close(self):
        self.stop_workers(); self.engine.close(); self.bus.close(); self.local_bus.close(); self.destroy()

if __name__=='__main__':
    App().mainloop()

