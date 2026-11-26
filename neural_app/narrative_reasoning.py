"""Source-traced event reasoning over fully parsed, ordered short narratives.

The state model is shared by movement, possession, handover, containment and
history queries. It never reads answers or task identities from evaluation data.
"""
import re

LABEL=r"[\w][\w'’ -]{0,70}?"
COUNT='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()

def label(text):
 value=re.sub(r'^(?:the|a|an)\s+','',text.strip(),flags=re.I)
 if not re.fullmatch(LABEL,value) or re.search(r'\b(?:he|she|they|it|him|her|them|there|someone|somewhere)\b',value,re.I):raise ValueError('Name the person, object or place explicitly instead of an unresolved reference.')
 return value.casefold(),value

def question(text):
 forms=[('before',r'where was (.+?) (?:just |immediately )?before (.+?)\?'),('location',r'where (?:is|are) (.+?)\?'),('count',r'how many objects is (.+?) carrying\?'),('inventory',r'what is (.+?) carrying\?'),('holder',r'who (?:has|is carrying) (.+?)\?'),('received',r'who received (.+?)\?'),('recipient',r'who did (.+?) give (.+?) to\?'),('gave',r'who gave (.+?) to (.+?)\?'),('giver',r'who gave (.+?)\?'),('object',r'what did (.+?) give to (.+?)\?')]
 for kind,pattern in forms:
  match=re.fullmatch(pattern,text.strip(),re.I)
  if match:return kind,match.groups()
 return None

def clause(text):
 source=re.sub(r'^(?:then|next|afterwards|after that|finally)[, ]+','',text.strip(),flags=re.I)
 forms=[
  ('move',r'(.+?) (?:moved|went|journeyed|travelled|traveled|walked|returned)(?: back)? to (.+?)'),
  ('place',r'(.+?) (?:is|was) (?:in|at|inside) (.+?)'),
  ('take',r'(.+?) (?:picked up|got|took|grabbed|collected) (.+?)(?: there)?'),
  ('drop',r'(.+?) (?:dropped|left|discarded|put down) (.+?)(?: there)?'),
  ('give',r'(.+?) (?:gave|handed|passed) (.+?) to (.+?)'),
  ('put',r'(.+?) put (.+?) (?:in|inside) (.+?)'),
 ]
 for kind,pattern in forms:
  match=re.fullmatch(pattern,source,re.I)
  if match:return kind,[label(x) for x in match.groups()]
 raise ValueError('This clause was not fully understood: “'+text[:160]+'”. Restate it as an explicit move, location, pickup, drop, placement or handover.')

