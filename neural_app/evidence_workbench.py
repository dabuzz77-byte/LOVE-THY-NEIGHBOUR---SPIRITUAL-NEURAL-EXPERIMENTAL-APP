"""Bounded, source-grounded research conversations; no model or network calls.

Extractive answers preserve the supplied wording. Agreement is not truth, and
duplicate passages never count as independent corroboration.
"""
import copy, hashlib, json, re
from fractions import Fraction
from urllib.parse import urlsplit

STOP = set('a an the is are was were be been of to for in on and or it this that what which how why does do can could should would with from about please tell me explain summarise summarize'.split())

def tokens(text):
    return set(re.findall(r"[\w]+", text.casefold())) - STOP

def short(value, limit, name):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{name} must contain 1–{limit} characters')
    return value.strip()

def prepare(body):
    if not isinstance(body, dict):
        raise ValueError('Provide a research question and a sources list')
    question = short(body.get('question'), 1000, 'Question')
    rows = body.get('sources')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
        raise ValueError('Supply 1–16 source passages')
    sources, ids, seen = [], set(), {}
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError('Each source needs text and an optional id/title/url/date')
        ident = short(row.get('id', f'S{index+1}'), 40, 'Source id')
        if not re.fullmatch(r'[\w-]+', ident) or ident in ids:
            raise ValueError('Source ids must be distinct letters, digits, underscores or hyphens')
        ids.add(ident)
        text = short(row.get('text'), 10000, 'Source text')
        total += len(text)
        if total > 60000:
            raise ValueError('Keep the research packet below 60,000 source characters')
        url = row.get('url', '')
        if not isinstance(url, str) or len(url) > 1500:
            raise ValueError('Use a bounded source URL')
        if url:
            parsed = urlsplit(url)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Source references must use HTTP(S) without embedded credentials')
        digest = hashlib.sha256(re.sub(r'\s+', ' ', text.casefold()).encode()).hexdigest()
        record = {'id': ident, 'title': short(row.get('title', ident), 240, 'Source title'),
                  'text': text, 'url': url, 'date': str(row.get('date', 'undated'))[:80],
                  'sha256': digest, 'duplicate_of': seen.get(digest)}
        seen.setdefault(digest, ident)
        sources.append(record)
    packet={'question': question, 'sources': sources, 'revision': 1, 'history': []}
    if 'hypotheses' in body:
        from .diagnostic_reasoning import diagnose
        model={'hypotheses':copy.deepcopy(body['hypotheses']),'observations':copy.deepcopy(body.get('observations',{}))}
        diagnose(model)  # Validate before storing or changing conversation state.
        packet['diagnostic_model']=model
    return packet

def sentences(packet):
    rows = []
    for source in packet['sources']:
        # Decimal points, URL punctuation and abbreviations do not split on their own.
        for index, match in enumerate(re.finditer(r'[^\n]+', source['text'])):
            line = match.group()
            for part in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', line):
                if part.strip():
                    start = source['text'].find(part, match.start())
                    rows.append({'source': source['id'], 'text': part.strip(), 'line': index+1,
                                 'start': start, 'end': start+len(part),
                                 'duplicate_source': source['duplicate_of']})
    return rows

def conflicts(rows):
    """Flag matching explicit subject/predicate assertions, not arbitrary disagreement."""
    groups = {}
    for row in rows:
        for part in re.split(r';\s*', row['text'].rstrip('.!?')):
            match = re.fullmatch(r'(.+?)\s+(is|are|was|were|has|have)\s+(not\s+)?(.+)', part, re.I)
            if not match:
                continue
            subject, verb, neg, predicate = match.groups()
            # A hedge is not an unconditional assertion.
            if re.search(r'\b(may|might|could|perhaps|reportedly|estimated|if)\b', part, re.I):
                continue
            key = (subject.casefold().strip(), verb.casefold(), predicate.casefold().strip())
            groups.setdefault(key, {False: [], True: []})[bool(neg)].append(row)
    result = []
    for key, signs in groups.items():
        if signs[False] and signs[True]:
            result.append({'kind': 'explicit-negation', 'subject': key[0],
                           'statements': signs[False]+signs[True]})
    # Same explicitly labelled numeric measurement, differing reported values.
    numeric = {}
    for row in rows:
        match = re.fullmatch(r'(.+?)\s+(?:is|was|equals|=)\s+([+-]?\d+(?:\.\d+)?)\s*([^\d]*?)\.?', row['text'], re.I)
        if match:
            name, value, unit = match.groups()
            numeric.setdefault((name.casefold().strip(), unit.casefold().strip().rstrip('.')), []).append((value, row))
    for (name, unit), values in numeric.items():
        if len({Fraction(v) for v, _ in values}) > 1:
            result.append({'kind': 'different-reported-values', 'subject': name, 'unit': unit,
                           'statements': [r for _, r in values]})
    return result

