"""Open the owner's existing Opera profile; never read its private profile files."""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

class OperaWorkspace:
    def __init__(self,data):
        self.path=Path(data)/'opera-workspace.json'
        self.config={'enabled':False,'open_activity':True}
        if self.path.exists():self.config.update(json.loads(self.path.read_text(encoding='utf-8')))
        self.status={'state':'not_started','last_opened':None,'error':None}

    def executable(self):
        candidates=[Path(os.environ.get('LOCALAPPDATA',''))/'Programs/Opera/opera.exe',
                    Path(os.environ.get('PROGRAMFILES',''))/'Opera/launcher.exe',
                    Path(os.environ.get('PROGRAMFILES',''))/'Opera/opera.exe']
        return next((str(p) for p in candidates if p.is_file()),None) or shutil.which('opera')

    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.config['enabled']=enabled
        self.path.write_text(json.dumps(self.config,indent=2),encoding='utf-8')
        return self.view()

    def open(self,url):
        from urllib.parse import urlsplit
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname!='127.0.0.1':raise ValueError('Use the local app address')
        exe=self.executable()
        if not exe:
            self.status.update(state='unavailable',error='Opera was not found in its usual installation locations.')
            return self.view()
        targets=[url.rstrip('/')+'/#googleworkspace']
        if self.config.get('open_activity'):targets.append('https://myactivity.google.com/myactivity?product=83')
        try:
            subprocess.Popen([exe,*targets],close_fds=True)
            self.status.update(state='opened',last_opened=time.time(),error=None)
        except OSError as error:self.status.update(state='error',error=str(error))
        return self.view()

    def on_start(self,url):
        return self.open(url) if self.config['enabled'] else self.view()

    def view(self):
        return {**self.config,**self.status,'capture':'A separately installed and paired browser connector is required for automatic capture. Opening Opera alone does not ingest account data.'}
