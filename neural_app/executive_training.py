"""Fresh-input native planning practice, independent expected answers."""
import random,threading,types
from .cognitive_executive import CognitiveExecutive
def trial(seed,step):
 rng=random.Random(int.from_bytes(seed,'big')+step);records=[]
 def save():pass
 r=types.SimpleNamespace(s={},lock=threading.RLock(),user_active=False,controller=types.SimpleNamespace(save=save))
 w=types.SimpleNamespace(r=r,lock=r.lock,record=lambda *args:None)
 engine=CognitiveExecutive(w)
 for offset in (0,100):
  for i in range(4):
   a=rng.randrange(2,50)+offset;b=rng.randrange(2,30);c=rng.randrange(2,8)
   goal=engine.submit(f'calculate {a} + {b} then calculate {{{{previous}}}} * {c}')
   engine.tick(force=True);engine.tick(force=True)
   want=(a+b)*c;passed=goal['status']=='complete' and goal['steps'][-1]['result']==want
   records.append({'input':[a,b,c],'expected':want,'actual':goal['steps'][-1].get('result'),'passed':passed})
 bad=engine.submit('calculate 1/0 then calculate {{previous}} + 1');engine.tick(force=True)
 failure_ok=bad['status']=='needs-input' and bad['steps'][1]['status']=='pending'
 return {'training_passed':all(r['passed'] for r in records[:4]),'validation_passed':all(r['passed'] for r in records[4:]) and failure_ok,'lesson':'goal decomposition → dependency substitution → execute → verify → retain','training_cases':records[:4],'fresh_validation_cases':records[4:],'failure_recovery_checked':failure_ok,'retained':all(r['passed'] for r in records),'scope':'Fresh arithmetic task composition and failure handling; no host or external changes'}
