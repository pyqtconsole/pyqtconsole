# -*- coding: utf-8 -*-
import sys
import contextlib
from functools import partial

import ast
from code import InteractiveInterpreter

from qtpy.QtCore import QObject, Slot, Signal


class PythonInterpreter(QObject, InteractiveInterpreter):

    exec_signal = Signal(object)
    done_signal = Signal(bool, object)
    exit_signal = Signal(object)

    def __init__(self, stdin, stdout, locals=None):
        QObject.__init__(self)
        InteractiveInterpreter.__init__(self, locals)
        self.locals['exit'] = Exit()
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
            with redirected_io(self.stdout):
                for code, mode in codes:
                    if mode == 'eval':
                        result = eval(code, self.locals)
                    else:
                        exec(code, self.locals)
        except SystemExit as e:
            self.exit_signal.emit(e)
        except BaseException:
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
            with disabled_excepthook():
                InteractiveInterpreter.showtraceback(self)

    def showsyntaxerror(self, filename):
        self.stdout.write('\n')

        with disabled_excepthook():
            InteractiveInterpreter.showsyntaxerror(self, filename)
        self.done_signal.emit(False, None)


def compile_multi(compiler, source, filename, symbol):
    """If mode is 'multi', split code into individual toplevel expressions or
    statements. Returns a list of tuples ``(code, mode)``. """
    if symbol != 'multi':
        return [(compiler(source, filename, symbol), symbol)]
    # First, check if the source compiles at all. This raises an exception if
    # there is a SyntaxError, or returns None if the code is incomplete:
    if compiler(source, filename, 'exec') is None:
        return None
    # Now split into individual 'single' units:
    module = ast.parse(source)
    # When entering a code block, the standard python interpreter waits for an
    # additional empty line to apply the input. We adhere to this convention,
    # checked by `compiler(..., 'single')`:
    if module.body:
        block_lineno = module.body[-1].lineno
        block_source = source[find_nth('\n' + source, '\n', block_lineno):]
        if compiler(block_source, filename, 'single') is None:
            return None
    return [
        compile_single_node(node, filename)
        for node in module.body
    ]


def compile_single_node(node, filename):
    """Compile a 'single' ast.node (expression or statement)."""
    mode = 'eval' if isinstance(node, ast.Expr) else 'exec'
    if mode == 'eval':
        root = ast.Expression(node.value)
    else:
        if sys.version_info >= (3, 8):
            root = ast.Module([node], type_ignores=[])
        else:
            root = ast.Module([node])
    return (compile(root, filename, mode), mode)


def find_nth(string, char, n):
    """Find the n'th occurence of a character within a string."""
    return [i for i, c in enumerate(string) if c == char][n-1]


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


# We use a custom exit function to avoid issues with environments such as
# spyder, where `builtins.exit` is not available, see #26:
class Exit:

    def __repr__(self):
        return "Type exit() to exit this console."

    def __call__(self, *args):
        raise SystemExit(*args)
