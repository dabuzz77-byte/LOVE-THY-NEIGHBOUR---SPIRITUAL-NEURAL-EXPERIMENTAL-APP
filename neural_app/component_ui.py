"""Native section control model used by migrated Python UI definitions.

Widget state, callbacks and vector drawing live in the shared process. The browser
renders the controls in Neural App's own DOM; no Tk interpreter/window is created.
"""
import base64,io,itertools,math,time,types,collections
from PIL import Image as PILImage

_ids=itertools.count();_current=None;_path=None;_messages=[];_confirm=False;_input=None;_clipboard=None
unsupported_calls=collections.Counter()
class Variable:
 def __init__(self,master=None,value=None,**kw):self.value=value;self.traces=[]
 def get(self):return self.value
 def set(self,v):self.value=v;[fn(None,None,None) for fn in self.traces]
 def trace_add(self,mode,fn):self.traces.append(fn);return str(len(self.traces))
 def trace(self,mode,fn):return self.trace_add(mode,fn)
class StringVar(Variable):
 def get(self):return '' if self.value is None else str(self.value)
class IntVar(Variable):
 def get(self):return int(self.value or 0)
class DoubleVar(Variable):
 def get(self):return float(self.value or 0)
class BooleanVar(Variable):
 def get(self):return bool(self.value)
class Widget:
 def __init__(self,master=None,*args,**kw):
  self.master=master if isinstance(master,Widget) else None;self.children=[];self.options=dict(kw);self.uid='p'+str(next(_ids));self.events={};self.value='';self.items=[];self.alive=True;self.scheduled={};self.selected=[]
  if self.master:self.master.children.append(self)
  self.width=kw.get('width',640);self.height=kw.get('height',320)
 def configure(self,cnf=None,**kw):self.options.update(cnf or {});self.options.update(kw);self.width=kw.get('width',self.width);self.height=kw.get('height',self.height)
 config=configure
 def cget(self,k):
  if k=='text' and isinstance(self.options.get('textvariable'),Variable):return self.options['textvariable'].get()
  return self.options.get(k,'')
 def __getitem__(self,k):return self.cget(k)
 def __setitem__(self,k,v):self.configure(**{k:v})
 def pack(self,*a,**k):self.options.update(k)
 grid=pack;place=pack;pack_configure=pack;grid_configure=pack;place_configure=pack
 def pack_forget(self):self.options['hidden']=True
 grid_remove=pack_forget;grid_forget=pack_forget;place_forget=pack_forget
 def rowconfigure(self,*a,**k):pass
 columnconfigure=rowconfigure;grid_rowconfigure=rowconfigure;grid_columnconfigure=rowconfigure;pack_propagate=rowconfigure;grid_propagate=rowconfigure
 def bind(self,event,fn,add=None):self.events[event]=fn;return event
 bind_all=bind
 def unbind(self,event,*a):self.events.pop(event,None)
 def event_generate(self,event,**kw):
  if event in self.events:return self.events[event](types.SimpleNamespace(widget=self,x=kw.get('x',0),y=kw.get('y',0),delta=kw.get('delta',0),keysym=kw.get('keysym',''),state=kw.get('state',0),char=kw.get('char',''),keycode=kw.get('keycode',0),x_root=kw.get('x_root',kw.get('x',0)),y_root=kw.get('y_root',kw.get('y',0)),width=self.winfo_width(),height=self.winfo_height()))
 def invoke(self):
  command=self.options.get('command')
  if callable(command):return command()
 def get(self,*a):
  var=self.options.get('textvariable') or self.options.get('variable')
  return var.get() if isinstance(var,Variable) else self.value
 def set(self,v):
  var=self.options.get('textvariable') or self.options.get('variable')
  if isinstance(var,Variable):var.set(v)
  else:self.value=v
 def insert(self,index,value,*args):self.value=str(value)+str(self.value) if str(index) in ('0','1.0') else str(self.value)+str(value)
 def delete(self,*a):self.value=''
 def after(self,delay,fn=None,*args):
  root=self.winfo_toplevel();ident=self.uid+':'+str(next(_ids))
  if fn:root.scheduled[ident]=(time.monotonic()+max(0,delay)/1000,fn,args)
  return ident
 def after_cancel(self,ident):self.winfo_toplevel().scheduled.pop(ident,None)
 def after_idle(self,fn,*args):return self.after(0,fn,*args)
 def winfo_toplevel(self):return self.master.winfo_toplevel() if self.master else self
 def winfo_children(self):return self.children[:]
 def winfo_width(self):return max(80,int(float(self.width)))
 def winfo_height(self):return max(40,int(float(self.height)))
 winfo_reqwidth=winfo_width;winfo_reqheight=winfo_height
 def winfo_class(self):return type(self).__name__
 def winfo_exists(self):return self.alive
 def winfo_ismapped(self):return not self.options.get('hidden',False)
 def winfo_screenwidth(self):return 1500
 def winfo_screenheight(self):return 980
 def winfo_rootx(self):return 0
 def winfo_rooty(self):return 0
 def winfo_id(self):return 0
 def destroy(self):
  self.alive=False
  if self.master and self in self.master.children:self.master.children.remove(self)
 def clipboard_clear(self):
  global _clipboard
  _clipboard=''
 def clipboard_append(self,value):
  global _clipboard
  _clipboard=(_clipboard or '')+str(value)
 def clipboard_get(self):return _clipboard or ''
 def update(self,*a,**kw):pass
 update_idletasks=update;focus_set=update;focus_force=update;see=update;lift=update;lower=update;bell=update
 def yview(self,*a):return (0,1)
 xview=yview;yview_moveto=yview;xview_moveto=yview;yview_scroll=yview;xview_scroll=yview
 def selection_range(self,*a):pass
 select_range=selection_range;tag_configure=selection_range;tag_config=selection_range;tag_add=selection_range;tag_remove=selection_range;mark_set=selection_range
 def index(self,*a):return '1.0'
 def state(self,values=None):
  if values:self.options['state']='disabled' if 'disabled' in values else 'normal'
  return ('disabled',) if self.options.get('state')=='disabled' else ()
 def register(self,fn):return fn
 def keys(self):return list(self.options)
 def option_add(self,*a):pass
 def __getattr__(self,name):
  if name in ('tk','_w'):return self
  raise AttributeError(name)
