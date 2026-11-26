"""Migrated Python controls and vector graphics owned by the shared app."""
import base64,html,importlib,io,json,math,sys,time,types,threading
from pathlib import Path
from .runtime import ROOT,clean
from . import component_ui as ui

LOCK=threading.RLock()
def text(w):
 variable=w.options.get('textvariable')
 return str(variable.get() if isinstance(variable,ui.Variable) else w.cget('text') or '')
def walk(w,lookup):
 lookup[w.uid]=w
 row={'id':w.uid,'enabled':w.options.get('state')!='disabled','type':'group'}
 if isinstance(w,ui.Canvas):
  graphic={'id':w.uid,'type':'graphic','enabled':True,'width':w.winfo_width(),'height':w.winfo_height(),'class':w.__class__.__name__}
  embedded=[child for child in w.children if child.alive and not isinstance(child,ui.Scrollbar)]
  if embedded:
   row.update(type='group',id=w.uid+'-content',children=([graphic] if any(shape['kind']!='window' for shape in w.shapes.values()) else [])+[walk(child,lookup) for child in embedded])
  else:row.update(graphic)
 elif isinstance(w,ui.Treeview):row.update(type='table',columns=[w.headings.get(c,c) for c in w.options.get('columns',[])],rows=[list(map(str,r.get('values',[]))) for r in w.rows.values()],row_ids=list(w.rows),selected=next(iter(w.selected),''))
 elif isinstance(w,ui.Listbox):row.update(type='list',items=list(map(str,w.items)),selected=next(iter(w.selected),-1))
 elif isinstance(w,ui.Notebook):row.update(type='tabs',tabs=[{'title':t,'body':walk(c,lookup)} for c,t in w.tabs_data],selected=w.selected_tab)
 elif isinstance(w,ui.Combobox):
  items=list(w.options.get('values',[]));row.update(type='select',items=items,selected=items.index(w.get()) if w.get() in items else -1,editable=w.options.get('state')!='readonly',value=w.get())
 elif isinstance(w,(ui.Checkbutton,ui.Radiobutton)):row.update(type='toggle',text=text(w),selected=bool(w.options.get('variable').get()) if isinstance(w.options.get('variable'),ui.Variable) else False)
 elif isinstance(w,ui.Button):row.update(type='button',text=text(w))
 elif isinstance(w,ui.Label):row.update(type='label',text=text(w))
 elif isinstance(w,ui.Scale):row.update(type='range',value=w.get() or w.options.get('from_',0),min=w.options.get('from_',0),max=w.options.get('to',1),step=w.options.get('resolution',.01))
 elif isinstance(w,ui.Spinbox):row.update(type='number',value=w.get(),min=w.options.get('from_',0),max=w.options.get('to',100),step=w.options.get('increment',1))
 elif isinstance(w,ui.Entry):row.update(type='input',value=w.get(),password=bool(w.options.get('show')))
 elif isinstance(w,ui.Text):row.update(type='textarea' if w.options.get('state')!='disabled' else 'output',value=str(w.get())[-120000:])
 elif isinstance(w,ui.Progressbar):row.update(type='progress',value=w.options.get('value',0),max=w.options.get('maximum',100))
 else:row.update(title=text(w),children=[walk(c,lookup) for c in w.children if c.alive and not c.options.get('hidden') and not isinstance(c,(ui.Scrollbar,ui.Separator))])
 return row

