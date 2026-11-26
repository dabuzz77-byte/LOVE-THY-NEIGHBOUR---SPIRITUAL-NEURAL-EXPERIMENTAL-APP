import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from ..source.conversations import ConversationStore
from ..source import cloud_ai as cloud_ai
from ..source import llama as llama

class ConversationTests(unittest.TestCase):

    def test_restart_archive_reopen_and_provider_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'conversations.db'
            store = ConversationStore(path)
            identities = {p: store.snapshot(p)[0] for p in ('llama', 'gemini', 'openai')}
            for provider, identity in identities.items():
                self.assertTrue(store.complete(provider, identity, 'Remember ' + provider, 'Remembered', provider))
            restored = ConversationStore(path)
            for provider, identity in identities.items():
                self.assertEqual(restored.snapshot(provider)[1][0]['content'], 'Remember ' + provider)
                fresh = restored.reset(provider)
                self.assertNotEqual(fresh, identity)
                self.assertEqual(restored.snapshot(provider)[1], [])
                self.assertEqual(len(restored.list(provider)), 2)
                self.assertFalse(restored.complete(provider, identity, 'Late', 'Ignored', provider))
                restored.select(provider, identity)
                self.assertEqual(restored.snapshot(provider)[1][-1]['content'], 'Remembered')
            with self.assertRaises(ValueError):
                restored.select('gemini', identities['openai'])

    def test_gemini_replays_all_turns_and_preserves_signature(self):
        wire = {'role': 'model', 'parts': [{'text': 'Your code is maple', 'thoughtSignature': 'opaque-signature'}]}
        raw = {'candidates': [{'content': wire, 'finishReason': 'STOP'}]}
        with patch('cloud_ai.request_json', return_value=raw) as request:
            first = cloud_ai.generate('gemini', 'test-key', 'model', 'Remember maple')
            history = [{'role': 'user', 'content': 'Remember maple'}, {'role': 'assistant', 'content': first['output'], 'wire': first['conversation_reply']}]
            cloud_ai.generate('gemini', 'test-key', 'model', 'What was my code?', {'now': 2}, history)
            body = request.call_args.args[3]
            self.assertEqual([m['role'] for m in body['contents']], ['user', 'model', 'user'])
            self.assertEqual(body['contents'][1], wire)
            self.assertIn('"now": 2', body['contents'][-1]['parts'][0]['text'])

    def test_openai_replays_messages_phase_and_encrypted_reasoning(self):
        wire = [{'type': 'reasoning', 'id': 'rs_1', 'summary': [], 'encrypted_content': 'opaque'}, {'type': 'message', 'id': 'msg_1', 'role': 'assistant', 'phase': 'final_answer', 'content': [{'type': 'output_text', 'text': 'Maple remembered', 'annotations': []}]}]
        with patch('cloud_ai.request_json', return_value={'status': 'completed', 'output': wire}) as request:
            first = cloud_ai.generate('openai', 'test-key', 'model', 'Remember maple')
            history = [{'role': 'user', 'content': 'Remember maple'}, {'role': 'assistant', 'content': first['output'], 'wire': first['conversation_reply']}]
            cloud_ai.generate('openai', 'test-key', 'model', 'What code?', history=history)
            body = request.call_args.args[3]
            self.assertEqual(body['input'][0], history[0])
            self.assertEqual(body['input'][1:3], wire)
            self.assertEqual(body['input'][-1]['content'], 'What code?')
            self.assertFalse(body['store'])

    def test_llama_replays_dialogue_with_current_context(self):
        answer = json.dumps({'answer': 'Maple', 'assessment': 'unresolved', 'reason': 'Conversation context', 'citations': []})
        history = [{'role': 'user', 'content': 'Remember maple'}, {'role': 'assistant', 'content': answer}]
        with patch('llama.request_json', return_value={'message': {'content': answer}}) as request:
            result = llama.guide('test', 'What code?', {'counts': {'python': 3}}, [], {}, history)
            messages = request.call_args.args[1]['messages']
            self.assertEqual(messages[1:3], history)
            self.assertEqual(json.loads(messages[-1]['content'])['input'], 'What code?')
            self.assertEqual(result['conversation_reply'], answer)

