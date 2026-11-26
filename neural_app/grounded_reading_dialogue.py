"""Native document conversation: extract, focus and answer from a retained text."""
import copy,json,re

def summarize(source,limit=3,focus=None):
    from .conversation_work import summarise
    if focus:
        from .evidence_workbench import tokens
        parts=[p.strip() for p in re.split(r'(?<=[.!?])\s+|\n+',source) if p.strip()]
        wanted=tokens(focus)
        ranked=sorted(enumerate(parts),key=lambda pair:(-len(wanted&tokens(pair[1])),pair[0]))
        chosen=sorted((i,text) for i,text in ranked[:limit] if wanted&tokens(text))
        extracts=[{'sentence':i+1,'text':text} for i,text in chosen]
        return {'summary':' '.join(row['text'] for row in extracts),'extracts':extracts,'source_sentences':len(parts),'scope':'Exact matching source sentences. A lexical match is not a semantic or factual verification.'}
    return summarise(source,limit)

def respond(text,state):
    start=re.fullmatch(r'(?:summari[sz]e(?: this)?|give me a summary of this|turn this into (?:bullet points|notes))\s*:\s*([\s\S]+)',text,re.I)
    reading=re.fullmatch(r'(?:read this|answer (?:from|using) this text):\s*([\s\S]+?)\nQuestion:\s*([^\n]+)',text,re.I)
    if reading:
        from .evidence_workbench import respond as evidence
        return evidence('research brief: '+json.dumps({'question':reading[2],'sources':[{'id':'Text','title':'Your supplied passage','text':reading[1]}]}),state)
    current=state.get('reading_dialogue');key=text.strip().casefold().rstrip('?.!');focus=None
    if start:
        source=start[1].strip();limit=3
    elif current and state.get('focus_kind')=='reading-dialogue':
        count=re.fullmatch(r'(?:make (?:that|it) |)(shorter|longer)|(?:use|give me) (\d+) (?:sentences?|points?)',key)
        topic=re.fullmatch(r'(?:focus on|what did (?:it|the text|i) say about)\s+(.+)',text.strip().rstrip('?.!'),re.I)
        if key in ('show the original','show original text'):
            return {'status':'complete','answer':current['source'],'model_calls':0,'action_repeated':False}
        if key in ('why','explain that','where did that come from','show sentence sources'):
            return {'status':'complete','answer':'These are verbatim extracts from your retained text:\n\n'+'\n\n'.join('Sentence '+str(r['sentence'])+': '+r['text'] for r in current['report']['extracts']),'model_calls':0}
        if not count and not topic:return None
        source=current['source'];limit=current['limit']
        if topic:focus=topic[1]
        elif count[2]:limit=int(count[2])
        else:limit=max(1,limit-1) if count[1]=='shorter' else min(8,limit+1)
    else:return None
    if not 1<=limit<=8:raise ValueError('Choose 1–8 extracted sentences')
    report=summarize(source,limit,focus)
    if not report['extracts']:
        return {'status':'needs-evidence','answer':'The text has no matching sentence for that topic. The previous summary remains available.','reading':copy.deepcopy(report),'model_calls':0}
    else:answer='From your supplied text:\n\n'+'\n'.join('- ['+str(r['sentence'])+'] '+r['text'] for r in report['extracts'])+'\n\n'+report['scope']
    state['reading_dialogue']={'source':source,'limit':limit,'focus':focus,'report':report};state['focus_kind']='reading-dialogue'
    return {'status':'complete' if report['extracts'] else 'needs-evidence','answer':answer,'reading':copy.deepcopy(report),'model_calls':0}
