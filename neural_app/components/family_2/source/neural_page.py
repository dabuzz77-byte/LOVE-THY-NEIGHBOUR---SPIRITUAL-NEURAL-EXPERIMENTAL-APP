"""Learning, automatic research and supplied ledger engines in one workspace."""
from copy import deepcopy
import json
import time
import uuid
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QTabWidget, QSplitter, QPlainTextEdit, QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QApplication
from ..source.neural_learning import NeuralLearning
from ..source.souls_ingress import ContinuousSoulsModule, INPUT_TEMPLATE
from ..source.resource_governor import INPUT_TEMPLATE as GOVERNOR_TEMPLATE
from ..source.central_bank_mesh import INPUT_TEMPLATE as MESH_TEMPLATE
from ..source.world_banking import INPUT_TEMPLATE as WORLD_TEMPLATE
from ..source.web_research import WebResearch
from ..source.routing import balanced_ternary
from ..source.text_view import update_text
from ..source.engine_graphics import DataGraphic

def examples():
    return {**deepcopy(INPUT_TEMPLATE), 'resource_governor': deepcopy(GOVERNOR_TEMPLATE), 'central_bank_mesh': deepcopy(MESH_TEMPLATE), 'world_banking': deepcopy(WORLD_TEMPLATE)}

def label(text):
    item = QLabel(text)
    item.setWordWrap(True)
    return item

class NeuralActivityGrid(QWidget):

    def __init__(self):
        super().__init__()
        self.values = []
        self.setMinimumHeight(145)

    def set_values(self, values):
        self.values = list(values)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = (self.width() - 28) / 8
        for i in range(8):
            val = self.values[i] if i < len(self.values) else None
            rect = QRectF(4 + i * width, 14, width - 8, 88)
            color = QColor('#87F7C4' if val is not None and val >= 0 else '#72B9F5')
            color.setAlphaF(0.13 if val is None else 0.16 + 0.6 * min(1, abs(val)))
            p.setBrush(color)
            p.setPen(QPen(QColor('#324452'), 1))
            p.drawRoundedRect(rect, 8, 8)
            p.setPen(QColor('#E7F0F3'))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, '—' if val is None else f'{val:+.3f}\nbit {int(val >= 0)}')
            p.drawText(QRectF(rect.left(), 110, rect.width(), 22), Qt.AlignmentFlag.AlignCenter, f'NEURON {i + 1}')
        p.end()

