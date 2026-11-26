"""Finite native Horn-rule induction with explicit counterexamples and validation.

Discovers one/two-premise relational patterns rather than requiring a supplied
rule. Predictions remain model-relative. No model, network, code or host action.
"""
import copy,hashlib,json,re,time

def label(value):
    if not isinstance(value,str) or not value.strip() or len(value)>80 or '\n' in value or value.startswith('?'):raise ValueError('Use named relation labels of 1–80 characters')
    return ' '.join(value.casefold().split())

def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()

def facts(raw,target):
    if not isinstance(raw,list) or not 1<=len(raw)<=128:raise ValueError('Provide 1–128 background relation triples')
    result=[]
    for row in raw:
        if not isinstance(row,(list,tuple)) or len(row)!=3:raise ValueError('Each background fact is [subject, relation, object]')
        parsed=tuple(label(v) for v in row)
        if parsed[1]==target:raise ValueError('Target-relation labels cannot appear in the background facts')
        if parsed not in result:result.append(parsed)
    return result

def examples(raw,minimum=1):
    if not isinstance(raw,list) or not minimum<=len(raw)<=16:raise ValueError('Provide '+str(minimum)+'–16 examples as [subject, object] pairs')
    rows=[]
    for row in raw:
        if not isinstance(row,list) or len(row)!=2:raise ValueError('Examples must be [subject, object] pairs')
        pair=tuple(label(v) for v in row)
        if pair in rows:raise ValueError('Example pairs must be distinct')
        rows.append(pair)
    return rows

def candidates(background,positive,constant):
    actor,obj=positive;direct=[f for f in background if f[0]==actor];other=[f for f in background if f[0]==obj];rules=set()
    head_vars={'?x'} if constant is not None else {'?x','?y'}
    def add(atoms):
        body=tuple(sorted(atoms));bound={v for atom in body for v in (atom[0],atom[2]) if v.startswith('?')}
        if head_vars<=bound:rules.add(body)
    for a in direct:
        add((('?x',a[1],'?y' if a[2]==obj and constant is None else a[2]),))
        for b in background:
            if b[0]!=a[2]:continue
            add((('?x',a[1],'?z'),('?z',b[1],'?y' if b[2]==obj and constant is None else b[2])))
    if constant is None:
        for a in direct:
            for b in other:add((('?x',a[1],a[2]),('?y',b[1],b[2])))
    if len(rules)>256:raise ValueError('Candidate space is too large; use a smaller, more relevant background')
    return sorted(rules,key=lambda r:(len(r),r))

def derive(body,background,constant,deadline):
    by_relation={}
    for index,row in enumerate(background):by_relation.setdefault(row[1],[]).append((index,row))
    bindings=[({},())];operations=0
    for pattern in body:
        following=[]
        for known,support in bindings:
            for index,row in by_relation.get(pattern[1],[]):
                operations+=1
                if operations>25000 or time.monotonic()>deadline:raise ValueError('Relational search budget reached; reduce the background or candidate ambiguity')
                update=dict(known);valid=True
                for expected,actual in zip(pattern,row):
                    if expected.startswith('?'):
                        if expected in update and update[expected]!=actual:valid=False;break
                        update[expected]=actual
                    elif expected!=actual:valid=False;break
                if valid:following.append((update,support+(index+1,)))
        bindings=following
        if len(bindings)>4096:raise ValueError('Relational join exceeds 4096 bindings')
    output={}
    for bound,support in bindings:
        pair=(bound['?x'],constant if constant is not None else bound['?y'])
        output.setdefault(pair,list(support))
    return output

def case_checks(rules,background,constant,positive,negative,deadline):
    results=[]
    for rule in rules:
        predicted=derive(rule,background,constant,deadline)
        results.append({'positive_passed':sum(p in predicted for p in positive),'negative_passed':sum(p not in predicted for p in negative),
                        'passed':all(p in predicted for p in positive) and all(p not in predicted for p in negative)})
    return results

