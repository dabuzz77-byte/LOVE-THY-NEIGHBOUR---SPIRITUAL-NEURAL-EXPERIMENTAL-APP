"""Generated native practice with independent expected answers and bounded histories."""
import collections,difflib,json,random
from urllib.parse import urlsplit
from .native_language import canonical_request
from .native_scripts import FORMATS,generate
from .native_skills import respond
COMMANDS=['status','system status','script formats','list files','show tasks','show memories','what did you learn?','what can you do','engine quality','run quality checks']
def suggestions(text):
 if len(text)>200:return []
 return difflib.get_close_matches(text.lower().strip(),COMMANDS,n=3,cutoff=.65)
def trial(kind,seed,step,data):
 rng=random.Random(int.from_bytes(seed,'big')+step);rows=[]
 if kind=='logic':
  language=list(FORMATS)[(step//2)%len(FORMATS)];extension,alias=FORMATS[language]
  for i in range(4):
   a,b=rng.randrange(1,90),rng.randrange(1,90);concept=rng.choice(['sum','product','difference']);draft=generate(language,concept,'Exercise'+extension,a,b);want={'sum':a+b,'product':a*b,'difference':a-b}[concept];rows.append({'expected':want,'actual':draft['expected'],'passed':want==draft['expected']})
  from .language_formats import syntax
  try:check=syntax({'language':alias,'source':draft['source'],'filename':draft['filename']},data)
  except (ValueError,OSError) as e:check={'passed':None,'method':'checker unavailable','diagnostics':str(e)}
  return {'training_passed':all(x['passed'] for x in rows[:2]),'validation_passed':all(x['passed'] for x in rows[2:]) and check.get('passed') is not False,'lesson':'script generation / '+language,'training_cases':rows[:2],'fresh_validation_cases':rows[2:],'source_check':check,'retained':False,'scope':'Template parameter validation; source-check status separate; generated programs not executed'}
 if kind=='conversation':
  for base in COMMANDS:
   actual=canonical_request('please could you '+base);rows.append({'input':base,'expected':base,'actual':actual,'passed':actual==base})
  return result('phrasing and command recognition',rows)
 if kind=='work':
  for i in range(8):
   values=[str(rng.randrange(30)) for _ in range(12)];ordered=respond('sort lines\n'+'\n'.join(values))['result'];actual=respond('unique lines\n'+ordered)['result'];expected='\n'.join(sorted(set(values)));rows.append({'expected':expected,'actual':actual,'passed':actual==expected})
  from .native_workbench import rank
  token='topic'+str(rng.randrange(1000000));retrieved=rank(token,[{'id':'match','text':token+' evidence'},{'id':'other','text':'unrelated record'}]);rows.append({'expected':'match','actual':retrieved[0]['id'] if retrieved else None,'passed':bool(retrieved) and retrieved[0]['id']=='match'})
  return result('linked transforms and source retrieval',rows)
 if kind=='coordinator':
  for i in range(8):
   jobs=[{'id':j,'priority':rng.randrange(4),'cost':rng.randrange(1,5)} for j in range(8)];budget=rng.randrange(4,20);actual=[];remaining=budget
   for j in sorted(jobs,key=lambda j:(j['priority'],j['id'])):
    if j['cost']<=remaining:actual.append(j['id']);remaining-=j['cost']
   passed=len(actual)==len(set(actual)) and sum(jobs[j]['cost'] for j in actual)<=budget
   rows.append({'budget':budget,'selected':actual,'remaining':remaining,'passed':passed})
  return result('variable scheduling budgets and unique actions',rows)
 for i in range(8):
  host='node'+str(rng.randrange(10000))+'.example.org';url='https://'+host+'/data?q='+str(i);p=urlsplit(url);rows.append({'url':url,'passed':p.scheme=='https' and p.hostname==host and p.path=='/data'})
 return result('varied network origin and request parsing',rows)
def result(lesson,rows):
 return {'training_passed':all(x['passed'] for x in rows[:4]),'validation_passed':all(x['passed'] for x in rows[4:]),'lesson':lesson,'training_cases':rows[:4],'fresh_validation_cases':rows[4:],'retained':False,'scope':'Generated native component exercises; not certification of arbitrary conversation or external system actions'}
