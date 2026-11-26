"""Postscarcity Hub — a native desktop neural scenario engine and local app bus."""
from __future__ import annotations
import ast
from collections import deque
import ctypes
import json
import math
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from hub_runtime import Runtime, DEFAULT_SCENARIO
from neural_engine import BASE, KEYS, mean_step
from bus_protocol import HZ

BG="#0b121b"; PANEL="#111e2b"; EDGE="#263a4c"; INK="#e4eef5"; MUTED="#8ba4b8"
TEAL="#72e3c1"; BLUE="#78acff"; GOLD="#e6bb6b"; RED="#f08490"
METRIC_NAMES={"access":"Access to resources","comfort":"Comfort availability","transition":"Transition index","automation":"Automation"}


def label(parent,text="",size=10,color=INK,bold=False,**kwargs):
    return tk.Label(parent,text=text,bg=parent.cget("bg"),fg=color,
                    font=("Segoe UI",size,"bold" if bold else "normal"),**kwargs)


def button(parent,text,command,primary=False):
    return tk.Button(parent,text=text,command=command,bg=TEAL if primary else "#1c3042",
                     fg=BG if primary else INK,activebackground="#9cf1d7",activeforeground=BG,
                     relief="flat",bd=0,padx=16,pady=8,cursor="hand2",font=("Segoe UI",10,"bold"))


