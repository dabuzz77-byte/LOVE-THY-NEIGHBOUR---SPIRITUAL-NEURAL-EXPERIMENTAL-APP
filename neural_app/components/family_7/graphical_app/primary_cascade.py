"""Always-running primary module: whole target -> forecast -> Flux -> chirals.

Every managed worker invocation enters prepare(), including drill and selected
target runs. Assessments are asynchronous: unresolved targets retain their exact
original data. Only a fresh, exact-context, rechecked prediction can supply a
changed local input copy on a subsequent invocation. Source files, observations,
process memory and remote systems are never rewritten by this module.
"""
import copy
import hashlib
import json
import re
from neural_app import section_threads as threading
import time
from collections import OrderedDict, Counter
from pathlib import Path
from ..graphical_app.alignment_core import BitVector
from ..graphical_app.module_reasoning import profile_for, PROFILES
from ..graphical_app.neural_rules import RULES
from ..graphical_app.predictive_rules import CONTRACT
from ..graphical_app.sources import now, save_json
from ..graphical_app.target_understanding import inspect_target, validate_candidate
from ..graphical_app.virtue_pipeline import VirtuePipeline
from ..graphical_app.consequence_policy import VERSION, prediction_gate
DEFAULTS = {'enabled': True, 'budget': 16, 'refresh_seconds': 600}
LOGIC = '1. Capture the complete effective target before each managed worker runs.\n2. Assess the whole target using the shared rules, neural field and local Llama.\n   Compare benefit, harm, harm from delay, affected people and less harmful alternatives.\n   Robin Hood: raise the floor while preserving rightful earnings and beneficial capacity.\n   Restrictions may be ethically assessed; an assessment never grants access authority.\n3. Compare remain and flip outcomes in that whole context, for groups down to one bit.\n   Highest virtue PASS or FAIL + predicted good remain: keep 0 as 0 and 1 as 1.\n   Highest virtue PASS or FAIL + harmful remain: flip only if the alternative is supported as good.\n   Uncertainty ON: preserve unresolved input for review. OFF: compare scores;\n   a forced choice remains unresolved and cannot authorize automatic propagation.\n4. Recheck the combined candidate, encoding, schema and protected context.\n5. Send original bytes plus the approved flip mask through Flux and both chirals.\n   Mask 0 = remain; mask 1 = flip. Verify exact output hash and reversible recovery.\n6. Reuse a verified result only for the same target, module, rules, settings and\n   evidence context. Apply changes only to a local declared-input copy on a later run.\n7. Preserve original data while queued, unavailable, uncertain, oversized or expired.\n   Measurements, resource records and ingested reference material stay unchanged.\n'

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

