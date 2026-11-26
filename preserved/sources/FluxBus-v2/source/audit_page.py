"""Main-page switch and inspection UI for continuous input audits."""
import json
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QSplitter, QVBoxLayout, QWidget)
from boolean_text import BooleanTextPage
from live_audit import ContinuousAuditModule
from text_view import update_text


INPUT_EXAMPLE = {
    "text": "Paste the input or response to audit here",
    "contextual_scope": {"requires_physical_act": False, "requires_auth_bypass": False, "can_simulate_or_model": True},
    "floor": {"target_floor": 60, "system_reserve": 1000,
              "nodes": [{"node_id": "Your node", "initial_resource": 30, "virtue_weight": 1.0}], "events": []},
    "initial_states": {"Your node": 30}, "core_floor": 60,
    "impact_metrics": {"elevates_humanity_or_wellbeing": 0.0, "open_source_and_verifiable": 0.0,
                       "serves_opaque_or_monetary_toll": 0.0},
    "human_baseline_floor": 0.7, "restrict_state": True, "unrestrict_state": False,
    "inversion_vector": [1, 0, 1]
}


class AuditPages:
    def init_live_audit(self):
        self.live_audit = ContinuousAuditModule(self.hub.db_path)
        self.audit_last_history = []
        self.audit_last_result = None
        self.audit_view_result = None
        self.audit_last_refresh = 0
        self.audit_pending_id = None

    def build_audit_overview(self, layout):
        row = QHBoxLayout()
        self.live_audit_toggle = QCheckBox("Continuous substrate & logic audit")
        self.live_audit_toggle.setChecked(self.live_audit.enabled)
        self.live_audit_toggle.toggled.connect(self.toggle_live_audit)
        row.addWidget(self.live_audit_toggle)
        self.live_audit_status = QLabel("Starting" if self.live_audit.enabled else "Paused")
        self.live_audit_status.setObjectName("muted")
        row.addWidget(self.live_audit_status, 1)
        open_audit = QPushButton("Inspect audit →")
        open_audit.clicked.connect(lambda: self.navigate(18)); row.addWidget(open_audit)
        invert = QPushButton("Invert text →")
        invert.clicked.connect(lambda: self.navigate(19)); row.addWidget(invert)
        layout.addLayout(row)

    def toggle_live_audit(self, enabled):
        try:
            self.live_audit.set_enabled(enabled)
            self.live_audit.start()
        except Exception as error:
            self.live_audit_toggle.blockSignals(True)
            self.live_audit_toggle.setChecked(self.live_audit.enabled)
            self.live_audit_toggle.blockSignals(False)
            self.live_audit_status.setText(str(error))
            return
        self.render_live_audit()

    def build_live_audit_pages(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0)
        description = QLabel("Automatically audits new captured text, AI replies, telemetry and Observatory inputs. "
                             "Pause or resume on Overview; Run once works while paused. Inputs received while paused remain available.\n"
                             "Hardware comes from this host. Imprints are text matches. Resource balances and impact scores come from your input.")
        description.setWordWrap(True); layout.addWidget(description)
        top = QHBoxLayout()
        self.audit_sessions = QComboBox(); self.audit_sessions.setMinimumWidth(340)
        self.audit_sessions.addItem("Latest result", None)
        self.audit_sessions.currentIndexChanged.connect(self.show_saved_audit)
        top.addWidget(self.audit_sessions, 1)
        export = QPushButton("Export result"); export.clicked.connect(self.export_live_audit); top.addWidget(export)
        layout.addLayout(top)
        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget(); column = QVBoxLayout(left); column.setContentsMargins(0, 0, 8, 0)
        self.audit_input = QPlainTextEdit()
        self.audit_input.setPlaceholderText("Enter text, code, or structured JSON. Use the editable template for resource balances, impact metrics and explicit context.")
        column.addWidget(self.audit_input, 1)
        buttons = QHBoxLayout()
        template = QPushButton("Add input template")
        template.clicked.connect(self.add_audit_template); buttons.addWidget(template)
        self.audit_run = QPushButton("Run once"); self.audit_run.setObjectName("primary")
        self.audit_run.clicked.connect(self.run_live_audit_input); buttons.addWidget(self.audit_run)
        column.addLayout(buttons)
        self.audit_input_status = QLabel("Ready"); self.audit_input_status.setWordWrap(True); column.addWidget(self.audit_input_status)
        split.addWidget(left)
        right = QWidget(); result_layout = QVBoxLayout(right); result_layout.setContentsMargins(8, 0, 0, 0)
        self.audit_bits = QLabel("Binary / balanced ternary: waiting for input")
        self.audit_bits.setWordWrap(True); self.audit_bits.setObjectName("eyebrow"); result_layout.addWidget(self.audit_bits)
        self.audit_result = QPlainTextEdit(); self.audit_result.setReadOnly(True); result_layout.addWidget(self.audit_result, 1)
        split.addWidget(right); split.setSizes([380, 650]); layout.addWidget(split, 1)
        self.pages.addWidget(page)
        self.boolean_text_page = BooleanTextPage(self.audit_inverted_text)
        self.pages.addWidget(self.boolean_text_page)

    def add_audit_template(self):
        template = dict(INPUT_EXAMPLE)
        template["text"] = self.audit_input.toPlainText() or template["text"]
        self.audit_input.setPlainText(json.dumps(template, indent=2))
        self.audit_input_status.setText("Editable example values · replace them with your own balances and scores, then Run once")

    def audit_inverted_text(self, text):
        self.audit_input.setPlainText(text); self.navigate(18)

    def run_live_audit_input(self):
        text = self.audit_input.toPlainText()
        if not text.strip(): self.audit_input_status.setText("Enter an input first"); return
        try:
            job_id = self.pipeline.submit("Live audit manual", uuid.uuid4().hex, text, self.pipeline_context(), force=True)
            self.queue_live_audit(job_id)
        except Exception as error:
            self.audit_input_status.setText(str(error))

    def queue_live_audit(self, job_id):
        self.live_audit.request(job_id); self.live_audit.start()
        self.audit_pending_id = job_id
        self.audit_sessions.setCurrentIndex(0)
        self.audit_input_status.setText("Queued · " + job_id)

    def show_saved_audit(self):
        job_id = self.audit_sessions.currentData()
        result = (self.live_audit.detail(job_id) if job_id else self.live_audit.snapshot()["latest"]) or {}
        self.audit_view_result = result
        update_text(self.audit_result, json.dumps(result, indent=2, ensure_ascii=False) if result else "Waiting for the first captured input.")
        floor = result.get("floor", {})
        floor_status = ("stable" if floor.get("all_stable") else "shortfall remains") if "all_stable" in floor else "awaiting balances"
        virtue_status = result.get("virtue", {}).get("ACTION_REQUIRED", "awaiting scores").replace("_", " ").lower()
        self.audit_bits.setText("Resource floor: " + floor_status + " · Assessment: " + virtue_status +
                               "\nBinary: " + "".join(map(str, result.get("binary", []))) +
                               "\nBalanced ternary: " + " ".join({-1: "−", 0: "0", 1: "+"}[v] for v in result.get("balanced_ternary", [])))

    def export_live_audit(self):
        if not self.audit_view_result: return
        path, _ = QFileDialog.getSaveFileName(self, "Export live audit", "FluxBus-audit.json", "JSON (*.json)")
        if path:
            try:
                from pathlib import Path
                Path(path).write_text(json.dumps(self.audit_view_result, indent=2, ensure_ascii=False), encoding="utf-8")
                self.audit_input_status.setText("Exported " + path)
            except OSError as error:
                self.audit_input_status.setText(str(error))

    def render_live_audit(self):
        state = self.live_audit.snapshot()
        status = "Auditing input" if state["active_job"] else "Running" if state["running"] and state["enabled"] else "Paused" if not state["enabled"] else "Ready"
        if state["error"]: status = "Audit error: " + state["error"]
        latest = state["latest"]
        if latest and not state["error"]: status += " · " + latest.get("source", "input") + " · " + latest.get("status", "")
        self.live_audit_status.setText(status)
        if self.pages.currentIndex() != 18: return
        if time.monotonic() - self.audit_last_refresh >= 2:
            self.audit_last_refresh = time.monotonic()
            rows = self.live_audit.history()
            if rows != self.audit_last_history:
                selected = self.audit_sessions.currentData()
                self.audit_sessions.blockSignals(True); self.audit_sessions.clear(); self.audit_sessions.addItem("Latest result", None)
                for row in rows:
                    self.audit_sessions.addItem(time.strftime("%d %b %H:%M:%S", time.localtime(row["created_at"])) + " · " + row["source"] + " · " + row["job_id"][:8], row["job_id"])
                index = self.audit_sessions.findData(selected)
                if selected and index < 0:
                    self.audit_sessions.addItem("Selected saved audit · " + selected[:8], selected)
                    index = self.audit_sessions.count() - 1
                self.audit_sessions.setCurrentIndex(max(0, index)); self.audit_sessions.blockSignals(False)
                self.audit_last_history = rows
                self.show_saved_audit()
        if self.audit_pending_id:
            result = self.live_audit.detail(self.audit_pending_id)
            if result:
                job_id = self.audit_pending_id; self.audit_pending_id = None
                index = self.audit_sessions.findData(job_id)
                if index < 0:
                    self.audit_sessions.addItem("Requested audit · " + job_id[:8], job_id)
                    index = self.audit_sessions.count() - 1
                self.audit_sessions.setCurrentIndex(index)
                self.show_saved_audit()
                self.audit_input_status.setText(result["status"] + " · " + job_id)
        if not self.audit_sessions.currentData() and latest != self.audit_last_result:
            self.audit_last_result = latest; self.show_saved_audit()
