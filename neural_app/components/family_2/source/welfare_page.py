"""Independent Overview control and inspectable results for all new engines."""
from copy import deepcopy
import json
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSplitter, QVBoxLayout, QWidget
from ..source.karmic_welfare import ContinuousWelfareModule, ENGINE_NAMES, INPUT_TEMPLATE
from ..source.unified_runtime import resolve_result
from ..source.text_view import update_text

class WelfarePages:

    def init_karmic_welfare(self):
        self.karmic_welfare = ContinuousWelfareModule(self.hub.db_path)
        self.welfare_rows = []
        self.welfare_refresh = 0
        self.welfare_pending = None
        self.welfare_view = None
        self.welfare_rendered = None

    def build_welfare_overview(self, layout):
        row = QHBoxLayout()
        self.welfare_toggle = QCheckBox('Continuous karmic + welfare · 3 engines')
        self.welfare_toggle.setChecked(self.karmic_welfare.enabled)
        self.welfare_toggle.toggled.connect(self.toggle_karmic_welfare)
        row.addWidget(self.welfare_toggle)
        self.welfare_status = QLabel('Ready')
        self.welfare_status.setObjectName('muted')
        row.addWidget(self.welfare_status, 1)
        open_page = QPushButton('Inspect karmic + welfare →')
        open_page.clicked.connect(lambda: self.navigate(23))
        row.addWidget(open_page)
        layout.addLayout(row)

    def toggle_karmic_welfare(self, enabled):
        try:
            self.karmic_welfare.set_enabled(enabled)
            self.karmic_welfare.start()
        except Exception as error:
            self.welfare_toggle.blockSignals(True)
            self.welfare_toggle.setChecked(self.karmic_welfare.enabled)
            self.welfare_toggle.blockSignals(False)
            self.welfare_status.setText(str(error))
            return
        self.render_karmic_welfare()

    def build_welfare_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel('KarmicWelfareEngine runs all three engines. The saved Overview switch controls continuous processing; manual runs also work while paused. Inspect local node changes, exact karma totals and welfare register snapshots.')
        intro.setWordWrap(True)
        layout.addWidget(intro)
        top = QHBoxLayout()
        self.welfare_sessions = QComboBox()
        self.welfare_sessions.addItem('Latest result', None)
        self.welfare_sessions.currentIndexChanged.connect(self.show_welfare_result)
        top.addWidget(self.welfare_sessions, 1)
        copy = QPushButton('Copy displayed result')
        self.welfare_copy = copy
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.welfare_output.toPlainText()))
        top.addWidget(copy)
        layout.addLayout(top)
        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        column = QVBoxLayout(left)
        column.setContentsMargins(0, 0, 8, 0)
        self.welfare_input = QPlainTextEdit()
        self.welfare_input.setPlaceholderText('Text, code or JSON. Load the supplied examples to edit node alignments, metric values, karma weights and welfare cycles.')
        column.addWidget(self.welfare_input, 1)
        template = QPushButton('Supplied examples')
        template.clicked.connect(self.add_welfare_template)
        run = QPushButton('Run all three engines')
        run.setObjectName('primary')
        run.clicked.connect(self.run_welfare_input)
        buttons = QHBoxLayout()
        buttons.addWidget(template)
        buttons.addWidget(run)
        column.addLayout(buttons)
        self.welfare_input_status = QLabel('Ready')
        self.welfare_input_status.setWordWrap(True)
        column.addWidget(self.welfare_input_status)
        note = QLabel('Each run saves its original input and complete results. No files are generated automatically.')
        note.setWordWrap(True)
        note.setObjectName('muted')
        column.addWidget(note)
        split.addWidget(left)
        right = QWidget()
        results = QVBoxLayout(right)
        results.setContentsMargins(8, 0, 0, 0)
        self.welfare_engines = QComboBox()
        self.welfare_engines.addItem('KarmicWelfareEngine · complete run', None)
        for i, name in enumerate(ENGINE_NAMES, 1):
            self.welfare_engines.addItem(f'{i:02d}  {name}', name)
        self.welfare_engines.currentIndexChanged.connect(self.display_welfare_selection)
        results.addWidget(self.welfare_engines)
        self.welfare_bits = QLabel('Binary / balanced ternary: waiting for input')
        self.welfare_bits.setWordWrap(True)
        self.welfare_bits.setObjectName('eyebrow')
        results.addWidget(self.welfare_bits)
        self.welfare_output = QPlainTextEdit()
        self.welfare_output.setReadOnly(True)
        results.addWidget(self.welfare_output, 1)
        split.addWidget(right)
        split.setSizes([450, 650])
        layout.addWidget(split, 1)
        self.pages.addWidget(page)

    def add_welfare_template(self):
        example = deepcopy(INPUT_TEMPLATE)
        example['text'] = self.welfare_input.toPlainText() or example['text']
        self.welfare_input.setPlainText(json.dumps(example, indent=2))
        self.welfare_input_status.setText('Supplied example assumptions · edit before running')

    def run_welfare_input(self):
        text = self.welfare_input.toPlainText()
        if not text.strip():
            self.welfare_input_status.setText('Enter an input first')
            return
        try:
            self.queue_welfare_input(text)
        except Exception as error:
            self.welfare_input_status.setText(str(error))

    def queue_welfare_input(self, payload):
        job = self.pipeline.submit('Karmic welfare manual', uuid.uuid4().hex, payload, self.pipeline_context(), force=True)
        self.karmic_welfare.request(job)
        self.karmic_welfare.start()
        self.welfare_pending = job
        self.welfare_sessions.setCurrentIndex(0)
        self.welfare_input_status.setText('Queued · ' + job)
        return job

    def show_welfare_result(self):
        job = self.welfare_sessions.currentData() or self.karmic_welfare.snapshot()['latest'].get('job_id')
        if not job:
            return
        result = self.karmic_welfare.detail(job)
        if result:
            self.welfare_view = result
            self.welfare_rendered = job
            self.display_welfare_selection()

    def display_welfare_selection(self):
        result = self.welfare_view
        if not result:
            return
        name = self.welfare_engines.currentData()
        selected = resolve_result(result, name) if name and name in result.get('engines', {}) else result
        update_text(self.welfare_output, json.dumps(selected, indent=2, ensure_ascii=False))
        statuses = {row['engine']: row['status'] for row in result.get('stages', [])}
        self.welfare_bits.setText((statuses.get(name, '') if name else result['status']) + ' · ' + str(len(statuses)) + ' engines · ' + str(result.get('milliseconds', '—')) + ' ms\nBinary: ' + ''.join(map(str, result.get('binary', []))) + '\nBalanced ternary: ' + ' '.join(({-1: '−', 0: '0', 1: '+'}[x] for x in result.get('balanced_ternary', []))))

    def render_karmic_welfare(self):
        state = self.karmic_welfare.snapshot()
        latest = state['latest']
        status = 'Processing' if state['active_job'] else 'Paused' if not state['enabled'] else 'Running' if state['running'] else 'Ready'
        self.welfare_status.setText(state['error'] or status + ' · ' + str(latest.get('status') or 'waiting for inputs'))
        if self.pages.currentIndex() != 23:
            return
        if time.monotonic() - self.welfare_refresh >= 2:
            self.welfare_refresh = time.monotonic()
            rows = self.karmic_welfare.history()
            if rows != self.welfare_rows:
                selected = self.welfare_sessions.currentData()
                self.welfare_sessions.blockSignals(True)
                self.welfare_sessions.clear()
                self.welfare_sessions.addItem('Latest result', None)
                for row in rows:
                    self.welfare_sessions.addItem(row['status'] + ' · ' + row['source'] + ' · ' + row['job_id'][:8], row['job_id'])
                index = self.welfare_sessions.findData(selected)
                if selected and index < 0:
                    self.welfare_sessions.addItem('Selected · ' + selected[:8], selected)
                    index = self.welfare_sessions.count() - 1
                self.welfare_sessions.setCurrentIndex(max(0, index))
                self.welfare_sessions.blockSignals(False)
                self.welfare_rows = rows
        if self.welfare_pending and self.karmic_welfare.ready(self.welfare_pending):
            job = self.welfare_pending
            self.welfare_pending = None
            index = self.welfare_sessions.findData(job)
            if index < 0:
                self.welfare_sessions.addItem('Requested · ' + job[:8], job)
                index = self.welfare_sessions.count() - 1
            self.welfare_sessions.setCurrentIndex(index)
            self.welfare_input_status.setText('Saved · ' + job)
        job = self.welfare_sessions.currentData() or latest.get('job_id')
        if job != self.welfare_rendered:
            self.show_welfare_result()