def svg(canvas):
 width=canvas.winfo_width();height=canvas.winfo_height();parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',f'<rect width="100%" height="100%" fill="{html.escape(str(canvas.options.get("bg",canvas.options.get("background","#080e17"))))}"/>']
 def attr(v):return html.escape(str(v),quote=True)
 for s in list(canvas.shapes.values())[:22000]:
  if s.get('state')=='hidden':continue
  try:
   kind=s['kind'];p=[float(v) for v in s['coords']];fill=attr(s.get('fill','none') or 'none');stroke=attr(s.get('outline',s.get('fill','#8ebad1')) or 'none');line=float(s.get('width',1));style=f'fill="{fill}" stroke="{stroke}" stroke-width="{line}"'
   if kind in ('line','polygon'):
    points=' '.join(f'{p[i]},{p[i+1]}' for i in range(0,len(p)-1,2));parts.append(f'<{"polyline" if kind=="line" else "polygon"} points="{points}" {style if kind=="polygon" else f"fill=\"none\" stroke=\"{fill}\" stroke-width=\"{line}\""}/>')
   elif kind=='rectangle':parts.append(f'<rect x="{min(p[0],p[2])}" y="{min(p[1],p[3])}" width="{abs(p[2]-p[0])}" height="{abs(p[3]-p[1])}" {style}/>')
   elif kind=='oval':parts.append(f'<ellipse cx="{(p[0]+p[2])/2}" cy="{(p[1]+p[3])/2}" rx="{abs(p[2]-p[0])/2}" ry="{abs(p[3]-p[1])/2}" {style}/>')
   elif kind=='text':
    font=s.get('font',('Segoe UI',11));size=abs(float(font[1])) if isinstance(font,(list,tuple)) and len(font)>1 else 11;anchor=s.get('anchor','center');align='start' if 'w' in anchor else 'end' if 'e' in anchor else 'middle'
    lines=str(s.get('text','')).splitlines() or [''];content=''.join(f'<tspan x="{p[0]}" dy="{0 if i==0 else size*1.25}">{html.escape(t)}</tspan>' for i,t in enumerate(lines))
    parts.append(f'<text x="{p[0]}" y="{p[1]}" fill="{fill}" font-family="Segoe UI, sans-serif" font-size="{size}" text-anchor="{align}" dominant-baseline="middle">{content}</text>')
   elif kind=='image':
    image=s.get('image');image=getattr(image,'image',image)
    if hasattr(image,'save'):
     buffer=io.BytesIO();image.save(buffer,format='PNG');encoded=base64.b64encode(buffer.getvalue()).decode();x,y=p[:2]
     if s.get('anchor','center')=='center':x-=image.width/2;y-=image.height/2
     parts.append(f'<image x="{x}" y="{y}" width="{image.width}" height="{image.height}" href="data:image/png;base64,{encoded}"/>')
   elif kind=='arc':
    cx=(p[0]+p[2])/2;cy=(p[1]+p[3])/2;rx=abs(p[2]-p[0])/2;ry=abs(p[3]-p[1])/2;start=math.radians(float(s.get('start',0)));extent=math.radians(float(s.get('extent',90)));end=start+extent
    path=f'M {cx+rx*math.cos(start)} {cy-ry*math.sin(start)} A {rx} {ry} 0 {int(abs(extent)>math.pi)} {int(extent<0)} {cx+rx*math.cos(end)} {cy-ry*math.sin(end)}'
    parts.append(f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="{line}"/>')
  except (ValueError,TypeError,IndexError):continue
 parts.append('</svg>');return ''.join(parts).encode()

class PythonSections:
 def __init__(self,runtime):self.runtime=runtime;self.index=json.loads((ROOT/'python-sections.json').read_text(encoding='utf8'));self.loaded={};self.controls={};self.errors={}
 def module(self,row):
  name=row['package']+'.'+str(Path(row['entry']).with_suffix('')).replace('\\','.').replace('/','.')
  return importlib.import_module(name)
 def open(self,ident):
  from . import section_threads
  section_threads.scope.ident=ident
  with LOCK:
   if ident not in self.loaded:
    from . import section_threads
    section_threads.scope.ident=ident
    row=self.index[ident];module=self.module(row);ui._messages.clear()
    from .native_actions import install
    install(module,ident,self.runtime)
    from .section_storage import section_data
    if ident=='atelier':module.DATA=section_data(self.runtime,ident,Path(module.__file__).parent/'data')
    if ident=='core':
     root=ui.Tk();controller=module.build_app(root,self.runtime.data/'sections'/'core')
     from .native_cycles import core
     core(controller)
    elif ident=='godmind':
     data=section_data(self.runtime,ident,Path(module.__file__).parent/'data');controller=module.GodmindDesktop(session=module.DesktopSession(data));root=controller
    elif ident=='creator':root=ui.Tk();controller=module.SoftwareCreatorObservatory(root)
    elif ident=='unified-neural':root=ui.Tk();controller=module.NeuralEngineApp(root);controller.shared_training=True
    elif ident=='hydrogen':
     from .hydrogen_components import integrate
     integrate(module,self.runtime);root=ui.Tk();controller=module.App(root,module.Runtime(data_dir=ROOT/'data'/'sections'/'hydrogen',port=0))
    elif ident=='dualrail':root=ui.Tk();controller=module.PostscarcityObservatoryV4(root)
    elif ident=='atelier':
     from .atelier_components import integrate
     integrate(module,self.runtime);controller=module.App();root=controller
    elif ident in ('backbone','backbone-worker'):
     from .knowledge_components import KnowledgeBridge,TextWorkerPanel
     if not hasattr(self,'knowledge'):self.knowledge=KnowledgeBridge(row['package'],self.runtime)
     if ident=='backbone':
      bridge=self.knowledge
      def worker_tick(desktop):return bridge.tick(desktop)
      module.Desktop.worker=worker_tick;controller=module.Desktop();root=controller
     else:controller=TextWorkerPanel(self.knowledge);root=controller
    elif ident=='scanner':
     from .knowledge_components import ScannerPanel
     controller=ScannerPanel(module,self.runtime);root=controller
    elif ident=='monad':controller=module.GraphicalPurifierApp(module.MonadEngine());root=controller
    elif ident=='scenario-hub':
     from .scenario_components import create
     controller=create(module,self.runtime);root=controller
    elif 'controller' in row:controller=getattr(module,row['controller'])();root=controller
    elif ident=='neural-lab':
     controller=module.RecursiveDrillEngine(checkpoint_path=ROOT/'data'/'sections'/'neural-lab'/'checkpoint.json');root=None
    elif ident=='carrier':controller=module.Lab(11434);root=None
    elif ident=='ambient':controller=module.AmbientFieldEngine();root=None
    elif ident=='injector':controller=module.MetaphysicalChargeInjectorAPI();root=None
    else:controller=module;root=None
    self.loaded[ident]={'module':module,'controller':controller,'root':root}
    if isinstance(root,ui.Widget):
     def configure(widget):
      if isinstance(widget.events,dict) and '<Configure>' in widget.events:
       try:widget.events['<Configure>'](types.SimpleNamespace(widget=widget,width=widget.winfo_width(),height=widget.winfo_height(),x=0,y=0))
       except Exception as e:self.errors[ident]=str(e)
      for child in widget.children:configure(child)
     configure(root)
   self.tick(ident);return self.describe(ident)
 def tick(self,ident):
  if ident in self.runtime.component_host.paused:return
  item=self.loaded.get(ident)
  if not item:return
  root=item['root'];controller=item['controller']
  if root is None:return
  if isinstance(root,ui.Widget):
   now=time.monotonic();due=[(k,v) for k,v in list(root.scheduled.items()) if v[0]<=now][:24]
   for key,(_,fn,args) in due:
    root.scheduled.pop(key,None)
    try:fn(*args)
    except Exception as e:self.errors[ident]=type(e).__name__+': '+str(e)
 def describe(self,ident):
  item=self.loaded[ident];root=item['root'];lookup={};row={'id':ident,'title':self.index[ident]['name'],'implementation':'Integrated Python section controls','windows':0,'messages':ui._messages[-10:],'failure':self.errors.get(ident)}
  row['ui']=walk(root,lookup) if isinstance(root,ui.Widget) else {'type':'engine','class':type(item['controller']).__name__}
  self.controls[ident]=lookup
  controller=item['controller'];methods=[]
  for name in dir(type(controller)):
   if name.startswith('_') or name in ('main','mainloop','start_worker','start_workers'):continue
   value=getattr(type(controller),name,None)
   if callable(value) and name not in dir(ui.Widget):
    import inspect
    try:methods.append({'name':name,'signature':str(inspect.signature(value))})
    except Exception:pass
  row['methods']=methods
  def fields(value,depth=0):
   if depth>3:return None
   if isinstance(value,float) and not math.isfinite(value):return None
   if value is None or isinstance(value,(str,int,float,bool)):return clean(value)
   if hasattr(type(value),'tolist'):return clean(value)
   if isinstance(value,dict):return {str(k):fields(v,depth+1) for k,v in list(value.items())[:128] if not any(word in str(k).lower() for word in ('secret','password','token','private_key'))}
   if isinstance(value,(tuple,list)):return [fields(v,depth+1) for v in value[:128]]
   if isinstance(value,ui.Variable):return fields(value.get(),depth+1)
   if isinstance(value,ui.Widget):return None
   if type(value).__module__.startswith('neural_app.components') and hasattr(value,'__dict__'):return fields(vars(value),depth+1)
   return None
  state={k:fields(v) for k,v in vars(controller).items() if not k.startswith('_') and k not in ('master','children','options','events','scheduled','root','module','runtime','bridge') and not any(word in k.lower() for word in ('secret','password','token','private_key'))}
  row['engine_fields']={k:v for k,v in state.items() if v is not None}
  if hasattr(controller,'snapshot') and callable(getattr(type(controller),'snapshot',None)):
   try:row['engine_fields']=clean(controller.snapshot())
   except Exception:pass
  return row
 def action(self,b):
  ident=b['section'];self.open(ident)
  with LOCK:
   ui._messages.clear();ui._clipboard=None;ui._path=b.get('path');ui._confirm=bool(b.get('confirm'));ui._input=b.get('input');item=self.loaded[ident]
   if b.get('method'):
    name=b['method'];allowed={m['name'] for m in self.describe(ident)['methods']}
    if name not in allowed:raise ValueError('Unknown section method')
    output=getattr(item['controller'],name)(*b.get('args',[]),**b.get('kwargs',{}))
   else:
    w=self.controls[ident][b['control']];action=b.get('action','click');value=b.get('value');output=None
    if action=='click':
     command=w.options.get('command');name=getattr(command,'__name__','').lower();label=str(w.options.get('text','')).lower()
     if 'observatory' in label and any(word in label for word in ('open','launch')):
      return {**self.describe(ident),'navigate':'observatory'}
     output=w.invoke()
    elif action=='set':
     if isinstance(w,ui.Combobox):w.current(int(value));w.event_generate('<<ComboboxSelected>>')
     elif isinstance(w,ui.Treeview):w.selection_set(value);w.event_generate('<<TreeviewSelect>>')
     elif isinstance(w,ui.Listbox):w.selection_set(value);w.event_generate('<<ListboxSelect>>')
     elif isinstance(w,ui.Notebook):w.select(int(value))
     elif isinstance(w,(ui.Scale,ui.Spinbox)):w.set(float(value));w.invoke()
     else:w.delete(0,'end');w.set(value)
    elif action=='set_text' and isinstance(w,ui.Combobox):w.set(value);w.event_generate('<<ComboboxSelected>>')
    elif action=='double':
     if isinstance(w,(ui.Treeview,ui.Listbox)):w.selection_set(value)
     w.event_generate('<Double-1>')
    elif action=='key':
     key=json.loads(value) if isinstance(value,str) else value
     name={'ArrowLeft':'Left','ArrowRight':'Right','ArrowUp':'Up','ArrowDown':'Down',' ':'space','Enter':'Return'}.get(key['key'],key['key'])
     modifiers=('Control-' if key.get('ctrl') else '')+('Alt-' if key.get('alt') else '')+('Shift-' if key.get('shift') else '')
     w.event_generate('<'+modifiers+name+'>',keysym=name,char=key['key'] if len(key['key'])==1 else '',state=(4 if key.get('ctrl') else 0)|(1 if key.get('shift') else 0)|(8 if key.get('alt') else 0))
    elif action=='enter':w.event_generate('<Return>')
    elif action=='pointer':x,y=map(float,str(value).split(','));w.event_generate('<Button-1>',x=x,y=y)
    elif action=='drag':
     x,y,ex,ey=map(float,str(value).split(','));w.event_generate('<Button-1>',x=x,y=y);w.event_generate('<B1-Motion>',x=ex,y=ey);w.event_generate('<ButtonRelease-1>',x=ex,y=ey)
    elif action=='wheel':x,y,delta=map(float,str(value).split(','));w.event_generate('<MouseWheel>',x=x,y=y,delta=-delta*120)
    else:raise ValueError('Unknown control action')
   self.tick(ident);result=self.describe(ident)
   if getattr(self,'navigation',None):result['navigate']=self.navigation;self.navigation=None
   if ui._clipboard is not None:result['clipboard']=ui._clipboard
   if output is not None:result['output']=clean(output)
   receipt_input={k:v for k,v in b.items() if k!='path'}
   if not b.get('method') and isinstance(w,ui.Entry) and w.options.get('show'):receipt_input.pop('value',None);receipt_input['password']='[redacted]'
   result['receipt']=self.runtime.component_result(ident,receipt_input,result)
   return result
 def graphic(self,ident,control,width=850,height=360):
  with LOCK:
   self.open(ident);w=self.controls[ident][control]
   if not isinstance(w,ui.Canvas):raise ValueError('Not a drawing')
   return svg(w)
