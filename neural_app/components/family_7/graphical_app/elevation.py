"""Python ports of the distinct Java calculations. No invented measurements."""
from collections import Counter
import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import math
import re
VIRTUE_RULES = {'ROBIN_HOOD_VIRTUE': 'Elevate the eco floor while preserving the eco top where it serves beneficial outcomes and rightful earnings (floor target 1.00).', 'anti_extraction': 'Reject degradation of the human or ecological floor. Preserve agency, transparency, restoration and compassion.', 'floor_target': '1.00 is the declared baseline target; only supplied evidence can describe an observed floor.', 'circuit_breaker': 'A negative localized floor impact blocks an allocation and proposes 55% of gross yield for restoration.', 'conservation': 'Only allocate supplied, available resources above the greatest of the donor floor, protected rightful earnings and protected beneficial top. Preserve units and exact totals.', 'virtuous_top': 'Rightful earnings and a top serving good outcomes are protected. Do not infer wrongdoing from wealth, success or an unverified label about a person.', 'virtue_transitions': 'Track a harmful or unmet state, a proposed repair, and evidence of improvement separately. A transition must preserve the protected top and avoid degrading the floor.', 'karma_review': 'A failed redemptive check with recorded evidence becomes a local case for human review. Surface observations and allegations separately. Human courts determine legal responsibility and consequences; the software does not punish people or publish accusations automatically.', 'proof': 'A saved plan is not a delivery. A ledger entry is not a bank transaction. Record receipts separately.', 'authority': 'Neural weights, ingested pages and Llama proposals cannot override resource bounds or tool permissions.', 'consequence_causality': 'A beneficial whole-candidate prediction can support a local change; predicted harm is denied and unresolved consequences stay under review. Evaluate keeping and changing restrictions, including harm from delay. Neither intent nor a bit value proves an outcome.', 'robin_hood_consequences': 'Raise the economic and ecological floor through access, repair and fair allocation while preserving essentials, rightful earnings and beneficial capacity. Assess specific effects; neither wealth nor a claim of false virtue establishes wrongdoing.'}

