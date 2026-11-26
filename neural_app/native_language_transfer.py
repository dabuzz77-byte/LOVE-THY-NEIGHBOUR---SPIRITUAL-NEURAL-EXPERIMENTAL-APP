"""Learn reviewable typed language mappings using checked native task results.

This learns symbolic request interpretations, not model weights or general world
knowledge. Built-in interpretations keep priority. No regex or code is supplied
by the learned mapping, and unvalidated/ambiguous matches never execute.
"""
import copy,hashlib,json,re,time
from fractions import Fraction

SLOT=re.compile(r'\{([a-z][a-z0-9_]{0,23}):(number|entity|json)\}')
PATTERNS={'number':r'[+-]?\d{1,12}(?:\.\d{1,8}|/\d{1,8})?',
          'entity':r'[\w][\w -]{0,79}?','json':r'[\s\S]{1,2048}'}

def starters():
    rows=[('starter_total','Gather the total from {items:json}','sum: {items}',
           [([2,3],5),([10,-4],6)],[([11,2,4],17),([0],0)]),
          ('starter_median','What is the median value of {items:json}','median: {items}',
           [([1,9,3],3),([2,4],3)],[([20,10,30],20),([-5,7,1,3],2)]),
          ('starter_distinct','Count unique entries in {items:json}','deduplicate then count: {items}',
           [([1,1,2],2),(['a','b','a'],2)],[([7,7,7],1),([],0)])]
    for name,source,target,training,validation in rows:
        render=lambda pair:{'input':source.replace('{items:json}',json.dumps(pair[0])),'expected':pair[1]}
        yield {'name':name,'source':source,'target':target,'training':[render(p) for p in training],'validation':[render(p) for p in validation]}

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def compile_template(source,target):
    if not all(isinstance(s,str) and 1<=len(s)<=600 for s in (source,target)):
        raise ValueError('Use source and target templates of 1–600 characters')
    slots=list(SLOT.finditer(source));names=[s[1] for s in slots]
    if not 1<=len(slots)<=3 or len(set(names))!=len(names):raise ValueError('Use 1–3 distinct typed slots: {name:number}, {name:entity} or {name:json}')
    if any(s[2]=='json' for s in slots) and len(slots)!=1:raise ValueError('A JSON slot must be the only slot in its source template')
    literals=[];previous=0;parts=[]
    for slot in slots:
        literal=source[previous:slot.start()]
        if previous and len(literal.strip())<2:raise ValueError('Separate typed slots with an explicit phrase or delimiter')
        literals.append(literal);parts.append(re.escape(literal));parts.append('(?P<'+slot[1]+'>'+PATTERNS[slot[2]]+')');previous=slot.end()
    parts.append(re.escape(source[previous:]))
    remainder=SLOT.sub('',source)
    if '{' in remainder or '}' in remainder:raise ValueError('Every source placeholder needs an explicit supported type')
    target_names=re.findall(r'\{([a-z][a-z0-9_]*)\}',target)
    if set(target_names)!=set(names) or any(target_names.count(n)!=1 for n in names):raise ValueError('Use each declared slot exactly once in the target template')
    if '{' in re.sub(r'\{[a-z][a-z0-9_]*\}','',target) or '}' in re.sub(r'\{[a-z][a-z0-9_]*\}','',target):raise ValueError('Use placeholders, rather than literal braces, in a learned target')
    if re.match(r'^(?:teach native phrasing|forget native phrasing|learned language)',target,re.I):raise ValueError('A learned target cannot define or manage language mappings')
    if not source[:slots[0].start()].strip():raise ValueError('A learned phrase needs a distinctive literal prefix before its slots')
    return re.compile(''.join(parts),re.I),{s[1]:s[2] for s in slots}

