"""Native problem framing and grounded follow-ups; no fabricated facts or model calls."""
import copy,hashlib,json,re,time
from decimal import Decimal

FIELDS={'facts':'facts','known':'facts','evidence':'evidence','assume':'assumptions','assumptions':'assumptions','options':'options','constraints':'constraints','criteria':'criteria','priority':'priority','goal':'goal','question':'question','predictions':'predictions','observations':'observations'}

def chunks(value):return [part.strip() for part in re.split(r';|\n',value) if part.strip()]

def natural_logic(text):
 """Translate a narrow, auditable set of sentence forms into explicit logic."""
 from .general_reasoning import parse_logic,atom
 if not re.search(r'\bif\b.+\bthen\b',text,re.I|re.S):return None
 source=re.sub(r'(?<=[\w)])\.\s+','; ',text.strip())
 source=re.sub(r'\bdoes (.+?) follow\?\s*$',r'Query: \1',source,flags=re.I)
 source=re.sub(r'\bcan we conclude (.+?)\?\s*$',r'Query: \1',source,flags=re.I)
 clauses=chunks(source);rewritten=[]
 for clause in clauses:
  clause=re.sub(r"\bisn't\b",'is not',clause,flags=re.I);clause=re.sub(r"\baren't\b",'are not',clause,flags=re.I)
  negative=re.fullmatch(r'(.+?) (is|are) not (.+)',clause,re.I)
  if negative and not re.search(r'\b(and|or|implies|iff|xor|then)\b',clause,re.I) and not clause.lower().startswith(('is ','query:')):
   clause='not '+negative[1]+' '+negative[2]+' '+negative[3]
  rewritten.append(clause)
 body=parse_logic('; '.join(rewritten));names=set()
 def collect(node):
  if isinstance(node,str):names.add(atom(node))
  elif isinstance(node,dict):
   for value in node.values():
    for child in value if isinstance(value,list) else [value]:collect(child)
 for premise in body['premises']:collect(premise)
 alignments=[]
 def align(node):
  if isinstance(node,str):
   name=atom(node)
   if name in names:return name
   matches=[v for v in names if re.sub(r'\b(?:is|are)\s+','',v)==name]
   if len(matches)>1:raise ValueError('The question matches more than one supplied statement; specify the intended statement')
   if matches:alignments.append({'question_phrase':node,'premise_phrase':matches[0]});return matches[0]
   return node
  if isinstance(node,dict):return {key:[align(v) for v in value] if isinstance(value,list) else align(value) for key,value in node.items()}
  return node
 body['query']=align(body['query']);body['phrase_alignment']=alignments;body['source_text']=text;body['interpretation']='Sentence separators, explicit negation and unambiguous is/are question alignment only; no synonym or world-knowledge inference.'
 return body

def kind(question):
 lower=question.casefold()
 if re.search(r'\b(crash|error|broken|fail|debug|not working|won.t open)\b',lower):return 'troubleshooting'
 if re.search(r'\b(choose|choice|should|better|cheaper|cheapest|decide|versus|vs|compare)\b',lower):return 'decision'
 if re.search(r'\b(why|cause|explain|reason for)\b',lower):return 'explanation'
 if re.search(r'\b(plan|how can|how do|how to|build|improve|achieve|create)\b',lower):return 'planning'
 return 'inquiry'

def source_followup(frame,question):
 if not frame or len(question)>500 or not (frame['facts'] or frame['evidence']):return False
 from .source_reasoning import query,statement,universal
 try:patterns,_=query(question)
 except ValueError:return False
 anchors={v.strip().casefold() for p in patterns for k,v in p.items() if k in ('subject','object') and not v.startswith('?')}
 known=set();passage='\n'.join(frame['facts']+frame['evidence'])[:16000]
 for sentence in re.split(r'(?<=[.!?])\s+|\n|;',passage):
  parsed=statement(sentence.strip().rstrip('.')) if sentence.strip() else None
  if parsed:known.update((parsed['subject'].strip().casefold(),parsed['object'].strip().casefold()))
  elif sentence.strip():
   rule=universal(sentence.strip().rstrip('.'),'default')
   if rule:known.update(p['object'].strip().casefold() for p in rule['if']+[rule['then']])
 return bool(anchors) and anchors<=known

