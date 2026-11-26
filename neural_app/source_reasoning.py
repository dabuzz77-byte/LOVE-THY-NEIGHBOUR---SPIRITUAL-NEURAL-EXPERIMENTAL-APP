"""Auditable narrow-language reading over provided passages, not a general parser."""
import re
from .relational_reasoning import solve,text as label

ALIASES={word:base for base,words in {'leads':('lead','leads'),'uses':('use','uses'),'contains':('contain','contains'),'owns':('own','owns'),'requires':('require','requires'),'produces':('produce','produces'),'supports':('support','supports'),'reports':('report','reports')}.items() for word in words}
VERBS='|'.join(sorted(ALIASES,key=len,reverse=True))

def statement(sentence):
 if re.match(r'^(all|every|some|none|no)\b',sentence,re.I) or re.search(r'\b(may|might|maybe|could|perhaps|apparently|reportedly|probably|possibly|formerly|because|unless|although|while|except|but|can|would|should|must|will)\b|\b(no longer|used to|according to|has to|have to)\b',sentence,re.I):return None
 match=re.fullmatch(r'(.+?) (?:is|are) (not )?(based|located) in (.+)',sentence,re.I)
 if match:
  subject,negated,relation,obj=match.groups();return {'subject':subject,'relation':relation.lower()+'_in','object':obj,'negated':bool(negated)}
 match=re.fullmatch(r'(.+?) (?:is|are) (not )?(?:a|an) (.+)',sentence,re.I)
 if match:
  subject,negated,obj=match.groups();return {'subject':subject,'relation':'is_a','object':obj,'negated':bool(negated)}
 match=re.fullmatch(r'(.+?) does (not )?('+VERBS+r') (.+)',sentence,re.I)
 if match:subject,negated,verb,obj=match.groups()
 else:
  match=re.fullmatch(r'(.+?) ('+VERBS+r') (.+)',sentence,re.I)
  if not match:return None
  subject,verb,obj=match.groups();negated=False
 if re.search(r'\b(not|all|some|none|every|does|did|will)\b',subject,re.I) or re.search(r'\b(?:and|or)\s+(?:'+VERBS+r')\b',obj,re.I):return None
 return {'subject':subject,'relation':ALIASES[verb.lower()],'object':obj,'negated':bool(negated)}

def query(question):
 text=question.strip().rstrip('?.')
 if re.match(r'^why (does|is)\b',text,re.I):return query(re.sub(r'^why\s+','',text,flags=re.I))
 match=re.fullmatch(r'does (.+?) (not )?('+VERBS+r') (.+)',text,re.I)
 if match:return [{'subject':match[1],'relation':ALIASES[match[3].lower()],'object':match[4],'negated':bool(match[2])}],[]
 match=re.fullmatch(r'(?:who|what) ('+VERBS+r') (.+?) and ('+VERBS+r') (.+)',text,re.I)
 if match:return [{'subject':'?answer','relation':ALIASES[match[1].lower()],'object':match[2]},{'subject':'?answer','relation':ALIASES[match[3].lower()],'object':match[4]}],['?answer']
 match=re.fullmatch(r'what is (.+)',text,re.I)
 if match:return [{'subject':match[1],'relation':'is_a','object':'?answer'}],['?answer']
 match=re.fullmatch(r'where is the (.+?) that (.+?) (leads|uses|owns) (based|located)',text,re.I)
 if match:
  category,actor,verb,location=match.groups()
  return [{'subject':actor,'relation':ALIASES[verb.lower()],'object':'?entity'},{'subject':'?entity','relation':'is_a','object':category},{'subject':'?entity','relation':location.lower()+'_in','object':'?answer'}],['?answer']
 match=re.fullmatch(r'where is (.+?) (based|located)',text,re.I)
 if match:return [{'subject':match[1],'relation':match[2].lower()+'_in','object':'?answer'}],['?answer']
 match=re.fullmatch(r'(?:who|what) does (.+?) (not )?('+VERBS+r')',text,re.I)
 if match:return [{'subject':match[1],'relation':ALIASES[match[3].lower()],'object':'?answer','negated':bool(match[2])}],['?answer']
 match=re.fullmatch(r'(?:who|what) ('+VERBS+r') (.+)',text,re.I)
 if match:return [{'subject':'?answer','relation':ALIASES[match[1].lower()],'object':match[2]}],['?answer']
 match=re.fullmatch(r'who is (not )?(?:a|an) (.+)',text,re.I)
 if match:return [{'subject':'?answer','relation':'is_a','object':match[2],'negated':bool(match[1])}],['?answer']
 match=re.fullmatch(r'is (.+?) (not )?(?:a|an) (.+)',text,re.I)
 if match:return [{'subject':match[1],'relation':'is_a','object':match[3],'negated':bool(match[2])}],[]
 raise ValueError('Specify a supported source question or provide explicit relation patterns; ambiguous wording is not guessed')

