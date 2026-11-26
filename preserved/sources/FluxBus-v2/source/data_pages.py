"""Google AI ingestion, full-pipeline controls, and Gemini/OpenAI state readers."""
import hashlib
import json
from pathlib import Path
import queue
import threading
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QLabel,QVBoxLayout,QHBoxLayout,QLineEdit,QPlainTextEdit,QPushButton,
    QComboBox,QCheckBox,QSplitter,QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QTabWidget,
    QDialog,QDialogButtonBox,QScrollArea,QWidget,QSpinBox)
from visuals import Panel
from pipeline import DataPipeline, encoded
from tcp_ingestion import TCPTargetIngestionAdapter,TCPPacketGrammarParser,parse_target
from cloud_ai import KeyVault,generate,list_models,compose_input,redact
from routing import register_record
from conversations import ConversationStore,transcript,preview
from text_view import update_text
from ai_context import context_choices,select_context,fit_context,estimated_tokens


def panel(name):
    widget=Panel(); layout=QVBoxLayout(widget); layout.setContentsMargins(18,16,18,16);layout.setSpacing(10)
    label=QLabel(name); label.setObjectName("eyebrow");layout.addWidget(label)
    return widget,layout


def note(text):
    label=QLabel(text);label.setWordWrap(True);label.setObjectName("muted");return label


def button(text,callback,primary=False):
    item=QPushButton(text);item.clicked.connect(callback)
    if primary:item.setObjectName("primary")
    return item


def table(headers):
    item=QTableWidget(0,len(headers));item.setHorizontalHeaderLabels(headers)
    item.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    item.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    item.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    item.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return item


def fill_table(widget,rows,keys):
    scroll=widget.verticalScrollBar().value()
    previous=widget.item(widget.currentRow(),0)
    identity=previous.data(Qt.ItemDataRole.UserRole) if previous else None
    widget.blockSignals(True);widget.setRowCount(len(rows))
    for i,row in enumerate(rows):
        for j,key in enumerate(keys):
            value=str(row.get(key, ""));item=QTableWidgetItem(value.replace("\n"," ")[:140]);item.setToolTip(value[:2000])
            item.setData(Qt.ItemDataRole.UserRole,row.get("entry_id",row.get("packet_id",row.get("id"))))
            widget.setItem(i,j,item)
        if widget.item(i,0).data(Qt.ItemDataRole.UserRole)==identity:widget.selectRow(i)
    widget.blockSignals(False)
    widget.verticalScrollBar().setValue(scroll)


def selected_id(widget):
    item=widget.item(widget.currentRow(),0)
    return item.data(Qt.ItemDataRole.UserRole) if item else None


