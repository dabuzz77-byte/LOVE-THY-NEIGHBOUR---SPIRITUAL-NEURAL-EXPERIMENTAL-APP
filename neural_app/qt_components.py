"""Original Qt calculation/drawing components, owned by one offscreen UI thread.

Only the individual custom graphics are painted. All controls are rendered by
Neural App's DOM. No original window or application process is opened.
"""
import importlib,io,json,os,queue,threading,time,traceback
from concurrent.futures import Future
from pathlib import Path
from .runtime import ROOT

class QtSections:
 def __init__(self,runtime,entry):
  self.runtime=runtime;self.entry=entry;self.queue=queue.Queue(maxsize=16);self.ready=threading.Event();self.error=None;self.window=None;self.controls={};self.ids={};self.messages=[];self.path=None;self.confirm=False;self.dialog=None;self.dialog_values=None
  self.stop=threading.Event();self.thread=threading.Thread(target=self.loop,name='neural-qt-components',daemon=True);self.thread.start();self.ready.wait(30)
  if self.error:raise ValueError(self.error)
 def loop(self):
  try:
   from . import section_threads
   section_threads.scope.ident='flux'
   os.environ['QT_QPA_PLATFORM']='offscreen'
   from PySide6 import QtCore,QtGui,QtWidgets
   self.C,self.G,self.W=QtCore,QtGui,QtWidgets;self.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
   def save(parent=None,caption='',directory='',filter='',*a,**kw):
    folder=ROOT/'data'/'exports';folder.mkdir(exist_ok=True);name=Path(directory).name or 'export.json';path=Path(self.path) if self.path else folder/(str(time.time_ns())+'-'+name)
    return str(path),filter
   QtWidgets.QFileDialog.getSaveFileName=save
   QtWidgets.QFileDialog.getOpenFileName=lambda *a,**k:(self.path or '', '')
   QtWidgets.QFileDialog.getOpenFileNames=lambda *a,**k:([self.path] if self.path else [],'')
   QtWidgets.QFileDialog.getExistingDirectory=lambda *a,**k:self.path or ''
   def message(parent,title,text,*args,**kw):self.messages.append(str(title)+': '+str(text));return QtWidgets.QMessageBox.StandardButton.Yes if self.confirm else QtWidgets.QMessageBox.StandardButton.Cancel
   for name in ('information','warning','critical','question'):setattr(QtWidgets.QMessageBox,name,message)
   def dialog(widget):
    fields=[];controls=[]
    for child in widget.findChildren(QtWidgets.QWidget):
     if isinstance(child,(QtWidgets.QLabel,QtWidgets.QLineEdit,QtWidgets.QTextEdit,QtWidgets.QPlainTextEdit,QtWidgets.QComboBox,QtWidgets.QSpinBox,QtWidgets.QDoubleSpinBox,QtWidgets.QCheckBox)):
      row=self.walk(child);row['id']=str(len(controls));fields.append(row);controls.append(child)
    if self.dialog_values is None:
     self.dialog={'title':widget.windowTitle(),'fields':fields};return int(QtWidgets.QDialog.DialogCode.Rejected)
    for key,value in self.dialog_values.items():
     child=controls[int(key)]
     if isinstance(child,QtWidgets.QLineEdit):child.setText(str(value))
     elif isinstance(child,(QtWidgets.QTextEdit,QtWidgets.QPlainTextEdit)):child.setPlainText(str(value))
     elif isinstance(child,QtWidgets.QComboBox):child.setCurrentIndex(int(value))
     elif isinstance(child,(QtWidgets.QSpinBox,QtWidgets.QDoubleSpinBox)):child.setValue(float(value) if isinstance(child,QtWidgets.QDoubleSpinBox) else int(value))
     elif isinstance(child,QtWidgets.QCheckBox):child.setChecked(bool(value))
    return int(QtWidgets.QDialog.DialogCode.Accepted)
   QtWidgets.QDialog.exec=dialog
   QtGui.QDesktopServices.openUrl=lambda url:self.messages.append('Connection URL: '+url.toString()) or True
   self.ready.set()
   while not self.stop.is_set():
    try:fn,args,future=self.queue.get(timeout=.25)
    except queue.Empty:self.app.processEvents();continue
    try:future.set_result(fn(*args));self.app.processEvents()
    except BaseException as error:future.set_exception(error)
    finally:self.queue.task_done()
   import shiboken6
   if self.window is not None:
    self.window.close();self.controls.clear();self.ids.clear();shiboken6.delete(self.window);self.window=None
   self.app.processEvents();application=self.app;self.app=None;shiboken6.delete(application)
  except BaseException:self.error=traceback.format_exc();self.ready.set()
 def call(self,fn,*args):
  if threading.current_thread() is self.thread:return fn(*args)
  future=Future();self.queue.put_nowait((fn,args,future));return future.result(60)
 def _open(self):
  if self.window is None:
   module=importlib.import_module(self.entry['package']+'.source.app');monitor=importlib.import_module(self.entry['package']+'.source.monitor')
   from .shared_credentials import install
   self.provider_settings=install(module.__package__,self.runtime)
   from .section_storage import section_data
   self.window=module.GraphicalVirtueMatrixEngine(monitor.SystemBusMonitor(),section_data(self.runtime,'flux'),start_services=False);self.window.resize(1320,900)
   from .flux_components import FluxScheduler
   self.scheduler=FluxScheduler(self.window,self.runtime)
   for provider,controls in self.window.cloud_controls.items():
    selected='chatgpt' if provider=='openai' else provider
    controls['model'].setEditText(self.provider_settings.settings()[selected]['model'])
   self.synced_keys={p:self.window.cloud_controls[p]['key'].text() for p in self.window.cloud_controls}
   self.synced_models={p:self.window.cloud_controls[p]['model'].currentText() for p in self.window.cloud_controls}
   def save_model(provider,model):
    import re
    if not re.fullmatch(r'[\w.:/+-]{1,150}',model):return
    selected='chatgpt' if provider=='openai' else provider;settings=self.provider_settings.settings()[selected]
    if settings['model']!=model:self.provider_settings.save_settings({'provider':selected,'model':model,'endpoint':settings['endpoint']})
   for provider,controls in self.window.cloud_controls.items():controls['model'].currentTextChanged.connect(lambda model,p=provider:save_model(p,model))
   self.window.ensurePolished()
   for widget in self.window.findChildren(self.W.QWidget):
    if widget.layout():widget.layout().activate()
  return self._describe()
 def open(self):return self.call(self._open)
 def _active(self,value):
  if self.window is None:return
  if value:
   for timer,interval in getattr(self,'paused_timers',[]):timer.start(interval)
   self.paused_timers=[]
  elif not getattr(self,'paused_timers',[]):
   self.paused_timers=[(timer,timer.interval()) for timer in self.window.findChildren(self.C.QTimer) if timer.isActive()]
   for timer,interval in self.paused_timers:timer.stop()
 def active(self,value):return self.call(self._active,bool(value))
 def key(self,widget):
  if widget not in self.ids:self.ids[widget]='q'+str(len(self.ids));self.controls[self.ids[widget]]=widget
  return self.ids[widget]
 def walk(self,w,depth=0):
  if depth>28:return None
  W=self.W;row={'id':self.key(w),'enabled':w.isEnabled(),'type':'group'}
  if isinstance(w,W.QAbstractButton):row.update(type='toggle' if w.isCheckable() else 'button',text=w.text(),selected=w.isChecked())
  elif isinstance(w,W.QLabel):row.update(type='label',text=w.text())
  elif isinstance(w,W.QLineEdit):row.update(type='input',value=w.text(),password=w.echoMode()!=W.QLineEdit.EchoMode.Normal)
  elif isinstance(w,(W.QPlainTextEdit,W.QTextEdit)):row.update(type='output' if w.isReadOnly() else 'textarea',value=w.toPlainText())
  elif isinstance(w,W.QComboBox):row.update(type='select',items=[w.itemText(i) for i in range(w.count())],selected=w.currentIndex(),editable=w.isEditable(),value=w.currentText())
  elif isinstance(w,(W.QSpinBox,W.QDoubleSpinBox)):row.update(type='number',value=w.value(),min=w.minimum(),max=w.maximum(),step=w.singleStep())
  elif isinstance(w,W.QSlider):row.update(type='range',value=w.value(),min=w.minimum(),max=w.maximum())
  elif isinstance(w,W.QTableWidget):row.update(type='table',columns=[w.horizontalHeaderItem(i).text() if w.horizontalHeaderItem(i) else str(i) for i in range(w.columnCount())],rows=[[w.item(r,c).text() if w.item(r,c) else '' for c in range(w.columnCount())] for r in range(min(w.rowCount(),500))],selected=w.currentRow())
  elif isinstance(w,W.QListWidget):row.update(type='list',items=[w.item(i).text() for i in range(w.count())],selected=w.currentRow())
  elif isinstance(w,W.QProgressBar):row.update(type='progress',value=w.value(),max=w.maximum())
  elif isinstance(w,W.QStackedWidget):row.update(type='group',children=[self.walk(w.currentWidget(),depth+1)] if w.currentWidget() else [])
  elif isinstance(w,W.QTabWidget):row.update(type='tabs',tabs=[{'title':w.tabText(i),'body':self.walk(w.widget(i),depth+1)} for i in range(w.count())],selected=w.currentIndex())
  elif 'paintEvent' in type(w).__dict__ and not type(w).__module__.startswith('PySide6'):row.update(type='graphic',**{'class':type(w).__name__},width=max(200,w.width()),height=max(160,w.height()))
  elif isinstance(w,W.QMainWindow):row.update(children=[self.walk(w.centralWidget(),depth+1)])
  elif isinstance(w,W.QScrollArea):row.update(children=[self.walk(w.widget(),depth+1)] if w.widget() else [])
  else:row.update(children=[self.walk(c,depth+1) for c in w.findChildren(W.QWidget,options=self.C.Qt.FindChildOption.FindDirectChildrenOnly) if not isinstance(c,(W.QScrollBar,W.QSizeGrip))])
  return row
 def _describe(self):
  from .runtime import clean
  if hasattr(self,'synced_keys'):
   settings=self.provider_settings.settings()
   for provider,controls in self.window.cloud_controls.items():
    selected='chatgpt' if provider=='openai' else provider;key=self.provider_settings.key(selected);model=settings[selected]['model']
    if controls['key'].text()==self.synced_keys[provider]:controls['key'].setText(key)
    if controls['model'].currentText()==self.synced_models[provider]:controls['model'].setEditText(model)
    self.synced_keys[provider]=key;self.synced_models[provider]=model
  if time.monotonic()-getattr(self,'last_sample',0)>1.5:
   self.last_sample=time.monotonic();self.window.bus_monitor.sample_once();self.window.tick()
  self.app.processEvents();graphics=[{'id':self.key(w),'type':'graphic','class':type(w).__name__,'width':max(200,w.width()),'height':max(160,w.height())} for w in self.window.findChildren(self.W.QWidget) if 'paintEvent' in type(w).__dict__ and not type(w).__module__.startswith('PySide6')]
  return {'id':'flux','title':'Flux Bus · full calculation studio','windows':0,'implementation':'Integrated Qt controls and drawing library','ui':self.walk(self.window),'all_graphics':graphics,'engine_fields':{'route':clean(self.window.route),'global_virtue_state':self.window.global_virtue_state},'messages':self.messages[-10:],'dialog':self.dialog}
 def _action(self,b):
  self._open();before_clipboard=self.app.clipboard().text();self.messages.clear();self.path=b.get('path');self.confirm=bool(b.get('confirm'));self.dialog_values=b.get('dialog');self.dialog=None;w=self.controls[b['control']];action=b.get('action','click');value=b.get('value');W=self.W
  if action=='click' and isinstance(w,W.QAbstractButton):w.click()
  elif action=='set':
   if isinstance(w,W.QLineEdit):w.setText(str(value))
   elif isinstance(w,W.QPlainTextEdit):w.setPlainText(str(value))
   elif isinstance(w,W.QTextEdit):w.setPlainText(str(value))
   elif isinstance(w,W.QComboBox):w.setCurrentIndex(int(value))
   elif isinstance(w,(W.QSpinBox,W.QDoubleSpinBox,W.QSlider)):w.setValue(float(value) if isinstance(w,W.QDoubleSpinBox) else int(value))
   elif isinstance(w,(W.QListWidget,)):w.setCurrentRow(int(value))
   elif isinstance(w,W.QTableWidget):w.selectRow(int(value))
   elif isinstance(w,W.QTabWidget):w.setCurrentIndex(int(value))
  elif action=='set_text' and isinstance(w,W.QComboBox) and w.isEditable():w.setEditText(str(value))
  elif action=='double':
   if isinstance(w,W.QTableWidget):w.selectRow(int(value));w.cellDoubleClicked.emit(int(value),0);w.itemDoubleClicked.emit(w.item(int(value),0))
   elif isinstance(w,W.QListWidget):w.setCurrentRow(int(value));w.itemDoubleClicked.emit(w.item(int(value)))
  elif action=='key':
   key=json.loads(value);C=self.C;name={'ArrowLeft':'Left','ArrowRight':'Right','ArrowUp':'Up','ArrowDown':'Down',' ':'Space','Enter':'Return','Escape':'Escape'}.get(key['key'],key['key'].upper())
   code=getattr(C.Qt.Key,'Key_'+name);mod=C.Qt.KeyboardModifier.NoModifier
   if key.get('ctrl'):mod|=C.Qt.KeyboardModifier.ControlModifier
   if key.get('shift'):mod|=C.Qt.KeyboardModifier.ShiftModifier
   if key.get('alt'):mod|=C.Qt.KeyboardModifier.AltModifier
   self.app.sendEvent(w,self.G.QKeyEvent(C.QEvent.Type.KeyPress,code,mod,key['key'] if len(key['key'])==1 else ''))
   self.app.sendEvent(w,self.G.QKeyEvent(C.QEvent.Type.KeyRelease,code,mod,key['key'] if len(key['key'])==1 else ''))
  elif action=='enter' and isinstance(w,W.QLineEdit):w.returnPressed.emit()
  elif action in ('pointer','drag','wheel'):
   values=list(map(float,str(value).split(',')));x,y=values[:2];C=self.C;G=self.G;point=C.QPointF(x,y)
   if action=='wheel':self.app.sendEvent(w,G.QWheelEvent(point,point,C.QPoint(),C.QPoint(0,int(-values[2]*120)),C.Qt.MouseButton.NoButton,C.Qt.KeyboardModifier.NoModifier,C.Qt.ScrollPhase.NoScrollPhase,False))
   else:
    self.app.sendEvent(w,G.QMouseEvent(C.QEvent.Type.MouseButtonPress,point,point,C.Qt.MouseButton.LeftButton,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier))
    if action=='drag':point=C.QPointF(*values[2:4]);self.app.sendEvent(w,G.QMouseEvent(C.QEvent.Type.MouseMove,point,point,C.Qt.MouseButton.NoButton,C.Qt.MouseButton.LeftButton,C.Qt.KeyboardModifier.NoModifier))
    self.app.sendEvent(w,G.QMouseEvent(C.QEvent.Type.MouseButtonRelease,point,point,C.Qt.MouseButton.LeftButton,C.Qt.MouseButton.NoButton,C.Qt.KeyboardModifier.NoModifier))
  self.app.processEvents();result=self._describe()
  if self.app.clipboard().text()!=before_clipboard:result['clipboard']=self.app.clipboard().text()
  result['receipt']=self.runtime.component_result('flux',{'control':b['control'],'action':action},result);return result
 def action(self,b):return self.call(self._action,b)
 def _graphic(self,control,width,height):
  self._open();w=self.controls[control]
  from PySide6.QtSvg import QSvgGenerator
  array=self.C.QByteArray();buffer=self.C.QBuffer(array);buffer.open(self.C.QIODevice.OpenModeFlag.WriteOnly)
  generator=QSvgGenerator();generator.setOutputDevice(buffer);generator.setSize(w.size());generator.setViewBox(w.rect())
  painter=self.G.QPainter(generator)
  try:w.render(painter,self.C.QPoint())
  finally:painter.end();buffer.close()
  return bytes(array)
 def graphic(self,control,width=850,height=360):return self.call(self._graphic,control,int(width),int(height))
 def pulse(self):
  if hasattr(self,'scheduler'):self.scheduler.pulse()
 def close(self):
  if hasattr(self,'scheduler'):self.scheduler.close()
  self.stop.set();self.thread.join(3)
