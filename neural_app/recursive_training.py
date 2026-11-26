"""Isolated practice of the actual recursive decision/filter/check core."""
import random,threading,types
from .recursive_core import RecursiveCore
from .flow_backbone import FlowBackbone
class PracticeBus:
 def __init__(self):self.sequence=0;self.events=[];self.listener=None
 def publish(self,event):
  self.sequence+=1;event={**event,'sequence':self.sequence};self.events.append(event)
  if self.listener:self.listener(event)
  return {'event':event}
def trial(seed,step):
 rng=random.Random(int.from_bytes(seed,'big')+step);bus=PracticeBus();backbone=FlowBackbone(bus,start=False);reasoner=types.SimpleNamespace(lock=threading.RLock(),s={},runtime=types.SimpleNamespace());core=RecursiveCore(bus,backbone,reasoner,start=False);bus.listener=core.observe;core.configure({'depth_limit':1,'goal':'calculate {{bit}} + 1'});rows=[]
 for i in range(8):
  value=''.join(str(rng.randrange(2)) for _ in range(16));index=rng.randrange(16);label=('good','evil','unknown')[i%3];want=int(value[index])^(label=='evil');core.seed({'value':value,'entry':'hydrogen','mode':'bit','bit_index':index,'label':label});result=core.step();event=next(e for e in reversed(bus.events) if e['origin']=='recursive-core');receipt=backbone.process(event);core.apply_acks();valid=result['output_bit']==want and core.goal_result['result']==want+1 and result.get('delivery_verified') is True and core.modulation['positive']==-core.modulation['negative'];rows.append({'value':value,'index':index,'label':label,'expected_bit':want,'actual_bit':result['output_bit'],'goal_result':core.goal_result['result'],'delivery_verified':result.get('delivery_verified'),'passed':valid})
 core.close()
 return {'training_passed':all(row['passed'] for row in rows[:4]),'validation_passed':all(row['passed'] for row in rows[4:]),'lesson':'recursive goal → native action → filter check → mailbox verification','training_cases':rows[:4],'fresh_validation_cases':rows[4:],'retained':False,'execution':'actual recursive and backbone implementations in an isolated in-memory bus','scope':'Fresh bit cases and checked native calculations; no remote devices, network calls, file changes or unreviewed shell actions'}
