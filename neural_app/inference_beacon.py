"""Portable inference advertisements and explicit, bounded route planning."""
import hashlib
import heapq
import json

TERMS = {
    'inference': 'Deriving an output from inputs using an identified model or rule; an output is not automatically true.',
    'post': 'An individual inference work item with a request digest, requested capability and destination.',
    'beacon': 'A portable advertisement of a node’s declared capabilities and protocol. It does not discover or contact devices by itself.',
    'gateway': 'An explicit boundary that checks allowed requests and permissions before crossing between nodes or systems.',
    'bridge': 'A declared directed connection that translates or carries a compatible request between two nodes.',
    'mesh': 'A graph of participating nodes with multiple possible bridges; membership is explicitly configured.',
    'network': 'The overall collection of participating nodes, links and agreed protocols.',
    'hyperpathway': 'This app’s term for a capability-compatible, permission-checked multi-hop route, bounded by a hop limit; not a physical extra dimension.',
}

DEFAULT_TOPOLOGY = {'nodes': [{'id': 'local', 'capabilities': ['inference'], 'enabled': True}], 'bridges': []}


def resolve(body):
    text = body.get('text', '')
    if not isinstance(text, str) or not text.strip() or len(text.encode('utf-8')) > 4096:
        raise ValueError('Enter 1–4096 UTF-8 bytes of request text')
    topology = body.get('topology', DEFAULT_TOPOLOGY)
    if not isinstance(topology, dict): raise ValueError('Topology must be an object')
    nodes, bridges = topology.get('nodes'), topology.get('bridges', [])
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 64 or not isinstance(bridges, list) or len(bridges) > 256:
        raise ValueError('Use 1–64 nodes and at most 256 bridges')
    indexed = {}
    for node in nodes:
        if not isinstance(node, dict): raise ValueError('Node must be an object')
        ident = node.get('id')
        caps = node.get('capabilities', [])
        if not isinstance(ident, str) or not 1 <= len(ident) <= 64 or ident in indexed:
            raise ValueError('Node IDs must be unique short strings')
        if not isinstance(caps, list) or len(caps) > 16 or any(not isinstance(c, str) or not 1 <= len(c) <= 64 for c in caps):
            raise ValueError('Use short capability names')
        if type(node.get('enabled', False)) is not bool: raise ValueError('Enabled must be boolean')
        indexed[ident] = node
    source, target = body.get('source', 'local'), body.get('target', 'local')
    capability, hops = body.get('capability', 'inference'), body.get('hop_limit', 8)
    if not isinstance(source, str) or not isinstance(target, str) or source not in indexed or target not in indexed:
        raise ValueError('Source and target must name configured nodes')
    if not isinstance(capability, str) or not 1 <= len(capability) <= 64: raise ValueError('Invalid capability')
    if type(hops) is not int or not 0 <= hops <= 16: raise ValueError('Hop limit must be 0–16')
    graph = {n: [] for n in indexed}
    for edge in bridges:
        if not isinstance(edge, dict): raise ValueError('Bridge must be an object')
        a, b, cost = edge.get('from'), edge.get('to'), edge.get('cost', 1)
        if not isinstance(a, str) or not isinstance(b, str) or a not in indexed or b not in indexed:
            raise ValueError('Bridge endpoints must exist')
        if type(cost) is not int or not 1 <= cost <= 10000: raise ValueError('Cost must be an integer from 1 to 10000')
        allowed = edge.get('allowed', False)
        if type(allowed) is not bool: raise ValueError('Bridge permission must be boolean')
        if allowed: graph[a].append((b, cost))
    eligible = lambda n: indexed[n].get('enabled', False) and capability in indexed[n].get('capabilities', [])
    queue = [(0, [source])] if eligible(source) else []
    best = {}; route = None; cost = None
    while queue:
        total, path = heapq.heappop(queue)
        node, depth = path[-1], len(path)-1
        key = (node, depth)
        if total >= best.get(key, float('inf')): continue
        best[key] = total
        if node == target: route, cost = path, total; break
        if depth >= hops: continue
        for nxt, weight in graph[node]:
            if nxt not in path and eligible(nxt): heapq.heappush(queue, (total+weight, path+[nxt]))
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    advertisement = {'format': 'neural-inference-beacon-v1', 'node': source, 'capabilities': indexed[source]['capabilities'], 'transport': 'explicit exchange; no automatic discovery', 'authentication': 'required by receiving transport; this advertisement is unsigned'}
    return {'status': 'ROUTE_READY' if route else 'NO_ROUTE', 'terms': TERMS, 'beacon': advertisement,
            'post': {'request_sha256': digest, 'utf8_bytes': len(text.encode('utf-8')), 'capability': capability, 'source': source, 'target': target, 'hop_limit': hops},
            'route': route, 'route_cost': cost, 'hops': len(route)-1 if route else None,
            'transport': {'sent': False, 'remote_execution': False},
            'scope': 'Configured graph route only. Allowed flags are owner-supplied planning declarations, not proof of another owner’s permission. No global registration, external traffic or remote inference occurs.'}
