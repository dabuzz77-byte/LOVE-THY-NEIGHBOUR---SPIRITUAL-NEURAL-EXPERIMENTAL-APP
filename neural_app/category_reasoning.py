"""Finite-model categorical reasoning with explicit existential witnesses."""
import copy,json,re

CATEGORY=r'([a-z][a-z0-9_-]{0,40})'

def clause(text,question=False):
 text=text.strip().casefold().rstrip('?.');kind=None
 patterns=[(rf'all {CATEGORY} are {CATEGORY}','all'),(rf'no {CATEGORY} are {CATEGORY}','none'),(rf'some {CATEGORY} are not {CATEGORY}','some-not'),(rf'some {CATEGORY} are {CATEGORY}','some')]
 if question:patterns=[(rf'are all {CATEGORY} {CATEGORY}','all'),(rf'are any {CATEGORY} {CATEGORY}','some'),(rf'are some {CATEGORY} not {CATEGORY}','some-not')]
 for pattern,kind in patterns:
  match=re.fullmatch(pattern,text)
  if match:
   names=[' '.join(v.split()) for v in match.groups()]
   if any(any(word in n.split() for word in ('and','or','not','are','all','some','no','any')) for n in names):continue
   return {'kind':kind,'left':names[0],'right':names[1]}
 raise ValueError('Use complete All A are B, No A are B, Some A are B or Some A are not B clauses, followed by Are all A B? or Are any A B? Use single-word category names in questions.')

def solve(text):
 parts=[s.strip() for s in re.split(r'[.;]\s*',text.strip()) if s.strip()]
 if not 2<=len(parts)<=17:raise ValueError('Use 1–16 category statements and one final question')
 statements=[clause(p) for p in parts[:-1]];query=clause(parts[-1],True)
 names=sorted({r[k] for r in statements+[query] for k in ('left','right')})
 if len(names)>8:raise ValueError('Use at most eight category names')
 bits={n:1<<i for i,n in enumerate(names)};types=list(range(1<<len(names)))
 def matches(mask,row):
  a=bool(mask&bits[row['left']]);b=bool(mask&bits[row['right']])
  return {'all':not a or b,'none':not(a and b),'some':a and b,'some-not':a and not b}[row['kind']]
 def model(rows):
  allowed=[mask for mask in types if all(matches(mask,r) for r in rows if r['kind'] in ('all','none'))];witnesses=[]
  for row in rows:
   if row['kind'] in ('some','some-not'):
    choices=[mask for mask in allowed if matches(mask,row)]
    if not choices:return None
    if choices[0] not in witnesses:witnesses.append(choices[0])
  if not allowed:return None
  return [[name for name in names if mask&bits[name]] for mask in (witnesses or [allowed[0]])]
 negation={'all':'some-not','none':'some','some':'none','some-not':'all'}
 base=model(statements);yes=model(statements+[query]);no=model(statements+[{**query,'kind':negation[query['kind']]}])
 status='inconsistent' if base is None else 'entailed' if no is None else 'refuted' if yes is None else 'undetermined'
 answer={'inconsistent':'The premises conflict; no conclusion is licensed.','entailed':'Yes. The conclusion follows from the supplied premises.','refuted':'No. The premises entail its negation.','undetermined':'The premises do not determine the answer; models supporting both answers exist.'}[status]
 return {'status':status,'answer':answer,'premises':statements,'query':query,'supporting_model':yes,'countermodel':no,'categories':names,'membership_types_examined':len(types),'model_calls':0,'scope':'Classical categorical logic over arbitrary nonempty domains. Universal statements do not imply their categories exist. Some explicitly requires a witness. Countermodels demonstrate logical possibilities, not observations.'}

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!')
 if key=='write python for category model':
  report=work.state.get('category_reasoning')
  if not report:return {'status':'needs-input','answer':'Complete a category problem first.','model_calls':0}
  from .native_work import digest
  if report.get('receipt_sha256')!=digest({k:v for k,v in report.items() if k!='receipt_sha256'}):raise ValueError('Category model changed after its receipt; supply the problem again')
  lines=['def check_model(population):','    if not isinstance(population, list):','        return False','    if len(population) == 0 or len(population) > 256:','        return False','    for member in population:','        if not isinstance(member, list):','            return False','        for category in member:','            if category not in '+repr(report['categories'])+':','                return False']
  for row in report['premises']:
   left=repr(row['left'])+' in member';right=repr(row['right'])+' in member'
   if row['kind'] in ('all','none'):
    condition=left+' and '+('not ('+right+')' if row['kind']=='all' else right)
    lines+=['    for member in population:','        if '+condition+':','            return False']
   else:
    condition=left+' and '+('not ('+right+')' if row['kind']=='some-not' else right)
    lines+=['    found = False','    for member in population:','        if '+condition+':','            found = True','    if not found:','        return False']
  lines+=['    return True'];source='\n'.join(lines)+'\n';populations=[[],[[]]]
  names=report['categories']
  populations += [[[name for i,name in enumerate(names) if mask&(1<<i)]] for mask in range(min(16,1<<len(names)))]
  populations += [v for v in (report['supporting_model'],report['countermodel']) if v is not None]
  def accepts(population):
   if not population:return False
   for row in report['premises']:
    pairs=[(row['left'] in member,row['right'] in member) for member in population]
    valid={'all':all(not a or b for a,b in pairs),'none':all(not(a and b) for a,b in pairs),'some':any(a and b for a,b in pairs),'some-not':any(a and not b for a,b in pairs)}[row['kind']]
    if not valid:return False
   return True
  cases=[{'args':[p],'expected':accepts(p)} for p in populations]
  from .function_testing import test_function
  checks=test_function({'source':source,'function':'check_model','cases':cases})
  if not checks['all_passed']:raise ValueError('Generated category checker failed differential checks; previous code retained')
  code={'source':source,'function':'check_model','source_sha256':digest(source),'checks':checks,'extra_checks':[],'replay_cases':copy.deepcopy(cases)}
  work.state['last_generated_code']=code;work.state['last_code_review']={'checks':copy.deepcopy(checks),'scope':'Checks whether a supplied finite population satisfies the premises. This does not establish the premises as real-world facts.'};work.state['focus_kind']='code'
  return {'status':'complete','answer':'```python\n'+source+'```\nThis function checks the premises against a supplied population, not whether the conclusion holds in every possible population.','code':copy.deepcopy(code),'model_calls':0}
 if key=='explain category reasoning':
  report=work.state.get('category_reasoning')
  if not report:return {'status':'needs-input','answer':'Supply a category problem first.','model_calls':0}
  from .native_work import digest
  if report.get('receipt_sha256')!=digest({k:v for k,v in report.items() if k!='receipt_sha256'}):raise ValueError('Category result changed; supply the problem again')
  return {'status':'complete','answer':report['answer']+'\nSupporting model: '+json.dumps(report['supporting_model'])+'\nCountermodel: '+json.dumps(report['countermodel'])+'\n'+report['scope'],'action_repeated':False,'model_calls':0}
 explicit=re.match(r'^reason categories:\s*(.+)',text.strip(),re.I|re.S)
 if not explicit and not (re.match(r'^(?:all|no|some)\s',text.strip(),re.I) and re.search(r'\bare (?:all|any|some)\b',text,re.I)):return None
 report=solve(explicit[1] if explicit else text)
 from .native_work import digest
 report['receipt_sha256']=digest(report)
 work.state['category_reasoning']=copy.deepcopy(report);work.state['focus_kind']='category-reasoning'
 return report
