# -*- coding: utf-8 -*-
import os

from .qt import QtCore
from .qt.QtWidgets import (QTextEdit, QCompleter)
from .qt.QtGui import (QTextCursor, QFontMetrics)

from .interpreter import PythonConsoleProxy
from .stream import Stream
from .syntaxhighlighter import PythonHighlighter

class BaseConsole(QTextEdit):
    def __init__(self, parent = None):
        super(BaseConsole, self).__init__(parent)
        self._buffer_pos = 0
        self._prompt_pos = 0
        self._history_size = 100
        self._cmd_history = ['']
        self._history_index = 1
        self._prev_buffer = ''

        self.stdin = Stream()
        self.stdout = Stream()
        self.stdout.write_event.connect(self._stdout_data_handler)

        font = self.document().defaultFont()
        font.setFamily("Courier New")
        font_width = QFontMetrics(font).width('M')
        self.document().setDefaultFont(font)
        geometry = self.geometry()
        geometry.setWidth(font_width*80+20)
        geometry.setHeight(font_width*40)
        self.setGeometry(geometry)
        self.resize(font_width*80+20, font_width*40)

    def set_completion_list(self, _words):
        self.completer = QCompleter(_words, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)

    def keyPressEvent(self, event):
        key = event.key()
        intercepted = False

        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self._parse_buffer()
            self._history_index = len(self._cmd_history) - 1
            intercepted = True

        elif key == QtCore.Qt.Key_Backspace:
            if not self._in_buffer():
                intercepted = True

        elif key == QtCore.Qt.Key_Escape:
            pass
        elif key == QtCore.Qt.Key_Tab:
            self._show_completion_suggestions()
            intercepted = True
        elif key == QtCore.Qt.Key_Up:
            self._dec_history_index()
            self._insert_history_entry()
            intercepted = True
        elif key == QtCore.Qt.Key_Down:
            self._inc_history_index()
            self._insert_history_entry()
            intercepted = True
        elif key == QtCore.Qt.Key_Left:
            if not self._in_buffer():
                intercepted = True
        elif key == QtCore.Qt.Key_Right:
            pass
        elif key == QtCore.Qt.Key_D:
            if event.modifiers() == QtCore.Qt.ControlModifier:
                self._close_cmd()
        else:
            if not self._in_buffer():
                self._keep_cursor_in_buffer()

        if not intercepted:
            event.ignore()
            super(BaseConsole, self).keyPressEvent(event)
            self._cmd_history[-1] = self._get_buffer()
        else:
            event.accept()
            return

    def _keep_cursor_in_buffer(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

    def _in_buffer(self):
        buffer_pos = self.textCursor().position()
        return buffer_pos > self._prompt_pos

    def _insert_prompt(self, prompt):
        self._keep_cursor_in_buffer()
        cursor = self.textCursor()
        cursor.insertText(prompt)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

    def _insert_welcome_message(self, message):
        self._insert_prompt(message)

    def _get_buffer(self):
        buffer_pos = self.textCursor().position()
        return self.toPlainText()[self._prompt_pos:buffer_pos]

    def _clear_buffer(self):
        self.textCursor().clearSelection()
        buffer_pos = self.textCursor().position()
        
        for i in range(self._prompt_pos,buffer_pos):
            self.textCursor().deletePreviousChar()

    def _insert_in_buffer(self, text):
        self.ensureCursorVisible()
        self.textCursor().insertText(text)

    def _inc_history_index(self):
        if self._history_index < (len(self._cmd_history) -1):
            self._history_index += 1
        else:
            self._history_index = len(self._cmd_history) -1

    def _dec_history_index(self):
        if self._history_index > 0:
            self._history_index -= 1
        else:
            self._history_index = 0

    def _add_history_entry(self, cmd):
        if len(self._cmd_history) <= self._history_size:
            self._cmd_history.append(cmd)

    def _insert_history_entry(self):
        if self._history_index < len(self._cmd_history):
            self.textCursor().clearSelection()
            cmd = self._cmd_history[self._history_index]
            self._clear_buffer()
            self._keep_cursor_in_buffer()
            self._insert_in_buffer(cmd)
            
    def _show_completion_suggestions(self):
        pass
        # self._prev_buffer = self._get_buffer()
        # self.completer.setCompletionPrefix(self._get_buffer())
        # # Just sends new line, to get the terminal back
        # self.stdin.write(os.linesep)

    def _parse_buffer(self):
        cmd = self._get_buffer()
        self.stdin.write(cmd + os.linesep)

        if cmd != os.linesep:
            self._add_history_entry(cmd)

    def _stdout_data_handler(self, data):
        self._insert_prompt(data)

        if self._prev_buffer:
            self._insert_in_buffer(self._prev_buffer)
            self._prev_buffer = ''

    def _close_cmd(self):
        self.stdin.write('EOF\n')

    def _evaluate_buffer(self):
        _buffer = self.sender().parent().parent().toPlainText()
        self.evaluate_buffer(_buffer)

    # Abstract
    def evaluate_buffer(self, _buffer):
        print(_buffer)


class PythonConsole(BaseConsole):
    def __init__(self, parent = None, local = {}):
        super(PythonConsole, self).__init__(parent)
        self.highlighter = PythonHighlighter(self.document())
        self.shell = PythonConsoleProxy(self.stdin, self.stdout, local = local)

    def _close_cmd(self):
        self.shell.exit()
        self.close()

    def closeEvent(self, event):
        self._close_cmd()
        event.accept()

    def evaluate_buffer(self, _buffer):
        self.shell.set_buffer(_buffer)
        self.stdin.write('eval_buffer\n')

    def push_local_ns(self, name, value):
        self.shell.local_ns[name] = value

    def repl_nonblock(self):
        return self.shell.repl_nonblock()

    def repl(self):
        return self.shell.repl()

# if __name__ == '__main__':
#     import sys

#     from threading import Thread
#     from .qt.QtWidgets import (QApplication)
    
#     app = QApplication([])

#     console = PythonConsole()
#     console.show()
    
#     ct = Thread(target = console.repl)
#     ct.start()

#     sys.exit(app.exec_())
    
