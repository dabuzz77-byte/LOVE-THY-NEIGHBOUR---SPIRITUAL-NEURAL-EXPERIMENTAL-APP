"""Independent Overview control and inspectable results for all new engines."""
from copy import deepcopy
import json
import time
import uuid
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication,QCheckBox,QComboBox,QHBoxLayout,QLabel,
    QPlainTextEdit,QPushButton,QSplitter,QVBoxLayout,QWidget,QTabWidget,QScrollArea)
from virtue_text import ContinuousTextModule,ENGINE_NAMES,INPUT_TEMPLATE
from unified_runtime import resolve_result
from text_view import update_text
from binary_layout import PRAYER_TEXT,ORIGINAL_LAYOUT,flip_binary_layout,ternary_text,BinaryLayoutGrid


class TextPipelinePages:
    def init_virtue_text(self):
        self.virtue_text=ContinuousTextModule(self.hub.db_path)
        self.text_pipeline_rows=[];self.text_pipeline_refresh=0;self.text_pipeline_pending=None
        self.text_pipeline_view=None;self.text_pipeline_rendered=None

    def build_text_pipeline_overview(self,layout):
        row=QHBoxLayout();self.text_pipeline_toggle=QCheckBox('Continuous text pipeline · 5 components')
        self.text_pipeline_toggle.setChecked(self.virtue_text.enabled);self.text_pipeline_toggle.toggled.connect(self.toggle_virtue_text)
        row.addWidget(self.text_pipeline_toggle)
        self.text_pipeline_status=QLabel('Ready');self.text_pipeline_status.setObjectName('muted');row.addWidget(self.text_pipeline_status,1)
        open_page=QPushButton('Inspect text pipeline →');open_page.clicked.connect(lambda:self.navigate(24));row.addWidget(open_page)
        layout.addLayout(row)

    def toggle_virtue_text(self,enabled):
        try:self.virtue_text.set_enabled(enabled);self.virtue_text.start()
        except Exception as error:
            self.text_pipeline_toggle.blockSignals(True);self.text_pipeline_toggle.setChecked(self.virtue_text.enabled);self.text_pipeline_toggle.blockSignals(False)
            self.text_pipeline_status.setText(str(error));return
        self.render_virtue_text()

    def build_text_pipeline_page(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        intro=QLabel('VirtueTextEngine runs all five components. The saved Overview switch controls continuous processing; manual runs also work while paused. '
                     'Inspect each text transformation, copy its output, or generate a flipped binary layout.')
        intro.setWordWrap(True);layout.addWidget(intro)
        top=QHBoxLayout();self.text_pipeline_sessions=QComboBox();self.text_pipeline_sessions.addItem('Latest result',None)
        self.text_pipeline_sessions.currentIndexChanged.connect(self.show_text_pipeline_result);top.addWidget(self.text_pipeline_sessions,1)
        copy=QPushButton('Copy displayed result');self.text_pipeline_copy=copy;copy.clicked.connect(lambda:QApplication.clipboard().setText(self.text_pipeline_output.toPlainText()));top.addWidget(copy)
        layout.addLayout(top)
        split=QSplitter(Qt.Orientation.Horizontal)
        left=QWidget();column=QVBoxLayout(left);column.setContentsMargins(0,0,8,0)
        self.text_pipeline_input=QPlainTextEdit();self.text_pipeline_input.setPlaceholderText('Text, code or JSON. Load the supplied example to choose the three processing levels and preserve whitespace.')
        column.addWidget(self.text_pipeline_input,1)
        template=QPushButton('Supplied examples');template.clicked.connect(self.add_text_pipeline_template)
        run=QPushButton('Run all five components');run.setObjectName('primary');run.clicked.connect(self.run_text_pipeline_input)
        buttons=QHBoxLayout();buttons.addWidget(template);buttons.addWidget(run);column.addLayout(buttons)
        self.text_pipeline_input_status=QLabel('Ready');self.text_pipeline_input_status.setWordWrap(True);column.addWidget(self.text_pipeline_input_status)
        note=QLabel('Each run saves its original input and complete results. No files are generated automatically.');note.setWordWrap(True);note.setObjectName('muted');column.addWidget(note)
        split.addWidget(left)
        right=QWidget();results=QVBoxLayout(right);results.setContentsMargins(8,0,0,0)
        self.text_pipeline_engines=QComboBox();self.text_pipeline_engines.addItem('Processed text · ready to copy','__text__')
        self.text_pipeline_engines.addItem('VirtueTextEngine · complete run',None)
        for i,name in enumerate(ENGINE_NAMES,1):self.text_pipeline_engines.addItem(f'{i:02d}  {name}',name)
        self.text_pipeline_engines.currentIndexChanged.connect(self.display_text_pipeline_selection);results.addWidget(self.text_pipeline_engines)
        self.text_pipeline_bits=QLabel('Binary / balanced ternary: waiting for input');self.text_pipeline_bits.setWordWrap(True);self.text_pipeline_bits.setObjectName('eyebrow');results.addWidget(self.text_pipeline_bits)
        self.text_pipeline_output=QPlainTextEdit();self.text_pipeline_output.setReadOnly(True);results.addWidget(self.text_pipeline_output,1)
        split.addWidget(right);split.setSizes([450,650]);layout.addWidget(split,1);tabs=QTabWidget();tabs.addTab(page,'Text pipeline');tabs.addTab(self.build_binary_workspace(),'Prayer + binary');self.pages.addWidget(tabs)

    def add_text_pipeline_template(self):
        example=deepcopy(INPUT_TEMPLATE)
        example['text']=self.text_pipeline_input.toPlainText() or example['text']
        self.text_pipeline_input.setPlainText(json.dumps(example,indent=2))
        self.text_pipeline_input_status.setText('Supplied example assumptions · edit before running')

    def run_text_pipeline_input(self):
        text=self.text_pipeline_input.toPlainText()
        if not text.strip():self.text_pipeline_input_status.setText('Enter an input first');return
        try:self.queue_text_pipeline_input(text)
        except Exception as error:self.text_pipeline_input_status.setText(str(error))

    def queue_text_pipeline_input(self,payload):
        job=self.pipeline.submit('Text pipeline manual',uuid.uuid4().hex,payload,self.pipeline_context(),force=True)
        self.virtue_text.request(job);self.virtue_text.start();self.text_pipeline_pending=job
        self.text_pipeline_sessions.setCurrentIndex(0);self.text_pipeline_input_status.setText('Queued · '+job)
        return job

    def show_text_pipeline_result(self):
        job=self.text_pipeline_sessions.currentData() or self.virtue_text.snapshot()['latest'].get('job_id')
        if not job:return
        result=self.virtue_text.detail(job)
        if result:
            self.text_pipeline_view=result;self.text_pipeline_rendered=job;self.display_text_pipeline_selection()

    def display_text_pipeline_selection(self):
        result=self.text_pipeline_view
        if not result:return
        name=self.text_pipeline_engines.currentData()
        selected=resolve_result(result,name) if name and name in result.get('engines',{}) else result
        if name=='__text__':
            update_text(self.text_pipeline_output,result.get('engines',{}).get('VirtueGatedMeshEngine',{}).get('output',result.get('error','')))
        else:
            update_text(self.text_pipeline_output,json.dumps(selected,indent=2,ensure_ascii=False))
        statuses={row['engine']:row['status'] for row in result.get('stages',[])}
        self.text_pipeline_bits.setText((statuses.get(name,'') if name else result['status'])+
            ' · '+str(len(statuses))+' engines · '+str(result.get('milliseconds','—'))+' ms\nBinary: '+''.join(map(str,result.get('binary',[])))+
            '\nBalanced ternary: '+' '.join({-1:'−',0:'0',1:'+'}[x] for x in result.get('balanced_ternary',[])))

    def render_virtue_text(self):
        state=self.virtue_text.snapshot();latest=state['latest']
        status='Processing' if state['active_job'] else 'Paused' if not state['enabled'] else 'Running' if state['running'] else 'Ready'
        self.text_pipeline_status.setText(state['error'] or status+' · '+str(latest.get('status') or 'waiting for inputs'))
        if self.pages.currentIndex()!=24:return
        if time.monotonic()-self.text_pipeline_refresh>=2:
            self.text_pipeline_refresh=time.monotonic();rows=self.virtue_text.history()
            if rows!=self.text_pipeline_rows:
                selected=self.text_pipeline_sessions.currentData();self.text_pipeline_sessions.blockSignals(True)
                self.text_pipeline_sessions.clear();self.text_pipeline_sessions.addItem('Latest result',None)
                for row in rows:self.text_pipeline_sessions.addItem(row['status']+' · '+row['source']+' · '+row['job_id'][:8],row['job_id'])
                index=self.text_pipeline_sessions.findData(selected)
                if selected and index<0:self.text_pipeline_sessions.addItem('Selected · '+selected[:8],selected);index=self.text_pipeline_sessions.count()-1
                self.text_pipeline_sessions.setCurrentIndex(max(0,index));self.text_pipeline_sessions.blockSignals(False);self.text_pipeline_rows=rows
        if self.text_pipeline_pending and self.virtue_text.ready(self.text_pipeline_pending):
            job=self.text_pipeline_pending;self.text_pipeline_pending=None;index=self.text_pipeline_sessions.findData(job)
            if index<0:self.text_pipeline_sessions.addItem('Requested · '+job[:8],job);index=self.text_pipeline_sessions.count()-1
            self.text_pipeline_sessions.setCurrentIndex(index);self.text_pipeline_input_status.setText('Saved · '+job)
        job=self.text_pipeline_sessions.currentData() or latest.get('job_id')
        if job!=self.text_pipeline_rendered:self.show_text_pipeline_result()

    def build_binary_workspace(self):
        page=QWidget();layout=QHBoxLayout(page)
        prayer_scroll=QScrollArea();prayer_scroll.setWidgetResizable(True);prayer_scroll.setMaximumWidth(290)
        prayer=QLabel(PRAYER_TEXT);prayer.setWordWrap(True)
        font=prayer.font();font.setItalic(True);prayer.setFont(font)
        prayer.setContentsMargins(16,20,16,20);prayer.setAlignment(Qt.AlignmentFlag.AlignTop)
        prayer_scroll.setWidget(prayer);layout.addWidget(prayer_scroll)
        right=QWidget();col=QVBoxLayout(right)
        description=QLabel('Generate flips 0 ↔ 1 while retaining spacing and line breaks. Balanced ternary gives the exact value of the resulting bits: −1, 0, +1.')
        description.setWordWrap(True);col.addWidget(description)
        editors=QSplitter()
        self.binary_input=QPlainTextEdit();self.binary_input.setPlaceholderText('Paste a binary layout…')
        self.binary_input.setPlainText(self.store.setting('binary_layout_input',ORIGINAL_LAYOUT))
        self.binary_output=QPlainTextEdit();self.binary_output.setReadOnly(True)
        for editor in (self.binary_input,self.binary_output):
            editor.setFont(QFont('Consolas',10))
            editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editors.addWidget(self.binary_input);editors.addWidget(self.binary_output);col.addWidget(editors,2)
        row=QHBoxLayout()
        generate=QPushButton('Generate · flip 0 ↔ 1');generate.setObjectName('primary');generate.clicked.connect(self.generate_binary_layout);row.addWidget(generate)
        copy=QPushButton('Copy flipped layout');copy.clicked.connect(lambda:QApplication.clipboard().setText(self.binary_output.toPlainText()));row.addWidget(copy)
        restore=QPushButton('Original layout');restore.clicked.connect(lambda:self.binary_input.setPlainText(ORIGINAL_LAYOUT));row.addWidget(restore)
        col.addLayout(row)
        self.binary_grid=BinaryLayoutGrid();col.addWidget(self.binary_grid,1)
        self.binary_ternary=QPlainTextEdit();self.binary_ternary.setReadOnly(True);self.binary_ternary.setMaximumHeight(155);col.addWidget(self.binary_ternary)
        copy=QPushButton('Copy balanced ternary');copy.clicked.connect(lambda:QApplication.clipboard().setText(self.binary_ternary.toPlainText()));col.addWidget(copy)
        self.binary_status=QLabel('Ready');self.binary_status.setWordWrap(True);col.addWidget(self.binary_status)
        layout.addWidget(right,1)
        self.show_binary_layout(flip_binary_layout(self.binary_input.toPlainText()))
        return page

    def show_binary_layout(self,result):
        update_text(self.binary_output,result['flipped'])
        self.binary_grid.set_layout(result['flipped'])
        lines=['Whole layout: '+ternary_text(result['balanced_ternary'])]
        lines += ['Line '+str(row['line'])+': '+ternary_text(row['balanced_ternary']) for row in result['rows']]
        update_text(self.binary_ternary,'\n'.join(lines))
        self.binary_status.setText(str(result['bit_count'])+' bits · green = 1 · blue = 0')

    def generate_binary_layout(self):
        text=self.binary_input.toPlainText()
        try:
            result=flip_binary_layout(text);self.show_binary_layout(result)
            self.store.set_setting('binary_layout_input',text)
            self.queue_text_pipeline_input({'text':text,'binary_layout':text,
                'text_pipeline':{'levels':{'1':False,'2':False,'3':False},'preserve_layout':True}})
            self.binary_status.setText(str(result['bit_count'])+' bits flipped · complete result queued for saved history')
        except Exception as error:self.binary_status.setText(str(error))