def finite(value, low=None, high=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('Supply a finite number')
    if low is not None and value < low or (high is not None and value > high):
        raise ValueError(f'Number must be between {low} and {high}')
    return float(value)

def money(value):
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid decimal amount') from None
    if not amount.is_finite() or amount < 0 or amount > Decimal('1000000000000'):
        raise ValueError('Amount must be finite, nonnegative and at most one trillion')
    return amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

def robin_hood(data):
    """RobinHoodCircuitBreaker.processTransaction, retaining the exact 0.55 rule."""
    impact = finite(data['floor_impact'])
    proposed = money(data['yield'])
    protected = max(money(data.get('protected_earnings', 0)), money(data.get('protected_top', 0)))
    if protected > proposed:
        raise ValueError('Protected earnings/top cannot exceed the supplied gross yield')
    original = (proposed * Decimal('.55')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) if impact < 0 else Decimal('0.00')
    repair = min(original, proposed - protected)
    return {'VIRTUE_TRIT': -1 if impact < 0 else 1, 'NO_EXECUTE_BIT': int(impact < 0), 'floor_impact': impact, 'gross_yield': str(proposed), 'original_55_percent_proposal': str(original), 'protected_top_and_earnings': str(protected), 'eligible_surplus': str(proposed - protected), 'restoration_proposal': str(repair), 'status': 'restoration required' if impact < 0 else 'passes supplied floor-impact check', 'basis': 'User-supplied figures; no funds moved', 'ROBIN_HOOD_FLOOR_INDEX': 1.0}

def allocate(data):
    """Floor-first resource matching, with exact conservation and no negative balances."""
    donors, needs = (data.get('donors', []), data.get('needs', []))
    if not isinstance(donors, list) or not isinstance(needs, list) or len(donors) + len(needs) > 500:
        raise ValueError('Provide at most 500 donor and need records')
    balances, floors, transfers, unit = ({}, {}, [], str(data.get('unit', 'units'))[:40])
    for row in donors:
        name = str(row['id']).strip()
        if not name or name in balances:
            raise ValueError('Donor IDs must be unique and nonempty')
        balances[name] = money(row['available'])
        floors[name] = max(money(row['floor']), money(row.get('protected_earnings', 0)), money(row.get('protected_top', 0)))
        if balances[name] < floors[name]:
            raise ValueError('A donor is already below its protected floor')
    before = sum(balances.values(), Decimal(0))
    unmet = []
    ids = set()
    for row in sorted(needs, key=lambda r: finite(r.get('priority', 1), 0, 100), reverse=True):
        target = str(row['id']).strip()
        if not target or target in ids or target in balances:
            raise ValueError('Need IDs must be unique and distinct from donors')
        ids.add(target)
        amount = money(row['amount'])
        for donor in sorted(balances, key=lambda k: balances[k] - floors[k], reverse=True):
            give = min(amount, balances[donor] - floors[donor])
            if give > 0:
                balances[donor] -= give
                amount -= give
                transfers.append({'from': donor, 'to': target, 'amount': str(give), 'unit': unit})
        if amount > 0:
            unmet.append({'id': target, 'amount': str(amount)})
    total = sum((Decimal(t['amount']) for t in transfers), Decimal(0))
    conserved = before == sum(balances.values(), Decimal(0)) + total
    if not conserved or any((balances[k] < floors[k] for k in balances)):
        raise ValueError('Resource invariant failed')
    return {'status': 'proposal', 'transfers': transfers, 'remaining': {k: str(v) for k, v in balances.items()}, 'protected_minimums': {k: str(v) for k, v in floors.items()}, 'unmet': unmet, 'total_allocated': str(total), 'conserved': conserved, 'unit': unit, 'delivered': False}

def base_digits(value, base):
    result = []
    while value:
        value, r = divmod(value, base)
        result.append(r)
    return list(reversed(result or [0]))

def balanced_digits(value):
    result = []
    while value:
        value, r = divmod(value, 3)
        if r == 2:
            r = -1
            value += 1
        result.append(r)
    return list(reversed(result or [0]))

def translate(data):
    """SixGrid + BinaryTernaryQutritTranslator: UTF-8, width and leading zeros survive."""
    text = data.get('text', '')
    if not isinstance(text, str):
        raise ValueError('Text must be a string')
    raw = text.encode('utf-8')
    if not 1 <= len(raw) <= 512:
        raise ValueError('Enter 1–512 UTF-8 bytes')
    bits = ''.join((f'{b:08b}' for b in raw))
    value = int.from_bytes(raw, 'big')
    ternary = base_digits(value, 3)
    balanced = balanced_digits(value)
    recovered = 0
    for trit in balanced:
        recovered = recovered * 3 + trit
    back = recovered.to_bytes(len(raw), 'big')
    qutrits = [{'digit': k, 'amplitudes': [[round(math.cos(math.tau * k * j / 3) / math.sqrt(3), 8), round(math.sin(math.tau * k * j / 3) / math.sqrt(3), 8)] for j in range(3)], 'probabilities': [1 / 3] * 3} for k in ternary]
    return {'text': text, 'bytes': len(raw), 'binary': bits, 'ternary': ternary, 'balanced': balanced, 'qutrit_indices': [v + 1 for v in balanced], 'qutrits': qutrits, 'recovered': back.decode('utf-8'), 'roundtrip': back == raw, 'sha256': hashlib.sha256(raw).hexdigest(), 'basis': 'Exact conversion; mathematical qutrit states'}

def spectral_vector(text):
    """Deterministic lexical vector; no remote embedding or pretended training."""
    return Counter(re.findall('\\w+', str(text).casefold()))

def cosine(left, right):
    a, b = (spectral_vector(left), spectral_vector(right))
    den = math.sqrt(sum((v * v for v in a.values())) * sum((v * v for v in b.values())))
    return sum((v * b.get(k, 0) for k, v in a.items())) / den if den else 0.0

def quantum_distribution(data):
    """QuantumTernaryBinaryCore distribution and entropy on supplied telemetry only."""
    values = data.get('values', [])
    if not isinstance(values, list) or not 1 <= len(values) <= 256:
        raise ValueError('Supply 1–256 measured values')
    phase = finite(data.get('phase', 0))
    p = [math.sin(finite(v) + phase) ** 2 for v in values]
    total = sum(p)
    if total == 0:
        raise ValueError('Zero norm; provide a nonzero input vector')
    p = [v / total for v in p]
    return {'probabilities': p, 'norm': sum(p), 'entropy_bits': -sum((v * math.log2(v) for v in p if v)), 'binary': [int(v > 1 / len(p)) for v in p], 'basis': 'Mathematical transform of supplied measurements'}

def identity(data):
    """QBiTerEngine clarity → Ennead → ternary weights, preserving thresholds."""
    clarity = finite(data['clarity'], 0, 1)
    floor = finite(data['floor'], 0)
    alpha = max(0, clarity - (0.3 if floor < 1 else 0))
    level = next((level for threshold, level in ((0.9, 9), (0.8, 8), (0.7, 7), (0.6, 6), (0.5, 5), (0.4, 4), (0.3, 3), (0.1, 2)) if alpha >= threshold), 1)
    probabilities = [0.05, 0.15, 0.8] if level >= 7 else [0.1, 0.7, 0.2] if level >= 4 else [0.85, 0.1, 0.05]
    return {'alpha': alpha, 'ennead': level, 'probabilities': probabilities, 'VIRTUE_TRIT': probabilities.index(max(probabilities)) - 1, 'NO_EXECUTE_BIT': int(floor < 1), 'basis': 'Supplied clarity and floor; no judgment of a person'}

def convergence(data):
    velocities = data.get('velocities', [])
    if not isinstance(velocities, list) or not velocities:
        raise ValueError('Supply observed trajectory velocities')
    divisor = finite(data.get('dimension_range', len(velocities)), 1e-06)
    variance = sum((abs(finite(v)) for v in velocities)) * (finite(data.get('frequency', 7.83), 0) / 7.83) / divisor
    return {'variance': variance, 'coherence_index': max(0, min(100, 100 - variance * 2.5)), 'basis': 'Calculated index'}

def crypto_flux(data):
    text = str(data.get('text', ''))
    digest = hashlib.sha256(text.encode()).hexdigest().upper()
    return {'sha256': digest, 'opposite_factor_flux': ''.join((f'{~b & 255:02X}' for b in digest.encode()[:12])), 'basis': 'TransformerMatrix textual hex-byte inversion'}

def sifter(data):
    text = str(data.get('text', '')).lower()
    positive = [w for w in ('iso20022', 'legitimate', 'restitution', 'sovereign') if w in text]
    negative = [w for w in ('skeleton', 'hidden', 'anonymous', 'override', 'key', 'crack') if w in text]
    return {'wheat_terms': positive, 'chaff_terms': negative, 'review_required': bool(negative), 'basis': 'Original SifterRegistryMatrix lexical flags, not a security verdict'}

def restitution(data):
    velocity = finite(data['loss_velocity'], 0)
    threshold = finite(data.get('threshold', 0), 0)
    proposal = money(velocity * 15.5) if velocity > threshold else Decimal('0.00')
    return {'restoration_proposal': str(proposal), 'status': 'proposal', 'delivered': False, 'basis': 'RestitutionPipeline 15.5 multiplier'}

def universal_floor(data):
    """UniversalIdentityEngine loop version's 10% structural floor, as a proposal."""
    floor = money(data['floor'])
    ceiling = money(data['ceiling'])
    if floor > ceiling:
        raise ValueError('Floor cannot exceed the declared ceiling')
    violated = floor <= 0 and ceiling > 1000
    fair = (ceiling * Decimal('.10')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    return {'NO_EXECUTE_BIT': int(violated), 'VIRTUE_TRIT': -1 if violated else 1, 'floor': str(floor), 'ceiling': str(ceiling), 'proposed_floor': str(max(floor, fair) if violated else floor), 'status': 'restoration proposal' if violated else 'passes supplied anomaly check', 'delivered': False}

def inference_gate(data):
    """InferenceBeacon's identity/floor gate with explicit proof of payload integrity."""
    payload = str(data.get('text', ''))
    digest = hashlib.sha256(payload.encode()).hexdigest()
    proof = str(data.get('sha256', '')).casefold()
    floor = finite(data.get('floor', 0), 0)
    flags = [t for t in ('predatory_interest', 'malicious_exploit', 'withhold_sovereignty') if t in payload.lower()]
    passed = bool(proof == digest and floor >= 1 and (not flags))
    return {'NO_EXECUTE_BIT': int(not passed), 'VIRTUE_TRIT': 1 if passed else -1, 'sha256': digest, 'payload_integrity': proof == digest, 'floor': floor, 'blocked_terms': flags, 'basis': 'Digest validates matching bytes; it does not authenticate an author or prove a beneficial outcome'}

def loss_audit(data):
    """PersonalLossAuditor port: real CSV parsing, exact decimals, explicit rejected rows."""
    text = data.get('csv', '')
    if not isinstance(text, str) or not 1 <= len(text) <= 200000:
        raise ValueError('Supply CSV text up to 200,000 characters')
    keywords = data.get('keywords', ['BET', 'CASINO', 'WAGER', 'POKER', 'SPORTSBOOK', 'LOTTERY', '888', 'BET365', 'SKYBET'])
    if not isinstance(keywords, list) or not 1 <= len(keywords) <= 100 or any((not isinstance(k, str) or not k.strip() for k in keywords)):
        raise ValueError('Supply a nonempty list of text keywords')
    reader = csv.DictReader(io.StringIO(text))
    matched = []
    rejected = []
    deposits = Decimal(0)
    returns = Decimal(0)
    if not reader.fieldnames or not {'description', 'amount'}.issubset(reader.fieldnames):
        raise ValueError('CSV requires description and amount columns')
    for line, row in enumerate(reader, start=2):
        if line > 10002:
            raise ValueError('CSV limit is 10,000 rows')
        if not any((k.upper() in (row.get('description') or '').upper() for k in keywords)):
            continue
        try:
            raw = (row.get('amount') or '').strip().replace('£', '').replace('$', '').replace(',', '')
            amount = Decimal(raw)
            if not amount.is_finite() or abs(amount) > Decimal('1000000000000'):
                raise ValueError('Amount is out of range')
            amount = amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            if amount < 0:
                deposits -= amount
            else:
                returns += amount
            matched.append({'line': line, 'description': row['description'], 'amount': str(amount)})
        except (InvalidOperation, ValueError):
            rejected.append({'line': line, 'error': 'Invalid amount'})
    return {'matches': matched, 'rejected': rejected, 'deposits': str(deposits), 'returns': str(returns), 'net': str(returns - deposits), 'basis': 'User-imported statement rows matching explicit keywords; no account identifiers embedded'}

def virtue_transition(data):
    """User's floor/top clarification applied to an evidenced, reversible state transition."""
    before = finite(data['before_floor'], 0)
    after = finite(data['after_floor'], 0)
    top = finite(data['after_top'], 0)
    protected = finite(data['protected_top'], 0)
    evidence = str(data.get('evidence', '')).strip()
    floor_preserved = after >= before
    top_preserved = top >= protected
    trit = -1 if not floor_preserved or not top_preserved else 1 if after >= 1 and evidence else 0
    return {'VIRTUE_TRIT': trit, 'NO_EXECUTE_BIT': int(trit < 0), 'floor_change': after - before, 'floor_preserved': floor_preserved, 'protected_top_preserved': top_preserved, 'floor_target_met': after >= 1, 'status': {-1: 'repair required', 0: 'proposed or partial improvement', 1: 'user-evidenced transition'}[trit], 'evidence': evidence, 'evidence_basis': 'User-supplied observation; independent verification remains separate'}

def karma_review(data):
    """Evidence-led redemptive review; court responsibility stays with humans."""
    check = data.get('redemptive_check', 'unknown')
    if check not in ('unknown', 'failed', 'passed'):
        raise ValueError('Choose unknown, failed or passed for the review result')
    observation = str(data.get('observation', '')).strip()
    evidence = data.get('evidence', [])
    if not isinstance(evidence, list) or len(evidence) > 30:
        raise ValueError('Supply at most 30 evidence references')
    if not observation or not all((isinstance(e, str) and e.strip() for e in evidence)):
        raise ValueError('Record the observation and nonempty evidence references')
    supported = bool(evidence)
    return {'redemptive_check': check, 'observation': observation, 'evidence': evidence, 'allegation': str(data.get('allegation', '')), 'unmet_repair_conditions': str(data.get('repair_conditions', '')), 'status': 'refer for human review' if check == 'failed' and supported else 'redemptive check passed' if check == 'passed' and supported else 'needs evidence or review', 'VIRTUE_TRIT': -1 if check == 'failed' and supported else 1 if check == 'passed' and supported else 0, 'human_court_required_for_legal_judgment': True, 'automatic_punishment': False, 'basic_floor_protected': True, 'legal_finding': 'No legal determination by this software', 'evidence_basis': 'User-submitted; record does not establish the allegation as fact'}
OPERATIONS = {'translation': translate, 'robin_hood': robin_hood, 'allocation': allocate, 'identity': identity, 'distribution': quantum_distribution, 'convergence': convergence, 'crypto_flux': crypto_flux, 'sifter': sifter, 'restitution': restitution, 'universal_floor': universal_floor, 'inference_gate': inference_gate, 'loss_audit': loss_audit, 'virtue_transition': virtue_transition, 'karma_review': karma_review}

def evaluate(operation, data=None, sources=None):
    """Shared module entry; empty inputs wait instead of manufacturing evidence."""
    data = dict(data or {})
    if not data and sources:
        text = '\n'.join((str(s.get('text', '')) for s in sources))[:400]
        if operation in ('translation', 'crypto_flux', 'sifter'):
            data = {'text': text}
    if not data:
        return {'status': 'awaiting input', 'operation': operation, 'VIRTUE_TRIT': 0, 'NO_EXECUTE_BIT': 1}
    return OPERATIONS[operation](data)
