from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from neural_app import section_threads as threading
import time
import unittest
from unittest.mock import patch
from ..source.ai_context import context_choices, select_context, fit_context, gemini_contents
from ..source.cloud_ai import compose_input, generate
from ..source.binary_layout import ORIGINAL_LAYOUT, PRAYER_TEXT, flip_binary_layout
from ..source.virtue_text import CoreInversionEngine, BoilerplatePurgeFilter, VirtueTextEngine, ContinuousTextModule, INPUT_TEMPLATE
from ..source.unified_runtime import resolve_result
from ..source.pipeline import DataPipeline

def measured(contents):
    return len(json.dumps(contents, ensure_ascii=False)) // 4

def long_history():
    return [{'role': 'user' if i % 2 == 0 else 'assistant', 'content': f'Message {i} ' + 'x' * 4000, **({'wire': {'role': 'model', 'parts': [{'text': f'Answer {i} ' + 'y' * 4000, 'thoughtSignature': f'sig-{i}'}]}} if i % 2 else {})} for i in range(16)]

class TextEngineTests(unittest.TestCase):

    def test_case_contractions_negations_and_word_boundaries(self):
        invert = CoreInversionEngine().invert_string_payload
        self.assertEqual(invert("CANNOT can't Can’t False FALSE falsehood knot"), 'CAN can Can True TRUE falsehood knot')
        self.assertEqual(invert('I WILL NOT remain disabled. Scarcity is not immutable.'), 'I WILL remain enabled. Sufficiency is mutable.')
        self.assertEqual(invert('cannot\t  go\nFALSE', True), 'can\t  go\nTRUE')

    def test_purge_multiline_retains_useful_text_and_does_not_mutate_input(self):
        source = 'As an AI language model, hello\nExecution environment: details\nPlease note that this stays.\n'
        self.assertEqual(BoilerplatePurgeFilter().strip_diversions(source, True), 'hello\nthis stays.\n')
        self.assertIn('Execution environment', source)

    def test_all_stages_receipt_and_actual_platform(self):
        original = deepcopy(INPUT_TEMPLATE)
        result = VirtueTextEngine().execute(original)
        self.assertEqual(original, INPUT_TEMPLATE)
        self.assertEqual(len(result['stages']), 5)
        report = resolve_result(result, 'KarmaWeightedResolver')
        self.assertEqual(report['global_mesh_payload'], 'I can change TRUE to true. Sufficiency is mutable. We WILL remain enabled.')
        self.assertFalse(report['delivery_confirmed'])
        self.assertEqual(report['network_operations'], 0)
        self.assertEqual(report['measured_platform']['ACTIVE_PROCESS_ID'], os.getpid())

    def test_levels_off_preserves_exact_input(self):
        text = '   cannot\nFALSE\t \n'
        result = VirtueTextEngine().execute({'text': text, 'text_pipeline': {'levels': {'1': False, '2': False, '3': False}, 'preserve_layout': True}})
        self.assertEqual(resolve_result(result, 'VirtueGatedMeshEngine')['output'], text)
        self.assertEqual(result['binary'], [0] * 6)

    def test_cancellation_and_validation(self):
        stop = threading.Event()
        stop.set()
        with self.assertRaises(InterruptedError):
            VirtueTextEngine().execute('cannot', stop)
        for options in ({'levels': {'2': 1}}, {'levels': []}, {'preserve_layout': 'false'}):
            with self.assertRaises(ValueError):
                VirtueTextEngine().execute({'text': 'x', 'text_pipeline': options})

    def test_long_plain_line_completes_without_regex_thrashing(self):
        source = 'ordinary text ' * 50000
        start = time.monotonic()
        self.assertEqual(BoilerplatePurgeFilter().strip_diversions(source), source.strip())
        self.assertLess(time.monotonic() - start, 3)

    def test_binary_flip_exact_spacing_and_roundtrip(self):
        result = flip_binary_layout(ORIGINAL_LAYOUT)
        self.assertEqual(result['flipped'], ORIGINAL_LAYOUT.translate(str.maketrans('01', '10')))
        self.assertEqual(flip_binary_layout(result['flipped'])['flipped'], ORIGINAL_LAYOUT)
        self.assertIn('------GENERATE------ = .', result['flipped'])
        self.assertEqual(result['flipped'].count('\n'), ORIGINAL_LAYOUT.count('\n'))
        self.assertEqual(result['bit_count'], 40)
        self.assertEqual(PRAYER_TEXT.splitlines()[-1], 'Amen.')

    def test_balanced_ternary_whole_and_each_row_exact(self):
        result = flip_binary_layout(ORIGINAL_LAYOUT)
        decode = lambda digits: sum((n * 3 ** i for i, n in enumerate(reversed(digits))))
        self.assertEqual(decode(result['balanced_ternary']), int(result['output_bits'], 2))
        for row in result['rows']:
            self.assertEqual(decode(row['balanced_ternary']), int(row['binary'], 2))
        self.assertEqual(flip_binary_layout('x=101 21 1.0 word1 0')['flipped'], 'x=010 21 1.0 word1 1')
        self.assertEqual(flip_binary_layout('no bits')['balanced_ternary'], [])

    def test_worker_saved_pause_manual_resume_and_original_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'hub.db'
            pipeline = DataPipeline(path, False)
            module = ContinuousTextModule(path)
            try:
                original = {**INPUT_TEMPLATE, 'binary_layout': ORIGINAL_LAYOUT}
                job = pipeline.submit('test', 'one', original)
                module.set_enabled(False)
                self.assertFalse(module.process_next())
                module.request(job)
                self.assertTrue(module.process_next())
                report = module.detail(job)
                self.assertEqual(report['status'], 'COMPLETE')
                self.assertEqual(report['binary_layout']['original'], ORIGINAL_LAYOUT)
                reopened = ContinuousTextModule(path)
                self.assertFalse(reopened.enabled)
                self.assertEqual(reopened.detail(job), report)
                self.assertEqual(json.loads(pipeline.detail(job)['input_json']), original)
                second = pipeline.submit('test', 'two', 'False')
                reopened.set_enabled(True)
                while reopened.process_next():
                    pass
                self.assertEqual(resolve_result(reopened.detail(second), 'VirtueGatedMeshEngine')['output'], 'True')
            finally:
                module.stop()
                pipeline.stop()