class DataPages:
    def init_data_pages(self):
        self.tcp_adapter=TCPTargetIngestionAdapter(db_path=self.history_engine.db_path)
        self.packet_parser=TCPPacketGrammarParser(self.history_engine.db_path)
        self.pipeline=DataPipeline(self.hub.db_path,self.store.setting("pipeline_auto","true")=="true")
        self.key_vault=KeyVault(self.data_dir/"credentials")
        self.conversations=ConversationStore(self.data_dir/"conversations.sqlite3")
        self.cloud_requests={};self.llama_request=None
        self.data_events=queue.Queue();self.tcp_jobs=queue.Queue();self.tcp_busy=False
        self.cloud_controls={};self.cloud_busy=set();self.latest_pipeline={};self.latest_packet={}
        self.pipeline_history_revision=-1;self.google_revision=-1;self.last_pipeline_view=None
        self.last_data_capture=0;self.pipeline_definition_hash=None;self.cloud_results={}
        self.seen_transmit=set();self.data_active=False;self.scan_busy=False
        self.history_captured={};self.rendered_pipeline=None;self.packet_dirty=False

    def _background(self,kind,operation):
        def worker():
            try:self.data_events.put((kind,operation(),None))
            except Exception as error:self.data_events.put((kind,None,str(error)))
        threading.Thread(target=worker,name="Flux "+kind,daemon=True).start()

    def start_data_pages(self):
        self.data_active=True;self.pipeline.start()

    def stop_data_pages(self):
        self.data_active=False;self.pipeline.stop()

    def build_data_pages(self):
        self.build_google_page();self.build_pipeline_page()
        self.build_cloud_page("gemini","Gemini","gemini-3.8-flash")
        self.build_cloud_page("openai","ChatGPT / OpenAI API","gpt-6-astra")

    def build_google_page(self):
        page,layout=panel("GOOGLE AI MODE / INGEST → TRANSMIT")
        row=QHBoxLayout();self.google_status=note("Ready to ingest")
        row.addWidget(self.google_status,1);row.addWidget(button("Scan history now",self.scan_google_history))
        row.addWidget(button("Browser source…",lambda:self.navigate(10)));layout.addLayout(row)
        split=QSplitter()
        left,col=panel("INGESTION")
        col.addWidget(note("Browser scans read AI Mode URLs and titles. Paste or import the full question and answer below to retain their complete text."))
        self.google_input=QPlainTextEdit();self.google_input.setPlaceholderText("Google AI Mode input, code, or URL…");col.addWidget(self.google_input,1)
        self.google_output=QPlainTextEdit();self.google_output.setPlaceholderText("Google AI Mode answer / output…");col.addWidget(self.google_output,1)
        row=QHBoxLayout();row.addWidget(button("Ingest",self.ingest_google,True));row.addWidget(button("Import file",self.import_google))
        row.addWidget(button("Ingest & transmit",lambda:self.ingest_google(True)));col.addLayout(row)
        self.google_records=table(["SOURCE","INPUT","TIME"]);self.google_records.setMinimumHeight(125)
        self.google_records.itemSelectionChanged.connect(self.show_google_record);col.addWidget(self.google_records,2)
        split.addWidget(left)
        right,col=panel("TRANSMISSION")
        self.tcp_target=QLineEdit(self.store.setting("tcp_target","127.0.0.1:9999"));col.addWidget(self.tcp_target)
        row=QHBoxLayout();self.tcp_node=QLineEdit("google_ai_mode");self.tcp_node.setPlaceholderText("Node ID")
        self.tcp_state=QComboBox();self.tcp_state.addItems(["good","evil"])
        row.addWidget(self.tcp_node,1);row.addWidget(self.tcp_state);col.addLayout(row)
        row=QHBoxLayout();row.addWidget(button("Transmit selected",self.transmit_selected,True))
        row.addWidget(button("Run selected through pipeline",self.pipeline_selected_history));col.addLayout(row)
        self.google_auto=QCheckBox("Transmit newly ingested records automatically");col.addWidget(self.google_auto)
        col.addWidget(note("The complete selected input/output and source are sent inside the context field. A confirmed ACK is shown only after the target responds."))
        self.google_ack=QPlainTextEdit();self.google_ack.setReadOnly(True);self.google_ack.setPlaceholderText("Payload and acknowledgement appear here.");col.addWidget(self.google_ack,1)
        self.packet_table=table(["STATUS","TARGET","BIT","TIME"]);col.addWidget(self.packet_table,1)
        self.packet_table.itemSelectionChanged.connect(self.show_packet)
        self.packet_signature=note("");col.addWidget(self.packet_signature)
        split.addWidget(right);split.setSizes([520,560]);layout.addWidget(split,1);self.pages.addWidget(page)
        self.seen_transmit.update(self.history_fingerprint(r) for r in self.history_engine.rows(1000000))
        self.refresh_google()

    def scan_google_history(self):
        if self.scan_busy:return
        self.scan_busy=True;self.google_status.setText("Reading the selected browser history…")
        self._background("scan",self.history_engine.ingest_history_delta)

    def ingest_google(self,transmit=False):
        text=self.google_input.toPlainText()
        if not text.strip():self.google_status.setText("Enter or import an input first");return
        entry=uuid.uuid4().hex
        self.history_engine._force_direct_payload_ingestion(entry,text,self.google_output.toPlainText(),"Google AI Mode import")
        self.refresh_google();self.google_status.setText("Saved input and output · queued for the full pipeline")
        record=next(r for r in self.history_engine.rows(1000000) if r["entry_id"]==entry)
        self.capture_history(record)
        if transmit:self.queue_transmission(record)
        return entry

    def import_google(self):
        path,_=QFileDialog.getOpenFileName(self,"Import Google AI text or code",str(Path.home()),"Text / code (*.txt *.md *.json *.py *.java);;All files (*)")
        if path:
            try:self.google_input.setPlainText(Path(path).read_text(encoding="utf-8-sig"))
            except (OSError,UnicodeError) as error:self.google_status.setText(str(error))

    def selected_history_record(self):
        identity=selected_id(self.google_records)
        return next((r for r in self.history_engine.rows(1000000) if r["entry_id"]==identity),None)

    def show_google_record(self):
        record=self.selected_history_record()
        if record:
            self.google_input.setPlainText(record["raw_input"]);self.google_output.setPlainText(record["raw_output"])
            self.google_ack.setPlainText(json.dumps(record,indent=2,ensure_ascii=False))

    def transmit_selected(self):
        record=self.selected_history_record()
        if record:self.queue_transmission(record)
        else:self.google_status.setText("Select an ingested record, or use Ingest & transmit")

    def queue_transmission(self,record):
        try:
            host,port=parse_target(self.tcp_target.text());self.tcp_target.setText(f"{host}:{port}")
            self.store.set_setting("tcp_target",self.tcp_target.text())
            context=json.dumps({"stream":"google_ai_mode","record":record},ensure_ascii=False)
            node=self.tcp_node.text().strip() or "google_ai_mode"
            self.tcp_jobs.put((host,port,node,context,self.tcp_state.currentText(),record["entry_id"]))
            self.google_status.setText("Transmission queued")
            self.seen_transmit.add(self.history_fingerprint(record))
        except Exception as error:self.google_status.setText(str(error))

    def show_packet(self):
        identity=selected_id(self.packet_table)
        record=next((r for r in self.tcp_adapter.rows() if r["packet_id"]==identity),None)
        if record:self.google_ack.setPlainText(json.dumps(record,indent=2,ensure_ascii=False))

    def refresh_google(self):
        self.google_revision=self.history_engine.revision
        fill_table(self.google_records,self.history_engine.rows(),("source_kind","raw_input","system_timestamp"))
        fill_table(self.packet_table,self.tcp_adapter.rows(),("delivery_status","network_address","corrected_bit","timestamp"))
        stats=self.tcp_adapter.stats()
        self.packet_signature.setText(f"{stats['confirmed']} confirmed / {stats['total']} attempts\nSupplied grammar declaration: "+self.packet_parser.compile_network_grammar_signature())

    def build_pipeline_page(self):
        page,layout=panel("FULL ENGINE PIPELINE / AUTOMATIC OR MANUAL")
        row=QHBoxLayout();self.pipeline_auto=QCheckBox("Automatically process incoming data / code")
        self.pipeline_auto.setChecked(self.pipeline.auto);self.pipeline_auto.toggled.connect(self.toggle_pipeline)
        row.addWidget(self.pipeline_auto,1);row.addWidget(button("Run pending",self.run_pipeline_pending,True))
        row.addWidget(button("Run selected again",self.rerun_pipeline));layout.addLayout(row)
        layout.addWidget(note("History, local TCP messages, Observatory inputs, definitions, AI replies and sampled telemetry enter the same ledger. Code is parsed and retained as source. Every pass records the audit, nine register engines, grammar and binary/ternary results."))
        split=QSplitter();left,col=panel("DATA / CODE INPUT")
        self.pipeline_input=QPlainTextEdit();self.pipeline_input.setPlaceholderText('Paste text, Python, Java or JSON…\n\n{"state_reg":"good","evaluate":"evil","can":false,"cannot":true}')
        col.addWidget(self.pipeline_input,1)
        row=QHBoxLayout();row.addWidget(button("Run full process",self.run_pipeline_input,True));row.addWidget(button("Import file",self.import_pipeline));col.addLayout(row)
        col.addWidget(button("Audit selected input",self.audit_selected_pipeline))
        self.pipeline_table=table(["SOURCE","STATUS","ID"]);col.addWidget(self.pipeline_table,2)
        self.pipeline_table.itemSelectionChanged.connect(self.show_pipeline)
        split.addWidget(left);right,col=panel("STAGES / COMPLETE RECEIPT")
        self.pipeline_status=note("Ready");col.addWidget(self.pipeline_status)
        self.pipeline_result=QPlainTextEdit();self.pipeline_result.setReadOnly(True);col.addWidget(self.pipeline_result,1)
        row=QHBoxLayout();row.addWidget(button("Read with Gemini →",lambda:self.pipeline_to_cloud("gemini")))
        row.addWidget(button("Read with ChatGPT →",lambda:self.pipeline_to_cloud("openai")));col.addLayout(row)
        split.addWidget(right);split.setSizes([480,600]);layout.addWidget(split,1);self.pages.addWidget(page)

    def pipeline_context(self):
        return {"route":self.read_route(),"virtue":self.global_virtue_state}

    def audit_selected_pipeline(self):
        job_id=selected_id(self.pipeline_table)
        if not job_id:self.pipeline_status.setText("Select an input first");return
        self.queue_live_audit(job_id);self.navigate(18)

    def capture_pipeline(self,source,identity,payload,**kwargs):
        if getattr(self,"batching_inputs",False):
            self.capture_batch.append((source,str(identity),payload,self.batch_route,kwargs.get("force",False),kwargs.get("run_now",False)))
            return None
        return self.pipeline.submit(source,str(identity),payload,self.pipeline_context(),**kwargs)

    @staticmethod
    def history_fingerprint(record):
        return hashlib.sha256(encoded(record).encode()).hexdigest()

    def capture_history(self,record):
        # Parse the actual prompt/code while retaining the complete original pair.
        fingerprint=self.history_fingerprint(record)
        if self.history_captured.get(record["entry_id"])==fingerprint:return None
        self.history_captured[record["entry_id"]]=fingerprint
        return self.capture_pipeline("history:"+record["source_kind"],record["entry_id"],record)

    def pipeline_selected_history(self):
        record=self.selected_history_record()
        if not record:self.google_status.setText("Select an ingested record first");return
        self.capture_pipeline("history:"+record["source_kind"],record["entry_id"],record,force=True,run_now=True)
        self.pipeline.start();self.navigate(15)

    def toggle_pipeline(self,enabled):
        self.pipeline.set_auto(enabled);self.store.set_setting("pipeline_auto",str(enabled).lower())
        if enabled:self.pipeline.start()

    def run_pipeline_pending(self):
        self.pipeline.run_pending();self.pipeline.start()

    def run_pipeline_input(self):
        text=self.pipeline_input.toPlainText()
        if not text.strip():self.pipeline_status.setText("Enter data or code first");return
        self.capture_pipeline("manual",uuid.uuid4().hex,text,force=True,run_now=True);self.pipeline.start()
        self.pipeline_status.setText("Queued full process")

    def import_pipeline(self):
        path,_=QFileDialog.getOpenFileName(self,"Import data or code",str(Path.home()),"All files (*)")
        if path:
            try:self.pipeline_input.setPlainText(Path(path).read_text(encoding="utf-8-sig"))
            except (OSError,UnicodeError) as error:self.pipeline_status.setText(str(error))

    def rerun_pipeline(self):
        identity=selected_id(self.pipeline_table)
        if identity:self.pipeline.run_selected(identity);self.pipeline.start()

    def show_pipeline(self):
        job=self.pipeline.detail(selected_id(self.pipeline_table))
        if job:
            update_text(self.pipeline_result,json.dumps(json.loads(job["result_json"] or job["input_json"]),indent=2,ensure_ascii=False))
            self.pipeline_status.setText(job["source"]+" · "+job["status"]+(" · "+job["error"] if job["error"] else ""))

    def pipeline_to_cloud(self,provider):
        controls=self.cloud_controls[provider]
        controls["input"].setPlainText("Read this full engine-pipeline receipt:\n"+self.pipeline_result.toPlainText())
        self.navigate(16 if provider=="gemini" else 17)

    def build_cloud_page(self,provider,name,default_model):
        page,layout=panel(name.upper()+" / INPUT ↔ OUTPUT")
        controls={};self.cloud_controls[provider]=controls
        row=QHBoxLayout();key=QLineEdit();key.setEchoMode(QLineEdit.EchoMode.Password);key.setPlaceholderText(name+" API key")
        controls["key"]=key;row.addWidget(key,1)
        row.addWidget(button("Save key",lambda:self.save_cloud_key(provider)))
        row.addWidget(button("Forget key",lambda:self.forget_cloud_key(provider)));layout.addLayout(row)
        controls["status"]=note("Enter an API key · saved keys are encrypted for this Windows account")
        try:
            saved=self.key_vault.load(provider);key.setText(saved)
            if saved:controls["status"].setText("Saved key loaded · encrypted for this Windows account")
        except OSError as error:controls["status"].setText("Saved key could not be loaded: "+str(error))
        layout.addWidget(controls["status"])
        saved=QHBoxLayout();saved.addWidget(QLabel("Saved conversations"))
        controls["sessions"]=QComboBox();controls["sessions"].setMinimumContentsLength(20)
        controls["sessions"].setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        controls["sessions"].currentIndexChanged.connect(lambda index:self.select_ai_conversation(provider))
        saved.addWidget(controls["sessions"],1);layout.addLayout(saved)
        row=QHBoxLayout();model=QComboBox();model.setEditable(True);model.addItem(self.store.setting(provider+"_model",default_model));controls["model"]=model
        row.addWidget(QLabel("Model"));row.addWidget(model,1);row.addWidget(button("Load available models",lambda:self.load_cloud_models(provider)))
        include=QCheckBox("Include engine state");include.setChecked(self.store.setting(provider+"_include_state","true")=="true");controls["include"]=include;row.addWidget(include)
        row.addWidget(button("Preview sent input",lambda:self.preview_cloud(provider)));layout.addLayout(row)
        self.build_cloud_context_controls(provider,layout)
        layout.addWidget(note("Only selected engine context is attached. Compact summaries reduce large arrays and repeated results. Your full saved history and engine records remain local; the preview shows what this request includes."))
        split=QSplitter();left,col=panel("INPUT")
        prompt=QPlainTextEdit();prompt.setPlaceholderText("Ask about the engine, enter text or code…");controls["input"]=prompt;col.addWidget(prompt,1)
        row=QHBoxLayout();send=button("Send →",lambda:self.send_cloud(provider),True);controls["send"]=send;row.addWidget(send)
        controls["reset"]=button("Reset conversation",lambda:self.reset_ai_conversation(provider));row.addWidget(controls["reset"])
        row.addWidget(button("Run input through pipeline",lambda:self.cloud_input_pipeline(provider)));col.addLayout(row)
        controls["preview"]=QPlainTextEdit();controls["preview"].setReadOnly(True);controls["preview"].setPlaceholderText("Preview of the complete outgoing message and state");col.addWidget(controls["preview"],1)
        split.addWidget(left);right,col=panel("OUTPUT")
        tabs=QTabWidget();output=QPlainTextEdit();output.setReadOnly(True);output.setPlaceholderText("The model’s actual response appears here.");controls["output"]=output
        conversation=QPlainTextEdit();conversation.setReadOnly(True);conversation.setPlaceholderText("Messages are remembered until you reset this conversation.");controls["conversation"]=conversation
        tabs.addTab(conversation,"Conversation");tabs.addTab(output,"Latest reply");col.addWidget(tabs,1)
        controls["memory"]=note("");col.addWidget(controls["memory"])
        row=QHBoxLayout();row.addWidget(button("Run output through pipeline",lambda:self.cloud_output_pipeline(provider)))
        row.addWidget(button("Copy output",lambda:output.selectAll() or output.copy()));col.addLayout(row)
        controls["usage"]=note("");col.addWidget(controls["usage"]);split.addWidget(right)
        split.setSizes([530,550]);layout.addWidget(split,1);self.pages.addWidget(page)
        self.refresh_conversation(provider)

    def refresh_conversation(self,provider):
        identity,messages=self.conversations.snapshot(provider)
        if provider=="llama":
            output=self.llama_conversation;status=self.llama_memory;selector=self.llama_sessions
        else:
            controls=self.cloud_controls[provider];output=controls["conversation"];status=controls["memory"];selector=controls["sessions"]
        selector.blockSignals(True);selector.clear()
        for session in self.conversations.list(provider):
            stamp=time.strftime('%d %b %H:%M',time.localtime(session["created_at"]))
            selector.addItem(f"{stamp} · {session['title']} · {session['message_count']//2} exchanges",session["id"])
        selector.setCurrentIndex(selector.findData(identity));selector.blockSignals(False)
        reset=getattr(output,"_conversation_id",None)!=identity
        update_text(output,transcript(messages),follow=True,reset=reset)
        output._conversation_id=identity
        if reset and messages:
            latest=self.guide_output if provider=="llama" else controls["output"]
            update_text(latest,messages[-1]["display"],reset=True)
        status.setText(f"{len(messages)//2} exchanges remembered · saved locally")

    def reset_ai_conversation(self,provider):
        self.conversations.reset(provider)
        self.clear_ai_request(provider)
        self.refresh_conversation(provider)
        self.log_activity("CONVERSATION",provider+" · reset; previous conversation saved")

    def select_ai_conversation(self,provider):
        selector=self.llama_sessions if provider=="llama" else self.cloud_controls[provider]["sessions"]
        identity=selector.currentData()
        if not identity or identity==self.conversations.snapshot(provider)[0]:return
        self.conversations.select(provider,identity)
        self.clear_ai_request(provider)
        self.refresh_conversation(provider)
        _,messages=self.conversations.snapshot(provider)
        if provider=="llama":
            self.llama_status.setText("Saved conversation opened · ready to continue")
            if messages:self.guide_output.setPlainText(messages[-1]["display"])
        else:
            controls=self.cloud_controls[provider];controls["status"].setText("Saved conversation opened · ready to continue")
            if messages:controls["output"].setPlainText(messages[-1]["display"])

    def clear_ai_request(self,provider):
        if provider=="llama":
            self.llama_request=None;self.llama_busy=False;self.guide_button.setEnabled(True)
            self.prompt_input.clear();self.guide_output.clear();self.llama_status.setText("Conversation reset")
            if self.command_mode.currentIndex()==1:
                self.command_input.clear();self.command_result.clear()
        else:
            self.cloud_requests.pop(provider,None);self.cloud_busy.discard(provider);self.cloud_results.pop(provider,None)
            controls=self.cloud_controls[provider];controls["send"].setEnabled(True)
            for key in ("input","output","preview"):controls[key].clear()
            controls["usage"].clear();controls["status"].setText("Conversation reset")

    def save_cloud_key(self,provider):
        controls=self.cloud_controls[provider]
        try:
            self.key_vault.save(provider,controls["key"].text());controls["status"].setText("Key saved with Windows account encryption")
            return True
        except (OSError,ValueError) as error:controls["status"].setText(str(error));return False

    def forget_cloud_key(self,provider):
        controls=self.cloud_controls[provider]
        try:self.key_vault.delete(provider);controls["key"].clear();controls["status"].setText("Saved key removed")
        except OSError as error:controls["status"].setText(str(error))

    def engine_state(self):
        return {"reference_engines":self.reference.snapshot(),"neural_learning":self.neural.snapshot(),"web_research":self.web_research.snapshot(),"souls_ingress":self.souls_ingress.snapshot(),"virtue_text":self.virtue_text.snapshot(),"karmic_welfare":self.karmic_welfare.snapshot(),"platform_alignment":self.platform_alignment.snapshot(),"unified_core":self.unified_core.snapshot(),"mesh_gateway":self.mesh_module.snapshot(),"continuous_audit":self.live_audit.snapshot(),"captured_at":time.strftime('%Y-%m-%d %H:%M:%S'),"route":self.read_route(),
            "engines":self.engine_results,"process_telemetry":self.bus_monitor.get_snapshot(),
            "hub":{"status":self.hub.status,"node_count":len(self.hub.rows())},
            "observatory":self.observatory.view(),"pipeline_counts":self.pipeline.stats(),
            "latest_pipeline":{"id":self.latest_pipeline.get("id"),"source":self.latest_pipeline.get("source"),
                "status":self.latest_pipeline.get("status"),"stages":self.latest_pipeline.get("stages",[]),
                "audit":self.latest_pipeline.get("audit"),"engines":self.latest_pipeline.get("engines",[]),
                "binary_ternary":self.latest_pipeline.get("binary_ternary",[])},"tcp":self.tcp_adapter.stats()}

    def build_cloud_context_controls(self,provider,layout):
        controls=self.cloud_controls[provider]
        try: controls["selected_engines"]=json.loads(self.store.setting(provider+"_engine_selection","null"))
        except (ValueError,TypeError): controls["selected_engines"]=None
        row=QHBoxLayout();detail=QComboBox()
        detail.addItem("Compact summaries","compact");detail.addItem("Full selected results","full")
        detail.setCurrentIndex(max(0,detail.findData(self.store.setting(provider+"_context_detail","compact"))))
        controls["context_detail"]=detail;row.addWidget(detail)
        row.addWidget(button("Choose engines…",lambda:self.choose_cloud_engines(provider)))
        if provider=="gemini":
            fit=QCheckBox("Fit conversation to input budget")
            fit.setChecked(self.store.setting("gemini_auto_fit","true")=="true")
            controls["auto_fit"]=fit;row.addWidget(fit)
            budget=QSpinBox();budget.setRange(1000,2000000);budget.setSingleStep(1000)
            budget.setValue(int(self.store.setting("gemini_input_budget","24000")))
            budget.setSuffix(" tokens");controls["input_budget"]=budget;row.addWidget(budget)
            fit.toggled.connect(lambda:self.save_cloud_context(provider))
            budget.valueChanged.connect(lambda:self.save_cloud_context(provider))
        row.addStretch();layout.addLayout(row)
        controls["context_status"]=note("Context preferences are saved separately for each provider.")
        layout.addWidget(controls["context_status"])
        detail.currentIndexChanged.connect(lambda:self.save_cloud_context(provider))
        controls["include"].toggled.connect(lambda:self.save_cloud_context(provider))

    def save_cloud_context(self,provider):
        c=self.cloud_controls[provider]
        self.store.set_setting(provider+"_engine_selection",json.dumps(c["selected_engines"]))
        self.store.set_setting(provider+"_context_detail",c["context_detail"].currentData())
        self.store.set_setting(provider+"_include_state",str(c["include"].isChecked()).lower())
        if provider=="gemini":
            self.store.set_setting("gemini_auto_fit",str(c["auto_fit"].isChecked()).lower())
            self.store.set_setting("gemini_input_budget",str(c["input_budget"].value()))
        c["context_status"].setText("Context choices saved · complete local history remains unchanged")

    def choose_cloud_engines(self,provider):
        c=self.cloud_controls[provider];dialog=QDialog(self);dialog.setWindowTitle("Choose engine context")
        dialog.resize(540,650);layout=QVBoxLayout(dialog)
        layout.addWidget(note("Choose what this provider can read in its outgoing state attachment."))
        scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();items=QVBoxLayout(body)
        choices=[]
        for key,label in context_choices(self.engine_state()):
            check=QCheckBox(label);check.setChecked(c["selected_engines"] is None or key in c["selected_engines"])
            items.addWidget(check);choices.append((key,check))
        items.addStretch();scroll.setWidget(body);layout.addWidget(scroll)
        row=QHBoxLayout()
        row.addWidget(button("Select all",lambda:[check.setChecked(True) for _,check in choices]))
        row.addWidget(button("Clear selection",lambda:[check.setChecked(False) for _,check in choices]));layout.addLayout(row)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            c["selected_engines"]=[key for key,check in choices if check.isChecked()]
            self.save_cloud_context(provider)

    def cloud_context(self,provider):
        c=self.cloud_controls[provider]
        return select_context(self.engine_state(),c["selected_engines"],c["context_detail"].currentData()) if c["include"].isChecked() else None

    def preview_cloud(self,provider):
        controls=self.cloud_controls[provider]
        state=self.cloud_context(provider)
        _,history=self.conversations.snapshot(provider)
        prompt=controls["input"].toPlainText()
        try:
            if provider=="gemini" and controls["auto_fit"].isChecked():
                prompt,history,report=fit_context(prompt,state,history,controls["input_budget"].value(),estimated_tokens,compose_input)
                controls["context_status"].setText(f"Preview estimate: {report['input_tokens']:,} tokens · {report['recent_messages']//2} recent exchanges · {report['excerpted_messages']} older messages as excerpts. Gemini checks actual tokens when sending.")
            controls["preview"].setPlainText(preview(prompt,state,history,compose_input))
        except ValueError as error:
            controls["context_status"].setText(str(error))
            controls["preview"].setPlainText(compose_input(prompt,state))

    def load_cloud_models(self,provider):
        if provider in self.cloud_busy:return
        controls=self.cloud_controls[provider];key=controls["key"].text().strip()
        if not key:controls["status"].setText("Enter an API key first");return
        token=uuid.uuid4().hex;self.cloud_requests[provider]={"token":token}
        self.cloud_busy.add(provider);controls["status"].setText("Loading available models…")
        self._background("models:"+provider+":"+token,lambda:list_models(provider,key))

    def send_cloud(self,provider):
        if provider in self.cloud_busy:return
        controls=self.cloud_controls[provider];prompt=controls["input"].toPlainText()
        if not prompt.strip():controls["status"].setText("Enter an input first");return
        if not self.save_cloud_key(provider):return
        key=controls["key"].text().strip();model=controls["model"].currentText().strip()
        state=self.cloud_context(provider)
        identity,history=self.conversations.snapshot(provider)
        token=uuid.uuid4().hex
        self.cloud_requests[provider]={"token":token,"conversation_id":identity,"prompt":prompt}
        self.store.set_setting(provider+"_model",model)
        self.capture_pipeline(provider+" input",str(time.time_ns()),prompt)
        controls["preview"].setPlainText(preview(prompt,state,history,compose_input));controls["send"].setEnabled(False)
        controls["status"].setText("Waiting for "+provider+"…");self.cloud_busy.add(provider)
        options={"auto_fit":controls["auto_fit"].isChecked(),"input_budget":controls["input_budget"].value()} if provider=="gemini" else None
        self._background("cloud:"+provider+":"+token,lambda:generate(provider,key,model,prompt,state,history=history,context_options=options))

    def cloud_input_pipeline(self,provider):
        self.pipeline_input.setPlainText(self.cloud_controls[provider]["input"].toPlainText());self.run_pipeline_input();self.navigate(15)

    def cloud_output_pipeline(self,provider):
        text=self.cloud_controls[provider]["output"].toPlainText()
        if not text:return
        self.capture_pipeline(provider+" output",uuid.uuid4().hex,text,force=True,run_now=True);self.pipeline.start();self.navigate(15)

    def tick_data_pages(self):
        if self.history_engine.revision!=self.pipeline_history_revision:
            self.pipeline_history_revision=self.history_engine.revision
            for record in self.history_engine.rows(1000000):
                self.capture_history(record)
                fingerprint=self.history_fingerprint(record)
                if fingerprint not in self.seen_transmit:
                    self.seen_transmit.add(fingerprint)
                    if self.google_auto.isChecked():self.queue_transmission(record)
        if self.pages.currentIndex()==14 and self.history_engine.revision!=self.google_revision:self.refresh_google()
        if self.data_active and time.monotonic()-self.last_data_capture>=5:
            self.last_data_capture=time.monotonic()
            telemetry=self.bus_monitor.get_snapshot()
            self.capture_pipeline("telemetry","current",telemetry)
            definitions=self.store.search();fingerprint=hashlib.sha256(encoded(definitions).encode()).hexdigest()
            if fingerprint!=self.pipeline_definition_hash:
                self.pipeline_definition_hash=fingerprint
                if definitions:self.capture_pipeline("definitions","library",definitions)
        if not self.tcp_busy and not self.tcp_jobs.empty():
            host,port,node,context,state,entry=self.tcp_jobs.get_nowait();self.tcp_busy=True
            self._background("tcp",lambda:TCPTargetIngestionAdapter(host,port,self.history_engine.db_path).transmit_and_ingest_payload(node,context,state,entry))
        while not self.data_events.empty():
            kind,result,error=self.data_events.get_nowait()
            if kind=="tcp":
                self.tcp_busy=False;self.latest_packet=result or {"status":"ERROR","error":error}
                self.capture_pipeline("TCP receipt",self.latest_packet.get("packet_id",str(time.time_ns())),self.latest_packet)
                update_text(self.google_ack,json.dumps(self.latest_packet,indent=2,ensure_ascii=False));self.packet_dirty=True
                self.google_status.setText("Transmission: "+self.latest_packet["status"])
                self.log_activity("TCP",self.latest_packet["status"])
            elif kind=="scan":
                self.scan_busy=False;self.google_status.setText(error or self.history_engine.status);self.refresh_google()
            elif kind.startswith(("cloud:","models:")):
                parts=kind.split(":");provider=parts[1]
                pending=self.cloud_requests.get(provider)
                if not pending or len(parts)!=3 or parts[2]!=pending["token"]:continue
                self.cloud_requests.pop(provider,None)
                controls=self.cloud_controls[provider];self.cloud_busy.discard(provider);controls["send"].setEnabled(True)
                if error:
                    controls["status"].setText(redact(error,controls["key"].text()));continue
                if kind.startswith("models:"):
                    current=controls["model"].currentText();controls["model"].clear();controls["model"].addItems(result);controls["model"].setCurrentText(current)
                    controls["status"].setText(f"{len(result)} models returned · choose a text-generation model")
                else:
                    wire=result.pop("conversation_reply",None)
                    if result["output"]:
                        if not self.conversations.complete(provider,pending["conversation_id"],pending["prompt"],result["output"],result["model"],wire):continue
                        self.refresh_conversation(provider)
                    self.cloud_results[provider]=result;update_text(controls["output"],result["output"] or "No text returned. Status: "+result["status"])
                    controls["status"].setText(result["model"]+" · "+result["status"])
                    controls["usage"].setText("Usage: "+json.dumps(result["usage"]))
                    context=result.get("context_report")
                    if context:
                        controls["context_status"].setText(f"{context['input_tokens']:,} / {context['budget']:,} input tokens · {context['recent_messages']//2} recent exchanges · {context['excerpted_messages']} older messages as excerpts · "+context["method"])
                        if result.get("context_preview"):update_text(controls["preview"],result["context_preview"])
                    entry=uuid.uuid4().hex
                    self.history_engine._force_direct_payload_ingestion(entry,result["input"],result["output"],provider+" API")
                    self.log_activity(provider.upper(),result["model"]+" · "+result["status"])
        while not self.pipeline.events.empty():
            result=self.pipeline.events.get_nowait();self.latest_pipeline=result
            self.pipeline_status.setText(result.get("source","Pipeline")+" · "+result["status"])
            self.log_activity("PIPELINE",result.get("source","")+" · "+result["status"])
            for start in range(0,len(result.get("audit",{}).get("transitions",[])),16):
                group=result["audit"]["transitions"][start:start+16]
                self.obs_grid.add(register_record([r["path"] for r in group],[r["before"] for r in group],[r["after"] for r in group],"Pipeline · "+result.get("source",""),result.get("id")))
            self.observatory.publish("pipeline",{"id":result.get("id"),"source":result.get("source"),"status":result["status"],"flips":result.get("audit",{}).get("flips",0)})
        if not getattr(self,"batching_inputs",False):self.render_data_pages()

    def render_data_pages(self):
        page=self.pages.currentIndex()
        if page==14 and (self.google_revision!=self.history_engine.revision or self.packet_dirty):
            self.refresh_google();self.packet_dirty=False
        if page==15:
            rows=self.pipeline.rows()
            if rows!=self.last_pipeline_view:
                self.last_pipeline_view=rows;fill_table(self.pipeline_table,rows,("source","status","id"))
                if selected_id(self.pipeline_table):self.show_pipeline()
            if selected_id(self.pipeline_table) is None and self.rendered_pipeline is not self.latest_pipeline:
                update_text(self.pipeline_result,json.dumps(self.latest_pipeline,indent=2,ensure_ascii=False))
                self.rendered_pipeline=self.latest_pipeline
