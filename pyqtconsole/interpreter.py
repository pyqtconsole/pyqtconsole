# -*- coding: utf-8 -*-
import sys
import contextlib
from functools import partial

from code import InteractiveInterpreter

from .qt.QtCore import QObject, Slot, Signal

try:
    from builtins import exit       # py3
except ImportError:
    from __builtin__ import exit    # py2


class PythonInterpreter(QObject, InteractiveInterpreter):

    exec_signal = Signal(object)
    done_signal = Signal(bool, object)
    exit_signal = Signal(object)

    def __init__(self, stdin, stdout, locals=None):
        QObject.__init__(self)
        InteractiveInterpreter.__init__(self, locals)
        self.locals['exit'] = exit
        self.stdin = stdin
        self.stdout = stdout
        self._executing = False
        self.compile = partial(compile_multi, self.compile)

    def executing(self):
        return self._executing

    def runcode(self, code):
        self.exec_signal.emit(code)

    @Slot(object)
    def exec_(self, codes):
        self._executing = True
        result = None

        # Redirect IO and disable excepthook, this is the only place were we
        # redirect IO, since we don't how IO is handled within the code we
        # are running. Same thing for the except hook, we don't know what the
        # user are doing in it.
        try:
            with redirected_io(self.stdout), disabled_excepthook():
                for code, mode in codes:
                    if mode == 'eval':
                        result = eval(code, self.locals)
                    else:
                        exec(code, self.locals)
        except SystemExit as e:
            self.exit_signal.emit(e)
        except:
            self.showtraceback()
        finally:
            self._executing = False
            self.done_signal.emit(True, result)

    def write(self, data):
        self.stdout.write(data)

    def showtraceback(self):
        type_, value, tb = sys.exc_info()
        self.stdout.write('\n')

        if type_ == KeyboardInterrupt:
            self.stdout.write('KeyboardInterrupt\n')
        else:
            InteractiveInterpreter.showtraceback(self)

    def showsyntaxerror(self, filename):
        InteractiveInterpreter.showsyntaxerror(self, filename)
        self.done_signal.emit(False, None)


def compile_multi(compiler, source, filename, symbol):
    if symbol != 'multi':
        return [(compiler(source, filename, symbol), symbol)]

    # First, check if the source compiles at all, otherwise the rest will be
    # wasted effort. This raises an exception if there is a SyntaxError, or
    # returns None if the code is incomplete:
    if compiler(source, symbol, 'exec') is None:
        return None

    lines = source.split('\n')

    for i, line in enumerate(lines):
        last_line = i != len(lines) - 1
        if last_line and (line.startswith((' ', '\t', '#')) or not line):
            continue
        exec_source = '\n'.join(lines[:i])
        single_source = '\n'.join(lines[i:])
        try:
            exec_code = compiler(exec_source, symbol, 'exec')
            single_code = compiler(single_source, symbol, 'single')
            if exec_code and single_code:
                try:
                    expr_code = compiler(single_source, symbol, 'eval')
                    if expr_code:
                        return [(exec_code, 'exec'), (expr_code, 'eval')]
                except SyntaxError:
                    pass
                return [(exec_code, 'exec'), (single_code, 'exec')]
        except SyntaxError:
            continue


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
