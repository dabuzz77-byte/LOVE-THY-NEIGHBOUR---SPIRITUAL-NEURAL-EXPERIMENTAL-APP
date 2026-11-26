"""Flux Bus — standalone native Windows telemetry and Boolean exploration studio."""
import argparse
import csv
import html
import json
import os
from pathlib import Path
import queue
import sys
import threading
import time

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QKeySequence, QShortcut, QPixmap, QPainter, QPen, QFontDatabase, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QStackedWidget, QFrame, QComboBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QPlainTextEdit,
    QTextBrowser, QCheckBox, QDoubleSpinBox, QScrollArea, QFileDialog, QMessageBox,
    QDialog, QListWidget, QListWidgetItem, QFormLayout)

from monitor import SystemBusMonitor, FAMILIES
from routing import Trajectory, run_model, DECLARED_LEDGER, flux_record
from visuals import Panel, MetricCard, BusCanvas, RouteCanvas, FluxGrid, Sparkline, COLORS, MINT, MUTED
from library import LibraryStore, LibrarySync, LICENSE_URL
import llama
from extensions import StudioExtensions
from text_view import update_text

STYLE = """
QWidget { background:#090C12; color:#ECF3F8; font-family:'Inter'; font-size:13px; }
QFrame#sidebar { background:#0D121A; border-right:1px solid #202A36; }
QFrame#panel { background:#111720; border:1px solid #25303D; border-radius:12px; }
QLabel { background:transparent; }
QLabel#muted { color:#8A9AAB; font-size:12px; }
QLabel#eyebrow { color:#8A9AAB; font-size:10px; font-weight:600; letter-spacing:2px; }
QLabel#title { font-size:27px; font-weight:600; }
QPushButton { background:#18212D; border:1px solid #2A3746; border-radius:7px; padding:9px 14px; font-weight:500; }
QPushButton:hover { background:#243345; border-color:#5E7B92; }
QPushButton:pressed { background:#314357; }
QPushButton:disabled { color:#647185; border-color:#202A35; }
QPushButton#primary { background:#87F7C4; color:#092018; border-color:#87F7C4; font-weight:700; }
QPushButton#primary:hover { background:#B6FFDB; }
QPushButton#nav { text-align:left; padding:12px 14px; border:none; background:transparent; color:#9CACBE; }
QPushButton#nav:checked { background:#1B302C; color:#A9FFD4; }
QPushButton#nav:hover { background:#19232F; color:#ECF3F8; }
QLineEdit, QComboBox, QDoubleSpinBox { background:#0D131C; border:1px solid #2D3B4C; border-radius:6px; padding:8px 10px; min-height:18px; }
QLineEdit:focus, QPlainTextEdit:focus { border-color:#87F7C4; }
QComboBox QAbstractItemView { background:#15202B; selection-background-color:#29443C; }
QPlainTextEdit, QTextBrowser { background:#0D131C; border:1px solid #25303D; border-radius:8px; padding:12px; selection-background-color:#356454; }
QTableWidget { background:#101720; alternate-background-color:#121C27; border:0; gridline-color:#1E2A37; selection-background-color:#253D43; }
QTableWidget::item { padding:7px 10px; border-bottom:1px solid #1D2835; }
QTableWidget::item:selected { background:#223D43; color:#FFFFFF; }
QHeaderView::section { background:#151F2B; color:#93A4B7; border:0; padding:10px; text-align:left; font-size:10px; font-weight:600; }
QTableCornerButton::section { background:#151F2B; border:0; }
QScrollBar:vertical { background:#0D131C; width:8px; margin:0; }
QScrollBar::handle:vertical { background:#354558; border-radius:4px; min-height:24px; }
QScrollBar:horizontal { background:#0D131C; height:8px; }
QScrollBar::handle:horizontal { background:#354558; border-radius:4px; }
QScrollBar::add-line, QScrollBar::sub-line { height:0;width:0; }
QScrollBar::add-page, QScrollBar::sub-page { background:none; }
QListWidget { background:#111720; border:1px solid #25303D; border-radius:8px; padding:8px; outline:0; }
QListWidget::item { padding:12px; border-radius:5px; }
QListWidget::item:selected { background:#223F39; color:#B9FFDC; }
QCheckBox { spacing:8px; background:transparent; }
QCheckBox::indicator { width:16px; height:16px; border:1px solid #4A5E70; border-radius:4px; background:#101720; }
QCheckBox::indicator:checked { background:#87F7C4; border-color:#87F7C4; }
QSplitter::handle { background:#090C12; }
QToolTip { background:#233141; color:#ECF3F8; border:1px solid #4A5E70; padding:6px; }
QScrollArea { border:0; background:transparent; }
"""


def label(text, kind=None, wrap=False):
    item = QLabel(text)
    if kind:
        item.setObjectName(kind)
    item.setWordWrap(wrap)
    return item


def button(text, callback, primary=False):
    item = QPushButton(text)
    if primary:
        item.setObjectName("primary")
    item.clicked.connect(callback)
    return item


def combo(values, current=0):
    item = QComboBox()
    item.addItems(values)
    item.setCurrentIndex(current)
    return item


def layout_panel(title=None):
    panel = Panel()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(20, 17, 20, 17)
    layout.setSpacing(12)
    if title:
        layout.addWidget(label(title, "eyebrow"))
    return panel, layout


def size_text(value):
    if value is None:
        return "—"
    if value >= 1073741824:
        return f"{value/1073741824:.2f} GB"
    return f"{value/1048576:.1f} MB"


class NumberItem(QTableWidgetItem):
    def __init__(self, text, value):
        super().__init__(str(text))
        self.value = value if value is not None else -1

    def __lt__(self, other):
        return self.value < other.value if isinstance(other, NumberItem) else super().__lt__(other)


class ProcessTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 7, parent)
        self.setHorizontalHeaderLabels(["PROCESS", "PID", "CHANNEL", "CPU %", "MEMORY", "STATE", "SCRIPT / ROLE"])
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(38)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for i, width in enumerate((170, 75, 90, 82, 100, 100, 280)):
            self.setColumnWidth(i, width)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.setSortingEnabled(True)
        self.sortItems(2, Qt.SortOrder.AscendingOrder)
        self.cellDoubleClicked.connect(self.details)

    def populate(self, rows):
        old = self.item(self.currentRow(), 0)
        identity = old.data(Qt.ItemDataRole.UserRole)["pid"] if old else None
        scroll = self.verticalScrollBar().value()
        self.setSortingEnabled(False)
        self.setRowCount(len(rows))
        for r, row in enumerate(rows):
            cpu = "—" if row["cpu"] is None else f"{row['cpu']:.1f}"
            items = [QTableWidgetItem(row["name"]), NumberItem(row["pid"], row["pid"]),
                     QTableWidgetItem(row["family"].capitalize()), NumberItem(cpu, row["cpu"]),
                     NumberItem(size_text(row["memory"]), row["memory"]),
                     QTableWidgetItem("partial" if row["partial"] else row["status"]), QTableWidgetItem(row["entry"])]
            items[0].setData(Qt.ItemDataRole.UserRole, row)
            items[2].setForeground(QColor(COLORS[row["family"]]))
            for c, item in enumerate(items):
                item.setToolTip(row["entry"] if c == 6 else item.text())
                self.setItem(r, c, item)
        self.setSortingEnabled(True)
        for r in range(self.rowCount()):
            if self.item(r, 0).data(Qt.ItemDataRole.UserRole)["pid"] == identity:
                self.selectRow(r)
                break
        self.verticalScrollBar().setValue(scroll)

    def details(self, row, column):
        item = self.item(row, 0)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Process {data['pid']} · {data['name']}")
        dialog.resize(760, 490)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label(data["name"], "title"))
        layout.addWidget(label("CPU is shown as a share of the whole machine. A dash means not yet measured or unavailable.", "muted", True))
        text = QPlainTextEdit(json.dumps(data, indent=2, ensure_ascii=False))
        text.setReadOnly(True)
        layout.addWidget(text)
        layout.addWidget(button("Close", dialog.accept))
        dialog.exec()


