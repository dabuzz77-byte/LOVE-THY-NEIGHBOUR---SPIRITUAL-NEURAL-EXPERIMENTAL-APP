"""Small explicit conversational name claims; no hidden history or host actions."""
import re

CLAIM=re.compile(r'^(?:(?:actually|correction)[,:]?\s+)?my ([\w -]{1,60}?) (?:is named|is called) ([^\n.!?]{1,120})(?:[.!?]|$)',re.I)

def claim(text):
 match=CLAIM.match(str(text).strip())
 if not match:return None
 label=' '.join(match[1].casefold().split());name=match[2].strip()
 if re.search(r'password|secret|token|key|account|pin\b',label,re.I):return None
 return label,name

def respond(text,history,state=None):
 current=claim(text)
 if current:
  label,name=current
  if state is not None:
   from .memory_revisions import update
   update(state,label+' name',name)
  return {'answer':'Understood—your '+label+' is named '+name+'.','context_claim':{'label':label,'value':name,'provenance':'explicit user report'},'model_calls':0,'action_repeated':False}
 query=re.fullmatch(r'(?:what is (?:the name of )?my ([\w -]{1,60}?)|what (?:did I name|is the name I gave) my ([\w -]{1,60}?))\??(?:\s+(?:give|answer|reply)[\s\S]*)?',str(text).strip(),re.I)
 if not query:return None
 label=' '.join((query[1] or query[2]).casefold().split())
 if label.endswith(' name'):label=label[:-5]
 if state is not None:
  for key,row in state.get('memories',{}).items():
   if key.casefold()==label+' name':return {'answer':row['value'],'provenance':'retained explicit user report','model_calls':0,'action_repeated':False}
 for row in reversed(history[-20:] if state is None else []):
  remembered=claim(row.get('request',''))
  if remembered and remembered[0]==label:return {'answer':remembered[1],'provenance':'explicit user report in this conversation','source_request':row['request'],'model_calls':0,'action_repeated':False}
 explicit_name=bool(re.search(r'\bname\b|\bdid I name\b',str(text),re.I))
 return {'answer':'I do not have a recorded name for your '+label+'. What should I remember?','found':False,'model_calls':0,'action_repeated':False} if state is not None and explicit_name else None

def conversational_only(text):
 value=str(text).strip()
 return bool(claim(value) or re.match(r'^(?:explain|describe|discuss|why\b|what\b|which\b|who\b|when\b|where\b|how\b|is\b|are\b|does\b|do\b|tell me about\b|in (?:one|two|three) (?:short )?sentences\b)',value,re.I))
