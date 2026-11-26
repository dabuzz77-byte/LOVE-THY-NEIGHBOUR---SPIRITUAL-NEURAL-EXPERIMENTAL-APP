"""Private local reader for exact supplied originals, independent of study summaries."""
import hashlib,json

def view(root):
    folder=root/'data/original-lessons';index=folder/'index.json'
    if not index.exists():return {'title':'Original supplied lessons','documents':[]}
    data=json.loads(index.read_text(encoding='utf-8'))
    for row in data['documents']:
        if row['kind']!='text':continue
        path=(folder/row['file']).resolve()
        if path.parent!=folder.resolve():raise ValueError('Invalid source document')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Original source digest mismatch')
        row['text']=raw.decode('utf-8-sig')
        row.pop('file',None)
    return data
