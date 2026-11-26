"""Source-linked finite table questions with exact aggregate arithmetic."""
import copy,json,re
from fractions import Fraction

def conversational_query(text):
 value=text.strip().rstrip('?.!');missing='error'
 if re.search(r',?\s+excluding missing values$',value,re.I):
  value=re.sub(r',?\s+excluding missing values$','',value,flags=re.I);missing='exclude'
 match=re.fullmatch(r'what is the (total|sum|average|mean|minimum|maximum) of ([A-Za-z_][\w-]{0,63})(?: where ([A-Za-z_][\w-]{0,63}) equals (.+))?',value,re.I)
 count=re.fullmatch(r'how many rows (?:are there )?where ([A-Za-z_][\w-]{0,63}) equals (.+)',value,re.I)
 if not match and not count:return None
 if match:
  query={'select':{'total':'sum','average':'mean'}.get(match[1].casefold(),match[1].casefold()),'field':match[2],'missing':missing};field,literal=match[3],match[4]
 else:query={'select':'count'};field,literal=count[1],count[2]
 if field:
  try:expected=json.loads(literal)
  except ValueError:return None
  if type(expected) not in (str,int,float,bool,type(None)):return None
  query['where']={'field':field,'equals':expected}
 return query

def respond(text,work):
 key=text.strip().casefold().rstrip('?.!');state=work.state
 if key.startswith('study table:'):
  rows=json.loads(text.split(':',1)[1])
  if not isinstance(rows,list) or not 1<=len(rows)<=1000 or any(not isinstance(r,dict) or len(r)>32 or any(not isinstance(k,str) or not 1<=len(k)<=80 for k in r) for r in rows) or len(json.dumps(rows,allow_nan=False))>65536:raise ValueError('Supply 1–1000 JSON object rows within 64 KB, with up to 32 named columns per row')
  if any(any(type(v) not in (str,int,float,bool,type(None)) for v in r.values()) for r in rows):raise ValueError('Table cells must be scalar JSON values')
  from .native_work import digest
  table={'rows':copy.deepcopy(rows),'source_sha256':digest(rows),'columns':sorted({k for r in rows for k in r})}
  state['study_table']=table;state.pop('table_result',None);state['focus_kind']='table'
  return {'status':'complete','answer':'Retained '+str(len(rows))+' rows. Columns: '+', '.join(table['columns'])+'. Ask how many rows are there, or what is the total of COLUMN.','table_source_sha256':table['source_sha256'],'model_calls':0}
 table=state.get('study_table')
 natural=re.fullmatch(r'what is the (total|mean|minimum|maximum) of (.+)',text.strip().rstrip('?.!'),re.I)
 conversational=conversational_query(text)
 active=state.get('focus_kind')=='table'
 special=key in ('how many rows are there','which columns are available','show table sources','explain this table result','write python for table query','write exact python for table query')
 if not key.startswith('table query:') and not (active and (natural or conversational or special)):return None
 if not table:return {'status':'needs-input','answer':'Supply study table: followed by JSON object rows first.','model_calls':0}
 from .native_work import digest
 if digest(table['rows'])!=table['source_sha256']:raise ValueError('Retained table differs from its source receipt; supply it again')
 if key=='write exact python for table query':
  previous=state.get('table_result')
  if not previous:return {'status':'needs-input','answer':'Complete a table query first.','model_calls':0}
  if previous.get('receipt_sha256')!=digest({k:v for k,v in previous.items() if k!='receipt_sha256'}):raise ValueError('Retained query result changed; ask the query again')
  from .exact_table_export import export
  code=export(table,previous)
  return {'status':'complete','answer':'```python\n'+code['source']+'```\n\nCall query_table(code_input, query_input) with the full table. '+code['scope'],'code':code,'code_input':code['code_input'],'query_input':code['query_input'],'model_calls':0}
 if key=='write python for table query':
  previous=state.get('table_result')
  if not previous:return {'status':'needs-input','answer':'Complete a table query first.','model_calls':0}
  import types
  trial=types.SimpleNamespace(state=copy.deepcopy(state));checked=respond('table query: '+json.dumps(previous['query']),trial)['table_result']
  if checked!=previous:raise ValueError('Retained query result changed; ask the query again')
  query=previous['query'];rows=[copy.deepcopy(table['rows'][i-1]) for i in previous['source_rows']]
  if query['select']=='count':steps=[{'op':'count'}];expected=len(rows)
  elif query['select']=='sum' and all(type(row[query['field']]) is int for row in rows):steps=[{'op':'field','name':query['field']},{'op':'sum'}];expected=int(previous['exact_result'])
  else:raise ValueError('Table code export currently supports row counts and integer sums; exact fractional queries remain available natively')
  from .native_work import python_export
  exported=python_export(steps,rows,expected)
  state['last_generated_code']={**copy.deepcopy(exported),'function':'transform','extra_checks':[]};state['last_code_review']={'checks':copy.deepcopy(exported['checks']),'scope':'Checked transformation of the explicitly selected rows. Filtering is not compiled into this function.'};state['focus_kind']='code'
  return {'status':'complete','answer':'```python\n'+exported['source']+'```\nPass the selected rows shown in code_input. The function does not repeat the table filter.','code':exported,'code_input':rows,'table_source_sha256':table['source_sha256'],'source_rows':previous['source_rows'],'model_calls':0}
 if key=='which columns are available':return {'status':'complete','answer':', '.join(table['columns']),'model_calls':0,'action_repeated':False}
 if key=='show table sources':return {'status':'complete','answer':'Source: explicitly supplied table, '+str(len(table['rows']))+' rows. Receipt: '+table['source_sha256'],'model_calls':0,'action_repeated':False}
 if key=='explain this table result':
  r=state.get('table_result')
  if not r:return {'status':'needs-input','answer':'Complete a table query first.','model_calls':0}
  if r.get('receipt_sha256')!=digest({k:v for k,v in r.items() if k!='receipt_sha256'}):raise ValueError('Retained query result changed; ask the query again')
  return {'status':'complete','answer':'Computed '+r['query']['select']+' from source rows '+', '.join(map(str,r['source_rows']))+'. Result: '+r['exact_result']+'. '+str(len(r['excluded_rows']))+' rows were explicitly excluded for missing values.','model_calls':0,'action_repeated':False}
 if key=='how many rows are there':query={'select':'count'}
 elif conversational:query=conversational
 elif natural:query={'select':{'total':'sum'}.get(natural[1].lower(),natural[1].lower()),'field':natural[2].strip()}
 else:query=json.loads(text.split(':',1)[1])
 if not isinstance(query,dict) or set(query)-{'select','field','where','missing'} or query.get('select') not in ('count','sum','mean','minimum','maximum') or query.get('missing','error') not in ('error','exclude'):raise ValueError('Use count, sum, mean, minimum or maximum with optional field, where and explicit missing policy')
 operation=query['select'];field=query.get('field');condition=query.get('where')
 if operation!='count' and field not in table['columns']:raise ValueError('Name an existing numeric column exactly: '+', '.join(table['columns']))
 if operation=='count' and field is not None:raise ValueError('Count selects rows; omit field')
 if condition is not None and (not isinstance(condition,dict) or set(condition)!={'field','equals'} or condition['field'] not in table['columns'] or type(condition['equals']) not in (str,int,float,bool,type(None))):raise ValueError('where needs an existing field and a scalar equals value')
 selected=[];excluded=[];values=[]
 for index,row in enumerate(table['rows'],1):
  if condition is not None:
   if condition['field'] not in row:raise ValueError('Filter column is missing at source row '+str(index))
   actual=row[condition['field']];expected=condition['equals']
   if type(actual)!=type(expected) or actual!=expected:continue
  if operation!='count':
   value=row.get(field)
   if value is None:
    if query.get('missing')=='exclude':excluded.append(index);continue
    raise ValueError('Missing numeric cell at source row '+str(index)+'; explicitly choose missing exclude to omit it')
   if type(value) not in (int,float):raise ValueError('Nonnumeric cell at source row '+str(index)+'; numeric strings and booleans are not silently converted')
   values.append(Fraction(str(value)))
  selected.append(index)
 if operation=='count':result=Fraction(len(selected))
 elif not values:raise ValueError('No numeric rows match; no mean or total is inferred from absent observations')
 elif operation=='sum':result=sum(values,Fraction())
 elif operation=='mean':result=sum(values,Fraction())/len(values)
 else:result=(min if operation=='minimum' else max)(values)
 report={'query':copy.deepcopy(query),'exact_result':str(result),'source_rows':selected,'excluded_rows':excluded,'source_sha256':table['source_sha256']}
 report['receipt_sha256']=digest(report)
 state['table_result']=copy.deepcopy(report);state['focus_kind']='table'
 return {'status':'complete','answer':str(result)+' from '+str(len(selected))+' source rows.','table_result':report,'model_calls':0,'scope':'Exact arithmetic on explicitly supplied scalar rows. Type-strict filters; source row numbers start at one. Missing cells and omitted causal relationships are not inferred.'}
