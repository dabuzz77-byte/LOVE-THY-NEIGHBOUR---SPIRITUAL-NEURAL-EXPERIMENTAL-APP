"""Public evidence -> module context -> local inference -> authenticated local beacon."""
import hashlib
import json
from neural_app import section_threads as threading
import time
import uuid
from ..graphical_app.sources import now, save_json

class WebPathway:

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.busy = False
        self.pending = None
        self.path = rt.data / 'web-pathway.json'
        self.folder = rt.data / 'work' / 'pathway'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.state = {'enabled': True, 'local_llama': True, 'last': None, 'runs': 0}
        try:
            self.state.update(json.loads(self.path.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            pass

    def view(self):
        with self.lock:
            return {**self.state, 'busy': self.busy, 'queued': self.pending is not None, 'public_web_ready': self.rt.privacy.ready(), 'beacon_destination': 'Authenticated local TCP/UDP bus on port ' + str(self.rt.config['port']), 'external_broadcast': False, 'scope': 'Research reports and module receipts; no changes to source websites or autonomous enforcement.'}

    def configure(self, body):
        with self.lock:
            for key in ('enabled', 'local_llama'):
                if key in body:
                    if type(body[key]) is not bool:
                        raise ValueError(key + ' must be true or false')
                    self.state[key] = body[key]
            if not self.state['enabled']:
                self.pending = None
            save_json(self.path, self.state)
        return self.view()

    def enqueue(self, report, references):
        fingerprint = hashlib.sha256(report.encode()).hexdigest()
        with self.lock:
            if not self.state['enabled']:
                return self.view()
            self.pending = {'text': report[:30000], 'references': references[:30], 'sha256': fingerprint}
        return self.view()

    def run(self, batch):
        batch_id = uuid.uuid4().hex[:12]
        key = 'pathway-' + batch_id
        receipt = {'id': batch_id, 'started': now(), 'source_sha256': batch['sha256'], 'references': batch['references'], 'modules': [], 'inference': None, 'error': None, 'external_broadcast': False, 'physical_outcome_verified': False}
        source = {'id': key, 'title': 'Research pathway ' + batch_id, 'kind': 'pathway', 'url': '', 'text': batch['text'], 'retrieved': now(), 'created': now(), 'status': 'ready', 'automatic': False, 'targets': list(self.rt.modules), 'next_fetch': 1e+30, 'attempts': 0, 'error': None}
        with self.rt.source_hub.lock:
            old = [k for k, v in self.rt.source_hub.items.items() if v.get('kind') == 'pathway']
            for k in old[:-4]:
                self.rt.source_hub.items.pop(k)
            self.rt.source_hub.items[key] = source
            self.rt.source_hub.save()
        self.rt.source_hub.attach(key, source)
        self.rt.binary_bus.feed('pathway-source', source['text'])
        try:
            pending = set(self.rt.modules)
            deadline = time.monotonic() + 150
            while pending and time.monotonic() < deadline and (not self.rt.stop.is_set()):
                if not self.state['enabled'] or not self.rt.config['running']:
                    raise ValueError('Pathway paused by its toggle or the module execution toggle')
                for name in list(pending):
                    with self.rt.lock:
                        result = self.rt.results.get(name, {})
                        covered = any((s.get('id') == key for s in result.get('source_context', [])))
                        if covered:
                            receipt['modules'].append({'id': name, 'ok': bool(result.get('ok')), 'source_supplied': True, 'error': result.get('error')})
                            pending.remove(name)
                        elif name not in self.rt.inflight:
                            self.rt.schedule(name)
                self.rt.stop.wait(0.5)
            for name in sorted(pending):
                receipt['modules'].append({'id': name, 'ok': False, 'source_supplied': False, 'error': 'No matching completion before deadline'})
            receipt['source_context_receipts'] = sum((m['source_supplied'] for m in receipt['modules']))
            receipt['successful_modules'] = sum((m['ok'] for m in receipt['modules']))
            if self.state['local_llama'] and (not self.rt.stop.is_set()) and self.state['enabled'] and self.rt.config['running']:
                prompt = 'Use the source evidence below to prepare useful work: identify public resource opportunities or documented business-practice concerns, cite source URLs, distinguish allegations from official findings, and list practical next steps. Do not infer guilt from weights, rank people, contact anyone, or impose consequences. All module receipts mean execution with source context, not verified outcomes.\n' + batch['text'][:1600]
                self.rt.model_hub.reserve('llama', 'public research inference')
                error = None
                try:
                    receipt['inference'], coverage = self.rt.model_hub.complete('llama', prompt, [{'role': 'user', 'content': prompt}], max_tokens=650)
                    receipt['model_context'] = coverage
                except Exception as exc:
                    error = str(exc)
                    receipt['inference_error'] = error
                finally:
                    self.rt.model_hub.release('llama', error)
            receipt['status'] = 'completed' if not pending and (not receipt.get('inference_error')) else 'partial'
        except Exception as exc:
            receipt.update(status='error', error=str(exc))
        receipt['finished'] = now()
        report = '\n'.join(['# Inference pathway receipt', '', 'Batch: ' + batch_id, 'Generated: ' + receipt['finished'], 'Scope: local research and review, not verified wrongdoing or external action.', '', receipt.get('inference') or 'No model inference available. See the receipt for pending steps.', '', '## Source references', *['- ' + str(r.get('url') or r.get('title')) for r in batch['references']], '', '## Execution receipt', '```json', json.dumps(receipt, indent=2, ensure_ascii=False), '```'])
        (self.folder / (batch_id + '.md')).write_text(report, encoding='utf-8')
        receipt['file'] = batch_id + '.md'
        with self.lock:
            self.state.update(last=receipt, runs=self.state['runs'] + 1)
            save_json(self.path, self.state)
        event = self.rt.publish('inference-beacon', {'id': batch_id, 'status': receipt['status'], 'source_sha256': batch['sha256'], 'file': receipt['file'], 'modules': len(receipt['modules']), 'inference_available': bool(receipt['inference']), 'external_action': False})
        with self.lock:
            receipt['local_beacon_seq'] = event['seq']
            save_json(self.path, self.state)
        return receipt

    def loop(self):
        for _shared_tick in range(1):
            with self.lock:
                if self.busy or not self.state['enabled'] or (not self.pending) or (not self.rt.config['running']):
                    continue
                batch = self.pending
                self.pending = None
                self.busy = True
            try:
                self.run(batch)
            except Exception as exc:
                with self.lock:
                    self.state['last'] = {'status': 'error', 'error': str(exc), 'finished': now()}
                    save_json(self.path, self.state)
            finally:
                with self.lock:
                    self.busy = False
