"""Native conversations over an open vocabulary of attributed relations and rules.

The vocabulary is open; the grammar is deliberately inspectable. Statements are
user-supplied premises, never independently verified facts or system instructions.
"""
import copy,json,re,time

def clean(value):
    value=' '.join(value.strip(' \t.?!"').casefold().split())
    if not value or len(value)>100 or value.startswith('?'):raise ValueError('Use named entities and relations of 1–100 characters')
    return value

def verb(value):
    value=clean(value)
    if value in ('is','are','am','was','were'):return 'is'
    if value in ('has','have'):return 'have'
    if value.endswith('ies') and len(value)>4:return value[:-3]+'y'
    if value.endswith(('ches','shes','sses','xes','zes','oes')):return value[:-2]
    if value.endswith('s') and not value.endswith(('ss','us','is')):return value[:-1]
    return value

def atom(subject,relation,obj,negative=False):
    return {'subject':subject if subject.startswith('?') else clean(subject),'relation':verb(relation),
            'object':obj if obj.startswith('?') else clean(obj),'negated':negative,'context':'conversation'}

def predicate(subject,tail):
    neg=re.fullmatch(r'(?:does|do|did) not ([\w-]+) (.+)',tail,re.I)
    if neg:return atom(subject,neg[1],neg[2],True)
    cat=re.fullmatch(r'(is|are|am|was|were) (not )?(?:a |an )?(.+)',tail,re.I)
    if cat:return atom(subject,'is_a' if re.match(r'(?:is|are|am|was|were) (?:not )?(?:a|an) ',tail,re.I) else 'is',cat[3],bool(cat[2]))
    match=re.fullmatch(r'([\w-]+) (.+)',tail)
    if not match or match[1].casefold() in ('might','may','could','would','should','must','will','can','not','and','or','then'):
        raise ValueError('Use an explicit subject, verb and object; conditional or uncertain statements need an explicit rule')
    return atom(subject,match[1],match[2])

def statement(text):
    text=text.strip().rstrip('.!?')
    pipes=text.split('|')
    if len(pipes)==3:return atom(*pipes)
    quoted=re.fullmatch(r'"([^"]+)"\s+(.+)',text)
    if quoted:return predicate(quoted[1],quoted[2])
    # Single-token subjects are unambiguous; quoted labels support longer names.
    match=re.fullmatch(r'([\w-]+)\s+(.+)',text)
    if not match or match[1].casefold() in ('if','every','some','all','who','what','why','how','when','where','which','please','tell','show','explain','describe','list','name','give','compare','help','write','create','calculate','run','execute','delete','forget','remember','sort','think','the','a','an','my','your','their'):
        raise ValueError('Name the subject explicitly; quote a multiword subject or use SUBJECT | VERB | OBJECT')
    return predicate(match[1],match[2])

def rule(text):
    universal=re.fullmatch(r'every ([\w-]+) (.+)',text.strip().rstrip('.!?'),re.I)
    if universal:return {'if':[atom('?x','is_a',universal[1])],'then':predicate('?x',universal[2])}
    implication=re.fullmatch(r'if (?:someone|a person) (.+) then (?:they|that person) (.+)',text.strip().rstrip('.!?'),re.I)
    if implication:
        return {'if':[predicate('?x',part.strip()) for part in re.split(r'\s+and\s+',implication[1],flags=re.I)],'then':predicate('?x',implication[2])}
    return None

def query(text):
    text=text.strip().rstrip('.!?')
    match=re.fullmatch(r'(?:what|who) (?:does|do) (.+?) ([\w-]+)',text,re.I)
    if match:return [atom(match[1],match[2],'?answer')]
    match=re.fullmatch(r'(?:does|do) ("[^"]+"|[\w-]+) (.+)',text,re.I)
    if match:return [predicate(match[1].strip('"'),match[2])]
    match=re.fullmatch(r'is ("[^"]+"|[\w-]+) (not )?(a |an )?(.+)',text,re.I)
    if match:return [atom(match[1].strip('"'),'is_a' if match[3] else 'is',match[4],bool(match[2]))]
    match=re.fullmatch(r'who both (.+)',text,re.I)
    if match:return [predicate('?answer',part) for part in re.split(r'\s+and\s+',match[1],flags=re.I)]
    match=re.fullmatch(r'(?:who|what) (.+)',text,re.I)
    if match:return [predicate('?answer',match[1])]
    raise ValueError('Ask who VERB OBJECT, what does NAME VERB, does NAME VERB OBJECT, or is NAME a CATEGORY')

