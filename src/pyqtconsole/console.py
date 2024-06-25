# -*- coding: utf-8 -*-
import threading
import ctypes
from abc import abstractmethod

from qtpy.QtCore import Qt, QThread, Slot, QEvent
from qtpy.QtWidgets import QPlainTextEdit, QApplication, QHBoxLayout, QFrame
from qtpy.QtGui import QFontMetrics, QTextCursor, QClipboard

from .interpreter import PythonInterpreter
from .stream import Stream
from .highlighter import PythonHighlighter, PromptHighlighter
from .commandhistory import CommandHistory
from .autocomplete import AutoComplete, COMPLETE_MODE
from .prompt import PromptArea

try:
    import jedi
    from jedi import settings
    settings.case_insensitive_completion = False
except ImportError:
    jedi = None


try:                        # PyQt >= 5.11
    QueuedConnection = Qt.ConnectionType.QueuedConnection
except AttributeError:      # PyQt < 5.11
    QueuedConnection = Qt.QueuedConnection


class BaseConsole(QFrame):

    """Base class for implementing a GUI console."""

    def __init__(self, parent=None, formats=None):
        super(BaseConsole, self).__init__(parent)

        self.edit = edit = InputArea()
        self.pbar = pbar = PromptArea(
            edit, self._get_prompt_text, PromptHighlighter(formats=formats))

        layout = QHBoxLayout()
        layout.addWidget(pbar)
        layout.addWidget(edit)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._prompt_doc = ['']
        self._prompt_pos = 0
        self._output_inserted = False
        self._tab_chars = 4 * ' '
        self._ctrl_d_exits = False
        self._copy_buffer = ''

        self._last_input = ''
        self._more = False
        self._current_line = 0

        self._ps1 = 'IN [%s]: '
        self._ps2 = '...: '
        self._ps_out = 'OUT[%s]: '
        self._ps = self._ps1 % self._current_line

        self.stdin = Stream()
        self.stdout = Stream()
        self.stdout.write_event.connect(self._stdout_data_handler)

        # show frame around both child widgets:
        self.setFrameStyle(edit.frameStyle())
        edit.setFrameStyle(QFrame.NoFrame)

        font = edit.document().defaultFont()
        font.setFamily("Courier New")
        font_width = QFontMetrics(font).width('M')
        self.setFont(font)

        geometry = edit.geometry()
        geometry.setWidth(font_width*80+20)
        geometry.setHeight(font_width*40)
        edit.setGeometry(geometry)
        edit.resize(font_width*80+20, font_width*40)

        edit.setReadOnly(True)
        edit.setTextInteractionFlags(
            Qt.TextSelectableByMouse |
            Qt.TextSelectableByKeyboard)
        self.setFocusPolicy(Qt.NoFocus)
        pbar.setFocusPolicy(Qt.NoFocus)
        edit.setFocusPolicy(Qt.StrongFocus)
        edit.setFocus()

        edit.installEventFilter(self)
        self._key_event_handlers = self._get_key_event_handlers()

        self.command_history = CommandHistory(self)
        self.auto_complete = jedi and AutoComplete(self)

        self._show_ps()

    def setFont(self, font):
        """Set font (you should only use monospace!)."""
        self.edit.document().setDefaultFont(font)
        self.edit.setFont(font)
        super(BaseConsole, self).setFont(font)

    def eventFilter(self, edit, event):
        """Intercepts events from the input control."""
        if event.type() == QEvent.KeyPress:
            return bool(self._filter_keyPressEvent(event))
        elif event.type() == QEvent.MouseButtonPress:
            return bool(self._filter_mousePressEvent(event))
        else:
            return False

    def _textCursor(self):
        return self.edit.textCursor()

    def _setTextCursor(self, cursor):
        self.edit.setTextCursor(cursor)

    def ensureCursorVisible(self):
        self.edit.ensureCursorVisible()

    def _update_ps(self, _more):
        # We need to show the more prompt of the input was incomplete
        # If the input is complete increase the input number and show
        # the in prompt
        if not _more:
            self._ps = self._ps1 % self._current_line
        else:
            self._ps = (len(self._ps) - len(self._ps2)) * ' ' + self._ps2

    @Slot(bool, object)
    def _finish_command(self, executed, result):
        if result is not None:
            self._insert_output_text(
                repr(result),
                prompt=self._ps_out % self._current_line)
            self._insert_output_text('\n')

        if executed and self._last_input:
            self._current_line += 1
        self._more = False
        self._show_cursor()
        self._update_ps(self._more)
        self._show_ps()

    def _show_ps(self):
        if self._output_inserted and not self._more:
            self._insert_output_text("\n")
        self._insert_prompt_text(self._ps)

    def _get_key_event_handlers(self):
        return {
            Qt.Key_Escape:      self._handle_escape_key,
            Qt.Key_Return:      self._handle_enter_key,
            Qt.Key_Enter:       self._handle_enter_key,
            Qt.Key_Backspace:   self._handle_backspace_key,
            Qt.Key_Delete:      self._handle_delete_key,
            Qt.Key_Home:        self._handle_home_key,
            Qt.Key_Tab:         self._handle_tab_key,
            Qt.Key_Backtab:     self._handle_backtab_key,
            Qt.Key_Up:          self._handle_up_key,
            Qt.Key_Down:        self._handle_down_key,
            Qt.Key_Left:        self._handle_left_key,
            Qt.Key_D:           self._handle_d_key,
            Qt.Key_C:           self._handle_c_key,
            Qt.Key_V:           self._handle_v_key,
            Qt.Key_U:           self._handle_u_key,
        }

    def insertFromMimeData(self, mime_data):
        if mime_data and mime_data.hasText():
            self.insert_input_text(mime_data.text())

    def _filter_mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Selection)
            self.insertFromMimeData(mime_data)
            return True

    def _filter_keyPressEvent(self, event):
        key = event.key()
        event.ignore()

        if self._executing():
            # ignore all key presses while executing, except for Ctrl-C
            if event.modifiers() == Qt.ControlModifier and key == Qt.Key_C:
                self._handle_ctrl_c()
            return True

        handler = self._key_event_handlers.get(key)
        intercepted = handler and handler(event)

        # Assumes that Control+Key is a movement command, i.e. should not be
        # handled as text insertion. However, on win10 AltGr is reported as
        # Alt+Control which is why we handle this case like regular
        # keypresses, see #53:
        if not event.modifiers() & Qt.ControlModifier or \
                event.modifiers() & Qt.AltModifier:
            self._keep_cursor_in_buffer()

            if not intercepted and event.text():
                intercepted = True
                self.insert_input_text(event.text())

        return intercepted

    def _handle_escape_key(self, event):
        return True

    def _handle_enter_key(self, event):
        if event.modifiers() & Qt.ShiftModifier:
            self.insert_input_text('\n')
        else:
            cursor = self._textCursor()
            cursor.movePosition(QTextCursor.End)
            self._setTextCursor(cursor)
            buffer = self.input_buffer()
            self._hide_cursor()
            self.insert_input_text('\n', show_ps=False)
            self.process_input(buffer)
        return True

    def _handle_backspace_key(self, event):
        self._keep_cursor_in_buffer()
        cursor = self._textCursor()
        offset = self.cursor_offset()
        if not cursor.hasSelection() and offset >= 1:
            tab = self._tab_chars
            buf = self._get_line_until_cursor()
            if event.modifiers() == Qt.ControlModifier:
                cursor.movePosition(
                    QTextCursor.PreviousWord,
                    QTextCursor.KeepAnchor, 1)
                self._keep_cursor_in_buffer()
            else:
                # delete spaces to previous tabstop boundary:
                tabstop = len(buf) % len(tab) == 0
                num = len(tab) if tabstop and buf.endswith(tab) else 1
                cursor.movePosition(
                    QTextCursor.PreviousCharacter,
                    QTextCursor.KeepAnchor, num)
        self._remove_selected_input(cursor)
        return True

    def _handle_delete_key(self, event):
        self._keep_cursor_in_buffer()
        cursor = self._textCursor()
        offset = self.cursor_offset()
        if not cursor.hasSelection() and offset < len(self.input_buffer()):
            tab = self._tab_chars
            left = self._get_line_until_cursor()
            right = self._get_line_after_cursor()
            if event.modifiers() == Qt.ControlModifier:
                cursor.movePosition(
                    QTextCursor.NextWord,
                    QTextCursor.KeepAnchor, 1)
                self._keep_cursor_in_buffer()
            else:
                # delete spaces to next tabstop boundary:
                tabstop = len(left) % len(tab) == 0
                num = len(tab) if tabstop and right.startswith(tab) else 1
                cursor.movePosition(
                    QTextCursor.NextCharacter,
                    QTextCursor.KeepAnchor, num)
        self._remove_selected_input(cursor)
        return True

    def _handle_tab_key(self, event):
        cursor = self._textCursor()
        if cursor.hasSelection():
            self._setTextCursor(self._indent_selection(cursor))
        else:
            # add spaces until next tabstop boundary:
            tab = self._tab_chars
            buf = self._get_line_until_cursor()
            num = len(tab) - len(buf) % len(tab)
            self.insert_input_text(tab[:num])
        event.accept()
        return True

    def _handle_backtab_key(self, event):
        self._setTextCursor(self._indent_selection(self._textCursor(), False))
        return True

    def _indent_selection(self, cursor, indent=True):
        buf = self.input_buffer()
        tab = self._tab_chars
        pos0 = cursor.selectionStart() - self._prompt_pos
        pos1 = cursor.selectionEnd() - self._prompt_pos
        line0 = buf[:pos0].count('\n')
        line1 = buf[:pos1].count('\n')
        lines = buf.split('\n')
        for i in range(line0, line1+1):
            # Although it at first seemed appealing to me to indent to the
            # next tab boundary, this leads to losing relative sub-tab
            # indentations and is therefore not desirable. We should therefore
            # always indent by a full tab:
            line = lines[i]
            if indent:
                lines[i] = tab + line
            else:
                lines[i] = line[:len(tab)].lstrip() + line[len(tab):]
            num = len(lines[i]) - len(line)
            pos0 += num if i == line0 else 0
            pos1 += num
        self.clear_input_buffer()
        self.insert_input_text('\n'.join(lines))
        cursor.setPosition(self._prompt_pos + pos0)
        cursor.setPosition(self._prompt_pos + pos1, QTextCursor.KeepAnchor)
        return cursor

    def _handle_home_key(self, event):
        select = event.modifiers() & Qt.ShiftModifier
        self._move_cursor(self._prompt_pos, select)
        return True

    def _handle_up_key(self, event):
        shift = event.modifiers() & Qt.ShiftModifier
        if shift or '\n' in self.input_buffer()[:self.cursor_offset()]:
            self._move_cursor(QTextCursor.Up, select=shift)
        else:
            self.command_history.dec(self.input_buffer())
        return True

    def _handle_down_key(self, event):
        shift = event.modifiers() & Qt.ShiftModifier
        if shift or '\n' in self.input_buffer()[self.cursor_offset():]:
            self._move_cursor(QTextCursor.Down, select=shift)
        else:
            self.command_history.inc()
        return True

    def _handle_left_key(self, event):
        return self.cursor_offset() < 1

    def _handle_d_key(self, event):
        if event.modifiers() == Qt.ControlModifier and not self.input_buffer():
            if self._ctrl_d_exits:
                self.exit()
            else:
                self._insert_output_text(
                    "\nCan't use CTRL-D to exit, you have to exit the "
                    "application !\n")
                self._more = False
                self._update_ps(False)
                self._show_ps()
            return True

    def _handle_c_key(self, event):
        intercepted = False
        if event.modifiers() == Qt.ControlModifier:
            self._handle_ctrl_c()
            intercepted = True
        elif event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier:
            self.edit.copy()
            intercepted = True
        return intercepted

    def _handle_u_key(self, event):
        if event.modifiers() == Qt.ControlModifier and self.input_buffer():
            self.clear_input_buffer()
            return True
        return False

    def _handle_v_key(self, event):
        if event.modifiers() == Qt.ControlModifier or \
                event.modifiers() == Qt.ControlModifier | Qt.ShiftModifier:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData(QClipboard.Clipboard)
            self.insertFromMimeData(mime_data)
            return True
        return False

    def _hide_cursor(self):
        self.edit.setCursorWidth(0)

    def _show_cursor(self):
        self.edit.setCursorWidth(1)

    def _move_cursor(self, position, select=False):
        cursor = self._textCursor()
        mode = QTextCursor.KeepAnchor if select else QTextCursor.MoveAnchor
        if isinstance(position, QTextCursor.MoveOperation):
            cursor.movePosition(position, mode)
        else:
            cursor.setPosition(position, mode)
        self._setTextCursor(cursor)
        self._keep_cursor_in_buffer()

    def _keep_cursor_in_buffer(self):
        cursor = self._textCursor()
        if cursor.anchor() < self._prompt_pos:
            cursor.setPosition(self._prompt_pos)
        if cursor.position() < self._prompt_pos:
            cursor.setPosition(self._prompt_pos, QTextCursor.KeepAnchor)
        self._setTextCursor(cursor)
        self.ensureCursorVisible()

    def _insert_output_text(self, text,
                            lf=False, keep_buffer=False, prompt=''):
        if keep_buffer:
            self._copy_buffer = self.input_buffer()

        cursor = self._textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self._prompt_pos = cursor.position()
        self.ensureCursorVisible()

        self._insert_prompt_text(prompt + '\n' * text.count('\n'))
        self._output_inserted = True
        if lf:
            self.process_input('')

    def _update_prompt_pos(self):
        cursor = self._textCursor()
        cursor.movePosition(QTextCursor.End)
        self._prompt_pos = cursor.position()
        self._output_inserted = self._more

    def input_buffer(self):
        """Retrieve current input buffer in string form."""
        return self.edit.toPlainText()[self._prompt_pos:]

    def cursor_offset(self):
        """Get current cursor index within input buffer."""
        return self._textCursor().position() - self._prompt_pos

    def _get_line_until_cursor(self):
        """Get current line of input buffer, up to cursor position."""
        return self.input_buffer()[:self.cursor_offset()].rsplit('\n', 1)[-1]

    def _get_line_after_cursor(self):
        """Get current line of input buffer, after cursor position."""
        return self.input_buffer()[self.cursor_offset():].split('\n', 1)[0]

    def clear_input_buffer(self):
        """Clear input buffer."""
        cursor = self._textCursor()
        cursor.setPosition(self._prompt_pos)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        self._remove_selected_input(cursor)
        self._setTextCursor(cursor)

    def insert_input_text(self, text, show_ps=True):
        """Insert text into input buffer."""
        self._keep_cursor_in_buffer()
        self.ensureCursorVisible()

        self._remove_selected_input(self._textCursor())
        self._textCursor().insertText(text)

        if show_ps and '\n' in text:
            self._update_ps(True)
            for _ in range(text.count('\n')):
                # NOTE: need to insert in two steps, because this internally
                # uses setAlignment, which affects only the first line:
                self._insert_prompt_text('\n')
                self._insert_prompt_text(self._ps)
        elif '\n' in text:
            self._insert_prompt_text('\n' * text.count('\n'))

    def set_auto_complete_mode(self, mode):
        if self.auto_complete:
            self.auto_complete.mode = mode

    def process_input(self, source):
        """Handle a new source snippet confirmed by the user."""
        self._last_input = source
        self._more = self._run_source(source)
        self._update_ps(self._more)
        if self._more:
            self._show_ps()
            self._show_cursor()
        else:
            self.command_history.add(source)
            self._update_prompt_pos()

    def _handle_ctrl_c(self):
        """Inject keyboard interrupt if code is being executed in a thread,
        else cancel the current prompt."""
        # There is a race condition here, we should lock on the value of
        # executing() to avoid accidentally raising KeyboardInterrupt after
        # execution has finished. Deal with this later…
        if self._executing():
            self._cancel()
        else:
            self._last_input = ''
            self.stdout.write('^C\n')
            self._output_inserted = False
            self._more = False
            self._update_ps(self._more)
            self._show_ps()

    def _stdout_data_handler(self, data):
        self._insert_output_text(data)

        if len(self._copy_buffer) > 0:
            self.insert_input_text(self._copy_buffer)
            self._copy_buffer = ''

    def _insert_prompt_text(self, text):
        lines = text.split('\n')
        self._prompt_doc[-1] += lines[0]
        self._prompt_doc += lines[1:]
        for line in self._prompt_doc[-len(lines):]:
            self.pbar.adjust_width(line)

    def _get_prompt_text(self, line_number):
        return self._prompt_doc[line_number]

    def _remove_selected_input(self, cursor):
        if not cursor.hasSelection():
            return

        num_lines = cursor.selectedText().replace(u'\u2029', '\n').count('\n')
        cursor.removeSelectedText()

        if num_lines > 0:
            block = cursor.blockNumber() + 1
            del self._prompt_doc[block:block+num_lines]

    def closeEvent(self, event):
        """Exit interpreter when we're closing."""
        self.exit()
        event.accept()

    def _close(self):
        if self.window().isVisible():
            self.window().close()

    def set_tab(self, chars):
        self._tab_chars = chars

    def ctrl_d_exits_console(self, b):
        self._ctrl_d_exits = b

    # Abstract

    @abstractmethod
    def exit(self):
        pass

    @abstractmethod
    def _executing(self):
        pass

    @abstractmethod
    def _cancel(self):
        pass

    @abstractmethod
    def _run_source(self, source):
        pass

    @abstractmethod
    def get_completions(self, line):
        return ['No completion support available']


