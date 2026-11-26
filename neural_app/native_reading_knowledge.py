"""General question retrieval over approved authored readings, with exact sources.

Retrieval is evidence selection, not verification or a language-model answer.
Only one fixed public-reading index is opened. No private app data or web calls.
"""
import collections,copy,functools,hashlib,json,math,re
from pathlib import Path

STOP=set('a an the this that these those is are was were be been of to for in on at and or it its as by with from about what which how why does do did can could should would me my you your we our i please tell explain describe understand know help give some more app text reading readings library teach teaches teaching teachings say says deal handle use using relates relate'.split())

def stem(word):
    word=word.casefold()
    if word.startswith('protect'):return 'protect'
    if word.startswith('practic'):return 'practice'
    if word.endswith('ies') and len(word)>5:return word[:-3]+'y'
    if word.endswith('s') and len(word)>4 and not word.endswith(('ss','is','us')):return word[:-1]
    return word

def terms(text):return [stem(w) for w in re.findall(r'[^\W_]+',text.casefold()) if w not in STOP and len(w)>1]

class ReadingIndex:
    def __init__(self,documents):
        if not isinstance(documents,list) or len(documents)>800:raise ValueError('Use a bounded approved reading list')
        self.documents={};self.rows=[];self.df=collections.Counter()
        for document in documents:
            if not isinstance(document,dict) or not all(isinstance(document.get(k),str) for k in ('id','title','text')):raise ValueError('Reading documents need id, title and text')
            ident=document['id']
            if ident in self.documents or not re.fullmatch(r'[\w-]{1,180}',ident) or len(document['title'])>400 or len(document['text'])>20000:raise ValueError('Invalid or duplicate reading document')
            actual=hashlib.sha256(document['text'].encode()).hexdigest()
            if document.get('text_sha256',actual)!=actual:raise ValueError('Reading text no longer matches its source receipt')
            self.documents[ident]=copy.deepcopy(document);title_terms=set(terms(document['title']))
            for part in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',document['text']):
                paragraph=part.group().strip()
                if paragraph.startswith('#') or len(paragraph)<25:continue
                # Retain exact source spans; bounded excerpts are marked in the result.
                if len(paragraph)>1400:
                    paragraph=paragraph[:1400].rsplit(' ',1)[0]
                words=collections.Counter(terms(paragraph))
                if not words:continue
                start=part.start()+len(part.group())-len(part.group().lstrip())
                row={'source_id':ident,'title':document['title'],'text':paragraph,'start':start,
                     'end':start+len(paragraph),'tokens':words,'title_terms':title_terms,
                     'text_sha256':actual,'provenance':document.get('provenance','Authored app reading')}
                self.rows.append(row);self.df.update(set(words)|title_terms)
                if len(self.rows)>=12000:raise ValueError('Reading paragraph index exceeds its bound')

    def search(self,question,limit=3,skip=()):
        query=set(terms(question));ranked=[];seen=set(skip);count=max(1,len(self.rows))
        if not query:return []
        for row in self.rows:
            signature=hashlib.sha256(row['text'].encode()).hexdigest()
            if signature in seen:continue
            matched=query&(set(row['tokens'])|row['title_terms']);coverage=len(matched)/len(query)
            # A weak single-word match in an otherwise unrelated question is insufficient.
            if coverage<.6 or not matched:continue
            score=0
            for word in matched:
                idf=math.log(1+(count-self.df[word]+.5)/(self.df[word]+.5))
                frequency=row['tokens'][word]
                score+=idf*((2*frequency/(frequency+1) if frequency else 0)+(2.5 if word in row['title_terms'] else 0))
            ranked.append((score*coverage,coverage,signature,row))
        ranked.sort(key=lambda item:(-item[0],-item[1],item[3]['source_id'],item[3]['start']))
        selected=[];per_document=collections.Counter()
        for score,coverage,signature,row in ranked:
            if signature in seen or per_document[row['source_id']]>=2:continue
            seen.add(signature);per_document[row['source_id']]+=1
            selected.append({k:copy.deepcopy(row[k]) for k in ('source_id','title','text','start','end','text_sha256','provenance')}|{'match_coverage':coverage,'retrieval_score':round(score,6),'passage_sha256':signature})
            if len(selected)>=limit:break
        return selected

@functools.lru_cache(maxsize=2)
def _load(path,size,mtime):
    if size>2500000:raise ValueError('Approved reading index exceeds 2.5 MB')
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return ReadingIndex(data['documents'])

