from typing import TYPE_CHECKING

from qtpy.QtCore import QObject

if TYPE_CHECKING:
    from .console import BaseConsole


class CommandHistory(QObject):
    def __init__(self, console: "BaseConsole"):
        super().__init__(console)
        self._cmd_history: list[str] = []
        self._idx = 0
        self._pending_input = ""
        self._console = console  # Use instead of `parent()` for type hinting

    def add(self, str_: str) -> None:
        if str_:
            self._cmd_history.append(str_)

        self._pending_input = ""
        self._idx = len(self._cmd_history)

    def inc(self) -> None:
        # index starts at 0 so + 1 to make sure that we are within the
        # limits of the list
        if self._cmd_history:
            self._idx = min(self._idx + 1, len(self._cmd_history))
            self._insert_in_editor(self.current())

    def dec(self, _input: str) -> None:
        if self._idx == len(self._cmd_history):
            self._pending_input = _input
        if len(self._cmd_history) and self._idx > 0:
            self._idx -= 1
            self._insert_in_editor(self.current())

    def current(self) -> str:
        if self._idx == len(self._cmd_history):
            return self._pending_input
        else:
            return self._cmd_history[self._idx]

    def _insert_in_editor(self, str_: str) -> None:
        self._console.clear_input_buffer()
        self._console.insert_input_text(str_)
