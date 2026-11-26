"""Workshop study and a cooperative, bounded learning rotation."""
import json,time
from pathlib import Path
from .matter_spirit import process as reflect
ROOT=Path(__file__).resolve().parents[1]
def catalogue():return json.loads((ROOT/'references/focus-study.json').read_text(encoding='utf-8'))
class FocusStudy:
    def __init__(self,runtime):
        self.runtime=runtime;self.path=runtime.data/'focus-study-settings.json';self.enabled=json.loads(self.path.read_text(encoding='utf-8')).get('enabled',True) if self.path.exists() else True
        self.pending=None;self.next_at=0;self.cycles=0;self.last=None;self.error=None
    def process(self,body):return reflect({'lesson':'overview',**body},catalogue())
    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
        self.enabled=enabled;self.path.write_text(json.dumps({'enabled':enabled}),encoding='utf-8');return self.view()
    def tick(self):
        if self.pending:
            job=self.runtime.result(self.pending)
            if job['status'] in ('queued','running'):return
            self.last=job.get('receipt');self.error=job.get('error');self.pending=None
        if not self.enabled or time.monotonic()<self.next_at or not self.runtime.settings['learning'] or self.runtime.queue.qsize()>3:return
        chapter=catalogue()['chapters'][self.cycles%len(catalogue()['chapters'])];text=chapter['paragraphs'][-1].encode('utf-8')[:360].decode('utf-8',errors='ignore')
        job=self.runtime.submit('pipeline',{'text':text,'sections':['focus_study','super_mesh','gnostic_four','inference'],'section_inputs':{'focus_study':{'lesson':chapter['id']},'gnostic_four':{'lesson':'truevirtue'}}});self.pending=job['id'];self.cycles+=1;self.next_at=time.monotonic()+60
    def view(self):return {'enabled':self.enabled,'interval_seconds':60,'cycles':self.cycles,'pending':self.pending,'last_receipt':self.last,'error':self.error,'scope':'Workshop study notes and authored technology comparisons through the shared local learner.'}
