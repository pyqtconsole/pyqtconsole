# -*- coding: utf-8 -*-
import threading
import ctypes

from .qt.QtCore import Qt, Signal, QThread, Slot
from .qt.QtWidgets import QTextEdit, QApplication
from .qt.QtGui import QFontMetrics, QTextCursor, QClipboard

from .interpreter import PythonInterpreter
from .stream import Stream
from .syntaxhighlighter import PythonHighlighter
from .extensions.extension import ExtensionManager
from .extensions.commandhistory import CommandHistory
from .extensions.autocomplete import AutoComplete, COMPLETE_MODE

try:
    import jedi
    from jedi import settings
    settings.case_insensitive_completion = False
except ImportError:
    jedi = None


class BaseConsole(QTextEdit):
    key_pressed_signal = Signal(object)
    post_key_pressed_signal = Signal(object)
    set_complete_mode_signal = Signal(int)

    def __init__(self, parent = None):
        super(BaseConsole, self).__init__(parent)
        self._prompt_pos = 0
        self._tab_chars = 4 * ' '
        self._ctrl_d_exits = False
        self._copy_buffer = ''

        self._last_input = ''
        self._more = False
        self._current_line = 0

        self._ps1 = 'IN [%s]: '
        self._ps2 = '...: '
        self._ps = self._ps1 % self._current_line

        self.stdin = Stream()
        self.stdout = Stream()
        self.stdout.write_event.connect(self._stdout_data_handler)
        self.stdout.close_event.connect(self._close)

        font = self.document().defaultFont()
        font.setFamily("Courier New")
        font_width = QFontMetrics(font).width('M')
        self.document().setDefaultFont(font)
        geometry = self.geometry()
        geometry.setWidth(font_width*80+20)
        geometry.setHeight(font_width*40)
        self.setGeometry(geometry)
        self.resize(font_width*80+20, font_width*40)
        self.setReadOnly(True)
        self.setTextInteractionFlags(
            Qt.TextSelectableByMouse |
            Qt.TextSelectableByKeyboard)

        self._key_event_handlers = self._get_key_event_handlers()

        self.extensions = ExtensionManager(self)
        self.extensions.install(CommandHistory)
        if jedi is not None:
            self.extensions.install(AutoComplete)

        self._show_ps()

    def _update_ps(self, _more):
        # We need to show the more prompt of the input was incomplete
        # If the input is complete increase the input number and show
        # the in prompt
        if not _more:
            self._ps = self._ps1 % self._current_line
        else:
            self._ps = (len(self._ps) - len(self._ps2)) * ' ' + self._ps2

    @Slot(bool)
    def _finish_command(self, executed):
        if executed and self._last_input != '\n':
            self._current_line += 1
        self._more = False
        self._update_ps(self._more)
        self._show_ps()

    def _show_ps(self):
        self.stdout.write(self._ps)

    def _get_key_event_handlers(self):
        return {
            Qt.Key_Return:      self.handle_enter_key,
            Qt.Key_Enter:       self.handle_enter_key,
            Qt.Key_Backspace:   self.handle_backspace_key,
            Qt.Key_Home:        self.handle_home_key,
            Qt.Key_Tab:         self.handle_tab_key,
            Qt.Key_Up:          self.handle_up_key,
            Qt.Key_Down:        self.handle_down_key,
            Qt.Key_Left:        self.handle_left_key,
            Qt.Key_D:           self.handle_d_key,
            Qt.Key_C:           self.handle_c_key,
            Qt.Key_V:           self.handle_v_key,
        }

    def insertFromMimeData(self, mime_data):
        if mime_data and mime_data.hasText():
            self.insert_text(mime_data.text())

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Selection)
            self.insertFromMimeData(mime_data)
            event.accept()
        else:
            super(BaseConsole, self).mousePressEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        event.ignore()

        self.key_pressed_signal.emit(event)

        handler = self._key_event_handlers.get(key)
        intercepted = handler and handler(event)

        # Make sure that we can't move the cursor outside of the editing buffer
        # If outside buffer and no modifiers used move the cursor back into to
        # the buffer
        if not event.modifiers() & Qt.ControlModifier:
            self._keep_cursor_in_buffer()

            if not intercepted and event.text():
                intercepted = True
                self.insertPlainText(event.text())

        # Call the TextEdit keyPressEvent for the events that are not
        # intercepted
        if not intercepted:
            super(BaseConsole, self).keyPressEvent(event)
        else:
            event.accept()

        self.post_key_pressed_signal.emit(event)

    def handle_enter_key(self, event):
        if not event.isAccepted():
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.EndOfLine)
            self.setTextCursor(cursor)
            self._parse_buffer()
            return True

    def handle_backspace_key(self, event):
        if self._cursor_offset() >= 1:
            if self._get_buffer().endswith(self._tab_chars):
                for i in range(len(self._tab_chars) - 1):
                    self.textCursor().deletePreviousChar()
            else:
                self.textCursor().deletePreviousChar()
        return True

    def handle_tab_key(self, event):
        if not event.isAccepted():
            self._insert_in_buffer(self._tab_chars)

        return True

    def handle_home_key(self, event):
        select = event.modifiers() & Qt.ShiftModifier
        self._move_cursor(self._prompt_pos, select)
        return True

    def handle_up_key(self, event):
        return True

    def handle_down_key(self, event):
        return True

    def handle_left_key(self, event):
        intercepted = self._cursor_offset() < 1
        return intercepted

    def handle_d_key(self, event):
        if event.modifiers() == Qt.ControlModifier and self._ctrl_d_exits:
            self.exit()
        elif event.modifiers() == Qt.ControlModifier:
            msg = "\nCan't use CTRL-D to exit, you have to exit the "
            msg += "application !\n"
            self._insert_prompt(msg)

        return False

    def handle_c_key(self, event):
        intercepted = False

        # Do not intercept so that the event is forwarded to the base class
        # can handle it. In this case for copy that is: CTRL-C
        if event.modifiers() == Qt.ControlModifier:
            self._handle_ctrl_c()

        return intercepted

    def handle_v_key(self, event):
        if event.modifiers() == Qt.ControlModifier:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Clipboard)
            self.insertFromMimeData(mime_data)
            return True
        return False

    def _move_cursor(self, position=None, select=False):
        cursor = self.textCursor()
        mode = QTextCursor.KeepAnchor if select else QTextCursor.MoveAnchor
        if position is None:
            cursor.movePosition(QTextCursor.End, mode)
        else:
            cursor.setPosition(position, mode)
        self.setTextCursor(cursor)
        self._keep_cursor_in_buffer()

    def _keep_cursor_in_buffer(self):
        cursor = self.textCursor()
        if cursor.anchor() < self._prompt_pos:
            cursor.setPosition(self._prompt_pos)
        if cursor.position() < self._prompt_pos:
            cursor.setPosition(self._prompt_pos, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _cursor_offset(self):
        return self.textCursor().position() - self._prompt_pos

    def _insert_prompt(self, prompt, lf=False, keep_buffer=False):
        if keep_buffer:
            self._copy_buffer = self._get_buffer()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(prompt)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

        if lf:
            self.recv_line('')

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

    # Asbtract
    def get_completions(self, line):
        return ['No completion support available']

    def set_auto_complete_mode(self, mode):
        self.set_complete_mode_signal.emit(mode)

    def _parse_buffer(self):
        cmd = self._get_buffer()
        self.stdout.write('\n')
        self.recv_line(cmd)

    # Abstract
    def recv_line(self, line):
        pass

    def _stdout_data_handler(self, data):
        self._insert_prompt(data)

        if len(self._copy_buffer) > 0:
            self._insert_in_buffer(self._copy_buffer)
            self._copy_buffer = ''

    # Abstract
    def insert_text(self, text):
        self._keep_cursor_in_buffer()
        text = '\n'.join([
            self._fix_line(line)
            for line in text.splitlines()])
        self.insertPlainText(text)

    def _fix_line(self, line):
        # Remove the any remaining more prompt, to make it easier
        # to copy/paste within the interpreter.
        if line.startswith(self._ps2):
            line = line[len(self._ps2):]
        return line

    def exit(self):
        pass

    def _close(self):
        if self.window().isVisible():
            self.window().close()

    # Abstract
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
        self.interpreter.done_signal.connect(self._finish_command)
        self.set_auto_complete_mode(COMPLETE_MODE.DROPDOWN)
        self._thread = None

    def recv_line(self, line):
        self._last_input = line
        self._more = self.interpreter.push(line)
        self._update_ps(self._more)
        if self._more:
            self._show_ps()

    def exit(self):
        if self._thread:
            self._thread.exit()
            self._thread = None
        self.interpreter.exit()

    def _handle_ctrl_c(self):
        # There is a race condition here, we should lock on the value of
        # executing() to avoid accidentally raising KeyboardInterrupt after
        # execution has finished. Deal with this later…
        if self._thread and self.interpreter.executing():
            self._thread.inject_exception(KeyboardInterrupt)
            # wake up thread in case it is currently waiting on input:
            self.stdin.flush()
        else:
            self.interpreter.resetbuffer()
            self.stdout.write('^C\n')
            self._more = False
            self._update_ps(self._more)
            self._show_ps()

    def closeEvent(self, event):
        self.exit()
        event.accept()

    def get_completions(self, line):
        script = jedi.Interpreter(line, [self.interpreter.local_ns])
        return [comp.name for comp in script.completions()]

    def push_local_ns(self, name, value):
        self.interpreter.local_ns[name] = value

    def eval_in_thread(self):
        self._thread = Thread()
        self.interpreter.moveToThread(self._thread)
        self.interpreter.exec_signal.connect(
            self.interpreter.exec_, Qt.ConnectionType.QueuedConnection)
        return self._thread

    def eval_queued(self):
        return self.interpreter.exec_signal.connect(
            self.interpreter.exec_, Qt.ConnectionType.QueuedConnection)

    def eval_executor(self, spawn):
        return self.interpreter.exec_signal.connect(
            lambda line: spawn(self.interpreter.exec_, line))


class Thread(QThread):

    """Thread that runs an event loop and exposes thread ID as ``.ident``."""

    def __init__(self, parent=None):
        super(Thread, self).__init__(parent)
        self.ready = threading.Event()
        self.start()
        self.ready.wait()

    def run(self):
        self.ident = threading.current_thread().ident
        self.ready.set()
        self.exec_()

    def inject_exception(self, value):
        """Raise exception in remote thread to stop execution of current
        commands (this only triggers once the thread executes any python
        bytecode)."""
        if self.ident != threading.current_thread().ident:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.ident),
                ctypes.py_object(value))
