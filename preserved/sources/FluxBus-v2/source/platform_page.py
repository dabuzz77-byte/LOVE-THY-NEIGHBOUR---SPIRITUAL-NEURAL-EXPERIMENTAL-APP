"""Independent Overview control and inspectable results for all new engines."""
from copy import deepcopy
import json
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,QCheckBox,QComboBox,QHBoxLayout,QLabel,
    QPlainTextEdit,QPushButton,QSplitter,QVBoxLayout,QWidget)
from platform_alignment import ContinuousPlatformModule,ENGINE_NAMES,INPUT_TEMPLATE
from unified_runtime import resolve_result
from text_view import update_text


class PlatformPages:
    def init_platform_alignment(self):
        self.platform_alignment=ContinuousPlatformModule(self.hub.db_path)
        self.platform_rows=[];self.platform_refresh=0;self.platform_pending=None
        self.platform_view=None;self.platform_rendered=None

    def build_platform_overview(self,layout):
        row=QHBoxLayout();self.platform_toggle=QCheckBox('Continuous platform alignment · 10 components')
        self.platform_toggle.setChecked(self.platform_alignment.enabled);self.platform_toggle.toggled.connect(self.toggle_platform_alignment)
        row.addWidget(self.platform_toggle)
        self.platform_status=QLabel('Ready');self.platform_status.setObjectName('muted');row.addWidget(self.platform_status,1)
        open_page=QPushButton('Inspect platform alignment →');open_page.clicked.connect(lambda:self.navigate(22));row.addWidget(open_page)
        layout.addLayout(row)

    def toggle_platform_alignment(self,enabled):
        try:self.platform_alignment.set_enabled(enabled);self.platform_alignment.start()
        except Exception as error:
            self.platform_toggle.blockSignals(True);self.platform_toggle.setChecked(self.platform_alignment.enabled);self.platform_toggle.blockSignals(False)
            self.platform_status.setText(str(error));return
        self.render_platform_alignment()

    def build_platform_page(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        intro=QLabel('PlatformAlignmentEngine runs all ten components. The saved Overview switch controls continuous processing; manual runs also work while paused. '
                     'Inspect scores, convergence, Krampus node results, base-3 conversions and the combined manifest.')
        intro.setWordWrap(True);layout.addWidget(intro)
        top=QHBoxLayout();self.platform_sessions=QComboBox();self.platform_sessions.addItem('Latest result',None)
        self.platform_sessions.currentIndexChanged.connect(self.show_platform_result);top.addWidget(self.platform_sessions,1)
        copy=QPushButton('Copy displayed result');self.platform_copy=copy;copy.clicked.connect(lambda:QApplication.clipboard().setText(self.platform_output.toPlainText()));top.addWidget(copy)
        layout.addLayout(top)
        split=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget();column=QVBoxLayout(left);column.setContentsMargins(0,0,8,0)
        self.platform_input=QPlainTextEdit();self.platform_input.setPlaceholderText('Text, code or JSON. Use the editable example for features, node scores, resonance, loopback depth, input mask, network entities and ternary vectors.')
        column.addWidget(self.platform_input,1)
        template=QPushButton('Supplied examples');template.clicked.connect(self.add_platform_template)
        run=QPushButton('Run PlatformAlignmentEngine');run.setObjectName('primary');run.clicked.connect(self.run_platform_input)
        buttons=QHBoxLayout();buttons.addWidget(template);buttons.addWidget(run);column.addLayout(buttons)
        self.platform_input_status=QLabel('Ready');self.platform_input_status.setWordWrap(True);column.addWidget(self.platform_input_status)
        note=QLabel('Each run saves its original input and complete results. No files are generated automatically.');note.setWordWrap(True);note.setObjectName('muted');column.addWidget(note)
        split.addWidget(left)
        right=QWidget();results=QVBoxLayout(right);results.setContentsMargins(8,0,0,0)
        self.platform_engines=QComboBox();self.platform_engines.addItem('PlatformAlignmentEngine · complete run',None)
        for i,name in enumerate(ENGINE_NAMES,1):self.platform_engines.addItem(f'{i:02d}  {name}',name)
        self.platform_engines.currentIndexChanged.connect(self.display_platform_selection);results.addWidget(self.platform_engines)
        self.platform_bits=QLabel('Binary / balanced ternary: waiting for input');self.platform_bits.setWordWrap(True);self.platform_bits.setObjectName('eyebrow');results.addWidget(self.platform_bits)
        self.platform_output=QPlainTextEdit();self.platform_output.setReadOnly(True);results.addWidget(self.platform_output,1)
        split.addWidget(right);split.setSizes([450,650]);layout.addWidget(split,1);self.pages.addWidget(page)

    def add_platform_template(self):
        example=deepcopy(INPUT_TEMPLATE)
        example['text']=self.platform_input.toPlainText() or example['text']
        self.platform_input.setPlainText(json.dumps(example,indent=2))
        self.platform_input_status.setText('Supplied example assumptions · edit before running')

    def run_platform_input(self):
        text=self.platform_input.toPlainText()
        if not text.strip():self.platform_input_status.setText('Enter an input first');return
        try:self.queue_platform_input(text)
        except Exception as error:self.platform_input_status.setText(str(error))

    def queue_platform_input(self,payload):
        job=self.pipeline.submit('Platform alignment manual',uuid.uuid4().hex,payload,self.pipeline_context(),force=True)
        self.platform_alignment.request(job);self.platform_alignment.start();self.platform_pending=job
        self.platform_sessions.setCurrentIndex(0);self.platform_input_status.setText('Queued · '+job)
        return job

    def show_platform_result(self):
        job=self.platform_sessions.currentData() or self.platform_alignment.snapshot()['latest'].get('job_id')
        if not job:return
        result=self.platform_alignment.detail(job)
        if result:
            self.platform_view=result;self.platform_rendered=job;self.display_platform_selection()

    def display_platform_selection(self):
        result=self.platform_view
        if not result:return
        name=self.platform_engines.currentData()
        selected=resolve_result(result,name) if name and name in result.get('engines',{}) else result
        update_text(self.platform_output,json.dumps(selected,indent=2,ensure_ascii=False))
        statuses={row['engine']:row['status'] for row in result.get('stages',[])}
        self.platform_bits.setText((statuses.get(name,'') if name else result['status'])+
            ' · '+str(len(statuses))+' engines · '+str(result.get('milliseconds','—'))+' ms\nBinary: '+''.join(map(str,result.get('binary',[])))+
            '\nBalanced ternary: '+' '.join({-1:'−',0:'0',1:'+'}[x] for x in result.get('balanced_ternary',[])))

    def render_platform_alignment(self):
        state=self.platform_alignment.snapshot();latest=state['latest']
        status='Processing' if state['active_job'] else 'Paused' if not state['enabled'] else 'Running' if state['running'] else 'Ready'
        self.platform_status.setText(state['error'] or status+' · '+str(latest.get('status') or 'waiting for inputs'))
        if self.pages.currentIndex()!=22:return
        if time.monotonic()-self.platform_refresh>=2:
            self.platform_refresh=time.monotonic();rows=self.platform_alignment.history()
            if rows!=self.platform_rows:
                selected=self.platform_sessions.currentData();self.platform_sessions.blockSignals(True)
                self.platform_sessions.clear();self.platform_sessions.addItem('Latest result',None)
                for row in rows:self.platform_sessions.addItem(row['status']+' · '+row['source']+' · '+row['job_id'][:8],row['job_id'])
                index=self.platform_sessions.findData(selected)
                if selected and index<0:self.platform_sessions.addItem('Selected · '+selected[:8],selected);index=self.platform_sessions.count()-1
                self.platform_sessions.setCurrentIndex(max(0,index));self.platform_sessions.blockSignals(False);self.platform_rows=rows
        if self.platform_pending and self.platform_alignment.ready(self.platform_pending):
            job=self.platform_pending;self.platform_pending=None;index=self.platform_sessions.findData(job)
            if index<0:self.platform_sessions.addItem('Requested · '+job[:8],job);index=self.platform_sessions.count()-1
            self.platform_sessions.setCurrentIndex(index);self.platform_input_status.setText('Saved · '+job)
        job=self.platform_sessions.currentData() or latest.get('job_id')
        if job!=self.platform_rendered:self.show_platform_result()
