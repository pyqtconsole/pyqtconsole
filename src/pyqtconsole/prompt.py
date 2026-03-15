from collections.abc import Callable

from PySide6.QtGui import QPaintEvent, QTextBlock
from qtpy.QtCore import QRect, Qt
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import QPlainTextEdit, QWidget

from .highlighter import PromptHighlighter


class PromptArea(QWidget):
    """Widget that displays the prompts on the left of the input area."""

    def __init__(
        self,
        edit: QPlainTextEdit,
        get_text: Callable[[int], str],
        highlighter: PromptHighlighter,
    ):
        super().__init__(edit)
        self.setFixedWidth(0)
        self.edit = edit
        self.get_text = get_text
        self.highlighter = highlighter
        edit.updateRequest.connect(self.updateContents)

    def paintEvent(self, event: QPaintEvent) -> None:
        edit = self.edit
        height = edit.fontMetrics().height()
        block = edit.firstVisibleBlock()
        count = block.blockNumber()
        painter = QPainter(self)
        painter.fillRect(event.rect(), edit.palette().base())
        first = True
        while block.isValid():
            count += 1
            block_top = (
                edit.blockBoundingGeometry(block).translated(edit.contentOffset()).top()
            )
            if not block.isVisible() or block_top > event.rect().bottom():
                break
            rect = QRect(0, int(block_top), self.width(), height)
            self.draw_block(painter, rect, block, first)
            first = False
            block = block.next()
        painter.end()
        super().paintEvent(event)

    def updateContents(self, rect: QWidget, scroll: int) -> None:
        if scroll:
            self.scroll(0, scroll)
        else:
            self.update()

    def adjust_width(self, new_text: str) -> None:
        width = calc_text_width(self.edit, new_text)
        if width > self.width():
            self.setFixedWidth(width)

    def draw_block(
        self, painter: QPainter, rect: QRect, block: QTextBlock, first: bool
    ) -> None:
        """Draw the info corresponding to a given block (text line) of the text
        document."""
        pen = painter.pen()
        text = self.get_text(block.blockNumber())

        default = self.edit.currentCharFormat()
        formats = [default] * len(text)
        painter.setFont(self.edit.font())

        for index, length, format in self.highlighter.highlight(text):
            formats[index : index + length] = [format] * length

        for idx, (_char, format) in enumerate(zip(text, formats, strict=True)):
            rpos = len(text) - idx - 1
            pen.setColor(format.foreground().color())
            painter.setPen(pen)
            painter.drawText(rect, Qt.AlignRight, text[idx] + " " * rpos)  # type: ignore


def calc_text_width(widget: QWidget, text: str) -> int:
    """Estimate the width that the given text would take within the widget."""
    return int(
        widget.fontMetrics().width(text)  # type: ignore
        + widget.fontMetrics().width("M")  # type: ignore
        + widget.contentsMargins().left()
        + widget.contentsMargins().right()
    )