def translate(row,text):
    pattern,types=compile_template(row['source'],row['target'])
    match=pattern.fullmatch(text.strip())
    if not match:return None
    bindings={};rendered=row['target']
    for name,kind in types.items():
        raw=match[name].strip()
        if kind=='number':
            exact=Fraction(raw)
            if abs(exact)>10**12:raise ValueError('Number slot exceeds its supported magnitude')
            value=str(exact)
        elif kind=='json':
            data=json.loads(raw)
            if len(json.dumps(data,allow_nan=False))>4096:raise ValueError('JSON slot exceeds 4 KB')
            value=json.dumps(data,ensure_ascii=False,allow_nan=False)
        else:
            if not re.fullmatch(r'[\w][\w -]{0,79}',raw):raise ValueError('Entity slots contain only names, spaces, underscores and hyphens')
            value=raw
        bindings[name]={'type':kind,'value':value};rendered=rendered.replace('{'+name+'}',value)
    return {'request':rendered,'bindings':bindings}

def execute(row,text,work):
    mapped=translate(row,text)
    if mapped is None:raise ValueError('The example does not match the proposed source template')
    trial=type(work)(work.state);trial.state.pop('learned_native_phrases',None)
    # The optional scope is explicit and points only at a retained local workspace.
    if row.get('scope')=='concept-discussion':
        if not trial.state.get('concept_conversation'):raise ValueError('This phrase needs a retained concept discussion')
        trial.state['focus_kind']='concept-conversation'
    result=trial._handle_builtin(mapped['request'])
    if result is None:raise ValueError('The target does not resolve to a built-in native skill')
    return trial,result,mapped

def teach(body,work):
    if not isinstance(body,dict):raise ValueError('Provide a mapping name, source, target, training and validation cases')
    name=body.get('name');source=body.get('source');target=body.get('target');scope=body.get('scope','work')
    if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,39}',name):raise ValueError('Use a short lower-case identifier for the mapping name')
    if scope not in ('work','concept-discussion'):raise ValueError('Choose work or concept-discussion scope')
    compile_template(source,target)
    training=body.get('training');validation=body.get('validation')
    if not all(isinstance(rows,list) and 2<=len(rows)<=8 for rows in (training,validation)):
        raise ValueError('Provide 2–8 training cases and 2–8 separate validation cases')
    row={'name':name,'source':source,'target':target,'scope':scope};seen=set();seen_bindings=set();checks=[];deadline=time.monotonic()+2
    from .shared_controller import outcome,succeeded
    from .workflow_contracts import equivalent
    for split,cases in (('training',training),('validation',validation)):
        for case in cases:
            if time.monotonic()>deadline:raise ValueError('Language validation time budget reached')
            if not isinstance(case,dict) or not isinstance(case.get('input'),str) or len(case['input'])>2500 or 'expected' not in case:
                raise ValueError('Each case needs a bounded input string and an expected JSON value')
            signature=digest(case['input'].strip().casefold())
            if signature in seen:raise ValueError('Training and validation inputs must all be distinct')
            seen.add(signature)
            trial,result,mapped=execute(row,case['input'],work)
            normalised={name:{'type':v['type'],'value':json.loads(v['value']) if v['type']=='json' else v['value'].casefold() if v['type']=='entity' else v['value']} for name,v in mapped['bindings'].items()}
            binding_signature=digest(normalised)
            if binding_signature in seen_bindings:raise ValueError('Validation must use different slot values, not just reformatted versions of training inputs')
            seen_bindings.add(binding_signature)
            actual=outcome(result)
            if not succeeded(result) or not equivalent(actual,case['expected']):raise ValueError('The proposed interpretation failed a '+split+' case; nothing was learned')
            checks.append({'split':split,'input_sha256':signature,'bindings_sha256':binding_signature,'target_request':mapped['request'],'actual_sha256':digest(actual),'expected_sha256':digest(case['expected']),'passed':True})
    row.update(checks=checks,trained_cases=len(training),validation_cases=len(validation),active=True)
    row['receipt_sha256']=digest(row)
    library=copy.deepcopy(work.state.get('learned_native_phrases',{}))
    if name in library:raise ValueError('Forget the existing named mapping before replacing it')
    if len(library)>=24:raise ValueError('Keep at most 24 reviewed native phrase mappings')
    library[name]=row
    work.state['learned_native_phrases']=library
    return {'status':'complete','answer':'Learned the native interpretation “'+name+'” after '+str(len(training))+' training and '+str(len(validation))+' separate validation checks. It can now interpret matching new inputs without an LLM call. This validates the supplied cases, not every possible meaning.','language_learning':copy.deepcopy(row),'model_calls':0}

