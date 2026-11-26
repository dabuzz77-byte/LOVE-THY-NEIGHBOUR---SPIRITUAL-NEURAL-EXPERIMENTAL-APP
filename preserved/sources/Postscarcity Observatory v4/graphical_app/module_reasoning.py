"""Function-aware adapters for shared evidence, prediction and conditional logic.

This layer describes each module's real function and inspects exact-input receipts.
It never turns successful computation into proof of good consequences.
"""
import ast
import hashlib
import json
from legacy_predictive import assess_payload
from code_archetypes import LIBRARY

PROFILES={
 'resource':{'criteria':['protected_floor','virtuous_disruptor','observed_receipt'],
             'meaning':'Allocation or repair proposal: preserve essentials, rightful earnings, beneficial capacity and exact resource totals.',
             'output_check':'A calculated proposal is not a delivered resource; require separate delivery evidence.'},
 'measurement':{'criteria':['evidence_separation','auditable_outcome','context_prediction'],
                'meaning':'Read actual host, network or source observations without changing them to satisfy a virtue label.',
                'output_check':'Preserve timestamp, source and units; missing readings remain unavailable.'},
 'transformation':{'criteria':['reversible_change','bit_inversion','context_prediction'],
                   'meaning':'Transform encoded data while retaining positions, widths and original content.',
                   'output_check':'Check format, whole candidate and round-trip where applicable; inversion alone is not a correction.'},
 'definitions':{'criteria':['evidence_separation','consent_and_minimization','uncertainty_hold'],
                'meaning':'Resolve terms and calls using attributed reference material, preserving source and interpretation boundaries.',
                'output_check':'A fetched or repeated definition is not independent proof of its claim.'},
 'prediction':{'criteria':['context_prediction','protected_floor','uncertainty_hold'],
               'meaning':'Assess the complete target, compare consequences, divide unresolved decisions and review the combined result.',
               'output_check':'Predicted consequences and supplied labels stay separate from observations; unresolved output is held for review.'},
 'restoration':{'criteria':['bounded_effect','explicit_authority','reversible_change'],
                'meaning':'Apply the module’s specific care, repair or restorative rule to supplied evidence.',
                'output_check':'A spiritual interpretation or rule result is attributed; it is not a measured external effect.'},
 'rule':{'criteria':['context_prediction','evidence_separation','uncertainty_hold'],
         'meaning':'Apply the original named functions to their declared data and retain the actual result.',
         'output_check':'Distinguish successful calculation, supplied assumptions and contextual consequence evidence.'}}


def profile_for(name, source):
    lower=name.lower()
    if any(t in lower for t in ('resource','allocation','robinhood','scarcity','economic')):return 'resource'
    if any(t in lower for t in ('drill','hierarch','virtuepass','historical_virtue','enforcement')):return 'prediction'
    if any(t in lower for t in ('registry','definition','ingest')):return 'definitions'
    if any(t in lower for t in ('binary','bit_array','chiral','alignment','ternary','flux')):return 'transformation'
    if any(t in lower for t in ('telemetry','probe','observation','measurement','livehost')) or 'psutil.' in source:return 'measurement'
    if any(t in lower for t in ('china','compassion','redemp','restor','buddha','covenant','spiritual','care')):return 'restoration'
    return 'rule'


class ModuleReasoning:
    def __init__(self, name, source, tree, context=None):
        self.name=name;self.context=context or {};self.profile=profile_for(name,source);self.functions=[];self.inputs={}
        self.hash=hashlib.sha256(source.encode('utf-8')).hexdigest()
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and not node.name.startswith('__'):
                self.functions.append({'name':node.name,'parameters':[a.arg for a in node.args.args],
                    'purpose':(ast.get_docstring(node) or '')[:300],'line':node.lineno})
        for node in tree.body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                try:value=ast.literal_eval(node.value)
                except (ValueError,TypeError):continue
                if isinstance(value,dict) and value:self.inputs[node.targets[0].id]=value

    def assess(self, value, function=None):
        if function is not None and function not in {f['name'] for f in self.functions}:raise ValueError('Unknown module function')
        receipt=assess_payload(value,self.context)
        return {k:receipt.get(k) for k in ('input_sha256','virtue_pass','classification','status','receipt_id','changed_bits','uncertainty_condition')} | {
            'function':function,'profile':self.profile,'propagation':'resolved local prediction' if receipt['receipt_id'] and any(r.get('id')==receipt['receipt_id'] and r.get('castback_ready') for r in self.context.get('receipts',[])) else 'retain original; contextual consequence unresolved'}

    def report(self, outputs):
        return {'module':self.name,'source_sha256':self.hash,'profile':self.profile,**PROFILES[self.profile],
            'functions':self.functions,'uncertainty_condition':self.context.get('uncertainty_condition',True),
            'input_assessments':{name:self.assess(value) for name,value in self.inputs.items()},
            'definition_calls':[LIBRARY.lookup(k) for k in PROFILES[self.profile]['criteria']],
            'observed_output_sha256':hashlib.sha256(json.dumps(outputs,sort_keys=True,default=str).encode()).hexdigest(),
            'scope':'Function-specific assessment adapter; original module execution and factual outputs are retained. Missing model receipts are not fabricated.'}
