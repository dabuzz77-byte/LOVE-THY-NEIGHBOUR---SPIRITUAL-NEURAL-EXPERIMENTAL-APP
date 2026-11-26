"""Small transparent command grammar, shared by work interface and trainer."""
import re
def canonical_request(text,aliases=None):
 original=str(text).lstrip();known=(aliases or {}).get(original.lower()) if '\n' not in original else None
 if known:return known
 value=original
 correction=re.fullmatch(r'(?:actually[,:]?|correction:|no,? I meant)\s+((?:calculate|compute|statistics|uppercase|lowercase|reverse text)\s+[\s\S]+)',value,re.I)
 if correction:value=correction[1]
 if ':' in value and not value.lower().startswith(('powershell:','cmd:','bat:')):
  instruction,payload=value.split(':',1)
  for _ in range(3):instruction=re.sub(r'^(?:please\s+|could you\s+|can you\s+|would you\s+)','',instruction,flags=re.I)
  return instruction+':'+payload
 if not value.lower().startswith('write file '):
  for _ in range(3):value=re.sub(r'^(?:please\s+|could you\s+|can you\s+|would you\s+)', '',value,flags=re.I)
  prefix=re.match(r'^(calcluate|calcualte|statistcs|upppercase|lowecase|analzye|anlayze)(\s+)([\s\S]*)$',value,re.I)
  if prefix:value={'calcluate':'calculate','calcualte':'calculate','statistcs':'statistics','upppercase':'uppercase','lowecase':'lowercase','analzye':'analyze','anlayze':'analyze'}[prefix[1].lower()]+prefix[2]+prefix[3]
  if not value.lower().startswith(('write file ','read file ','analyze ','analyse ','examine ','inspect text ','run pipeline:','remember ','recall ','edit file ','plan:','powershell:','cmd:','bat:','sort lines\n','unique lines\n','count words ','format json ','calculate ','compute ','reverse text ','uppercase ','lowercase ','normalise whitespace ','normalize whitespace ','statistics ','text statistics ','csv to json\n','json to csv ','research ','find sources ','search memory ','compare sources ','workflow:','causal model:','learn workflow:','use workflow:','queue workflow:','summarise:','summarize:','compare options:','reason:','reason from:','summarise this:','summarize this:','count unique words:','count words:','sort and deduplicate:','deduplicate and sort:','reverse and uppercase:')):value=re.sub(r'\?+$','',value).strip()
 exact={'show me my files':'list files','what can you help me with':'what can you do','what can you help with':'what can you do','resume plan':'continue plan','continue working':'continue plan','pause the plan':'pause plan','show the last result':'explain last result','last result':'explain last result','show status':'status','show me status':'status','tell me what is happening':'status','show my files':'list files','show workspace files':'list files','list workspace files':'list files','show learned procedures':'what did you learn?','what did you learn':'what did you learn?','what do you remember':'what do you remember?','what are you doing':'what are you doing?'}
 value=exact.get(value.lower(),value)
 # Only documented command-prefix misspellings change; payload/code stays literal.
 typo=re.match(r'^(calcluate|calcualte|statistcs|upppercase|lowecase|analzye|anlayze)(\s+)([\s\S]*)$',value,re.I)
 if typo:value={'calcluate':'calculate','calcualte':'calculate','statistcs':'statistics','upppercase':'uppercase','lowecase':'lowercase','analzye':'analyze','anlayze':'analyze'}[typo[1].lower()]+typo[2]+typo[3]
 value=re.sub(r'^(?:examine|inspect text)\s+', 'analyze ',value,flags=re.I)
 return value
