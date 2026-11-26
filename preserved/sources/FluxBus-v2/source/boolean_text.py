"""Formatting-preserving Boolean literal inversion; no evaluation or execution."""
import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QSplitter, QVBoxLayout, QWidget)


def invert_boolean_text(text, flip_bits=False):
    if not isinstance(text, str):
        raise TypeError("Input must be text")
    counts = {"words": 0, "bits": 0}
    pattern = r"(?<!\w)(?:true|false)(?!\w)"
    if flip_bits:
        pattern += r"|(?<![\w.+-])[01](?![\w.])"
    def replace(match):
        value = match[0]
        if value in ("0", "1"):
            counts["bits"] += 1
            return "1" if value == "0" else "0"
        counts["words"] += 1
        opposite = "false" if value.lower() == "true" else "true"
        if value.isupper(): return opposite.upper()
        if value.istitle(): return opposite.title()
        return opposite
    output = re.sub(pattern, replace, text, flags=re.I)
    return {"output": output, "replacements": counts, "total": sum(counts.values())}


class BooleanTextPage(QWidget):
    def __init__(self, audit_callback=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        intro = QLabel("Paste text, JSON, or code. Invert whole true / false words while keeping its layout.\n"
                       "Optional bit inversion swaps standalone 0 / 1 tokens. Names and other numbers stay intact.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        controls = QHBoxLayout()
        self.flip_bits = QCheckBox("Also invert 0 / 1")
        controls.addWidget(self.flip_bits)
        controls.addStretch()
        self.invert_button = QPushButton("Invert text")
        self.invert_button.setObjectName("primary")
        self.invert_button.clicked.connect(self.transform)
        controls.addWidget(self.invert_button)
        self.copy_button = QPushButton("Copy output")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_output)
        controls.addWidget(self.copy_button)
        layout.addLayout(controls)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText('can = false\ncannot = true\n{"enabled": true, "paused": false}\nbits = [1, 0, 1]')
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        for title, field in (("INPUT", self.input), ("INVERTED OUTPUT", self.output)):
            panel = QWidget(); column = QVBoxLayout(panel)
            column.setContentsMargins(0, 6, 0, 0)
            heading = QLabel(title); heading.setObjectName("eyebrow")
            column.addWidget(heading); column.addWidget(field)
            split.addWidget(panel)
        layout.addWidget(split, 1)
        bottom = QHBoxLayout()
        self.status = QLabel("Ready · literal text transformation")
        self.status.setWordWrap(True)
        bottom.addWidget(self.status, 1)
        reuse = QPushButton("Use output as input")
        reuse.clicked.connect(lambda: self.input.setPlainText(self.output.toPlainText()))
        bottom.addWidget(reuse)
        if audit_callback:
            audit = QPushButton("Audit output")
            audit.clicked.connect(lambda: audit_callback(self.output.toPlainText()))
            bottom.addWidget(audit)
        layout.addLayout(bottom)
        self.input.textChanged.connect(self.mark_changed)
        self.flip_bits.toggled.connect(self.mark_changed)

    def mark_changed(self):
        self.copy_button.setEnabled(False)
        self.status.setText("Input changed · press Invert text to update the output")

    def transform(self):
        result = invert_boolean_text(self.input.toPlainText(), self.flip_bits.isChecked())
        self.output.setPlainText(result["output"])
        self.copy_button.setEnabled(True)
        self.status.setText(f"{result['replacements']['words']} Boolean words and {result['replacements']['bits']} bits inverted · ready to copy")

    def copy_output(self):
        QApplication.clipboard().setText(self.output.toPlainText())
        self.status.setText("Copied inverted output to clipboard")
