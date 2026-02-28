#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from pyqtconsole.console import PythonConsole
from qtpy.QtWidgets import QApplication


def greet():
    print("hello world")


def version(args=None):
    """example of a custom magic command"""
    import pyqtconsole
    return str(pyqtconsole.__version__)


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole(shell_cmd_prefix=True)
    console.push_local_ns('greet', greet)
    console.interpreter.locals["clear"] = console.clear

    # add a custom magic command:
    console.add_magic_command('version', version)

    console.show()
    console.eval_in_thread()
    sys.exit(app.exec_())
