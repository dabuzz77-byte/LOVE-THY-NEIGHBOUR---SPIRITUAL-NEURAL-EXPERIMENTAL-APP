"""Resolution-independent, animated native graphics for Flux Bus."""
import math
import time
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel

BG = "#090C12"
PANEL = "#111720"
BORDER = "#25303D"
TEXT = "#ECF3F8"
MUTED = "#8A9AAB"
MINT = "#87F7C4"
COLORS = {"python": "#7AA8FF", "java": "#FFC084", "opera": "#FF829B"}


def color(value, alpha=255):
    c = QColor(value)
    c.setAlpha(alpha)
    return c


def font(size=10, bold=False, mono=False):
    return QFont("IBM Plex Mono" if mono else "Inter", size, QFont.Weight.DemiBold if bold else QFont.Weight.Normal)


def draw_text(p, rect, text, size=10, fill=TEXT, bold=False, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, mono=False):
    p.setPen(QColor(fill))
    p.setFont(font(size, bold, mono))
    p.drawText(QRectF(rect), align, str(text))


class Panel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")


class Sparkline(QWidget):
    def __init__(self, tint=MINT, height=46):
        super().__init__()
        self.tint = tint
        self.values = []
        self.ceiling = None
        self.setMinimumHeight(height)

    def set_values(self, values, ceiling=None):
        self.values = [float(v) if v is not None else 0 for v in values][-100:]
        self.ceiling = ceiling
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(color(BORDER, 120), 1))
        for y in (h * .3, h * .65, h - 2):
            p.drawLine(QPointF(0, y), QPointF(w, y))
        if len(self.values) < 2:
            draw_text(p, QRectF(0, 0, w, h), "Collecting samples…", 9, MUTED)
            return
        ceiling = self.ceiling or max(2, max(self.values) * 1.25)
        step = w / (max(30, len(self.values)) - 1)
        start_x = w - step * (len(self.values) - 1)
        points = [QPointF(start_x + i * step, h - 3 - min(v / ceiling, 1) * (h - 10)) for i, v in enumerate(self.values)]
        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)
        area = QPainterPath(path)
        area.lineTo(w, h)
        area.lineTo(start_x, h)
        area.closeSubpath()
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, color(self.tint, 60))
        gradient.setColorAt(1, color(self.tint, 0))
        p.fillPath(area, gradient)
        p.setPen(QPen(QColor(self.tint), 1.8))
        p.drawPath(path)
        p.setBrush(QColor(self.tint))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(points[-1], 2.8, 2.8)


