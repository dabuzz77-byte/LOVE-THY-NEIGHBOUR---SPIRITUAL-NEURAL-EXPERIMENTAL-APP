"""Searchable source-labelled reference corpus; no command execution."""
import collections,functools,json,re,sqlite3,threading
from pathlib import Path
_lock=threading.RLock()
@functools.lru_cache(maxsize=1)
def database():
 db=sqlite3.connect(':memory:',check_same_thread=False)
 db.execute('CREATE VIRTUAL TABLE entries USING fts5(domain,title,body,source,level)')
 p=Path(__file__).resolve().parents[1]/'references/knowledge-library.jsonl'
 with p.open(encoding='utf-8') as f:
  for line in f:
   r=json.loads(line);db.execute('INSERT INTO entries VALUES(?,?,?,?,?)',tuple(r[k].encode('utf-8','backslashreplace').decode('utf-8') for k in ('domain','title','body','source','level')))
 db.commit();return db

def search(query,limit=8):
 terms=re.findall(r'[^\W_]+',str(query),re.UNICODE)[:16]
 if not terms:return []
 match=' OR '.join('"'+t+'"' for t in terms)
 with _lock:
  rows=database().execute('SELECT rowid,domain,title,body,source,level FROM entries WHERE entries MATCH ? ORDER BY bm25(entries,0.5,8,1,0,0) LIMIT ?',(match,max(1,min(int(limit),30)))).fetchall()
 return [dict(zip(('id','domain','title','excerpt','source','level'),r)) for r in rows]

def stats():
 with _lock:counts=dict(database().execute('SELECT domain,count(*) FROM entries GROUP BY domain'))
 return {'records':sum(counts.values()),'domains':counts,'scope':'Source-labelled reference retrieval. Lexical recognition, grammar orientation and verified execution are distinct capabilities.','usage':'library: your question or term','training':'Retrieved knowledge; model weights are unchanged.'}

