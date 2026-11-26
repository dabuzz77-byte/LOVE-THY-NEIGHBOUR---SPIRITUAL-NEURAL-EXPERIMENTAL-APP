"""Compact source-labelled retrieval for local knowledge and user memories."""
import collections,hashlib,json,math,re,threading,unicodedata
from pathlib import Path
STOP=set('a an the and or of to in is are was were be been it this that for with from what who why how tell me about explain please my do you know'.split())
def tokens(text):return [w for w in re.findall(r'[^\W_]+',unicodedata.normalize('NFKC',str(text)).casefold()) if w not in STOP and len(w)>1][:1024]
RELATED_GROUPS=[set(group.split()) for group in ('money cost price finance budget','food nutrition provision nourishment','care compassion welfare kindness','star stellar sun','code programming software','learn learning study education','water hydration','nature environment ecology','energy electricity power','safety protection security') ]
def retrieve(query,documents,limit=4):
 q=set(tokens(query));rows=[]
 if not q:return []
 for d in documents[:512]:
  title=tokens(d.get('title',''));body=tokens(d.get('text',''));counts=collections.Counter(body);overlap=q&set(title+body)
  if not overlap and not any(t in group and bool(group&set(title+body)) for t in q for group in RELATED_GROUPS):continue
  related={t for t in q-overlap if any(t in group and bool(group&set(title+body)) for group in RELATED_GROUPS)}
  coverage=(len(overlap)+len(related))/len(q);score=sum(2.5*(t in title)+min(2,counts[t]) for t in q)/math.sqrt(max(8,len(body)))+.25*len(related)/math.sqrt(max(8,len(body)))
  if coverage<.5:continue
  rows.append((score,coverage,d))
 selected=sorted(rows,key=lambda x:(x[0],x[1]),reverse=True)[:limit]
 return [{**d,'score':round(score,4),'query_coverage':coverage} for score,coverage,d in selected]
class EvidenceIndex:
 def __init__(self):self.lock=threading.RLock();self.documents=None;self.stream_documents=collections.OrderedDict();self.queries=0;self.hits=0
 def load(self):
  with self.lock:
   if self.documents is not None:return self.documents
   docs=[];base=Path(__file__).resolve().parents[1]
   for file in sorted((base/'assets').glob('*lesson.json')):
    try:
     data=json.loads(file.read_text(encoding='utf-8'))
     for i,row in enumerate(data.get('chapters',[])[:40]):
      for field in ('story','human','text'):
       if isinstance(row.get(field),str):docs.append({'id':file.stem+':'+str(i)+':'+field,'title':data.get('title','')+' · '+row.get('title',''),'text':row[field][:3000],'provenance':'authored spiritual reflection' if field=='human' else 'source-linked lesson summary','sources':data.get('sources',[])[:4]})
    except (OSError,ValueError,TypeError):continue
   for name in ('mustard_seed','animal_kinship','dinosaur_faith','watts_unity'):
    try:
     from importlib import import_module
     data=import_module('.'+name,__package__).lesson()
     for i,row in enumerate((data.get('chapters') or data.get('stages') or [])[:40]):
      if isinstance(row,dict) and isinstance(row.get('text'),str):docs.append({'id':name+':'+str(i),'title':data.get('title',name)+' · '+row.get('title',''),'text':row['text'][:3000],'provenance':'authored lesson text','sources':data.get('sources',[])[:3]})
    except (ImportError,AttributeError,TypeError,ValueError):continue
   self.documents=docs[:256];return self.documents
 def add_source(self,url,title,text):
  key=hashlib.sha256((url+'\0'+text).encode()).hexdigest()[:24]
  with self.lock:
   self.stream_documents[key]={'id':'net:'+key,'title':str(title)[:200],'text':str(text)[:1200],'provenance':'retrieved public source; not independently verified','sources':[{'title':str(title)[:200],'url':url}]}
   self.stream_documents.move_to_end(key)
   while len(self.stream_documents)>128:self.stream_documents.popitem(last=False)
 def search(self,query,memories=None,limit=4):
  docs=list(self.load())
  with self.lock:docs+=list(self.stream_documents.values())
  for key,row in list((memories or {}).items())[-128:]:
   if isinstance(row,dict) and isinstance(row.get('value'),str) and not re.search(r'password|secret|token|api.?key',key,re.I) and not re.search(r'(?i)(password|api.?key|token)\s*[:=]|sk-[A-Za-z0-9_-]{10,}',row['value']):docs.append({'id':'memory:'+hashlib.sha256(key.encode()).hexdigest()[:16],'title':key,'text':row['value'][:3000],'provenance':row.get('provenance','user-reported'),'sources':[]})
  result=retrieve(query,docs,limit)
  with self.lock:self.queries+=1;self.hits+=bool(result)
  return result
 def view(self):
  with self.lock:return {'indexed_lesson_passages':len(self.load()),'indexed_stream_passages':len(self.stream_documents),'queries':self.queries,'queries_with_matches':self.hits,'scope':'Local selected lesson text and explicitly stored memories; retrieval does not certify a claim or infer new private access.'}
 def respond(self,text,memories):
  personal=re.fullmatch(r'what is my (.+?)[?]?',text,re.I)
  if personal:
   key=personal[1].strip().rstrip('?').casefold();matches=[(k,r) for k,r in memories.items() if k.casefold()==key and isinstance(r,dict) and isinstance(r.get('value'),str)]
   if matches and not re.search(r'password|secret|token|api.?key',key,re.I):
    k,row=matches[0];return {'answer':'You told me your '+k+' is '+row['value']+'.','model_used':False,'native_skill':'explicit-user-memory','provenance':row.get('provenance','user-reported')}
  m=re.fullmatch(r'(?:explain|tell me about|what (?:do you remember|is in the app) about|search lessons for)\s+(.+)',text,re.I|re.S)
  if not m:return None
  query=m[1].strip();rows=self.search(query,memories,3)
  if not rows:return None
  return {'answer':'\n\n'.join(r['title']+' ['+r['provenance']+']\n'+r['text'][:1100] for r in rows),'model_used':False,'native_skill':'source-labelled-retrieval','references':[{'id':r['id'],'title':r['title'],'provenance':r['provenance'],'sources':r['sources']} for r in rows],'scope':'Extractive local response; passages retain their source and interpretive status.'}
INDEX=EvidenceIndex()
