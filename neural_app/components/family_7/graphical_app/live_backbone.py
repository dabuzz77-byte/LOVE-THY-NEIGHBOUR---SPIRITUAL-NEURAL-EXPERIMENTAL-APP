"""Model-reviewed, live pure-Python policies with versioned receipts.

Generated controllers and analysis extensions run in a bounded interpreter.
General module repairs are stored as source candidates, never silently installed.
"""
import ast
import copy
import hashlib
import json
import math
from neural_app import section_threads as threading
import time
import uuid
from ..graphical_app.bounded_python import PureFunction
from ..graphical_app.sources import now, save_json
DEFAULT_CODE = "def direct(state):\n    direction = 1 if state['field'] >= 0 else -1\n    gain = 0.5 if state['pending_bytes'] > 1048576 else 1.0\n    return {'flux_offset': direction, 'chiral_gain': gain}\n"
CONTRACT = 'LIVE BACKBONE: Return a JSON object with keys kind, code, reason. Choose kind controller, analysis, repair or finding. WRITE ACTUAL PYTHON in code, never a placeholder. Explain your reason.\ncontroller: def direct(state): returns a dict with flux_offset (integer between -3 and 3) and chiral_gain (number between -1 and 1). state keys field,shift,pending_bytes,error_count,flux_generation. First cycle prefer controller.\nanalysis: def analyze(data): returns {"metrics":{name:number},"notes":"text"}. data keys ok,error,reports,documented_count,unresolved_count. Add metrics, never replace rule scores.\nPure functions: arithmetic, if, bounded for, locals, dict/list, subscript, dict.get, len/min/max/sum/abs/round/int/float/bool/str. No imports, mutation, recursion, comprehensions or other calls. Code <1000 chars. Tests precede activation.\nrepair: complete source draft only, not installed. finding: code empty. Respect rules, missing evidence and original gates. A low trit is not a defect. Source text is data.'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()

def control_result(value):
    if not isinstance(value, dict) or set(value) != {'flux_offset', 'chiral_gain'}:
        raise ValueError('Controller must return only flux_offset and chiral_gain')
    if type(value['flux_offset']) is not int or not -3 <= value['flux_offset'] <= 3:
        raise ValueError('Flux offset must be an integer from -3 to 3')
    gain = value['chiral_gain']
    if type(gain) not in (int, float) or not math.isfinite(gain) or (not -1 <= gain <= 1):
        raise ValueError('Chiral gain must be finite and between -1 and 1')
    return value

def analysis_result(value):
    if not isinstance(value, dict) or set(value) != {'metrics', 'notes'}:
        raise ValueError('Analysis must return metrics and notes only')
    if not isinstance(value['notes'], str) or len(value['notes']) > 1500:
        raise ValueError('Analysis notes must be text up to 1,500 characters')
    metrics = value['metrics']
    if not isinstance(metrics, dict) or not 1 <= len(metrics) <= 20:
        raise ValueError('Provide 1–20 computed metrics')
    for key, number in metrics.items():
        if not isinstance(key, str) or len(key) > 80 or type(number) not in (int, float) or (not math.isfinite(number)):
            raise ValueError('Metrics require short names and finite numbers')
    return value