def known_statement(text,model):
    known={f[k] for f in model['facts'] for k in ('subject','object')}
    candidates=[name for name in known if ' ' in name and text.casefold().startswith(name+' ')]
    if candidates:
        longest=max(candidates,key=len)
        return predicate(longest,text[len(longest):].strip())
    return statement(text)

def singular(value):
    lower=value.casefold()
    return {'people':'person','children':'child','men':'man','women':'woman','mice':'mouse','geese':'goose'}.get(lower,verb(lower))

def interpret_question(text,model):
    original=text.strip().rstrip('.!?');text=original
    text=re.sub(r'^(?:(?:please|could you|can you|would you)\s+)+','',text,flags=re.I)
    truth=re.fullmatch(r'(?:is it true that|tell me whether|do we know whether)\s+(.+)',text,re.I)
    if truth:
        try:return {'patterns':[known_statement(truth[1],model)],'mode':'answer','original':original}
        except ValueError:return None
    text=re.sub(r'^(?:i would like to know|i.d like to know|tell me|remind me)\s+','',text,flags=re.I)
    text=re.sub(r'^(?:name everyone who|list everyone who|who is it that)\s+','who ',text,flags=re.I)
    text=re.sub(r'^which (?:things|objects) (does|do)\s+',r'what \1 ',text,flags=re.I)
    text=re.sub(r'^which (?:entities|subjects)\s+','who ',text,flags=re.I)
    object_count=re.fullmatch(r'how many (?:things|objects) (?:does|do) (.+?) ([\w-]+)',text,re.I)
    if object_count:return {'patterns':[atom(object_count[1],object_count[2],'?answer')],'mode':'count','original':original}
    category=re.fullmatch(r'(which|how many) ([\w-]+) ([\w-]+) (.+)',text,re.I)
    if category:
        return {'patterns':[atom('?answer','is_a',singular(category[2])),predicate('?answer',category[3]+' '+category[4])],
                'mode':'count' if category[1].casefold()=='how many' else 'answer','original':original}
    # Embedded object questions require a known subject; unknown wording is not guessed.
    embedded=re.fullmatch(r'what (.+?) ([\w-]+)',text,re.I)
    subjects={f['subject'] for f in model['facts']}
    if embedded and clean(embedded[1]) in subjects:
        return {'patterns':[atom(embedded[1],embedded[2],'?answer')],'mode':'answer','original':original}
    try:return {'patterns':query(text),'mode':'answer','original':original}
    except ValueError:return None

def render(report,model):
    lines=['Under the statements and rules supplied in this conversation:']
    answers=report.get('answers',[])
    if report.get('answer_mode')=='count':
        lines.append(str(len(answers))+' distinct matching entities in the retained premises. This is a count of recorded support, not a count of all real-world entities.')
    elif answers:
        for answer in answers:
            values=', '.join(answer['bindings'].values()) or 'The queried statement follows.'
            lines.append('- '+values+(' — supporting statements conflict.' if answer.get('has_conflicted_support') else ''))
    elif report.get('counter_supporting_fact_ids'):lines.append('The supplied premises explicitly support the opposite of that statement.')
    else:lines.append('That relation is unknown from the retained premises. Unknown does not mean false.')
    graph=report.get('proof_graph',[])
    sources={s['source'] for row in graph for s in row.get('given_sources',[])}
    used_rules={row['proof']['rule'] for row in graph if row['proof']['kind']=='derived'}
    sources|={model['rules'][i-1]['source'] for i in used_rules}
    if sources:lines.append('Supporting records: '+', '.join(sorted(sources))+'.')
    if report.get('status')=='conflicting-support':lines.append('Resolve the conflicting records before relying on this conclusion.')
    if not report.get('complete'):lines.append('Processing reached a bound; this answer is incomplete.')
    lines.append('These are conditional deductions from your attributed premises, not independent verification of people or events.')
    return '\n\n'.join(lines)

def solve(model,patterns):
    from .relational_reasoning import solve as infer
    return infer({'facts':model['facts'],'rules':[{'if':r['if'],'then':r['then']} for r in model['rules']], 'query':patterns})