class PrimaryCascade:
    """Bounded background analysis with exact-context reuse and visible coverage."""

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.settings = {**DEFAULTS, **rt.config.get('primary_cascade', {})}
        self.pipeline = VirtuePipeline(rt, 'primary-cascade-jobs')
        self.entries = OrderedDict()
        self.queue = OrderedDict()
        self.modules = {}
        self.active = None
        self.alive = False
        self.counters = Counter()
        self.next_attempt = 0
        self.status = 'starting'
        self.last_error = None
        self.path = rt.data / 'primary-cascade.json'
        self.previous = {}
        try:
            self.previous = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
        rt.node('primary-cascade', 'Primary · arrayFLUX cascade', 'primary')
        for name in rt.modules:
            rt.edges.setdefault('module:' + name + '|primary-cascade', 0.1)
        rt.edges.setdefault('primary-cascade|chiral', 0.1)

    def policy(self):
        with self.rt.lock:
            return {'uncertainty': bool(self.rt.config.get('virtue_uncertainty', True)), 'weights': dict(self.rt.config.get('weights', {})), 'model': self.rt.model_hub.models['llama'], 'rules': sha(RULES), 'consequence_policy': VERSION}

    def prepare(self, name, request, origin, *, observed=None):
        """Mandatory admission hook; never labels pending data as assessed."""
        request = copy.deepcopy(request)
        module = self.rt.modules[name]
        inputs = copy.deepcopy(module['inputs'])
        inputs.update(request.get('inputs') or {})
        target = {'inputs': inputs}
        for field in ('sources', 'runtime'):
            if request.get(field):
                target[field] = request[field]
        if observed is not None:
            target = {'observed_output': observed}
        text = canonical(target)
        source = (self.rt.root / module['file']).read_text(encoding='utf-8-sig')
        profile = 'measurement' if observed is not None else profile_for(name, source)
        policy = self.policy()
        context = sha(canonical({'policy': policy, 'source': sha(source), 'definitions': request.get('definitions', {})}))
        key = sha(name + '\n' + context + '\n' + text)
        clock = time.monotonic()
        with self.lock:
            self.counters['invocations' if observed is None else 'observed_targets'] += 1
            row = self.entries.get(key)
            if row and row.get('finished_at') and (clock - row['finished_at'] >= self.settings['refresh_seconds']):
                self.entries.pop(key)
                row = None
                self.counters['expired'] += 1
            if row is None:
                row = {'id': key, 'module': name, 'created': now(), 'origin': origin, 'input_sha256': sha(text), 'bytes': len(text.encode('utf-8')), 'profile': profile, 'status': 'queued', 'stage': 'worker output observation' if observed is not None else 'pre-worker target', 'uncertainty_condition': policy['uncertainty'], 'context_sha256': context, 'encounters': 0, 'job': None, 'summary': None, 'route': None, 'error': None, '_text': text, '_policy': policy, '_output': None}
                if row['bytes'] > 512:
                    row.update(status='held: whole target exceeds 512 bytes', finished_at=clock)
                    self.counters['oversized'] += 1
                elif observed is None and (not inputs) and (not target.get('sources')) and (not target.get('runtime')):
                    row.update(status='held: target produced inside worker', finished_at=clock)
                    self.counters['internal_targets'] += 1
                else:
                    old = self.queue.pop(name, None)
                    if old and old in self.entries:
                        self.entries[old].update(status='superseded by newer target', finished_at=clock)
                        self.counters['superseded'] += 1
                    self.queue[name] = key
                    self.counters['enqueued'] += 1
                self.entries[key] = row
            else:
                self.counters['reused'] += 1
            row['encounters'] += 1
            row['last_seen'] = now()
            protected = set(self.queue.values()) | {self.active}
            for stale in list(self.entries):
                if len(self.entries) <= 160:
                    break
                if stale not in protected and stale != key:
                    self.entries.pop(stale)
            apply = observed is None and self.settings['enabled'] and (row['status'] == 'verified') and (row.get('_output') is not None)
            if apply:
                candidate = json.loads(row['_output'])
                if candidate.get('inputs') != inputs:
                    request['inputs'] = candidate['inputs']
                    self.counters['changed_input_uses'] += 1
            receipt = self.public(row)
            receipt.update(execution_policy='Original calculation continues while assessment is pending; only verified exact-target input copies can change.')
            receipt['applied_to_this_run'] = bool(apply and json.loads(row['_output'])['inputs'] != inputs)
            self.modules[name] = {'module': name, 'target': key, 'status': row['status'], 'last_seen': row['last_seen'], 'invocations': self.modules.get(name, {}).get('invocations', 0) + (observed is None), 'applied_to_last_run': receipt['applied_to_this_run']}
        request['primary_cascade'] = receipt
        self.wake.set()
        return (request, receipt)

    @staticmethod
    def public(row):
        return copy.deepcopy({k: v for k, v in row.items() if not k.startswith('_') and k != 'finished_at'})

    def configure(self, body):
        with self.lock:
            settings = dict(self.settings)
        for key, value in body.items():
            if key == 'enabled' and type(value) is bool:
                settings[key] = value
            elif key == 'budget' and type(value) is int and (1 <= value <= 64):
                settings[key] = value
            elif key == 'refresh_seconds' and type(value) is int and (60 <= value <= 86400):
                settings[key] = value
            else:
                raise ValueError('Use enabled on/off, budget 1–64 and refresh_seconds 60–86400')
        with self.rt.lock:
            self.rt.config['primary_cascade'] = settings
            self.rt.save_config()
        with self.lock:
            self.settings = settings
        if not settings['enabled']:
            self.pipeline.stop()
        self.wake.set()
        return self.view()

    def complete(self, row, job):
        """Finalize assessment before constructing a mask; never zero-fill."""
        row['summary'] = job.get('summary')
        row['final_assessment'] = job.get('final_assessment')
        row['finished_at'] = time.monotonic()
        if job['status'] == 'error':
            row.update(status='waiting: model unavailable', error=job.get('error'))
            self.last_error = job.get('error')
            self.next_attempt = time.monotonic() + 30
            if row['module'] not in self.queue:
                self.queue[row['module']] = row['id']
            row['finished_at'] = None
            return
        if job.get('consequence_policy_version') != VERSION:
            row['status'] = 'held: historical consequence policy'
            return
        if not job.get('castback_ready') or not prediction_gate(job.get('final_assessment') or {})['local_candidate_allowed']:
            row['status'] = 'held: prediction unresolved'
            self.counters['held'] += 1
            return
        bits = job['modes'][job['primary_mode']]['output_bits']
        output, padding = BitVector.pack(bits)
        if padding:
            raise ValueError('Prediction changed byte alignment')
        output = output.decode('utf-8')
        original = json.loads(row['_text'])
        candidate = json.loads(output)
        validate_candidate(inspect_target(row['_text']), inspect_target(output))
        if {k: v for k, v in candidate.items() if k != 'inputs'} != {k: v for k, v in original.items() if k != 'inputs'}:
            row['status'] = 'held: candidate changes protected context'
            return
        if candidate != original and row['profile'] in ('measurement', 'resource', 'definitions'):
            row['status'] = 'held: observed or protected records cannot be rewritten'
            return
        row['_output'] = output
        row['status'] = 'waiting: Flux and chirals'

    def advance_routes(self):
        """Wait for actual byte processing, not merely acceptance into a queue."""
        with self.lock:
            candidates = [r for r in self.entries.values() if r['status'] == 'waiting: Flux and chirals']
        for row in candidates:
            if not row.get('route'):
                try:
                    receipt = self.rt.flux.inject(BitVector(row['_text'], 'text').bits, 'bits', 'Primary cascade · ' + row['module'], approved_bits=BitVector(row['_output'], 'text').bits)
                except ValueError:
                    continue
                if receipt['status'] == 'rejected':
                    continue
                with self.lock:
                    row['route'] = receipt
            receipt = self.rt.flux.command_receipt(row['route']['id'])
            if receipt and receipt['status'] == 'complete' and receipt.get('prediction_verified'):
                with self.lock:
                    row.update(status='verified', route=receipt, finished_at=time.monotonic())
                    self.counters['verified'] += 1
                self.rt.activate('primary-cascade', 1.0)
            elif receipt is None or receipt['status'] in ('verification failed', 'rejected'):
                with self.lock:
                    row.update(status='held: transport verification missing', finished_at=time.monotonic())

    def tick(self):
        if not self.settings['enabled']:
            self.status = 'paused'
            return
        self.advance_routes()
        if self.active:
            if self.pipeline.busy:
                self.status = 'assessing'
                return
            with self.pipeline.lock:
                row = self.entries[self.active]
                job = next((j for j in self.pipeline.jobs if j['id'] == row['job']), None)
            with self.lock:
                if job:
                    self.complete(row, job)
                else:
                    row.update(status='held: missing prediction receipt', finished_at=time.monotonic())
                self.active = None
            self.save()
        if self.rt.virtue.busy or self.rt.model_hub.view()['llama']['busy']:
            self.status = 'waiting for Llama'
            return
        if time.monotonic() < self.next_attempt:
            self.status = 'waiting to retry'
            return
        with self.lock:
            if not self.queue:
                self.status = 'listening for module targets'
                return
            _, key = self.queue.popitem(last=False)
            row = self.entries[key]
            row['job'] = None
        if self.policy() != row['_policy']:
            with self.lock:
                row.update(status='held: policy changed; awaiting fresh invocation', finished_at=time.monotonic())
            return
        intent = (row['module'] + ' · ' + PROFILES[row['profile']]['meaning'])[:300]
        try:
            response = self.pipeline.submit({'kind': 'text', 'input': row['_text'], 'intent': intent, 'providers': ['llama'], 'budget': self.settings['budget'], 'compare': False}, origin={'module': row['module'], 'source': 'Complete captured worker target', 'primary_target': key})
        except Exception as exc:
            with self.lock:
                row.update(status='held: could not start forecast', error=str(exc), finished_at=time.monotonic())
            raise
        with self.lock:
            row.update(status='assessing', job=response['id'])
            self.active = key
            self.status = 'assessing'
        self.counters['assessments_started'] += 1

    def loop(self):
        self.alive = True
        try:
            while not self.rt.stop.is_set():
                try:
                    self.tick()
                except Exception as exc:
                    self.last_error = str(exc)
                    self.status = 'error; retaining original data'
                    with self.lock:
                        if self.active and self.active in self.entries:
                            self.entries[self.active].update(status='held: internal error', error=str(exc), finished_at=time.monotonic())
                            self.active = None
                    self.next_attempt = time.monotonic() + 30
                self.wake.wait(1)
                self.wake.clear()
        finally:
            self.alive = False
            self.pipeline.stop()
            self.save()

    def save(self):
        with self.lock:
            save_json(self.path, {'saved': now(), 'counters': dict(self.counters), 'modules': list(self.modules.values()), 'targets': [self.public(r) for r in self.entries.values()]})
        folder = self.pipeline.folder.resolve()
        receipts = sorted((p for p in folder.glob('*.json') if re.fullmatch('[0-9a-f]{12}\\.json', p.name) and p.resolve().parent == folder), key=lambda p: p.stat().st_mtime)
        for path in receipts[:-256]:
            path.unlink(missing_ok=True)

    def view(self, target=None):
        with self.lock:
            if target:
                row = self.entries.get(target)
                if not row:
                    raise ValueError('Target no longer retained')
                result = self.public(row)
                result['input'] = row['_text']
                result['proposed_output'] = row['_output']
                jobid = row.get('job')
            else:
                return {'name': 'Primary · ' + self.pipeline.context()['name'], 'logic': LOGIC, 'contract': CONTRACT, 'alive': self.alive, 'status': self.status, 'settings': dict(self.settings), 'error': self.last_error, 'active': self.active, 'queued': len(self.queue), 'counters': dict(self.counters), 'modules': [{**copy.deepcopy(self.modules.get(n, {'module': n, 'status': 'not yet invoked', 'invocations': 0})), **({'status': self.entries[self.modules[n]['target']]['status']} if n in self.modules and self.modules[n]['target'] in self.entries else {})} for n in self.rt.modules], 'targets': [self.public(r) for r in reversed(self.entries.values())], 'previous_session_saved': self.previous.get('saved'), 'scope': 'Every managed worker target enters before execution. Model analysis is queued. Pending or unsupported targets run their original calculation. Only verified local input copies change; external app/process memory is not modified.', 'limits': {'target_bytes': 512, 'queued_latest_per_module': 1, 'retained_targets': 160, 'provider': 'llama', 'source': 'Local Ollama'}}
        if jobid:
            try:
                result['prediction'] = self.pipeline.view(jobid)
            except ValueError:
                result['prediction_archive'] = str(self.pipeline.folder / (jobid + '.json'))
        return result

    def source(self):
        return {'logic': LOGIC, 'files': {name: Path(__file__).with_name(name).read_text(encoding='utf-8') for name in ('primary_cascade.py', 'predictive_rules.py', 'consequence_policy.py', 'virtue_pipeline.py', 'chiral.py', 'flux_hub.py')}}

    def stop(self):
        self.pipeline.stop()
        self.wake.set()
        self.save()