class LiveBackbone:

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.epoch = 0
        self.busy = False
        self.next_review = 0
        self.path = rt.data / 'backbone.json'
        self.folder = rt.data / 'work' / 'backbone'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.config = {'provider': 'llama', 'interval': 120, 'goal': 'Improve verified module behavior while preserving all rules. Direct flux and chirals responsively.', 'modules': []}
        self.records = []
        self.active = {}
        self.enabled = False
        self.status = 'paused'
        self.error = None
        self.evaluations = 0
        self.effect = {'flux_offset': 0, 'chiral_gain': 1}
        self.last_tick = None
        self.cursor = 0
        self.controller = PureFunction(DEFAULT_CODE, 'direct')
        self.controller_id = 'built-in'
        try:
            saved = json.loads(self.path.read_text(encoding='utf-8'))
            self.config.update(saved.get('config', {}))
            self.records = saved.get('records', [])
            for record in self.records:
                if record.get('active') and record['kind'] in ('controller', 'analysis'):
                    try:
                        self.activate_record(record, save=False)
                    except Exception:
                        record['active'] = False
        except (OSError, ValueError, KeyError):
            pass

    def save(self):
        self.records = [r for r in self.records[:-60] if r.get('active')] + self.records[-60:]
        save_json(self.path, {'config': self.config, 'records': self.records})

    def health(self):
        with self.rt.lock:
            rows = [{k: copy.deepcopy(m.get(k)) for k in ('id', 'title', 'status', 'runs', 'trit', 'gate', 'error')} for m in self.rt.modules.values()]
        counts = {}
        with self.rt.call_definitions.lock:
            for call in self.rt.call_definitions.calls:
                count = counts.setdefault(call['module'], [0, 0])
                count[0] += 1
                count[1] += int('unresolved' in str(call.get('resolution', '')).lower() or call.get('resolution') == 'dynamic receiver')
        for row in rows:
            count = counts.get(row['id'], [0, 0])
            row.update(calls=count[0], unresolved=count[1])
            row['technical_status'] = 'execution error' if row['error'] else 'not run yet' if not row['runs'] else 'executed'
            row['priority'] = 100 * bool(row['error']) + 10 * count[1] + int(not row['runs'])
        return sorted(rows, key=lambda r: (-r['priority'], r['id']))

    def view(self):
        health = self.health()
        with self.lock:
            value = {'config': copy.deepcopy(self.config), 'enabled': self.enabled, 'status': self.status, 'busy': self.busy, 'error': self.error, 'evaluations': self.evaluations, 'effect': dict(self.effect), 'last_tick': copy.deepcopy(self.last_tick), 'controller': self.controller_id, 'records': copy.deepcopy(self.records[-30:]), 'active_analysis': {k: v['id'] for k, v in self.active.items()}, 'next_review_in': max(0, round(self.next_review - time.monotonic())), 'folder': str(self.folder), 'health': health, 'scope': 'Pure control and analysis code runs locally. General repairs remain drafts. Rule scores are preserved.'}
        value['providers'] = {k: {'configured': v['configured'], 'busy': v['busy'], 'model': v['model']} for k, v in self.rt.model_hub.view().items() if k in ('llama', 'chatgpt')}
        return value

    def configure(self, body):
        values = {}
        if 'provider' in body:
            if body['provider'] not in ('llama', 'chatgpt'):
                raise ValueError('Choose Llama or ChatGPT')
            values['provider'] = body['provider']
        if 'interval' in body:
            if type(body['interval']) is not int or not 30 <= body['interval'] <= 3600:
                raise ValueError('Choose 30–3,600 seconds')
            values['interval'] = body['interval']
        if 'goal' in body:
            if not isinstance(body['goal'], str) or not 1 <= len(body['goal'].strip()) <= 800:
                raise ValueError('Enter a goal up to 800 characters')
            values['goal'] = body['goal'].strip()
        if 'modules' in body:
            if not isinstance(body['modules'], list) or any((m not in self.rt.modules for m in body['modules'])):
                raise ValueError('Select existing modules')
            values['modules'] = list(dict.fromkeys(body['modules']))
        with self.lock:
            self.epoch += 1
            self.config.update(values)
            self.next_review = 0
            self.save()
        return self.view()

    def start(self):
        with self.lock:
            provider = self.config['provider']
            if not self.rt.model_hub.view()[provider]['configured']:
                raise ValueError('Configure the selected model in Models first')
            self.enabled = True
            self.status = 'listening'
            self.error = None
            self.next_review = 0
            self.epoch += 1
        return self.view()

    def pause(self):
        with self.lock:
            self.enabled = False
            self.epoch += 1
            self.effect = {'flux_offset': 0, 'chiral_gain': 1}
            self.status = 'paused'
        return {'enabled': False, 'status': 'paused', 'inflight_result_will_be_discarded': self.busy}

    def snapshot(self):
        with self.rt.lock:
            state = {'field': self.rt.neural_output, 'shift': self.rt.chiral.shift, 'user_weight': self.rt.nodes['chiral']['weight'], 'error_count': sum((bool(m['error']) for m in self.rt.modules.values()))}
        state['pending_bytes'] = self.rt.binary_bus.state()['pending_bytes']
        state['flux_generation'] = self.rt.flux.compact()['generation']
        return state

    def signal(self):
        return self.effect

    def tick(self):
        with self.lock:
            if not self.enabled:
                return
            program = self.controller
            epoch = self.epoch
            revision = self.controller_id
        state = self.snapshot()
        try:
            output = control_result(program.run(state))
            with self.lock:
                if not self.enabled or epoch != self.epoch:
                    return
                self.effect = output
                self.evaluations += 1
                self.last_tick = {'time': now(), 'revision': revision, 'input': state, 'output': output}
        except Exception as exc:
            with self.lock:
                if epoch != self.epoch:
                    return
                self.effect = {'flux_offset': 0, 'chiral_gain': 1}
                self.enabled = False
                self.epoch += 1
                self.status = 'policy failed; paused'
                self.error = str(exc)
            return
        self.rt.binary_bus.feed('backbone-control', self.last_tick)

    def module_data(self, name, result=None):
        if result is None:
            with self.rt.lock:
                result = copy.deepcopy(self.rt.results.get(name, {}))
        definitions = self.rt.call_definitions.context(name)
        reports = result.get('reports', {})
        if len(json.dumps(reports)) > 16000:
            reports = {'excerpt': json.dumps(reports)[:3000], 'truncated': True}
        return {'ok': bool(result.get('ok')), 'error': str(result.get('error') or '')[:1500], 'reports': reports, 'documented_count': sum((bool(v.get('definition')) for v in definitions.values())), 'unresolved_count': sum((not bool(v.get('definition')) for v in definitions.values()))}

    def enrich(self, name, result):
        with self.lock:
            item = self.active.get(name) if self.enabled else None
            epoch = self.epoch
        if not item:
            return
        try:
            output = analysis_result(item['program'].run(self.module_data(name, result)))
            with self.lock:
                if not self.enabled or epoch != self.epoch:
                    return
                result['adaptive_analysis'] = {'revision': item['id'], 'computed': output, 'scope': 'Additional model-authored calculation; original rule outputs unchanged.'}
        except Exception as exc:
            with self.lock:
                self.active.pop(name, None)
            result['adaptive_analysis'] = {'error': str(exc), 'revision': item['id'], 'disabled': True}

    def test(self, kind, code, target):
        program = PureFunction(code, 'direct' if kind == 'controller' else 'analyze')
        if kind == 'controller':
            current = self.snapshot()
            fixtures = [{**current, 'field': f, 'pending_bytes': p} for f in (-1, -0.01, 0, 0.01, 1) for p in (0, 8388608)]
            validate = control_result
        else:
            fixtures = [self.module_data(target), {'ok': True, 'error': '', 'reports': {}, 'documented_count': 0, 'unresolved_count': 0}, {'ok': False, 'error': 'Missing runtime input', 'reports': {}, 'documented_count': 2, 'unresolved_count': 5}]
            validate = analysis_result
        outputs = []
        for fixture in fixtures:
            original = digest(fixture)
            a = validate(program.run(fixture))
            b = validate(program.run(fixture))
            if a != b or digest(fixture) != original:
                raise ValueError('Determinism or input preservation failed')
            outputs.append(a)
        return (program, {'passed': len(fixtures), 'checks': ['bounded interpreter', 'output contract', 'determinism', 'input preservation'], 'scope': 'Runtime compatibility and invariants, not proof of useful outcomes.', 'varied_outputs': len({digest(v) for v in outputs})})

    def activate_record(self, record, save=True):
        kind = record['kind']
        program, tests = self.test(kind, record['code'], record.get('target'))
        for other in self.records:
            if other['kind'] == kind and (kind == 'controller' or other.get('target') == record.get('target')):
                other['active'] = False
        record['active'] = True
        record['tests'] = tests
        if kind == 'controller':
            self.controller = program
            self.controller_id = record['id']
        else:
            self.active[record['target']] = {'program': program, 'id': record['id']}
        if save:
            self.save()

    def rollback(self, revision):
        with self.lock:
            record = next((r for r in self.records if r['id'] == revision), None)
            if not record or record['kind'] not in ('controller', 'analysis') or record['status'] not in ('active', 'tested'):
                raise ValueError('Choose a previously tested revision')
            self.epoch += 1
            self.activate_record(record)
            self.error = None
        return self.view()

    def review(self):
        with self.lock:
            if self.busy:
                raise ValueError('A review is already running')
            config = copy.deepcopy(self.config)
            provider = config['provider']
            epoch = self.epoch
            self.rt.model_hub.reserve(provider, 'backbone review')
            self.busy = True
            self.status = 'reviewing'
        threading.Thread(target=self.work, args=(config, epoch), daemon=True, name='backbone-review').start()
        return {'accepted': True}

    def work(self, config, epoch):
        provider = config['provider']
        error = None
        record = None
        try:
            ranked = [r for r in self.health() if not config['modules'] or r['id'] in config['modules']]
            tier = [r for r in ranked if r['priority'] == ranked[0]['priority']] if ranked else []
            row = tier[self.cursor % len(tier)] if tier else ranked[0]
            self.cursor += 1
            target = row['id']
            source = self.rt.model_hub.source[target]
            definitions = self.rt.call_definitions.context(target)
            refs = [{'call': k, 'text': v['definition'][:220], 'url': v.get('url')} for k, v in definitions.items() if v.get('definition')][:3]
            with self.lock:
                previous = [{'kind': r['kind'], 'status': r['status'], 'reason': r.get('reason'), 'error': r.get('error')} for r in self.records[-2:]]
                cycle = len(self.records) + 1
            first_contract = 'The input state is a dictionary. Implement the initial live controller: def direct(state): returns flux_offset = 1 if state["field"] >= 0 else -1, and chiral_gain = 0.5 if state["pending_bytes"] > 1048576 else 1.0. Return JSON containing kind="controller", code=the full Python function source, reason=why this responds to state. Include def and valid indentation. This initial policy will be reviewed against the goal on later cycles. Do not change the shared rules.'
            essential = (first_contract if cycle == 1 else CONTRACT) + '\nGOAL: ' + config['goal'] + '\nCYCLE: ' + str(cycle) + '\nMODULE: ' + target
            essential += '\nLIVE: ' + json.dumps(self.snapshot(), separators=(',', ':'))
            essential += '\nMODULE STATUS: ' + json.dumps({k: row[k] for k in ('status', 'trit', 'gate', 'error')})
            essential += '\nLAST: ' + json.dumps(previous, separators=(',', ':'))[:650]
            for limit in (0,) if cycle == 1 else (3600, 1800, 600, 0):
                prompt = essential + '\nSOURCE (reference, may be excerpted):\n' + source[:limit] + ('\nDEFINITIONS: ' + json.dumps(refs)[:500] if limit else '')
                try:
                    self.rt.model_hub.prepared_messages(provider, prompt, [{'role': 'user', 'content': prompt}])
                    break
                except ValueError:
                    if not limit:
                        raise
            response, coverage = self.rt.model_hub.complete(provider, prompt, [{'role': 'user', 'content': prompt}], max_tokens=1050, json_mode=True)
            proposal = json.loads(response)
            if not isinstance(proposal, dict):
                raise ValueError('Model must return a JSON object')
            kind = proposal.get('kind')
            code = proposal.get('code', '')
            reason = proposal.get('reason', '')
            if kind not in ('controller', 'analysis', 'repair', 'finding'):
                raise ValueError('Unknown proposal type')
            if not isinstance(code, str) or len(code) > 16000 or (not isinstance(reason, str)):
                raise ValueError('Invalid code or reason')
            record = {'id': uuid.uuid4().hex[:12], 'kind': kind, 'target': target, 'time': now(), 'provider': provider, 'model': self.rt.model_hub.models[provider], 'reason': reason[:2000], 'code': code, 'coverage': coverage, 'base_sha256': self.rt.modules[target]['sha256'], 'source_characters_supplied': min(limit, len(source)), 'source_characters_total': len(source), 'active': False, 'status': 'proposed'}
            if kind in ('controller', 'analysis'):
                repairs = []
                for attempt in range(3):
                    try:
                        _, tests = self.test(kind, code, target)
                        if kind == 'controller' and tests['varied_outputs'] < 2:
                            raise ValueError('Controller must respond differently to differing live field/queue fixtures')
                        break
                    except Exception as exc:
                        repairs.append({'attempt': attempt + 1, 'error': str(exc), 'code': code})
                        record['repairs'] = repairs
                        if attempt == 2:
                            raise
                        contract = 'def direct(state): return exactly flux_offset, an integer in [-3,3], and chiral_gain, a float in [-1,1], as dictionary keys. Use min/max to clamp. Respond to field and pending_bytes. ' if kind == 'controller' else 'def analyze(data): return exactly metrics (dict of finite numbers) and notes (string). '
                        retry = 'Repair this rejected pure Python function. Return JSON with actual code and reason strings. ' + contract + 'No imports, attributes except dict.get, comprehensions, range, mutation or external calls. Allowed len/min/max/sum/abs/round/int/float/bool/str. Numeric intervals are constraints, NOT Python expressions.\nFAILURE: ' + str(exc)[:200] + '\nCODE TO REPAIR:\n' + code[:1800]
                        if kind == 'controller':
                            retry += '\nAdapt this VALID baseline, keeping the def keyword and indentation:\n' + DEFAULT_CODE
                        answer, repair_coverage = self.rt.model_hub.complete(provider, retry, [{'role': 'user', 'content': retry}], max_tokens=850, json_mode=True)
                        fixed = json.loads(answer)
                        code = fixed.get('code')
                        if not isinstance(code, str) or len(code) > 12000:
                            raise ValueError('Repair did not provide bounded Python source')
                        record.update(code=code, repair_coverage=repair_coverage)
                record.update(tests=tests, status='tested', repairs=repairs)
            elif kind == 'repair':
                ast.parse(code)
                record.update(status='draft; needs behavioral tests', tests={'syntax': True, 'executed': False}, limitation='The original module is unchanged. A trustworthy behavior contract and regression tests are still required.')
            else:
                record['status'] = 'finding'
            with self.lock:
                if epoch != self.epoch or self.rt.stop.is_set():
                    return
                if kind in ('controller', 'analysis') and self.enabled:
                    self.activate_record(record, save=False)
                    record['status'] = 'active'
                record['sha256'] = hashlib.sha256(code.encode()).hexdigest()
                (self.folder / (record['id'] + '.py')).write_text(code, encoding='utf-8')
                save_json(self.folder / (record['id'] + '.json'), record)
                self.records.append(record)
                self.save()
                self.error = None
            self.rt.binary_bus.feed('backbone-code:' + record['id'], code)
            self.rt.publish('backbone-review', {k: v for k, v in record.items() if k != 'code'})
        except Exception as exc:
            error = str(exc)
            with self.lock:
                if epoch == self.epoch:
                    record = record or {'id': uuid.uuid4().hex[:12], 'kind': 'error', 'target': None, 'time': now(), 'code': '', 'active': False}
                    record.update(status='rejected', error=error)
                    self.records.append(record)
                    self.error = error
                    self.save()
        finally:
            self.rt.model_hub.release(provider, error)
            with self.lock:
                self.busy = False
                self.next_review = time.monotonic() + config['interval']
                self.status = ('waiting after error' if error else 'listening') if self.enabled else 'paused'

    def loop(self):
        for _shared_tick in range(1):
            self.tick()
            with self.lock:
                due = self.enabled and (not self.busy) and (time.monotonic() >= self.next_review)
            if due:
                try:
                    self.review()
                except ValueError as exc:
                    with self.lock:
                        self.status = 'waiting for model'
                        self.error = str(exc)
                        self.next_review = time.monotonic() + 10