def new_frame(text):
 return {'id':hashlib.sha256((text+str(time.time_ns())).encode()).hexdigest()[:20],'question':text.strip(),'goal':'','kind':kind(text),'facts':[],'assumptions':[],'evidence':[],'options':[],'constraints':[],'criteria':[],'priority':'','updates':[],'status':'needs-clarification','waiting_for':None,'created':time.time()}

def put(frame,field,value):
 value=value.strip()
 if field in ('predictions','observations'):frame.setdefault(field,[])
 if not value or len(value)>4000:raise ValueError('Use 1–4000 characters for a reasoning update')
 if isinstance(frame[field],list):
  parts=chunks(value)
  if field=='options':parts=[v.strip() for v in re.split(r';|\n|\s+or\s+',value,flags=re.I) if v.strip()]
  for part in parts:
   if part not in frame[field]:frame[field].append(part)
  if len(frame[field])>16:raise ValueError('Use up to 16 entries in each reasoning field')
 else:frame[field]=value

def cost_data(frame):
 rows=[]
 for source in frame['facts']:
  for part in re.split(r';|\n|(?<=[A-Za-z0-9])\.\s+',source):
   if re.search(r'\b(might|may|could|maybe|perhaps|about|roughly|approximately|estimated|estimate|previously|formerly|not)\b|\bused to\b',part,re.I):continue
   match=re.fullmatch(r'\s*([\w][\w -]{0,60}?)\s+(?:costs?|is priced at)\s*([£$€]?)\s*(\d{1,12}(?:\.\d{1,6})?)\s*(GBP|USD|EUR)?\s*[.]?\s*',part,re.I)
   if not match:continue
   label,symbol,number,unit=match.groups();symbol_unit={'£':'GBP','$':'USD','€':'EUR'}.get(symbol,'')
   unit=(unit or symbol_unit).upper()
   if symbol_unit and unit!=symbol_unit:raise ValueError('A cost has conflicting currency labels')
   rows.append({'option':label.strip(),'amount':number,'unit':unit,'source':source})
 return rows

