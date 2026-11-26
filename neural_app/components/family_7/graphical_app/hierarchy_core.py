"""Evidence-explicit, interval-based next-best selection under protected floors."""
import math
CRITERIA = {'floor': ('Essentials floor change', 0.25, 'Protect access to food, shelter, water, energy and care; use locally evidenced needs.'), 'harm': ('Harm reduction', 0.2, 'Compare expected harm before and after, including displaced harm and affected groups.'), 'earnings': ('Rightful earnings protected', 0.1, 'Protect documented legitimate earnings; wealth alone is not wrongdoing.'), 'top': ('Beneficial eco top protected', 0.1, 'Preserve productive capacity serving evidenced good outcomes.'), 'consent': ('Consent and agency', 0.1, 'Include affected people’s informed choices and lawful authority.'), 'restoration': ('Repair and restoration', 0.1, 'Estimate practical repair, redemptive opportunity and durability.'), 'feasibility': ('Feasibility', 0.1, 'Check resources, dependencies, delivery capacity and realistic timescale.'), 'reversibility': ('Reversibility', 0.05, 'Prefer recoverable steps when consequences remain uncertain.')}
PROTECTED = ('floor', 'harm', 'earnings', 'top', 'consent')

def number(value):
    return type(value) in (int, float) and math.isfinite(value)

