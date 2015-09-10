# -*- coding: utf-8 -*-
import os
import threading
import ctypes
import time


from .qt import QtCore
from .qt.QtWidgets import (QTextEdit, QCompleter)
from .qt.QtGui import (QFontMetrics, QTextCursor)

from .interpreter import PythonInterpreter
from .stream import Stream
from .syntaxhighlighter import PythonHighlighter
from .text import columnize, long_substr


class COMPLETE_MODE(object):
    DROPDOWN = '1'
    INLINE = '2'


class BaseConsole(QTextEdit):

    def __init__(self, parent = None):
        super(BaseConsole, self).__init__(parent)
        self._buffer_pos = 0
        self._prompt_pos = 0
        self._history_size = 100
        self._cmd_history = []
        self._history_index = 1
        self._tab_chars = 4 * ' '
        self._ctrl_d_exits = False
        self._complete_mode = COMPLETE_MODE.INLINE
        self._copy_buffer = ''

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

    def insertFromMimeData(self, mime_data):
        if mime_data.hasText():
            self._keep_cursor_in_buffer()
            self.evaluate_buffer(mime_data.text(), echo_lines = True)

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
            intercepted = self.handle_c_key(event)

        # Make sure that we can't move the cursor outside of the editing buffer
        # If outside buffer and no modifiers used move the cursor back into to
        # the buffer
        if not event.modifiers() and not self._in_buffer():
            self._keep_cursor_in_buffer()

        # Call the TextEdit keyPressEvent for the events that are not
        # intercepted
        if not intercepted:
            super(BaseConsole, self).keyPressEvent(event)

            # Show a new list of completion alternatives after the key
            # has been added to the TextEdit
            self._update_completion(key)

            # Append the current buffer to the history
            if self._cmd_history:
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
            # Move to end of line before parsing the current line
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.EndOfLine)
            self.setTextCursor(cursor)
            self._parse_buffer()

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

        if self._complete_mode == COMPLETE_MODE.DROPDOWN:
            if len(_buffer):
                self._show_completion_suggestions(_buffer)
            else:
                self._insert_in_buffer(self._tab_chars)
        else:
            self._show_completion_suggestions(_buffer)

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
        if event.modifiers() == QtCore.Qt.ControlModifier and self._ctrl_d_exits:
            self._close()
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            msg = "\nCan't use CTRL-D to exit, you have to exit the "
            msg += "application !\n"
            self._insert_prompt(msg)

        return False

    def handle_c_key(self, event):
        intercepted = False

        # Do not intercept so that the event is forwarded to the base class
        # can handle it. In this case for copy that is: CTRL-C
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self._handle_ctrl_c()

        return intercepted

    def _keep_cursor_in_buffer(self):
        cursor = self.textCursor()
        cursor.setPosition(self._prompt_pos)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _in_buffer(self):
        buffer_pos = self.textCursor().position()
        return buffer_pos > self._prompt_pos

    def _insert_prompt(self, prompt, lf=False, keep_buffer=False):
        if keep_buffer:
            self._copy_buffer = self._get_buffer()

        cursor = self.textCursor()
        cursor.insertText(prompt)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

        if lf:
            self.stdin.write(os.linesep)

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
            self._cmd_history.append('')

    def _insert_history_entry(self):
        if self._history_index < len(self._cmd_history):
            self.textCursor().clearSelection()
            cmd = self._cmd_history[self._history_index]
            self._clear_buffer()
            self._keep_cursor_in_buffer()
            self._insert_in_buffer(cmd)

    def init_completion_list(self, words):
        self.completer = QCompleter(words, self)
        self.completer.setCompletionPrefix(self._get_buffer())
        self.completer.setWidget(self)

        if self._complete_mode == COMPLETE_MODE.DROPDOWN:
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
            self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)
            self.completer.activated.connect(self._insert_completion)
        else:
            self.completer.setCompletionMode(QCompleter.InlineCompletion)
            self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
            self.completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)

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
        words = self.get_completions(_buffer)

        # No words to show, just return
        if len(words) == 0:
            return

        # Close any popups before creating a new one
        if self.completer.popup():
            self.completer.popup().close()

        self.init_completion_list(words)

        leastcmn = long_substr(words)
        self._insert_completion(leastcmn)

        # If only one word to complete, just return and don't display options
        if len(words) == 1:
            return

        if self._complete_mode == COMPLETE_MODE.DROPDOWN:
            cr = self.cursorRect()
            sbar_w = self.completer.popup().verticalScrollBar()
            popup_width = self.completer.popup().sizeHintForColumn(0)
            popup_width += sbar_w.sizeHint().width()
            cr.setWidth(popup_width)
            self.completer.complete(cr)

        elif self._complete_mode == COMPLETE_MODE.INLINE:
            cl = columnize(words, colsep = '  |  ')
            self._insert_prompt('\n\n' + cl + '\n', lf=True, keep_buffer = True)

    def _completing(self):
        if self._complete_mode == COMPLETE_MODE.DROPDOWN:
            return self.completer.popup() and self.completer.popup().isVisible()
        else:
            return False

    def _highlight_current_completion(self):
        self.completer.setCurrentRow(0)
        model = self.completer.completionModel()
        self.completer.popup().setCurrentIndex(model.index(0,0))

    def _insert_completion(self, completion):
        _buffer = self._get_buffer()
        cursor = self.textCursor()

        # Handling the . operator in object oriented languages so we don't
        # overwrite the . when we are inserting the completion. Its not the .
        # operator If the buffer starts with a . (dot), but something else
        # perhaps terminal specific so do nothing.
        if '.' in _buffer and _buffer[0] != '.':
            idx = _buffer.rfind('.') + 1
            _buffer = _buffer[idx:]

        cursor.insertText(completion[len(_buffer):])

    def _complete(self):
        if self._complete_mode == COMPLETE_MODE.DROPDOWN:
            index = self.completer.popup().currentIndex()
            model = self.completer.completionModel()
            word = model.itemData(index)[0]
            self._insert_completion(word)
            self.completer.popup().hide()

    def set_auto_complete_mode(self, mode):
        self._complete_mode = mode

    def _parse_buffer(self):
        cmd = self._get_buffer()
        self.stdin.write(cmd + os.linesep)

        if cmd != '':
            self._history_index = len(self._cmd_history)
            self._add_history_entry(cmd)

    def _stdout_data_handler(self, data):
        self._insert_prompt(data)

        if len(self._copy_buffer) > 0:
            self._insert_in_buffer(self._copy_buffer)
            self._copy_buffer = ''

    # Abstract
    def _close(self):
        self.stdin.write('EOF\n')

    def _evaluate_buffer(self):
        _buffer = str(self.sender().parent().parent().toPlainText())
        self.evaluate_buffer(_buffer)

    # Abstract
    def evaluate_buffer(self, _buffer, echo_lines = False):
        print(_buffer)

    def set_tab(self, chars):
        self._tab_chars = chars

    def ctrl_d_exits_console(self, b):
        self._ctrl_d_exits = b

    # Abstract
    def _handle_ctrl_c(self):
        pass