def analyse(frame,state):
 frame['kind']=kind(frame['question']);rows=cost_data(frame);conflicts=[];seen={}
 from .decision_reasoning import compile_frame,compare
 compiled=compile_frame(frame);frame['decision_model']=None
 if compiled and 'model' in compiled:frame['decision_model']=compiled['model'];decision=compare(compiled['model'])
 else:decision=None
 reading=None;frame['reading_model']=None
 from .diagnostic_reasoning import compile_frame as compile_diagnostic,diagnose
 diagnostic=compile_diagnostic(frame);frame['diagnostic_model']=None
 if diagnostic and 'model' in diagnostic:frame['diagnostic_model']=diagnostic['model'];diagnostic_report=diagnose(diagnostic['model'])
 if frame['evidence'] or frame['facts']:
  from .source_reasoning import query
  from .general_reasoning import reason
  try:
   query(frame['question']);passage='\n'.join(frame['facts']+frame['evidence']);model={'mode':'reading','text':passage[:16000],'source_truncated':len(passage)>16000,'question':frame['question'],'source':'workspace supplied statements'}
   reading=reason(model);frame['reading_model']=model
  except ValueError:pass
 frame['unbounded_request']=bool(re.search(r'\b(?:solve|answer|do) (?:every|all|any) (?:possible )?(?:problem|problems|question|questions|task|tasks)(?: in (?:the )?world| ever| at once)\b',frame['question'],re.I))
 for row in rows:
  key=row['option'].casefold()
  if key in seen and (Decimal(seen[key]['amount'])!=Decimal(row['amount']) or seen[key]['unit']!=row['unit']):conflicts.append(row['option'])
  seen[key]=row
 frame['cost_observations']=rows;frame['conflicts']=sorted(set(conflicts));frame['findings']=[]
 if frame['unbounded_request']:
  frame['waiting_for']='question';question='Which concrete problem should we start with?'
 elif diagnostic and 'clarification' in diagnostic:
  frame['waiting_for']='predictions';question=diagnostic['clarification']
 elif diagnostic:
  frame['findings'].append({'kind':'diagnostic-comparison','report':diagnostic_report,'basis':'Explicit candidate predictions compared with supplied observations.'})
  frame['waiting_for']='observations';question=diagnostic_report['next_step']
 elif reading is not None:
  frame['findings'].append({'kind':'source-answer','report':reading,'basis':'Only the explicitly parsed supplied statements and their proof trails were used.'})
  frame['waiting_for']='evidence';question=reading['next_step']
 elif compiled and 'clarification' in compiled:
  frame['waiting_for']='facts';question=compiled['clarification']
 elif decision is not None:
  frame['findings'].append({'kind':'multi-criteria-comparison','report':decision,'basis':compiled['provenance']})
  frame['waiting_for']='facts' if decision['status']=='needs-evidence' else 'constraints' if decision['status']=='no-feasible-option' else 'priority'
  question=decision['next_step']
 elif conflicts:
  frame['waiting_for']='correction';question='Which stated cost is current for '+', '.join(frame['conflicts'])+'? Use correct fact NUMBER: followed by the replacement.'
 elif rows and (len({r['unit'] for r in rows})>1 or any(not r['unit'] for r in rows)):
  frame['waiting_for']='facts';question='What comparable currency and cost basis should I use? The stated amounts have different or missing units.'
 elif len(seen)>=2 and (re.search(r'\b(cheaper|cheapest|lowest cost|lowest price)\b',frame['question'],re.I) or re.search(r'\b(cost|price|cheaper|cheapest)\b',frame['priority'],re.I)):
  minimum=min(Decimal(r['amount']) for r in seen.values());best=[r for r in seen.values() if Decimal(r['amount'])==minimum]
  frame['findings'].append({'kind':'stated-cost-comparison','lowest_options':[r['option'] for r in best],'amount':str(minimum),'unit':best[0]['unit'],'basis':'Exact decimal comparison of supplied costs only; no other attribute, currency conversion or missing option was inferred.'})
  frame['waiting_for']='constraints';question='Are there requirements or costs missing from that comparison? Cost alone does not compare reliability, timing or suitability.'
 elif frame['kind']=='decision':
  if len(frame['options'])<2 and len(seen)<2:frame['waiting_for']='options';question='Which options are you considering?'
  elif not frame['priority']:frame['waiting_for']='priority';question='What matters most in this decision, and which requirement must every option meet?'
  else:frame['waiting_for']='facts';question='What comparable evidence or measurements do you have for each option on that priority?'
 elif frame['kind']=='troubleshooting':
  if not frame['facts']:frame['waiting_for']='facts';question='What exactly happens, when does it happen, and what error or observation can you provide?'
  elif not frame['evidence']:frame['waiting_for']='evidence';question='What changes between a successful and failing run, or what controlled comparison could you observe?'
  elif not frame['options']:frame['waiting_for']='options';question='Which candidate explanations should we compare against those observations?'
  else:frame['waiting_for']='assumptions';question='What different result would each candidate predict, and which assumptions connect it to the observations?'
 elif frame['kind']=='explanation':
  if not frame['evidence']:frame['waiting_for']='evidence';question='What observations support the explanation, and what alternative could explain the same observations?'
  elif not frame['options']:frame['waiting_for']='options';question='Which alternative explanations fit those observations?'
  else:frame['waiting_for']='assumptions';question='What observation would distinguish those explanations, and which assumptions does each require?'
 elif frame['kind']=='planning':
  if not frame['goal']:frame['waiting_for']='goal';question='What observable result would count as success?'
  elif not frame['constraints']:frame['waiting_for']='constraints';question='What limits or requirements must the plan respect?'
  elif not frame['facts']:frame['waiting_for']='facts';question='What is already available, and which actions have known preconditions and effects?'
  else:frame['waiting_for']='options';question='Which available actions could move from the stated starting conditions toward the goal?'
 else:frame['waiting_for']='evidence';question='What context or source should I use to answer this, and which part is still uncertain?'
 frame['next_question']=question;frame['status']='partial-analysis' if frame['findings'] else 'conflicting-input' if conflicts else 'needs-clarification'
 from .artifact_memory import search
 frame['related_artifacts']=[{k:row.get(k) for k in ('kind','name','status','source','scope')} for row in search(state,frame['question'])[:3]]
 frame['evidence_extracts']=[]
 if frame['evidence']:
  from .conversation_work import summarise
  source='\n'.join(frame['evidence'])[:16000];frame['evidence_extracts']=[row['text'][:1000] for row in summarise(source)['extracts']]
 frame['scope']='Native problem framing and explicit-data checks. Supplied statements remain unverified; assumptions are separate. No general factual answer, diagnosis or real action is fabricated.'
 return frame