def respond(text,state,fallback=False):
    key=text.strip().casefold().rstrip('?.!');old=state.get('concept_conversation');focused=state.get('focus_kind')=='concept-conversation'
    explicit=re.match(r'^(?:discuss these statements|conversation facts|note that|let.s discuss):?\s*(.+)',text,re.I|re.S)
    replacement=re.fullmatch(r'replace (F\d+):\s*(.+)',text,re.I|re.S) if old else None
    if focused:
        recall=re.fullmatch(r'what did i say about (.+)',key)
        if recall:text='Tell me about '+recall[1];key=text.casefold()
        follow=re.fullmatch(r'(?:what about|and|actually,? i meant)\s+(.+)',text.strip().rstrip('?.!'),re.I)
        if follow:
            if clean(follow[1]) in ('he','she','it','they','them','this','that'):
                return {'status':'needs-clarification','answer':'Which named entity do you mean? I have not guessed the pronoun reference.','model_calls':0}
            previous=old.get('last_report');patterns=copy.deepcopy(previous.get('query',[])) if previous else []
            subjects={p['subject'] for p in patterns if not p['subject'].startswith('?')}
            if len(subjects)!=1 or not any(p['object'].startswith('?') for p in patterns):
                return {'status':'needs-clarification','answer':'Which question or relation should I apply to '+follow[1]+'? I have not guessed whether you mean a subject or an object.','model_calls':0}
            for pattern in patterns:pattern['subject']=clean(follow[1])
            report=solve(old,patterns);report['source_question']=text;report['answer_mode']=previous.get('answer_mode','answer');report['inference_status']=report['status']
            if report['answer_mode']=='count' and report['complete'] and report['status']!='conflicting-support':report['status']='counted'
            new=copy.deepcopy(old);new['last_report']=report;state['concept_conversation']=new
            return {'status':report['status'],'answer':render(report,new),'concept_reasoning':report,'model_calls':0,**({'count':len(report['answers'])} if report['answer_mode']=='count' else {})}
    hypothetical=re.fullmatch(r'what if (F\d+) (?:were|was|became)\s*:\s*(.+)',text.strip().rstrip('?.!'),re.I|re.S) if old and focused else None
    if hypothetical:
        if not old.get('last_report'):return {'status':'needs-input','answer':'Ask a discussion question first; I can then recheck it under that hypothetical replacement.','model_calls':0}
        model=copy.deepcopy(old);prior=next((f for f in model['facts'] if f['source']==hypothetical[1].upper()),None)
        if prior is None:raise ValueError('Choose an existing F-number from show discussion records')
        changed=statement(hypothetical[2]);model['facts'].remove(prior)
        model['facts'].append({**changed,'source':hypothetical[1].upper()+'-hypothesis','text':hypothetical[2]})
        report=solve(model,old['last_report']['query'])
        report['answer_mode']=old['last_report'].get('answer_mode','answer');report['inference_status']=report['status']
        if report['answer_mode']=='count' and report['complete'] and report['status']!='conflicting-support':report['status']='counted'
        state['concept_scenario']={'report':report,'replacement':hypothetical[2]}
        return {'status':report['status'],'answer':'Hypothetical replacement only; the original discussion is unchanged.\n\n'+render(report,model),'concept_reasoning':report,'hypothetical':True,'model_calls':0}
    if old and key in ('resume discussion','back to discussion'):
        state['focus_kind']='concept-conversation'
        return {'status':'complete','answer':f"Discussion retained: {len(old['facts'])} attributed statements and {len(old['rules'])} rules. Ask a question or say “show discussion records”.",'model_calls':0}
    if focused and key in ('show discussion records','show premises','show discussion sources'):
        rows=old['facts']+old['rules']
        return {'status':'complete','answer':'\n\n'.join(row['source']+': '+row['text'] for row in rows),'model_calls':0}
    if focused and key in ('why','why is that','show proof','explain that','how did you get that','why is this verified','explain result plainly'):
        report=old.get('last_report')
        if not report:return {'status':'needs-input','answer':'Ask a question first so I can show its supporting records.','model_calls':0}
        proof=json.dumps(report['proof_graph'],ensure_ascii=False,indent=2)
        return {'status':report['status'],'answer':render(report,old)+'\n\nRecorded proof:\n'+proof,'model_calls':0}
    if focused and key in ('what could change that conclusion','which premises matter','what assumptions matter'):
        report=old.get('last_report')
        if not report:return {'status':'needs-input','answer':'Ask a discussion question first so I can check its dependencies.','model_calls':0}
        changes=[];started=time.monotonic();checked=0
        for fact in old['facts']:
            if checked>=24 or time.monotonic()-started>.35:break
            trial=copy.deepcopy(old);trial['facts']=[f for f in trial['facts'] if f['source']!=fact['source']]
            tested=solve(trial,report['query'])
            checked+=1
            signature=lambda r:(r.get('inference_status',r['status']),sorted(json.dumps(a['bindings'],sort_keys=True) for a in r['answers']))
            if signature(tested)!=signature(report):changes.append(fact['source']+': '+fact['text']+' — removing it changes the conclusion to '+tested['status'])
        return {'status':'complete' if checked==len(old['facts']) else 'partial-analysis','answer':'Individual-premise sensitivity under this model ('+str(checked)+' of '+str(len(old['facts']))+' facts checked):\n\n'+('\n\n'.join(changes) if changes else 'No checked individual fact removal changes this answer.')+'\n\nThis does not test every combination or removal of rules.','model_calls':0}
    if focused and re.match(r'^(?:tell me about|what do you know about)\s+',key):
        name=re.sub(r'^(?:tell me about|what do you know about)\s+','',key);name=clean(name)
        rows=[f for f in old['facts'] if name in (f['subject'],f['object'])]
        answer='Retained statements about '+name+':\n\n'+'\n\n'.join(f['source']+': '+f['text'] for f in rows) if rows else 'No retained statement names '+name+'. What should I use as a source?'
        return {'status':'complete' if rows else 'needs-evidence','answer':answer+'\n\nThese remain user-supplied statements.','model_calls':0}
    interpreted=interpret_question(text,old) if focused else None
    if interpreted:
        patterns=interpreted['patterns']
        known={f[k] for f in old['facts'] for k in ('subject','object')}
        known.update(r['then']['object'] for r in old['rules'])
        anchors={p[k] for p in patterns for k in ('subject','object') if not p[k].startswith('?')}
        if anchors and not anchors&known:return None
        if any(p[k] in ('it','he','she','they','them','this','that') for p in patterns for k in ('subject','object')):
            return {'status':'needs-clarification','answer':'Which named entity do you mean? I have not guessed the pronoun reference.','model_calls':0}
        report=solve(old,patterns);report['source_question']=interpreted['original'];report['answer_mode']=interpreted['mode'];report['inference_status']=report['status']
        if interpreted['mode']=='count' and report['complete'] and report['status']!='conflicting-support':report['status']='counted'
        new=copy.deepcopy(old);new['last_report']=report;state['concept_conversation']=new
        return {'status':report['status'],'answer':render(report,new),'concept_reasoning':report,'model_calls':0,**({'count':len(report['answers'])} if interpreted['mode']=='count' else {})}
    if not explicit and not replacement and not (focused or fallback):return None
    # Bare questions always belong to another skill or its clarification path.
    if not explicit and not replacement and re.match(r'^(?:who|what|why|how|when|where|which|can|could|would|should|is|are|does|do)\b',key):return None
    content=explicit[1] if explicit else replacement[2] if replacement else text
    pieces=[part.strip().rstrip('.') for part in re.split(r'\n|;|(?<=[.!?])\s+',content) if part.strip()]
    if len(pieces)>16:raise ValueError('Add at most 16 discussion statements at a time')
    model=copy.deepcopy(old) if old else {'facts':[],'rules':[],'revision':0,'withdrawn':[]}
    additions=[]
    try:
        for part in pieces:
            parsed_rule=rule(part)
            additions.append(('rule',parsed_rule,part) if parsed_rule else ('fact',known_statement(part,model),part))
    except ValueError:
        if not explicit and not replacement:return None
        raise
    if replacement:
        if len(additions)!=1 or additions[0][0]!='fact':raise ValueError('Replace one fact with one explicit statement')
        ident=replacement[1].upper();prior=next((f for f in model['facts'] if f['source']==ident),None)
        if prior is None:raise ValueError('Choose an existing F-number from show discussion records')
        model['withdrawn']=(model['withdrawn']+[prior])[-32:];model['facts'].remove(prior)
        model['facts'].append({**additions[0][1],'source':ident,'text':additions[0][2]})
    else:
        for kind,record,original in additions:
            target=model['rules' if kind=='rule' else 'facts']
            ident=('R' if kind=='rule' else 'F')+str(max([int(r['source'][1:]) for r in target]+[0])+1)
            target.append({**record,'source':ident,'text':original})
    if len(model['facts'])>128 or len(model['rules'])>16:raise ValueError('Keep a discussion within 128 statements and 16 rules')
    model['revision']+=1;model.pop('last_report',None)
    if len(json.dumps(model))>64000:raise ValueError('Discussion exceeds its 64 KB workspace')
    # Validate rule bindings and fact syntax before committing any state.
    solve(model,[atom('?answer','is_a','__validation_probe__')])
    state['concept_conversation']=model;state['focus_kind']='concept-conversation'
    return {'status':'recorded','answer':'Recorded your supplied premises:\n\n'+'\n\n'.join(row['source']+': '+row['text'] for row in model['facts']+model['rules'])+'\n\nAsk a question about these premises. They are retained as your statements, not independently verified facts.','model_calls':0}
