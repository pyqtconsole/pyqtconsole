# -*- coding: utf-8 -*-
from .qt.QtCore import QObject


class CommandHistory(QObject):
    def __init__(self, parent):
        super(CommandHistory, self).__init__(parent)
        self._cmd_history = []
        self._idx = 0
        parent.input_applied_signal.connect(self.add)

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

    def dec(self):
        if len(self._cmd_history) and self._idx > 0:
            self._idx -= 1
            self._insert_in_editor(self.current())

    def current(self):
        if len(self._cmd_history):
            return self._cmd_history[self._idx]

    def _insert_in_editor(self, str_):
        self.parent().clear_input_buffer()
        self.parent().insert_input_text(str_)
