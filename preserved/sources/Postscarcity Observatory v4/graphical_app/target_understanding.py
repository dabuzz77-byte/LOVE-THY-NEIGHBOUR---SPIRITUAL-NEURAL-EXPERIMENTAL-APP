"""Static target descriptions and UTF-8 bit provenance, without executing input."""
import ast
import hashlib
import json
import re


def shape(value, depth=0):
    if depth > 12:raise ValueError('JSON nesting exceeds the inspection limit')
    if isinstance(value, dict):return {k:shape(v,depth+1) for k,v in sorted(value.items())}
    if isinstance(value, list):return [shape(v,depth+1) for v in value]
    return type(value).__name__


def inspect_target(text, kind='text', intent='', provenance=None):
    raw=text.encode('utf-8');parts=[];interfaces=[]
    result={'format':'text','kind':kind,'intent':intent,'intent_basis':'User statement; not independently verified',
            'provenance':provenance or {},'encoding':'UTF-8','bytes':len(raw),'bits':len(raw)*8,
            'content_sha256':hashlib.sha256(raw).hexdigest(),'parts':parts,'interfaces':interfaces,
            'known':['Exact supplied content and bit positions'],
            'unknown':['Actual downstream effects, external dependencies and authority are not established by this input alone.'],
            'analysis_executes_input':False}
    def add(label, category, start, end):
        if start < end and len(parts)<2000:
            parts.append({'label':str(label)[:120],'kind':category,'start_bit':start*8,'end_bit':end*8})
    if kind=='code':
        result['format']='python'
        try:tree=ast.parse(text)
        except SyntaxError as exc:
            result['syntax_error']=str(exc);return result
        lines=text.splitlines(keepends=True);offsets=[0]
        for line in lines:offsets.append(offsets[-1]+len(line.encode('utf-8')))
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                args=node.args
                interfaces.append({'name':node.name,'async':isinstance(node,ast.AsyncFunctionDef),
                    'posonly':[a.arg for a in args.posonlyargs],'args':[a.arg for a in args.args],
                    'kwonly':[a.arg for a in args.kwonlyargs],'vararg':args.vararg.arg if args.vararg else None,
                    'kwarg':args.kwarg.arg if args.kwarg else None})
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.If,ast.Return,ast.Call,ast.Compare,ast.Constant,ast.Name,ast.Assign)):
                label=getattr(node,'name',None) or (ast.get_source_segment(text,node) or type(node).__name__)
                add(label,type(node).__name__,offsets[node.lineno-1]+node.col_offset,offsets[node.end_lineno-1]+node.end_col_offset)
        result['known'].append('Python syntax, function signatures and source spans')
    else:
        try:parsed=json.loads(text)
        except (ValueError,RecursionError):parsed=None
        if isinstance(parsed,(dict,list)):
            result['format']='json';result['shape']=shape(parsed)
            decoder=json.JSONDecoder()
            for match in re.finditer(r'"(?:\\.|[^"\\])*"\s*:',text):
                start=match.end()
                while start<len(text) and text[start].isspace():start+=1
                try:_,end=decoder.raw_decode(text,start)
                except ValueError:continue
                add(match.group().rstrip(':').strip(),'JSON value',len(text[:start].encode('utf-8')),len(text[:end].encode('utf-8')))
            result['known'].append('JSON field names, value types and value spans')
        else:
            for match in re.finditer(r'\S+',text):
                add(match.group(),'text token',len(text[:match.start()].encode('utf-8')),len(text[:match.end()].encode('utf-8')))
    result['parts_limited']=len(parts)>=2000
    if kind=='process':result['unknown'].append('A telemetry snapshot does not reveal executable semantics, private memory or intent.')
    if kind=='module':result['unknown'].append('A module input describes supplied data; assessing it does not execute the module or prove its effects.')
    return result


def affected_parts(target, start, end, limit=6):
    rows=[p for p in target.get('parts',[]) if p['start_bit']<end and p['end_bit']>start]
    return sorted(rows,key=lambda p:(p['end_bit']-p['start_bit'],p['start_bit']))[:limit]


def validate_candidate(original, candidate):
    """Preserve declared structure; structure alone never establishes moral value."""
    if candidate.get('syntax_error'):raise ValueError('Invalid Python syntax: '+candidate['syntax_error'])
    if original['format']=='python' and candidate['interfaces']!=original['interfaces']:
        raise ValueError('The candidate changes a function signature; this run preserves the target interface')
    if original['format']=='json' and (candidate['format']!='json' or candidate['shape']!=original['shape']):
        raise ValueError('The candidate damages JSON field names, collection shape or value types')