class Tk(Widget):
 def title(self,text=None):
  if text is not None:self.options['title']=text
  return self.options.get('title','')
 def geometry(self,text):
  try:self.width,self.height=map(int,text.split('+')[0].split('x'))
  except Exception:pass
 def mainloop(self):pass
 def protocol(self,*a):pass
 def iconphoto(self,*images):self.options['icon']=images
 def minsize(self,*a):pass
 def maxsize(self,*a):pass
 def withdraw(self):pass
 def deiconify(self):pass
Toplevel=Tk
class Frame(Widget):pass
class LabelFrame(Frame):pass
Labelframe=LabelFrame
class Label(Widget):pass
class Button(Widget):pass
class Entry(Widget):pass
class Text(Widget):pass
class ScrolledText(Text):pass
class Scrollbar(Widget):pass
class Separator(Widget):pass
class Progressbar(Widget):pass
class Checkbutton(Button):
 def invoke(self):
  var=self.options.get('variable')
  if isinstance(var,Variable):var.set(not var.get())
  return super().invoke()
class Radiobutton(Button):
 def invoke(self):
  var=self.options.get('variable')
  if isinstance(var,Variable):var.set(self.options.get('value'))
  return super().invoke()
class Scale(Widget):pass
class Spinbox(Entry):pass
class Combobox(Widget):
 def current(self,index=None):
  items=self.options.get('values',[])
  if index is None:return items.index(self.get()) if self.get() in items else -1
  if items:self.set(items[index])
class Listbox(Widget):
 def insert(self,index,*values):self.items.extend(values)
 def delete(self,first,last=None):
  if str(last)=='end' and str(first)=='0':self.items=[]
  elif self.items:self.items.pop(int(first))
 def get(self,first,last=None):return self.items[int(first)] if last is None else tuple(self.items[int(first):])
 def curselection(self):return tuple(self.selected)
 def selection_set(self,first,last=None):self.selected=[int(first)]
 select_set=selection_set
 def selection_clear(self,*a):self.selected=[]
 def size(self):return len(self.items)