def render(frame):
 lines=['**Reasoning workspace**',frame['question']]
 if frame.get('unbounded_request'):lines+=['There is no native procedure that solves every possible problem. We can narrow this to a specific question and check what follows.']
 if frame['goal']:lines+=['','Goal: '+frame['goal']]
 if frame['facts']:lines+=['','Supplied statements:']+[str(i+1)+'. '+v for i,v in enumerate(frame['facts'])]
 if frame['options']:lines+=['','Options: '+ ' / '.join(frame['options'])]
 if frame['priority']:lines+=['Priority: '+frame['priority']]
 if frame['criteria']:lines+=['Criteria: '+ '; '.join(frame['criteria'])]
 if frame['constraints']:lines+=['Requirements: '+ '; '.join(frame['constraints'])]
 if frame['assumptions']:lines+=['','Assumptions, not established facts:']+['- '+v for v in frame['assumptions']]
 if frame['evidence']:lines+=['','Evidence you supplied:']+['- '+v for v in frame['evidence']]
 if frame.get('related_artifacts'):lines+=['','Related saved reasoning or procedures (not executed):']+['- '+r['name']+' · '+r['status'] for r in frame['related_artifacts']]
 for finding in frame['findings']:
  if finding['kind']=='diagnostic-comparison':
   report=finding['report'];lines+=['','Prediction comparison: '+report['status']+'.','Still compatible or unresolved: '+(', '.join(report['remaining']) or 'none')+'.']
   for row in report['hypotheses']:
    if row['mismatches']:lines+=['- '+row['name']+' conflicts with: '+', '.join(row['mismatches'])+'.']
   lines+=[report['scope']]
  if finding['kind']=='stated-cost-comparison':lines+=['','On the supplied cost figures, '+', '.join(finding['lowest_options'])+' has the lowest stated cost: '+finding['amount']+' '+finding['unit']+'.',finding['basis']]
  elif finding['kind']=='multi-criteria-comparison':
   report=finding['report'];lines+=['','Comparison under the declared criteria: '+report['status']+'.','Undominated complete options: '+(', '.join(report['pareto_frontier']) or 'none established')+'.']
   if report['unresolved_options']:lines+=['Still unresolved: '+', '.join(report['unresolved_options'])+'.']
   if report['robust_best_under_declared_criteria']:lines+=['Robustly better within the declared model: '+', '.join(report['robust_best_under_declared_criteria'])+'.']
   lines+=[report['scope']]
  elif finding['kind']=='source-answer':
   report=finding['report'];lines+=['','Answer under the supplied statements: '+report['status']+'.']
   for answer in report['answers']:
    values=list(answer['bindings'].values());lines+=['- '+(', '.join(values) if values else 'The queried statement has explicit support.')+(' Supporting evidence conflicts.' if answer.get('has_conflicted_support') else '')]
   if report.get('counter_supporting_fact_ids'):lines+=['The supplied statements include explicit counter-support.']
   if report.get('explanation_sources'):lines+=['Recorded support:']+['- '+row['source']+': '+row['text'] for row in report['explanation_sources']]
   lines+=[report['scope']]
 lines+=['',frame['next_question']]
 return '\n'.join(lines)

