"""Source-preserving native summarisation and explicit option comparison."""
import collections,json,math,re

def summarise(text,limit=3):
 if len(text)>16000:raise ValueError('Use up to 16000 characters')
 sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+',text) if x.strip()]
 stop={'the','and','that','with','from','this','have','are','for','was','you','but','not','its','can','will','they','their','of','to','a','in','is','it'}
 def words(s):return [w.casefold() for w in re.findall(r'[^\W_]+',s) if len(w)>2 and w.casefold() not in stop]
 counts=collections.Counter(w for s in sentences for w in set(words(s)));ranked=sorted(range(len(sentences)),key=lambda i:sum(counts[w] for w in set(words(sentences[i])))/max(1,len(words(sentences[i])))**.5,reverse=True)
 chosen=sorted(ranked[:limit]);return {'summary':' '.join(sentences[i] for i in chosen),'extracts':[{'sentence':i+1,'text':sentences[i]} for i in chosen],'source_sentences':len(sentences),'scope':'Extractive summary of supplied text; quoted claims remain claims of that text'}

def compare(body):
 weights=body.get('weights');options=body.get('options')
 if not isinstance(weights,dict) or not 1<=len(weights)<=16 or not isinstance(options,list) or not 2<=len(options)<=16:raise ValueError('Provide 1 to 16 weighted criteria and 2 to 16 named options')
 for w in weights.values():
  if type(w) not in (float,int) or not math.isfinite(w) or abs(w)>100:raise ValueError('Use finite weights within -100 to 100')
 rows=[]
 for option in options:
  scores=option.get('scores',{})
  if set(scores)!=set(weights):raise ValueError('Every option must score every criterion')
  for v in scores.values():
   if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=10:raise ValueError('Use finite scores from 0 to 10')
  parts={k:weights[k]*scores[k] for k in weights};rows.append({'name':str(option.get('name','unnamed'))[:120],'score':math.fsum(parts.values()),'contributions':parts})
 rows.sort(key=lambda r:-r['score']);best=rows[0]['score'];return {'ranking':rows,'selected':[r['name'] for r in rows if r['score']==best],'scope':'Decision under supplied criteria, weights and scores; not a claim that the ratings are objective','model_calls':0}

def respond(text,history):
 lower=text.lower()
 if text.casefold().strip().rstrip('?.!') in ('explain result plainly','explain the result plainly') and history:
  from .result_explanation import explain_attempt
  attempted=explain_attempt(history[-1].get('work_result'))
  if attempted:return attempted
 for prefix in ('summarise:','summarize:','summarise this:','summarize this:'):
  if lower.startswith(prefix):return summarise(text[len(prefix):].strip())
 if lower.startswith('compare options:'):return compare(json.loads(text.split(':',1)[1]))
 if lower in ('explain that','why that result','how did you get that','explain your last answer'):
  if not history:return {'answer':'There is no preceding result to explain yet.'}
  previous=history[-1];answer=str(previous.get('answer',''))
  try:body=previous.get('work_result') or json.loads(answer)
  except (ValueError,TypeError):body={}
  if isinstance(body,dict) and body.get('trace'):return {'answer':'Each completed operation used the previous step’s output.','steps':body['trace'],'source_request':previous.get('request'),'scope':body.get('scope'),'action_repeated':False}
  return {'answer':answer[:6000],'source_request':previous.get('request'),'explanation':'This is the recorded previous answer. No additional derivation was recorded for it.','action_repeated':False}
 return None
