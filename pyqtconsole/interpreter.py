# -*- coding: utf-8 -*-
import sys
import contextlib

from code import InteractiveInterpreter

from .qt.QtCore import QObject, Slot, Signal

try:
    from builtins import exit       # py3
except ImportError:
    from __builtin__ import exit    # py2


class PythonInterpreter(QObject, InteractiveInterpreter):

    exec_signal = Signal(object)
    done_signal = Signal(bool)
    exit_signal = Signal(object)

    def __init__(self, stdin, stdout, locals=None):
        QObject.__init__(self)
        InteractiveInterpreter.__init__(self, locals)
        self.locals['exit'] = exit
        self.stdin = stdin
        self.stdout = stdout
        self._executing = False

    def executing(self):
        return self._executing

    def runcode(self, code):
        self.exec_signal.emit(code)

    @Slot(object)
    def exec_(self, code):
        self._executing = True

        # Redirect IO and disable excepthook, this is the only place were we
        # redirect IO, since we don't how IO is handled within the code we
        # are running. Same thing for the except hook, we don't know what the
        # user are doing in it.
        try:
            with redirected_io(self.stdout), disabled_excepthook():
                InteractiveInterpreter.runcode(self, code)
        except SystemExit as e:
            self.exit_signal.emit(e)
        finally:
            self._executing = False
            self.done_signal.emit(True)

    def write(self, data):
        self.stdout.write(data)

    def showtraceback(self):
        type_, value, tb = sys.exc_info()
        self.stdout.write('\n')

        if type_ == KeyboardInterrupt:
            self.stdout.write('KeyboardInterrupt\n')
        else:
            InteractiveInterpreter.showtraceback(self)

        self.stdout.write('\n')

    def showsyntaxerror(self, filename):
        self.stdout.write('\n')
        InteractiveInterpreter.showsyntaxerror(self, filename)
        self.stdout.write('\n')
        self.done_signal.emit(False)


@contextlib.contextmanager
def disabled_excepthook():
    """Run code with the exception hook temporarily disabled."""
    old_excepthook = sys.excepthook
    sys.excepthook = sys.__excepthook__

    try:
        yield
    finally:
        # If the code we did run did change sys.excepthook, we leave it
        # unchanged. Otherwise, we reset it.
        if sys.excepthook is sys.__excepthook__:
            sys.excepthook = old_excepthook


@contextlib.contextmanager
def redirected_io(stdout):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout
    sys.stderr = stdout
    try:
        yield
    finally:
        if sys.stdout is stdout:
            sys.stdout = old_stdout
        if sys.stderr is stdout:
            sys.stderr = old_stderr