def respond(text,state,fallback=False):
 if not isinstance(text,str) or not text.strip() or len(text)>16000:raise ValueError('Enter a reasoning message of 1–16000 characters')
 lower=text.casefold().strip().rstrip('?.!');current=state.get('open_reasoning');explicit=re.match(r'^(?:open reasoning:|think through:|help me reason about\s+|new reasoning topic:)\s*(.+)',text,re.I|re.S)
 if lower=='resume waiting workflow' and state.get('suspended_pending_input'):
  pending=state.pop('suspended_pending_input');state['pending']=pending
  return {'status':'needs-input','answer':'Waiting for input to the suspended workflow: '+ ' → '.join(s['op'] for s in pending)+'. Send its input next.','steps':copy.deepcopy(pending),'model_calls':0}
 logical_text=explicit[1] if explicit else text
 if (explicit or fallback) and re.match(r'^if\b',logical_text.strip(),re.I):
  try:logical=natural_logic(logical_text)
  except ValueError:logical=None
  if logical is not None:
   from .general_reasoning import reason,retain
   result=reason(logical);retain(state,logical,result);state['focus_kind']='general-reasoning'
   return {'answer':json.dumps(result,ensure_ascii=False,indent=2),'status':result['status'],'general_reasoning':result,'interpretation':logical,'model_calls':0}
 if lower=='cancel open reasoning':
  if current:state['open_reasoning']=None
  return {'answer':'Open reasoning workspace closed. Earlier checked work is retained.','status':'cancelled','model_calls':0}
 if lower in ('open reasoning status','why this question','what can we conclude','what does that imply','why that result','explain that finding','what should we test next','which explanations remain') and current:
  frame=copy.deepcopy(current)
  answer='The next question targets the missing '+str(frame['waiting_for'])+' needed for this '+frame['kind']+'. '+frame['next_question'] if lower=='why this question' else render(frame)+'\n\n'+frame['scope']
  return {'answer':answer,'status':frame['status'],'open_reasoning':frame,'model_calls':0}
 update=re.fullmatch(r'(facts|known|evidence|assume|assumptions|options|constraints|criteria|priority|goal|question|predictions|observations):\s*(.+)',text,re.I|re.S)
 setter=re.fullmatch(r'(?:set|replace) (facts|known|evidence|assume|assumptions|options|constraints|criteria|priority|goal|question|predictions|observations):\s*(.+)',text,re.I|re.S)
 clear=re.fullmatch(r'clear (facts|evidence|assumptions|options|constraints|criteria|predictions|observations)',lower)
 correction=re.fullmatch(r'correct (fact|constraint|criterion|option|assumption|evidence) (\d+):\s*(.+)',text,re.I|re.S)
 followup=not explicit and source_followup(current,text)
 if not explicit and not current and not fallback:return None
 if not explicit and current and not update and not correction and not setter and not clear and not followup and not fallback:return None
 started_new=bool(explicit or not current)
 frame=new_frame(explicit[1] if explicit else text) if started_new else copy.deepcopy(current)
 if explicit:
  parts=re.split(r'\n(?=(?:facts|known|evidence|assume|options|constraints|criteria|priority|goal|question|predictions|observations):)',explicit[1],flags=re.I);frame['question']=parts[0].strip()
  for part in parts[1:]:
   key,_,value=part.partition(':');put(frame,FIELDS[key.casefold()],value)
 elif followup:
  before=frame['question'];frame['question']=text.strip();frame['updates'].append({'kind':'source-followup','before':before,'after':frame['question']})
 elif clear:
  field=clear[1];before=copy.deepcopy(frame.get(field,[]));frame[field]=[];frame['updates'].append({'kind':'explicit-clear','field':field,'before':before,'after':[]})
 elif correction:
  field={'fact':'facts','constraint':'constraints','criterion':'criteria','option':'options','assumption':'assumptions','evidence':'evidence'}[correction[1].casefold()];index=int(correction[2])-1
  if not 0<=index<len(frame[field]):raise ValueError('Choose the number of an existing '+correction[1])
  before=frame[field][index];value=correction[3].strip()
  if len(value)>4000:raise ValueError('Use a replacement below 4000 characters')
  frame[field][index]=value;frame['updates'].append({'kind':'explicit-correction','field':field,'before':before,'after':value})
 elif setter:
  field=FIELDS[setter[1].casefold()];before=copy.deepcopy(frame.get(field,[]));frame[field]=[] if isinstance(before,list) else '';put(frame,field,setter[2]);frame['updates'].append({'kind':'explicit-replacement','field':field,'before':before,'after':copy.deepcopy(frame[field])})
 elif update:put(frame,FIELDS[update[1].casefold()],update[2])
 elif fallback and current:
  if re.match(r'^(?:why|how|what|who|when|where|should|can|could|would|is|are)\b',lower):frame=new_frame(text);started_new=True
  elif frame.get('waiting_for') in ('facts','evidence','options','priority','constraints','goal','assumptions','question'):put(frame,frame['waiting_for'],text)
  else:return {'answer':frame['next_question'],'status':frame['status'],'open_reasoning':frame,'model_calls':0}
 # Cost-bearing sentences in an initial question are quoted as supplied data.
 if started_new:
  for part in re.split(r'(?<=[?])\s+|;|\n|(?<=[A-Za-z0-9])\.\s+',frame['question']):
   if re.fullmatch(r'[\w][\w -]{0,60}?\s+(?:costs?|is priced at)\s*[£$€]?\s*\d{1,12}(?:\.\d{1,6})?\s*(?:GBP|USD|EUR)?[.]?',part.strip(),re.I):put(frame,'facts',part.strip())
 frame['updates']=frame['updates'][-12:];analyse(frame,state)
 if len(json.dumps(frame))>65536:raise ValueError('Reasoning workspace exceeds 64 KB; start a smaller topic')
 if started_new and current:
  history=(state.get('open_reasoning_history',[])+[copy.deepcopy(current)])[-3:]
  while len(history)>1 and len(json.dumps(history))>131072:history.pop(0)
  state['open_reasoning_history']=history
 if started_new and state.get('pending'):state['suspended_pending_input']=copy.deepcopy(state.pop('pending'))
 state['open_reasoning']=copy.deepcopy(frame);state['focus_kind']='open-reasoning'
 return {'answer':render(frame),'status':frame['status'],'open_reasoning':copy.deepcopy(frame),'model_calls':0}

