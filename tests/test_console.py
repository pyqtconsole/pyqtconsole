from collections.abc import Generator

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt

from pyqtconsole.console import PythonConsole


class TestConsole:
    """A collection of integration tests, directly on the console."""

    bot: QtBot
    console: PythonConsole

    @pytest.fixture(autouse=True)
    def _qt_bot(self, qtbot):
        """Automatically include qtbot for all test-methods."""
        self.bot = qtbot

    @pytest.fixture(autouse=True)
    def _console(self, _qt_bot) -> Generator[PythonConsole, None, None]:
        self.console = PythonConsole()
        self.bot.add_widget(self.console)
        self.console.show()
        self.console.eval_in_thread()
        yield self.console

    def hit_enter(self):
        """Trigger of hitting the [Enter] key inside the prompt."""
        self.bot.keyClick(self.console.edit, Qt.Key.Key_Enter)

    def test_basic(self):
        """Test a single, very basic input."""
        self.console.edit.insertPlainText("print(1 + 1)")
        self.hit_enter()

        def check():
            content = self.console.edit.toPlainText()
            lines = content.splitlines()
            assert len(lines) == 3
            assert lines == [
                "print(1 + 1)",
                "2",
                "",
            ]

        self.bot.waitUntil(check)