def evaluate(case):
    options = case.get('options', [])
    custom = case.get('weights', {})
    if not isinstance(options, list) or not 1 <= len(options) <= 32:
        raise ValueError('Compare 1–32 concrete options')
    if not isinstance(custom, dict) or set(custom) - set(CRITERIA):
        raise ValueError('Use the documented criteria for weights')
    weights = {k: custom.get(k, v[1]) for k, v in CRITERIA.items()}
    if any((not number(v) or not 0 <= v <= 10 for v in weights.values())) or sum(weights.values()) <= 0:
        raise ValueError('Weights must be finite, nonnegative, and not all zero')
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}
    rows = []
    ids = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError('Each option must be an object')
        key = option.get('id', str(index + 1))
        name = option.get('name', '')
        if not isinstance(key, str) or not 1 <= len(key) <= 80 or key in ids or (not isinstance(name, str)) or (not 1 <= len(name) <= 200):
            raise ValueError('Options need unique IDs and names')
        ids.add(key)
        metrics = option.get('metrics', {})
        if not isinstance(metrics, dict) or set(metrics) - set(CRITERIA):
            raise ValueError('Unknown criterion in option ' + name)
        values = {}
        missing = []
        trace = []
        for criterion in CRITERIA:
            item = metrics.get(criterion)
            if item is None:
                values[criterion] = {'low': -1.0, 'high': 1.0, 'evidence': '', 'basis': 'unknown'}
                missing.append(criterion)
                continue
            if not isinstance(item, dict):
                raise ValueError('Each criterion needs low, high, evidence and basis')
            low = item.get('low')
            high = item.get('high')
            evidence = item.get('evidence', '')
            basis = item.get('basis', 'projection')
            if not number(low) or not number(high) or (not -1 <= low <= high <= 1):
                raise ValueError('Use ordered effect bounds within -1 to +1')
            if not isinstance(evidence, str) or len(evidence) > 2000 or basis not in ('projection', 'observation'):
                raise ValueError('Provide evidence text and projection/observation basis')
            if not evidence.strip():
                values[criterion] = {'low': -1.0, 'high': 1.0, 'evidence': '', 'basis': 'unknown'}
                missing.append(criterion)
            else:
                values[criterion] = {'low': low, 'high': high, 'evidence': evidence.strip(), 'basis': basis}
        blocked = []
        uncertain = []
        for criterion in PROTECTED:
            v = values[criterion]
            status = 'blocked' if v['high'] < 0 else 'uncertain' if v['low'] < 0 or criterion in missing else 'protected'
            if status == 'blocked':
                blocked.append(criterion)
            elif status == 'uncertain':
                uncertain.append(criterion)
            trace.append({'criterion': criterion, 'rule': 'lower bound must be >=0, with supplied evidence', 'state': status, 'bounds': [v['low'], v['high']]})
        lo = sum((weights[k] * v['low'] for k, v in values.items()))
        hi = sum((weights[k] * v['high'] for k, v in values.items()))
        ready = not blocked and (not uncertain) and (not missing) and (values['feasibility']['low'] >= 0)
        if values['feasibility']['high'] < 0:
            blocked.append('feasibility')
        elif values['feasibility']['low'] < 0:
            uncertain.append('feasibility')
        trace.append({'criterion': 'feasibility', 'rule': 'lower bound must be >=0', 'state': 'blocked' if 'feasibility' in blocked else 'uncertain' if 'feasibility' in uncertain else 'feasible'})
        tier = 1 if ready and lo >= 0.65 else 2 if ready and lo >= 0 else 3
        rows.append({'id': key, 'name': name, 'metrics': values, 'tier': tier, 'eligible': ready and lo >= 0, 'blocked': blocked, 'uncertain': uncertain, 'missing_evidence': missing, 'score_low': round(lo, 6), 'score_high': round(hi, 6), 'coverage': (len(CRITERIA) - len(missing)) / len(CRITERIA), 'trace': trace, 'basis': 'Evidence-backed supplied estimates; source truth and impact are not independently verified.'})

    def rank(weights):

        def key(r):
            score = sum((weights[k] * v['low'] for k, v in r['metrics'].items()))
            return (not r['eligible'], -r['metrics']['floor']['low'] if r['eligible'] else len(r['blocked']), -score, r['id'])
        return sorted(rows, key=key)
    ordered = rank(weights)
    eligible = [r for r in ordered if r['eligible']]
    for row in rows:
        row['dominated_by'] = [other['id'] for other in eligible if other is not row and all((other['metrics'][k]['low'] >= row['metrics'][k]['high'] for k in CRITERIA)) and any((other['metrics'][k]['low'] > row['metrics'][k]['high'] for k in CRITERIA))]
    best = eligible[0] if eligible else None
    challengers = []
    sensitivity = []
    if best:
        challengers = [r['id'] for r in eligible[1:] if r['metrics']['floor']['high'] >= best['metrics']['floor']['low'] and r['score_high'] >= best['score_low']]
        for criterion in CRITERIA:
            for factor in (0.8, 1.2):
                variant = {**weights, criterion: weights[criterion] * factor}
                denom = sum(variant.values())
                variant = {k: v / denom for k, v in variant.items()}
                ordered_variant = [r for r in rank(variant) if r['eligible']]
                sensitivity.append({'criterion': criterion, 'factor': factor, 'first': ordered_variant[0]['id'] if ordered_variant else None})
    return {'ranked': ordered, 'selected': best['id'] if best else None, 'next_bests': [r['id'] for r in eligible[1:]], 'status': 'provisional ranking; intervals overlap' if challengers else 'preferred under supplied criteria' if best else 'restorative hold; gather evidence or repair constraints', 'NO_EXECUTE_BIT': 0 if best else 1, 'overlapping_challengers': challengers, 'weights': weights, 'sensitivity': sensitivity, 'weight_stable': all((s['first'] == best['id'] for s in sensitivity)) if best else None, 'selection_rule': 'First enforce protected floors and evidence. Among eligible choices maximize the conservative essentials-floor change, then weighted lower-bound benefit. ID breaks exact ties only.', 'scope': 'Decision support for concrete options, not a universal moral hierarchy of people. No external action is executed. User-supplied observations are not independently verified.', 'scale': 'Each effect is normalized to -1 (deterioration), 0 (no change), +1 (improvement). Document the real units and baseline in evidence.'}

class HierarchyHub:

    def __init__(self, rt):
        self.rt = rt
        self.last = None

    def view(self):
        return {'criteria': {k: {'label': v[0], 'weight': v[1], 'definition': v[2], 'protected': k in PROTECTED} for k, v in CRITERIA.items()}, 'last': self.last}

    def compare(self, body):
        from ..graphical_app.sources import now, save_json
        import uuid
        result = evaluate(body)
        result.update(id=uuid.uuid4().hex[:12], time=now())
        folder = self.rt.data / 'work' / 'hierarchy'
        folder.mkdir(parents=True, exist_ok=True)
        save_json(folder / (result['id'] + '.json'), {'case': body, 'result': result})
        self.last = result
        self.rt.binary_bus.feed('hierarchy-comparison', result)
        with self.rt.lock:
            self.rt.overrides['HierarchicalVirtueEngine'] = {'hierarchy_case': body}
            save_json(self.rt.data / 'inputs.json', self.rt.overrides)
        self.rt.schedule('HierarchicalVirtueEngine')
        return result