def analyse(packet, question=None):
    question = question or packet['question']
    query = tokens(question)
    rows = sentences(packet)
    ranked = []
    for row in rows:
        overlap = query & tokens(row['text'])
        if overlap and not row['duplicate_source']:
            ranked.append((len(overlap)/max(1, len(query)), len(overlap), row))
    ranked.sort(key=lambda item: (-item[0], -item[1], len(item[2]['text']), item[2]['source']))
    selected, seen = [], set()
    for _, _, row in ranked:
        normal = re.sub(r'\s+', ' ', row['text'].casefold())
        if normal not in seen:
            selected.append(row); seen.add(normal)
        if len(selected) == 6:
            break
    disagreements = conflicts(rows)
    relevant_conflicts = [c for c in disagreements if query & tokens(c['subject']) or
                          any(query & tokens(r['text']) for r in c['statements'])]
    deduction = None
    if sum(len(s['text']) for s in packet['sources']) <= 16000:
        from .source_reasoning import read
        try:
            deduction = read({'question':question,'sources':[{'source':s['id'],'text':s['text']} for s in packet['sources'] if not s['duplicate_of']]})
        except ValueError:
            pass
    status = 'conflicting-evidence' if relevant_conflicts else ('evidence-found' if selected else 'needs-evidence')
    if deduction and deduction.get('status')=='conflicting-support':status='conflicting-evidence'
    diagnostic=None
    if packet.get('diagnostic_model'):
        from .diagnostic_reasoning import diagnose
        diagnostic=diagnose(packet['diagnostic_model'])
    return {'status': status, 'question': question, 'passages': selected, 'diagnostic':diagnostic,
            'conflicts': relevant_conflicts, 'deduction':deduction, 'sources': [{k: r[k] for k in ('id','title','url','date','sha256','duplicate_of')} for r in packet['sources']],
            'method': 'Extractive lexical retrieval with exact passage references; no semantic truth verification.',
            'next_checks': ['Check the original source and its date, population and measurement definitions.',
                            'Resolve explicit conflicts before choosing a factual conclusion.',
                            'Find independent evidence and an observation that could disprove the working explanation.'],
            'model_calls': 0}

def render(report, compact=False):
    lines = [f"**Research: {report['question']}**"]
    if report['status'] == 'needs-evidence':
        lines.append('The retained passages do not supply matching evidence for that question.')
    else:
        lines.append('Relevant supplied passages:')
        for row in report['passages'][:2 if compact else 6]:
            lines.append(f"- [{row['source']}, line {row['line']}] {row['text']}")
    if report['conflicts']:
        lines.append('**Unresolved evidence conflicts:**')
        for conflict in report['conflicts']:
            lines.append('- '+conflict['subject']+': '+' / '.join('['+r['source']+'] '+r['text'] for r in conflict['statements']))
    deduction=report.get('deduction')
    if deduction and (deduction.get('answers') or deduction.get('counter_supporting_fact_ids')):
        lines.append('**Consequences under the parsed source statements:**')
        for answer in deduction.get('answers',[]):
            values=', '.join(answer['bindings'].values()) or 'The queried statement has explicit support.'
            lines.append('- '+values+(' Support is conflicted.' if answer.get('has_conflicted_support') else ''))
        if deduction.get('counter_supporting_fact_ids'):lines.append('The sources also explicitly support the opposite of the queried statement.')
        if not deduction.get('complete'):lines.append('Some wording was not parsed; this remains a partial source analysis.')
        source_ids={s['source'] for p in deduction.get('proof_graph',[]) for s in p.get('given_sources',[])}
        used_rules={p['proof']['rule'] for p in deduction.get('proof_graph',[]) if p.get('proof',{}).get('kind')=='derived'}
        source_ids=sorted(source_ids|{r['source'] for r in deduction.get('source_rules',[]) if r['rule'] in used_rules})
        if source_ids:lines.append('Support: '+', '.join(source_ids))
    lines.append('These are attributed source statements, not a verified consensus or a causal finding.')
    diagnostic=report.get('diagnostic')
    if diagnostic:
        lines.append('**Competing explanations:** '+(', '.join(diagnostic['remaining']) or 'none matches the supplied observations')+'.')
        lines.append(diagnostic['next_step'])
        lines.append('These predictions were supplied explicitly; no source-to-hypothesis mapping or causal certainty was invented.')
    return '\n\n'.join(lines)