class App(tk.Tk):
    def __init__(self, runtime=None, autostart=True):
        super().__init__()
        self.title("Postscarcity Hub · local inference & process bus")
        self.geometry("1440x960")
        self.minsize(1120,790)
        self.configure(bg=BG)
        self.runtime=runtime or Runtime()
        self.snapshot={"phase":"stopped","processes":{"processes":[],"note":""},"status":{},"pulse":None}
        self.logs=deque(maxlen=120)
        self.jitter=deque(maxlen=120)
        self.cpu_history=deque(maxlen=120)
        self.last_sequence=0
        self.last_sample=None
        self.last_render=0
        self.last_hub_pulse=0
        self.selected_pid=None
        self.node_hits=[]
        self.inference=None
        self.future=None
        self.closing=False
        self.active_page="Hub"
        self.model_activations=[]
        self.sim_running=False
        self.last_infer=0
        self._style()
        self._layout()
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.after(65,self.pump)
        self.after(33,self.animate)
        if autostart:self.runtime.start()

    def _style(self):
        style=ttk.Style(self);style.theme_use("clam")
        style.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=INK,
                        rowheight=32,borderwidth=0,font=("Segoe UI",10))
        style.configure("Treeview.Heading",background="#1a2a39",foreground=MUTED,
                        font=("Segoe UI",9,"bold"),relief="flat",padding=8)
        style.map("Treeview",background=[("selected","#234b58")],foreground=[("selected",INK)])
        style.configure("TScrollbar",background=EDGE,troughcolor=PANEL,borderwidth=0)

    def _layout(self):
        self.sidebar=tk.Frame(self,bg="#0d1823",width=190)
        self.sidebar.pack(side="left",fill="y");self.sidebar.pack_propagate(False)
        brand=tk.Frame(self.sidebar,bg="#0d1823");brand.pack(fill="x",padx=20,pady=(24,28))
        label(brand,"◈",30,TEAL).pack(anchor="w")
        label(brand,"POSTSCARCITY",13,bold=True).pack(anchor="w",pady=(9,3))
        label(brand,"LOCAL INFERENCE HUB",8,MUTED).pack(anchor="w")
        self.nav={}
        for name,sub in [("Hub","Pulse & topology"),("Programs","Observed & connected"),("Scenario lab","Neural forecasts"),("Source notes","Your original inputs")]:
            frame=tk.Frame(self.sidebar,bg="#0d1823");frame.pack(fill="x",padx=12,pady=3)
            b=tk.Button(frame,text=name,anchor="w",command=lambda n=name:self.show_page(n),bg="#0d1823",fg=INK,
                        activebackground="#1b3042",activeforeground=TEAL,relief="flat",padx=14,pady=9,font=("Segoe UI",11,"bold"))
            b.pack(fill="x");self.nav[name]=b
            label(frame,sub,8,MUTED).pack(anchor="w",padx=14,pady=(0,8))
        bottom=tk.Frame(self.sidebar,bg="#0d1823");bottom.pack(side="bottom",fill="x",padx=20,pady=22)
        label(bottom,"COMMUNICATION RATE",8,MUTED).pack(anchor="w")
        label(bottom,f"{HZ:.2f} Hz",25,TEAL,True).pack(anchor="w",pady=4)
        label(bottom,f"{1000/HZ:.3f} ms target period",9,MUTED).pack(anchor="w")
        label(bottom,"Windows · local port",9,MUTED).pack(anchor="w",pady=(20,0))
        self.content=tk.Frame(self,bg=BG);self.content.pack(side="left",fill="both",expand=True,padx=26,pady=22)
        top=tk.Frame(self.content,bg=BG);top.pack(fill="x")
        titles=tk.Frame(top,bg=BG);titles.pack(side="left")
        self.page_title=label(titles,"Your local inference network",24,bold=True);self.page_title.pack(anchor="w")
        self.page_sub=label(titles,"Measured pulses. Visible programs. A shared communication layer.",10,MUTED)
        self.page_sub.pack(anchor="w",pady=(5,0))
        actions=tk.Frame(top,bg=BG);actions.pack(side="right")
        self.toggle=button(actions,"Stop hub",self.toggle_hub);self.toggle.pack(side="right",padx=(8,0))
        button(actions,"Export",self.export).pack(side="right")
        self.status_line=label(self.content,"Starting local hub…",10,TEAL)
        self.status_line.pack(anchor="w",pady=(18,16))
        stats=tk.Frame(self.content,bg=BG);stats.pack(fill="x")
        self.stat={}
        for i,(key,title,detail,color) in enumerate([
            ("processes","OBSERVED PROGRAMS","Python + Java processes",BLUE),
            ("peers","CONNECTED ADAPTERS","Live message participants",TEAL),
            ("rate","MEASURED PULSE",f"Target {HZ:.3f} Hz",TEAL),
            ("inferences","INFERENCE REQUESTS","Local scenario model",GOLD)]):
            stats.columnconfigure(i,weight=1,uniform="stats")
            card=tk.Frame(stats,bg=PANEL,highlightbackground=EDGE,highlightthickness=1)
            card.grid(row=0,column=i,sticky="nsew",padx=(0,10 if i<3 else 0))
            label(card,title,8,MUTED).pack(anchor="w",padx=16,pady=(13,3))
            value=label(card,"—",25,color,True);value.pack(anchor="w",padx=16)
            label(card,detail,8,MUTED).pack(anchor="w",padx=16,pady=(2,13))
            self.stat[key]=value
        self.page_container=tk.Frame(self.content,bg=BG);self.page_container.pack(fill="both",expand=True,pady=(18,0))
        self.pages={n:tk.Frame(self.page_container,bg=BG) for n in self.nav}
        self._hub_page(self.pages["Hub"])
        self._program_page(self.pages["Programs"])
        self._scenario_page(self.pages["Scenario lab"])
        self._source_page(self.pages["Source notes"])
        self.show_page("Hub")

    def _panel(self,parent,title,subtitle=""):
        frame=tk.Frame(parent,bg=PANEL,highlightbackground=EDGE,highlightthickness=1)
        head=tk.Frame(frame,bg=PANEL);head.pack(fill="x",padx=18,pady=(15,10))
        label(head,title,11,bold=True).pack(anchor="w")
        if subtitle:label(head,subtitle,9,MUTED).pack(anchor="w",pady=(4,0))
        return frame

    def _hub_page(self,page):
        top=tk.Frame(page,bg=BG);top.pack(fill="both",expand=True)
        top.columnconfigure(0,weight=3);top.columnconfigure(1,weight=2);top.rowconfigure(0,weight=1)
        net=self._panel(top,"Live topology","Dotted links carry observed telemetry. Solid links are connected adapters.")
        net.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        self.network=tk.Canvas(net,bg=PANEL,highlightthickness=0,height=320)
        self.network.pack(fill="both",expand=True,padx=6)
        self.network.bind("<Button-1>",self.pick_node)
        self.graph_note=label(net,"Discovering programs…",8,MUTED,anchor="w")
        self.graph_note.pack(fill="x",padx=18,pady=(0,12))
        right=tk.Frame(top,bg=BG);right.grid(row=0,column=1,sticky="nsew")
        pulse=self._panel(right,"Pulse timing","Send lateness relative to the scheduled heartbeat")
        pulse.pack(fill="both",expand=True,pady=(0,12))
        self.pulse_chart=tk.Canvas(pulse,bg=PANEL,highlightthickness=0,height=96)
        self.pulse_chart.pack(fill="both",expand=True,padx=16)
        self.timing_note=label(pulse,"Waiting for heartbeat",9,MUTED)
        self.timing_note.pack(anchor="w",padx=18,pady=(4,14))
        resource=self._panel(right,"Program activity","CPU samples from visible Python and Java processes")
        resource.pack(fill="both",expand=True)
        self.resource_chart=tk.Canvas(resource,bg=PANEL,highlightthickness=0,height=96)
        self.resource_chart.pack(fill="both",expand=True,padx=16)
        self.resource_note=label(resource,"Waiting for process samples",9,MUTED)
        self.resource_note.pack(anchor="w",padx=18,pady=(4,14))
        bottom=self._panel(page,"Event stream","Real connection, discovery and inference events")
        bottom.pack(fill="x",pady=(12,0))
        self.event_text=tk.Text(bottom,height=6,bg=PANEL,fg=MUTED,relief="flat",font=("Consolas",9),wrap="word",padx=18)
        self.event_text.pack(fill="x",pady=(0,12));self.event_text.configure(state="disabled")

    def _program_page(self,page):
        frame=self._panel(page,"Running programs","All discovered programs are mirrored as observed nodes; adapters provide two-way messages.")
        frame.pack(fill="both",expand=True)
        self.process_note=label(frame,"",9,MUTED,anchor="w",wraplength=900)
        self.process_note.pack(fill="x",padx=18,pady=(0,12))
        body=tk.Frame(frame,bg=PANEL);body.pack(fill="both",expand=True,padx=12,pady=(0,10))
        columns=("app","runtime","pid","cpu","memory","bus")
        self.table=ttk.Treeview(body,columns=columns,show="headings",selectmode="browse")
        for key,title,width in zip(columns,["APPLICATION","RUNTIME","PID","CPU %","MEMORY MB","BUS ROLE"],[300,85,70,70,110,170]):
            self.table.heading(key,text=title);self.table.column(key,width=width,minwidth=55,anchor="w")
        scroll=ttk.Scrollbar(body,orient="vertical",command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y");self.table.pack(fill="both",expand=True)
        self.table.bind("<<TreeviewSelect>>",self.select_process)
        self.process_detail=tk.Text(frame,height=4,bg=PANEL,fg=INK,font=("Segoe UI",10),wrap="word",relief="flat",padx=18)
        self.process_detail.pack(fill="x",pady=(0,14));self.process_detail.configure(state="disabled")

    def _scenario_page(self,page):
        page.columnconfigure(0,weight=1);page.columnconfigure(1,weight=2);page.rowconfigure(0,weight=1)
        controls=self._panel(page,"Scenario controls","Inputs from your original simulation")
        controls.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        self.vars={k:tk.DoubleVar(value=DEFAULT_SCENARIO[k]) for k in KEYS}
        self.control_vars={k:tk.BooleanVar(value=DEFAULT_SCENARIO[k]) for k in ("valve","gate")}
        for key in KEYS:
            row=tk.Frame(controls,bg=PANEL);row.pack(fill="x",padx=18,pady=(12,0))
            label(row,METRIC_NAMES[key],10).pack(anchor="w")
            scale=tk.Scale(row,from_=0,to=100,orient="horizontal",variable=self.vars[key],resolution=.1,
                           bg=PANEL,fg=MUTED,troughcolor="#203749",activebackground=TEAL,highlightthickness=0,
                           bd=0,sliderrelief="flat",font=("Consolas",9),length=200)
            scale.pack(fill="x")
        for key,text in [("valve","Resource-flow valve"),("gate","Automation gate")]:
            tk.Checkbutton(controls,text=text,variable=self.control_vars[key],bg=PANEL,fg=INK,selectcolor="#203749",
                           activebackground=PANEL,activeforeground=TEAL,font=("Segoe UI",10)).pack(anchor="w",padx=14,pady=(10,0))
        buttons=tk.Frame(controls,bg=PANEL);buttons.pack(fill="x",padx=18,pady=20)
        self.predict_button=button(buttons,"Predict 60 ticks",self.predict,True);self.predict_button.pack(fill="x")
        self.sim_button=button(buttons,"Run scenario",self.toggle_scenario);self.sim_button.pack(fill="x",pady=(8,0))
        label(controls,"Model trained on generated simulation cases.\nThese values do not measure world resources.",9,MUTED,justify="left",wraplength=280).pack(anchor="w",padx=18,pady=(0,15))
        right=tk.Frame(page,bg=BG);right.grid(row=0,column=1,sticky="nsew")
        network=self._panel(right,"Neural activity","6 inputs → 32 → 24 → 4 outputs · grouped neurons shown")
        network.pack(fill="both",expand=True,pady=(0,12))
        self.neural_canvas=tk.Canvas(network,bg=PANEL,highlightthickness=0,height=215)
        self.neural_canvas.pack(fill="both",expand=True,padx=12)
        self.model_note=label(network,"Trained scenario predictor",9,MUTED);self.model_note.pack(anchor="w",padx=18,pady=12)
        output=self._panel(right,"60-tick forecast","Neural estimate alongside the simulation's mean-step reference")
        output.pack(fill="both",expand=True)
        self.forecast_canvas=tk.Canvas(output,bg=PANEL,highlightthickness=0,height=215)
        self.forecast_canvas.pack(fill="both",expand=True,padx=16)
        self.forecast_note=label(output,"Choose inputs and run a prediction.",9,MUTED)
        self.forecast_note.pack(anchor="w",padx=18,pady=12)

    def _source_page(self,page):
        frame=self._panel(page,"Source notes & provenance","The supplied files are preserved as references; text in this panel is not executed.")
        frame.pack(fill="both",expand=True)
        notes=tk.Text(frame,bg=PANEL,fg=INK,relief="flat",font=("Segoe UI",11),wrap="word",padx=22,pady=10)
        notes.pack(fill="both",expand=True,pady=(0,18))
        original=BASE/"source_reference"/"post_scarcity_simulation.py"
        content="HOW THE ENGINE USES YOUR FILES\n\nThe neural model learns a deterministic version of the original simulation, using the midpoint of each random increment. Its forecasts describe that software scenario.\n\n"
        content+="The bus listens on this computer. The observer reads process metadata and broadcasts it to subscribers. It does not import, inject into, or change the other programs.\n\nORIGINAL BLUEPRINT NOTES\n\n"
        try:
            tree=ast.parse(original.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=="historical_manifestos" for t in node.targets):
                    for item in ast.literal_eval(node.value):content+="• "+item+"\n\n"
            content+="SUPPLIED TEXT NOTE\n\n"+(BASE/"source_reference"/"principles.txt").read_text(encoding="utf-8-sig")
        except (OSError,ValueError,SyntaxError) as exc:content+=f"Could not read references: {exc}"
        notes.insert("1.0",content);notes.configure(state="disabled")

    def show_page(self,name):
        for page in self.pages.values():page.pack_forget()
        # The scenario page uses grid internally; its outer placement is still pack.
        self.pages[name].pack(fill="both",expand=True)
        self.active_page=name
        for key,b in self.nav.items():b.configure(bg="#1b3042" if key==name else "#0d1823",fg=TEAL if key==name else INK)
        titles={"Hub":("Your local inference network","Measured pulses. Visible programs. A shared communication layer."),
                "Programs":("Programs on the bus","Observed processes and authenticated message participants."),
                "Scenario lab":("Explore the simulation","A trained neural model predicts the next 60 scenario ticks."),
                "Source notes":("Built from your inputs","Original concepts, preserved with a clear software execution boundary.")}
        self.page_title.configure(text=titles[name][0]);self.page_sub.configure(text=titles[name][1])

    def toggle_hub(self):
        phase=self.snapshot.get("phase")
        if phase in ("starting","listening"):
            self.runtime.shutdown();self.sim_running=False;self.sim_button.configure(text="Run scenario")
        elif not(self.runtime.thread and self.runtime.thread.is_alive()):self.runtime.start()

    def toggle_scenario(self):
        if self.snapshot.get("phase")!="listening":return
        self.sim_running=not self.sim_running
        self.sim_button.configure(text="Pause scenario" if self.sim_running else "Run scenario")
        if self.sim_running:self.predict()

    def scenario(self):
        return {**{k:v.get() for k,v in self.vars.items()},**{k:v.get() for k,v in self.control_vars.items()}}

    def predict(self):
        if self.future and not self.future.done():return
        try:
            self.future=self.runtime.infer(self.scenario());self.predict_button.configure(state="disabled")
            self.last_infer=time.monotonic()
        except (ValueError,RuntimeError) as exc:self.forecast_note.configure(text=str(exc))

    def pump(self):
        if self.closing:return
        self.snapshot,events=self.runtime.take()
        state=self.snapshot;phase=state["phase"];status=state.get("status",{})
        color=TEAL if phase=="listening" else RED if phase=="error" else MUTED
        phrase=f"●  LISTENING  ·  {state['address']}  ·  local TCP bus" if phase=="listening" else phase.upper()
        if state.get("error"):phrase+=" · "+state["error"]
        self.status_line.configure(text=phrase,fg=color)
        self.toggle.configure(text="Stop hub" if phase in ("starting","listening") else "Stopping…" if phase=="stopping" else "Start hub")
        processes=state.get("processes",{}).get("processes",[])
        peers=status.get("services",[])
        self.stat["processes"].configure(text=str(len(processes)) if phase=="listening" else "—")
        self.stat["peers"].configure(text=str(len(peers)) if phase=="listening" else "—")
        hz=status.get("measured_hz")
        self.stat["rate"].configure(text=f"{hz:.3f} Hz" if hz else "—")
        self.stat["inferences"].configure(text=str(status.get("inference_count",0)))
        p=state.get("pulse")
        if p and p["sequence"]!=self.last_sequence:
            delta=p["sequence"]-self.last_sequence if self.last_sequence else 1
            if delta<0:delta=1;self.jitter.clear()
            self.last_sequence=p["sequence"];self.last_hub_pulse=time.monotonic()
            self.jitter.append(p["lateness_ms"])
            if self.sim_running:
                s=self.scenario();new=mean_step([[s[k] for k in KEYS]],[[s["valve"],s["gate"]]],min(delta,60))[0]
                for key,value in zip(KEYS,new):self.vars[key].set(round(float(value),3))
                if time.monotonic()-self.last_infer>1:self.predict()
        late=status.get("lateness_p95_ms")
        self.timing_note.configure(text=f"{status.get('pulse_count',0)} pulses  ·  {status.get('skipped_ticks',0)} missed  ·  p95 {late:.1f} ms" if late is not None else "Waiting for timing samples")
        sample=state.get("processes",{})
        if sample.get("sample_monotonic")!=self.last_sample:
            self.last_sample=sample.get("sample_monotonic")
            cpus=[r["cpu_percent"] for r in processes if r.get("cpu_percent") is not None]
            memory=sum(r.get("memory_mb") or 0 for r in processes)
            if cpus:self.cpu_history.append(sum(cpus))
            self.resource_note.configure(text=f"{sum(cpus):.2f}% of system CPU  ·  {memory:.0f} MB working set" if cpus else f"{memory:.0f} MB working set  ·  CPU warming up")
        self.process_note.configure(text=sample.get("note",""))
        self.refresh_table(processes,peers)
        for event in events:
            data=event["data"];topic=event["topic"]
            if topic=="process.sample":continue
            detail=data.get("message") or data.get("label") or data.get("id") or data.get("service") or ""
            self.logs.append(f"{time.strftime('%H:%M:%S',time.localtime(event['time']))}   {topic:<20}  {detail}")
        if events:
            self.event_text.configure(state="normal");self.event_text.delete("1.0","end")
            self.event_text.insert("1.0","\n".join(list(self.logs)[-6:]));self.event_text.configure(state="disabled")
        if self.future and self.future.done():
            try:
                self.inference=self.future.result();self.model_activations=self.inference["activations"]
                self.forecast_note.configure(text=f"Completed in {self.inference['latency_ms']:.2f} ms · neural estimate, not a world measurement")
            except Exception as exc:self.forecast_note.configure(text=f"Inference failed: {exc}")
            self.future=None;self.predict_button.configure(state="normal")
        model=state.get("model")
        if model:self.model_note.configure(text=f"Held-out error {model['held_out_mae_points']:.2f} points · 1,000 synthetic cases · 6 → 32 → 24 → 4")
        self.after(80,self.pump)

    def refresh_table(self,processes,peers):
        connected={p.get("reported_pid") for p in peers}
        existing=set(self.table.get_children());wanted=set()
        for p in processes:
            id_=p["id"];wanted.add(id_)
            values=(p["label"],p["language"],p["pid"],f"{p['cpu_percent']:.2f}" if p.get("cpu_percent") is not None else "—",
                    f"{p['memory_mb']:.1f}" if p.get("memory_mb") is not None else "—",
                    "Adapter + observation" if p["pid"] in connected else "Observed telemetry")
            if id_ in existing:self.table.item(id_,values=values)
            else:self.table.insert("","end",iid=id_,values=values)
        known={p["pid"] for p in processes}
        for peer in peers:
            if peer.get("reported_pid") in known:continue
            id_="peer:"+peer["id"];wanted.add(id_)
            values=(peer["id"],"Adapter",peer.get("reported_pid") or "—","—","—","Connected adapter")
            if id_ in existing:self.table.item(id_,values=values)
            else:self.table.insert("","end",iid=id_,values=values)
        for id_ in existing-wanted:self.table.delete(id_)

    def select_process(self,event=None):
        selection=self.table.selection()
        if not selection:return
        row=next((p for p in self.snapshot.get("processes",{}).get("processes",[]) if p["id"]==selection[0]),None)
        if row:
            self.selected_pid=row["pid"]
            text=f"{row['label']} · PID {row['pid']} · {row['language']}\n{row.get('path') or 'Executable path unavailable'}\nObserved metadata is published to subscribers. A matching adapter adds two-way messages; its PID is self-reported."
        else:text="Connected participant. Process identity is reported by the adapter."
        self.process_detail.configure(state="normal");self.process_detail.delete("1.0","end")
        self.process_detail.insert("1.0",text);self.process_detail.configure(state="disabled")

    def pick_node(self,event):
        for x,y,pid in self.node_hits:
            if (x-event.x)**2+(y-event.y)**2<25**2 and pid:
                self.selected_pid=pid;self.show_page("Programs")
                for row in self.snapshot.get("processes",{}).get("processes",[]):
                    if row["pid"]==pid and self.table.exists(row["id"]):
                        self.table.selection_set(row["id"]);self.table.see(row["id"]);self.select_process();break
                break

    def animate(self):
        if self.closing:return
        if self.active_page=="Hub":
            self.draw_network();self.draw_chart(self.pulse_chart,self.jitter,TEAL,"LATENESS · ms",minimum=5)
            self.draw_chart(self.resource_chart,self.cpu_history,BLUE,"SYSTEM CPU · %",minimum=1)
        elif self.active_page=="Scenario lab":self.draw_neural();self.draw_forecast()
        self.after(33,self.animate)

    def draw_network(self):
        c=self.network;c.delete("all");w=max(c.winfo_width(),300);h=max(c.winfo_height(),250)
        cx,cy=w/2,h/2-6;r=min(w*.34,h*.35)
        phase=self.snapshot.get("phase");active=phase=="listening"
        for scale in (.72,1.0,1.24):c.create_oval(cx-r*scale,cy-r*scale,cx+r*scale,cy+r*scale,outline="#1b3142",dash=(2,7))
        for i in range(24):
            a=i*math.tau/24
            c.create_line(cx+(r+5)*math.cos(a),cy+(r+5)*math.sin(a),cx+(r+10)*math.cos(a),cy+(r+10)*math.sin(a),fill="#2c465a")
        rows=self.snapshot.get("processes",{}).get("processes",[])
        peers=self.snapshot.get("status",{}).get("services",[])
        nodes=[{"id":p["id"],"label":p["id"],"pid":p.get("reported_pid"),"connected":True,"color":TEAL} for p in peers]
        pids={p.get("reported_pid") for p in peers}
        nodes += [{"id":p["id"],"label":p["label"],"pid":p["pid"],"connected":False,"color":BLUE if p["language"]=="Python" else GOLD} for p in rows if p["pid"] not in pids]
        nodes=nodes[:20];self.node_hits=[]
        age=time.monotonic()-self.last_hub_pulse
        for i,node in enumerate(nodes):
            angle=-math.pi/2+i*math.tau/max(1,len(nodes));x=cx+r*math.cos(angle);y=cy+r*math.sin(angle)
            c.create_line(cx,cy,x,y,fill="#315869" if node["connected"] else "#2a4152",width=2 if node["connected"] else 1,dash=() if node["connected"] else (3,6))
            if node["connected"] and active and age<1/HZ:
                t=min(1,age*HZ);px=cx+(x-cx)*t;py=cy+(y-cy)*t
                c.create_oval(px-3,py-3,px+3,py+3,fill=TEAL,outline="")
            color=node["color"]
            c.create_oval(x-12,y-12,x+12,y+12,fill="#182c3d",outline=color,width=2)
            c.create_oval(x-3,y-3,x+3,y+3,fill=color,outline="")
            caption=node["label"][:17]+("…" if len(node["label"])>17 else "")
            label_y=y+24 if math.sin(angle)>=0 else y-24
            c.create_text(x,label_y,text=caption,fill=MUTED,font=("Segoe UI",8))
            self.node_hits.append((x,y,node["pid"]))
        breath=(math.sin(time.monotonic()*math.tau*1.2)+1)*2 if active else 0
        if active and age<.4:
            ring=43+age*85
            c.create_oval(cx-ring,cy-ring,cx+ring,cy+ring,outline="#2a665d",width=1)
        c.create_oval(cx-43-breath,cy-43-breath,cx+43+breath,cy+43+breath,fill="#102d31",outline="#346e67",width=2)
        c.create_text(cx,cy-7,text=f"{HZ:.2f}",fill=TEAL if active else MUTED,font=("Segoe UI",23,"bold"))
        c.create_text(cx,cy+19,text="Hz · LOCAL BUS",fill=MUTED,font=("Segoe UI",8))
        if not nodes:c.create_text(cx,h-22,text="Waiting for visible programs or adapters",fill=MUTED,font=("Segoe UI",10))
        self.graph_note.configure(text=f"{len(rows)} observed processes · {len(peers)} adapters · showing {len(nodes)} nodes · click a process to inspect")

    @staticmethod
    def draw_chart(c,values,color,caption,minimum=1):
        c.delete("all");w=max(200,c.winfo_width());h=max(70,c.winfo_height());bottom=h-20;top=24
        data=list(values);peak=max(minimum,max(data,default=0)*1.2)
        for j in range(3):
            y=top+j*(bottom-top)/2;c.create_line(0,y,w,y,fill="#243849",dash=(2,5))
        c.create_text(0,5,text=caption,fill=MUTED,anchor="nw",font=("Consolas",8))
        c.create_text(w,5,text=f"{peak:.1f}",fill=MUTED,anchor="ne",font=("Consolas",8))
        if len(data)>1:
            points=[coord for i,v in enumerate(data) for coord in (i*(w-4)/max(119,len(data)-1)+2,bottom-v/peak*(bottom-top))]
            c.create_line(*points,fill=color,width=2)
        else:c.create_text(w/2,h/2,text="Collecting samples",fill=MUTED,font=("Segoe UI",9))

    def draw_neural(self):
        c=self.neural_canvas;c.delete("all");w=max(c.winfo_width(),350);h=max(c.winfo_height(),190)
        counts=[6,12,10,4];positions=[]
        for layer,count in enumerate(counts):
            positions.append([(45+layer*(w-90)/3,22+(i+.5)*(h-44)/count) for i in range(count)])
        for left,right in zip(positions,positions[1:]):
            for i,(x,y) in enumerate(left):
                for j,(xx,yy) in enumerate(right):
                    if (i+j)%3==0:c.create_line(x,y,xx,yy,fill="#263c4d")
        input_values=[v.get()/100 for v in self.vars.values()]+[float(v.get()) for v in self.control_vars.values()]
        output_values=[self.inference["predicted"][k]/100 for k in KEYS] if self.inference else [0]*4
        layers=[input_values,self.model_activations[0] if self.model_activations else [0]*32,
                self.model_activations[1] if self.model_activations else [0]*24,output_values]
        for li,coords in enumerate(positions):
            for i,(x,y) in enumerate(coords):
                v=abs(layers[li][int(i*len(layers[li])/len(coords))]);bright=min(1,v)
                color=f"#{int(45+69*bright):02x}{int(80+147*bright):02x}{int(91+102*bright):02x}"
                c.create_oval(x-6,y-6,x+6,y+6,fill=color,outline="#538575")

    def draw_forecast(self):
        c=self.forecast_canvas;c.delete("all");w=max(350,c.winfo_width());h=max(180,c.winfo_height())
        if not self.inference:
            c.create_text(w/2,h/2,text="Run a prediction to inspect the four outputs.",fill=MUTED,font=("Segoe UI",10));return
        for i,key in enumerate(KEYS):
            y=20+i*(h-25)/4;value=self.inference["predicted"][key];ref=self.inference["rule_reference"][key]
            c.create_text(0,y,text=METRIC_NAMES[key],anchor="w",fill=INK,font=("Segoe UI",9))
            c.create_text(w,y,text=f"{value:.1f}  /  rule {ref:.1f}",anchor="e",fill=MUTED,font=("Consolas",9))
            c.create_rectangle(0,y+12,w,y+20,fill="#23394b",outline="")
            c.create_rectangle(0,y+12,w*value/100,y+20,fill=TEAL,outline="")
            c.create_line(w*ref/100,y+8,w*ref/100,y+24,fill=GOLD,width=2)

    def export(self):
        path=filedialog.asksaveasfilename(parent=self,title="Export hub snapshot",defaultextension=".json",initialfile="postscarcity-snapshot.json")
        if not path:return
        try:Path(path).write_text(json.dumps({"snapshot":self.snapshot,"forecast":self.inference,"events":list(self.logs)},indent=2),encoding="utf-8")
        except OSError as exc:messagebox.showerror("Export failed",str(exc),parent=self)

    def close(self):
        if self.closing:return
        self.closing=True;self.runtime.shutdown();self.destroy()
        self.runtime.wait_stopped()


def main():
    try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (OSError,AttributeError):pass
    App().mainloop()


if __name__=="__main__":main()
