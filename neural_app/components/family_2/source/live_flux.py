"""Active square cells for real serialized engine/telemetry frames."""
import hashlib
import json
import math
import struct
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget
from ..source.routing import balanced_ternary
from ..source.visuals import draw_text, MINT

class LiveFluxCanvas(QWidget):
    HEADER_NAMES = ('Python process count', 'Java process count', 'Opera process count', 'CPU × 100', 'Memory % × 100', 'Sample sequence low word', 'Observatory received low word', 'Observatory accepted low word')

    def __init__(self):
        super().__init__()
        self.raw = b''
        self.previous = b''
        self.sha = ''
        self.page = 0
        self.setMinimumSize(520, 400)
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update() if self.isVisible() else None)
        self.timer.start(100)

    @property
    def rows_per_page(self):
        return max(5, min(24, (self.height() - 105) // 28))

    @property
    def page_count(self):
        return max(1, math.ceil(len(self.raw) / (self.rows_per_page * 2)))

    def set_page(self, page):
        self.page = max(0, min(page, self.page_count - 1))
        self.update()

    def set_frame(self, data):
        telemetry = data.get('telemetry', {})
        counts = telemetry.get('counts', {})
        obs = data.get('observatory', {})
        readings = [counts.get(k, 0) for k in ('python', 'java', 'opera')]
        readings += [round((telemetry.get('host_cpu') or 0) * 100), round((telemetry.get('host_memory') or 0) * 100), telemetry.get('sequence', 0), obs.get('received', 0), obs.get('acknowledged', 0)]
        self.previous = self.raw
        self.raw = struct.pack('>8H', *(int(v) & 65535 for v in readings)) + json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.page = min(self.page, self.page_count - 1)
        self.update()

    def mouseMoveEvent(self, event):
        row = int((event.position().y() - 55) // 28)
        word = self.page * self.rows_per_page + row
        if 0 <= row < self.rows_per_page and word * 2 < len(self.raw):
            value = int.from_bytes(self.raw[word * 2:word * 2 + 2].ljust(2, b'\x00'), 'big')
            name = self.HEADER_NAMES[word] if word < 8 else f'Full snapshot UTF-8 bytes {(word - 8) * 2}–{(word - 8) * 2 + 1}'
            self.setToolTip(f'{name}\n{value:016b} (binary) = {value} (decimal)\nBalanced ternary: {balanced_ternary(value)}')
        else:
            self.setToolTip('')

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor('#0D131C'))
        cell = (self.width() - 36) / 28
        gap = 3
        start = 12
        tern = start + 17 * cell
        draw_text(p, QRectF(start, 12, 16 * cell, 20), '16 BIT WORDS / LIVE BYTES', 8, '#8A9AAB', True, mono=True)
        draw_text(p, QRectF(tern, 12, 11 * cell, 20), 'BALANCED TERNARY', 8, '#8A9AAB', True, mono=True)
        for row in range(self.rows_per_page):
            offset = (self.page * self.rows_per_page + row) * 2
            if offset >= len(self.raw):
                break
            value = int.from_bytes(self.raw[offset:offset + 2].ljust(2, b'\x00'), 'big')
            old = int.from_bytes(self.previous[offset:offset + 2].ljust(2, b'\x00'), 'big')
            digits = balanced_ternary(value)
            digits = [0] * (11 - len(digits)) + digits
            for i in range(16):
                bit = value >> 15 - i & 1
                changed = bit != old >> 15 - i & 1
                tint = MINT if changed and bit else '#FF829B' if changed else '#82ADFF' if bit else '#3C5064'
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor('#244C3D' if changed and bit else '#182535'))
                rect = QRectF(start + i * cell, 55 + row * 28, cell - gap, 23)
                p.drawRoundedRect(rect, 3, 3)
                draw_text(p, rect, bit, 9, tint, True, Qt.AlignmentFlag.AlignCenter, mono=True)
            for i, trit in enumerate(digits):
                p.setBrush(QColor('#1C2A32'))
                p.setPen(Qt.PenStyle.NoPen)
                rect = QRectF(tern + i * cell, 55 + row * 28, cell - gap, 23)
                p.drawRoundedRect(rect, 3, 3)
                draw_text(p, rect, {1: '+', 0: '0', -1: '−'}[trit], 10, MINT if trit > 0 else '#B7A1FF' if trit < 0 else '#506173', True, Qt.AlignmentFlag.AlignCenter, mono=True)
        draw_text(p, QRectF(12, self.height() - 38, self.width() - 24, 25), f'Page {self.page + 1} / {self.page_count} · {len(self.raw):,} real bytes · hover for register details', 9, '#8A9AAB')