def respond(text, state):
    key = text.strip().casefold().rstrip('?.!')
    match = re.match(r'^(?:research brief|review evidence|analyse evidence|analyze evidence):\s*', text, re.I)
    packet = state.get('evidence_packet')
    if match:
        body = text[match.end():]
        if body.lstrip().startswith('{'):
            new = prepare(json.loads(body))
        else:
            parts = re.split(r'\nSource\s+([\w-]+)\s*:\s*', body, flags=re.I)
            if len(parts) < 3:
                return {'status':'needs-input', 'answer':'Supply a question followed by source passages, for example:\nresearch brief: Does rain affect output?\nSource A: Rain reduces output in this report.\nSource B: Output also depends on temperature.', 'model_calls':0}
            new = prepare({'question':parts[0], 'sources':[{'id':parts[i], 'text':parts[i+1]} for i in range(1,len(parts),2)]})
    elif packet and re.match(r'^add source\s+([\w-]+)\s*:', text, re.I):
        match = re.match(r'^add source\s+([\w-]+)\s*:\s*([\s\S]+)', text, re.I)
        new = prepare({'question':packet['question'], 'sources':packet['sources']+[{'id':match[1], 'text':match[2]}]})
        if packet.get('diagnostic_model'):new['diagnostic_model']=copy.deepcopy(packet['diagnostic_model'])
        new['revision'] = packet['revision']+1
        new['history'] = (packet.get('history', [])+[{'revision':packet['revision'], 'source_count':len(packet['sources']), 'status':state['evidence_report']['status']}])[-16:]
    elif packet and state.get('focus_kind') == 'evidence-research':
        observation=re.fullmatch(r'research observation:\s*([^=\n]{1,120})\s*=\s*(.+)',text,re.I|re.S)
        if observation:
            if not packet.get('diagnostic_model'):raise ValueError('Supply explicit hypotheses and their predicted observations in the research packet first')
            new=copy.deepcopy(packet);new['diagnostic_model']['observations'][observation[1].strip()]=json.loads(observation[2])
            report=analyse(new);new['revision']+=1
            state['evidence_packet'],state['evidence_report']=new,report
            return {'status':report['status'],'answer':render(report),'research':report,'model_calls':0}
        if key in ('show sources','show research sources','sources'):
            return {'status':'complete','answer':'\n\n'.join('['+s['id']+'] '+s['title']+' · '+s['date']+' · '+(s['url'] or 'supplied text')+(' · duplicate of '+s['duplicate_of'] if s['duplicate_of'] else '') for s in packet['sources']), 'model_calls':0}
        if key in ('what would change your conclusion','what evidence is missing','what should we check next'):
            return {'status':'complete','answer':'\n\n'.join(state['evidence_report']['next_checks']), 'model_calls':0}
        if key in ('what changed','what changed in the evidence'):
            return {'status':'complete','answer':f"Research revision {packet['revision']}: {len(packet['sources'])} sources; status {state['evidence_report']['status']}.\n"+json.dumps(packet.get('history',[])), 'model_calls':0}
        if key in ('summarize that','summarise that','make that shorter','explain research','explain evidence','show evidence'):
            return {'status':state['evidence_report']['status'],'answer':render(state['evidence_report'],True),'model_calls':0}
        follow = re.match(r'^(?:what about|ask sources|ask the sources|research followup)\s*:?\s+(.+)',text,re.I|re.S)
        if not follow:
            from .open_reasoning import source_followup
            if not source_followup({'facts':[s['text'] for s in packet['sources']],'evidence':[]},text):return None
            follow=re.match(r'([\s\S]+)',text)
        new = copy.deepcopy(packet)
        new['question'] = short(follow[1],1000,'Question')
    else:
        return None
    report = analyse(new)
    state['evidence_packet'], state['evidence_report'], state['focus_kind'] = new, report, 'evidence-research'
    return {'status':report['status'],'answer':render(report),'research':report,'model_calls':0}
