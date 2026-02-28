#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from qtpy.QtWidgets import QApplication
from pyqtconsole.console import PythonConsole

welcome_msg = """Python Console v1.0
Commands starting with ! are executed as shell commands
"""


def greet():
    print("hello world")


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole(shell_cmd_prefix=True,
                            welcome_message=welcome_msg)
    console.push_local_ns('greet', greet)
    console.interpreter.locals["clear"] = console.clear
    console.show()
    console.eval_in_thread()
    sys.exit(app.exec_())