def learn(body):
    if not isinstance(body,dict):raise ValueError('Provide name, target, facts, positive, negative and validation examples')
    name=body.get('name');target=label(body.get('target'))
    if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,39}',name):raise ValueError('Use a short lower-case model name')
    background=facts(body.get('facts'),target);positive=examples(body.get('positive'),2);negative=examples(body.get('negative'))
    if set(positive)&set(negative):raise ValueError('A pair cannot be labelled both positive and negative')
    validation=body.get('validation')
    if not isinstance(validation,list) or not 2<=len(validation)<=16:raise ValueError('Provide 2–16 separate validation examples with expected true/false labels')
    vp=[];vn=[];seen=set(positive+negative)
    for row in validation:
        if not isinstance(row,dict) or type(row.get('expected'))is not bool:raise ValueError('Each validation example needs subject, object and expected boolean')
        pair=(label(row.get('subject')),label(row.get('object')))
        if pair in seen:raise ValueError('Validation pairs must be distinct and separate from training pairs')
        seen.add(pair);(vp if row['expected'] else vn).append(pair)
    if not vp or not vn:raise ValueError('Validation must include both a positive and a negative example')
    objects={p[1] for p in positive};constant=next(iter(objects)) if len(objects)==1 else None
    deadline=time.monotonic()+1.5;hypotheses=candidates(background,positive[0],constant);retained=[]
    for candidate in hypotheses:
        predicted=derive(candidate,background,constant,deadline)
        if all(p in predicted for p in positive) and all(p not in predicted for p in negative):retained.append(candidate)
    if not retained:raise ValueError('No one/two-premise pattern fits the supplied positive and negative examples')
    if len(retained)>64:raise ValueError('More than 64 patterns remain consistent; supply distinguishing negative examples')
    # Freeze the candidates from training before checking validation. Do not fit to it.
    checks=case_checks(retained,background,constant,vp,vn,deadline)
    if not all(r['passed'] for r in checks):raise ValueError('A training-consistent pattern failed separate validation; provide distinguishing training examples and fresh validation')
    result={'name':name,'target':target,'facts':[list(f) for f in background],'constant_object':constant,
            'rules':[[list(atom) for atom in rule] for rule in retained], 'positive':[list(p) for p in positive],'negative':[list(p) for p in negative],
            'validation_positive':[list(p) for p in vp],'validation_negative':[list(p) for p in vn],
            'validation_checks':checks,'active':True,'revision':1,'counterexamples':[],
            'scope':'Finite one/two-premise relational pattern induction under supplied labelled examples. Validation is locally supplied, not independent scientific proof. Predictions are model-relative, not universal facts or authority for external action.'}
    result['receipt_sha256']=fingerprint(result);return result

def review(model):
    if model.get('receipt_sha256')!=fingerprint({k:v for k,v in model.items() if k!='receipt_sha256'}):raise ValueError('Model differs from its checked receipt; train it again')

def predict(model,subject,obj):
    review(model)
    if not model['active']:raise ValueError('This model has an unresolved counterexample; retrain it with fresh validation')
    subject,obj=label(subject),label(obj);known={f[0] for f in model['facts']}
    if subject not in known:return {'status':'needs-observations','subject':subject,'object':obj,'prediction':None,'answer':'Supply background observations for '+subject+' before making a prediction.'}
    deadline=time.monotonic()+.5;votes=[]
    for i,rule in enumerate(model['rules'],1):
        derived=derive(rule,model['facts'],model['constant_object'],deadline)
        votes.append({'rule':i,'predicts_relation':(subject,obj) in derived,'support_fact_ids':derived.get((subject,obj),[])})
    values={v['predicts_relation'] for v in votes};prediction=next(iter(values)) if len(values)==1 else None
    answer='The reviewed patterns disagree on this new case. Supply a distinguishing observation.' if prediction is None else ('All reviewed patterns derive this relation from the supplied background.' if prediction else 'The reviewed patterns do not derive this relation from the supplied background; this is not proof that it is false in the world.')
    return {'status':'model-prediction' if prediction is not None else 'ambiguous-prediction','subject':subject,'object':obj,'prediction':prediction,'votes':votes,'answer':answer,'model_scope':model['scope'],'model_calls':0}

