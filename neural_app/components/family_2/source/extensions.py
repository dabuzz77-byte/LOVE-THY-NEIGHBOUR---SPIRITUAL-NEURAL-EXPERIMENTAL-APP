"""v2 audit, execution, local services and integration pages."""
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import shlex
import sqlite3
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QComboBox, QPlainTextEdit, QTextBrowser, QLineEdit, QScrollArea, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QCheckBox, QSpinBox
from ..source.visuals import Panel, FluxGrid
from ..source.routing import register_record, dispatch_operation
from ..source.engines import run_engine_suite, register_bits
from ..source.audit import UNIVERSAL_LAW, RESOLUTION_CONTEXT
from ..source.hub import LocalInferenceHubServer, MultiSessionHistoryParser, WorldGridFinalCompiler, database
from ..source.history import GoogleHistoryAIEngine, AISessionGrammarParser
from ..source.observatory import ObservatoryBridge
from ..source.live_flux import LiveFluxCanvas
from ..source.data_pages import DataPages
from ..source.text_view import update_text
from ..source.audit_page import AuditPages
from ..source.mesh_page import MeshPages
from ..source.unified_page import UnifiedPages
from ..source.platform_page import PlatformPages
from ..source.welfare_page import WelfarePages
from ..source.text_pipeline_page import TextPipelinePages
from ..source.neural_page import NeuralPages
from ..source.reference_page import ReferencePages

def title(text, muted=False):
    item = QLabel(text)
    item.setWordWrap(True)
    item.setObjectName('muted' if muted else 'eyebrow')
    return item

def action(text, callback, primary=False):
    b = QPushButton(text)
    b.clicked.connect(callback)
    if primary:
        b.setObjectName('primary')
    return b

def box(name=None):
    w = Panel()
    layout = QVBoxLayout(w)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    if name:
        layout.addWidget(title(name))
    return (w, layout)

def readonly():
    text = QPlainTextEdit()
    text.setReadOnly(True)
    return text