class MetricCard(Panel):
    def __init__(self, title, subtitle, tint):
        super().__init__()
        self.tint = tint
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 12)
        layout.setSpacing(4)
        heading = QHBoxLayout()
        heading.addWidget(QLabel(title))
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{tint}; font-size:10px")
        heading.addStretch()
        heading.addWidget(dot)
        layout.addLayout(heading)
        value_row = QHBoxLayout()
        self.value = QLabel("—")
        self.value.setStyleSheet("font-size:33px;font-weight:600;color:#ECF3F8")
        self.detail = QLabel(subtitle)
        self.detail.setStyleSheet("font-size:11px;color:#8A9AAB")
        value_row.addWidget(self.value)
        value_row.addStretch()
        value_row.addWidget(self.detail, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(value_row)
        self.chart = Sparkline(tint, 33)
        self.chart.setMaximumHeight(37)
        layout.addWidget(self.chart)
        self.setMinimumHeight(142)

    def update_data(self, value, detail, values, ceiling=None):
        self.value.setText(value)
        self.detail.setText(detail)
        self.chart.set_values(values, ceiling)


class BusCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.counts = dict.fromkeys(COLORS, 0)
        self.virtue = "PASS"
        self.bits = [True, False]
        self.phase_start = time.monotonic()
        self.paused_at = None
        self.setMinimumSize(440, 300)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(33)

    def advance(self):
        if self.isVisible() and self.paused_at is None:
            self.update()

    def pause(self, paused):
        if paused and self.paused_at is None:
            self.paused_at = time.monotonic()
        elif not paused and self.paused_at is not None:
            self.phase_start += time.monotonic() - self.paused_at
            self.paused_at = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        t = (self.paused_at or time.monotonic()) - self.phase_start
        cx, cy = w * .5, h * .46
        s = min(w / 820, h / 395)
        accent = MINT if self.virtue == "PASS" else "#FF829B"
        p.fillRect(self.rect(), QColor("#0D131C"))
        glow = QRadialGradient(QPointF(cx, cy), max(w, h) * .46)
        glow.setColorAt(0, color(accent, 19))
        glow.setColorAt(1, color(accent, 0))
        p.fillRect(self.rect(), glow)
        p.setPen(QPen(QColor("#17222D"), .6))
        for x in range(20, w, 36):
            for y in range(18, h, 36):
                p.drawPoint(x, y)
        draw_text(p, QRectF(22, 13, 220, 21), "LIVE PROCESS TOPOLOGY", 9, MUTED, True, mono=True)
        draw_text(p, QRectF(w - 210, 13, 185, 21), "03 CHANNELS  /  01 CORE", 8, MUTED, align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, mono=True)
        # The original four binary rows, kept as a quiet matrix layer.
        for row in range(4):
            bits = ("10101010101010" if row % 2 == 0 else "01010101010101")
            draw_text(p, QRectF(24, 53 + row * 17, 160, 18), bits, 8, "#34514C", mono=True)
        # Orbital paths.
        for tilt, radius in ((-.22, 235), (.3, 215), (.02, 260)):
            p.save()
            p.translate(cx, cy)
            p.rotate(math.degrees(tilt))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(color(accent, 35), .8))
            p.drawEllipse(QRectF(-radius*s, -85*s, radius*2*s, 170*s))
            for i in range(9):
                a = t * .28 + i * math.tau / 9 + radius * .01
                point = QPointF(math.cos(a) * radius*s, math.sin(a) * 85*s)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(color(accent, 38))
                p.drawEllipse(point, 6*s, 6*s)
                p.setBrush(color(accent, 180))
                p.drawEllipse(point, 1.8*s, 1.8*s)
            p.restore()
        # True 4D hypercube projected through 3D to the screen.
        points = []
        angle = t * .16
        for i in range(16):
            x, y, z, q = [1 if (i >> j) & 1 else -1 for j in range(4)]
            x, q = x * math.cos(angle) - q * math.sin(angle), x * math.sin(angle) + q * math.cos(angle)
            y, z = y * math.cos(.45 + angle*.7) - z * math.sin(.45 + angle*.7), y * math.sin(.45 + angle*.7) + z * math.cos(.45 + angle*.7)
            d4 = 2.8 / (3.4 - q)
            x, y, z = x*d4, y*d4, z*d4
            x, z = x * math.cos(.5) + z * math.sin(.5), -x * math.sin(.5) + z * math.cos(.5)
            d3 = 4 / (5 - z)
            points.append(QPointF(cx + x*d3*69*s, cy + y*d3*69*s))
        for i, a in enumerate(points):
            for j in range(i+1, 16):
                if (i ^ j).bit_count() == 1:
                    p.setPen(QPen(color(accent, 20), 7*s))
                    p.drawLine(a, points[j])
                    p.setPen(QPen(color(accent, 145 if i < 8 else 220), 1.1*s))
                    p.drawLine(a, points[j])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color(accent, 255))
            p.drawEllipse(a, 2*s, 2*s)
        label_y = cy + 116*s
        draw_text(p, QRectF(cx-120, label_y, 240, 22), "T E S S E R A C T   C O R E", 9, TEXT, True, Qt.AlignmentFlag.AlignCenter)
        # Live bus nodes and packets into the core.
        by = h - 47
        for i, family in enumerate(COLORS):
            x = w * (.18 + .32*i)
            tint = COLORS[family]
            path = QPainterPath(QPointF(x, by-17))
            path.cubicTo(x, by-50, cx + (x-cx)*.6, cy+70*s, cx, cy+40*s)
            p.setPen(QPen(color(tint, 70), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            if self.counts[family] > 0:
                for offset in (0, .5):
                    point = path.pointAtPercent((t*.28 + offset + i*.2) % 1)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(color(tint, 40))
                    p.drawEllipse(point, 6, 6)
                    p.setBrush(QColor(tint))
                    p.drawEllipse(point, 2, 2)
            p.setPen(QPen(color(tint, 100), 1))
            p.setBrush(QColor("#131D28"))
            p.drawRoundedRect(QRectF(x-68, by-18, 136, 45), 8, 8)
            draw_text(p, QRectF(x-56, by-13, 84, 30), family.upper(), 8, tint, True, mono=True)
            draw_text(p, QRectF(x+21, by-13, 36, 30), self.counts[family], 16, TEXT, True, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        draw_text(p, QRectF(w-140, h-22, 123, 15), "ANIMATED TELEMETRY", 7, "#65768A", align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, mono=True)


class RouteCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.result = {}
        self.setMinimumHeight(118)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        result = self.result.get("trajectory", {})
        labels = ["LOCAL CAN", "CORRECTIVE SHIFT", "RESOLVED CAN"]
        vals = [str(result.get("local_can_before", False)).lower(), "FLIP" if result.get("corrective_shift") else "HOLD", str(result.get("can_after", True)).lower()]
        positions = [w*.16, w*.5, w*.84]
        for a, b in zip(positions, positions[1:]):
            p.setPen(QPen(QColor("#345349"), 2))
            p.drawLine(QPointF(a+57, h*.5), QPointF(b-57, h*.5))
            p.drawLine(QPointF(b-62, h*.5-4), QPointF(b-57, h*.5))
            p.drawLine(QPointF(b-62, h*.5+4), QPointF(b-57, h*.5))
        for i, x in enumerate(positions):
            tint = MINT if i == 2 else ("#FF829B" if i == 0 and result.get("conflict") else "#B7A1FF")
            p.setPen(QPen(color(tint, 100), 1))
            p.setBrush(color(tint, 14))
            p.drawRoundedRect(QRectF(x-57, 14, 114, h-28), 12, 12)
            draw_text(p, QRectF(x-57, 20, 114, 20), labels[i], 7, tint, True, Qt.AlignmentFlag.AlignCenter)
            draw_text(p, QRectF(x-57, 45, 114, 42), vals[i], 21, TEXT, True, Qt.AlignmentFlag.AlignCenter, mono=True)


class FluxGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.records = []
        self.selected = 0
        self.last_step = time.monotonic()
        self.setMinimumSize(600, 320)
        self.setMouseTracking(True)
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update() if self.isVisible() and time.monotonic()-self.last_step < 1.2 else None)
        self.timer.start(40)

    def add(self, record):
        self.records.insert(0, record)
        self.records = self.records[:120]
        self.selected = 0
        self.last_step = time.monotonic()
        self.update()

    def mousePressEvent(self, event):
        row = int((event.position().y() - 62) // 29)
        if 0 <= row < len(self.records):
            self.selected = row
            self.update()
            if hasattr(self, "on_select"):
                self.on_select(self.records[row])

    def mouseMoveEvent(self, event):
        cell = (self.width()-62)/29
        row = int((event.position().y()-62)//29)
        column = int((event.position().x()-18)//cell)
        if 0 <= row < len(self.records) and 0 <= column < 16:
            record = self.records[row]
            self.setToolTip(f"{record['names'][column]}: {int(record['before'][column])} → {int(record['after'][column])}")
        else:
            self.setToolTip("")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0D131C"))
        x0, gap = 18, 5
        cell = (w - 62) / 29
        tern_x = x0 + 17*cell
        draw_text(p, QRectF(x0, 10, 16*cell, 22), "BINARY  /  16 MODEL REGISTERS", 9, MUTED, True, mono=True)
        draw_text(p, QRectF(tern_x, 10, 11*cell, 22), "BALANCED TERNARY  /  SAME VALUE", 9, MUTED, True, mono=True)
        for i in range(16):
            draw_text(p, QRectF(x0+i*cell, 36, cell-gap, 19), str(15-i), 8, MUTED, align=Qt.AlignmentFlag.AlignCenter, mono=True)
        for i in range(11):
            draw_text(p, QRectF(tern_x+i*cell, 36, cell-gap, 19), str(10-i), 8, MUTED, align=Qt.AlignmentFlag.AlignCenter, mono=True)
        visible = max(1, int((h-170)//29))
        for r in range(visible):
            record = self.records[r] if r < len(self.records) else None
            y = 62+r*29
            if record and r == self.selected:
                p.fillRect(QRectF(9, y-3, w-18, 29), QColor("#1D2938"))
            for i in range(16):
                v = record["after"][i] if record else False
                changed = record and record["before"][i] != v
                tint = (MINT if v else COLORS["opera"]) if changed else ("#7AA8FF" if v else "#344351")
                p.setPen(Qt.PenStyle.NoPen)
                pulse = max(0, 1-(time.monotonic()-self.last_step)/1.2) if r == 0 and changed else 0
                p.setBrush(color(tint, int(38 + pulse*110) if record else 12))
                rect = QRectF(x0+i*cell, y, cell-gap, 23)
                p.drawRoundedRect(rect, 4, 4)
                if record:
                    draw_text(p, rect, str(int(v)), 10, tint, True, Qt.AlignmentFlag.AlignCenter, mono=True)
            for i in range(11):
                v = record["trits"][i] if record else 0
                tint = MINT if v > 0 else ("#B7A1FF" if v < 0 else "#455468")
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(color(tint, 32 if record else 12))
                rect = QRectF(tern_x+i*cell, y, cell-gap, 23)
                p.drawRoundedRect(rect, 4, 4)
                if record:
                    draw_text(p, rect, {1: "+", -1: "−", 0: "0"}[v], 12, tint, True, Qt.AlignmentFlag.AlignCenter, mono=True)
        if self.records:
            record = self.records[min(self.selected, len(self.records)-1)]
            bitstring = "".join(str(int(v)) for v in record["after"])
            tritstring = "".join({1: "+", -1: "−", 0: "0"}[v] for v in record["trits"])
            y = h-94
            draw_text(p, QRectF(18, y, w-36, 22), f"{record['label']}   ·   {record['flips']} shifts   ·   {16-record['flips']} held", 10, TEXT, True)
            draw_text(p, QRectF(18, y+28, w-36, 25), f"{bitstring} ₂   =   {record['decimal']} ₁₀   =   {tritstring} ₃", 13, MINT, mono=True)
            draw_text(p, QRectF(18, y+59, w-36, 20), "+ = +1     − = −1     0 = 0       ·       Select a row to inspect its conversion", 9, MUTED)
