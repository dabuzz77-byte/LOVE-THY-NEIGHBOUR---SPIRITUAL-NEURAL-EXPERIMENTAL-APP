"""Read existing FluxBus receipts without modifying the app or its database."""
import json, sqlite3, sys
from pathlib import Path

def read_events(path, cursor):
    uri=Path(path).resolve().as_uri()+'?mode=ro'
    with sqlite3.connect(uri, uri=True, timeout=.5) as db:
        top=db.execute('SELECT COALESCE(MAX(id),0) FROM node_events').fetchone()[0]
        if cursor<0 or cursor>top:
            return {'cursor':top,'events':[]}
        rows=db.execute('SELECT id,node_id,after_json,source,timestamp FROM node_events WHERE id>? ORDER BY id LIMIT 24',(int(cursor),)).fetchall()
    events=[]
    for ident,node,after,source,stamp in rows:
        if str(node).startswith('allprev-'):continue
        try:state=json.loads(after)
        except (ValueError,TypeError):state={'summary':'Stored FluxBus node update'}
        if isinstance(state,dict):state={k:str(v)[:250] for k,v in state.items() if k in ('node_id','raw_state','corrected_bit','timestamp')}
        events.append({'receipt':ident,'node':str(node)[:100],'source':str(source)[:100],'state':state,'timestamp':stamp})
    return {'cursor':rows[-1][0] if rows else top,'events':events}

if __name__=='__main__':
    print(json.dumps(read_events(sys.argv[1],float(sys.argv[2])),ensure_ascii=True))
