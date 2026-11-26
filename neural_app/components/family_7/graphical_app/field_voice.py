"""One conversational view over the actual aggregate neural runtime."""
import json
from neural_app import section_threads as threading
from ..graphical_app.sources import save_json

class FieldVoice:

    def __init__(self, runtime):
        self.rt = runtime
        self.lock = threading.RLock()
        self.messages = []
        self.busy = False
        self.error = None
        self.context = None
        self.path = runtime.data / 'field-history.json'
        try:
            self.messages = [m for m in json.loads(self.path.read_text(encoding='utf-8'))[-40:] if isinstance(m, dict) and m.get('role') in ('user', 'assistant') and isinstance(m.get('content'), str)]
        except (OSError, ValueError, TypeError):
            pass
        runtime.node('field-voice', 'Whole-system reply', 'model')
        runtime.edges.setdefault('chiral|field-voice', 0.1)

    def view(self):
        with self.lock:
            return {'messages': [dict(item) for item in self.messages], 'busy': self.busy, 'error': self.error, 'context': self.context}

    def submit(self, text, provider='llama', source_ids=None):
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 5000:
            raise ValueError('Enter 1–5,000 characters')
        self.rt.source_hub.selected_context(source_ids or [])
        with self.lock:
            if self.busy:
                raise ValueError('Wait for the whole-system reply to finish')
            reserved = self.rt.model_hub.begin_interactive(provider, 'field reply')
            self.busy = True
            self.error = None
            self.messages.append({'role': 'user', 'content': text.strip()})
            save_json(self.path, self.messages[-40:])
        self.rt.binary_bus.feed('field-input', text.strip().encode('utf-8'))
        threading.Thread(target=self.run, args=(text.strip(), provider, source_ids or [], reserved), daemon=True).start()
        return {'accepted': True}

    def run(self, text, provider, source_ids, reserved=True):
        error = None
        try:
            if not reserved:
                self.rt.model_hub.await_interactive(provider, 'field reply')
                reserved = True
            with self.rt.lock:
                nodes = sorted((node for node in self.rt.nodes.values() if node['updates']), key=lambda n: abs(n['activation']), reverse=True)
                active = {'field_output': self.rt.neural_output, 'nodes': len(self.rt.nodes), 'connections': len(self.rt.edges), 'strongest_active_nodes': [[n['id'], n['weight'], n['activation']] for n in nodes[:6]], 'bussed_clients': [[p['pid'], p['name']] for p in list(self.rt.clients.values())[:6]], 'chiral_bytes_processed': self.rt.binary_bus.state()['processed_bytes']}
            work = self.rt.workbench.view()['outcomes']
            active['work_outcomes'] = work
            prompt = 'Reply as the single voice of the assembled Postscarcity field, using every shared rule and the complete module inventory in your system context. The numerical neural field provides state and weighted priorities; you provide its language interface. Explain observations and propose useful next steps, without inventing completed actions. Live aggregate and strongest contributions: ' + json.dumps(active, separators=(',', ':')) + '\nUSER: ' + text
            with self.lock:
                history = [dict(item) for item in self.messages[-5:]]
            history[-1]['content'] = prompt
            prompt, history, provenance, reference_chars = self.rt.model_hub.with_sources(provider, prompt, history, source_ids, max_tokens=900)
            response, coverage = self.rt.model_hub.complete(provider, prompt, history, max_tokens=900)
            coverage.update(provider=provider, sources=provenance, reference_characters=reference_chars, field_output=active['field_output'], node_count=active['nodes'])
            with self.lock:
                self.messages.append({'role': 'assistant', 'content': response})
                self.messages = self.messages[-40:]
                self.context = coverage
                save_json(self.path, self.messages)
            self.rt.activate('field-voice', 1)
            self.rt.binary_bus.feed('field-reply', response.encode('utf-8'))
            self.rt.publish('field-reply', {'provider': provider, 'characters': len(response), 'field_output': active['field_output']})
        except Exception as exc:
            error = str(exc)
            self.error = error
            self.rt.activate('field-voice', 0)
        finally:
            with self.lock:
                self.busy = False
            if reserved:
                self.rt.model_hub.release(provider, error)

    def clear(self):
        with self.lock:
            if self.busy:
                raise ValueError('Wait for the reply before clearing')
            self.messages = []
            self.error = None
            self.context = None
            save_json(self.path, self.messages)
        return self.view()