def solve(text,make_result):
 source=re.sub(r'^(?:story|reason about the story):\s*','',text.strip(),flags=re.I)
 match=re.fullmatch(r'([\s\S]+[.;\n])\s*([^.;\n]+\?)\s*',source)
 if not match:return None
 query=question(match[2])
 if query is None:return None
 statements=[s.strip() for s in re.split(r'[.;\n]+',match[1]) if s.strip()]
 if not statements:return None
 # Ordinary open questions without a recognisable story stay with other routes.
 if not re.search(r'\b(?:moved|went|journeyed|travelled|traveled|walked|returned|picked up|got|took|grabbed|collected|dropped|left|discarded|gave|handed|passed|put|is in|is at|was in|is inside)\b',statements[0],re.I):return None
 scope='Ordered-story inference only: sentences are replayed in supplied order. Inventory answers enumerate only explicitly tracked objects, not unmentioned possessions. Historical “before” refers to the most recent stated visit. This does not predict real-world behaviour.'
 def stopped(message,status='needs-clarification',evidence=None):return {'status':status,'answer':message,'reasoning_family':'narrative-state','source_request':text,'evidence':evidence or {},'model_calls':0,'scope':scope}
 if len(statements)>160:return stopped('Split the story into at most 160 statements.')
 try:
  events=[clause(s) for s in statements];kind,arguments=query;arguments=[label(a)[0] for a in arguments]
 except ValueError as exc:return stopped(str(exc))
 names={};parents={};places=set();history={};transfers=[];trace=[]
 def location(entity):
  proof=[];seen=set();current=entity
  while current in parents:
   if current in seen:raise ValueError('The supplied containment relationships form a cycle.')
   seen.add(current);edge=parents[current];proof.extend([edge['event'],*edge.get('dependencies',[])]);current=edge['parent']
  return (current,sorted(set(proof))) if current in places else (None,sorted(set(proof)))
 def snapshot(number):
  for entity in names:
   place,proof=location(entity)
   records=history.setdefault(entity,[])
   if not records or records[-1]['place']!=place:records.append({'place':place,'event':number,'proof':proof})
 try:
  for i,((operation,terms),sentence) in enumerate(zip(events,statements),1):
   for ident,display in terms:names.setdefault(ident,display)
   ids=[v[0] for v in terms];actor=ids[0];changed=[]
   if operation in ('move','place'):
    destination=ids[1]
    if actor==destination:raise ValueError('An entity cannot be placed inside itself.')
    places.add(destination);parents[actor]={'parent':destination,'kind':'location','event':i};changed=[actor]
   elif operation=='take':
    obj=ids[1];old=parents.get(obj)
    if obj==actor:raise ValueError('A person cannot pick themselves up in this model.')
    if old and old['kind']=='holding' and old['parent']!=actor:raise ValueError('The pickup conflicts with the recorded holder; state the handover or drop first.')
    parents[obj]={'parent':actor,'kind':'holding','event':i};changed=[obj]
   elif operation=='drop':
    obj=ids[1];old=parents.get(obj)
    if not old or old['kind']!='holding' or old['parent']!=actor:raise ValueError('A drop requires the stated person to hold that object; provide the missing pickup or handover.')
    place,dependencies=location(actor)
    if place:parents[obj]={'parent':place,'kind':'location','event':i,'dependencies':sorted(set([old['event'],*dependencies]))}
    else:parents.pop(obj,None)
    changed=[obj]
   elif operation=='give':
    obj,recipient=ids[1:];old=parents.get(obj)
    if obj==recipient or actor==recipient:raise ValueError('Clarify the self-handover; it is not represented as a new transfer.')
    if not old or old['kind']!='holding' or old['parent']!=actor:raise ValueError('The handover requires its giver to hold the object; provide that missing fact.')
    parents[obj]={'parent':recipient,'kind':'holding','event':i};transfers.append({'giver':actor,'object':obj,'recipient':recipient,'event':i});changed=[obj]
   elif operation=='put':
    obj,destination=ids[1:];old=parents.get(obj)
    if not old or old['kind']!='holding' or old['parent']!=actor:raise ValueError('Placement requires the stated person to hold the object first.')
    if obj==destination:raise ValueError('An object cannot contain itself.')
    places.add(destination);parents[obj]={'parent':destination,'kind':'location','event':i};changed=[obj]
   snapshot(i);trace.append({'event':i,'source':sentence,'operation':operation,'changed_entities':changed})
 except ValueError as exc:return stopped(str(exc),'inconsistent-story',{'parsed_events':trace})
 selected=[];support=[];raw=None
 if kind=='location':
  place,support=location(arguments[0]);raw=names.get(place,place) if place else None
 elif kind=='before':
  entity,place=arguments;records=history.get(entity,[]);matches=[i for i,r in enumerate(records) if r['place']==place]
  if matches:
   pos=matches[-1]
   if pos>0 and records[pos-1]['place']:
    raw=names.get(records[pos-1]['place'],records[pos-1]['place']);support=records[pos-1]['proof']+records[pos]['proof']
 elif kind in ('inventory','count'):
  selected=sorted(obj for obj,edge in parents.items() if edge['kind']=='holding' and edge['parent']==arguments[0]);support=[edge['event'] for obj,edge in parents.items() if obj in selected]
  # Retain relevant drops/transfers too: they explain absence from a known set.
  support+= [r['event'] for r in trace if any(arguments[0]==t[0] for t in events[r['event']-1][1])]
  if arguments[0] not in names:return stopped('That person has no stated events. Supply their inventory or actions before asking for a count.')
  raw=(('none' if not selected else COUNT[len(selected)]) if len(selected)<len(COUNT) else str(len(selected))) if kind=='count' else ','.join(names[x] for x in selected) or 'nothing'
 elif kind=='holder':
  edge=parents.get(arguments[0]);raw=names[edge['parent']] if edge and edge['kind']=='holding' else None;support=[edge['event']] if raw else []
 else:
  candidates=[t for t in transfers if (kind in ('received','giver') and t['object']==arguments[0]) or (kind=='recipient' and t['giver']==arguments[0] and t['object']==arguments[1]) or (kind=='gave' and t['object']==arguments[0] and t['recipient']==arguments[1]) or (kind=='object' and t['giver']==arguments[0] and t['recipient']==arguments[1])]
  if candidates:
   last=candidates[-1];field={'received':'recipient','recipient':'recipient','giver':'giver','gave':'giver','object':'object'}[kind];raw=names[last[field]];support=[last['event']]
 if raw is None:return stopped('The story does not supply enough information to answer that question. State the missing location, holder or earlier event.','insufficient-information',{'query':query,'events':trace})
 evidence={'question':match[2],'answer_basis':'explicit-story-state','supporting_events':[trace[i-1] for i in sorted(set(support))],'events_processed':len(trace),'state':parents,'history':{name:history[name] for name in arguments if name in history},'tracked_inventory':selected if kind in ('count','inventory') else None,'count_value':len(selected) if kind=='count' else None}
 result=make_result('narrative-state',raw,evidence,scope)
 result.update(story_statements=statements,story_question=match[2])
 result['answer']=raw+'\n\nSupporting story steps:\n'+'\n'.join(str(r['event'])+'. '+r['source'] for r in evidence['supporting_events'])+'\n\n'+scope
 return result

