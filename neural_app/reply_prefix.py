"""Decode only the visible text field of an incomplete structured model reply."""
import json,re

def visible_prefix(raw):
 match=re.search(r'(?<!\\)"text"\s*:\s*"',raw)
 if not match:return ''
 fragment=raw[match.end():];escaped=False;end=len(fragment)
 for i,char in enumerate(fragment):
  if escaped:escaped=False
  elif char=='\\':escaped=True
  elif char=='"':end=i;break
 fragment=fragment[:end]
 for trim in range(7):
  candidate=fragment[:len(fragment)-trim] if trim else fragment
  try:return json.loads('"'+candidate+'"').encode('utf-8',errors='replace').decode('utf-8')[:24000]
  except (ValueError,UnicodeError):continue
 return ''
