"""Separate workflow clauses without interpreting quoted data as instructions."""
import re

def partition_input(text):
 """Locate the input separator outside literal instruction strings."""
 quote=None;escaped=False
 for i,char in enumerate(text):
  if escaped:escaped=False;continue
  if quote:
   if char=='\\':escaped=True
   elif char==quote:quote=None
  elif char in ('"',"'"):quote=char
  elif char==':':return text[:i],':',text[i+1:]
 return text,'',''

def split_clauses(text):
 parts=[];start=0;quote=None;escaped=False;i=0
 while i<len(text):
  char=text[i]
  if escaped:escaped=False;i+=1;continue
  if quote:
   if char=='\\':escaped=True
   elif char==quote:quote=None
   i+=1;continue
  if char in ('"',"'"):quote=char;i+=1;continue
  match=re.match(r',\s*(?:then\s+)?|\s+(?:and\s+then|then|and)\s+',text[i:],re.I)
  if match:
   parts.append(text[start:i].strip());i+=match.end();start=i
  else:i+=1
 if quote:raise ValueError('Close the quoted text before continuing the instruction')
 parts.append(text[start:].strip())
 if any(not part for part in parts):raise ValueError('An operation is missing between instruction separators')
 return parts