class GraphicalVirtueMatrixEngine(StudioExtensions, QMainWindow):
    def __init__(self, bus_monitor, data_dir, start_services=True):
        super().__init__()
        self.bus_monitor = bus_monitor
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = LibraryStore(self.data_dir / "library.sqlite3")
        self.library_sync = LibrarySync(self.store)
        self.events_queue = queue.Queue()
        self.snapshot = bus_monitor.get_snapshot()
        self.last_sequence = -1
        self.paused = False
        self.global_virtue_state = "PASS"
        self.route = run_model()
        self.init_extensions()
        self.trace = []
        self.llama_busy = False
        self.last_auto = 0
        self.last_library_revision = -1
        self.pages = QStackedWidget()
        self.setWindowTitle("Flux Bus v2 — Live System & Logic Studio")
        self.resize(1440, 960)
        self.setMinimumSize(1100, 740)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(make_icon())
        self.build_ui()
        self.apply_route("Engine initialized")
        self.load_library()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(250)
        self.shortcuts = []
        for keys, callback in (("Ctrl+F", self.focus_search), ("Ctrl+S", self.export_snapshot),
                               ("Ctrl+R", self.bus_monitor.refresh), ("F11", self.toggle_fullscreen)):
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)
        if start_services:
            self.bus_monitor.start()
            self.library_sync.start()
            self.connect_llama()
            self.start_extensions()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(188)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 24, 16, 20)
        brand = label("FLUX BUS")
        brand.setStyleSheet("font-size:20px;font-weight:700;color:#B2FFD7;background:transparent")
        side.addWidget(brand)
        side.addWidget(label("LIVE TELEMETRY", "eyebrow"))
        side.addSpacing(18)
        side.addWidget(label("WORKSPACE", "eyebrow"))
        self.nav = []
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll = nav_scroll
        nav_page = QWidget()
        nav_layout = QVBoxLayout(nav_page)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)
        for i, title in enumerate(("Overview", "Processes", "Logic studio", "Flux grid", "Definitions", "Llama guide", "Event ledger", "Deep audit", "Engines", "Local hub", "History", "Observatory link", "Logic summary", "Live flux + input", "Google AI Mode", "Full pipeline", "Gemini", "ChatGPT / API", "Continuous audit", "Text inverter", "Mesh + bridge", "Unified core", "Platform alignment", "Karmic + welfare", "Text pipeline", "Learning + research", "Reference atlas")):
            nav = button(title, lambda checked=False, index=i: self.navigate(index))
            nav.setIcon(nav_icon(i))
            nav.setObjectName("nav")
            nav.setCheckable(True)
            nav.setChecked(i == 0)
            nav_layout.addWidget(nav)
            self.nav.append(nav)
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_page)
        side.addWidget(nav_scroll, 1)
        side.addWidget(label("MODEL STATE", "eyebrow"))
        self.virtue_button = button("●  VIRTUE: PASS", self.toggle_virtue)
        side.addWidget(self.virtue_button)
        self.sidebar_counts = label("PY  —    JV  —    OP  —", "muted")
        side.addWidget(self.sidebar_counts)
        side.addSpacing(18)
        side.addWidget(label("Native desktop · v2.0\nTelemetry + local intelligence", "muted", True))
        outer.addWidget(sidebar)
        main = QVBoxLayout()
        main.setContentsMargins(26, 22, 26, 12)
        main.setSpacing(18)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.page_title = label("System overview", "title")
        self.page_subtitle = label("Your running processes, connected in one live view.", "muted")
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        header.addLayout(titles)
        header.addStretch()
        self.status_badge = label("● CONNECTING")
        self.status_badge.setStyleSheet("color:#87F7C4;font-size:11px;font-weight:600")
        header.addWidget(self.status_badge)
        self.pause_button = button("Pause view", self.toggle_pause)
        header.addWidget(self.pause_button)
        header.addWidget(button("Export snapshot ↗", self.export_snapshot))
        main.addLayout(header)
        self.build_overview()
        self.build_processes()
        self.build_routing()
        self.build_flux()
        self.build_library()
        self.build_llama()
        self.build_ledger()
        self.build_extensions()
        main.addWidget(self.pages, 1)
        footer = QHBoxLayout()
        self.footer = label("Waiting for first live sample…", "muted")
        footer.addWidget(self.footer)
        footer.addStretch()
        footer.addWidget(label("CTRL+F  Search    CTRL+S  Export    F11  Focus", "muted"))
        main.addLayout(footer)
        outer.addLayout(main, 1)

    def build_overview(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        cards = QHBoxLayout()
        cards.setSpacing(14)
        self.cards = {}
        for family, title in (("python", "PYTHON / .py"), ("java", "JAVA / .java"), ("opera", "OPERA / BROWSER"), ("cpu", "HOST / CPU")):
            card = MetricCard(title, "active processes" if family != "cpu" else "whole machine", COLORS.get(family, MINT))
            self.cards[family] = card
            cards.addWidget(card)
        layout.addLayout(cards)
        self.build_audit_overview(layout)
        self.build_mesh_overview(layout)
        self.build_unified_overview(layout)
        self.build_platform_overview(layout)
        self.build_welfare_overview(layout)
        self.build_text_pipeline_overview(layout)
        self.build_neural_overview(layout)
        self.build_reference_overview(layout)
        split = QSplitter(Qt.Orientation.Vertical)
        split.setChildrenCollapsible(False)
        upper = QWidget()
        upper.setMinimumHeight(390)
        row = QHBoxLayout(upper)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(15)
        canvas_panel = Panel()
        canvas_layout = QVBoxLayout(canvas_panel)
        canvas_layout.setContentsMargins(1, 1, 1, 1)
        self.canvas = BusCanvas()
        canvas_layout.addWidget(self.canvas)
        row.addWidget(canvas_panel, 1)
        core, core_layout = layout_panel("CORE RESOLUTION")
        core.setFixedWidth(242)
        self.core_mode = label("PASS / CORRECTIVE")
        self.core_mode.setStyleSheet("font-size:18px;color:#87F7C4;font-weight:600")
        core_layout.addWidget(self.core_mode)
        core_layout.addWidget(label("Boolean output", "muted"))
        self.output_bits = label("[ true, false ]")
        self.output_bits.setStyleSheet("font-family:'IBM Plex Mono';font-size:18px;color:#E9F6F1")
        core_layout.addWidget(self.output_bits)
        self.core_description = label("Good holds. Evil corrects.\nEvery transition keeps its input.", "muted", True)
        core_layout.addWidget(self.core_description)
        core_layout.addSpacing(8)
        core_layout.addWidget(label("MEMORY PRESSURE", "eyebrow"))
        self.memory_label = label("—")
        core_layout.addWidget(self.memory_label)
        self.memory_chart = Sparkline("#B7A1FF", 42)
        self.memory_chart.setMaximumHeight(50)
        core_layout.addWidget(self.memory_chart)
        core_layout.addStretch()
        core_layout.addWidget(button("Open logic studio  →", lambda: self.navigate(2)))
        row.addWidget(core)
        split.addWidget(upper)
        lower, low = layout_panel()
        lower.setMinimumHeight(210)
        bar = QHBoxLayout()
        bar.addWidget(label("LIVE PROCESS FEED", "eyebrow"))
        bar.addStretch()
        bar.addWidget(button("View all  →", lambda: self.navigate(1)))
        low.addLayout(bar)
        self.preview_table = ProcessTable()
        self.preview_table.setMinimumHeight(125)
        low.addWidget(self.preview_table, 1)
        split.addWidget(lower)
        split.setSizes([390, 230])
        layout.addWidget(split, 1)
        page.setMinimumHeight(1250)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.pages.addWidget(scroll)

    def build_processes(self):
        page, layout = layout_panel()
        from engine_graphics import DataGraphic
        self.process_graph=DataGraphic('processes',126);self.process_graph.setMaximumHeight(132);layout.addWidget(self.process_graph)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name, PID, script, module or executable…")
        self.search.textChanged.connect(self.filter_processes)
        self.family_filter = combo(["All channels", "Python", "Java", "Opera"])
        self.family_filter.currentIndexChanged.connect(self.filter_processes)
        self.rate = combo(["0.5 s", "1.5 s", "3 s", "5 s"], 1)
        self.rate.currentTextChanged.connect(lambda value: self.bus_monitor.set_interval(float(value.split()[0])))
        bar.addWidget(self.search, 1)
        bar.addWidget(self.family_filter)
        bar.addWidget(label("Refresh", "muted"))
        bar.addWidget(self.rate)
        bar.addWidget(button("Scan now", self.bus_monitor.refresh))
        layout.addLayout(bar)
        self.process_count = label("Waiting for processes…", "muted")
        layout.addWidget(self.process_count)
        self.process_table = ProcessTable()
        layout.addWidget(self.process_table, 1)
        layout.addWidget(label("APP COMMAND + EXECUTION ACTIVITY", "eyebrow"))
        self.activity_text = QPlainTextEdit()
        self.activity_text.setReadOnly(True)
        self.activity_text.setMaximumHeight(150)
        layout.addWidget(self.activity_text)
        layout.addWidget(label("Includes visible runtime processes and their descendants. Double-click for full details. CPU % is a share of the whole machine.", "muted", True))
        self.pages.addWidget(page)

    def build_routing(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        top = QHBoxLayout()
        nodes, n = layout_panel("01 / ARRAY ROUTING")
        form = QGridLayout()
        self.bit_controls, self.node_controls = [], []
        for i in range(2):
            bit = combo(["false / 0", "true / 1"], i)
            state = combo(["registered good", "registered evil"], i)
            self.bit_controls.append(bit)
            self.node_controls.append(state)
            form.addWidget(label(f"{i}array"), i, 0)
            form.addWidget(bit, i, 1)
            form.addWidget(state, i, 2)
        self.bridge = combo(["false / 0", "true / 1"])
        form.addWidget(label("Bridge bit"), 2, 0)
        form.addWidget(self.bridge, 2, 1)
        self.first_effect = combo(["evil", "good"])
        form.addWidget(label("First shift effect"), 3, 0)
        form.addWidget(self.first_effect, 3, 1, 1, 2)
        n.addLayout(form)
        n.addWidget(label("PASS and FAIL retain the supplied mapping. Set the evaluated labels on the Deep audit page.", "muted", True))
        n.addWidget(button("Evaluate labels →", lambda: self.navigate(7)))
        top.addWidget(nodes, 1)
        capability, cap = layout_panel("02 / CAPABILITY TRAJECTORY")
        form2 = QFormLayout()
        self.stored_bit = combo(["false / 0", "true / 1"])
        self.cap_state = combo(["evil / correct conflict", "good / preserve state"])
        self.false_is_one = QCheckBox("Encode false as 1")
        self.weight = QDoubleSpinBox()
        self.weight.setRange(0, 1000000)
        self.weight.setDecimals(2)
        self.weight.setValue(1)
        form2.addRow("Stored bit", self.stored_bit)
        form2.addRow("State assessment", self.cap_state)
        form2.addRow("Restriction weight", self.weight)
        form2.addRow("Encoding", self.false_is_one)
        cap.addLayout(form2)
        cap.addWidget(label("Universal CAN is the model premise. A good false CAN stays false; an evil conflicting false CAN is corrected.", "muted", True))
        top.addWidget(capability, 1)
        layout.addLayout(top)
        self.route_canvas = RouteCanvas()
        layout.addWidget(self.route_canvas)
        vectors, vec = layout_panel("03 / INPUT VECTORS")
        self.vectors = QPlainTextEdit()
        self.vectors.setPlaceholderText("Enter cannot claims, one per line, to inspect their model states…")
        self.vectors.setMaximumHeight(95)
        vec.addWidget(self.vectors)
        row = QHBoxLayout()
        row.addWidget(label("Good = preserve · Evil = correct · Original values remain in the trace", "muted"), 1)
        row.addWidget(button("Run cascade  →", lambda: self.apply_route("Manual cascade"), True))
        vec.addLayout(row)
        layout.addWidget(vectors)
        self.route_json = QPlainTextEdit()
        self.route_json.setReadOnly(True)
        self.route_json.setMinimumHeight(220)
        layout.addWidget(self.route_json)
        scroll.setWidget(page)
        self.pages.addWidget(scroll)

    def build_flux(self):
        page, layout = layout_panel()
        layout.addWidget(label("BINARY → BALANCED TERNARY", "eyebrow"))
        layout.addWidget(label("Each row is an actual model evaluation. Both grids encode the same number; powers decrease from left to right.", "muted", True))
        self.flux_grid = FluxGrid()
        self.flux_grid.on_select = self.show_flux_detail
        layout.addWidget(self.flux_grid, 1)
        self.flux_detail = label("Select a step to inspect its reason. Hover a binary cell for its before / after values.", "muted", True)
        layout.addWidget(self.flux_detail)
        layout.addWidget(label("Mint: 0 → 1    Rose: 1 → 0    Blue: held 1    Dim: held 0    Ternary: +1 / 0 / −1", "muted", True))
        names = flux_record(self.route)["names"]
        layout.addWidget(label("Register order: " + " · ".join(names), "muted", True))
        row = QHBoxLayout()
        row.addWidget(button("Run current model", lambda: self.apply_route("Flux grid evaluation")))
        row.addWidget(button("Edit inputs  →", lambda: self.navigate(2)))
        row.addStretch()
        layout.addLayout(row)
        self.pages.addWidget(page)

    def build_library(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.library_search = QLineEdit()
        self.library_search.setPlaceholderText("Search cached definitions…")
        self.library_search.textChanged.connect(self.load_library)
        self.auto_sync = QCheckBox("Refresh every 30 min")
        self.auto_sync.setChecked(self.library_sync.enabled)
        self.auto_sync.toggled.connect(self.library_sync.set_enabled)
        bar.addWidget(self.library_search, 1)
        bar.addWidget(self.auto_sync)
        bar.addWidget(button("Sync now", self.library_sync.sync_now, True))
        layout.addLayout(bar)
        self.library_status = label("Loading local library…", "muted")
        layout.addWidget(self.library_status)
        split = QSplitter()
        self.library_list = QListWidget()
        self.library_list.currentItemChanged.connect(self.show_article)
        self.article_view = QTextBrowser()
        self.article_view.setOpenExternalLinks(True)
        split.addWidget(self.library_list)
        split.addWidget(self.article_view)
        split.setSizes([250, 780])
        layout.addWidget(split, 1)
        add = QHBoxLayout()
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Add a Wikipedia article title to the library…")
        self.topic_input.returnPressed.connect(self.add_topic)
        add.addWidget(self.topic_input, 1)
        add.addWidget(button("Add topic", self.add_topic))
        layout.addLayout(add)
        layout.addWidget(label("Wikipedia reference excerpts · CC BY-SA 4.0 · cached locally · updates while this app is running", "muted"))
        self.pages.addWidget(page)

    def build_llama(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.llama_status = label("Checking local Ollama…", "muted")
        bar.addWidget(self.model_combo)
        bar.addWidget(button("Reconnect", self.connect_llama))
        self.llama_reset=button("Reset conversation",lambda:self.reset_ai_conversation("llama"))
        bar.addWidget(self.llama_reset)
        bar.addWidget(self.llama_status, 1)
        layout.addLayout(bar)
        saved=QHBoxLayout();saved.addWidget(label("Saved conversations","muted"))
        self.llama_sessions=QComboBox();self.llama_sessions.setMinimumContentsLength(20)
        self.llama_sessions.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.llama_sessions.currentIndexChanged.connect(lambda index:self.select_ai_conversation("llama"))
        saved.addWidget(self.llama_sessions,1);layout.addLayout(saved)
        self.guide_output = QTextBrowser()
        self.guide_output.setOpenExternalLinks(True)
        self.guide_output.setHtml("<h2>Your system, in context.</h2><p>Describe an action, ask about your processes, or explore a Boolean state.</p><p>Llama reads a snapshot of this dashboard and the cached definitions. Its answer and cited assessment appear here.</p>")
        from PySide6.QtWidgets import QTabWidget
        tabs=QTabWidget();self.llama_conversation=QPlainTextEdit();self.llama_conversation.setReadOnly(True)
        self.llama_conversation.setPlaceholderText("Messages are remembered until you reset this conversation.")
        tabs.addTab(self.llama_conversation,"Conversation");tabs.addTab(self.guide_output,"Latest assessment")
        layout.addWidget(tabs,1)
        self.llama_memory=label("","muted");layout.addWidget(self.llama_memory)
        self.refresh_conversation("llama")
        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlaceholderText("Describe the action and context, or ask Llama about the system…")
        self.prompt_input.setFixedHeight(110)
        layout.addWidget(self.prompt_input)
        options = QHBoxLayout()
        self.apply_guidance = QCheckBox("Apply supported assessment to model")
        self.apply_guidance.setChecked(True)
        self.auto_guide = QCheckBox("Reassess every 60 seconds")
        self.guide_button = button("Ask Llama  ↗", self.ask_llama, True)
        options.addWidget(self.apply_guidance)
        options.addWidget(self.auto_guide)
        options.addStretch()
        options.addWidget(self.guide_button)
        layout.addLayout(options)
        layout.addWidget(label("Local Ollama · system metrics + definitions · results guide the Boolean model and flux grid", "muted"))
        self.pages.addWidget(page)

    def build_ledger(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("PROCESS EVENTS + MODEL TRACE", "eyebrow"))
        self.event_text = QPlainTextEdit()
        self.event_text.setReadOnly(True)
        layout.addWidget(self.event_text, 1)
        layout.addWidget(label("ORIGINAL DECLARATIONS / MODEL METADATA", "eyebrow"))
        self.declarations = QPlainTextEdit("\n".join(f"{key:30s} : {value}" for key, value in DECLARED_LEDGER.items()))
        self.declarations.setReadOnly(True)
        self.declarations.setMaximumHeight(210)
        layout.addWidget(self.declarations)
        layout.addWidget(label("Declarations are retained as model metadata. The live status above reports measured conditions.", "muted", True))
        self.pages.addWidget(page)

    def navigate(self, index):
        titles = ["System overview", "Process explorer", "Logic studio", "Binary / ternary flux", "Definition library", "Llama guide", "Event ledger", "Deep virtue audit", "Supplied engines", "Local inference hub", "History & grammar", "Observatory connection", "Complete logic summary", "Live flux & command input", "Google AI Mode", "Full engine pipeline", "Gemini", "ChatGPT / OpenAI API", "Continuous substrate & logic audit", "Boolean text inverter", "Local mesh gateway & session bridge", "Unified core / 23 engines", "Platform alignment engine", "Karmic welfare engine", "Text pipeline & binary layout", "Neural learning + automatic research", "Reference atlas + engine graphics"]
        subtitles = ["Your running processes, connected in one live view.",
                     "Python, Java and Opera — including their visible helper processes.",
                     "Good states hold. Evil states correct. Every input stays in the trace.",
                     "Follow the shifts. Translate the value. Inspect each step.",
                     "A living, attributed collection of definitions and ethical viewpoints.",
                     "Read the system. Compare definitions. Guide the model.",
                     "Measured process changes and the full Boolean trajectory.",
                     "Expose mismatched labels. Preserve the original values. Trace the correction.",
                     "Real local execution, with complete before and after records.",
                     "Live TCP messages and committed SQLite node records.",
                     "Continuous URL/title ingestion and imported session text.",
                     "Receive module results, audit their states, return traceable receipts.",
                     "Every module and pathway, summarized in one place.",
                     "Watch all engine bytes change. Enter text or run a command.",
                     "Ingest complete records. Transmit them. Inspect real acknowledgements.",
                     "Every input, every local stage, one persistent receipt.",
                     "Ask Gemini to read the live engine state and respond.",
                     "Ask an OpenAI model to read the live engine state and respond.",
                     "Live host measurements, complete input imprints and supplied resource calculations.",
                     "Paste Boolean statements. Invert their values. Copy the result.",
                     "Redact inputs, calculate the supplied logic and verify local hub delivery.",
                     "Inspect every supplied layer, run it manually and export its infrastructure report.",
                     "Ten components: substrate, convergence, filtering, karmic masks and full base-3 conversion.",
                     "Local node changes, exact karma arithmetic and welfare register snapshots.",
                     "Five text components, saved results and a copyable binary / ternary workspace.",
                     "Learn from engine results, your ratings, system activity and attributed web definitions.",
                     "Trace the supplied scripts, inspect their calculations and measure app performance."]
        self.pages.setCurrentIndex(index)
        self.page_title.setText(titles[index])
        self.page_subtitle.setText(subtitles[index])
        for i, nav in enumerate(self.nav):
            nav.setChecked(i == index)
        self.nav_scroll.ensureWidgetVisible(self.nav[index])
        if hasattr(self,"cloud_controls") and len(self.cloud_controls)==2:
            self.render_extension_pages()
            self.last_extension_tick=0

    def show_flux_detail(self, record):
        evidence = record.get("evidence", {})
        if evidence:
            sources = "; ".join(c["title"] + ": “" + c["quote"] + "”" for c in evidence.get("citations", []))
            self.flux_detail.setText(evidence.get("reason", "") + ("\n" + sources if sources else ""))
        else:
            self.flux_detail.setText(record["label"] + " · Manual model inputs. Hover any binary cell to inspect its original and resulting bit.")
        audit = record.get("deep_audit")
        if audit:
            self.flux_detail.setText(self.flux_detail.text() + "\n" + " · ".join(
                f"Node {d['NODE']}: {d['REGISTER_BEFORE']} → {d['REGISTER_AFTER']} ({int(d['BIT_BEFORE'])} → {int(d['BIT_AFTER'])})" for d in audit["NODES"]))

    def focus_search(self):
        self.navigate(1)
        self.search.setFocus()

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.setText("Resume view" if self.paused else "Pause view")
        self.canvas.pause(self.paused)

    def toggle_virtue(self):
        self.global_virtue_state = "FAIL" if self.global_virtue_state == "PASS" else "PASS"
        self.virtue_button.setText("●  VIRTUE: " + self.global_virtue_state)
        self.apply_route("Virtue mode " + self.global_virtue_state)

    def read_route(self):
        trajectory = Trajectory(stored_bit=bool(self.stored_bit.currentIndex()),
            false_is_one=self.false_is_one.isChecked(), state="evil" if self.cap_state.currentIndex() == 0 else "good",
            restriction_weight=self.weight.value())
        return run_model(bits=tuple(bool(c.currentIndex()) for c in self.bit_controls),
            states=tuple("evil" if c.currentIndex() else "good" for c in self.node_controls),
            virtue=self.global_virtue_state, bridge=bool(self.bridge.currentIndex()),
            trajectory=trajectory, effect=self.first_effect.currentText(), statements=self.vectors.toPlainText(),
            evaluations=tuple(c.currentText() for c in self.evaluation_controls))

    def apply_route(self, note="Model evaluation", guidance=None):
        self.route = self.read_route()
        if guidance:
            self.route["guidance"] = guidance
        self.route_canvas.result = self.route
        self.route_canvas.update()
        bits = self.route["output_boolean_array"]
        self.canvas.bits = bits
        self.canvas.virtue = self.global_virtue_state
        self.canvas.update()
        self.output_bits.setText("[ " + ", ".join(str(b).lower() for b in bits) + " ]")
        self.core_mode.setText(self.global_virtue_state + " / " + ("CORRECT" if self.route["trajectory"]["corrective_shift"] else "HOLD"))
        self.core_mode.setStyleSheet(f"font-size:18px;font-weight:600;color:{MINT if self.global_virtue_state == 'PASS' else '#FF829B'}")
        update_text(self.route_json,json.dumps(self.route, indent=2, ensure_ascii=False))
        record = flux_record(self.route, time.strftime("%H:%M:%S") + " · " + note)
        record["evidence"] = guidance or {}
        record["route"] = self.route
        self.flux_grid.add(record)
        self.show_flux_detail(record)
        self.trace.insert(0, {"time": time.time(), "note": note, "result": self.route})
        self.trace = self.trace[:120]
        self.update_ledger()
        self.update_audit_page()
        self.log_activity("AUDIT",note + " · " + ", ".join(self.route["deep_audit"]["RAISED_FLAGS"]))
        self.observatory.publish("model", {"bits": bits, "audit": self.route["deep_audit"], "source": note})

    def tick(self):
        tick_started=time.perf_counter()
        self.tick_extensions()
        latest = self.bus_monitor.get_snapshot()
        if not self.paused and (latest["sequence"] != self.last_sequence or latest["mode"] != self.snapshot["mode"]):
            self.snapshot = latest
            self.last_sequence = latest["sequence"]
            self.update_metrics()
        self.status_badge.setText("Ⅱ VIEW PAUSED" if self.paused else "● " + self.snapshot["mode"])
        self.status_badge.setStyleSheet("color:" + ("#FFC084" if self.paused or self.snapshot["mode"] != "LIVE" else MINT) + ";font-size:11px;font-weight:600")
        timestamp = self.snapshot.get("timestamp")
        age = max(0, int(time.time() - timestamp)) if timestamp else None
        if timestamp:
            self.footer.setText(f"Sample {time.strftime('%H:%M:%S', time.localtime(timestamp))} · {age}s ago   |   {self.snapshot['scan_ms']:.0f} ms scan   |   {self.snapshot['total_processes']} OS processes   |   {self.snapshot['partial_processes']} partial")
            if self.snapshot.get("error"):
                self.footer.setText("Last sample retained · " + self.snapshot["error"][:130])
        lib = self.library_sync.get_status()
        if lib["revision"] != self.last_library_revision:
            self.last_library_revision = lib["revision"]
            self.library_status.setText(lib["message"])
            self.library_status.setToolTip("\n".join(lib["errors"]))
            self.load_library()
        while True:
            try:
                event, payload = self.events_queue.get_nowait()
            except queue.Empty:
                break
            if event == "models":
                self.model_combo.clear()
                self.model_combo.addItems(payload)
                preferred = next((i for i, name in enumerate(payload) if "llama" in name.lower()), 0)
                self.model_combo.setCurrentIndex(preferred)
                self.llama_status.setText("● Local Ollama connected" if payload else "Connected · no models installed")
            elif event == "connection_error":
                self.llama_status.setText("Ollama unavailable · reconnect after starting it")
                self.llama_status.setToolTip(payload)
            elif event == "guidance":
                self.receive_guidance(payload)
            elif event == "guide_error":
                if payload["token"]!=self.llama_request:continue
                self.llama_request=None
                self.llama_busy = False
                self.guide_button.setEnabled(True)
                self.llama_status.setText("Request failed · model unchanged")
                self.guide_output.setPlainText("Llama could not complete the request.\n\n" + payload["error"])
                self.llama_status.setText("Request failed · conversation retained · "+payload["error"])
        if self.auto_guide.isChecked() and self.prompt_input.toPlainText().strip() and not self.llama_busy and time.time() - self.last_auto >= 60:
            self.ask_llama()
        self.tick_durations.append((time.perf_counter()-tick_started)*1000)

    def update_metrics(self):
        s = self.snapshot
        self.process_graph.set_data(s)
        for family in FAMILIES:
            rows = [p for p in s["processes"] if p["family"] == family]
            memory = sum(p["memory"] or 0 for p in rows)
            self.cards[family].update_data(str(s["counts"][family]), size_text(memory), [p[family] for p in s["history"]])
        cpu = s.get("host_cpu")
        self.cards["cpu"].update_data("—" if cpu is None else f"{cpu:.1f}%", "whole machine", [p["cpu"] for p in s["history"]], 100)
        self.memory_label.setText(f"{s['host_memory'] or 0:.1f}%   ·   {size_text(s['memory_used'])} / {size_text(s['memory_total'])}")
        self.memory_chart.set_values([p["memory"] for p in s["history"]], 100)
        self.canvas.counts = s["counts"]
        self.sidebar_counts.setText(f"PY  {s['counts']['python']}    JV  {s['counts']['java']}    OP  {s['counts']['opera']}")
        self.preview_table.populate(s["processes"])
        self.filter_processes()
        self.update_ledger()

    def filter_processes(self, *args):
        query = self.search.text().casefold()
        family = self.family_filter.currentText().lower()
        rows = [p for p in self.snapshot["processes"] if (family == "all channels" or p["family"] == family)
                and query in " ".join((str(p["pid"]), p["name"], p["exe"], p["entry"], " ".join(p["cmdline"]))).casefold()]
        self.process_table.populate(rows)
        self.process_count.setText(f"{len(rows)} shown / {len(self.snapshot['processes'])} monitored · " + ("No matching processes" if not rows else "Double-click a row to inspect"))

    def update_ledger(self):
        lines = []
        events = [(e["time"], f"{e['event']:8s}  {e['family'].upper():7s}  PID {e['pid']}  {e['name']}") for e in self.snapshot.get("events", [])]
        events += [(e["time"], "MODEL    " + e["note"] + "  →  " + json.dumps(e["result"]["output_boolean_array"])) for e in self.trace]
        for stamp, text in sorted(events, reverse=True)[:160]:
            lines.append(time.strftime("%H:%M:%S", time.localtime(stamp)) + "  " + text)
        if self.trace:
            lines += ["", "LATEST OPERATION TRACE (names retained from input)"]
            lines += [op["operation"] + "  ·  " + op["status"] for op in self.trace[0]["result"]["operation_trace"]]
            lines += ["", "LATEST DEEP AUDIT FLAGS"] + self.route["deep_audit"]["RAISED_FLAGS"]
        text = "\n".join(lines) or "Waiting for process events…"
        if self.event_text.toPlainText() != text:
            position = self.event_text.verticalScrollBar().value()
            self.event_text.setPlainText(text)
            self.event_text.verticalScrollBar().setValue(position)

    def load_library(self, *args):
        selected = self.library_list.currentItem()
        title = selected.text() if selected else None
        articles = self.store.search(self.library_search.text())
        self.library_list.blockSignals(True)
        self.library_list.clear()
        for article in articles:
            item = QListWidgetItem(article["title"])
            item.setData(Qt.ItemDataRole.UserRole, article)
            self.library_list.addItem(item)
        match = next((i for i, a in enumerate(articles) if a["title"] == title), 0)
        if articles:
            self.library_list.setCurrentRow(match)
        self.library_list.blockSignals(False)
        if articles:
            self.show_article(self.library_list.currentItem())
        else:
            self.article_view.setHtml("<h2>Your definition library</h2><p>Articles will appear here after syncing with Wikipedia.</p><p>Cached articles remain available offline. Use Sync now to retry if the connection is unavailable.</p>")

    def show_article(self, item, previous=None):
        if not item:
            return
        a = item.data(Qt.ItemDataRole.UserRole)
        paragraphs = "".join("<p>" + html.escape(p) + "</p>" for p in a["summary"].split("\n") if p.strip())
        url = html.escape(a["url"], quote=True)
        revision_url = f"https://en.wikipedia.org/w/index.php?oldid={a['revision']}" if a["revision"].isdigit() else a["url"]
        self.article_view.setHtml(f"<h1>{html.escape(a['title'])}</h1><p style='color:#8A9AAB'>Wikipedia contributors · {html.escape(a['revised_at'])}</p>{paragraphs}<hr><p><a style='color:#87F7C4' href='{url}'>Read full article</a> · <a style='color:#87F7C4' href='{html.escape(revision_url, quote=True)}'>Source revision</a> · <a style='color:#87F7C4' href='{LICENSE_URL}'>CC BY-SA 4.0</a></p><p>Introductory excerpt; formatting adapted. Retrieved {time.strftime('%Y-%m-%d %H:%M', time.localtime(a['fetched_at']))}.</p>")

    def add_topic(self):
        title = self.topic_input.text().strip()
        if title:
            self.store.add_topic(title)
            self.topic_input.clear()
            self.library_sync.sync_now()

    def connect_llama(self):
        self.llama_status.setText("Connecting to local Ollama…")
        def worker():
            try:
                self.events_queue.put(("models", llama.list_models()))
            except Exception as error:
                self.events_queue.put(("connection_error", str(error)))
        threading.Thread(target=worker, name="Ollama connection", daemon=True).start()

    def ask_llama(self):
        prompt = self.prompt_input.toPlainText().strip()
        model = self.model_combo.currentText()
        if not prompt:
            self.prompt_input.setFocus()
            return
        if not model:
            self.llama_status.setText("No model selected · connect to local Ollama first")
            return
        if self.llama_busy:
            return
        self.llama_busy = True
        self.last_auto = time.time()
        self.guide_button.setEnabled(False)
        self.llama_status.setText("Llama is reading the snapshot and definitions…")
        snapshot = self.bus_monitor.get_snapshot()
        snapshot["continuous_audit"] = self.live_audit.snapshot()
        snapshot["mesh_gateway"] = self.mesh_module.snapshot()
        snapshot["unified_core"] = self.unified_core.snapshot()
        snapshot["platform_alignment"] = self.platform_alignment.snapshot()
        snapshot["karmic_welfare"] = self.karmic_welfare.snapshot()
        snapshot["virtue_text"] = self.virtue_text.snapshot()
        snapshot["neural_learning"] = self.neural.snapshot()
        snapshot["web_research"] = self.web_research.snapshot()
        snapshot["souls_ingress"] = self.souls_ingress.snapshot()
        snapshot["reference_engines"] = self.reference.snapshot()
        route = self.read_route()
        signature = json.dumps(route, sort_keys=True)
        articles = self.store.search()
        identity,history=self.conversations.snapshot("llama")
        token=os.urandom(16).hex();self.llama_request=token
        def worker():
            try:
                result = llama.guide(model, prompt, snapshot, articles, route, history=history)
                self.events_queue.put(("guidance", {"result": result, "prompt": prompt, "signature": signature,
                                                   "token":token,"conversation_id":identity}))
            except Exception as error:
                self.events_queue.put(("guide_error", {"token":token,"error":str(error)}))
        threading.Thread(target=worker, name="Llama guidance", daemon=True).start()

    def receive_guidance(self, payload):
        if not self.llama_request or payload.get("token")!=self.llama_request:return
        self.llama_request=None
        self.llama_busy = False
        self.guide_button.setEnabled(True)
        result = payload["result"]
        raw=result.pop("conversation_reply",None)
        display=result["answer"]+"\n\n"+result["reason"]
        if not self.conversations.complete("llama",payload["conversation_id"],payload["prompt"],
                                           raw or json.dumps(result,ensure_ascii=False),result["model"],display=display):return
        self.refresh_conversation("llama")
        state = result["assessment"]
        stale = payload["prompt"] != self.prompt_input.toPlainText().strip() or payload["signature"] != json.dumps(self.read_route(), sort_keys=True)
        node_evaluations = result.get("node_evaluations", [])
        apply = self.apply_guidance.isChecked() and not stale and (state in {"good", "evil"} or any(n["evaluation"] in {"good", "evil"} for n in node_evaluations))
        if apply:
            if state in {"good", "evil"}:
                self.cap_state.setCurrentIndex(0 if state == "evil" else 1)
            for index, control in enumerate(self.evaluation_controls):
                node = next((n for n in node_evaluations if n["node"] == index), {})
                control.setCurrentText(node.get("evaluation", "unresolved"))
            self.apply_route("Llama assessment: " + state.upper(), result)
        action = "Applied to model + flux grid" if apply else ("Inputs changed · response retained without applying" if stale else "Bits held · " + state)
        self.llama_status.setText(action)
        evidence = ""
        for c in result["citations"]:
            evidence += f"<p><b>{html.escape(c['title'])}</b><br>“{html.escape(c['quote'])}”<br><a style='color:#87F7C4' href='{html.escape(c['url'], quote=True)}'>Wikipedia · revision {html.escape(c['revision'])}</a></p>"
        answer = html.escape(result["answer"]).replace("\n", "<br>")
        reason = html.escape(result["reason"]).replace("\n", "<br>")
        for node in node_evaluations:
            reason += f"<p><b>Node {node['node']}: {html.escape(node['evaluation'])}</b> · {html.escape(node['reason'])}</p>"
            for c in node.get("citations", []):
                evidence += f"<p>Node {node['node']} · {html.escape(c['title'])}: “{html.escape(c['quote'])}”</p>"
        update_text(self.guide_output,f"<p style='color:#87F7C4'>{html.escape(result['model'])} · {state.upper()}</p><h2>{html.escape(payload['prompt'])}</h2><p>{answer}</p><h3>Assessment</h3><p>{reason}</p><p style='color:#8A9AAB'>{html.escape(action)}</p><h3>Definition evidence</h3>{evidence or '<p>No verified definition passage.</p>'}",rich=True)
        if self.command_mode.currentIndex() == 1 and self.command_input.toPlainText().strip() == payload["prompt"]:
            self.command_result.setPlainText(result["answer"] + "\n\n" + result["reason"] + "\n\n" + action)
            self.last_command = {"input": payload["prompt"], "result": result, "time": time.time()}
        self.log_activity("LLAMA", result["model"] + " · " + action)
        self.capture_pipeline("Llama",str(time.time_ns()),{"input":payload["prompt"],"output":result})

    def export_snapshot(self):
        suggested = str(Path.home() / "Documents" / ("FluxBus-" + time.strftime("%Y%m%d-%H%M%S") + ".json"))
        path, kind = QFileDialog.getSaveFileName(self, "Export current snapshot", suggested, "JSON snapshot (*.json);;Process table CSV (*.csv)")
        if not path:
            return
        csv_mode = "CSV" in kind or path.lower().endswith(".csv")
        if not Path(path).suffix:
            path += ".csv" if csv_mode else ".json"
        try:
            write_export(path, self.snapshot, self.route, self.flux_grid.records, csv_mode, self.extension_export())
            self.footer.setText("Snapshot saved to " + path)
        except OSError as error:
            QMessageBox.warning(self, "Export could not be saved", str(error))

    def closeEvent(self, event):
        self.timer.stop()
        self.canvas.timer.stop()
        self.bus_monitor.stop()
        self.library_sync.stop()
        self.stop_extensions()
        event.accept()


def write_export(path, snapshot, route, records, csv_mode=False, extensions=None):
    import tempfile
    target = Path(path)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig" if csv_mode else "utf-8",
                                         newline="", dir=target.parent, delete=False) as file:
            temp_name = file.name
            if csv_mode:
                writer = csv.writer(file)
                writer.writerow(["family", "pid", "ppid", "name", "cpu_percent_machine", "memory_bytes", "status", "entry", "executable"])
                for p in snapshot["processes"]:
                    values = [p[k] for k in ("family", "pid", "ppid", "name", "cpu", "memory", "status", "entry", "exe")]
                    writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for v in values])
            else:
                json.dump({"app": "Flux Bus 2.0", "telemetry": snapshot, "model": route, "flux": records, "runtime": extensions or {}}, file, indent=2, ensure_ascii=False)
        os.replace(temp_name, target)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def make_icon():
    pix = QPixmap(128, 128)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#101B22"))
    painter.setPen(QPen(QColor("#284638"), 3))
    painter.drawRoundedRect(5, 5, 118, 118, 28, 28)
    painter.setPen(QPen(QColor(MINT), 5))
    from PySide6.QtCore import QPointF
    vertices = [(64, 23), (103, 45), (103, 84), (64, 106), (25, 84), (25, 45)]
    for i, point in enumerate(vertices):
        painter.drawLine(QPointF(*point), QPointF(*vertices[(i+1)%6]))
    for i in (1, 3, 5):
        painter.drawLine(QPointF(64, 64), QPointF(*vertices[i]))
    painter.end()
    return QIcon(pix)


def nav_icon(index):
    pix = QPixmap(22, 22)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#9EB6BC"), 1.3))
    if index in (0, 5):
        p.drawEllipse(4, 4, 14, 14)
        p.drawEllipse(8, 8, 6, 6)
    elif index == 3:
        for x in (4, 10, 16):
            for y in (4, 10, 16):
                p.drawRect(x, y, 3, 3)
    elif index == 2:
        p.drawLine(3, 7, 19, 7)
        p.drawLine(15, 3, 19, 7)
        p.drawLine(3, 15, 19, 15)
        p.drawLine(3, 15, 7, 19)
    else:
        for y in (5, 11, 17):
            p.drawLine(6, y, 19, y)
            p.drawPoint(2, y)
    p.end()
    return QIcon(pix)


def main():
    parser = argparse.ArgumentParser(description="Flux Bus system and logic studio")
    parser.add_argument("--demo", action="store_true", help="Show explicitly labelled simulated telemetry")
    parser.add_argument("--data-dir", type=Path, help="Override the portable local data directory")
    parser.add_argument("--smoke-test", action="store_true", help="Render all pages and exit after a short live run")
    parser.add_argument("--smoke-hub-port", type=int, default=9999, help="Test-only local hub port; use 0 for an unused temporary port")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Flux Bus v2")
    app.setStyle("Fusion")
    load_fonts(app)
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    data_dir = args.data_dir or (base / "FluxBus-data")
    monitor = SystemBusMonitor(demo=args.demo)
    window = GraphicalVirtueMatrixEngine(monitor, data_dir, start_services=not args.smoke_test)
    if args.smoke_test:
        window.hub.port = args.smoke_hub_port
        window.bus_monitor.start()
        window.library_sync.start()
        window.connect_llama()
        window.start_extensions()
    window.show()
    screen = app.primaryScreen().availableGeometry()
    if not args.smoke_test and (window.width() > screen.width() or window.height() > screen.height()):
        window.resize(min(1440, screen.width()-20), min(960, screen.height()-40))
    if args.smoke_test:
        from karmic_welfare import KarmicWelfareEngine,INPUT_TEMPLATE as WELFARE_EXAMPLE
        window.queue_welfare_input(WELFARE_EXAMPLE)
        from virtue_text import VirtueTextEngine,INPUT_TEMPLATE as TEXT_EXAMPLE
        from binary_layout import ORIGINAL_LAYOUT
        window.queue_text_pipeline_input({**TEXT_EXAMPLE,'binary_layout':ORIGINAL_LAYOUT})
        from neural_page import examples
        from reference_catalog import examples as reference_examples
        neural_job=window.queue_neural_input({**examples(),'reference_engines':reference_examples(),'neural':{'target':.9}})
        def finish():
            (data_dir/"neural-smoke.json").write_text(json.dumps({"learning":window.neural.detail(neural_job),"ledgers":window.souls_ingress.detail(neural_job)},indent=2),encoding="utf-8")
            (data_dir/'reference-smoke.json').write_text(json.dumps(window.reference.detail(neural_job),indent=2),encoding='utf8')
            for i in range(window.pages.count()):
                window.navigate(i)
                app.processEvents()
                window.grab().save(str(data_dir / f"page-{i}.png"))
            (data_dir / "smoke.json").write_text(json.dumps({"snapshot": window.snapshot, "route": window.route, "runtime": window.extension_export()}, indent=2), encoding="utf-8")
            from unified_runtime import execute_unified_engines,resolve_result,INPUT_TEMPLATE
            from infrastructure_pdf import GraphicalPDFGenerator
            from platform_alignment import PlatformAlignmentEngine,INPUT_TEMPLATE as PLATFORM_EXAMPLE
            text_report=VirtueTextEngine().execute({**TEXT_EXAMPLE,'binary_layout':ORIGINAL_LAYOUT})
            (data_dir/'text-smoke.json').write_text(json.dumps(text_report,indent=2),encoding='utf-8')
            welfare_report=KarmicWelfareEngine().execute(WELFARE_EXAMPLE)
            (data_dir/'welfare-smoke.json').write_text(json.dumps(welfare_report,indent=2),encoding='utf-8')
            platform_report=PlatformAlignmentEngine().execute(PLATFORM_EXAMPLE)
            (data_dir/'platform-smoke.json').write_text(json.dumps(platform_report,indent=2),encoding='utf-8')
            report=execute_unified_engines(INPUT_TEMPLATE)
            (data_dir/'unified-smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            GraphicalPDFGenerator().export(data_dir/'infrastructure-smoke.pdf',resolve_result(report,'InfrastructureLogCompiler'))
            window.close()
        QTimer.singleShot(8000, finish)
    return app.exec()


def load_fonts(app):
    assets = Path(__file__).resolve().parent / "assets"
    for filename in ("Inter.ttf", "IBMPlexMono-Regular.ttf"):
        QFontDatabase.addApplicationFont(str(assets / filename))
    app.setFont(QFont("Inter", 10))


if __name__ == "__main__":
    raise SystemExit(main())
