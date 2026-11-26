"""Lossless binary-layout inversion and exact balanced-ternary translation."""
import re
from routing import balanced_ternary
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPainter, QFont
from PySide6.QtWidgets import QWidget

PRAYER_TEXT = """Our Father in heaven,
hallowed be your name,
your kingdom come,
your will be done,
on earth as in heaven.
Give us today our daily bread.
Forgive us our sins
as we forgive those who sin against us.
Lead us not into temptation
but deliver us from evil.
For the kingdom, the power,
and the glory are yours
now and for ever.
Amen."""

ORIGINAL_LAYOUT = """    1   0 0   1      0   1 1    0
    1                0
    0   1 1   0      1   0 0    1
    0   1 1   0      1   0 0    1
    1                0
    1         1      0          0 ------GENERATE------ = .


    1         1      0          0


    0         0      1          1"""

BINARY_RUN = re.compile(r'(?<![\w.])[01]+(?![\w.]|\.\d)')


def layout_bits(text):
    return ''.join(match[0] for match in BINARY_RUN.finditer(text))


def flip_binary_layout(text):
    if not isinstance(text, str):
        raise ValueError('Enter a text layout')
    flipped = BINARY_RUN.sub(lambda m: m[0].translate(str.maketrans('01', '10')), text)
    original_bits, output_bits = layout_bits(text), layout_bits(flipped)
    rows = []
    for number, line in enumerate(flipped.splitlines(), 1):
        bits = layout_bits(line)
        if bits:
            value = int(bits, 2)
            rows.append({'line': number, 'binary': bits, 'balanced_ternary': balanced_ternary(value)})
    return {
        'original': text, 'flipped': flipped, 'original_bits': original_bits,
        'output_bits': output_bits, 'bit_count': len(output_bits),
        'balanced_ternary': balanced_ternary(int(output_bits, 2)) if output_bits else [],
        'rows': rows,
        'translation': 'Read binary runs left to right, top to bottom; leading zeros retain their grid positions. '
                       'Balanced ternary represents the same integer with digits -1, 0, +1.',
    }


def ternary_text(digits):
    return ' '.join({-1:'−1', 0:'0', 1:'+1'}[digit] for digit in digits)


class BinaryLayoutGrid(QWidget):
    """Spatial bit positions preserved; every colored square is a real input bit."""
    def __init__(self):
        super().__init__()
        self.positions = []
        self.columns = self.rows = 1
        self.setMinimumHeight(150)

    def set_layout(self, text):
        self.positions = []
        lines = text.expandtabs(4).splitlines()
        for y, line in enumerate(lines):
            for match in BINARY_RUN.finditer(line):
                for offset, value in enumerate(match[0]):
                    self.positions.append((match.start()+offset, y, value))
        self.columns = max((x+1 for x,y,v in self.positions), default=1)
        self.rows = max(len(lines), 1)
        self.update()

    def sizeHint(self):
        return QSize(620, 220)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#101c29'))
        cell = min((self.width()-20)/self.columns, (self.height()-20)/self.rows, 28)
        side = max(1, int(cell*.88))
        painter.setFont(QFont('Consolas', max(6, int(cell*.5))))
        for x,y,value in self.positions:
            px, py = int(10+x*cell), int(10+y*cell)
            painter.fillRect(px, py, side, side, QColor('#64dfb2' if value=='1' else '#364c68'))
            painter.setPen(QColor('#102028' if value=='1' else '#c6d3e5'))
            if side >= 10:
                painter.drawText(px, py, side, side, Qt.AlignmentFlag.AlignCenter, value)
