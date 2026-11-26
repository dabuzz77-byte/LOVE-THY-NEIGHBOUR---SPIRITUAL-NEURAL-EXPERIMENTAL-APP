"""Bounded relational joins and range-restricted rules with source/proof trails."""
import re,time,copy

def text(value):
 if not isinstance(value,str) or not value.strip() or len(value)>120 or '\n' in value:raise ValueError('Relation labels must be short nonempty single-line text')
 return ' '.join(value.casefold().split())

def variable(value):return bool(re.fullmatch(r'\?[a-z][a-z0-9_]{0,30}',value))

def pattern(row,ground=False):
 if not isinstance(row,dict):raise ValueError('Provide relation objects with subject, relation and object')
 result={k:text(row.get(k,'default' if k=='context' else '')) for k in ('subject','relation','object','context')}
 if type(row.get('negated',False))is not bool:raise ValueError('Negated must be a boolean')
 result['negated']=row.get('negated',False)
 for key,value in result.items():
  if key=='negated':continue
  if value.startswith('?') and (not variable(value) or ground or key=='relation'):raise ValueError('Variables are allowed only in query/rule subject, object and context positions')
 return result

def key(row):return tuple(row[k] for k in ('subject','relation','object','context','negated'))

class Limit(Exception):pass

def solve(body):
 raw=body.get('facts',[]);rules=body.get('rules',[]);query=body.get('query');limit=body.get('fact_limit',512)
 if not isinstance(raw,list) or len(raw)>128 or not isinstance(rules,list) or len(rules)>16 or not isinstance(query,list) or not 1<=len(query)<=4 or type(limit)is not int or not 1<=limit<=512:raise ValueError('Use up to 128 facts, 16 rules, 1–4 query patterns and fact_limit 1–512')
 queries=[pattern(row) for row in query];compiled=[]
 def variables(row):return {v for k,v in row.items() if k!='negated' and variable(v)}
 for i,row in enumerate(rules):
  if not isinstance(row,dict) or not isinstance(row.get('if'),list) or not 1<=len(row['if'])<=4:raise ValueError('Rules require 1–4 premise patterns and one then pattern')
  premises=[pattern(p) for p in row['if']];head=pattern(row.get('then'))
  if not variables(head)<=set().union(*(variables(p) for p in premises)):raise ValueError('Every rule output variable must be bound in a premise')
  compiled.append({'id':i+1,'if':premises,'then':head})
 names=sorted(set().union(*(variables(p) for p in queries)));selected=body.get('select',names)
 if not isinstance(selected,list) or len(selected)>8 or any(not isinstance(v,str) or v not in names for v in selected) or len(set(selected))!=len(selected):raise ValueError('Select only distinct variables bound by the query')
 facts=[];lookup={};index={};deadline=time.monotonic()+1;operations=0;complete=True;limit_reason=None
 def add(row,proof):
  signature=key(row)
  if signature in lookup:
   old=facts[lookup[signature]-1]
   if proof['kind']=='given' and proof not in old['given_sources']:old['given_sources'].append(proof)
   return False
  if len(facts)>=limit:raise Limit('fact limit')
  ident=len(facts)+1;record={**row,'id':ident,'proof':proof,'given_sources':[proof] if proof['kind']=='given' else []};facts.append(record);lookup[signature]=ident;index.setdefault((row['relation'],row['negated']),[]).append(ident);return True
 for i,row in enumerate(raw):
  parsed=pattern(row,ground=True);source=row.get('source','user-fact:'+str(i+1))
  if not isinstance(source,str) or len(source)>300:raise ValueError('Source attributions must be bounded text')
  try:add(parsed,{'kind':'given','source_fact':i+1,'source':source})
  except Limit:
   complete=False;limit_reason='fact limit while loading supplied facts';break
 def join(patterns):
  nonlocal operations
  current=[({},[])]
  for row in patterns:
   following=[]
   for bindings,parents in current:
    for ident in list(index.get((row['relation'],row['negated']),[])):
     operations+=1
     if operations>50000 or time.monotonic()>deadline:raise Limit('join/time budget')
     fact=facts[ident-1];updated=dict(bindings);matches=True
     for field in ('subject','object','context'):
      term=row[field];actual=fact[field]
      if variable(term):
       if term in updated and updated[term]!=actual:matches=False;break
       updated[term]=actual
      elif term!=actual:matches=False;break
     if matches:following.append((updated,parents+[ident]))
     if len(following)>=2048:raise Limit('join result limit')
   current=following
   if not current:break
  return current
 if complete:
  try:
   changed=True
   while changed:
    changed=False
    for rule in compiled:
     for bindings,parents in join(rule['if']):
      head={k:bindings.get(v,v) if k!='negated' else v for k,v in rule['then'].items()}
      if add(head,{'kind':'derived','rule':rule['id'],'premise_ids':parents}):changed=True
  except Limit as exc:complete=False;limit_reason=str(exc)
 conflicts=[];conflicted=set()
 for fact in facts:
  if fact['negated']:continue
  opposite={**fact,'negated':True};negative=lookup.get(key(opposite))
  if negative:conflicts.append({'subject':fact['subject'],'relation':fact['relation'],'object':fact['object'],'context':fact['context'],'positive_id':fact['id'],'negative_id':negative});conflicted.update((fact['id'],negative))
 # Allow bounded queries over the facts already retained after saturation stops.
 operations=0;deadline=time.monotonic()+.25;answers=[];seen=set();query_complete=True
 try:matches=join(queries)
 except Limit as exc:matches=[];query_complete=False;limit_reason=limit_reason or str(exc)
 for bindings,parents in matches:
  projection={v:bindings[v] for v in selected};signature=tuple(projection.items())
  if signature in seen:continue
  seen.add(signature);answers.append({'bindings':projection,'supporting_fact_ids':parents})
  if len(answers)>=64:query_complete=False;limit_reason=limit_reason or 'answer limit';break
 counter_support=[]
 if len(queries)==1 and not names:
  opposite={**queries[0],'negated':not queries[0]['negated']};counter=lookup.get(key(opposite))
  if counter:counter_support=[counter]
 opposites={}
 for conflict in conflicts:opposites[conflict['positive_id']]=conflict['negative_id'];opposites[conflict['negative_id']]=conflict['positive_id']
 needed=set();pending=[ident for answer in answers for ident in answer['supporting_fact_ids']]+counter_support
 while pending:
  ident=pending.pop()
  if ident in needed:continue
  needed.add(ident);pending.extend(facts[ident-1]['proof'].get('premise_ids',[]))
  if ident in opposites:pending.append(opposites[ident])
 def has_conflict(parents):
  todo=list(parents);visited=set()
  while todo:
   ident=todo.pop()
   if ident in visited:continue
   visited.add(ident);todo.extend(facts[ident-1]['proof'].get('premise_ids',[]))
  return bool(visited&conflicted)
 for answer in answers:answer['has_conflicted_support']=has_conflict(answer['supporting_fact_ids'])
 counter_conflict=has_conflict(counter_support);affected=counter_conflict or any(a['has_conflicted_support'] for a in answers)
 complete=complete and query_complete
 status='answered' if answers and complete else 'partial-answers' if answers else 'refuted' if counter_support and complete else 'partial-counter-support' if counter_support else 'unknown' if complete else 'incomplete'
 if affected:status='conflicting-support'
 return {'status':status,'answers':answers,'counter_supporting_fact_ids':counter_support,'counter_support_conflicted':counter_conflict,'select':selected,'complete':complete,'limit_reason':limit_reason,'fact_count':len(facts),'derived_fact_count':sum(f['proof']['kind']=='derived' for f in facts),'conflicts':conflicts,'proof_graph':[copy.deepcopy(f) for f in facts if f['id'] in needed],'query':queries,'next_step':'Resolve conflicting supporting claims before relying on affected answers.' if affected else 'Check the source statements and explicit rules behind the answer.' if answers or counter_support else 'Supply the missing relation or rule; absence of support is not a negative fact.','scope':'Relational consequences of supplied statements and range-restricted rules, with explicit contexts and negation. Sources are attributions, not independent verification. Repeated claims are not independent confirmations; unknown relations remain unknown.'}