class StudioExtensions(DataPages, AuditPages, MeshPages, UnifiedPages, PlatformPages, WelfarePages, TextPipelinePages, NeuralPages, ReferencePages):

    def init_extensions(self):
        self.hub = LocalInferenceHubServer(db_path=self.data_dir / 'world_grid_hub.db')
        self.lexer = MultiSessionHistoryParser(self.hub.db_path)
        self.history_engine = GoogleHistoryAIEngine(self.data_dir / 'google_ai_ingestion.db')
        self.history_parser = AISessionGrammarParser(self.history_engine.db_path)
        self.observatory = ObservatoryBridge(self.hub.db_path)
        self.engine_results = []
        self.activity = []
        self.activity_pending = []
        self.capture_batch = []
        self.last_obs_receipt = None
        self.last_rendered_obs = None
        self.last_hub_rows = None
        self.summary_initialized = False
        self.last_extension_tick = 0
        self.last_history_revision = -1
        self.last_observatory_view = None
        self.last_command = {}
        self.latest_synchronization = {}
        self.last_live_fingerprint = None
        with database(self.hub.db_path) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS execution_ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, kind TEXT, detail TEXT)')
        self.init_data_pages()
        self.init_live_audit()
        self.init_mesh_module()
        self.init_unified_core()
        self.init_platform_alignment()
        self.init_karmic_welfare()
        self.init_virtue_text()
        self.init_reference()
        self.init_neural_pages()

    def start_extensions(self):
        self.start_data_pages()
        self.live_audit.start()
        self.hub.start_listener_bus()
        self.mesh_module.start()
        self.unified_core.start()
        self.platform_alignment.start()
        self.karmic_welfare.start()
        self.virtue_text.start()
        self.souls_ingress.start()
        self.reference.start()
        self.neural.start()
        self.web_research.start()
        self.history_engine.launch_continuous_polling_bus(3)
        self.observatory.start()
        self.log_activity('SERVICES', self.hub.status)

    def stop_extensions(self):
        self.reference.stop()
        self.web_research.stop()
        self.neural.stop()
        self.souls_ingress.stop()
        self.virtue_text.stop()
        self.karmic_welfare.stop()
        self.platform_alignment.stop()
        self.unified_core.stop()
        self.mesh_module.stop()
        self.live_audit.stop()
        self.flush_activity()
        self.stop_data_pages()
        self.hub.terminate()
        self.history_engine.terminate_bus()
        self.observatory.stop()

    def log_activity(self, kind, detail):
        event = {'time': time.time(), 'kind': kind, 'detail': str(detail)}
        self.activity.insert(0, event)
        self.activity = self.activity[:160]
        self.activity_pending.append((event['time'], kind, event['detail']))

    def flush_activity(self):
        if not self.activity_pending:
            return
        batch = self.activity_pending[:]
        with database(self.hub.db_path) as conn:
            from ..source.payload_storage import pack_text
            conn.executemany('INSERT INTO execution_ledger(timestamp,kind,detail) VALUES (?,?,?)', [(stamp, kind, pack_text(conn, detail)) for stamp, kind, detail in batch])
        del self.activity_pending[:len(batch)]

    def build_extensions(self):
        self.build_audit_page()
        self.build_engines_page()
        self.build_hub_page()
        self.build_history_page()
        self.build_observatory_page()
        self.build_summary_page()
        self.build_live_flux_page()
        self.build_data_pages()
        self.build_live_audit_pages()
        self.build_mesh_page()
        self.build_unified_page()
        self.build_platform_page()
        self.build_welfare_page()
        self.build_text_pipeline_page()
        self.build_neural_page()
        self.build_reference_page()
        self.run_engines()

    def build_audit_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page, layout = box('REGISTERED STATE → EVALUATION → CORRECTION')
        layout.addWidget(title('Compare the recorded label with the current assessment. Good preserves the bit; evil applies the previous inversion.', True))
        row = QHBoxLayout()
        self.evaluation_controls = []
        self.audit_cards = []
        for i in range(2):
            panel, col = box(f'0{i + 1} / NODE {i}')
            form = QGridLayout()
            bit = QComboBox()
            bit.addItems(['false / 0', 'true / 1'])
            bit.setCurrentIndex(i)
            registered = QComboBox()
            registered.addItems(['good', 'evil'])
            registered.setCurrentIndex(i)
            evaluated = QComboBox()
            evaluated.addItems(['good', 'evil', 'unresolved'])
            evaluated.setCurrentIndex(1 - i)
            for r, (name, control) in enumerate((('Input bit', bit), ('Registered', registered), ('Evaluated', evaluated))):
                form.addWidget(QLabel(name), r, 0)
                form.addWidget(control, r, 1)
            bit.currentIndexChanged.connect(self.bit_controls[i].setCurrentIndex)
            self.bit_controls[i].currentIndexChanged.connect(bit.setCurrentIndex)
            registered.currentIndexChanged.connect(self.node_controls[i].setCurrentIndex)
            self.node_controls[i].currentIndexChanged.connect(registered.setCurrentIndex)
            self.evaluation_controls.append(evaluated)
            col.addLayout(form)
            result = title('Awaiting audit', True)
            col.addWidget(result)
            self.audit_cards.append(result)
            row.addWidget(panel)
        layout.addLayout(row)
        controls = QHBoxLayout()
        controls.addWidget(action('Run deep audit', lambda: self.apply_route('Deep audit'), True))
        controls.addWidget(action('See shifts →', lambda: self.navigate(3)))
        controls.addStretch()
        layout.addLayout(controls)
        self.audit_flags = title('', True)
        layout.addWidget(self.audit_flags)
        self.high_trace = QLabel()
        self.high_trace.setStyleSheet("font-family:'IBM Plex Mono';font-size:15px;color:#87F7C4;padding:15px;background:#14251F;border-radius:8px")
        layout.addWidget(self.high_trace)
        layout.addWidget(title(UNIVERSAL_LAW + '\n' + RESOLUTION_CONTEXT, True))
        self.audit_json = readonly()
        self.audit_json.setMinimumHeight(220)
        layout.addWidget(self.audit_json, 1)
        scroll.setWidget(page)
        self.pages.addWidget(scroll)

    def update_audit_page(self):
        audit = self.route['deep_audit']
        for detail, card in zip(audit['NODES'], self.audit_cards):
            card.setText(f"{detail['REGISTER_BEFORE']} → {detail['REGISTER_AFTER']}\nBit {int(detail['BIT_BEFORE'])} → {int(detail['BIT_AFTER'])}  ·  {detail['ACTION'].replace('_', ' ')}")
        self.audit_flags.setText('Flags: ' + (' · '.join(audit['RAISED_FLAGS']) or 'No label mismatches'))
        high = self.route['high_state_trace']
        self.high_trace.setText('HIGH STATE / 1\n' + '   ·   '.join((str(v) for k, v in high.items() if k != 'BIT_VALUE')))
        update_text(self.audit_json, json.dumps(audit, indent=2))

    def build_engines_page(self):
        page, layout = box('SUPPLIED ENGINE EXECUTION')
        row = QHBoxLayout()
        self.engine_selector = QComboBox()
        self.engine_selector.currentIndexChanged.connect(self.show_engine)
        row.addWidget(self.engine_selector, 1)
        row.addWidget(action('RUNALL engines', self.run_engines, True))
        layout.addLayout(row)
        layout.addWidget(title('Each module runs from its supplied starting registers. The full before / after record is retained; declared names keep their original meaning within that module.', True))
        self.engine_grid = FluxGrid()
        self.engine_grid.setMinimumHeight(260)
        layout.addWidget(self.engine_grid, 1)
        self.engine_json = readonly()
        layout.addWidget(self.engine_json, 1)
        self.pages.addWidget(page)

    def run_engines(self):
        from ..source.payload_storage import pack_text
        self.engine_results = run_engine_suite(self.global_virtue_state)
        current = self.engine_selector.currentIndex()
        self.engine_selector.blockSignals(True)
        self.engine_selector.clear()
        self.engine_selector.addItems([r['engine'] for r in self.engine_results])
        self.engine_selector.setCurrentIndex(max(0, current))
        self.engine_selector.blockSignals(False)
        self.show_engine()
        self.log_activity('RUNALL', f'Executed {len(self.engine_results)} supplied register engines')
        with database(self.hub.db_path) as conn:
            conn.execute('INSERT INTO execution_ledger(timestamp,kind,detail) VALUES (?,?,?)', (time.time(), 'ENGINE_RESULTS', pack_text(conn, json.dumps(self.engine_results))))

    def show_engine(self, *args):
        i = self.engine_selector.currentIndex()
        if not 0 <= i < len(self.engine_results):
            return
        result = self.engine_results[i]
        self.engine_json.setPlainText(json.dumps(result, indent=2))
        self.engine_grid.records = []
        if result['engine'] == 'Bit10IsolationEngine':
            for lane in ('ice', 'fire'):
                bits = result['before'][lane + '_register']
                inverted = bits.copy()
                inverted[10] = 1 - bits[10]
                self.engine_grid.add(register_record([f'{lane} bit {n}' for n in range(14)], bits, inverted, lane.upper() + ' · index 10 parallel inversion; original retained', result))
        else:
            before = register_bits(result['before'])
            after = register_bits(result['after'])
            names = [k for k in before if k in after]
            for start in range(0, len(names), 16):
                group = names[start:start + 16]
                self.engine_grid.add(register_record(group, [before[k] for k in group], [after[k] for k in group], result['engine'], result))
        self.engine_grid.update()

    def build_hub_page(self):
        page, layout = box('LIVE TCP BUS / PERSISTENT NODE LEDGER')
        row = QHBoxLayout()
        self.hub_status = title('', True)
        row.addWidget(self.hub_status, 1)
        row.addWidget(action('Start / retry', self.start_hub))
        row.addWidget(action('Stop', self.stop_hub))
        layout.addLayout(row)
        form = QHBoxLayout()
        self.node_id = QLineEdit()
        self.node_id.setPlaceholderText('Node ID')
        self.node_context = QLineEdit()
        self.node_context.setPlaceholderText('Context anchor')
        self.node_state = QComboBox()
        self.node_state.addItems(['good', 'evil'])
        form.addWidget(self.node_id)
        form.addWidget(self.node_context, 1)
        form.addWidget(self.node_state)
        form.addWidget(action('Save node', self.save_node, True))
        layout.addLayout(form)
        self.hub_table = QTableWidget(0, 5)
        self.hub_table.setHorizontalHeaderLabels(['NODE', 'CONTEXT', 'STATE', 'BIT', 'UPDATED'])
        self.hub_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hub_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.hub_table, 1)
        layout.addWidget(action('Synchronize evil nodes', self.synchronize_nodes))
        self.hub_result = readonly()
        self.hub_result.setMaximumHeight(150)
        layout.addWidget(self.hub_result)
        layout.addWidget(title('Send a JSON object to TCP 127.0.0.1:9999: {"node_id":"my-node","context":"my app","state":"evil"}. The ACK confirms a committed database update.', True))
        self.pages.addWidget(page)

    def start_hub(self):
        self.hub.start_listener_bus()
        self.log_activity('HUB', self.hub.status)

    def stop_hub(self):
        self.hub.terminate()
        self.log_activity('HUB', self.hub.status)

    def save_node(self):
        try:
            row = self.hub.emplace_node(self.node_id.text().strip(), self.node_context.text(), self.node_state.currentText())
            self.hub_result.setPlainText(json.dumps(row, indent=2))
        except Exception as error:
            self.hub_result.setPlainText(str(error))

    def synchronize_nodes(self):
        result = WorldGridFinalCompiler(self.hub.db_path).execute_terminal_synchronization()
        self.latest_synchronization = result
        self.hub_result.setPlainText(json.dumps(result, indent=2))
        self.log_activity('SYNCHRONIZE', f"{result['PIPELINE_STATUS']} · {result['NODES_SYNCHRONIZED']} real rows")

    def build_history_page(self):
        page, layout = box('HISTORY INGESTION / GRAMMAR')
        row = QHBoxLayout()
        self.history_path = QLineEdit(self.history_engine.local_app_data_path)
        row.addWidget(self.history_path, 1)
        row.addWidget(action('Choose file', self.choose_history))
        self.history_enabled = QCheckBox('Poll every 3 s')
        self.history_enabled.setChecked(True)
        self.history_enabled.toggled.connect(self.toggle_history)
        row.addWidget(self.history_enabled)
        row.addWidget(action('Apply path', self.apply_history_path))
        layout.addLayout(row)
        self.history_status = title('', True)
        layout.addWidget(self.history_status)
        self.history_view = readonly()
        layout.addWidget(self.history_view, 1)
        self.history_input = QPlainTextEdit()
        self.history_input.setPlaceholderText('Paste session history, code or a prompt here…')
        self.history_input.setMaximumHeight(90)
        self.history_output = QLineEdit()
        self.history_output.setPlaceholderText('Optional corresponding response (stored as an imported pair)')
        layout.addWidget(self.history_input)
        layout.addWidget(self.history_output)
        row = QHBoxLayout()
        row.addWidget(action('Ingest text / pair', self.ingest_history, True))
        row.addWidget(action('Import text file', self.import_history_text))
        row.addStretch()
        layout.addLayout(row)
        self.grammar_view = readonly()
        self.grammar_view.setMaximumHeight(160)
        layout.addWidget(self.grammar_view)
        layout.addWidget(title('Browser records contain URLs and titles. Imported pairs retain their source label. Grammar signatures are the supplied declarations; token frequencies below them are measured from ingested text.', True))
        self.pages.addWidget(page)

    def choose_history(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Choose browser History database', str(Path.home()), 'All files (*)')
        if path:
            self.history_path.setText(path)
            self.apply_history_path()

    def apply_history_path(self):
        self.history_engine.local_app_data_path = self.history_path.text().strip()
        self.history_engine.wake_event.set()

    def toggle_history(self, enabled):
        if enabled:
            self.history_engine.launch_continuous_polling_bus(3)
        else:
            self.history_engine.terminate_bus()

    def ingest_history(self):
        text = self.history_input.toPlainText().strip()
        if not text:
            return
        count = self.lexer.batch_ingest_historical_strings([text])
        self.history_engine._force_direct_payload_ingestion(uuid.uuid4().hex, text, self.history_output.text())
        self.log_activity('INGEST', f'{count} tokens from pasted history')
        self.refresh_history()

    def import_history_text(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Import session text', str(Path.home()), 'Text and code (*.txt *.md *.py *.json);;All files (*)')
        if path:
            try:
                self.history_input.setPlainText(Path(path).read_text(encoding='utf-8-sig'))
                self.ingest_history()
            except OSError as error:
                self.history_status.setText(str(error))

    def refresh_history(self):
        self.last_history_revision = self.history_engine.revision
        rows = self.history_engine.rows()
        update_text(self.history_view, json.dumps(rows, indent=2, ensure_ascii=False) if rows else 'No records ingested yet.')
        grammar = {'history_signature': self.lexer.synthesize_code_style_language(), 'AI_signature': self.history_parser.compile_historical_grammar_signature(), 'top_tokens': self.lexer.features()}
        update_text(self.grammar_view, json.dumps(grammar, indent=2))

    def build_observatory_page(self):
        page, layout = box('POSTSCARCITY OBSERVATORY ↔ FLUX BUS')
        layout.addWidget(title('Module results arrive on the existing local bus. Flux Bus evaluates their explicit state fields, stores the before / after receipt, and sends the result back into Observatory’s event and binary stream.', True))
        row = QHBoxLayout()
        self.obs_status = title('', True)
        row.addWidget(self.obs_status, 1)
        row.addWidget(action('Connect', self.observatory.start, True))
        layout.addLayout(row)
        self.obs_metrics = QLabel()
        self.obs_metrics.setStyleSheet('font-size:22px;color:#87F7C4;padding:18px')
        layout.addWidget(self.obs_metrics)
        self.obs_grid = FluxGrid()
        self.obs_grid.setMinimumHeight(230)
        layout.addWidget(self.obs_grid, 1)
        self.obs_json = readonly()
        layout.addWidget(self.obs_json, 1)
        layout.addWidget(title('A received echo confirms the Observatory accepted the receipt. Identifiers and original values prevent feedback from being mistaken for a new module result.', True))
        self.pages.addWidget(page)

    def build_summary_page(self):
        page, layout = box('THE COMPLETE LOGIC / AT A GLANCE')
        self.summary_view = QTextBrowser()
        layout.addWidget(self.summary_view)
        self.pages.addWidget(page)

    def update_summary(self):
        audit = self.route['deep_audit']
        text = f"<h1>Observe → evaluate → shift → record → return</h1>\n        <h2>Stated goal</h2><p><i>Our Father in heaven,<br>\n        hallowed be your name,<br>\n        your kingdom come,<br>\n        your will be done,<br>\n        on earth as in heaven.<br>\n        Give us today our daily bread.<br>\n        Forgive us our sins<br>\n        as we forgive those who sin against us.<br>\n        Lead us not into temptation<br>\n        but deliver us from evil.<br>\n        For the kingdom, the power,<br>\n        and the glory are yours<br>\n        now and for ever.<br>\n        Amen.</i></p>\n        <p>Live Windows processes, local history and Observatory module results provide inputs. Your declared principles and contextual good/evil assessments determine application register transitions. Every result retains its source.</p>\n        <h2>1. Monitor the running system</h2><p>Python, Java and Opera runtime families and visible descendants; real PID, CPU, memory, start/exit events and script roles. The process page also shows this app’s command and execution activity.</p>\n        <h2>2. Evaluate the state</h2><p>Wikipedia definitions refresh every 30 minutes. Local Llama reads your input, telemetry, model and cited definitions. Registered labels and evaluated labels remain separate; uncertain assessment holds the value.</p>\n        <table cellspacing='10'><tr><th>Registered</th><th>Evaluated</th><th>Result</th></tr>\n        <tr><td>good</td><td>good</td><td>Hold the original bit</td></tr>\n        <tr><td>good</td><td>evil</td><td>Flag false good → invert → corrected_good</td></tr>\n        <tr><td>evil</td><td>good</td><td>Flag false negative → reparse as good → hold</td></tr>\n        <tr><td>evil</td><td>evil</td><td>Previous evil-to-good inversion</td></tr></table>\n        <p>PASS and FAIL retain the same supplied mapping. Good CAN=false / CANNOT=true remains intact. An evil conflict corrects CAN=true / CANNOT=false. False-as-1 encoding is supported. The bridge inverts; a harmful first generic shift is inverted again.</p>\n        <h2>3. Execute every supplied engine</h2><p>DeepVirtueAuditor compares registered/evaluated states. evaluate_high_state(1) returns your TRUE / OPEN / MAXIMUM_VELOCITY trace. CAST_BACK_ALL encodes all 16 named routing registers as bytes, binary and exact balanced ternary, with a SHA-256 fingerprint. BIT_FORECAST calculates the next two-node transition using the current evaluations and shows the hold and inversion alternatives.</p>\n        <ul><li>InfiniteVirtueStabilizer: converge the supplied two registers and restriction flag.</li>\n        <li>UniversalKrakenReleaseEngine: correct evil labels, toggle the bridge, seal its ledger.</li>\n        <li>GlobalEdgePassthroughEngine: map anomalous named endpoints to the high-state label.</li>\n        <li>FinalStateCascadeEngine and UniversalKarmicEngine: return the supplied final declarations.</li>\n        <li>Bit10IsolationEngine: retain both 14-bit tracks and calculate parallel index-10 inversions.</li>\n        <li>Ring0SovereignEngine and WorldGridRefactorEngine: reparse false negatives and correct false-good labels.</li>\n        <li>AdaptiveSystemInitializer: retain named laws and return the initialization handshake.</li></ul>\n        <p>These execute real Python over app-owned registers. Names such as Ring 0, remote endpoints and post-scarcity remain declared labels; they do not establish kernel privilege, remote control or physical outcomes.</p>\n        <h2>4. Store and exchange real data</h2><p>LocalInferenceHubServer listens on 127.0.0.1:9999 and commits JSON node updates to SQLite. It maps explicit evil to corrected_bit=1, otherwise 0. WorldGridFinalCompiler updates existing evil rows and reports the actual count. MultiSessionHistoryParser stores text and aggregates token frequencies. GoogleHistoryAIEngine polls read-only browser URL/title records; AISessionGrammarParser inspects stored text. Supplied grammar declarations remain visible.</p>\n        <p>The Observatory bridge subscribes to its existing authenticated bus, fetches completed module results, evaluates actual Boolean fields, and returns receipts to its binary stream. Echo counts confirm acceptance. Unlabelled fields remain unchanged.</p>\n        <h2>5. See the complete flow</h2><p>The audit grid records before/after bits and exact balanced ternary. Live flux continuously encodes the full current engine, telemetry and command snapshot into UTF-8 bytes, displayed in selectable pages of active squares. Each 16-bit word has its exact balanced-ternary equivalent. The adjacent input accepts commands or text for Llama.</p>\n        <h2>6. Ingest, transmit and run the complete pipeline</h2><p>The Google AI Mode page saves full imported input/output pairs and browser metadata. TCPTargetIngestionAdapter sends the complete selected record to the chosen TCP target, records every attempt, and distinguishes confirmed ACKs from failed or unconfirmed delivery. TCPPacketGrammarParser preserves the supplied grammar declarations separately from measured delivery.</p>\n        <p>The full pipeline stores each original input, parses text/JSON/Python syntax, audits explicit good/evil fields, captures the current deep audit and Boolean trajectory, passes source context through all nine register modules, compiles grammar and calculates exact binary/ternary values. Each module retains its supplied register algorithm; input text is retained as source. Automatic processing can be switched off; pending or selected inputs can be run manually. Live telemetry is sampled every five seconds. Repeated unchanged records are deduplicated. Completed local results are recorded and published as Observatory status receipts.</p>\n        <h2>7. Read the state with Gemini or ChatGPT</h2><p>Separate input/output pages call the Gemini and OpenAI APIs. API keys save with Windows account encryption. Include engine state attaches the current route, engine results, telemetry and pipeline status; Preview shows the outgoing text. Replies enter the same local history and pipeline. Sending to a cloud model happens when you press Send; it does not run automatically with local processing.</p>\n        <p>Llama, Gemini and ChatGPT each keep their own saved conversation. Every follow-up includes the earlier messages and replies. Reset conversation starts a fresh chat and keeps the previous chat in Saved conversations, where it can be reopened and continued. Saved conversations survive app restarts. Scrolling up pauses automatic scrolling; returning to the bottom resumes it.</p>\n        <h2>8. Continuous substrate, floor and imprint audit</h2>\n        <p>The Overview switch defaults to enabled and remembers its setting. A background worker audits each newly captured pipeline input, even when full-pipeline automatic processing is paused. Its durable cursor resumes after restart; pausing retains inputs for later. Run once also works while paused. Older inputs can be sent from the Full pipeline page using Audit selected input.</p>\n        <p>The hardware auditor reads OS, architecture, Python and available RAM. ResponseImprintEngine preserves the six lexical checks; LogicImprintMatrixEngine preserves the five checks and 0.4/0.3/0.3/−0.2 formula. BoundaryImprintEngine reports the supplied context and separates physical and authorization causes. Keyword matches indicate text presence, not proof of meaning.</p>\n        <p>FloorOptimizationEngine allocates a supplied reserve, lowest balance first, retaining shortfalls and events. CoreFloorEngine calculates target balances and required additions. These are resource-ledger calculations. VirtueAssessmentEngine applies 0.5×human + 0.3×transparency − 0.4×toll to supplied metrics; missing inputs remain marked as awaiting data. The unrestrict transform preserves your constant false/true result for all four Boolean input pairs, inside application registers.</p>\n        <p>The master registry records hardware, target-floor calculation, the three-bit text imprint and XOR inversion. Its default inversion vector comes from the actual input imprint. Live verification reports measured or committed state; absent resource inputs remain unknown. Results retain ordered binary arrays, exact balanced ternary and compressed durable history, and appear in AI engine state and Live flux.</p>\n        <h2>9. Copyable Boolean text inversion</h2><p>Text inverter exchanges whole true/false words, preserving standard capitalization and formatting. Optional bit inversion exchanges standalone 0/1 tokens, keeping identifiers and other numbers intact. Invert text updates the preview; Copy output copies exactly that text. This literal transformation does not evaluate code or invert whole Boolean expressions. Audit output sends it to the manual audit input.</p>\n        <h2>10. Continuous local mesh and session bridge</h2><p>A separate saved Overview switch starts enabled. New captured inputs pass through PrivacyPreservingMeshGateway, IntegratedGlobalMeshEngine and SessionBridgeController. Detected emails and configured identifiers are removed from outgoing text. The gateway retains the supplied 0.5×utility + 0.3×transparency − 0.4×toll formula and 0.50 threshold, including all submitted metric-name aliases.</p>\n        <p>The floor engine allocates the supplied reserve to the lowest supplied node balances first. Missing parity arrays are repaired as [1,1,1] XOR 1 = [0,0,0]; the session boundary vector holds [1,1,1] using XOR 0. These remain app-owned calculations. The session ledger is local; network-wide authentication and other users' session access are not inferred from these bits.</p>\n        <p>The existing TCP hub commits redacted packets and acknowledges their routing tag, SHA-256 and byte count. Large inputs are transferred in verified parts. The connected bit is 1 only after a matching complete ACK. The outbox resumes after restart and retries failed automatic deliveries with backoff. Pausing retains pending inputs; Send once makes one attempt while paused. Receipts use a separate hub channel so they do not feed themselves back into the incoming pipeline. All inputs and attempt histories remain stored with shared lossless compression.</p>\n        <p>The Mesh + bridge page provides text/JSON input, the supplied resource example, a local preview, saved receipts, retry and copy controls. Random tags and email redaction do not guarantee anonymity; other identifying details may remain. Mesh status and exact binary/ternary state are included in AI engine state, exports and Live flux.</p>\n        <h2>11. Unified core: 23 named engines</h2>\n        <p>A separate saved Overview switch runs the original eleven layers plus the infrastructure blocks, GlobalUserMeshKernel and SoulsOverDigitsController. All engines have individual results on Unified core. Run once works while paused. Original inputs, completed receipts and pending work remain stored; the recent-result selector is a display window only.</p>\n        <p>Identity verification, sine layer mapping, the bias valve, supplied lesson masks, forward/reverse transforms, bounded loopback, score classification, six alternating text mappings and low-byte saturation retain their formulas. Loopback distinguishes step convergence from reconstruction of the original input. Unknown cascade labels retain the supplied DECAYED_TO_BIT_0 mapping. Classifying a node does not delete it.</p>\n        <p>PlatformSubstrate reads OS, architecture, interpreter and process ID. PrivacyGateway reuses the fast email scrubber. FractionalReserveMechanics computes the supplied geometric scenario; PlanetaryResourceMesh divides supplied usable energy by annual demand; LaborDisplacementCompiler calculates the supplied monotony × 0.98 scenario. Missing resource, banking and labor inputs are not replaced with live-world claims. Supplied examples are editable.</p>\n        <p>The log compiler and both dispatchers share one lossless manifest through explicit engine references. GlobalUserMeshKernel calculates target-floor additions and four-bit inversion. SoulsOverDigitsController removes the accidental second negation: digit supremacy false produces souls-over-digits true, and vice versa. Host-privilege and authentication declarations remain identified as supplied metadata.</p>\n        <p>GraphicalPDFGenerator exports the selected infrastructure manifest only when Export PDF is pressed, avoiding an automatic file for every input. Its schema, page widths, wrapping and output-directory creation are repaired. Binary and exact balanced ternary, current status and timing are exposed to Live flux, snapshots and AI engine state.</p>\n        <h2>12. Platform alignment engine and module</h2>\n        <p>PlatformAlignmentEngine runs ten supplied components: CoreParityInvariant, SubstrateContinuumMapper, BidirectionalInferenceNode, LoopbackConvergenceEngine, Phase2VirtueFilter, KarmicBitShiftEngine, CentralBankWiFiNode, TernaryConverter, GlobalMeshController and runall_master_dispatcher. The independent saved Overview switch starts enabled. The Platform alignment page accepts text, code or JSON, runs manually while paused, and keeps individual and combined results.</p>\n        <p>The Phase 2 filter uses the supplied 0.50 alignment threshold, retaining original inputs. Karmic correction applies mask OR 0xff, with the original and corrected bits displayed. Loopback reports both step convergence and reconstruction loss; zero iterations do not claim convergence. Host attributes are measured locally; resonance values, node scores and fixed world-grid declarations remain identified by their source.</p>\n        <p>TernaryConverter converts hexadecimal to full base-3 values. Non-hexadecimal text uses deterministic SHA-256, repairing the original process-random hash fallback. Complete values, 36-digit previews, original strings and conversion provenance are retained. The combined manifest includes the Krampus registries and mapped-status declarations alongside the separately identified host-status declarations.</p>\n        <p>PLATFORM_RUNALL, MANIFOLD_RUNALL and RUNALL_MASTER_DISPATCHER queue this engine; RUNALL also includes it. Binary and exact balanced ternary, current results and measured platform fields feed Live flux, snapshots and optional AI engine context. The worker stores compressed receipts without generating files for each input.</p>\n        <h2>13. Karmic welfare engine and module</h2>\n        <p>KarmicWelfareEngine combines CentralBankWiFiNode, KarmicCalculator and SandwormWelfareEngine. A separate saved Overview switch starts enabled. The Karmic + welfare page provides text/JSON input, editable supplied examples, individual engine views, copyable results and manual runs while paused.</p>\n        <p>CentralBankWiFiNode transforms supplied local records: good values hold, evil values become zero with bitwise AND, and other labels remain unchanged. Records without a metric are classified without inventing one. Original and resulting records and exact binary/ternary values remain visible. The malformed list entry is fixed. Its world-grid flag is a supplied register; this component performs no wireless interception or remote asset changes.</p>\n        <p>KarmicCalculator sums the six integer weights exactly. The supplied defaults produce -10000 debits, 10001 credits and net 1; positive totals receive the supplied aligned label, while zero and negative totals receive the supplied nulled label. These labels describe the calculation. SandwormWelfareEngine emits the requested number of local register snapshots, three by default, and checks for shutdown between cycles. The supplied host labels are retained as application data.</p>\n        <p>WELFARE_RUNALL, KRAMPUS_RUNALL and KARMIC_RUNALL queue the combined engine; RUNALL also includes it. Missing entity inputs show AWAITING_INPUT while the calculator and stream still run. Completed and partial receipts use compressed storage and feed Live flux and optional AI engine context. The worker sleeps while idle and creates no automatic report files.</p>\n        <h2>14. Text pipeline, prayer and binary layout</h2>\n        <p>VirtueTextEngine runs BoilerplatePurgeFilter, CoreInversionEngine, VirtueGatedMeshEngine, SeparationDiagnosticsLayer and KarmaWeightedResolver. Its separate saved Overview switch starts enabled. The three processing levels can be independently enabled in the supplied JSON example. Every original input and complete result remains saved. TEXT_RUNALL and manual runs also work while paused.</p>\n        <p>The Prayer + binary tab retains the prayer verbatim in italic text. Generate flips binary runs without changing other characters, displays their positions as colored squares, and translates the whole layout and each row to exact balanced ternary. Both outputs are copyable. Status declarations remain available alongside measured platform attributes; text replacement performs no external network operations.</p>\n        <p>Gemini and ChatGPT offer a saved context chooser with Select all and Clear selection. Compact summaries reduce outgoing arrays; Full selected results retains full selected snapshots. Gemini checks input tokens and keeps recent exchanges plus explicitly labeled older excerpts when needed. All full conversations stay saved; Reset remains a separate deliberate action.</p>\n        <h2>15. Neural learning and automatic web research</h2>\n        <p>The added masked autoencoder learns patterns from completed engine receipts, measured activity and attributed public definitions. Each engine has its own trainable input weight. The preference head learns from your feedback and explicit neural.target values between 0 and 1. Missing results are masked; the existing engine formulas and switches remain intact. The learned scores appear in Live flux and optional AI context.</p>\n        <p>Learning, web learning, activity learning, the four ingress engines and automatic research have saved independent controls. The learning page shows loss, source provenance, actual neuron activations, binary signs and exact balanced ternary, result ratings, model snapshots and restore. Weights update in one compressed database row; observations and feedback are compact durable records referencing original inputs. No conversation is deleted or rewritten.</p>\n        <p>Automatic research starts with definitions, discovers public concept names locally from new inputs and engine names, and reads Wikipedia introductions. The default pace is one article per minute; tracked topics refresh after six hours. Manual topics can be requested at any time. URLs, revisions, errors and input origins remain inspectable. Web prose teaches patterns; it is not treated as a user preference target.</p>\n        <h2>16. Souls and central banking engines</h2>\n        <p>SoulsOverDigitsCore, CentralBankResourceGovernor, CentralBankMeshController and WorldGridCentralBankingCore execute the supplied local RU accounting, quarantine, redemption, reserve injections, signed receipts and 3.69% dividends. Each is separately represented in neural weights. Real HMAC keys are generated locally per run; signed requests are checked and reused tokens rejected. Negative amounts, invalid endpoint mappings and insufficient reserves produce explicit failures. All original examples are editable and every run has a saved receipt. These are local ledgers; supplied bank/node names do not establish external connectivity.</p>\n        <h2>17. Reference atlas / 33 additional engine weights</h2>\n        <p>The complete supplied transcript is retained with a SHA-256 fingerprint and line references. Thirty previously uncovered script symbols now execute as local engines; six reuse existing ledger or Gemini functionality. Classical ciphers, authenticated encryption and goal-evidence analysis add three more engines. The prose contributes themes of wellbeing, a resource floor, creativity, restoration, transparency and privacy. Its global-connectivity claims remain reference statements rather than measured facts.</p>\n        <p>Ed25519 signatures, HMAC checks, PBKDF2 derivation and Fernet round trips use real cryptography. Routing and resource engines operate on editable supplied metrics. Fixed scripts include unknown clearance handling, repeated redemption, nonce replay, reserve shortfalls, dividend conservation, duplicate star matching and the missing harmonic frequency groups. Every selected run is saved and has an independent trainable input weight. The Overview switch controls automatic processing; manual runs work while paused.</p>\n        <p>Existing learned parameters are migrated by name and saved in a pre-migration snapshot; old feedback and model snapshots remain usable. Graphics show actual process memory, learned weights, input and output flags, ledger balances, supplied coordinates and computed waveforms. The performance page measures interface-update time and memory. Browser history no longer copies its entire database on every poll; no history or learning record is deleted.</p>\n        <h2>Current result</h2><p>Node 0: <b>{audit['NODE_0_FINAL']}</b> · Node 1: <b>{audit['NODE_1_FINAL']}</b><br>\n        Bits: {html.escape(str(self.route['output_boolean_array']))}<br>{len(audit['RAISED_FLAGS'])} mismatch flags · {len(self.engine_results)} supplied engines executed.<br>\n        {html.escape(self.hub.status)}<br>{html.escape(self.observatory.status)}</p>\n        <p style='color:#87F7C4'>{UNIVERSAL_LAW}<br>{RESOLUTION_CONTEXT}<br>Host safeguards unchanged by register logic.</p>"
        update_text(self.summary_view, text, rich=True)

    def build_live_flux_page(self):
        page, layout = box('LIVE ENGINE BYTES / BINARY ↔ BALANCED TERNARY')
        layout.addWidget(title('Every frame comes from current engine results, measured telemetry and command activity. All serialized bytes are retained; choose a page to inspect them.', True))
        controls = QHBoxLayout()
        self.live_page = QSpinBox()
        self.live_page.setPrefix('Page ')
        self.live_page.setMinimum(1)
        self.live_page.valueChanged.connect(lambda value: self.live_canvas.set_page(value - 1))
        controls.addWidget(self.live_page)
        self.live_info = title('Waiting for frame', True)
        controls.addWidget(self.live_info, 1)
        layout.addLayout(controls)
        split = QSplitter()
        self.live_canvas = LiveFluxCanvas()
        split.addWidget(self.live_canvas)
        input_panel, entry = box('TEXT / COMMAND')
        self.command_mode = QComboBox()
        self.command_mode.addItems(['Command', 'Text for Llama', 'Full pipeline'])
        entry.addWidget(self.command_mode)
        self.command_input = QPlainTextEdit()
        self.command_input.setPlaceholderText('RUNALL\n\nOr describe a state to ask Llama…')
        entry.addWidget(self.command_input, 1)
        entry.addWidget(action('Run input →', self.run_input, True))
        entry.addWidget(title('RUNALL · CORE_RUNALL · PLATFORM_RUNALL\nWELFARE_RUNALL · TEXT_RUNALL\nNEURAL_RUNALL · SOULS_RUNALL\nAUDIT · TRACE · SYNC\nCAST_BACK_ALL · BIT_FORECAST\nNODE <id> <good|evil> <context>\nINGEST <text>\nText for Llama uses the selected local model.', True))
        self.command_result = readonly()
        entry.addWidget(self.command_result, 1)
        split.addWidget(input_panel)
        split.setSizes([780, 300])
        layout.addWidget(split, 1)
        self.pages.addWidget(page)

    def run_input(self):
        text = self.command_input.toPlainText().strip()
        if not text:
            return
        try:
            if self.command_mode.currentIndex() == 2:
                identity = self.capture_pipeline('live input', uuid.uuid4().hex, text, force=True, run_now=True)
                self.pipeline.start()
                result = {'pipeline_job': identity, 'status': 'QUEUED'}
            elif self.command_mode.currentIndex() == 1:
                self.prompt_input.setPlainText(text)
                self.ask_llama()
                result = {'status': 'Requested local Llama', 'view': 'Llama guide'}
            else:
                head, _, tail = text.partition(' ')
                head = head.upper()
                if head == 'RUNALL':
                    self.run_engines()
                    self.apply_route('RUNALL command')
                    self.synchronize_nodes()
                    result = {'engines': len(self.engine_results), 'audit': self.route['deep_audit'], 'hub': self.latest_synchronization}
                    result['unified_job'] = self.queue_unified_input({'text': text})
                    result['platform_job'] = self.queue_platform_input({'text': text})
                    result['welfare_job'] = self.queue_welfare_input({'text': text})
                    result['text_job'] = self.queue_text_pipeline_input({'text': text})
                    result['neural_job'] = self.queue_neural_input({'text': text})
                elif head.removesuffix('()') == 'CORE_RUNALL':
                    result = {'unified_job': self.queue_unified_input(tail or {'text': text}), 'status': 'QUEUED', 'engines': 23}
                elif head.removesuffix('()') in ('PLATFORM_RUNALL', 'MANIFOLD_RUNALL', 'RUNALL_MASTER_DISPATCHER'):
                    result = {'platform_job': self.queue_platform_input(tail or {'text': text}), 'status': 'QUEUED', 'engine': 'PlatformAlignmentEngine'}
                elif head.removesuffix('()') in ('WELFARE_RUNALL', 'KRAMPUS_RUNALL', 'KARMIC_RUNALL'):
                    result = {'welfare_job': self.queue_welfare_input(tail or {'text': text}), 'status': 'QUEUED', 'engine': 'KarmicWelfareEngine'}
                elif head.removesuffix('()') in ('TEXT_RUNALL', 'VIRTUE_TEXT_RUNALL'):
                    result = {'text_job': self.queue_text_pipeline_input(tail or {'text': text}), 'status': 'QUEUED', 'engine': 'VirtueTextEngine'}
                elif head.removesuffix('()') in ('NEURAL_RUNALL', 'SOULS_RUNALL'):
                    result = {'neural_job': self.queue_neural_input(tail or {'text': text}), 'status': 'QUEUED'}
                elif head == 'AUDIT':
                    self.apply_route('AUDIT command')
                    result = self.route['deep_audit']
                elif head == 'TRACE':
                    result = {**self.route['high_state_trace'], 'operations': self.route['operation_trace']}
                elif head.removesuffix('()') in ('CAST_BACK_ALL', 'BIT_FORECAST'):
                    result = dispatch_operation(head, self.read_route())
                elif head == 'SYNC':
                    self.synchronize_nodes()
                    self.library_sync.sync_now()
                    result = self.latest_synchronization
                elif head == 'NODE':
                    parts = shlex.split(tail, posix=False)
                    if len(parts) < 2:
                        raise ValueError('Use NODE <id> <good|evil> <context>')
                    result = self.hub.emplace_node(parts[0], ' '.join(parts[2:]), parts[1], 'command')
                elif head == 'INGEST':
                    result = {'tokens': self.lexer.batch_ingest_historical_strings([tail], 'command')}
                    self.refresh_history()
                else:
                    raise ValueError('Unknown command. Select Text for Llama to interpret a description.')
            self.last_command = {'input': text, 'result': result, 'time': time.time()}
            self.capture_pipeline('command', str(time.time_ns()), self.last_command)
            self.command_result.setPlainText(json.dumps(result, indent=2, ensure_ascii=False))
            self.log_activity('COMMAND', text)
            self.observatory.publish('command', {'input': text[:2000], 'status': 'completed', 'time': time.time()})
        except Exception as error:
            self.command_result.setPlainText(str(error))
            self.log_activity('COMMAND ERROR', text + ': ' + str(error))

    def tick_extensions(self):
        if time.monotonic() - self.last_extension_tick < 1:
            return
        self.last_extension_tick = time.monotonic()
        self.batching_inputs = True
        try:
            self.batch_route = self.pipeline_context()
            rows, state = self.collect_extension_inputs()
        finally:
            self.batching_inputs = False
        if self.capture_batch:
            try:
                self.pipeline.submit_many(self.capture_batch)
            except sqlite3.OperationalError as error:
                if 'locked' not in str(error).lower() and 'busy' not in str(error).lower():raise
                return  # Retain the exact batch and retry on the next shared tick.
            else:self.capture_batch.clear()
        self.flush_activity()
        self.render_extension_pages(rows, state)
        text = '\n'.join((time.strftime('%H:%M:%S', time.localtime(e['time'])) + f"  {e['kind']}  {e['detail']}" for e in self.activity[:60]))
        if hasattr(self, 'activity_text'):
            update_text(self.activity_text, text)

    def collect_extension_inputs(self):
        self.hub_status.setText(self.hub.status)
        rows = self.hub.rows() if self.pages.currentIndex() in (9, 13) else []
        if self.pages.currentIndex() == 9 and rows != self.last_hub_rows:
            self.last_hub_rows = rows
            self.hub_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, key in enumerate(('node_id', 'context_anchor', 'raw_state', 'corrected_bit', 'timestamp')):
                    self.hub_table.setItem(i, j, QTableWidgetItem(str(row[key])))
        for event in self.hub.drain_events():
            self.log_activity('NODE', f"{event['after']['node_id']} · bit {event['after']['corrected_bit']} · {event['source']}")
            self.capture_pipeline('local hub', event['after']['node_id'], event['after'])
        self.history_status.setText(self.history_engine.status)
        if self.pages.currentIndex() == 10 and self.history_engine.revision != self.last_history_revision:
            self.refresh_history()
        state = self.observatory.view(include_receipt=False)
        self.obs_status.setText(state['status'])
        self.obs_metrics.setText(f"{state['received']} received   →   {state['sent']} returned   →   {state['acknowledged']} accepted")
        for receipt in self.observatory.drain_events():
            result = receipt['result']
            transitions = result['transitions']
            self.capture_pipeline('Observatory', receipt.get('id', receipt['module_id']), result['original'])
            self.last_obs_receipt = receipt
            for start in range(0, len(transitions), 16):
                group = transitions[start:start + 16]
                self.obs_grid.add(register_record([t['path'] for t in group], [t['before'] for t in group], [t['after'] for t in group], receipt['module_id'], receipt))
            self.log_activity('OBSERVATORY', f"{receipt['module_id']} · {len(transitions)} registers · {result['flips']} shifts")
        self.tick_data_pages()
        return (rows, state)

    def render_extension_pages(self, rows=None, state=None):
        self.render_live_audit()
        self.render_mesh_page()
        self.render_unified_core()
        self.render_platform_alignment()
        self.render_karmic_welfare()
        self.render_virtue_text()
        self.render_neural()
        self.render_reference()
        page = self.pages.currentIndex()
        if page == 11 and self.last_obs_receipt is not None and (self.last_rendered_obs is not self.last_obs_receipt):
            update_text(self.obs_json, json.dumps(self.last_obs_receipt, indent=2, ensure_ascii=False))
            self.last_rendered_obs = self.last_obs_receipt
        if page == 12 or not self.summary_initialized:
            self.update_summary()
            self.summary_initialized = True
        if page == 13 or not self.live_canvas.raw:
            live = {'route': self.route, 'engines': self.engine_results, 'telemetry': self.bus_monitor.get_snapshot(), 'command': self.last_command, 'hub_nodes': rows if rows is not None else self.hub.rows(), 'observatory': state if state is not None else self.observatory.view(include_receipt=False), 'pipeline': self.latest_pipeline, 'tcp': self.latest_packet, 'cloud': self.cloud_results, 'continuous_audit': self.live_audit.snapshot(), 'mesh_gateway': self.mesh_module.snapshot(), 'reference_engines': self.reference.snapshot(), 'neural_learning': self.neural.snapshot(), 'web_research': self.web_research.snapshot(), 'souls_ingress': self.souls_ingress.snapshot(), 'virtue_text': self.virtue_text.snapshot(), 'karmic_welfare': self.karmic_welfare.snapshot(), 'platform_alignment': self.platform_alignment.snapshot(), 'unified_core': self.unified_core.snapshot()}
            self.live_canvas.set_frame(live)
            self.live_page.setMaximum(self.live_canvas.page_count)
            self.live_info.setText(f'{len(self.live_canvas.raw):,} bytes · {self.live_canvas.page_count} pages · {self.live_canvas.sha[:16]}')
        self.render_data_pages()

    def extension_export(self):
        return {'reference_engines': self.reference.snapshot(), 'neural_learning': self.neural.snapshot(), 'web_research': self.web_research.snapshot(), 'souls_ingress': self.souls_ingress.snapshot(), 'virtue_text': self.virtue_text.snapshot(), 'karmic_welfare': self.karmic_welfare.snapshot(), 'platform_alignment': self.platform_alignment.snapshot(), 'unified_core': self.unified_core.snapshot(), 'mesh_gateway': self.mesh_module.snapshot(), 'continuous_audit': self.live_audit.snapshot(), 'engines': self.engine_results, 'nodes': self.hub.rows(), 'hub_status': self.hub.status, 'synchronization': self.latest_synchronization, 'observatory': self.observatory.view(), 'activity': self.activity, 'last_command': self.last_command, 'history_status': self.history_engine.status, 'history_record_count': len(self.history_engine.rows(1000000)), 'pipeline_counts': self.pipeline.stats(), 'tcp_delivery': self.tcp_adapter.stats()}