class NeuralPages:

    def init_neural_pages(self):
        self.souls_ingress = ContinuousSoulsModule(self.hub.db_path)
        self.neural = NeuralLearning(self.hub.db_path)
        self.web_research = WebResearch(self.store, self.pipeline)
        self.neural_last_render = 0
        self.neural_rows = None
        self.souls_rows = None
        self.neural_selected = None

    def build_neural_overview(self, layout):
        for attr, text, service in (('neural_toggle', 'Neural learning', self.neural), ('souls_toggle', 'Souls + banking engines', self.souls_ingress), ('research_toggle', 'Automatic web research', self.web_research)):
            row = QHBoxLayout()
            switch = QCheckBox(text)
            switch.setChecked(service.enabled)
            setattr(self, attr, switch)
            switch.toggled.connect(lambda value, s=service: self.set_learning_switch(s, value))
            row.addWidget(switch)
            row.addStretch()
            if attr == 'neural_toggle':
                self.neural_overview_status = label('Learning from new inputs')
                row.addWidget(self.neural_overview_status, 1)
                button = QPushButton('Learning + research →')
                button.clicked.connect(lambda: self.navigate(25))
                row.addWidget(button)
            layout.addLayout(row)

    def set_learning_switch(self, service, value):
        try:
            service.set_enabled(value)
            service.start()
        except Exception as error:
            self.neural_overview_status.setText(str(error))

    def build_neural_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.neural_headline = label('NEURAL LEARNING · Ready')
        self.neural_headline.setObjectName('eyebrow')
        layout.addWidget(self.neural_headline)
        layout.addWidget(label('Patterns come from engine results, system activity and web references. Your ratings and explicit targets teach preferences. Every existing engine continues to run its original logic.'))
        row = QHBoxLayout()
        self.learn_web = QCheckBox('Learn from web')
        self.learn_web.setChecked(self.neural.web)
        self.learn_activity = QCheckBox('Learn from activity')
        self.learn_activity.setChecked(self.neural.activity)
        self.learn_web.toggled.connect(lambda value: self.neural.configure(web=value))
        self.learn_activity.toggled.connect(lambda value: self.neural.configure(activity=value))
        row.addWidget(self.learn_web)
        row.addWidget(self.learn_activity)
        row.addStretch()
        layout.addLayout(row)
        tabs = QTabWidget()
        self.learning_tabs = tabs
        tabs.addTab(self.build_learning_workspace(), 'Learn + feedback')
        tabs.addTab(self.build_weights_workspace(), 'Engine weights')
        tabs.addTab(self.build_research_workspace(), 'Web research')
        tabs.addTab(self.build_souls_workspace(), 'Souls + banking engines')
        layout.addWidget(tabs, 1)
        self.pages.addWidget(page)

    def build_learning_workspace(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.neural_grid = NeuralActivityGrid()
        layout.addWidget(self.neural_grid)
        self.neural_score = label('Preference score: not trained yet')
        layout.addWidget(self.neural_score)
        split = QSplitter()
        left = QWidget()
        col = QVBoxLayout(left)
        col.addWidget(label('Text / command / structured input'))
        self.neural_input = QPlainTextEdit()
        self.neural_input.setPlaceholderText('Enter text or JSON. Optional: {"text":"…", "neural":{"target":0.9}}')
        col.addWidget(self.neural_input, 1)
        row = QHBoxLayout()
        self.neural_target_on = QCheckBox('Supply target')
        self.neural_target = QDoubleSpinBox()
        self.neural_target.setRange(0, 1)
        self.neural_target.setSingleStep(0.05)
        self.neural_target.setValue(0.9)
        row.addWidget(self.neural_target_on)
        row.addWidget(self.neural_target)
        col.addLayout(row)
        run = QPushButton('Run engines + learn')
        run.setObjectName('primary')
        run.clicked.connect(self.run_neural_input)
        col.addWidget(run)
        self.neural_input_status = label('Ready')
        col.addWidget(self.neural_input_status)
        split.addWidget(left)
        right = QWidget()
        col = QVBoxLayout(right)
        self.neural_history = QComboBox()
        self.neural_history.addItem('Latest learned result', None)
        self.neural_history.currentIndexChanged.connect(self.show_neural_result)
        col.addWidget(self.neural_history)
        row = QHBoxLayout()
        self.feedback_score = QDoubleSpinBox()
        self.feedback_score.setRange(0, 1)
        self.feedback_score.setSingleStep(0.05)
        self.feedback_score.setValue(1)
        row.addWidget(label('Your rating'))
        row.addWidget(self.feedback_score)
        train = QPushButton('Teach this result')
        train.clicked.connect(self.teach_neural)
        row.addWidget(train)
        col.addLayout(row)
        self.feedback_note = QLineEdit()
        self.feedback_note.setPlaceholderText('Optional feedback note')
        col.addWidget(self.feedback_note)
        self.neural_detail = QPlainTextEdit()
        self.neural_detail.setReadOnly(True)
        col.addWidget(self.neural_detail, 1)
        split.addWidget(right)
        split.setSizes([450, 620])
        layout.addWidget(split, 1)
        return page

    def build_weights_workspace(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.weight_graph = DataGraphic('weights', 200)
        self.weight_graph.setMaximumHeight(220)
        layout.addWidget(self.weight_graph)
        layout.addWidget(label('Each engine has a trainable input weight. 1.0 is the starting weight; missing engine results are excluded from training. These weights influence the added prediction, without changing engine formulas.'))
        self.neural_weights = QTableWidget(0, 2)
        self.neural_weights.setHorizontalHeaderLabels(['ENGINE / INPUT GROUP', 'LEARNED WEIGHT'])
        self.neural_weights.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.neural_weights.setColumnWidth(1, 160)
        self.neural_weights.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.neural_weights, 1)
        row = QHBoxLayout()
        save = QPushButton('Save model snapshot')
        save.clicked.connect(self.save_neural_snapshot)
        row.addWidget(save)
        self.neural_snapshots = QComboBox()
        row.addWidget(self.neural_snapshots, 1)
        restore = QPushButton('Restore selected snapshot')
        restore.clicked.connect(self.restore_neural_snapshot)
        row.addWidget(restore)
        layout.addLayout(row)
        layout.addWidget(label('Weights save automatically. Named snapshots also retain a full model; restoring saves the current model first. Original inputs, conversations and feedback remain stored.'))
        self.refresh_neural_snapshots()
        return page

    def build_research_workspace(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(label('Automatic research follows public concepts found in inputs and engine names. It fetches Wikipedia introductions, then runs their text through the pipeline and learning layer. Add any topic below. Complete prompts and local process paths are not sent as search queries.'))
        row = QHBoxLayout()
        self.research_topic = QLineEdit()
        self.research_topic.setPlaceholderText('Topic to research…')
        row.addWidget(self.research_topic, 1)
        run = QPushButton('Research now')
        run.setObjectName('primary')
        run.clicked.connect(self.request_research)
        row.addWidget(run)
        row.addWidget(label('Seconds between reads'))
        self.research_interval = QSpinBox()
        self.research_interval.setRange(10, 3600)
        self.research_interval.setValue(int(self.web_research.interval))
        self.research_interval.valueChanged.connect(self.web_research.set_interval)
        row.addWidget(self.research_interval)
        layout.addLayout(row)
        self.research_status = label('Ready')
        layout.addWidget(self.research_status)
        self.research_results = QComboBox()
        self.research_results.currentIndexChanged.connect(self.show_research_result)
        layout.addWidget(self.research_results)
        self.research_output = QPlainTextEdit()
        self.research_output.setReadOnly(True)
        layout.addWidget(self.research_output, 1)
        self.research_queue = label('Queued topics')
        layout.addWidget(self.research_queue)
        return page

    def build_souls_workspace(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(label('Four supplied engines: SoulsOverDigitsCore, CentralBankResourceGovernor, CentralBankMeshController and WorldGridCentralBankingCore. Each has a separate neural weight. Receipts show local ledger transfers, conservation, dividends, signatures and quarantine actions.'))
        self.souls_graph = DataGraphic(height=200)
        self.souls_graph.setMaximumHeight(210)
        layout.addWidget(self.souls_graph)
        split = QSplitter()
        left = QWidget()
        col = QVBoxLayout(left)
        self.souls_input = QPlainTextEdit()
        self.souls_input.setPlaceholderText('Load the supplied examples or enter configured ledger JSON')
        col.addWidget(self.souls_input, 1)
        row = QHBoxLayout()
        example = QPushButton('Load all supplied examples')
        example.clicked.connect(lambda: self.souls_input.setPlainText(json.dumps(examples(), indent=2)))
        row.addWidget(example)
        run = QPushButton('Run + learn')
        run.clicked.connect(self.run_souls_input)
        row.addWidget(run)
        col.addLayout(row)
        split.addWidget(left)
        right = QWidget()
        col = QVBoxLayout(right)
        self.souls_history = QComboBox()
        self.souls_history.addItem('Latest run', None)
        self.souls_history.currentIndexChanged.connect(self.show_souls_result)
        col.addWidget(self.souls_history)
        self.souls_result = QPlainTextEdit()
        self.souls_result.setReadOnly(True)
        col.addWidget(self.souls_result, 1)
        copy = QPushButton('Copy result')
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.souls_result.toPlainText()))
        col.addWidget(copy)
        split.addWidget(right)
        split.setSizes([500, 600])
        layout.addWidget(split, 1)
        return page

    def queue_neural_input(self, payload):
        job = self.pipeline.submit('Neural manual', uuid.uuid4().hex, payload, self.pipeline_context(), force=True, run_now=True)
        self.pipeline.start()
        for service in (self.live_audit, self.unified_core, self.platform_alignment, self.karmic_welfare, self.virtue_text, self.souls_ingress, self.reference):
            if service.enabled or service is self.souls_ingress:
                service.request(job)
                service.start()
        self.neural.request(job)
        self.neural.start()
        self.neural_pending = job
        if isinstance(payload, dict) and any((k in payload for k in ('souls_ingress', 'resource_governor', 'central_bank_mesh', 'world_banking'))):
            self.souls_pending = job
        self.neural_input_status.setText('Queued · ' + job)
        return job

    def run_neural_input(self):
        text = self.neural_input.toPlainText()
        if not text.strip():
            return
        try:
            try:
                payload = json.loads(text)
            except ValueError:
                payload = {'text': text}
            if self.neural_target_on.isChecked():
                if not isinstance(payload, dict):
                    payload = {'text': payload}
                payload['neural'] = {**payload.get('neural', {}), 'target': self.neural_target.value()}
            self.queue_neural_input(payload)
        except Exception as error:
            self.neural_input_status.setText(str(error))

    def run_souls_input(self):
        try:
            self.queue_neural_input(json.loads(self.souls_input.toPlainText()))
        except Exception as error:
            update_text(self.souls_result, str(error))

    def show_neural_result(self):
        job = self.neural_history.currentData() or self.neural.snapshot()['latest'].get('job_id')
        if not job:
            return
        result = self.neural.detail(job)
        if result:
            self.neural_selected = job
            view = {k: v for k, v in result.items() if k not in ('x', 'mask', 'feature_schema')}
            update_text(self.neural_detail, json.dumps(view, indent=2, ensure_ascii=False))

    def teach_neural(self):
        try:
            self.neural.add_feedback(self.neural_selected, self.feedback_score.value(), self.feedback_note.text())
            self.neural.start()
            self.neural_input_status.setText('Feedback queued for the selected result')
        except Exception as error:
            self.neural_input_status.setText(str(error))

    def refresh_neural_snapshots(self):
        self.neural_snapshots.clear()
        for row in self.neural.snapshots():
            self.neural_snapshots.addItem(row['name'] + ' · ' + time.strftime('%d %b %H:%M', time.localtime(row['created'])), row['id'])

    def save_neural_snapshot(self):
        self.neural.save_snapshot('Model · ' + str(self.neural.snapshot()['updates']) + ' updates')
        self.refresh_neural_snapshots()

    def restore_neural_snapshot(self):
        identity = self.neural_snapshots.currentData()
        if identity:
            self.neural.restore_snapshot(identity)
            self.refresh_neural_snapshots()

    def request_research(self):
        try:
            self.web_research.request(self.research_topic.text())
            self.web_research.start()
        except Exception as error:
            self.research_status.setText(str(error))

    def show_research_result(self):
        row = self.research_results.currentData()
        if not row:
            return
        article = self.store.search(row['topic'])
        if row['url']:
            article = [a for a in self.store.search() if a['url'] == row['url']]
        update_text(self.research_output, json.dumps({'fetch_receipt': row, 'reference': article}, indent=2, ensure_ascii=False))

    def show_souls_result(self):
        pending = getattr(self, 'souls_pending', None)
        if pending and self.souls_ingress.ready(pending):
            self.souls_pending = None
            self.souls_history.blockSignals(True)
            index = self.souls_history.findData(pending)
            if index < 0:
                self.souls_history.addItem('Requested · ' + pending[:8], pending)
                index = self.souls_history.count() - 1
            self.souls_history.setCurrentIndex(index)
            self.souls_history.blockSignals(False)
        job = self.souls_history.currentData() or self.souls_ingress.snapshot()['latest'].get('job_id')
        if job:
            result = self.souls_ingress.detail(job)
            update_text(self.souls_result, json.dumps(result, indent=2, ensure_ascii=False))
            engines = (result or {}).get('engines', {})
            active = next(((name, value) for name, value in engines.items() if value.get('after')), None)
            if active:
                self.souls_graph.set_data({'engine': active[0], 'state': active[1]['after'], 'actions': active[1].get('actions', [])})

    @staticmethod
    def fill_history(combo, rows, first):
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(first, None)
        for row in rows:
            combo.addItem(row['source'] + ' · ' + row['job_id'][:8], row['job_id'])
        index = combo.findData(selected)
        if selected and index < 0:
            combo.addItem('Selected · ' + selected[:8], selected)
            index = combo.count() - 1
        combo.setCurrentIndex(max(0, index))
        combo.blockSignals(False)

    def render_neural(self):
        if time.monotonic() - self.neural_last_render < 1:
            return
        self.neural_last_render = time.monotonic()
        state = self.neural.snapshot()
        latest = state['latest']
        self.neural_overview_status.setText(state['error'] or ('Learning' if state['enabled'] else 'Paused') + ' · ' + str(state['observations']) + ' observations')
        if self.pages.currentIndex() != 25:
            return
        self.neural_headline.setText(f"NEURAL LEARNING · {state['observations']} observations · {state['feedback']} ratings · {state['targets']} targets")
        if getattr(self, 'neural_pending', None) and self.neural.detail(self.neural_pending):
            self.neural_input_status.setText('Learned and saved · ' + self.neural_pending)
            self.neural_pending = None
        self.neural_grid.set_values(latest.get('activations', []))
        if latest:
            bits = latest['binary']
            number = int(''.join(map(str, bits)), 2)
            self.neural_score.setText(('Learned preference: ' + f"{latest['prediction_after']:.1%}" if latest['trained_preferences'] else 'Preference score: not trained yet') + f" · pattern error {latest['reconstruction_after']:.5f}\nBinary: {''.join(map(str, bits))} · exact balanced ternary: {' '.join(map(str, balanced_ternary(number)))} · {latest['observed_engines']} observed groups")
        tab = self.learning_tabs.currentIndex()
        if tab == 0:
            rows = self.neural.history()
            if rows != self.neural_rows:
                self.fill_history(self.neural_history, rows, 'Latest learned result')
                self.neural_rows = rows
            key = (self.neural_history.currentData(), state['updates'], state['feedback'])
            if key != getattr(self, '_neural_detail_key', None):
                self.show_neural_result()
                self._neural_detail_key = key
        if tab == 1:
            weights = state['weights']
            if weights != getattr(self, '_shown_weights', None):
                self.neural_weights.setRowCount(len(weights))
                for i, row in enumerate(weights):
                    for j, value in enumerate((row['engine'], f"{row['weight']:.6f}")):
                        item = self.neural_weights.item(i, j)
                        if item:
                            item.setText(value)
                        else:
                            self.neural_weights.setItem(i, j, QTableWidgetItem(value))
                self._shown_weights = weights
                if hasattr(self, 'weight_graph'):
                    self.weight_graph.set_data(weights)
        if tab == 3:
            rows = self.souls_ingress.history()
            if rows != self.souls_rows:
                self.fill_history(self.souls_history, rows, 'Latest run')
                self.souls_rows = rows
            key = (self.souls_history.currentData(), self.souls_ingress.snapshot()['latest'].get('job_id'), getattr(self, 'souls_pending', None))
            if key != getattr(self, '_souls_detail_key', None):
                self.show_souls_result()
                self._souls_detail_key = key
        if tab != 2:
            return
        research = self.web_research.snapshot()
        self.research_status.setText(research['status'] + (' · ' + research['error'] if research['error'] else ''))
        history = self.web_research.history()
        if history != getattr(self, 'research_rows', None):
            selected = self.research_results.currentData()
            self.research_results.blockSignals(True)
            self.research_results.clear()
            for row in history:
                self.research_results.addItem(row['status'] + ' · ' + row['topic'], row)
            index = next((i for i, r in enumerate(history) if selected and r['id'] == selected['id']), 0)
            self.research_results.setCurrentIndex(index)
            self.research_results.blockSignals(False)
            self.research_rows = history
            self.show_research_result()
        topics = self.web_research.topics()
        self.research_queue.setText(str(len(topics)) + ' tracked topics · refresh every 6 hours\n' + ', '.join((r['topic'] for r in topics[:12])))