class Treeview(Widget):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.rows={};self.headings={};self._focus=''
 def heading(self,name,**kw):self.headings[name]=kw.get('text',name)
 def column(self,*a,**k):pass
 def insert(self,parent,index,iid=None,**kw):
  ident=str(iid or 'row'+str(next(_ids)));self.rows[ident]=dict(kw,parent=parent);return ident
 def get_children(self,item=None):return tuple(k for k,v in self.rows.items() if not item or v.get('parent')==item)
 def delete(self,*ids):
  for ident in ids:
   if isinstance(ident,(list,tuple)):self.delete(*ident)
   else:self.rows.pop(str(ident),None)
 def item(self,ident,option=None,**kw):
  row=self.rows.get(str(ident),{});row.update(kw);return row.get(option) if option else row
 def set(self,item,column=None,value=None):
  row=self.rows[str(item)];columns=list(self.options.get('columns',[]));values=list(row.get('values',[]))
  if value is None:return dict(zip(columns,values)) if column is None else values[columns.index(column)]
  values[columns.index(column)]=value;row['values']=values
 def selection(self):return tuple(self.selected)
 def selection_set(self,items):self.selected=list(items) if isinstance(items,(list,tuple)) else [items];self._focus=self.selected[0] if self.selected else ''
 def focus(self,item=None):
  if item is not None:self._focus=item
  return self._focus
 def exists(self,item):return item in self.rows
class Notebook(Frame):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.tabs_data=[];self.selected_tab=0
 def add(self,child,**kw):self.tabs_data.append((child,kw.get('text','Section')))
 def select(self,tab=None):
  if tab is None:return self.tabs_data[self.selected_tab][0] if self.tabs_data else None
  self.selected_tab=tab if isinstance(tab,int) else next((i for i,(w,t) in enumerate(self.tabs_data) if w is tab),0);self.event_generate('<<NotebookTabChanged>>')
 def tab(self,index,option=None,**kw):return self.tabs_data[index][1] if option=='text' else {}
 def tabs(self):return [p for p,t in self.tabs_data]
 def index(self,tab):
  if tab=='current':return self.selected_tab
  if isinstance(tab,Widget):return next((i for i,(w,t) in enumerate(self.tabs_data) if w is tab),0)
  return int(tab)
class PanedWindow(Frame):
 def add(self,child,**kw):pass
Panedwindow=PanedWindow
class Menu(Frame):
 def add_command(self,**kw):return Button(self,text=kw.get('label',''),command=kw.get('command'))
 def add_separator(self):pass
 def add_cascade(self,**kw):pass
 def add_checkbutton(self,**kw):return Checkbutton(self,**kw)
 def add_radiobutton(self,**kw):return Radiobutton(self,**kw)
 def entryconfig(self,*a,**kw):pass
