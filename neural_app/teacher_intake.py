"""Provider-neutral lesson preparation with independent native task fixtures."""
import copy,hashlib,json,os,threading,time
from .native_synthesis import execute,OPS,bounded
TASKS={
 'reverse-text':{'operations':['reverse'],'cases':[('abc','cba'),('a😀β','β😀a'),('',''),('aa bb','bb aa')]},
 'trim-lower-text':{'operations':['strip','lower'],'cases':[('  HELLO  ','hello'),('\tMiXeD\n','mixed'),('',''),('  ÉCOLE ','école')]},
 'sorted-unique-lines':{'operations':['to-lines','unique','sort','join-lines'],'cases':[('b\na\nb','a\nb'),('z\nz','z'),('',''),('β\nα\nβ','α\nβ')]},
 'increment-number':{'operations':['increment'],'cases':[(0,1),(-9,-8),(42,43),(0.5,1.5)]}}
TASKS.update({
 'lowercase-text':{'operations':['lower'],'cases':[('ABC','abc'),('ÉCOLE','école'),('',''),('İ','i̇')]},
 'sorted-lines':{'operations':['to-lines','sort','join-lines'],'cases':[('b\na\nb','a\nb\nb'),('',''),('β\nα','α\nβ'),('A\na','A\na')]},
 'double-number':{'operations':['double'],'cases':[(0,0),(-9,-18),(42,84),(0.5,1.0)]},
 'absolute-number':{'operations':['absolute'],'cases':[(0,0),(-9,9),(42,42),(-0.5,0.5)]}})
class TeacherIntake:
 def __init__(self,data):
  self.path=data/'verified-teacher-skills.json';self.lock=threading.RLock();self.skills={};self.recent=[]
  try:
   if self.path.stat().st_size>524288:raise ValueError('Stored skill library exceeds its bounded size')
   saved=json.loads(self.path.read_text(encoding='utf-8'))
   if not isinstance(saved,dict):raise ValueError('Stored skills must be a mapping')
   for key,row in list(saved.items())[-64:]:
    if isinstance(key,str) and isinstance(row,dict) and row.get('task') in TASKS and row.get('retained') is True and isinstance(row.get('operations'),list) and 1<=len(row['operations'])<=4 and all(op in OPS for op in row['operations']):self.skills[key]=row
  except (OSError,ValueError,TypeError):pass
 def submit(self,proposal):
  if not isinstance(proposal,dict) or len(json.dumps(proposal))>16000:raise ValueError('Provide a compact lesson object')
  task=proposal.get('task');ops=proposal.get('operations');teacher=str(proposal.get('teacher','imported proposal'))[:100]
  if task not in TASKS:raise ValueError('Choose a registered task with independent native fixtures')
  if not isinstance(ops,list) or not 1<=len(ops)<=4 or any(op not in OPS for op in ops):raise ValueError('Use 1 to 4 registered pure operations')
  checks=[]
  for value,expected in TASKS[task]['cases']:
   try:actual=execute(ops,copy.deepcopy(value));ok=type(actual)==type(expected) and actual==expected
   except (ValueError,TypeError,OverflowError):ok=False
   checks.append(ok)
  row={'task':task,'teacher_label':teacher,'teacher_identity_verified':False,'operations':ops,'checks_passed':sum(checks),'checks_total':len(checks),'retained':all(checks),'time':time.time(),'scope':'Independent bundled fixtures for this task; not proof of unrestricted generalisation or model-weight transfer.'}
  row['id']=hashlib.sha256(json.dumps([task,ops],sort_keys=True).encode()).hexdigest()[:24]
  with self.lock:
   self.recent=(self.recent+[row])[-32:]
   if row['retained']:
    self.skills[row['id']]=row
    while len(self.skills)>64:self.skills.pop(next(iter(self.skills)))
    tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.skills),encoding='utf-8');os.replace(tmp,self.path)
  return copy.deepcopy(row)
 def run(self,ident,value):
  bounded(value)
  with self.lock:skill=copy.deepcopy(self.skills.get(str(ident)))
  if not skill:raise ValueError('Select a retained verified skill')
  # An independent task oracle checks every new use, not only initial fixtures.
  if skill['task'] in ('reverse-text','trim-lower-text','sorted-unique-lines','lowercase-text','sorted-lines') and not isinstance(value,str):raise ValueError('Text required')
  if skill['task'] in ('increment-number','double-number','absolute-number') and type(value) not in (int,float):raise ValueError('Number required')
  actual=execute(skill['operations'],copy.deepcopy(value))
  expected=value[::-1] if skill['task']=='reverse-text' else value.strip().lower() if skill['task']=='trim-lower-text' else '\n'.join(sorted(set(value.splitlines()))) if skill['task']=='sorted-unique-lines' else value.lower() if skill['task']=='lowercase-text' else '\n'.join(sorted(value.splitlines())) if skill['task']=='sorted-lines' else value*2 if skill['task']=='double-number' else abs(value) if skill['task']=='absolute-number' else value+1
  ok=type(actual)==type(expected) and actual==expected
  if not ok:raise ValueError('Skill failed independent verification; result withheld')
  return {'skill':ident,'task':skill['task'],'result':actual,'verified':True,'model_calls':0,'verification':'Independent task-specific oracle on this input'}
 def view(self):
  with self.lock:return {'tasks':list(TASKS),'allowed_operations':list(OPS),'skills':copy.deepcopy(list(self.skills.values())),'recent':copy.deepcopy(self.recent[-12:]),'connections':{'local_models':'Use existing configured local inference; this intake does not call a model','external_models':'No new connection configured or inferred'},'policy':'✝ Useful learning, truthful attribution, independent verification and repair. Imported proposals are inert data, not commands.','cost':'No model calls or paid provider access from lesson submission or skill reuse.'}
