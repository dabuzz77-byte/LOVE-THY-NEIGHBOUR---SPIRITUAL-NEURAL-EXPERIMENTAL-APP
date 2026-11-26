"""Independent task contracts and measured execution, separate from visual activity."""
import collections,copy,json,random,threading,time
from .native_synthesis import synthesize,execute
from .game_trainer import validate
from .document_trainer import outline,review
TASKS=('text-procedure','numeric-procedure','level-reachability','document-structure','compound-native-request','generated-code-transfer','goal-failure-recovery','conversation-context','branched-plan-transfer','grouped-table-transfer','constraint-ambiguity','general-deduction','general-explanation','general-probability','general-planning','open-reasoning-continuity','sentence-logic','exact-equations','multi-criterion-choice','cross-model-case','relational-transfer','supplied-source-answer','diagnostic-transfer','scenario-regret','transactional-task-recovery')
TASKS+=('attributed-rule-transfer','two-edit-code-repair','cross-tool-result-binding')
TASKS+=('quantity-transfer','code-counterexample-retention','task-preview-recovery')
class CapabilityValidation:
 def __init__(self,data):
  self.path=data/'capability-validation.json';self.lock=threading.RLock();self.next_at=0;self.sequence=0;self.results=collections.deque(maxlen=100);self.counts={};self.research_cache=collections.OrderedDict()
  try:
   old=json.loads(self.path.read_text(encoding='utf-8'));self.sequence=old.get('sequence',0);self.results.extend(old.get('results',[])[-100:]);self.counts=old.get('counts',{})
  except (OSError,ValueError):pass
 def run(self):
  start=time.perf_counter();rng=random.SystemRandom();kind=TASKS[self.sequence%len(TASKS)];record={'task':kind,'time':time.time(),'model_calls':0,'status':'failed'}
  try:
   if kind in ('text-procedure','numeric-procedure'):
    if kind=='text-procedure':
     values=['  '+''.join(rng.choice('aBcDeF') for _ in range(n))+'  ' for n in (4,7,9,12)];pairs=[{'input':v,'output':v.strip().lower()} for v in values];ops=['strip','lower'];fresh='  HeLdOuT '+str(rng.randrange(100000))+'  ';expected=fresh.strip().lower()
    else:
     values=[rng.randrange(-500,-1),rng.randrange(1,500),rng.randrange(-1000,-501),rng.randrange(501,1000)];pairs=[{'input':v,'output':abs(v)*2} for v in values];ops=['absolute','double'];fresh=rng.randrange(-100000,-1000);expected=abs(fresh)*2
    found=synthesize({'examples':pairs[:2],'holdout':pairs[2:],'operations':ops,'max_depth':2})
    if not found.get('solution'):raise ValueError('No procedure passed independent holdouts')
    record['selected_procedure']=found['solution']['operations'];record['fresh_input']=fresh
    actual=execute(found['solution']['operations'],fresh);assert actual==expected
    record.update(procedure=found['solution']['operations'],heldout_pairs=2,extra_unseen_test={'input':fresh,'expected':expected,'actual':actual},verification='Program selected using examples and holdouts, then checked on an additional unseen input.')
   elif kind=='level-reachability':
    width=rng.randrange(5,20);height=rng.randrange(5,16);rows=['#'*width]+['#'+'.'*(width-2)+'#' for _ in range(height-2)]+['#'*width];rows[1]=rows[1][:1]+'S'+rows[1][2:];rows[-2]=rows[-2][:-2]+'G#';a=validate(rows);expected=width+height-6;assert a['reachable'] and a['steps']==expected;negative=validate(['#####','#S#G#','#####']);assert not negative['reachable'];record.update(expected_shortest_path=expected,actual_shortest_path=a['steps'],blocked_goal_rejected=True)
   elif kind=='compound-native-request':
    from .native_task_planner import compile_goal
    from .reasoning_engine import pipeline
    a,b,c=[rng.randrange(1,1000) for _ in range(3)]
    request=f'add {b} then multiply by {c}: {a}';plan=compile_goal(request)
    actual=pipeline(plan['input'],plan['steps'])['result'];expected=(a+b)*c
    if actual!=expected:raise ValueError('Compound request disagrees with arithmetic oracle')
    record.update(request=request,actual=actual,expected=expected,verification='Fresh generated operands; independent arithmetic oracle; no model calls.')
   elif kind=='generated-code-transfer':
    from .native_work import python_export
    from .function_testing import FunctionTest
    values=[rng.randrange(-100,100) for _ in range(9)];threshold=rng.randrange(-30,30)
    steps=[{'op':'filter','relation':'at_least','value':threshold},{'op':'sort'}]
    expected=sorted(v for v in values if v>=threshold)
    exported=python_export(steps,values,expected)
    fresh=[rng.randrange(-1000,1000) for _ in range(17)];oracle=sorted(v for v in fresh if v>=threshold)
    actual=FunctionTest(exported['source']).invoke('transform',[fresh])
    if actual!=oracle:raise ValueError('Generated code fails fresh independent transfer case')
    record.update(source_sha256=exported['source_sha256'],extra_unseen_test={'input':fresh,'actual':actual,'expected':oracle},verification='Code generated before fresh input; bounded execution with an independent list-comprehension oracle.')
   elif kind=='goal-failure-recovery':
    from .native_goals import create,advance
    from .native_work import NativeWork
    base=rng.randrange(2,1000);work=NativeWork({'last':'retained','has_last':True})
    broken=create({'name':'recovery check','input':base,'stages':[{'instruction':'add 2','expected':base+99}]})
    advance(broken,work)
    if broken['status']!='acceptance-failed' or work.state['last']!='retained':raise ValueError('Failed goal overwrote previous accepted work')
    fixed=create({'name':'corrected goal','input':base,'stages':[{'instruction':'add 2','expected':base+2},{'instruction':'multiply by 3','expected':(base+2)*3}]})
    while fixed['status']=='running':advance(fixed,work)
    if not fixed['committed'] or work.state['last']!=(base+2)*3:raise ValueError('Corrected goal did not commit verified result')
    record.update(failure_retained_previous=True,recovery_verified=True,verification='Deliberate incorrect acceptance case, preserved prior result, corrected two-stage task and complete replay.')
   elif kind=='conversation-context':
    from .native_dialogue import NativeDialogue
    from .deliberation import Deliberation
    chat=NativeDialogue(Deliberation());a,b=rng.randrange(1,100),rng.randrange(1,100)
    chat.send({'text':'uppercase'})
    question=chat.send({'text':f'what is {a} times {b}?'})
    if question['answer']!=str(a*b):raise ValueError('A new question was consumed as pending data')
    literal=chat.send({'text':'input: field: '+str(a)})
    if literal['answer']!='FIELD: '+str(a):raise ValueError('Explicit literal input lost pending context')
    record.update(new_question_answered=True,pending_context_preserved=True,verification='Fresh arithmetic question during pending text input, followed by explicit literal input; no model calls.')
   elif kind=='branched-plan-transfer':
    from .native_plans import run_plan,export_plan
    from .function_testing import FunctionTest
    number=rng.randrange(-100,101)
    spec={'input':number,'nodes':[{'id':'branch','when':{'from':'input','relation':'at_least','value':0},'then':[{'op':'scale','value':2}],'else':[{'op':'scale','value':-2}]}],'output':'branch'}
    report=run_plan(spec);code=export_plan(spec,report)
    fresh=-number if number else -7;actual=FunctionTest(code['source']).invoke('transform',[fresh]);expected=abs(fresh)*2
    if actual!=expected:raise ValueError('Exported branch fails an independently evaluated fresh input')
    record.update(source_sha256=code['source_sha256'],fresh_input=fresh,actual=actual,expected=expected,verification='Opposite-sign branch transfer after export; independently calculated absolute-value oracle.')
   elif kind=='grouped-table-transfer':
    from .reasoning_engine import pipeline
    from .native_work import python_export
    rows=[{'region':rng.choice(['north','south','east']),'amount':rng.randrange(-100,100)} for _ in range(8)]
    keys=list(dict.fromkeys(r['region'] for r in rows));expected=[{'key':key,'value':sum(r['amount'] for r in rows if r['region']==key),'count':sum(r['region']==key for r in rows)} for key in keys]
    steps=[{'op':'group','field':'region','value_field':'amount','aggregate':'sum'}];actual=pipeline(rows,steps)['result'];code=python_export(steps,rows,expected)
    if actual!=expected or not code['checks']['all_passed']:raise ValueError('Grouped table disagrees with independently accumulated totals')
    record.update(source_sha256=code['source_sha256'],actual=actual,expected=expected,verification='Fresh grouped rows, independent sum/count oracle and checked Python export.')
   elif kind=='constraint-ambiguity':
    from .constraint_reasoning import solve
    target=rng.randrange(0,7);oracle=[{'x':x,'y':y} for x in range(4) for y in range(4) if x+y==target]
    result=solve({'domains':{'x':list(range(4)),'y':list(range(4))},'constraints':[{'terms':{'x':1,'y':1},'relation':'equal','value':target}],'check_uniqueness':True})
    expected='multiple' if len(oracle)>1 else 'unique' if oracle else 'no-solution'
    if result['uniqueness']!=expected or any(row not in oracle for row in result['solutions']):raise ValueError('Constraint ambiguity report disagrees with exhaustive enumeration')
    record.update(uniqueness=result['uniqueness'],expected=expected,verification='All domain pairs independently enumerated; every returned witness checked.')
   elif kind=='general-deduction':
    from .general_reasoning import reason
    result=reason({'premises':[{'implies':['p','q']},'q'],'query':'p'})
    if result['status']!='contingent' or result['counterexample_world']!={'p':False,'q':True}:raise ValueError('Affirming the consequent was not rejected')
    record.update(status_checked=result['status'],verification='Separate counterexample to an invalid converse; finite logic, not a world observation.')
   elif kind=='general-explanation':
    from .general_reasoning import reason
    result=reason({'mode':'explanation','facts':[],'hypotheses':['a','b'],'observations':['observed'],'rules':[{'if':['a'],'then':'observed'},{'if':['b'],'then':'observed'}]})
    if result['equal_cost_explanation_count']!=2 or not result['minimum_cost_proven']:raise ValueError('Competing explanations were conflated')
    record.update(explanations=2,verification='Two explicit alternative explanations; neither is promoted to an observed cause.')
   elif kind=='general-probability':
    from .general_reasoning import reason
    prior=rng.randrange(1,10)/10;likelihood_a=rng.randrange(1,10)/10;likelihood_b=rng.randrange(1,10)/10
    result=reason({'mode':'probability','hypotheses':[{'name':'a','prior':prior,'likelihoods':{'e':likelihood_a}},{'name':'b','prior':1-prior,'likelihoods':{'e':likelihood_b}}],'evidence':['e']})
    expected=prior*likelihood_a/(prior*likelihood_a+(1-prior)*likelihood_b);actual=result['posterior'][0]['posterior']
    if abs(actual-expected)>1e-12:raise ValueError('Posterior disagrees with independent direct Bayes calculation')
    record.update(actual=actual,expected=expected,verification='Fresh declared priors and likelihoods; no empirical calibration claim.')
   elif kind=='general-planning':
    from .general_reasoning import reason
    a,b,c=[rng.randrange(1,20) for _ in range(3)]
    result=reason({'mode':'planning','initial':['start'],'goals':['goal'],'actions':[{'name':'first','preconditions':['start'],'add':['middle'],'cost':a},{'name':'second','preconditions':['middle'],'add':['goal'],'cost':b},{'name':'direct','preconditions':['start'],'add':['goal'],'cost':c}]})
    if result.get('total_cost')!=min(a+b,c) or not result.get('plan_replayed'):raise ValueError('Route is not the least-cost replayed model plan')
    record.update(cost=result['total_cost'],verification='Two independently calculated possible routes; simulated plan only.')
   elif kind=='open-reasoning-continuity':
    from .native_dialogue import NativeDialogue
    from .deliberation import Deliberation
    chat=NativeDialogue(Deliberation());a,b=rng.randrange(1,100),rng.randrange(1,100)
    chat.send({'text':'Should I choose Alpha or Beta?'})
    chat.send({'text':'options: Alpha or Beta'});chat.send({'text':'priority: cost'})
    reply=chat.send({'text':f'facts: Alpha costs £{a}; Beta costs £{b}'})
    finding=reply['work']['open_reasoning']['findings'][0];expected=['Alpha'] if a<b else ['Beta'] if b<a else ['Alpha','Beta']
    if finding['lowest_options']!=expected:raise ValueError('Multi-turn cost conclusion does not match supplied figures')
    record.update(expected=expected,actual=finding['lowest_options'],verification='Supplied-cost comparison after clarification; no general recommendation or model call.')
   elif kind=='sentence-logic':
    from .general_reasoning import reason
    from .open_reasoning import natural_logic
    suffix=str(rng.randrange(1000));source=f'If signal{suffix} then alarm{suffix}. Alarm{suffix}. Does signal{suffix} follow?'
    result=reason(natural_logic(source))
    if result['status']!='contingent':raise ValueError('Sentence interpretation incorrectly affirmed the converse')
    record.update(status_checked=result['status'],verification='Plain-sentence explicit implication; invalid converse remains unresolved with a counterexample.')
   elif kind=='exact-equations':
    from .general_reasoning import reason
    x,y=rng.randrange(-100,100),rng.randrange(-100,100)
    result=reason({'mode':'equations','variables':['x','y'],'equations':[{'terms':{'x':1,'y':1},'equals':x+y},{'terms':{'x':1,'y':-1},'equals':x-y}]})
    if result['determined_values']!={'x':str(x),'y':str(y)} or not result['all_equations_substitution_checked']:raise ValueError('Exact equations disagree with generated source values')
    record.update(values=result['determined_values'],verification='Fresh known-solution equations, exact solution and full symbolic substitution.')
   elif kind=='multi-criterion-choice':
    from .general_reasoning import reason
    points=[(rng.randrange(20),rng.randrange(20)) for _ in range(4)]
    result=reason({'mode':'decision','criteria':[{'name':'cost','direction':'min'},{'name':'quality','direction':'max'}],'options':[{'name':str(i),'values':{'cost':c,'quality':q}} for i,(c,q) in enumerate(points)]})
    expected={str(i) for i,(c,q) in enumerate(points) if not any(j!=i and c2<=c and q2>=q and (c2<c or q2>q) for j,(c2,q2) in enumerate(points))}
    if set(result['pareto_frontier'])!=expected:raise ValueError('Trade-off frontier disagrees with independent pairwise comparison')
    record.update(frontier=result['pareto_frontier'],verification='Fresh objective points with explicit min/max directions; no invented utility weights.')
   elif kind=='cross-model-case':
    from .general_reasoning import reason
    cost=rng.randrange(1,100)
    result=reason({'mode':'case','stages':[{'id':'derive','task':{'mode':'equations','variables':['x'],'equations':[{'terms':{'x':2},'equals':2*cost}]}},{'id':'choose','task':{'mode':'decision','criteria':[{'name':'cost','direction':'min'}],'options':[{'name':'a','values':{'cost':0}},{'name':'b','values':{'cost':cost+1}}]},'bindings':[{'from':'derive','path':['determined_values','x'],'to':['options',0,'values','cost']}]}]})
    if result['status']!='complete' or result['stages'][1]['result']['pareto_frontier']!=['a']:raise ValueError('Checked model output did not reach the downstream comparison')
    record.update(binding=result['stages'][1]['bindings'][0]['exact_value'],verification='Exact algebra value passed with provenance into an independent pure decision model.')
   elif kind=='relational-transfer':
    from .general_reasoning import reason
    suffix=str(rng.randrange(10000));actor='actor'+suffix;project='project'+suffix;place='place'+suffix
    result=reason({'mode':'relations','facts':[{'subject':actor,'relation':'leads','object':project},{'subject':project,'relation':'based_in','object':place}],'query':[{'subject':actor,'relation':'leads','object':'?project'},{'subject':'?project','relation':'based_in','object':'?place'}],'select':['?place']})
    if result['status']!='answered' or result['answers'][0]['bindings']!={'?place':place}:raise ValueError('Relational join failed a fresh entity binding')
    record.update(proof_facts=len(result['proof_graph']),verification='Two supplied relations joined with an inspectable proof trail; no external knowledge assumed.')
   elif kind=='supplied-source-answer':
    from .general_reasoning import reason
    suffix=str(rng.randrange(10000));actor='Actor'+suffix;project='Project'+suffix
    result=reason({'mode':'reading','text':actor+' leads '+project+'. '+project+' is a project. '+project+' is based in Oslo.','question':'Where is the project that '+actor+' leads based?'})
    if result['status']!='answered' or result['answers'][0]['bindings']!={'?answer':'oslo'} or len(result['proof_graph'])!=3:raise ValueError('Source question did not retain the required three facts')
    record.update(proof_facts=3,verification='Fresh named entities in a supplied passage; answer checked against the explicit source chain.')
   elif kind=='quantity-transfer':
    from .general_reasoning import reason
    from fractions import Fraction
    distance,minutes=rng.randrange(1,10000),rng.randrange(1,1000)
    result=reason({'mode':'units','expression':f'{distance} km / {minutes} min','target':'m/s'})
    if Fraction(result['exact_value'])!=Fraction(distance*1000,minutes*60):raise ValueError('Unit conversion disagrees with independent rational oracle')
    record.update(verification='Fresh distance and time quantities, dimensional conversion and independent exact fraction check.')
   elif kind=='code-counterexample-retention':
    from .native_work import NativeWork
    work=NativeWork();work.handle('write Python to double: 3')
    failed=work.handle('test this code: '+json.dumps({'cases':[{'args':[4],'expected':9}]}));later=work.handle('test this code: '+json.dumps({'cases':[{'args':[5],'expected':10}]}))
    if failed['status']!='test-failed' or later['status']!='test-failed':raise ValueError('A later passing test erased a recorded counterexample')
    record.update(verification='Deliberately failing test retained despite a later passing case; no source was executed on the host.')
   elif kind=='task-preview-recovery':
    from .native_work import NativeWork
    work=NativeWork({'last':77,'has_last':True});work.handle('preview tasks: '+json.dumps({'tasks':[{'id':'sum','kind':'workflow','request':'sum: [2,3]'},{'id':'double','kind':'workflow','request':'double; expect: 99'}]}));before=copy.deepcopy(work.state)
    failed=work.handle('run previewed tasks')
    if failed['committed'] or work.state!=before:raise ValueError('Failed preview changed completed working data')
    work.handle('revise preview task double: {"request":"double; expect: 10"}');fixed=work.handle('run previewed tasks')
    if not fixed['committed'] or work.state['last']!=10:raise ValueError('Corrected preview failed to complete')
    record.update(verification='Preview without computation, failed bundle rollback, explicit task correction and successful rerun.')
   elif kind=='attributed-rule-transfer':
    from .general_reasoning import reason
    actor='P'+str(rng.randrange(100000));category='C'+str(rng.randrange(100000))
    result=reason({'mode':'reading','sources':[{'source':'roster','text':actor+' is a '+category+'.'},{'source':'policy','text':'Every '+category+' requires funding.'}],'question':'Does '+actor+' require funding?'})
    if result['status']!='answered' or len(result['source_rules'])!=1 or len(result['proof_graph'])!=2:raise ValueError('Attributed rule transfer lost its proof')
    record.update(verification='Fresh actor and category labels; attributed universal rule and explicit membership checked together.')
   elif kind=='two-edit-code-repair':
    from .tested_repairs import repair
    from .function_testing import FunctionTest
    result=repair({'source':'def f(a,b):\n return (a-b)*2\n','function':'f','cases':[{'args':[3,1],'expected':12},{'args':[2,4],'expected':18},{'args':[5,-1],'expected':12}]})
    if result['status']!='validated-proposal' or result['edit_count']!=2:raise ValueError('Two-edit function repair failed')
    a,b=rng.randrange(-100,100),rng.randrange(-100,100)
    if FunctionTest(result['source']).invoke('f',[a,b])!=(a+b)*3:raise ValueError('Repaired function failed fresh arithmetic oracle')
    record.update(verification='Two local edits selected on training cases, distinct validation and fresh arithmetic transfer input.')
   elif kind=='cross-tool-result-binding':
    from .native_work import NativeWork
    value=rng.randrange(-100,100)
    result=NativeWork().handle('run tasks: '+json.dumps({'tasks':[{'id':'solve','kind':'reasoning','task':{'mode':'equations','variables':['x'],'equations':[{'terms':{'x':2},'equals':2*value}]}},{'id':'work','kind':'workflow','request':'double','input_from':{'task':'solve','path':['general_reasoning','determined_values','x'],'convert':'number'}}]}))
    if not result['committed'] or result['outputs'][-1]['value']!=2*value:raise ValueError('Checked numeric result did not transfer between tools')
    record.update(verification='Fresh exact equation solution transferred through an explicit attributed input binding to checked data work.')
   elif kind=='diagnostic-transfer':
    from .general_reasoning import reason
    actual=rng.randrange(100);other=actual+1
    result=reason({'mode':'diagnostic','observations':{'probe':actual},'hypotheses':[{'name':'A','predictions':{'probe':actual}},{'name':'B','predictions':{'probe':other}},{'name':'unknown','predictions':{}}]})
    if result['remaining']!=['A','unknown']:raise ValueError('Diagnostic transfer eliminated an unknown or retained a mismatch')
    record.update(verification='Fresh explicit predictions; a missing prediction remains unresolved rather than treated as false.')
   elif kind=='scenario-regret':
    from .general_reasoning import reason
    values=[[rng.randrange(-100,100) for _ in range(3)] for _ in range(4)];states=['a','b','c'];best=[max(r[j] for r in values) for j in range(3)];regrets=[max(best[j]-r[j] for j in range(3)) for r in values]
    result=reason({'mode':'scenarios','scenarios':states,'options':[{'name':str(i),'outcomes':dict(zip(states,r))} for i,r in enumerate(values)]})
    expected=[str(i) for i,r in enumerate(regrets) if r==min(regrets)]
    if result['minimax_regret_options']!=expected or result['probabilities_supplied']:raise ValueError('Scenario regret disagrees with independent integer oracle')
    record.update(verification='Fresh outcome table and independent worst-case regret oracle; no probabilities inferred.')
   elif kind=='transactional-task-recovery':
    from .native_work import NativeWork
    initial=rng.randrange(100);work=NativeWork({'last':initial,'has_last':True});before=copy.deepcopy(work.state)
    result=work.handle('run tasks: '+json.dumps({'tasks':[{'id':'first','kind':'workflow','request':'sum: [2,3]'}, {'id':'second','kind':'workflow','request':'double; expect: 99'}]}))
    if result['committed'] or work.state!=before:raise ValueError('Failed bundle changed accepted working state')
    record.update(verification='A later failed acceptance check rolls back all earlier bundle working-memory changes.')
   else:
    kind_doc=rng.choice(['Policy','Formal letter','Research report','Meeting minutes']);sections=outline(kind_doc);omitted=rng.randrange(len(sections));draft='\n'.join(h+'\nVerified section content.' for h in sections);broken='\n'.join(h for i,h in enumerate(sections) if i!=omitted);a=review(kind_doc,draft);b=review(kind_doc,broken);assert not a['missing_sections'] and sections[omitted] in b['missing_sections'];record.update(document_type=kind_doc,omitted_section_detected=sections[omitted],verification='Structural check only; prose quality and factual accuracy not assessed.')
   record['status']='passed'
  except Exception as e:record.update(error=type(e).__name__+': '+str(e)[:300],next_step='Reproduce the failed contract before retaining or extending a procedure.')
  record['milliseconds']=round((time.perf_counter()-start)*1000,3)
  with self.lock:
   self.sequence+=1;record['sequence']=self.sequence;self.results.append(record);count=self.counts.setdefault(kind,{'passed':0,'failed':0});count[record['status']]+=1
   if self.sequence%4==0:self.save()
  return copy.deepcopy(record)
 def save(self):
  tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps({'sequence':self.sequence,'results':list(self.results),'counts':self.counts}),encoding='utf-8');tmp.replace(self.path)
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+10;result=self.run();c.bus.publish({'origin':'capability-validation','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'passed':result['status']=='passed','milliseconds':result['milliseconds'],'provenance':'independent-native-task-contract','predefined_text':True,'stochastic':False}})
 def view(self):
  with self.lock:
   rows=copy.deepcopy(list(self.results));times=sorted(x['milliseconds'] for x in rows)
   return {'sequence':self.sequence,'counts':copy.deepcopy(self.counts),'recent':rows[-16:],'timing':{'median_ms':times[len(times)//2] if times else None,'maximum_ms':max(times) if times else None},'scope':'Independent native bounded-task contracts. These do not establish general intelligence or real-world task success.'}

 def read_source(self,c,url,query=''):
  from .free_learning import RESOURCES
  from .world_knowledge import SOURCES
  from .reviewed_web import read_page
  allowed={row[1] for entries in RESOURCES.values() for row in entries}|{row[1] for entries in SOURCES.values() for row in entries}
  from .principle_research import DOMAINS
  allowed.update(url for _, refs in DOMAINS.values() for _,url in refs)
  study=getattr(c,'source_study',None)
  if study:
   with study.lock:allowed.update(study.discovered)
  if url not in allowed:raise ValueError('Choose a catalogued public learning or world-knowledge source')
  key=url;now=time.time()
  with self.lock:cached=self.research_cache.get(key)
  if cached and now-cached['fetched']<3600:result=copy.deepcopy(cached);result['cached']=True
  else:
   page=read_page(url);paragraphs=[x.strip() for x in page['text'].splitlines() if len(x.strip())>=35]
   result={'url':url,'fetched':now,'cached':False,'paragraphs':paragraphs[:160],'bytes':page['bytes'],'truncated':page.get('text_truncated',False),'scope':'Extracted source text, not verified claims or instructions.'}
   with self.lock:
    self.research_cache[key]=copy.deepcopy(result);self.research_cache.move_to_end(key)
    while len(self.research_cache)>24:self.research_cache.popitem(last=False)
  terms=set(str(query).lower().split());ranked=sorted(enumerate(result['paragraphs']),key=lambda row:(-sum(t in row[1].lower() for t in terms),row[0]));result['excerpts']=[text[:1200] for _,text in ranked[:4]];result.pop('paragraphs',None)
  intake=getattr(c.world_knowledge,'intake',None)
  if intake and hasattr(intake,'store'):
   for text in result['excerpts']:intake.store('Retrieved public learning content',url,'Source excerpt: '+str(query)[:100],text)
  return result
