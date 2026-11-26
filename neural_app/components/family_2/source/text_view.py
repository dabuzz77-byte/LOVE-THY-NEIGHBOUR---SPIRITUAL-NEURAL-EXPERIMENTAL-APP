"""Refresh read-only text without stealing the reader's scroll position."""
from PySide6.QtGui import QTextCursor

def update_text(widget, text, *, rich=False, follow=False, reset=False):
    previous = widget.toPlainText()
    if not rich and previous == text:
        return
    if rich and getattr(widget, '_flux_html', None) == text and previous:
        return
    vertical = widget.verticalScrollBar()
    horizontal = widget.horizontalScrollBar()
    top, left = (vertical.value(), horizontal.value())
    selection = widget.textCursor()
    anchor, position = (selection.anchor(), selection.position())
    at_end = vertical.maximum() - top <= 2 and (not selection.hasSelection()) and (not vertical.isSliderDown())
    if rich:
        widget.setHtml(text)
        widget._flux_html = text
    elif previous and text.startswith(previous) and (not reset):
        cursor = QTextCursor(widget.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text[len(previous):])
    else:
        widget.setPlainText(text)
    if not reset:
        limit = max(0, widget.document().characterCount() - 1)
        selection = widget.textCursor()
        selection.setPosition(min(anchor, limit))
        selection.setPosition(min(position, limit), QTextCursor.MoveMode.KeepAnchor)
        widget.setTextCursor(selection)
    vertical.setValue(vertical.maximum() if follow and (at_end or reset) else 0 if reset else top)
    horizontal.setValue(0 if reset else left)
