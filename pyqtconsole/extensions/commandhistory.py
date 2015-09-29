# -*- coding: utf-8 -*-
from ..qt import QtCore
from .extension import Extension


class CommandHistory(Extension):
    def __init__(self):
        super(CommandHistory, self).__init__()
        self.parent = None
        self._cmd_history = []
        self._idx = 0

    def install(self, parent):
        self.parent = parent    
        parent.installEventFilter(self)

    def add(self, str_):
        if str_:
            self._cmd_history.append(str_)

        self._idx = len(self._cmd_history)

    def inc(self):
        # index starts at 0 so + 1 to make sure that we are within the
        # limits of the list
        if len(self._cmd_history) and (self._idx + 1) < len(self._cmd_history):
            self._idx += 1
            self._insert_in_editor(self.current())
        else:
            self._insert_in_editor('')

    def dec(self):
        if len(self._cmd_history) and self._idx > 0:
            self._idx -= 1
            self._insert_in_editor(self.current())

    def current(self):
        if len(self._cmd_history):
            return self._cmd_history[self._idx]

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()

            if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                self.add(self.parent._get_buffer())
            elif key == QtCore.Qt.Key_Up:
                self.dec()
            elif key == QtCore.Qt.Key_Down:
                self.inc()

        return False

    def _insert_in_editor(self, str_):
        self.parent.textCursor().clearSelection()
        self.parent._clear_buffer()
        self.parent._keep_cursor_in_buffer()
        self.parent._insert_in_buffer(str_)