def followup(text,previous,make_result):
 """Reuse only the currently focused, explicitly retained story."""
 if not previous or previous.get('reasoning_family')!='narrative-state' or not previous.get('story_statements'):return None
 statements=list(previous['story_statements']);new_question=previous.get('story_question');revision=None;value=text.strip()
 if question(value):new_question=value
 elif re.match(r'^(?:then|next|afterwards|after that|finally)[, ]+',value,re.I):
  match=re.fullmatch(r'([\s\S]+[.;\n])\s*([^.;\n]+\?)',value)
  if not match or not question(match[2]):return None
  statements.extend(s.strip() for s in re.split(r'[.;\n]+',match[1]) if s.strip());new_question=match[2]
 else:
  match=re.fullmatch(r'(?:replace|correct) story step (\d+):\s*(.+?)\.?',value,re.I)
  if not match:return None
  index=int(match[1])-1
  if not 0<=index<len(statements):return {**{k:v for k,v in previous.items() if k!='final_answer'},'status':'needs-clarification','answer':'Choose an existing story step from 1 to '+str(len(statements))+'. The previous story is retained.','model_calls':0}
  revision={'step':index+1,'before':statements[index],'after':match[2]};statements[index]=match[2]
 combined='. '.join(s.rstrip('.') for s in statements)+'. '+new_question
 result=solve(combined,make_result)
 if result is None:return None
 if result['status']!='answered':
  result['story_statements']=previous['story_statements'];result['story_question']=previous['story_question'];result['answer']+=' The previous valid story is retained; this change was not applied.'
 elif revision:result['story_revisions']=(previous.get('story_revisions',[])+[revision])[-8:]
 result['context_source']='explicitly-retained-story';return result