class PythonConsole(BaseConsole):
    def __init__(self, parent = None, local = {}):
        super(PythonConsole, self).__init__(parent)
        self.highlighter = PythonHighlighter(self.document())
        self.interpreter = PythonInterpreter(self.stdin, self.stdout, local=local)
        self._complete_mode = COMPLETE_MODE.DROPDOWN
        self._thread = None

    def _close(self):
        self.interpreter.exit()
        self.close()

    def _handle_ctrl_c(self):
        _id = threading.current_thread().ident
        
        if self._thread:
            _id = self._thread.ident

        if _id:
            self.stdout.write('\n\nKeyboardInterrupt')
            _id, exobj = ctypes.c_long(_id), ctypes.py_object(KeyboardInterrupt)
            ctypes.pythonapi.PyThreadState_SetAsyncExc(_id, exobj)
            time.sleep(0.1)            
            self.stdin.write('\n\n')
        
    def closeEvent(self, event):
        self._close()
        event.accept()

    def evaluate_buffer(self, _buffer, echo_lines = False):
        self.interpreter.set_buffer(_buffer)
        if echo_lines:
            self.stdin.write('%%eval_lines\n')
        else:
            self.stdin.write('%%eval_buffer\n')

    def get_completions(self, line):
        return self.interpreter.get_completions(line)

    def push_local_ns(self, name, value):
        self.interpreter.local_ns[name] = value

    def repl_nonblock(self):
        return self.interpreter.repl_nonblock()

    def repl(self):
        return self.interpreter.repl()

    def eval_in_thread(self):
        self._thread = threading.Thread(target = self.repl)
        self._thread.start()
        return self._thread
