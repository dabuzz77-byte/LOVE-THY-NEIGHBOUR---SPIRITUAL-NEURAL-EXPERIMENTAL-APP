"""Explicitly selected Windows window/tab accessibility text ingestion."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from sources import now


class ScreenHub:
    def __init__(self, runtime):
        self.rt=runtime;self.lock=threading.RLock();self.windows=[];self.selection=None
        self.automatic=False;self.source_id=None;self.status='Choose a window';self.error=None
        self.picking=False;self.command=None

    def call(self, request):
        with tempfile.TemporaryDirectory(prefix='screen-',dir=self.rt.data) as folder:
            path=Path(folder)/'request.json';path.write_text(json.dumps(request),encoding='utf-8')
            shell=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
            script='screen_picker.ps1' if request.get('mode')=='pick' else 'screen_reader.ps1'
            result=subprocess.run([str(shell),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name(script)),str(path)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=40 if request.get('mode')=='pick' else 25,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode:raise ValueError(result.stderr.split('\nAt ')[0].strip()[:500] or 'The selected app did not expose readable content')
            return json.loads(result.stdout.lstrip('\ufeff'))

    def list_windows(self):
        rows=self.call({'mode':'windows'})
        with self.lock:self.windows=rows
        return rows

    def pick(self):
        with self.lock:
            if self.picking:raise ValueError('A picker is already open. Click a window or press Escape.')
            self.picking=True
        try:
            result=self.call({'mode':'pick'})
            if result.get('cancelled'):return result
            window=result['window']
            with self.lock:self.windows=[w for w in self.windows if w['handle']!=window['handle']]+[window]
            result['tabs']=self.inspect('tabs',window['handle'])
            if result.get('tab') and not any(t['id']==result['tab'] for t in result['tabs']):
                raise ValueError('That tab changed while selecting it. Pick it again or use the tab list.')
            if not result.get('tab'):
                selected=[t for t in result['tabs'] if t.get('selected')]
                if len(selected)==1:result['tab']=selected[0]['id']
            return result
        finally:
            with self.lock:self.picking=False

    def command_input(self,body):
        command=body.get('command','');provider=body.get('provider','llama')
        mode=body.get('mode','analyze')
        if mode not in ('analyze','interpret'):raise ValueError('Choose a neural reply or a Windows command plan')
        if not isinstance(command,str) or not 1<=len(command.strip())<=2000:raise ValueError('Enter a command of 1–2,000 characters')
        if provider not in ('llama','chatgpt','gemini'):raise ValueError('Choose a model')
        if self.rt.model_hub.view()[provider]['busy']:raise ValueError('The selected model is working. Wait for its reply.')
        captured=self.ingest(body.get('handle'),body.get('tab',''),body.get('element',''),body.get('automatic',False),body.get('targets'))
        if mode=='interpret':
            plan=self.rt.interpreter.prepare(command.strip(),provider,[captured['source_id']])
            with self.lock:self.command={'provider':provider,'mode':mode,'plan_id':plan['id'],'text':command.strip(),'source_id':captured['source_id']}
        else:
            result=self.rt.model_hub.submit(provider,command.strip(),[captured['source_id']])
            with self.lock:self.command={'provider':provider,'mode':mode,'request_id':result['request_id'],'text':command.strip(),'source_id':captured['source_id']}
        return self.view()

    def request(self, handle, tab='', element=''):
        with self.lock:window=next((w for w in self.windows if w['handle']==str(handle)),None)
        if not window:raise ValueError('Refresh windows, then choose one from the list')
        if not isinstance(tab,str) or not isinstance(element,str):raise ValueError('Choose a tab or element from its list')
        return {'handle':window['handle'],'pid':window['pid'],'tab':tab,'element':element,
            'browser':window['process'].lower() in ('chrome','msedge','firefox','brave','opera','vivaldi') or (window['process'].lower()=='codex' and bool(tab))}

    def inspect(self, mode, handle, tab=''):
        if mode not in ('tabs','elements'):raise ValueError('Choose tabs or elements')
        request=self.request(handle,tab);request.update(mode=mode,activate=mode=='elements')
        return self.call(request)

    def ingest(self, handle, tab='', element='', automatic=False, targets=None):
        if type(automatic) is not bool:raise ValueError('Automatic capture must be true or false')
        targets=list(self.rt.modules) if targets is None else targets
        if not isinstance(targets,list) or not targets or any(not isinstance(key,str) or key not in self.rt.modules for key in targets):raise ValueError('Choose one or more existing modules')
        request=self.request(handle,tab,element)
        request['targets']=list(dict.fromkeys(targets))
        result=self.call({**request,'mode':'read','activate':True})
        with self.lock:
            self.selection=request;self.automatic=automatic;self.source_id=None
            self.store(result);self.status='Captured selected app text';self.error=None
        return self.view()

    def store(self, result):
        hub=self.rt.source_hub
        if not self.source_id:
            item=hub.add('text','Screen · '+result['title'][:140],text=result['text'])
            self.source_id=item['id']
        with hub.lock:
            item=hub.items[self.source_id]
            item.update(kind='screen',text=result['text'],title='Screen · '+result['title'][:140],retrieved=now(),status='ready',
                screen_origin=self.selection,automatic=False,truncated=result['truncated'],targets=self.selection['targets'])
            hub.save()
        with self.rt.lock:
            source_node='source:'+self.source_id
            self.rt.edges.pop(source_node+'|module:2/ingest_live_web_definitions',None)
            for key in self.selection['targets']:self.rt.edges.setdefault(source_node+'|module:'+key,.1)
        self.rt.binary_bus.feed('screen-text:'+self.source_id,result['text'].encode('utf-8'))
        self.rt.activate('source:'+self.source_id,1)
        self.rt.publish('screen',{'source':self.source_id,'title':item['title'],'characters':len(item['text'])})
        for key in self.selection['targets']:self.rt.schedule(key)

    def view(self):
        with self.lock:
            result={'selection':self.selection,'automatic':self.automatic,'source_id':self.source_id,'status':self.status,'error':self.error,'picking':self.picking}
            command=dict(self.command) if self.command else None
        if command:
            if command['mode']=='interpret':
                with self.rt.interpreter.lock:plan=next((dict(p) for p in self.rt.interpreter.plans if p['id']==command['plan_id']),{})
                command.update(plan=plan,output=plan.get('output') or plan.get('preview',''),busy=plan.get('status')=='running',error=plan.get('error'))
            else:
                with self.rt.model_hub.lock:
                    history=self.rt.model_hub.histories[command['provider']]
                    reply=next((m for m in history if m.get('reply_to')==command['request_id']),{})
                    command.update(output=reply.get('content',''),busy=self.rt.model_hub.busy[command['provider']],error=self.rt.model_hub.errors[command['provider']])
            result['command']=command
        return result

    def stop_capture(self):
        with self.lock:self.automatic=False;self.status='Automatic capture stopped'
        return self.view()

    def loop(self):
        while not self.rt.stop.wait(10):
            with self.lock:selection=dict(self.selection) if self.selection and self.automatic else None
            if not selection:continue
            try:
                result=self.call({**selection,'mode':'read','activate':False})
                with self.lock:
                    if self.automatic and selection==self.selection:self.store(result);self.status='Selected app text refreshed';self.error=None
            except Exception as exc:
                with self.lock:self.error=str(exc);self.status='Capture waiting for the selected app or tab'