def respond(text,state):
    if text.casefold().startswith('learn relation model:'):
        model=learn(json.loads(text.split(':',1)[1]));models=copy.deepcopy(state.get('learned_relation_models',{}))
        if model['name'] in models:raise ValueError('Choose a new model name for a revised lesson so its history remains explicit')
        if len(models)>=12:raise ValueError('Keep at most 12 reviewed relation models')
        models[model['name']]=model
        if len(json.dumps(models))>160000:raise ValueError('Reviewed relation models exceed 160 KB; forget a selected model before adding another')
        state['learned_relation_models']=models
        return {'status':'complete','answer':'Discovered '+str(len(model['rules']))+' training-consistent relational patterns. Every retained pattern passed the separate validation cases. Use predict relation '+model['name']+': SUBJECT | OBJECT.\n\n'+model['scope'],'relation_model':copy.deepcopy(model),'model_calls':0}
    key=text.strip().casefold()
    if key=='list relation models':return {'status':'complete','answer':'\n'.join(name+' — '+('active' if row['active'] else 'counterexample; inactive') for name,row in state.get('learned_relation_models',{}).items()) or 'No relation models have been learned.','model_calls':0}
    forget=re.fullmatch(r'forget relation model ([a-z][a-z0-9_-]{0,39})',key)
    if forget:
        models=copy.deepcopy(state.get('learned_relation_models',{}));existed=models.pop(forget[1],None) is not None;state['learned_relation_models']=models
        return {'status':'complete','answer':('Forgot ' if existed else 'No model named ')+forget[1]+'.','model_calls':0}
    match=re.fullmatch(r'(predict relation|check relation|add relation facts|show relation model) ([a-z][a-z0-9_-]{0,39})(?::\s*([\s\S]+))?',text,re.I)
    if not match:return None
    operation,name,payload=match.groups();name=name.casefold();model=copy.deepcopy(state.get('learned_relation_models',{}).get(name))
    if not model:raise ValueError('No learned relation model has that name')
    review(model)
    if operation.casefold()=='show relation model':return {'status':'complete','answer':json.dumps(model,ensure_ascii=False,indent=2),'relation_model':model,'model_calls':0}
    if payload is None:raise ValueError('Provide the case or new background facts after a colon')
    if operation.casefold()=='predict relation':
        pair=payload.split('|')
        if len(pair)!=2:raise ValueError('Use SUBJECT | OBJECT for a prediction')
        result=predict(model,*pair);return {**result,'answer':result['answer']+'\n\n'+model['scope'],'relation_prediction':copy.deepcopy(result),'model_calls':0}
    if operation.casefold()=='check relation':
        body=json.loads(payload)
        if not isinstance(body,dict) or type(body.get('expected'))is not bool:raise ValueError('Supply subject, object and an observed expected boolean')
        result=predict(model,body.get('subject'),body.get('object'))
        if result['prediction'] is None and result['status']=='needs-observations':return {**result,'model_active':model['active'],'model_calls':0}
        passed=result['prediction'] is not None and result['prediction']==body['expected']
        if not passed:
            model['active']=False;model['counterexamples']=(model['counterexamples']+[{'subject':body['subject'],'object':body['object'],'observed':body['expected'],'prediction':result['prediction']}])[-16:]
        result={'status':'check-passed' if passed else 'needs-refinement' if result['prediction'] is None else 'counterexample','passed':passed,'observed':body['expected'],'prediction':result['prediction'],'model_active':model['active']}
    else:
        added=facts(json.loads(payload),model['target']);model['facts']=[list(f) for f in facts(model['facts']+added,model['target'])]
        checks=case_checks(model['rules'],model['facts'],model['constant_object'],[tuple(p) for p in model['positive']+model['validation_positive']],[tuple(p) for p in model['negative']+model['validation_negative']],time.monotonic()+.75)
        if not all(r['passed'] for r in checks):model['active']=False;model['counterexamples']=(model['counterexamples']+[{'kind':'background-update-invalidated-retained-checks'}])[-16:]
        result={'status':'background-updated','model_active':model['active'],'retained_checks_passed':all(r['passed'] for r in checks)}
    model['revision']+=1;model.pop('receipt_sha256');model['receipt_sha256']=fingerprint(model)
    state['learned_relation_models']={**state['learned_relation_models'],name:model}
    return {**result,'answer':json.dumps(result,ensure_ascii=False)+'\n\n'+model['scope'],'model_calls':0}
