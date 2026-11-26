"""Controls and durable receipts for the independent local mesh module."""
import json
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSplitter, QVBoxLayout, QWidget
from ..source.mesh_worker import ContinuousMeshModule
from ..source.mesh_engine import prepare_mesh_run
from ..source.text_view import update_text
MESH_TEMPLATE = {'text': 'Maintain the baseline floor and 1=1 parity.', 'gateway_metrics': {'human_utility': 1.0, 'open_transparency': 1.0, 'serves_opaque_monetary_toll': 0.0}, 'mesh': {'target_floor': 60.0, 'global_reserve': 1500.0, 'container_delusion_bits': [1, 1, 1], 'nodes': {'End_User_Data_Layer': 25.0, 'Gateway_Proxy_Layer': 45.0, 'Core_Substrate_Mesh': 95.0}}}

class MeshPages:

    def init_mesh_module(self):
        self.mesh_module = ContinuousMeshModule(self.hub.db_path, lambda: (self.hub.host, self.hub.port), lambda: self.hub.is_running)
        self.mesh_history_rows = []
        self.mesh_last_refresh = 0
        self.mesh_pending = None
        self.mesh_rendered = None

    def build_mesh_overview(self, layout):
        row = QHBoxLayout()
        self.mesh_toggle = QCheckBox('Continuous local mesh gateway')
        self.mesh_toggle.setChecked(self.mesh_module.enabled)
        self.mesh_toggle.toggled.connect(self.toggle_mesh_module)
        row.addWidget(self.mesh_toggle)
        self.mesh_overview_status = QLabel('Ready')
        self.mesh_overview_status.setObjectName('muted')
        row.addWidget(self.mesh_overview_status, 1)
        open_page = QPushButton('Open mesh + session bridge →')
        open_page.clicked.connect(lambda: self.navigate(20))
        row.addWidget(open_page)
        layout.addLayout(row)

    def toggle_mesh_module(self, enabled):
        try:
            self.mesh_module.set_enabled(enabled)
            self.mesh_module.start()
        except Exception as error:
            self.mesh_toggle.blockSignals(True)
            self.mesh_toggle.setChecked(self.mesh_module.enabled)
            self.mesh_toggle.blockSignals(False)
            self.mesh_overview_status.setText(str(error))
            return
        self.render_mesh_page()

    def build_mesh_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel('New captured inputs pass through email redaction, the supplied score formula, resource-floor calculations, parity inversion and the local session bridge. Sending uses the existing Flux Bus TCP hub. Overview controls automatic processing; Send once also works while paused.')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.mesh_target = QLabel()
        self.mesh_target.setObjectName('eyebrow')
        layout.addWidget(self.mesh_target)
        controls = QHBoxLayout()
        self.mesh_sessions = QComboBox()
        self.mesh_sessions.addItem('Latest result', None)
        self.mesh_sessions.currentIndexChanged.connect(self.show_mesh_result)
        controls.addWidget(self.mesh_sessions, 1)
        retry = QPushButton('Retry selected')
        retry.clicked.connect(self.retry_mesh_selected)
        controls.addWidget(retry)
        copy = QPushButton('Copy result')
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.mesh_result.toPlainText()))
        controls.addWidget(copy)
        layout.addLayout(controls)
        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        column = QVBoxLayout(left)
        column.setContentsMargins(0, 0, 8, 0)
        self.mesh_input = QPlainTextEdit()
        self.mesh_input.setPlaceholderText('Paste text, code or JSON. Use the supplied example for node capacities, reserve and scoring inputs.')
        column.addWidget(self.mesh_input, 1)
        privacy = QLabel('Emails are removed automatically. Additional identifiers to remove (one per line):')
        privacy.setWordWrap(True)
        column.addWidget(privacy)
        self.mesh_identifiers = QPlainTextEdit()
        self.mesh_identifiers.setMaximumHeight(80)
        self.mesh_identifiers.setPlainText('\n'.join(self.mesh_module.settings['identifiers']))
        column.addWidget(self.mesh_identifiers)
        save = QPushButton('Save identifiers for new inputs')
        save.clicked.connect(self.save_mesh_identifiers)
        column.addWidget(save)
        note = QLabel('Other identifying details can remain. The random routing tag does not guarantee anonymity.')
        note.setObjectName('muted')
        note.setWordWrap(True)
        column.addWidget(note)
        row = QHBoxLayout()
        example = QPushButton('Supplied example')
        example.clicked.connect(self.add_mesh_example)
        row.addWidget(example)
        preview = QPushButton('Preview')
        preview.clicked.connect(self.preview_mesh)
        row.addWidget(preview)
        self.mesh_send = QPushButton('Send once')
        self.mesh_send.setObjectName('primary')
        self.mesh_send.clicked.connect(self.send_mesh_input)
        row.addWidget(self.mesh_send)
        column.addLayout(row)
        self.mesh_input_status = QLabel('Ready')
        self.mesh_input_status.setWordWrap(True)
        column.addWidget(self.mesh_input_status)
        split.addWidget(left)
        right = QWidget()
        results = QVBoxLayout(right)
        results.setContentsMargins(8, 0, 0, 0)
        self.mesh_bits = QLabel('Waiting for the first input')
        self.mesh_bits.setWordWrap(True)
        self.mesh_bits.setObjectName('eyebrow')
        results.addWidget(self.mesh_bits)
        self.mesh_result = QPlainTextEdit()
        self.mesh_result.setReadOnly(True)
        results.addWidget(self.mesh_result, 1)
        split.addWidget(right)
        split.setSizes([430, 650])
        layout.addWidget(split, 1)
        self.pages.addWidget(page)

    def save_mesh_identifiers(self):
        try:
            self.mesh_module.set_identifiers(self.mesh_identifiers.toPlainText().splitlines())
            self.mesh_input_status.setText('Saved · applies to newly prepared inputs')
        except Exception as error:
            self.mesh_input_status.setText(str(error))

    def add_mesh_example(self):
        example = dict(MESH_TEMPLATE)
        if self.mesh_input.toPlainText():
            example['text'] = self.mesh_input.toPlainText()
        self.mesh_input.setPlainText(json.dumps(example, indent=2))
        self.mesh_input_status.setText('Supplied example balances · edit as needed, then preview or send')

    def preview_mesh(self):
        text = self.mesh_input.toPlainText()
        if not text.strip():
            self.mesh_input_status.setText('Enter an input first')
            return
        try:
            result = prepare_mesh_run(text, f'tcp://{self.hub.host}:{self.hub.port}', self.mesh_module.session_id, self.mesh_identifiers.toPlainText().splitlines())
            self.display_mesh_result({'status': 'PREVIEW', 'result': result})
            self.mesh_rendered = 'preview'
            self.mesh_input_status.setText('Preview only · no packet sent')
        except Exception as error:
            self.mesh_input_status.setText(str(error))

    def queue_mesh_input(self, job_id):
        self.mesh_module.request(job_id)
        self.mesh_module.start()
        self.mesh_pending = job_id
        self.mesh_sessions.setCurrentIndex(0)
        self.mesh_input_status.setText('Queued · ' + job_id)

    def send_mesh_input(self):
        text = self.mesh_input.toPlainText()
        if not text.strip():
            self.mesh_input_status.setText('Enter an input first')
            return
        try:
            self.mesh_module.set_identifiers(self.mesh_identifiers.toPlainText().splitlines())
            job = self.pipeline.submit('Mesh manual', uuid.uuid4().hex, text, self.pipeline_context(), force=True)
            self.queue_mesh_input(job)
        except Exception as error:
            self.mesh_input_status.setText(str(error))

    def retry_mesh_selected(self):
        job = self.mesh_sessions.currentData() or self.mesh_module.snapshot()['latest'].get('job_id')
        if job:
            self.queue_mesh_input(job)

    def show_mesh_result(self):
        job = self.mesh_sessions.currentData() or self.mesh_module.snapshot()['latest'].get('job_id')
        detail = self.mesh_module.detail(job) if job else None
        if detail:
            detail.pop('result_json', None)
            self.display_mesh_result(detail)
            self.mesh_rendered = (job, detail['status'], detail['attempts'])

    def display_mesh_result(self, detail):
        result = detail.get('result', {})
        gateway = result.get('GATEWAY_REPORT', {})
        bits = result.get('BINARY', [])
        trits = result.get('BALANCED_TERNARY', [])
        self.mesh_bits.setText(f"{detail.get('status', '')} · Local hub connected: {bool(gateway.get('DELIVERY', {}).get('delivery_confirmed'))}" + '\nGateway bits: ' + str(gateway.get('MESH_INTEGRATION_ARRAY', [])) + ' · Corrected parity: ' + str(result.get('CORRECTED_SUBSTRATE_PARITY_VECTOR', [])) + '\nBinary: ' + ''.join(map(str, bits)) + ' · Balanced ternary: ' + ' '.join(({-1: '−', 0: '0', 1: '+'}[v] for v in trits)))
        update_text(self.mesh_result, json.dumps(detail, indent=2, ensure_ascii=False))

    def render_mesh_page(self):
        state = self.mesh_module.snapshot()
        latest = state['latest']
        status = 'Sending' if state['active_job'] else 'Running' if state['running'] and state['enabled'] else 'Paused' if not state['enabled'] else 'Ready'
        self.mesh_overview_status.setText(state['error'] or status + ' · ' + latest.get('status', 'waiting for inputs'))
        if self.pages.currentIndex() != 20:
            return
        self.mesh_target.setText('LOCAL TARGET  ' + state['target'] + '   ·   ' + self.hub.status)
        if time.monotonic() - self.mesh_last_refresh >= 2:
            self.mesh_last_refresh = time.monotonic()
            rows = self.mesh_module.history()
            if rows != self.mesh_history_rows:
                selected = self.mesh_sessions.currentData()
                self.mesh_sessions.blockSignals(True)
                self.mesh_sessions.clear()
                self.mesh_sessions.addItem('Latest result', None)
                for row in rows:
                    self.mesh_sessions.addItem(row['status'] + ' · ' + row['source'] + ' · ' + row['job_id'][:8], row['job_id'])
                index = self.mesh_sessions.findData(selected)
                if selected and index < 0:
                    self.mesh_sessions.addItem('Saved · ' + selected[:8], selected)
                    index = self.mesh_sessions.count() - 1
                self.mesh_sessions.setCurrentIndex(max(0, index))
                self.mesh_sessions.blockSignals(False)
                self.mesh_history_rows = rows
        if self.mesh_pending:
            detail = self.mesh_module.metadata(self.mesh_pending)
            if detail and detail['status'] not in ('READY',):
                job = self.mesh_pending
                self.mesh_pending = None
                index = self.mesh_sessions.findData(job)
                if index < 0:
                    self.mesh_sessions.addItem('Requested · ' + job[:8], job)
                    index = self.mesh_sessions.count() - 1
                self.mesh_sessions.setCurrentIndex(index)
                self.mesh_input_status.setText(detail['status'] + ' · ' + job)
        job = self.mesh_sessions.currentData() or latest.get('job_id')
        if job:
            detail = self.mesh_module.metadata(job)
            if detail and self.mesh_rendered != 'preview' and ((job, detail['status'], detail['attempts']) != self.mesh_rendered):
                self.show_mesh_result()
