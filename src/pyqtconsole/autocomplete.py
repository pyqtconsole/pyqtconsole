from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtGui import QKeyEvent
from qtpy.QtCore import QEvent, QObject, Qt
from qtpy.QtWidgets import QCompleter

from .text import columnize, long_substr

if TYPE_CHECKING:
    from .console import BaseConsole


class CompleteMode(Enum):
    DROPDOWN = 1
    INLINE = 2


class AutoComplete(QObject):
    def __init__(self, console: "BaseConsole"):
        super().__init__(console)
        self.mode = CompleteMode.INLINE
        self.completer: QCompleter
        self._last_key = None
        self._console = console  # Use instead of `parent()` to assist type hinting

        console.edit.installEventFilter(self)
        self.init_completion_list([])

    def eventFilter(self, widget: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:  # type: ignore
            return bool(self.key_pressed_handler(event))  # type: ignore
        return False

    def key_pressed_handler(self, event: QKeyEvent) -> bool:
        intercepted = False
        key = event.key()

        if key == Qt.Key.Key_Tab:
            intercepted = self.handle_tab_key(event)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            intercepted = self.handle_complete_key(event)
        elif key == Qt.Key.Key_Escape:
            intercepted = self.hide_completion_suggestions()

        self._last_key = key
        return intercepted

    def handle_tab_key(self, event: QEvent) -> bool:
        if self._console._textCursor().hasSelection():
            return False

        if self.mode == CompleteMode.DROPDOWN:
            if self._console.input_buffer().split("\n")[-1].strip():
                if self.completing():
                    self.complete()
                else:
                    self.trigger_complete()

                event.accept()
                return True

        elif self.mode == CompleteMode.INLINE:
            if self._last_key == Qt.Key.Key_Tab:
                self.trigger_complete()

            event.accept()
            return True

        return False

    def handle_complete_key(self, event: QEvent) -> bool:
        if self.completing():
            self.complete()
            event.accept()
            return True

        return False

    def _get_word_being_completed(self, _buffer: str) -> str:
        """Extract the word currently being completed from the buffer.

        Returns the partial word after the last separator (space or dot).
        Returns empty string if buffer ends with a separator.
        """
        word_being_completed = _buffer.strip()

        # Check if buffer ends with a separator - if so, we're starting fresh
        if _buffer.endswith(" ") or _buffer.endswith("."):
            word_being_completed = ""
        # Check for . operator (attribute access)
        elif "." in _buffer and not _buffer.startswith("."):
            idx = _buffer.rfind(".") + 1
            word_being_completed = _buffer[idx:].strip()
        # Check for space separator (e.g., "from os import abc")
        elif " " in _buffer:
            idx = _buffer.rfind(" ") + 1
            word_being_completed = _buffer[idx:].strip()

        return word_being_completed

    def init_completion_list(self, words: list[str]) -> None:
        # Create a new completer (old one will be garbage collected)
        self.completer = QCompleter(words, self)

        # Extract just the word being completed to use as prefix
        _buffer = self._console.input_buffer()
        word_being_completed = self._get_word_being_completed(_buffer)

        self.completer.setCompletionPrefix(word_being_completed)
        self.completer.setWidget(self._console.edit)
        self.completer.setCaseSensitivity(Qt.CaseSensitive)  # type: ignore
        self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)  # type: ignore

        if self.mode == CompleteMode.DROPDOWN:
            self.completer.setCompletionMode(QCompleter.PopupCompletion)  # type: ignore
            self.completer.activated[str].connect(self.insert_completion)  # type: ignore
        else:
            self.completer.setCompletionMode(QCompleter.InlineCompletion)  # type: ignore

    def trigger_complete(self) -> None:
        _buffer = self._console.input_buffer()
        self.show_completion_suggestions(_buffer)

    def show_completion_suggestions(self, _buffer: str) -> None:
        words = self._console.get_completions(_buffer)

        # No words to show, just return
        if len(words) == 0:
            return

        # Close any popups before creating a new one
        if self.completer.popup():
            self.completer.popup().close()  # type: ignore

        self.init_completion_list(words)

        leastcmn = long_substr(words)
        # Only insert the common substring if it's not empty
        # This handles "from os import " where there's no partial word yet
        if leastcmn:
            self.insert_completion(leastcmn)

        # If only one word to complete, just return and don't display options
        if len(words) == 1:
            return

        if self.mode == CompleteMode.DROPDOWN:
            cr = self._console.edit.cursorRect()
            sbar_w = self.completer.popup().verticalScrollBar()  # type: ignore
            popup_width = self.completer.popup().sizeHintForColumn(0)  # type: ignore
            popup_width += sbar_w.sizeHint().width()
            cr.setWidth(popup_width)
            self.completer.complete(cr)
        elif self.mode == CompleteMode.INLINE:
            cl = columnize(words, colsep="  |  ")
            self._console._insert_output_text(
                "\n\n" + cl + "\n", lf=True, keep_buffer=True
            )

    def hide_completion_suggestions(self) -> bool:
        if self.completing():
            self.completer.popup().close()  # type: ignore
            return True

        return False

    def completing(self) -> bool:
        if self.mode == CompleteMode.DROPDOWN:
            return self.completer.popup() and self.completer.popup().isVisible()  # type: ignore
        else:
            return False

    def insert_completion(self, completion: str) -> None:
        # Close the popup first if it's visible
        if self.completing():
            self.completer.popup().hide()  # type: ignore

        _buffer = self._console.input_buffer()
        word_being_completed = self._get_word_being_completed(_buffer)

        if self.mode == CompleteMode.DROPDOWN:
            # If we have a partial word, remove it first before inserting
            if len(word_being_completed) > 0:
                # Remove the partial word by moving cursor back and deleting
                cursor = self._console._textCursor()
                for _ in range(len(word_being_completed)):
                    cursor.deletePreviousChar()

            # Insert the full completion word
            self._console.insert_input_text(completion)
        elif self.mode == CompleteMode.INLINE:
            # Preserve the prefix before the word being completed
            _buffer_stripped = _buffer.strip()
            prefix_len = len(_buffer_stripped) - len(word_being_completed)
            prefix = _buffer_stripped[:prefix_len]

            # If original buffer ends with space and we have no partial word,
            # the prefix should include that space for proper reconstruction
            if len(word_being_completed) == 0 and _buffer.endswith(" "):
                prefix += " "

            self._console.clear_input_buffer()
            self._console.insert_input_text(prefix + completion)

            # Get completions for the full completed line
            words = self._console.get_completions(prefix + completion)

            if len(words) == 1:
                self._console.insert_input_text(" ")

    def complete(self) -> None:
        if self.completing() and self.mode == CompleteMode.DROPDOWN:
            index = self.completer.popup().currentIndex()  # type: ignore
            model = self.completer.completionModel()
            word = model.itemData(index)[0]
            self.insert_completion(word)
