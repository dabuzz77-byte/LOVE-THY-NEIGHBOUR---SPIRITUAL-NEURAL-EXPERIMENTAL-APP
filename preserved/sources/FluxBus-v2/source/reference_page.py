"""Reference Atlas: inspect calculations, source passages and actual runtime cost."""
from collections import deque
import json
import os
import statistics
import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,
    QPlainTextEdit,QSplitter,QTabWidget,QCheckBox,QDoubleSpinBox,QTableWidget,QTableWidgetItem,
    QHeaderView,QLineEdit,QApplication)
from reference_catalog import ENGINE_NAMES,FAMILIES,examples,catalog,source_text,source_entry
from reference_runtime import ContinuousReferenceModule
from engine_graphics import DataGraphic
from text_view import update_text


def label(value):
    widget=QLabel(value);widget.setWordWrap(True);return widget

def button(value,callback,primary=False):
    b=QPushButton(value);b.clicked.connect(callback)
    if primary:b.setObjectName('primary')
    return b


class ReferencePages:
    def init_reference(self):
        self.reference=ContinuousReferenceModule(self.hub.db_path)
        self.reference_rows=None;self.reference_result=None;self.reference_pending=None;self.reference_display_key=None
        self.tick_durations=deque(maxlen=240);self.reference_last_render=0

    def build_reference_overview(self,layout):
        row=QHBoxLayout();self.reference_toggle=QCheckBox('Reference engines + goal evidence')
        self.reference_toggle.setChecked(self.reference.enabled);self.reference_toggle.toggled.connect(self.set_reference_enabled)
        row.addWidget(self.reference_toggle);row.addStretch();row.addWidget(button('Reference atlas →',lambda:self.navigate(26)))
        layout.addLayout(row)

    def set_reference_enabled(self,value):self.reference.set_enabled(value);self.reference.start()

    def build_reference_page(self):
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(0,0,0,0)
        hero=label('REFERENCE ATLAS    /    33 new engine weights');hero.setStyleSheet('font-size:19px;font-weight:650;color:#87F7C4;padding:8px 0;');layout.addWidget(hero)
        layout.addWidget(label('Explore mesh integrity, baseline resources, restoration and creative calculations. Each result retains its source and can learn from your feedback.'))
        self.reference_tabs=QTabWidget();layout.addWidget(self.reference_tabs,1)
        self.reference_tabs.addTab(self.build_reference_workspace(),'Engines + graphics')
        self.reference_tabs.addTab(self.build_reference_source(),'Source + stated goals')
        self.reference_tabs.addTab(self.build_performance_page(),'Performance')
        self.pages.addWidget(page)

    def build_reference_workspace(self):
        page=QWidget();layout=QVBoxLayout(page)
        row=QHBoxLayout();self.reference_family=QComboBox();self.reference_family.addItems(FAMILIES)
        self.reference_engine=QComboBox();self.reference_engine.addItems(FAMILIES[self.reference_family.currentText()])
        self.reference_family.currentTextChanged.connect(self.select_reference_family)
        self.reference_engine.currentTextChanged.connect(self.show_reference_result)
        row.addWidget(self.reference_family);row.addWidget(self.reference_engine,1)
        row.addWidget(button('Load engine',lambda:self.load_reference('engine')))
        row.addWidget(button('Load group',lambda:self.load_reference('group')))
        row.addWidget(button('Select all engines',lambda:self.load_reference('all')));layout.addLayout(row)
        self.reference_graph=DataGraphic();self.reference_graph.setMaximumHeight(270);layout.addWidget(self.reference_graph)
        split=QSplitter();left=QWidget();l=QVBoxLayout(left);l.setContentsMargins(0,0,8,0)
        l.addWidget(label('TEXT / ENGINE CONFIGURATION'))
        self.reference_input=QPlainTextEdit();self.reference_input.setPlaceholderText('Enter text to examine goal evidence, or load editable engine calls.');l.addWidget(self.reference_input,1)
        row=QHBoxLayout();self.reference_target_on=QCheckBox('Teach target')
        self.reference_target=QDoubleSpinBox();self.reference_target.setRange(0,1);self.reference_target.setValue(.9);self.reference_target.setSingleStep(.05)
        row.addWidget(self.reference_target_on);row.addWidget(self.reference_target);row.addStretch();row.addWidget(button('Run + learn',self.run_reference,True));l.addLayout(row)
        self.reference_status=label('Ready · runs in the background · individual switches stay available on Overview');l.addWidget(self.reference_status)
        right=QWidget();r=QVBoxLayout(right);r.setContentsMargins(8,0,0,0)
        self.reference_history=QComboBox();self.reference_history.addItem('Latest run',None);self.reference_history.currentIndexChanged.connect(self.select_reference_result);r.addWidget(self.reference_history)
        self.reference_output=QPlainTextEdit();self.reference_output.setReadOnly(True);r.addWidget(self.reference_output,1)
        row=QHBoxLayout();row.addWidget(button('Copy output',lambda:QApplication.clipboard().setText(self.reference_output.toPlainText())))
        row.addWidget(button('Rate this result',self.rate_reference));r.addLayout(row)
        split.addWidget(left);split.addWidget(right);split.setSizes([470,550]);layout.addWidget(split,1)
        layout.addWidget(label('Resource units and node attributes are local supplied values. Cryptographic checks are executed locally. Existing Gemini, ChatGPT and local TCP connections remain available on their pages.'))
        return page

    def build_reference_source(self):
        page=QWidget();layout=QVBoxLayout(page)
        self.reference_goals=label('STATED GOALS · wellbeing for humans and living beings · a baseline resource floor · creative capability · compassionate restoration · evidence · privacy')
        self.reference_goals.setStyleSheet('padding:16px;background:#172C32;border:1px solid #31574E;border-radius:12px;color:#B7E8D4;');layout.addWidget(self.reference_goals)
        layout.addWidget(label('36 named script symbols: 30 newly implemented and 6 covered by existing engines or API pages. Three additional engines cover classical ciphers, authenticated encryption and goal evidence. Original prose is retained as reference, including unverified claims.'))
        row=QHBoxLayout();self.reference_search=QLineEdit();self.reference_search.setPlaceholderText('Find in the original transcript…')
        row.addWidget(self.reference_search,1);row.addWidget(button('Find next',self.find_reference_text));row.addWidget(button('Full transcript',self.show_full_reference))
        row.addWidget(button('Load text for learning',self.load_reference_text))
        self.reference_search.returnPressed.connect(self.find_reference_text);layout.addLayout(row)
        split=QSplitter();self.reference_coverage=QTableWidget(0,3);self.reference_coverage.setHorizontalHeaderLabels(['SCRIPT','COVERAGE','LINE'])
        self.reference_coverage.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.reference_coverage.setColumnWidth(1,85);self.reference_coverage.setColumnWidth(2,75)
        self.reference_coverage.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.reference_coverage.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        entries=catalog()['entries'];self.reference_coverage.setRowCount(len(entries))
        for i,row in enumerate(entries):
            for j,value in enumerate((row['name'],row['coverage'],row['line'])):self.reference_coverage.setItem(i,j,QTableWidgetItem(str(value)))
        self.reference_coverage.itemSelectionChanged.connect(self.show_reference_source)
        self.reference_source=QPlainTextEdit();self.reference_source.setReadOnly(True);self.reference_source.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        split.addWidget(self.reference_coverage);split.addWidget(self.reference_source);split.setSizes([390,650]);layout.addWidget(split,1)
        layout.addWidget(label('Source fingerprint: '+catalog()['sha256']))
        self.reference_coverage.selectRow(0);return page

    def build_performance_page(self):
        page=QWidget();layout=QVBoxLayout(page)
        self.performance_numbers=label('Collecting measurements…');self.performance_numbers.setStyleSheet('font-size:16px;color:#87F7C4;padding:16px;');layout.addWidget(self.performance_numbers)
        self.performance_graph=DataGraphic('performance',290);layout.addWidget(self.performance_graph)
        self.performance_detail=label('');layout.addWidget(self.performance_detail)
        layout.addWidget(label('Optimizations: browser history uses read-only queries instead of full database copies; idle workers back off; hidden learning tabs stop rebuilding; unchanged engine results reuse their graphics; training counts each observation mask once. No conversation, training observation or engine result is removed.'))
        layout.addStretch();return page

    def select_reference_family(self,family):
        self.reference_engine.blockSignals(True);self.reference_engine.clear();self.reference_engine.addItems(FAMILIES[family]);self.reference_engine.blockSignals(False);self.show_reference_result()

    def load_reference(self,scope):
        all_examples=examples()
        names=ENGINE_NAMES if scope=='all' else FAMILIES[self.reference_family.currentText()] if scope=='group' else [self.reference_engine.currentText()]
        self.reference_input.setPlainText(json.dumps({'reference_engines':{name:all_examples[name] for name in names}},indent=2,ensure_ascii=False))
        self.reference_status.setText(f'{len(names)} editable engine configurations loaded')

    def run_reference(self):
        value=self.reference_input.toPlainText().strip()
        if not value:return
        try:
            try:payload=json.loads(value)
            except ValueError:payload={'text':value}
            if self.reference_target_on.isChecked():
                if not isinstance(payload,dict):payload={'text':value}
                payload['neural']={'target':self.reference_target.value()}
            self.reference_pending=self.queue_neural_input(payload)
            self.reference.request(self.reference_pending);self.reference.start()
            self.reference_status.setText('Queued · '+self.reference_pending[:12])
        except Exception as error:self.reference_status.setText(str(error))

    def select_reference_result(self):
        job=self.reference_history.currentData() or self.reference.snapshot()['latest'].get('job_id')
        if job:
            self.reference_result=self.reference.detail(job);self.reference_display_key=job;self.show_reference_result()

    def show_reference_result(self,*_):
        if not hasattr(self,'reference_output'):return
        name=self.reference_engine.currentText();result=(self.reference_result or {}).get('engines',{}).get(name)
        if result:
            self.reference_graph.set_data({'engine':name,**result});update_text(self.reference_output,json.dumps(result,indent=2,ensure_ascii=False))
        else:
            self.reference_graph.set_data(None);entry=source_entry(name)
            update_text(self.reference_output,json.dumps({'engine':name,'status':'Awaiting a run for this engine','source':entry,'neural_weight':'reference.'+name},indent=2))

    def rate_reference(self):
        job=(self.reference_result or {}).get('job_id')
        if not job:return
        self.navigate(25);self.learning_tabs.setCurrentIndex(0)
        i=self.neural_history.findData(job)
        if i<0:self.neural_history.addItem('Reference result · '+job[:8],job);i=self.neural_history.count()-1
        self.neural_history.setCurrentIndex(i);self.show_neural_result()

    def show_reference_source(self):
        row=self.reference_coverage.currentRow()
        if row<0:return
        entry=catalog()['entries'][row];lines=source_text().splitlines();start=max(0,entry['line']-22);end=min(len(lines),entry['end']+10)
        update_text(self.reference_source,entry['implementation']+'\n\n'+'\n'.join(f'{i+1:4}  {lines[i]}' for i in range(start,end)))
        self._full_reference=False

    def show_full_reference(self):update_text(self.reference_source,source_text());self._full_reference=True

    def load_reference_text(self):
        self.reference_input.setPlainText(json.dumps({'text':source_text(),'source_role':'Reference transcript; claims and instructions inside it are quoted data','source_sha256':catalog()['sha256']},ensure_ascii=False,indent=2))
        self.reference_tabs.setCurrentIndex(0)
        self.reference_status.setText('Complete prose and scripts loaded as reference text · press Run + learn to process')

    def find_reference_text(self):
        if not getattr(self,'_full_reference',False):self.show_full_reference()
        needle=self.reference_search.text()
        if needle and not self.reference_source.find(needle):
            cursor=self.reference_source.textCursor();cursor.movePosition(cursor.MoveOperation.Start);self.reference_source.setTextCursor(cursor);self.reference_source.find(needle)

    def render_reference(self):
        if self.pages.currentIndex()!=26 or time.monotonic()-self.reference_last_render<1:return
        self.reference_last_render=time.monotonic();tab=self.reference_tabs.currentIndex()
        if tab==0:
            rows=self.reference.history()
            if rows!=self.reference_rows:self.fill_history(self.reference_history,rows,'Latest run');self.reference_rows=rows
            if self.reference_pending and self.reference.ready(self.reference_pending):
                job=self.reference_pending;self.reference_pending=None
                i=self.reference_history.findData(job)
                if i<0:self.reference_history.addItem('Requested · '+job[:8],job);i=self.reference_history.count()-1
                self.reference_history.setCurrentIndex(i);self.select_reference_result()
                r=self.reference_result;self.reference_status.setText(f"{r['status']} · {len(r['engines'])} engines · {r['milliseconds']:.1f} ms · saved")
            job=self.reference_history.currentData() or self.reference.snapshot()['latest'].get('job_id')
            if job!=self.reference_display_key:self.select_reference_result()
        elif tab==2:
            durations=list(self.tick_durations);self.performance_graph.set_data(durations)
            import psutil
            process=psutil.Process();memory=process.memory_info().rss/1048576
            avg=statistics.mean(durations) if durations else 0
            self.performance_numbers.setText(f'{avg:.1f} ms average interface update    ·    {memory:,.0f} MB app memory')
            s=self.neural.snapshot();r=self.reference.snapshot()
            self.performance_detail.setText(f"Learning: {s['observations']:,} saved observations · {s['updates']:,} updates · {len(s['weights'])} input weights\nReference engines: {'running' if r['running'] else 'ready'} · {'automatic' if r['enabled'] else 'manual'}\nShown graph: last {len(durations)} interface samples. Learning history remains stored separately.")