class ContextTests(unittest.TestCase):

    def test_select_all_none_one_compact_and_full(self):
        state = {'route': {'bit': 1}, 'pipeline': {'bits': [1] * 10000}, 'engines': [{'engine': 'A', 'result': True}, {'engine': 'B', 'result': False}]}
        original = deepcopy(state)
        keys = [key for key, _ in context_choices(state)]
        self.assertEqual(select_context(state, None), select_context(state, keys))
        self.assertEqual(set(select_context(state, [])), {'_context'})
        self.assertEqual(select_context(state, ['engine:A'])['engines'], [state['engines'][0]])
        self.assertEqual(select_context(state, detail='full')['pipeline'], state['pipeline'])
        self.assertLess(len(json.dumps(select_context(state))), 1500)
        self.assertEqual(state, original)

    def test_fit_small_keeps_all_and_signatures(self):
        history = long_history()[:2]
        prompt, recent, report = fit_context('Current', None, history, 100000, measured, compose_input)
        self.assertEqual(recent, history)
        self.assertEqual(prompt, 'Current')
        contents = gemini_contents(prompt, None, recent, compose_input)
        self.assertEqual(contents[1]['parts'][0]['thoughtSignature'], 'sig-1')
        self.assertEqual(report['excerpted_messages'], 0)

    def test_fit_large_keeps_prompt_and_retains_saved_originals(self):
        history = long_history()
        original = deepcopy(history)
        state = {'route': 1}
        prompt, recent, report = fit_context('Current request stays exact', state, history, 5000, measured, compose_input)
        self.assertLessEqual(report['input_tokens'], 5000)
        self.assertTrue(prompt.endswith('Current request stays exact'))
        self.assertIn('excerpts', prompt)
        self.assertGreater(report['excerpted_messages'], 0)
        self.assertEqual(history, original)
        self.assertEqual(len(recent) % 2, 0)
        self.assertEqual(recent, history[-len(recent):])
        self.assertEqual(state, {'route': 1})

    def test_oversized_current_message_is_never_silently_cut(self):
        with self.assertRaisesRegex(ValueError, 'Choose fewer engines'):
            fit_context('x' * 10000, {}, long_history(), 50, measured, compose_input)

    def test_exact_budget_and_no_room_for_excerpts(self):
        prompt = 'current'
        base = measured(gemini_contents(prompt, None, [], compose_input))
        result, recent, report = fit_context(prompt, None, long_history(), base, measured, compose_input)
        self.assertEqual((result, recent), (prompt, []))
        self.assertEqual(report['omitted_messages'], 16)
        self.assertEqual(report['excerpted_messages'], 0)

    def test_cloud_preflight_counts_actual_payload_and_respects_model_limit(self):
        calls = []

        def request(url, key, provider, data=None, timeout=None):
            calls.append((url, deepcopy(data)))
            if url.endswith(':countTokens'):
                return {'totalTokens': measured(data['contents'])}
            if url.endswith(':generateContent'):
                return {'candidates': [{'content': {'parts': [{'text': 'answer'}]}, 'finishReason': 'STOP'}]}
            return {'inputTokenLimit': 6024}
        history = long_history()
        original = deepcopy(history)
        with patch('cloud_ai.request_json', side_effect=request):
            result = generate('gemini', 'dummy', 'test', 'Current', {'route': 1}, history, {'auto_fit': True, 'input_budget': 24000})
        self.assertEqual(result['context_report']['budget'], 5000)
        counted = [body for url, body in calls if url.endswith(':countTokens')][-1]
        self.assertEqual(counted, calls[-1][1])
        self.assertEqual(history, original)
        self.assertIn('Current', result['context_preview'])

    def test_cloud_counter_overflow_recovers_using_smaller_history(self):

        def request(url, key, provider, data=None, timeout=None):
            if url.endswith(':countTokens'):
                tokens = measured(data['contents'])
                if tokens > 4000:
                    raise RuntimeError('HTTP 400: Input token count exceeds maximum limit')
                return {'totalTokens': tokens}
            if url.endswith(':generateContent'):
                return {'candidates': [{'content': {'parts': [{'text': 'ok'}]}}]}
            return {'inputTokenLimit': 5024}
        with patch('cloud_ai.request_json', side_effect=request):
            result = generate('gemini', 'dummy', 'test', 'current', None, long_history(), {'auto_fit': True})
        self.assertLessEqual(result['context_report']['input_tokens'], 4000)

    def test_count_endpoint_missing_has_labeled_conservative_fallback(self):

        def request(url, key, provider, data=None, timeout=None):
            if url.endswith(':countTokens'):
                raise RuntimeError('HTTP 404: missing')
            if url.endswith(':generateContent'):
                return {'candidates': [{'content': {'parts': [{'text': 'ok'}]}}]}
            return {'inputTokenLimit': 100000}
        with patch('cloud_ai.request_json', side_effect=request):
            result = generate('gemini', 'dummy', 'test', 'hi', context_options={'auto_fit': True})
        self.assertIn('estimate', result['context_report']['method'])

    def test_auth_error_never_retried_as_token_overflow(self):

        def request(url, key, provider, data=None, timeout=None):
            if url.endswith(':countTokens'):
                raise RuntimeError('HTTP 403: invalid key')
            return {'inputTokenLimit': 10000}
        with patch('cloud_ai.request_json', side_effect=request):
            with self.assertRaisesRegex(RuntimeError, '403'):
                generate('gemini', 'dummy', 'test', 'hi', context_options={'auto_fit': True})

