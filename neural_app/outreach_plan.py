"""Need-first, consent-aware planning for a finite public-intent packet budget."""
import json
import math
from .intent_packet import prepare_intent

DEFAULT_INTENT='Support voluntary learning, privacy, autonomy and practical care, prioritising people with the fewest resources and greatest unmet needs.'


def unit(value,name):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:raise ValueError(name+' must be finite from 0 to 1')
    return float(value)


def plan_outreach(body):
    from .outreach_evidence import context
    evidence_context=context(body)
    # Optional proposal review is separate from recipient permission. Passing
    # this gate never supplies consent, reachability or delivery evidence.
    action_review=None
    if 'action_candidates' in body:
        from .gnostic_four import decide
        action_review=decide({'candidates':body['action_candidates'],
                              'budget':body.get('action_budget',3)})
    intent=prepare_intent(body.get('intent',DEFAULT_INTENT))
    budget=body.get('byte_budget',2048)
    if type(budget) is not int or not 0<=budget<=1048576:raise ValueError('Use a planning budget from 0 to 1048576 bytes')
    nodes=body.get('nodes',[])
    if not isinstance(nodes,list) or not 1<=len(nodes)<=64:raise ValueError('Provide 1–64 explicitly described participant nodes')
    envelope={'format':'neural-public-intent-v1','text':intent['text'],'sha256':intent['sha256'],'direction':'Care first for greatest unmet need; voluntary participation.'}
    packet_bytes=len(json.dumps(envelope,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
    checked=[];ids=set()
    for n in nodes:
        if not isinstance(n,dict):raise ValueError('Node must be an object')
        ident=n.get('id')
        if not isinstance(ident,str) or not 1<=len(ident)<=64 or ident in ids:raise ValueError('Use unique short node IDs')
        ids.add(ident)
        for k in ['consent','reachable','offline_handoff']:
            if type(n.get(k,False)) is not bool:raise ValueError(k+' must be boolean')
        need=unit(n.get('need',.5),'need');urgency=unit(n.get('urgency',.5),'urgency');access=unit(n.get('existing_access',.5),'existing_access')
        checked.append({'id':ident,'need':need,'urgency':urgency,'existing_access':access,
                        'priority':need*(.5+.5*urgency)*(1-.75*access),'consent':n.get('consent',False),
                        'route':'configured live peer' if n.get('reachable',False) else 'voluntary offline handoff' if n.get('offline_handoff',False) else None})
    remaining=budget
    for row in sorted(checked,key=lambda n:(-n['priority'],n['id'])):
        if action_review is not None and action_review['selected'] is None:row.update(status='AWAITING_ACTION_REVIEW',planned_bytes=0)
        elif not row['consent']:row.update(status='AWAITING_CONSENT',planned_bytes=0)
        elif not row['route']:row.update(status='AWAITING_CONNECTION',planned_bytes=0)
        elif remaining<packet_bytes:row.update(status='DEFERRED_CAPACITY',planned_bytes=0)
        else:row.update(status='READY_TO_SHARE',planned_bytes=packet_bytes);remaining-=packet_bytes
    return {'status':'COMPLETE','module':'humane-network-outreach','intent':envelope,'packet_bytes':packet_bytes,
            'byte_budget':budget,'planned_bytes':budget-remaining,'remaining_bytes':remaining,
            'priority_order':[n['id'] for n in sorted(checked,key=lambda n:(-n['priority'],n['id']))],
            'nodes':checked,'ready':sum(n['status']=='READY_TO_SHARE' for n in checked),'sent':0,
            'evidence_context':evidence_context,
            'action_review':action_review,
            'constructive_counters':({key:message for key,message in {
                'truthful':'Explain the teaching, costs and actual delivery status.',
                'non_harm':'Replace threats or coercion with protective, voluntary learning.',
                'consent':'Use an existing permitted invitation channel and a separate subscription choice.',
                'privacy':'Minimise recipient data and omit private source text.',
                'fairness':'Prioritise declared unmet need without identity-based guilt.',
                'repairable':'Provide pause, leave, revocation and correction.',
                'reviewed':'Review content and outcomes with willing participants.'}.items()
                if any(key in reason for action in action_review['actions'] for reason in action['reasons'])}
                if action_review else {}),
            'formula':'need × (0.5 + 0.5 × urgency) × (1 − 0.75 × existing access)',
            'transition_plan':['Identify essential needs and current access through voluntary reports.',
                               'Count volunteered bandwidth, hosting, energy, maintenance and contributor capacity.',
                               'Use open code, compact packets, caching, shared infrastructure and offline handoffs.',
                               'Prioritise greater unmet need, preserve consent and record actual delivery separately.',
                               'Review outcomes, replenish capacity and expand only where the approach works.'],
            'scope':'Public-intent distribution plan only. Byte counts describe the serialized application packet, excluding network overhead. Readiness is based on entered declarations; delivery is not performed or verified. No funds, credits, private compute or device access are transferred.'}
