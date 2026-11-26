"""Independent Overview control and inspectable results for all new engines."""
from copy import deepcopy
import json
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,QCheckBox,QComboBox,QFileDialog,QHBoxLayout,QLabel,
    QPlainTextEdit,QPushButton,QSplitter,QVBoxLayout,QWidget)
from unified_runtime import ContinuousUnifiedModule,ENGINE_NAMES,INPUT_TEMPLATE,execute_unified_engines,resolve_result
from infrastructure_pdf import GraphicalPDFGenerator
from text_view import update_text


class UnifiedPages:
    def init_unified_core(self):
        self.unified_core=ContinuousUnifiedModule(self.hub.db_path)
        self.unified_rows=[];self.unified_refresh=0;self.unified_pending=None
        self.unified_view=None;self.unified_rendered=None

    def build_unified_overview(self,layout):
        row=QHBoxLayout();self.unified_toggle=QCheckBox('Continuous unified core · 23 engines')
        self.unified_toggle.setChecked(self.unified_core.enabled);self.unified_toggle.toggled.connect(self.toggle_unified_core)
        row.addWidget(self.unified_toggle)
        self.unified_status=QLabel('Ready');self.unified_status.setObjectName('muted');row.addWidget(self.unified_status,1)
        open_page=QPushButton('Inspect unified engines →');open_page.clicked.connect(lambda:self.navigate(21));row.addWidget(open_page)
        layout.addLayout(row)

    def toggle_unified_core(self,enabled):
        try:self.unified_core.set_enabled(enabled);self.unified_core.start()
        except Exception as error:
            self.unified_toggle.blockSignals(True);self.unified_toggle.setChecked(self.unified_core.enabled);self.unified_toggle.blockSignals(False)
            self.unified_status.setText(str(error));return
        self.render_unified_core()

    def build_unified_page(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        intro=QLabel('All 23 named engines process new captured inputs. The separate Overview switch saves its state; Run once also works while paused. '
                     'Host attributes are measured. Resonance, finance, energy and labor values are calculations from your inputs.')
        intro.setWordWrap(True);layout.addWidget(intro)
        top=QHBoxLayout();self.unified_sessions=QComboBox();self.unified_sessions.addItem('Latest result',None)
        self.unified_sessions.currentIndexChanged.connect(self.show_unified_result);top.addWidget(self.unified_sessions,1)
        copy=QPushButton('Copy displayed result');copy.clicked.connect(lambda:QApplication.clipboard().setText(self.unified_output.toPlainText()));top.addWidget(copy)
        pdf=QPushButton('Export PDF');pdf.clicked.connect(self.export_unified_pdf);top.addWidget(pdf);layout.addLayout(top)
        split=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget();column=QVBoxLayout(left);column.setContentsMargins(0,0,8,0)
        self.unified_input=QPlainTextEdit();self.unified_input.setPlaceholderText('Text, code or JSON. Use the editable example for features, lessons, node scores, banking, energy and labor inputs.')
        column.addWidget(self.unified_input,1)
        template=QPushButton('Supplied examples');template.clicked.connect(self.add_unified_template)
        run=QPushButton('Run once · all engines');run.setObjectName('primary');run.clicked.connect(self.run_unified_input)
        buttons=QHBoxLayout();buttons.addWidget(template);buttons.addWidget(run);column.addLayout(buttons)
        self.unified_input_status=QLabel('Ready');self.unified_input_status.setWordWrap(True);column.addWidget(self.unified_input_status)
        note=QLabel('PDFs are created only when you export. Every input and receipt stays in the database.');note.setWordWrap(True);note.setObjectName('muted');column.addWidget(note)
        split.addWidget(left)
        right=QWidget();results=QVBoxLayout(right);results.setContentsMargins(8,0,0,0)
        self.unified_engines=QComboBox();self.unified_engines.addItem('Complete run · all engines',None)
        for i,name in enumerate(ENGINE_NAMES,1):self.unified_engines.addItem(f'{i:02d}  {name}',name)
        self.unified_engines.currentIndexChanged.connect(self.display_unified_selection);results.addWidget(self.unified_engines)
        self.unified_bits=QLabel('Binary / balanced ternary: waiting for input');self.unified_bits.setWordWrap(True);self.unified_bits.setObjectName('eyebrow');results.addWidget(self.unified_bits)
        self.unified_output=QPlainTextEdit();self.unified_output.setReadOnly(True);results.addWidget(self.unified_output,1)
        split.addWidget(right);split.setSizes([450,650]);layout.addWidget(split,1);self.pages.addWidget(page)

    def add_unified_template(self):
        example=deepcopy(INPUT_TEMPLATE)
        example['text']=self.unified_input.toPlainText() or example['text']
        self.unified_input.setPlainText(json.dumps(example,indent=2))
        self.unified_input_status.setText('Supplied example assumptions · edit before running')

    def run_unified_input(self):
        text=self.unified_input.toPlainText()
        if not text.strip():self.unified_input_status.setText('Enter an input first');return
        try:self.queue_unified_input(text)
        except Exception as error:self.unified_input_status.setText(str(error))

    def queue_unified_input(self,payload):
        job=self.pipeline.submit('Unified core manual',uuid.uuid4().hex,payload,self.pipeline_context(),force=True)
        self.unified_core.request(job);self.unified_core.start();self.unified_pending=job
        self.unified_sessions.setCurrentIndex(0);self.unified_input_status.setText('Queued · '+job)
        return job

    def show_unified_result(self):
        job=self.unified_sessions.currentData() or self.unified_core.snapshot()['latest'].get('job_id')
        if not job:return
        result=self.unified_core.detail(job)
        if result:
            self.unified_view=result;self.unified_rendered=job;self.display_unified_selection()

    def display_unified_selection(self):
        result=self.unified_view
        if not result:return
        name=self.unified_engines.currentData()
        selected=resolve_result(result,name) if name and name in result.get('engines',{}) else result
        update_text(self.unified_output,json.dumps(selected,indent=2,ensure_ascii=False))
        statuses={row['engine']:row['status'] for row in result.get('stages',[])}
        self.unified_bits.setText((statuses.get(name,'') if name else result['status'])+
            ' · '+str(len(statuses))+' engines · '+str(result.get('milliseconds','—'))+' ms\nBinary: '+''.join(map(str,result.get('binary',[])))+
            '\nBalanced ternary: '+' '.join({-1:'−',0:'0',1:'+'}[x] for x in result.get('balanced_ternary',[])))

    def export_unified_pdf(self):
        if not self.unified_view:self.unified_input_status.setText('Run or select a result first');return
        try:
            manifest=resolve_result(self.unified_view,'InfrastructureLogCompiler')
            if 'error' in manifest:raise ValueError('Infrastructure calculation has errors; inspect the selected engines first')
            path,_=QFileDialog.getSaveFileName(self,'Export infrastructure report','FluxBus-infrastructure.pdf','PDF (*.pdf)')
            if path:
                GraphicalPDFGenerator().export(path,manifest)
                self.unified_input_status.setText('Exported '+path)
                self.log_activity('UNIFIED PDF','Exported '+path)
        except Exception as error:self.unified_input_status.setText(str(error))

    def render_unified_core(self):
        state=self.unified_core.snapshot();latest=state['latest']
        status='Processing' if state['active_job'] else 'Paused' if not state['enabled'] else 'Running' if state['running'] else 'Ready'
        self.unified_status.setText(state['error'] or status+' · '+str(latest.get('status') or 'waiting for inputs'))
        if self.pages.currentIndex()!=21:return
        if time.monotonic()-self.unified_refresh>=2:
            self.unified_refresh=time.monotonic();rows=self.unified_core.history()
            if rows!=self.unified_rows:
                selected=self.unified_sessions.currentData();self.unified_sessions.blockSignals(True)
                self.unified_sessions.clear();self.unified_sessions.addItem('Latest result',None)
                for row in rows:self.unified_sessions.addItem(row['status']+' · '+row['source']+' · '+row['job_id'][:8],row['job_id'])
                index=self.unified_sessions.findData(selected)
                if selected and index<0:self.unified_sessions.addItem('Selected · '+selected[:8],selected);index=self.unified_sessions.count()-1
                self.unified_sessions.setCurrentIndex(max(0,index));self.unified_sessions.blockSignals(False);self.unified_rows=rows
        if self.unified_pending and self.unified_core.ready(self.unified_pending):
            job=self.unified_pending;self.unified_pending=None;index=self.unified_sessions.findData(job)
            if index<0:self.unified_sessions.addItem('Requested · '+job[:8],job);index=self.unified_sessions.count()-1
            self.unified_sessions.setCurrentIndex(index);self.unified_input_status.setText('Saved · '+job)
        job=self.unified_sessions.currentData() or latest.get('job_id')
        if job!=self.unified_rendered:self.show_unified_result()