class ConversationUITests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        from ..source import app as app
        from ..source.monitor import SystemBusMonitor
        self.folder = tempfile.TemporaryDirectory()
        self.window = app.GraphicalVirtueMatrixEngine(SystemBusMonitor(), self.folder.name, start_services=False)
        self.window.timer.stop()
        self.window.pipeline_auto.setChecked(False)

    def tearDown(self):
        self.window.close()
        self.folder.cleanup()

    def wait(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            self.window.tick()
            self.application.processEvents()
            time.sleep(0.01)
        self.assertTrue(condition())

    def test_cloud_continuation_archive_selection_reset_and_failure(self):
        w = self.window
        for provider in ('gemini', 'openai'):
            c = w.cloud_controls[provider]
            c['key'].setText('dummy-key')
            c['include'].setChecked(False)
            calls = []

            def reply(service, key, model, prompt, state, history=None, context_options=None):
                calls.append(history)
                return {'model': model, 'output': 'Saved answer ' + prompt, 'input': prompt, 'status': 'completed', 'usage': {}}
            with patch('data_pages.generate', side_effect=reply):
                for prompt in ('Remember maple', 'What was the code?'):
                    c['input'].setPlainText(prompt)
                    w.send_cloud(provider)
                    self.wait(lambda: provider not in w.cloud_busy)
            self.assertEqual(calls[0], [])
            self.assertEqual([m['role'] for m in calls[1]], ['user', 'assistant'])
            self.assertIn('Remember maple', c['conversation'].toPlainText())
            original = w.conversations.snapshot(provider)[0]
            with patch('data_pages.generate', side_effect=RuntimeError('offline')):
                w.send_cloud(provider)
                self.wait(lambda: provider not in w.cloud_busy)
            self.assertEqual(len(w.conversations.snapshot(provider)[1]), 4)
            c['reset'].click()
            self.assertEqual(w.conversations.snapshot(provider)[1], [])
            self.assertEqual(c['sessions'].count(), 2)
            self.assertEqual(c['key'].text(), 'dummy-key')
            c['sessions'].setCurrentIndex(c['sessions'].findData(original))
            self.assertEqual(len(w.conversations.snapshot(provider)[1]), 4)
            c['input'].setPlainText('Continue saved conversation')
            with patch('data_pages.generate', side_effect=reply):
                w.send_cloud(provider)
                self.wait(lambda: provider not in w.cloud_busy)
            self.assertEqual(len(calls[-1]), 4)
            w.preview_cloud(provider)
            self.assertIn('Saved answer Remember maple', c['preview'].toPlainText())

    def test_cloud_reset_ignores_old_success_and_error_while_new_request_pending(self):
        w = self.window
        for provider in ('gemini', 'openai'):
            c = w.cloud_controls[provider]
            c['key'].setText('dummy-key')
            c['include'].setChecked(False)
            captured = []
            with patch.object(w, '_background', side_effect=lambda kind, fn: captured.append(kind)):
                c['input'].setPlainText('old')
                w.send_cloud(provider)
                c['reset'].click()
                c['input'].setPlainText('new')
                w.send_cloud(provider)
            w.data_events.put((captured[0], {'output': 'old reply'}, None))
            w.data_events.put((captured[0], None, 'old error'))
            w.tick_data_pages()
            self.assertIn(provider, w.cloud_busy)
            self.assertFalse(c['send'].isEnabled())
            self.assertEqual(w.conversations.snapshot(provider)[1], [])
            w.data_events.put((captured[1], {'model': 'test', 'output': 'new reply', 'input': 'new', 'status': 'completed', 'usage': {}}, None))
            w.tick_data_pages()
            self.assertEqual(w.conversations.snapshot(provider)[1][-1]['content'], 'new reply')

    def test_llama_memory_reset_and_archive_reopen(self):
        w = self.window
        w.model_combo.addItem('test')
        calls = []

        def guide(model, prompt, snapshot, articles, route, history=None):
            calls.append(history)
            return {'model': model, 'answer': 'Maple remembered', 'reason': 'From conversation', 'assessment': 'unresolved', 'citations': [], 'node_evaluations': []}
        with patch('app.llama.guide', side_effect=guide):
            for prompt in ('Remember maple', 'What code?'):
                w.prompt_input.setPlainText(prompt)
                w.ask_llama()
                self.wait(lambda: not w.llama_busy)
        self.assertEqual(len(calls[1]), 2)
        self.assertIn('Maple remembered', calls[1][1]['content'])
        original = w.conversations.snapshot('llama')[0]
        w.llama_reset.click()
        self.assertEqual(w.conversations.snapshot('llama')[1], [])
        w.llama_sessions.setCurrentIndex(w.llama_sessions.findData(original))
        self.assertIn('Remember maple', w.llama_conversation.toPlainText())
        restored = ConversationStore(Path(self.folder.name) / 'conversations.sqlite3')
        self.assertEqual(len(restored.snapshot('llama')[1]), 4)

    def test_llama_late_result_cannot_change_model_after_reset(self):
        w = self.window
        old = w.conversations.snapshot('llama')[0]
        w.llama_request = 'old'
        w.llama_reset.click()
        w.llama_request = 'new'
        w.llama_busy = True
        route = w.read_route()
        w.receive_guidance({'token': 'old', 'conversation_id': old, 'result': {'assessment': 'evil'}})
        w.events_queue.put(('guide_error', {'token': 'old', 'error': 'late'}))
        w.tick()
        self.assertTrue(w.llama_busy)
        self.assertEqual(w.read_route(), route)
        self.assertEqual(w.conversations.snapshot('llama')[1], [])

    def test_all_conversation_views_preserve_scroll_and_follow_only_at_bottom(self):
        w = self.window
        w.resize(1440, 960)
        w.show()
        for provider, index in (('llama', 5), ('gemini', 16), ('openai', 17)):
            w.navigate(index)
            self.application.processEvents()
            identity, _ = w.conversations.snapshot(provider)
            long_text = '\n'.join((f'Earlier line {i}' for i in range(220)))
            w.conversations.complete(provider, identity, 'Long conversation', long_text, 'test')
            w.refresh_conversation(provider)
            self.application.processEvents()
            widget = w.llama_conversation if provider == 'llama' else w.cloud_controls[provider]['conversation']
            bar = widget.verticalScrollBar()
            self.assertGreater(bar.maximum(), 30)
            bar.setValue(12)
            before = bar.value()
            for _ in range(3):
                w.refresh_conversation(provider)
                self.application.processEvents()
            self.assertEqual(bar.value(), before)
            w.conversations.complete(provider, identity, 'Next', 'New reply\n' * 60, 'test')
            w.refresh_conversation(provider)
            self.application.processEvents()
            self.assertEqual(bar.value(), before)
            bar.setValue(bar.maximum())
            w.conversations.complete(provider, identity, 'More', 'Another reply\n' * 60, 'test')
            w.refresh_conversation(provider)
            self.application.processEvents()
            self.assertEqual(bar.value(), bar.maximum())
            bar.setValue(8)
            self.application.processEvents()
            w.refresh_conversation(provider)
            self.assertEqual(bar.value(), 8)

    def test_live_text_updates_preserve_scroll_and_selection(self):
        from ..source.text_view import update_text
        from PySide6.QtWidgets import QPlainTextEdit, QTextBrowser
        from PySide6.QtGui import QTextCursor
        widget = QPlainTextEdit()
        widget.resize(450, 240)
        widget.show()
        try:
            text = '\n'.join((f'Log line {i}' for i in range(150)))
            update_text(widget, text)
            cursor = widget.textCursor()
            cursor.setPosition(30)
            cursor.setPosition(42, QTextCursor.MoveMode.KeepAnchor)
            widget.setTextCursor(cursor)
            widget.verticalScrollBar().setValue(20)
            selection = widget.textCursor().selectedText()
            update_text(widget, text + '\nnew activity', follow=True)
            self.application.processEvents()
            self.assertEqual(widget.verticalScrollBar().value(), 20)
            self.assertEqual(widget.textCursor().selectedText(), selection)
            update_text(widget, text.replace('Log line', 'New line'))
            self.application.processEvents()
            self.assertEqual(widget.verticalScrollBar().value(), 20)
        finally:
            widget.close()
        rich = QTextBrowser()
        rich.resize(450, 240)
        rich.show()
        try:
            update_text(rich, '<p>Reading</p>' * 150, rich=True)
            self.application.processEvents()
            rich.verticalScrollBar().setValue(80)
            update_text(rich, '<p>Updated</p>' * 151, rich=True)
            self.application.processEvents()
            self.assertEqual(rich.verticalScrollBar().value(), 80)
        finally:
            rich.close()
