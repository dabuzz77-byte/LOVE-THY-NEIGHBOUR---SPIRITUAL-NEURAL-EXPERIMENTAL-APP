"""Pure bounded data skills. No shell, file, model or network execution."""
import csv,io,json,math,re,statistics,collections

def numeric_stats(text):
 tokens=[x for x in re.split(r'[\s,;]+',text.strip()) if x]
 if not 1<=len(tokens)<=512:raise ValueError('Provide 1 to 512 finite numbers')
 values=[float(x) for x in tokens]
 if any(not math.isfinite(x) or abs(x)>1e100 for x in values):raise ValueError('Use finite numbers within the supported range')
 total=math.fsum(values)
 return {'count':len(values),'sum':total,'minimum':min(values),'maximum':max(values),'mean':total/len(values),'median':statistics.median(values),'population_variance':statistics.pvariance(values)}

def csv_to_json(text):
 rows=list(csv.reader(io.StringIO(text)))
 if not rows or not rows[0]:raise ValueError('CSV needs a header row')
 header=rows[0]
 if any(not x for x in header) or len(set(header))!=len(header):raise ValueError('Use nonempty unique CSV column names')
 if len(rows)>513 or len(header)>64:raise ValueError('Use at most 512 data rows and 64 columns')
 if any(len(row)!=len(header) for row in rows[1:]):raise ValueError('Every CSV row must have the header column count')
 return [dict(zip(header,row)) for row in rows[1:]]

def json_to_csv(text):
 rows=json.loads(text)
 if not isinstance(rows,list) or not 1<=len(rows)<=512 or any(not isinstance(r,dict) for r in rows):raise ValueError('Provide 1 to 512 JSON objects in an array')
 header=list(rows[0]);keys=set(header)
 if not header or len(header)>64 or any(set(r)!=keys for r in rows):raise ValueError('Use matching nonempty object keys in every row')
 if any(isinstance(v,(dict,list)) for r in rows for v in r.values()):raise ValueError('CSV cells must be scalar values')
 output=io.StringIO(newline='');writer=csv.writer(output,lineterminator='\n');writer.writerow(header);writer.writerows([[r[k] for k in header] for r in rows]);return output.getvalue()

def respond(text):
 if len(text)>8192:raise ValueError('Use a request below 8192 characters')
 lower=text.lower()
 for prefix,kind,op in [('reverse text ','text-reverse',lambda s:s[::-1]),('uppercase ','text-uppercase',str.upper),('lowercase ','text-lowercase',str.lower),('normalise whitespace ','whitespace-normalisation',lambda s:' '.join(s.split())),('normalize whitespace ','whitespace-normalisation',lambda s:' '.join(s.split())),('statistics ','numeric-statistics',numeric_stats),('csv to json\n','csv-to-json',csv_to_json),('json to csv ','json-to-csv',json_to_csv)]:
  if lower.startswith(prefix):
   source=text[len(prefix):];value=op(source)
   return {'skill':kind,'result':value,'verification':'Bounded pure transformation; correctness is tested against independent contracts in the quality suite.','model_calls':0}
 if lower.startswith('text statistics '):
  value=text[len('text statistics '):];words=re.findall(r"[^\W_]+",value,flags=re.UNICODE)
  return {'skill':'text-statistics','result':{'characters':len(value),'utf8_bytes':len(value.encode('utf-8')),'lines':len(value.splitlines()),'words':len(words),'unique_words':len({w.casefold() for w in words})},'model_calls':0}
 return None