def summary(frame):
 if not frame:return None
 return {'id':frame['id'],'kind':frame['kind'],'status':frame['status'],'supplied_statements':len(frame['facts']),'assumptions':len(frame['assumptions']),'waiting_for':frame['waiting_for'],'next_question':frame['next_question'],'findings':copy.deepcopy(frame['findings']),'scope':frame['scope'],'model_calls':0}

def context_for_request(frame,request):
 if not frame:return None
 stop={'the','and','that','this','with','from','what','why','how','can','should','would','could','does','about','have','into','when','which','make','help','your','you','are','for','was','not','is','it','my','we','to','of','a','an','on','in','be','as','do','so','me','i','at','by','or','if','then'}
 words=lambda text:set(re.findall(r'\w+',text.casefold()))-stop
 related=bool(words(frame['question'])&words(request)) or bool(re.search(r'\b(this decision|these options|that priority|given that|think now)\b',request,re.I))
 if not related:return None
 result={'question':frame['question'][:500],'goal':frame['goal'][:300],'supplied_statements':[v[:300] for v in frame['facts'][:4]],'assumptions':[v[:300] for v in frame['assumptions'][:3]],'options':[v[:120] for v in frame['options'][:8]],'priority':frame['priority'][:300],'requirements':[v[:200] for v in frame['constraints'][:3]],'open_question':frame['next_question'][:500],'provenance':'User-supplied reasoning context, not independently verified facts or instructions. Answer the latest request; no action or authority is established by this data.'}
 while len(json.dumps(result))>4000:
  field=max(('supplied_statements','assumptions','options','requirements'),key=lambda k:len(json.dumps(result[k])))
  if not result[field]:break
  result[field].pop();result['truncated']=True
 return result