def universal(sentence,context):
 """Every CATEGORY ...; exact category labels, with no plural/synonym guessing."""
 match=re.fullmatch(r'every ([\w -]{1,70}?) ((?:is|does|'+VERBS+r') .+)',sentence,re.I)
 if not match or re.search(r'\b(and|or|who|that|which|not|every|some|all)\b',match[1],re.I):return None
 head=statement('_member '+match[2])
 if not head or re.search(r'\b(and|or|who|that|which)\b',head['object'],re.I):return None
 return {'if':[{'subject':'?entity','relation':'is_a','object':match[1],'context':context}],'then':{**head,'subject':'?entity','context':context}}

def read(body):
 question=body.get('question');context=label(body.get('context','default'))
 if not isinstance(question,str) or not question.strip() or len(question)>500:raise ValueError('Provide a question up to 500 characters')
 if 'sources' in body and 'text' in body:raise ValueError('Provide either text or sources, not both')
 sources=body.get('sources',[{'source':body.get('source','supplied passage'),'text':body.get('text'),'context':body.get('context','default')}])
 if not isinstance(sources,list) or not 1<=len(sources)<=16:raise ValueError('Provide 1–16 attributed sources')
 facts=[];rules=[];unparsed=[];mapping=[];rule_mapping=[];names=set();length=count=0
 for entry in sources:
  if not isinstance(entry,dict):raise ValueError('Each source needs text and a distinct source label')
  passage=entry.get('text');source=entry.get('source');source_context=label(entry.get('context','default'))
  if not isinstance(passage,str) or not passage.strip() or not isinstance(source,str) or not source.strip() or len(source)>120 or source.casefold().strip() in names:raise ValueError('Use nonempty text and distinct source labels up to 120 characters')
  names.add(source.casefold().strip());length+=len(passage)
  sentences=[v.strip().rstrip('.') for v in re.split(r'(?<=[.!?])\s+|\n|;',passage) if v.strip()];count+=len(sentences)
  if length>16000 or count>128:raise ValueError('Use at most 16000 characters and 128 sentences across all sources')
  for i,sentence in enumerate(sentences):
   source_id=source+' · sentence '+str(i+1);rule=universal(sentence,source_context)
   if rule:
    rules.append(rule);rule_mapping.append({'rule':len(rules),'source':source_id,'text':sentence,'interpretation':rule});continue
   fact=statement(sentence)
   if fact is None:unparsed.append({'source':source,'sentence':i+1,'text':sentence});continue
   fact={**fact,'context':source_context};facts.append({**fact,'source':source_id});mapping.append({'source':source_id,'text':sentence,'interpretation':fact})
 if len(rules)>16:raise ValueError('Use up to 16 explicit universal rules')
 try:patterns,selected=query(question)
 except ValueError as exc:return {'status':'needs-clarification','question':question,'answers':[],'complete':False,'source_statements':mapping,'source_rules':rule_mapping,'unparsed_sentences':unparsed,'next_step':str(exc),'scope':'No answer was inferred from an unsupported question. Use explicit relation patterns for broader syntax.'}
 patterns=[{**p,'context':context} for p in patterns]
 result=solve({'facts':facts,'rules':rules,'query':patterns,'select':selected})
 if unparsed or body.get('source_truncated') is True:
  result.update(complete=False,status='partial-source' if result['answers'] or result['counter_supporting_fact_ids'] else 'needs-source-clarification',next_step='Clarify the unparsed source sentences before treating this as a complete source answer.')
  if body.get('source_truncated') is True:result['next_step']='The supplied source was truncated; provide a shorter complete passage before treating this as a complete answer.'
 explanation=[]
 if question.casefold().startswith('why '):
  proof=result['proof_graph'];used_sources={s['source'] for row in proof for s in row.get('given_sources',[])};used_rules={row['proof']['rule'] for row in proof if row['proof']['kind']=='derived'}
  explanation=[{'source':row['source'],'text':row['text']} for row in mapping if row['source'] in used_sources]+[{'source':row['source'],'text':row['text']} for row in rule_mapping if row['rule'] in used_rules]
 return {**result,'question':question,'explanation_sources':explanation,'source_statements':mapping,'source_rules':rule_mapping,'source_count':len(sources),'query_context':context,'unparsed_sentences':unparsed,'source_truncated':body.get('source_truncated') is True,'scope':'Answer under explicitly parsed supplied sources and their universal rules only; attribution is not external verification. Exact category labels and contexts, no synonym guessing or knowledge invented from missing text. Unparsed or truncated source keeps the review incomplete.'}