def installed_index():
    path=Path(__file__).resolve().parent.parent/'references/native-public-readings.json'
    if not path.is_file():return None
    stat=path.stat();return _load(str(path),stat.st_size,stat.st_mtime_ns)

def render(question,passages):
    lines=['**From the app’s authored readings**',question]
    for row in passages:
        lines.append('['+row['source_id']+'] **'+row['title']+'**\n\n'+row['text'])
    lines.append('These are source excerpts selected for relevance. They express the authored readings; retrieval does not independently verify their claims or establish a causal explanation. Ask “show app sources” to inspect their provenance.')
    return '\n\n'.join(lines)

def respond(text,state,index=None):
    key=text.strip().casefold().rstrip('?.!');current=state.get('app_reading_answer');focused=state.get('focus_kind')=='app-reading-answer'
    explicit=re.match(r'^(?:search app teachings|ask app readings):\s*(.+)',text,re.I|re.S)
    source=re.fullmatch(r'show app source\s+([\w-]+)',text,re.I)
    resume=bool(current and key=='resume app readings')
    if not explicit and not source:
        if key in ('what can you do','what are your capabilities'):return None
        if key in ('what are you thinking','what is your thought process','why is this verified','explain your reasoning') and not focused:return None
        # A request about the user's particular plan or failure needs its observations,
        # rather than a coincidental match in an authored teaching.
        if re.match(r'how (?:can|do|could|should) (?:i|we)\b',key):return None
        if re.match(r'(?:why|how)\b',key) and re.search(r'\b(?:crash|crashes|failed|failure|error|broken|stopped|yesterday|today)\b',key):return None
        if re.search(r'\b(?:this|that|it)\b',key) and len(set(terms(key)))<3 and not focused:return None
    if not (explicit or source or resume or focused or re.match(r'^(?:what|how|why|explain|describe|tell me|compare)\b',key)):return None
    index=index or installed_index()
    if index is None:return None
    if resume:
        state['focus_kind']='app-reading-answer'
        return {'status':'source-answer','answer':render(current['question'],current['passages']),'source_knowledge':copy.deepcopy(current),'model_calls':0}
    if source:
        document=index.documents.get(source[1])
        if document is None:return {'status':'needs-input','answer':'That identifier is not in the approved reading index.','model_calls':0}
        return {'status':'source-text','answer':document['title']+'\n\n'+document['text']+'\n\nProvenance: '+document.get('provenance','Authored app reading'),'model_calls':0}
    if focused and key=='show app sources':
        return {'status':'complete','answer':'\n\n'.join('['+r['source_id']+'] '+r['title']+'\n'+r['provenance']+'\nText SHA-256: '+r['text_sha256'] for r in current['passages']),'model_calls':0}
    if focused and key in ('why','why these sources','why did you choose those','explain that','why is this verified','explain result plainly','what are you thinking','what is your thought process','explain your reasoning'):
        return {'status':'complete','answer':'I selected exact passages by content-word coverage and relevance to the source titles. This is retrieval evidence, not an independent proof of the claims.\n\n'+render(current['question'],current['passages']),'model_calls':0}
    more=focused and key in ('more','give me more','continue with more sources','show more')
    question=current['question'] if more else explicit[1].strip() if explicit else text.strip()
    if focused and re.search(r'\b(?:this|that|it)\b',key) and len(set(terms(key)))<3:question=current['question']
    if focused:
        follow=re.fullmatch(r'what about\s+(.+)',text.strip().rstrip('?.!'),re.I)
        if follow:question=follow[1]
    passages=index.search(question,3,current.get('seen_passages',[]) if more else ())
    if not passages:
        if explicit or more:return {'status':'needs-evidence','answer':'No sufficiently matching passage is available in the approved app readings. Supply a source or choose a more specific topic; I have not invented an answer.','model_calls':0}
        return None
    report={'question':question,'passages':passages,'scope':'Approved authored reading corpus only; no private files or network retrieval.',
            'seen_passages':((current.get('seen_passages',[]) if more else [])+[r['passage_sha256'] for r in passages])[-24:]}
    state['app_reading_answer']=copy.deepcopy(report);state['focus_kind']='app-reading-answer'
    return {'status':'source-answer','answer':render(question,passages),'source_knowledge':report,'model_calls':0}