def command(text,work):
    if text.casefold().startswith('teach native phrasing:'):return teach(json.loads(text.split(':',1)[1]),work)
    key=text.strip().casefold().rstrip('?.!')
    if key=='show learned native phrasings':
        library=work.state.get('learned_native_phrases',{})
        return {'status':'complete','answer':'\n\n'.join(r['name']+': '+r['source']+' → '+r['target'] for r in library.values()) or 'No reviewed native phrase mappings have been learned yet.','model_calls':0}
    match=re.fullmatch(r'forget native phrasing ([a-z][a-z0-9_-]{0,39})',key)
    if match:
        updated=copy.deepcopy(work.state.get('learned_native_phrases',{}));existed=updated.pop(match[1],None) is not None
        work.state['learned_native_phrases']=updated
        if match[1].startswith('starter_'):
            work.state['suppressed_native_starters']=list(set(work.state.get('suppressed_native_starters',[]))|{match[1]})
        return {'status':'complete','answer':('Forgot ' if existed else 'No mapping named ')+match[1]+'.','model_calls':0}
    return None

def apply(text,work):
    if len(text)>2500:return None
    matches=[]
    for name,row in work.state.get('learned_native_phrases',{}).items():
        if row.get('receipt_sha256')!=digest({k:v for k,v in row.items() if k!='receipt_sha256'}):raise ValueError('A learned phrase differs from its validation receipt; forget and retrain it')
        try:mapped=translate(row,text)
        except (ValueError,ZeroDivisionError) as exc:
            return {'status':'needs-input','answer':'The learned phrase '+name+' matches, but its input needs correction: '+str(exc)[:250]+'. Nothing ran.','model_calls':0}
        if mapped:matches.append((row,mapped))
    if not matches:
        for body in starters():
            if body['name'] in work.state.get('suppressed_native_starters',[]):continue
            if body['name'] in work.state.get('learned_native_phrases',{}):continue
            try:mapped=translate(body,text)
            except (ValueError,ZeroDivisionError) as exc:
                return {'status':'needs-input','answer':'This phrase matches a native lesson, but its input needs correction: '+str(exc)[:250]+'. Nothing ran.','model_calls':0}
            if mapped:
                teach(body,work)
                return apply(text,work)
        return None
    if len({m['request'] for _,m in matches})!=1:
        return {'status':'needs-clarification','answer':'This wording matches conflicting learned interpretations: '+', '.join(r['name'] for r,_ in matches)+'. Use an explicit native request or forget one mapping. Nothing ran.','model_calls':0}
    row,mapped=matches[0]
    trial,result,mapped=execute(row,text,work)
    from .shared_controller import succeeded
    completed_question='concept_reasoning' in result and result['concept_reasoning'].get('complete') is True
    if succeeded(result) or completed_question:
        # Keep the verified library; execution uses a trial copy without recursive mappings.
        library=copy.deepcopy(work.state['learned_native_phrases']);work.state.clear();work.state.update(trial.state);work.state['learned_native_phrases']=library
    return {**result,'learned_interpretation':{'name':row['name'],'canonical_request':mapped['request'],'bindings':mapped['bindings'],'validation_receipt':row['receipt_sha256']},'model_calls':0}

def engine_bridge(text,state,command_only=False):
    from .native_work import NativeWork
    saved=copy.deepcopy(state.get('native_tasks',{}))
    fields=('learned_native_phrases','suppressed_native_starters','learned_relation_models','concept_conversation','focus_kind','last','previous','has_last')
    for field in fields:
        if field in state:saved[field]=copy.deepcopy(state[field])
    work=NativeWork(saved);result=command(text,work) if command_only else apply(text,work)
    if result is not None:
        state['native_tasks']=copy.deepcopy(work.state)
        for field in fields:
            if field in work.state:state[field]=copy.deepcopy(work.state[field])
    return result
