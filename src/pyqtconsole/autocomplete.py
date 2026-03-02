from qtpy.QtCore import QEvent, QObject, Qt
from qtpy.QtWidgets import QCompleter

from .text import columnize, long_substr


class COMPLETE_MODE:
    DROPDOWN = 1
    INLINE = 2


class AutoComplete(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.mode = COMPLETE_MODE.INLINE
        self.completer = None
        self._last_key = None

        parent.edit.installEventFilter(self)
        self.init_completion_list([])

    def eventFilter(self, widget, event):
        if event.type() == QEvent.KeyPress:
            return bool(self.key_pressed_handler(event))
        return False

    def key_pressed_handler(self, event):
        intercepted = False
        key = event.key()

        if key == Qt.Key_Tab:
            intercepted = self.handle_tab_key(event)
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            intercepted = self.handle_complete_key(event)
        elif key == Qt.Key_Escape:
            intercepted = self.hide_completion_suggestions()

        self._last_key = key
        return intercepted

    def handle_tab_key(self, event):
        if self.parent()._textCursor().hasSelection():
            return False

        if self.mode == COMPLETE_MODE.DROPDOWN:
            if self.parent().input_buffer().split("\n")[-1].strip():
                if self.completing():
                    self.complete()
                else:
                    self.trigger_complete()

                event.accept()
                return True

        elif self.mode == COMPLETE_MODE.INLINE:
            if self._last_key == Qt.Key_Tab:
                self.trigger_complete()

            event.accept()
            return True

    def handle_complete_key(self, event):
        if self.completing():
            self.complete()
            event.accept()
            return True

    def _get_word_being_completed(self, _buffer):
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

    def init_completion_list(self, words):
        # Create a new completer (old one will be garbage collected)
        self.completer = QCompleter(words, self)

        # Extract just the word being completed to use as prefix
        _buffer = self.parent().input_buffer()
        word_being_completed = self._get_word_being_completed(_buffer)

        self.completer.setCompletionPrefix(word_being_completed)
        self.completer.setWidget(self.parent().edit)
        self.completer.setCaseSensitivity(Qt.CaseSensitive)
        self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)

        if self.mode == COMPLETE_MODE.DROPDOWN:
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            self.completer.activated[str].connect(self.insert_completion)
        else:
            self.completer.setCompletionMode(QCompleter.InlineCompletion)

    def trigger_complete(self):
        _buffer = self.parent().input_buffer()
        self.show_completion_suggestions(_buffer)

    def show_completion_suggestions(self, _buffer):
        words = self.parent().get_completions(_buffer)

        # No words to show, just return
        if len(words) == 0:
            return

        # Close any popups before creating a new one
        if self.completer.popup():
            self.completer.popup().close()

        self.init_completion_list(words)

        leastcmn = long_substr(words)
        # Only insert the common substring if it's not empty
        # This handles "from os import " where there's no partial word yet
        if leastcmn:
            self.insert_completion(leastcmn)

        # If only one word to complete, just return and don't display options
        if len(words) == 1:
            return

        if self.mode == COMPLETE_MODE.DROPDOWN:
            cr = self.parent().edit.cursorRect()
            sbar_w = self.completer.popup().verticalScrollBar()
            popup_width = self.completer.popup().sizeHintForColumn(0)
            popup_width += sbar_w.sizeHint().width()
            cr.setWidth(popup_width)
            self.completer.complete(cr)
        elif self.mode == COMPLETE_MODE.INLINE:
            cl = columnize(words, colsep="  |  ")
            self.parent()._insert_output_text(
                "\n\n" + cl + "\n", lf=True, keep_buffer=True
            )

    def hide_completion_suggestions(self):
        if self.completing():
            self.completer.popup().close()
            return True

    def completing(self):
        if self.mode == COMPLETE_MODE.DROPDOWN:
            return self.completer.popup() and self.completer.popup().isVisible()
        else:
            return False

    def insert_completion(self, completion):
        # Close the popup first if it's visible
        if self.completing():
            self.completer.popup().hide()

        _buffer = self.parent().input_buffer()
        word_being_completed = self._get_word_being_completed(_buffer)

        if self.mode == COMPLETE_MODE.DROPDOWN:
            # If we have a partial word, remove it first before inserting
            if len(word_being_completed) > 0:
                # Remove the partial word by moving cursor back and deleting
                cursor = self.parent()._textCursor()
                for _ in range(len(word_being_completed)):
                    cursor.deletePreviousChar()

            # Insert the full completion word
            self.parent().insert_input_text(completion)
        elif self.mode == COMPLETE_MODE.INLINE:
            # Preserve the prefix before the word being completed
            _buffer_stripped = _buffer.strip()
            prefix_len = len(_buffer_stripped) - len(word_being_completed)
            prefix = _buffer_stripped[:prefix_len]

            # If original buffer ends with space and we have no partial word,
            # the prefix should include that space for proper reconstruction
            if len(word_being_completed) == 0 and _buffer.endswith(" "):
                prefix += " "

            self.parent().clear_input_buffer()
            self.parent().insert_input_text(prefix + completion)

            # Get completions for the full completed line
            words = self.parent().get_completions(prefix + completion)

            if len(words) == 1:
                self.parent().insert_input_text(" ")

    def complete(self):
        if self.completing() and self.mode == COMPLETE_MODE.DROPDOWN:
            index = self.completer.popup().currentIndex()
            model = self.completer.completionModel()
            word = model.itemData(index)[0]
            self.insert_completion(word)