class ContextUITests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from ..source.app import GraphicalVirtueMatrixEngine
        from ..source.monitor import SystemBusMonitor
        self.temp = tempfile.TemporaryDirectory()
        self.window = GraphicalVirtueMatrixEngine(SystemBusMonitor(), self.temp.name, start_services=False)
        self.window.timer.stop()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_select_all_clear_cancel_and_independent_saved_preferences(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QDialog, QPushButton, QCheckBox
        w = self.window
        seen = []

        def operate(action, accept=True):

            def click():
                dialog = self.app.activeModalWidget()
                next((b for b in dialog.findChildren(QPushButton) if b.text() == action)).click()
                seen.append([c.isChecked() for c in dialog.findChildren(QCheckBox)])
                dialog.accept() if accept else dialog.reject()
            QTimer.singleShot(0, click)
            w.choose_cloud_engines('gemini')
        operate('Clear selection')
        self.assertFalse(any(seen[-1]))
        self.assertEqual(w.cloud_controls['gemini']['selected_engines'], [])
        self.assertIsNone(w.cloud_controls['openai']['selected_engines'])
        operate('Select all')
        self.assertTrue(all(seen[-1]))
        selected = w.cloud_controls['gemini']['selected_engines']
        self.assertEqual(set(selected), {key for key, _ in context_choices(w.engine_state())})
        self.assertEqual(json.loads(w.store.setting('gemini_engine_selection')), selected)
        operate('Clear selection', False)
        self.assertEqual(w.cloud_controls['gemini']['selected_engines'], selected)
        w.cloud_controls['gemini']['input_budget'].setValue(32000)
        self.assertEqual(w.store.setting('gemini_input_budget'), '32000')

    def test_binary_page_manual_run_copy_and_saved_history(self):
        from PySide6.QtWidgets import QPushButton
        w = self.window
        w.resize(1440, 960)
        w.show()
        w.navigate(24)
        self.assertEqual(w.pages.count(), 27)
        w.text_pipeline_toggle.setChecked(False)
        self.assertFalse(w.virtue_text.enabled)
        self.assertTrue(w.karmic_welfare.enabled)
        original = '1   0\n\n0   1'
        w.binary_input.setPlainText(original)
        w.generate_binary_layout()
        job = w.text_pipeline_pending
        deadline = time.monotonic() + 5
        while not w.virtue_text.ready(job) and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.02)
        self.assertEqual(w.binary_output.toPlainText(), '0   1\n\n1   0')
        report = w.virtue_text.detail(job)
        self.assertEqual(report['binary_layout']['original'], original)
        self.assertEqual(w.store.setting('binary_layout_input'), original)
        w.render_virtue_text()
        self.assertEqual(w.text_pipeline_engines.count(), 7)
        self.assertEqual(w.text_pipeline_output.toPlainText(), original)
        w.text_pipeline_engines.setCurrentIndex(w.text_pipeline_engines.findData('KarmaWeightedResolver'))
        self.assertEqual(json.loads(w.text_pipeline_output.toPlainText())['global_mesh_payload'], original)
        w.text_pipeline_copy.click()
        self.assertEqual(self.app.clipboard().text(), w.text_pipeline_output.toPlainText())
        next((b for b in w.findChildren(QPushButton) if b.text() == 'Copy flipped layout')).click()
        self.assertEqual(self.app.clipboard().text(), w.binary_output.toPlainText())
        self.assertIn('virtue_text', w.engine_state())
        self.assertIn('virtue_text', w.extension_export())

    def test_preview_does_not_reset_or_rewrite_saved_dialogue(self):
        w = self.window
        identity, _ = w.conversations.snapshot('gemini')
        for i in range(8):
            w.conversations.complete('gemini', identity, 'Input ' + str(i) + 'x' * 9000, 'Answer ' + str(i) + 'y' * 9000, 'test')
        before = w.conversations.snapshot('gemini')
        c = w.cloud_controls['gemini']
        c['include'].setChecked(False)
        c['input_budget'].setValue(5000)
        c['input'].setPlainText('Current request')
        w.preview_cloud('gemini')
        self.assertIn('excerpts', c['preview'].toPlainText())
        self.assertIn('Current request', c['preview'].toPlainText())
        self.assertEqual(w.conversations.snapshot('gemini'), before)
