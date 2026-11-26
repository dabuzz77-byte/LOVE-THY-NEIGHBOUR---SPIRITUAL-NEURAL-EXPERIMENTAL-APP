"""Data-driven Qt graphics. No animation timers or fabricated telemetry."""
import math
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QLinearGradient
from PySide6.QtWidgets import QWidget
INK = '#E8F2F8'
MUTED = '#8FA8BA'
MINT = '#87F7C4'
BLUE = '#70BFFF'
VIOLET = '#BBA4FF'

def text(p, rect, value, size=10, color=INK, bold=False, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
    font = QFont('Segoe UI', size)
    font.setBold(bold)
    p.setFont(font)
    p.setPen(QColor(color))
    p.drawText(rect, align, str(value))

class DataGraphic(QWidget):

    def __init__(self, kind='report', height=230):
        super().__init__()
        self.kind = kind
        self.data = None
        self.setMinimumHeight(height)
        self.setMouseTracking(True)

    def set_data(self, data):
        if data != self.data:
            self.data = data
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor('#132331'))
        gradient.setColorAt(1, QColor('#101722'))
        p.setBrush(gradient)
        p.setPen(QPen(QColor('#294252'), 1))
        p.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 14, 14)
        if self.kind == 'weights':
            self.weights(p)
        elif self.kind == 'processes':
            self.processes(p)
        elif self.kind == 'performance':
            self.performance(p)
        else:
            self.report(p)
        p.end()

    def empty(self, p, title, detail):
        text(p, QRectF(22, 18, self.width() - 44, 27), title, 12, MINT, True)
        text(p, QRectF(22, 53, self.width() - 44, self.height() - 65), detail, 10, MUTED, False, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap)

    def weights(self, p):
        if not self.data:
            return self.empty(p, 'ENGINE WEIGHT LANDSCAPE', 'Weights appear after the model is available.')
        rows = sorted(self.data, key=lambda row: abs(row['weight'] - 1), reverse=True)[:8]
        text(p, QRectF(20, 12, self.width() - 40, 25), 'LEARNED INFLUENCE  /  1.0 = starting weight', 11, MINT, True)
        width = (self.width() - 40) / len(rows)
        baseline = self.height() - 42
        for i, row in enumerate(rows):
            x = 20 + i * width
            h = max(2, (self.height() - 91) * row['weight'] / 2)
            p.setBrush(QColor(MINT if row['weight'] >= 1 else VIOLET))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(x + 10, baseline - h, width - 20, h), 4, 4)
            text(p, QRectF(x, baseline - h - 24, width, 22), f"{row['weight']:.3f}", 9, INK, True, Qt.AlignmentFlag.AlignCenter)
            name = row['engine'].split('.')[-1]
            text(p, QRectF(x, baseline + 6, width, 24), name[:13], 8, MUTED, False, Qt.AlignmentFlag.AlignCenter)
        y = baseline - (self.height() - 91) / 2
        p.setPen(QPen(QColor('#668080'), 1, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(20, y), QPointF(self.width() - 20, y))
        self.setToolTip('\n'.join((f"{r['engine']}: {r['weight']:.6f}" for r in rows)))

    def processes(self, p):
        data = self.data or {}
        processes = data.get('processes', [])
        text(p, QRectF(20, 10, self.width() - 40, 24), 'RUNNING CHANNELS  /  measured process memory', 11, MINT, True)
        total = sum((row.get('memory') or 0 for row in processes))
        x = 22
        w = self.width() - 44
        for i, family in enumerate(('python', 'java', 'opera')):
            rows = [r for r in processes if r['family'] == family]
            used = sum((r.get('memory') or 0 for r in rows))
            span = w / 3
            text(p, QRectF(x + i * span, 42, span, 23), f'{family.upper()}  ·  {len(rows)}', 11, (MINT, BLUE, VIOLET)[i], True)
            text(p, QRectF(x + i * span, 67, span, 22), f'{used / 1048576:,.0f} MB', 10, INK)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#203444'))
            p.drawRoundedRect(QRectF(x + i * span, 100, span - 18, 8), 4, 4)
            p.setBrush(QColor((MINT, BLUE, VIOLET)[i]))
            p.drawRoundedRect(QRectF(x + i * span, 100, (span - 18) * used / max(1, total), 8), 4, 4)

    def performance(self, p):
        values = self.data or []
        text(p, QRectF(20, 12, self.width() - 40, 25), 'INTERFACE RESPONSE  /  milliseconds per update', 11, MINT, True)
        if not values:
            return self.empty(p, 'INTERFACE RESPONSE', 'Samples appear while the application runs.')
        ceiling = max(16, max(values))
        rect = QRectF(22, 55, self.width() - 44, self.height() - 92)
        for fraction in (0, 0.5, 1):
            y = rect.bottom() - fraction * rect.height()
            p.setPen(QPen(QColor('#253E4D'), 1))
            p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
        path = QPainterPath()
        for i, v in enumerate(values):
            point = QPointF(rect.left() + i * rect.width() / max(1, len(values) - 1), rect.bottom() - v / ceiling * rect.height())
            path.moveTo(point) if i == 0 else path.lineTo(point)
        p.setPen(QPen(QColor(MINT), 2))
        p.drawPath(path)
        text(p, QRectF(22, self.height() - 32, self.width() - 44, 22), f'Latest {values[-1]:.1f} ms     Average {sum(values) / len(values):.1f} ms     Peak {max(values):.1f} ms', 9, MUTED)

    def report(self, p):
        report = self.data or {}
        name = report.get('engine', 'ENGINE EXPLORER')
        state = report.get('state', {})
        actions = report.get('actions', [])
        outputs = [r['output'] for r in actions if isinstance(r.get('output'), dict)]
        title = name.replace('Controller', '').replace('Engine', '').replace('Governor', '')
        text(p, QRectF(22, 12, self.width() - 44, 29), title or name, 12, MINT, True)
        if not report:
            return self.empty(p, 'ENGINE EXPLORER', 'Run an engine to see its measured or calculated result here.')
        wave = next((o['wave'] for o in outputs if 'wave' in o), None)
        if wave:
            rect = QRectF(25, 70, self.width() - 50, self.height() - 125)
            path = QPainterPath()
            p.setPen(QPen(QColor('#2B4050'), 1))
            p.drawLine(QPointF(rect.left(), rect.center().y()), QPointF(rect.right(), rect.center().y()))
            for i, (x, y) in enumerate(wave):
                point = QPointF(rect.left() + x * rect.width(), rect.center().y() - y * rect.height() * 0.45)
                path.moveTo(point) if i == 0 else path.lineTo(point)
            p.setPen(QPen(QColor(VIOLET), 2))
            p.drawPath(path)
            output = next((o for o in outputs if 'wave' in o))
            text(p, QRectF(22, 43, self.width() - 44, 23), f"{output['frequency_hz']} Hz · mathematical waveform", 10, VIOLET)
            text(p, QRectF(22, self.height() - 38, self.width() - 44, 24), output['active_harmonic_tier'].replace('_', ' '), 9, MUTED)
            return
        stars = state.get('star_catalog_matrix')
        if stars:
            rect = QRectF(45, 60, self.width() - 90, self.height() - 110)
            for name, (x, y) in stars.items():
                point = QPointF(rect.left() + x / 14 * rect.width(), rect.bottom() - y / 50 * rect.height())
                p.setBrush(QColor(VIOLET))
                p.setPen(QPen(QColor('#E2D8FF'), 1))
                p.drawEllipse(point, 5, 5)
                text(p, QRectF(point.x() + 9, point.y() - 9, 180, 20), name.split('_')[0].upper(), 9, INK)
            text(p, QRectF(22, self.height() - 33, self.width() - 44, 22), 'Supplied 2D reference coordinates · matches recorded in output', 9, MUTED)
            return
        metrics = []

        def walk(value, path=''):
            if isinstance(value, dict):
                for k, v in value.items():
                    if any((s in k.lower() for s in ('secret', 'time', 'signature', 'seal', 'nonce', 'token'))):
                        continue
                    if isinstance(v, (int, float)) and (not isinstance(v, bool)) and math.isfinite(v):
                        metrics.append((path + k, float(v)))
                    elif isinstance(v, dict):
                        walk(v, path + k + '/')
        walk(state)
        if not metrics:
            for output in outputs:
                walk(output)
        if metrics:
            ordered = sorted(metrics, key=lambda row: (not any((s in row[0].lower() for s in ('balance', 'resource', 'reserve', 'pool', 'wallet', 'ru', 'liquidity'))), row[0]))[:6]
            width = self.width() - 44
            row_height = max(22, (self.height() - 90) / len(ordered))
            maximum = max(1, max((abs(v) for _, v in ordered)))
            for i, (key, value) in enumerate(ordered):
                y = 54 + i * row_height
                bar_x = 22 + width * 0.49
                bar_width = width * 0.32
                text(p, QRectF(22, y, width * 0.46, row_height - 2), key[-42:].replace('_', ' '), 9, MUTED)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor('#203747'))
                p.drawRoundedRect(QRectF(bar_x, y + 7, bar_width, 9), 4, 4)
                p.setBrush(QColor((MINT, BLUE, VIOLET)[i % 3]))
                p.drawRoundedRect(QRectF(bar_x, y + 7, bar_width * abs(value) / maximum, 9), 4, 4)
                text(p, QRectF(bar_x + bar_width + 8, y, width * 0.17, row_height - 2), f'{value:,.2f}'.rstrip('0').rstrip('.'), 9, INK, True)
            return
        flags = []

        def flags_walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, bool):
                        flags.append((k, v))
                    elif isinstance(v, dict):
                        flags_walk(v)
        for output in outputs:
            flags_walk(output)
        if not flags:
            flags = [(r['operation'], True) for r in actions]
        if not flags and 'binary' in report:
            flags = [('Goal ' + str(i + 1), bool(b)) for i, b in enumerate(report['binary'])]
        flags = flags[:8]
        width = (self.width() - 44) / max(1, len(flags))
        for i, (key, passed) in enumerate(flags):
            rect = QRectF(22 + i * width, 68, width - 10, 75)
            p.setPen(QPen(QColor('#416272'), 1))
            p.setBrush(QColor('#1C4A3B' if passed else '#44304E'))
            p.drawRoundedRect(rect, 9, 9)
            text(p, rect, '1' if passed else '0', 24, MINT if passed else VIOLET, True, Qt.AlignmentFlag.AlignCenter)
            text(p, QRectF(rect.left(), 150, rect.width(), 45), key.replace('_', ' ')[:30], 8, MUTED, False, Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap)