class PythonConsole(BaseConsole):

    """Interactive python GUI console."""

    def __init__(self, parent=None, locals=None, formats=None):
        super(PythonConsole, self).__init__(parent, formats=formats)
        self.highlighter = PythonHighlighter(
            self.edit.document(), formats=formats)
        self.interpreter = PythonInterpreter(
            self.stdin, self.stdout, locals=locals)
        self.interpreter.done_signal.connect(self._finish_command)
        self.interpreter.exit_signal.connect(self.exit)
        self.set_auto_complete_mode(COMPLETE_MODE.DROPDOWN)
        self._thread = None

    def _executing(self):
        return self.interpreter.executing()

    def _cancel(self):
        if self._thread:
            self._thread.inject_exception(KeyboardInterrupt)
            # wake up thread in case it is currently waiting on input:
            self.stdin.flush()

    def _run_source(self, source):
        return self.interpreter.runsource(source, symbol='multi')

    def exit(self):
        """Exit interpreter."""
        if self._thread:
            self._thread.exit()
            self._thread.wait()
            self._thread = None
        self._close()

    def get_completions(self, line):
        """Get completions. Used by the ``autocomplete`` extension."""
        script = jedi.Interpreter(line, [self.interpreter.locals])

        try:
            comps = script.complete()
        except AttributeError:
            # Jedi < 0.16.0 named the method differently
            comps = script.completions()

        return [comp.name for comp in comps]

    def push_local_ns(self, name, value):
        """Set a variable in the local namespace."""
        self.interpreter.locals[name] = value

    def eval_in_thread(self):
        """Start a thread in which code snippets will be executed."""
        self._thread = Thread()
        self.interpreter.moveToThread(self._thread)
        self.interpreter.exec_signal.connect(
            self.interpreter.exec_, QueuedConnection)
        return self._thread

    def eval_queued(self):
        """Setup connections to execute code snippets in later mainloop
        iterations in the main thread."""
        return self.interpreter.exec_signal.connect(
            self.interpreter.exec_, QueuedConnection)

    def eval_executor(self, spawn):
        """Exec snippets using the given executor function (e.g.
        ``gevent.spawn``)."""
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
        """Run Qt event dispatcher within the thread."""
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


class InputArea(QPlainTextEdit):

    """Widget that is used for the input/output edit area of the console."""

    def insertFromMimeData(self, mime_data):
        return self.parent().insertFromMimeData(mime_data)
