"""Shared bridge for original modules; only exact whole-input receipts can apply."""
import json
from ..graphical_app.predictive_rules import NAME, CONTRACT, digest
from ..graphical_app.code_archetypes import LIBRARY

def assess_payload(value, context=None):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    bits = ''.join((f'{b:08b}' for b in text.encode('utf-8')))
    key = digest(bits)
    matching = next((r for r in reversed((context or {}).get('receipts', [])) if r['input_sha256'] == key), None)
    out = matching['output_bits'] if matching and matching.get('castback_ready') else bits
    raw = bytes((int(out[i:i + 8], 2) for i in range(0, len(out), 8)))
    transformed = value
    try:
        decoded = raw.decode('utf-8')
        proposed = decoded if isinstance(value, str) else json.loads(decoded)
        if type(proposed) is type(value):
            transformed = proposed
    except (ValueError, UnicodeError):
        pass
    return {'name': NAME, 'contract': CONTRACT, 'input_sha256': key, 'input': value, 'output': transformed, 'uncertainty_condition': (context or {}).get('uncertainty_condition', True), 'virtue_pass': matching['whole_assessment'].get('virtue_pass') if matching else None, 'classification': matching.get('final_assessment', {}).get('classification', 'unknown') if matching else 'unknown', 'status': 'assessed exact input' if matching else 'awaiting whole-input model assessment', 'receipt_id': matching['id'] if matching else None, 'input_bits': bits, 'output_bits': out, 'changed_bits': sum((a != b for a, b in zip(bits, out))), 'forced_success': False, 'definition_calls': [LIBRARY.lookup(k) for k in ('context_prediction', 'uncertainty_hold', 'evidence_separation')], 'assessment_input': text, 'scope': 'Local data prediction only; original observations are retained and no process or OS privileges change.'}
