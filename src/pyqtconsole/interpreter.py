import ast
import contextlib
import sys
from code import InteractiveInterpreter
from codeop import CommandCompiler
from collections.abc import Generator
from functools import partial
from types import CodeType
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QObject, Signal, Slot  # type: ignore

if TYPE_CHECKING:
    from .stream import Stream


class PythonInterpreter(QObject, InteractiveInterpreter):
    exec_signal = Signal(object)
    done_signal = Signal(bool, object)
    exit_signal = Signal(object)

    def __init__(self, stdin: "Stream", stdout: "Stream", locals: Any = None):
        QObject.__init__(self)
        InteractiveInterpreter.__init__(self, locals)
        self.locals["exit"] = Exit()
        self.stdin = stdin
        self.stdout = stdout
        self._executing = False
        self.compile = partial(compile_multi, self.compile)  # type: ignore

    def executing(self) -> bool:
        return self._executing

    def runcode(self, code: CodeType) -> None:
        self.exec_signal.emit(code)

    @Slot(object)  # type: ignore [untyped-decorator]
    def exec_(self, codes: list[Any]) -> None:
        self._executing = True
        result = None

        # Redirect IO and disable excepthook, this is the only place were we
        # redirect IO, since we don't how IO is handled within the code we
        # are running. Same thing for the except hook, we don't know what the
        # user are doing in it.
        try:
            with redirected_io(self.stdout):
                for code, mode in codes:
                    if mode == "eval":
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

    def write(self, data: str) -> None:
        self.stdout.write(data)

    def showtraceback(self) -> None:
        type_, value, tb = sys.exc_info()
        self.stdout.write("\n")

        if type_ is KeyboardInterrupt:
            self.stdout.write("KeyboardInterrupt\n")
        else:
            with disabled_excepthook():
                InteractiveInterpreter.showtraceback(self)

    def showsyntaxerror(self, filename: str | None = None, **kwargs: Any) -> None:
        self.stdout.write("\n")

        with disabled_excepthook():
            # It seems Python 3.13 requires **kwargs, older versions don't
            InteractiveInterpreter.showsyntaxerror(self, filename, **kwargs)
        self.done_signal.emit(False, None)


def compile_multi(
    compiler: CommandCompiler, source: str, filename: str, symbol: str
) -> None | list[tuple[Any, str]]:
    """If mode is 'multi', split code into individual toplevel expressions or
    statements. Returns a list of tuples ``(code, mode)``."""
    if symbol != "multi":
        return [(compiler(source, filename, symbol), symbol)]
    # First, check if the source compiles at all. This raises an exception if
    # there is a SyntaxError, or returns None if the code is incomplete:
    if compiler(source, filename, "exec") is None:
        return None
    # Now split into individual 'single' units:
    module = ast.parse(source)
    # When entering a code block, the standard python interpreter waits for an
    # additional empty line to apply the input. We adhere to this convention,
    # checked by `compiler(..., 'single')`:
    if module.body:
        block_lineno = module.body[-1].lineno
        block_source = source[find_nth("\n" + source, "\n", block_lineno) :]
        if compiler(block_source, filename, "single") is None:
            return None
    return [compile_single_node(node, filename) for node in module.body]


def compile_single_node(node: ast.AST, filename: str) -> tuple[Any, str]:
    """Compile a 'single' ast.node (expression or statement)."""
    mode = "eval" if isinstance(node, ast.Expr) else "exec"
    if mode == "eval":
        root = ast.Expression(node.value)  # type: ignore
    else:
        root = ast.Module([node], type_ignores=[])  # type: ignore
    return compile(root, filename, mode), mode


def find_nth(string: str, char: str, n: int) -> int:
    """Find the n'th occurence of a character within a string."""
    return [i for i, c in enumerate(string) if c == char][n - 1]


@contextlib.contextmanager
def disabled_excepthook() -> Generator[Any, None, None]:
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
def redirected_io(stdout: "Stream") -> Generator[Any, None, None]:
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
    def __repr__(self) -> str:
        return "Type exit() to exit this console."

    def __call__(self, *args: Any) -> None:
        raise SystemExit(*args)