class Canvas(Widget):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.shapes={}
 def _create(self,kind,args,kw):
  ident=next(_ids);coords=[]
  def flatten(v):
   if isinstance(v,(list,tuple)):
    for a in v:flatten(a)
   else:coords.append(v)
  flatten(args);self.shapes[ident]={'kind':kind,'coords':coords,**kw};return ident
 def create_line(self,*a,**kw):return self._create('line',a,kw)
 def create_oval(self,*a,**kw):return self._create('oval',a,kw)
 def create_rectangle(self,*a,**kw):return self._create('rectangle',a,kw)
 def create_text(self,*a,**kw):return self._create('text',a,kw)
 def create_polygon(self,*a,**kw):return self._create('polygon',a,kw)
 def create_arc(self,*a,**kw):return self._create('arc',a,kw)
 def create_image(self,*a,**kw):return self._create('image',a,kw)
 def create_window(self,*a,**kw):return self._create('window',a,kw)
 def find_withtag(self,tag):
  def matches(ident,shape):
   tags=shape.get('tags',())
   if isinstance(tags,str):tags=tags.split()
   return tag in (ident,'all') or str(tag)==str(ident) or tag in tags
  return tuple(i for i,shape in self.shapes.items() if matches(i,shape))
 def delete(self,*tags):
  for tag in tags:
   for ident in self.find_withtag(tag):self.shapes.pop(ident,None)
 def itemconfigure(self,tag,**kw):
  for ident in self.find_withtag(tag):self.shapes[ident].update(kw)
 itemconfig=itemconfigure
 def coords(self,tag,*coords):
  ids=self.find_withtag(tag)
  if not ids:return []
  if coords:
   values=coords[0] if len(coords)==1 and isinstance(coords[0],(list,tuple)) else coords
   self.shapes[ids[0]]['coords']=list(values)
  return self.shapes[ids[0]]['coords']
 def move(self,tag,dx,dy):
  for ident in self.find_withtag(tag):
   shape=self.shapes[ident];shape['coords']=[v+(dx if i%2==0 else dy) for i,v in enumerate(shape['coords'])]
 def _order(self,tag,relative,above):
  selected=set(self.find_withtag(tag));moving=[(i,s) for i,s in self.shapes.items() if i in selected];remaining=[(i,s) for i,s in self.shapes.items() if i not in selected]
  targets=set(self.find_withtag(relative)) if relative is not None else set()
  positions=[i for i,(ident,_) in enumerate(remaining) if ident in targets]
  index=(max(positions)+1 if above else min(positions)) if positions else len(remaining) if above else 0
  self.shapes=dict(remaining[:index]+moving+remaining[index:])
 def tag_lower(self,tag,below=None):self._order(tag,below,False)
 def tag_raise(self,tag,above=None):self._order(tag,above,True)
 lower=tag_lower;lift=tag_raise
 def bbox(self,*tags):
  points=[]
  for tag in tags or ('all',):
   for ident in self.find_withtag(tag):
    shape=self.shapes[ident];coords=shape['coords']
    if shape['kind']=='text' and len(coords)>=2:
     font=shape.get('font',('Segoe UI',11));size=abs(float(font[1])) if isinstance(font,(list,tuple)) and len(font)>1 else 11
     width=max(map(len,str(shape.get('text','')).splitlines() or ['']))*size*.6;height=len(str(shape.get('text','')).splitlines() or [''])*size*1.25
     x,y=coords[:2];anchor=shape.get('anchor','center');x-=0 if 'w' in anchor else width if 'e' in anchor else width/2;y-=0 if 'n' in anchor else height if 's' in anchor else height/2;points.extend([(x,y),(x+width,y+height)])
    else:points.extend(zip(coords[::2],coords[1::2]))
  return (min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)) if points else None
 def find_all(self):return tuple(self.shapes)
 def canvasx(self,x):return x
 def canvasy(self,y):return y
 def tag_bind(self,tag,event,fn):self.bind(event,fn)
 def itemcget(self,item,key):return self.shapes.get(item,{}).get(key,'')
class PhotoImage:
 def __init__(self,image=None,file=None,**kw):self.image=image if image is not None else PILImage.open(file) if file else PILImage.new('RGB',(int(kw.get('width',1)),int(kw.get('height',1))))
 def put(self,color,to=None):
  if to is None:return
  from PIL import ImageDraw
  coordinates=tuple(map(int,to));draw=ImageDraw.Draw(self.image)
  if len(coordinates)==2:draw.point(coordinates,fill=color)
  else:draw.rectangle(coordinates,fill=color)
 def width(self):return self.image.width
 def height(self):return self.image.height
 def subsample(self,n,*a):return PhotoImage(self.image.resize((self.image.width//n,self.image.height//n)))
class Style:
 def __init__(self,*a,**k):pass
 def configure(self,*a,**k):pass
 map=configure;theme_use=configure;layout=configure
 def lookup(self,*a,**k):return ''
 def theme_names(self):return ('clam','default')
class Font:
 def __init__(self,*a,**k):self.size=k.get('size',12)
 def measure(self,text):return len(str(text))*abs(self.size)*.6
 def metrics(self,*a):return abs(self.size)+4
 def configure(self,**kw):self.size=kw.get('size',self.size)
def askopenfilename(**kw):return _path or ''
asksaveasfilename=askopenfilename;askdirectory=askopenfilename
def showinfo(title,message,**kw):_messages.append(str(title)+': '+str(message))
showerror=showinfo;showwarning=showinfo
def askyesno(title,message,**kw):showinfo(title,message);return bool(_confirm)
askokcancel=askyesno
def askstring(title,prompt,**kw):showinfo(title,prompt);return _input if _input is not None else None
def __getattr__(name):
 if name.isupper():return name.lower()
 raise AttributeError(name)
import sys
ttk=sys.modules[__name__];filedialog=ttk;messagebox=ttk;simpledialog=ttk;font=ttk;scrolledtext=ttk
