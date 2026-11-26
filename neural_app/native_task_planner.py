"""Compile explicit natural-language data goals into typed pure workflows."""
import json,re
from .instruction_clauses import split_clauses,partition_input

# Text payload after the first colon is data. It is never parsed as another instruction.
def compile_goal(request):
 raw=request.strip();head,sep,data=partition_input(raw);instruction=head.strip().lower()
 instruction=re.sub(r'^(?:(?:please|can you|could you|would you)\s+)+','',instruction)
 if instruction.startswith(('workflow','learn workflow','use workflow','queue workflow','causal model','compare options','summarise','summarize','remember','write file','read file','powershell','cmd','bat')):return None
 if not re.match(r'^(?:group|add|subtract|multiply|scale|divide|parse|remove|deduplicate|sort|order|count|extract|take|keep|filter|convert|split|join|trim|strip|lowercase|uppercase|reverse|replace|find|calculate|get|make|normalise|normalize)\b',instruction):return None
 if not sep and (instruction.startswith(('calculate ','find ','get ')) or '\n' in raw):return None
 if not sep:return {'status':'needs-input','question':'What data should I use? Put the text, numbers, CSV or JSON after a colon.','missing':['input data'],'executed':False}
 # Single natural compound aggregate over a table.
 aggregate=re.fullmatch(r'(?:get|find|calculate) (?:the )?(average|mean|sum|median|minimum|maximum|count) (?:of )?(?:the )?([a-z_][a-z0-9_]*)(?: (?:for|of) rows)?(?: where ([a-z_][a-z0-9_]*) (is )?(above|below|at least|at most|equal to) (-?\d+(?:\.\d+)?))?',instruction)
 if aggregate:
  op,field,condition,_,relation,threshold=aggregate.groups();steps=[]
  if condition:steps.append({'op':'filter','field':condition,'relation':{'above':'greater','below':'less','at least':'at_least','at most':'at_most','equal to':'equal'}[relation],'value':float(threshold)})
  steps.extend([{'op':'field','name':field},{'op':'numbers'}] if op!='count' else [{'op':'field','name':field}]);steps.append({'op':'mean' if op=='average' else op})
  try:value=json.loads(data)
  except ValueError:return {'status':'needs-input','question':'Provide a JSON array of rows for that field-based request.','executed':False}
  return {'status':'planned','input':value,'steps':steps,'interpretation':instruction}
 clauses=split_clauses(re.sub(r'^(?:(?:please|can you|could you|would you)\s+)+','',head.strip(),flags=re.I))
 steps=[];kind='text';errors=[]
 stripped=data.lstrip()
 if stripped.startswith(('[','{')):
  try:value=json.loads(data);kind='list' if isinstance(value,list) else 'object'
  except ValueError:value=data
 else:
  value=data.lstrip(' \r\n')
  if re.fullmatch(r'-?\d+(?:\.\d+)?',value.strip()) and re.match(r'^(?:add|subtract|multiply|scale|divide)\b',instruction):value=float(value.strip());kind='number'
  if 'numbers' in instruction:
   try:value=[float(v) for v in re.split(r'[,;\s]+',data.strip()) if v];kind='list'
   except ValueError:pass
 def need_list(words=False):
  nonlocal kind
  if kind=='text':steps.append({'op':'words' if words else 'lines'});kind='list'
 def need_text():
  nonlocal kind
  if kind=='list':steps.append({'op':'join'});kind='text'
 for original_clause in clauses:
  clause=original_clause.lower()
  clause=re.sub(r'^(?:please |the result |it |them )','',clause).strip()
  grouping=re.fullmatch(r'group by ([a-zA-Z_][\w-]{0,63}) (count|sum|mean|minimum|maximum)(?: ([a-zA-Z_][\w-]{0,63}))?',original_clause.strip(),re.I)
  if grouping:
   field,aggregate,measure=grouping.groups();aggregate=aggregate.lower()
   if aggregate!='count' and not measure:errors.append(clause);continue
   steps.append({'op':'group','field':field,'aggregate':aggregate,**({'value_field':measure} if measure else {})});kind='list'
  elif clause in ('parse csv','convert csv to json','csv to json'):
   steps.append({'op':'csv'});kind='list'
  elif clause in ('parse json','convert json','as json'):
   steps.append({'op':'json'});kind='list' if data.lstrip().startswith('[') else 'object'
  elif re.fullmatch(r'''replace ["'].*?["'] with ["'].*?["']''',clause):
   replacement=re.fullmatch(r'''replace ["'](.*?)["'] with ["'](.*?)["']''',original_clause.strip(),re.I)
   need_text();steps.append({'op':'replace','old':replacement[1],'new':replacement[2]})
  elif re.fullmatch(r'(?:remove (?:the )?duplicates?(?: lines| words)?|deduplicate(?: lines| words)?)',clause):
   need_list('word' in clause);steps.append({'op':'unique'})
  elif re.fullmatch(r'(?:sort|order)(?: (?:them|it|the result|lines|numbers|alphabetically|ascending|descending|in reverse order))*',clause):
   need_list();steps.append({'op':'sort','descending':any(w in clause for w in ('descending','reverse'))})
  elif re.fullmatch(r'(?:sort|order) (?:rows )?by [a-z_][a-z0-9_]*(?: ascending| descending)?',clause):
   field=re.search(r'by ([a-z_][a-z0-9_]*)',clause)[1];steps.append({'op':'sort','field':field,'descending':clause.endswith('descending')});kind='list'
  elif re.fullmatch(r'(?:split (?:into |by )?(?:lines|words)|extract words)',clause):need_list('word' in clause)
  elif re.fullmatch(r'(?:count(?: (?:the )?(?:unique )?(?:words|lines|items|values))?)',clause):
   need_list('word' in clause)
   if 'unique' in clause:steps.append({'op':'unique'})
   steps.append({'op':'count'});kind='number'
  elif re.fullmatch(r'(?:turn (?:it|them|the result) (?:into |to )?|convert (?:to )?|make (?:it|them) )?(?:upper ?case|lower ?case)',clause):
   need_text();steps.append({'op':'upper' if 'upper' in clause else 'lower'})
  elif re.fullmatch(r'(?:add|subtract|multiply by|scale by|divide by) -?\d+(?:\.\d+)?',clause):
   match=re.fullmatch(r'(add|subtract|multiply by|scale by|divide by) (-?\d+(?:\.\d+)?)',clause);word,number=match.groups();operand=float(number)
   steps.append({'op':'add' if word in ('add','subtract') else 'divide' if word=='divide by' else 'scale','value':-operand if word=='subtract' else operand})
  elif clause in ('reverse','reverse text','reverse it'):need_text();steps.append({'op':'reverse'})
  elif clause in ('trim','strip','trim whitespace','strip whitespace'):need_text();steps.append({'op':'strip'})
  elif re.fullmatch(r'(?:extract|take|get)(?: (?:the )?field)? [a-z_][a-z0-9_]*',clause) and not re.fullmatch(r'get (?:sum|mean|average|median|minimum|maximum)',clause):steps.append({'op':'field','name':clause.split()[-1]});kind='list' if kind=='list' else 'unknown'
  elif re.fullmatch(r'(?:keep|filter)(?: rows| values| numbers)? (?:where )?(?:[a-z_][a-z0-9_]* )?(?:is )?(?:above|below|at least|at most|equal to) -?\d+(?:\.\d+)?',clause):
   match=re.search(r'(?:(?P<field>[a-z_][a-z0-9_]*) (?:is )?)?(?P<rel>above|below|at least|at most|equal to) (?P<n>-?\d+(?:\.\d+)?)$',clause);field=match['field'];field=None if field in ('values','numbers','where','rows') else field
   need_list();step={'op':'filter','relation':{'above':'greater','below':'less','at least':'at_least','at most':'at_most','equal to':'equal'}[match['rel']],'value':float(match['n'])}
   if field:step['field']=field
   steps.append(step)
  elif re.fullmatch(r'(?:take|keep) (?:the )?first \d+(?: items| rows| values| lines)?',clause):need_list();steps.append({'op':'take','count':int(re.search(r'\d+',clause)[0])})
  elif clause in ('convert to numbers','as numbers','numbers'):need_list();steps.append({'op':'numbers'})
  elif clause in ('join','join lines','join them','join with newlines'):need_list();steps.append({'op':'join'});kind='text'
  elif re.fullmatch(r'(?:find |calculate |get )?(?:the )?(sum|mean|average|median|minimum|maximum)',clause):need_list();steps.extend([{'op':'numbers'},{'op':'mean' if 'average' in clause else clause.split()[-1]}]);kind='number'
  else:errors.append(clause)
 if errors:return {'status':'needs-input','question':'Which operation do you intend for: '+', '.join(errors)+'?','unrecognised_steps':errors,'executed':False}
 if not steps:return None
 if kind=='list' and isinstance(value,str):steps.append({'op':'join'})
 return {'status':'planned','input':value,'steps':steps,'interpretation':instruction}

