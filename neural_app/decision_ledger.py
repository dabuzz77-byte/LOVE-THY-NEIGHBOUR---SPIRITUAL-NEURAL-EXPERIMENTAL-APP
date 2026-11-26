"""Bounded, content-minimised persistent outcome ledger."""
import copy,json,threading,time,os
class DecisionLedger:
 def __init__(self,data):
  self.path=data/'decision-ledger.json';self.lock=threading.RLock();self.rows=[];self.next_at=0;self.dirty=False;self.error=None
  try:self.rows=json.loads(self.path.read_text(encoding='utf-8'))[-256:]
  except (OSError,ValueError):pass
 def record(self,row):
  assessment=row.get('decision_assessment',{})
  record={'id':str(time.time_ns()),'time':row.get('time',time.time()),'action':row.get('action'),'stage':row.get('stage'),'purpose':'Check a registered software action against its explicit contract','affected_scope':'Internal software value; downstream consequences need separate review','permission':assessment.get('automatic_scope'),'alternatives':['Preserve original','Perform the checked transformation','Delay and review missing evidence'],'prediction_matches':row.get('prediction_matches'),'verified':row.get('operation_verified'),'outcome':'failed' if row.get('prediction_matches') is False or row.get('operation_verified') is False else 'verified' if row.get('operation_verified') is True else 'pending','repair':'Preserve input and rerun a corrected contract; this record grants no external action authority','four_way_review':assessment.get('production_bit_rule'),'privacy':'Raw inputs, generated content, secrets and user file paths are not stored here'}
  with self.lock:self.rows=(self.rows+[record])[-256:];self.dirty=True
 def tick(self,c=None):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+5;self.flush()
 def flush(self):
  with self.lock:
   if not self.dirty:return
   try:
    tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.rows,ensure_ascii=False),encoding='utf-8');os.replace(tmp,self.path);self.dirty=False;self.error=None
   except OSError as e:self.error=type(e).__name__
 def view(self):
  with self.lock:return {'records':copy.deepcopy(self.rows[-64:]),'retained':len(self.rows),'pending_save':self.dirty,'storage_error':self.error,'orientation':'✝ Lord’s Prayer: provision, forgiveness, protection and repair.','scope':'Actual registered action outcomes; software verification does not establish all human consequences.'}
