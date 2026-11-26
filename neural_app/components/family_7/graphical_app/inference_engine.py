"""Actual model inference with persisted input, context coverage and provider receipts."""
import json
from neural_app import section_threads as threading
import time
import uuid
from ..graphical_app.sources import now, save_json

class InferenceEngine:

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.busy = False
        self.path = rt.data / 'inference.json'
        try:
            self.jobs = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.jobs = []
        for job in self.jobs:
            if job['status'] in ('queued', 'running'):
                job.update(status='interrupted', error='The runtime stopped before this inference completed')

    def view(self):
        with self.lock:
            return {'busy': self.busy, 'jobs': json.loads(json.dumps(self.jobs[-20:])), 'providers': {p: {k: s[k] for k in ('model', 'configured', 'busy', 'status', 'error')} for p, s in self.rt.model_hub.view().items()}, 'scope': 'Actual provider execution using all shared rules, all module identities, live neural state and chosen evidence. App weights are context; Llama parameters are unchanged.'}

    def submit(self, body):
        prompt = body.get('prompt')
        provider = body.get('provider', 'llama')
        ids = body.get('source_ids', [])
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 4000:
            raise ValueError('Enter 1–4,000 characters')
        if provider not in ('llama', 'gemini', 'chatgpt'):
            raise ValueError('Choose a model provider')
        if type(body.get('latest_research', False)) is not bool:
            raise ValueError('Latest research must be true or false')
        if not isinstance(ids, list) or any((not isinstance(i, str) for i in ids)):
            raise ValueError('Choose source IDs')
        ids = list(ids)
        if body.get('latest_research'):
            if not any((s['id'] == 'opportunity-watch' and s.get('text') for s in self.rt.source_hub.view())):
                raise ValueError('No research report is available yet. Run Internet watch or turn off latest research.')
            ids = list(dict.fromkeys(ids + ['opportunity-watch']))
        self.rt.source_hub.selected_context(ids)
        if self.rt.stop.is_set():
            raise ValueError('The runtime is stopping')
        if provider != 'llama' and (not self.rt.model_hub.view()[provider]['configured']):
            raise ValueError('Configure this provider in its model panel first')
        with self.lock:
            if self.busy:
                raise ValueError('An inference is already running')
            self.busy = True
            job = {'id': uuid.uuid4().hex[:12], 'prompt': prompt.strip(), 'provider': provider, 'model': self.rt.model_hub.models[provider], 'source_ids': ids, 'created': now(), 'status': 'queued', 'answer': None, 'error': None, 'context': None, 'references': [], 'field_at_submission': self.rt.neural_output, 'external_action': False}
            self.jobs.append(job)
            self.jobs = self.jobs[-20:]
            save_json(self.path, self.jobs)
        threading.Thread(target=self.run, args=(job,), daemon=True, name='inference-engine').start()
        return {'accepted': True, 'id': job['id']}

    def run(self, job):
        provider = job['provider']
        started = time.monotonic()
        reserved = False
        error = None
        try:
            self.rt.model_hub.reserve(provider, 'inference engine')
            reserved = True
            with self.lock:
                job.update(status='running', started=now())
                save_json(self.path, self.jobs)
            prompt = 'Answer the request using the shared system rules and available evidence. State the answer, its evidence, material uncertainties and useful next steps. Distinguish model inference from observed facts. Do not claim to execute actions.\nREQUEST: ' + job['prompt']
            message, history, refs, characters = self.rt.model_hub.with_sources(provider, prompt, [{'role': 'user', 'content': prompt}], job['source_ids'])
            answer, coverage = self.rt.model_hub.complete(provider, message, history, max_tokens=768)
            if not answer.strip():
                raise ValueError('The provider returned no answer')
            with self.lock:
                job.update(status='complete', answer=answer, context=coverage, references=refs, reference_characters=characters)
            self.rt.activate('model:' + provider, 1)
            self.rt.binary_bus.feed('inference-answer', {'id': job['id'], 'answer': answer})
        except Exception as exc:
            error = str(exc)
            with self.lock:
                job.update(status='error', error=error)
            self.rt.activate('model:' + provider, 0)
        finally:
            if reserved:
                self.rt.model_hub.release(provider, error)
            with self.lock:
                job.update(finished=now(), duration_ms=round((time.monotonic() - started) * 1000))
                self.busy = False
                save_json(self.path, self.jobs)
            self.rt.publish('inference-result', {'id': job['id'], 'provider': provider, 'model': job['model'], 'status': job['status'], 'duration_ms': job['duration_ms'], 'external_action': False})
