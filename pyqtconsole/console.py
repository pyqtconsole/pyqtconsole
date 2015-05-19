# -*- coding: utf-8 -*-
import os

from .qt import QtCore
from .qt.QtWidgets import (QTextEdit, QCompleter)
from .qt.QtGui import QFontMetrics

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
        self._tab_chars = 4 * ' '

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

        self.init_completion_list([])

    # Disable pasting code for the moment
    def insertFromMimeData(self, mime_data):
        return

    def keyPressEvent(self, event):
        key = event.key()
        intercepted = False

        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            intercepted = self.handle_enter_key(event)
        elif key == QtCore.Qt.Key_Space:
            intercepted = self.handle_space_key(event)
        elif key == QtCore.Qt.Key_Backspace:
            intercepted = self.handle_backspace_key(event)
        elif key == QtCore.Qt.Key_Escape:
            pass
        elif key == QtCore.Qt.Key_Home:
            intercepted = self.handle_home_key(event)
        elif key == QtCore.Qt.Key_Tab:
            intercepted = self.handle_tab_key(event)
        elif key == QtCore.Qt.Key_Up:
            intercepted = self.handle_up_key(event)
        elif key == QtCore.Qt.Key_Down:
            intercepted = self.handle_down_key(event)
        elif key == QtCore.Qt.Key_Left:
            intercepted = self.handle_left_key(event)
        elif key == QtCore.Qt.Key_Right:
            pass
        elif key == QtCore.Qt.Key_D:
            intercepted = self.handle_d_key(event)
        elif key == QtCore.Qt.Key_C:
            intercepted = self.handle_d_key(event)
            
        # Make sure that we can't move the cursor outside of the editing buffer
        if not self._in_buffer():
            self._keep_cursor_in_buffer()

        # Call the TextEdit keyPressEvent for the events that are not
        # intercepted
        if not intercepted:
            super(BaseConsole, self).keyPressEvent(event)

            # Show a new list of completion alternatives after the key
            # has been added to the TextEdit
            self._update_completion(key)

            # Append the current buffer to the history
            self._cmd_history[-1] = self._get_buffer()
        else:
            event.accept()
            
        # Regardless of key pressed, if we are completing a word, highlight
        # the first match !
        if self._completing():
            self._highlight_current_completion()

    def handle_enter_key(self, event):
        if self._completing():
            self._complete()
        else:
            self._parse_buffer()
            self._history_index = len(self._cmd_history) - 1

        return True

    def handle_space_key(self, event):
        intercepted = False

        if self._completing():
            self._complete()
            intercepted = True

        return intercepted

    def handle_backspace_key(self, event):
        intercepted = False

        if not self._in_buffer():
            intercepted = True
        else:
            if self._get_buffer().endswith(self._tab_chars):
                for i in range(len(self._tab_chars) - 1):
                    self.textCursor().deletePreviousChar()

        return intercepted

    def handle_tab_key(self, event):
        _buffer = self._get_buffer().strip(' ')

        if len(_buffer):
            self._show_completion_suggestions(_buffer)
        else:
            self._insert_in_buffer(self._tab_chars)

        return True

    def handle_home_key(self, event):
        self._keep_cursor_in_buffer()
        return True
    
    def handle_up_key(self, event):
        self._dec_history_index()
        self._insert_history_entry()
        return True

    def handle_down_key(self, event):
        self._inc_history_index()
        self._insert_history_entry()
        return True

    def handle_left_key(self, event):
        intercepted = False

        if not self._in_buffer():
            intercepted = True

        return intercepted

    def handle_d_key(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self._close()

        return False

    def handle_c_key(self, event):
        intercepted = False
        
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self._handle_ctrl_c()
            intercepted = True

        return intercepted

    def _keep_cursor_in_buffer(self):
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_pos)
        self.setTextCursor(cursor)        
        self.ensureCursorVisible()

    def _in_buffer(self):
        buffer_pos = self.textCursor().position()
        return buffer_pos > self._prompt_pos

    def _insert_prompt(self, prompt):
        cursor = self.textCursor()
        cursor.insertText(prompt)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

    def _insert_welcome_message(self, message):
        self._insert_prompt(message)

    def _get_buffer(self):
        buffer_pos = self.textCursor().position()
        return str(self.toPlainText()[self._prompt_pos:buffer_pos])

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

    def init_completion_list(self, words):
        self.completer = QCompleter(words, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)
        self.completer.activated.connect(self._insert_completion)

    # Asbtract
    def get_completions(self, line):
        return ['No completion support available']

    def _update_completion(self, key):
        if self._completing():
            _buffer = self._get_buffer()

            if len(_buffer) > 1:
                self._show_completion_suggestions(_buffer)
            else:
                self.completer.popup().hide()

    def _show_completion_suggestions(self, _buffer):
        if self.completer.popup().isVisible():
            self.completer.popup().hide()

        words = self.get_completions(_buffer)

        if len(words) == 1:
            self._insert_completion(words[0])
        else:
            self.init_completion_list(words)
            self.completer.setCompletionPrefix(_buffer)

            cr = self.cursorRect()
            sbar_w = self.completer.popup().verticalScrollBar().sizeHint().width()
            popup_width = self.completer.popup().sizeHintForColumn(0) + sbar_w
            cr.setWidth(popup_width)
            self.completer.complete(cr)

    def _completing(self):
        return self.completer.popup().isVisible()

    def _highlight_current_completion(self):
        self.completer.setCurrentRow(0)
        model = self.completer.completionModel()
        self.completer.popup().setCurrentIndex(model.index(0,0))

    def _insert_completion(self, completion):
        _buffer = self._get_buffer()
        cursor = self.textCursor()
        cursor.insertText(completion[len(_buffer):])

    def _complete(self):
        index = self.completer.popup().currentIndex()
        model = self.completer.completionModel()
        word = model.itemData(index)[0]
        self._insert_completion(word)
        self.completer.popup().hide()

    def _parse_buffer(self):
        cmd = self._get_buffer()    
        self.stdin.write(cmd + os.linesep)

        if cmd != os.linesep:
            self._add_history_entry(cmd)

    def _stdout_data_handler(self, data):
        self._insert_prompt(data)

    # Abstract
    def _close(self):
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

    def _close(self):
        self.shell.exit()
        self.close()

    def _handle_ctrl_c(self):
        print('ctrl C')
        self.shell.send_keyboard_interrupt()

    def closeEvent(self, event):
        self._close()
        event.accept()

    def evaluate_buffer(self, _buffer):
        self.shell.set_buffer(_buffer)
        self.stdin.write('eval_buffer\n')

    def get_completions(self, line):
        return self.shell.get_completions(line)

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

