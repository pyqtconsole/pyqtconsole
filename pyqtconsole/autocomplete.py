# -*- coding: utf-8 -*-
from qtpy.QtCore import Qt, QObject, QEvent
from qtpy.QtWidgets import QCompleter

from .text import columnize, long_substr


class COMPLETE_MODE(object):
    DROPDOWN = 1
    INLINE = 2


class AutoComplete(QObject):
    def __init__(self, parent):
        super(AutoComplete, self).__init__(parent)
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
        self.update_completion(key)
        return intercepted

    def handle_tab_key(self, event):
        if self.parent()._textCursor().hasSelection():
            return False

        if self.mode == COMPLETE_MODE.DROPDOWN:
            if self.parent().input_buffer().strip():
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

    def init_completion_list(self, words):
        self.completer = QCompleter(words, self)
        self.completer.setCompletionPrefix(self.parent().input_buffer())
        self.completer.setWidget(self.parent().edit)
        self.completer.setCaseSensitivity(Qt.CaseSensitive)
        self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)

        if self.mode == COMPLETE_MODE.DROPDOWN:
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            self.completer.activated.connect(self.insert_completion)
        else:
            self.completer.setCompletionMode(QCompleter.InlineCompletion)

    def trigger_complete(self):
        _buffer = self.parent().input_buffer().strip()
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
            cl = columnize(words, colsep='  |  ')
            self.parent()._insert_output_text(
                '\n\n' + cl + '\n', lf=True, keep_buffer=True)

    def hide_completion_suggestions(self):
        if self.completing():
            self.completer.popup().close()
            return True

    def completing(self):
        if self.mode == COMPLETE_MODE.DROPDOWN:
            return (self.completer.popup() and
                    self.completer.popup().isVisible())
        else:
            return False

    def insert_completion(self, completion):
        _buffer = self.parent().input_buffer().strip()

        # Handling the . operator in object oriented languages so we don't
        # overwrite the . when we are inserting the completion. Its not the .
        # operator If the buffer starts with a . (dot), but something else
        # perhaps terminal specific so do nothing.
        if '.' in _buffer and _buffer[0] != '.':
            idx = _buffer.rfind('.') + 1
            _buffer = _buffer[idx:]

        if self.mode == COMPLETE_MODE.DROPDOWN:
            self.parent().insert_input_text(completion[len(_buffer):])
        elif self.mode == COMPLETE_MODE.INLINE:
            self.parent().clear_input_buffer()
            self.parent().insert_input_text(completion)

            words = self.parent().get_completions(completion)

            if len(words) == 1:
                self.parent().insert_input_text(' ')

    def update_completion(self, key):
        if self.completing():
            _buffer = self.parent().input_buffer()

            if len(_buffer) > 1:
                self.show_completion_suggestions(_buffer)
                self.completer.setCurrentRow(0)
                model = self.completer.completionModel()
                self.completer.popup().setCurrentIndex(model.index(0, 0))
            else:
                self.completer.popup().hide()

    def complete(self):
        if self.completing() and self.mode == COMPLETE_MODE.DROPDOWN:
            index = self.completer.popup().currentIndex()
            model = self.completer.completionModel()
            word = model.itemData(index)[0]
            self.insert_completion(word)
            self.completer.popup().hide()
