#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from qtpy.QtWidgets import QApplication
from pyqtconsole.console import PythonConsole


def greet():
    print("hello world")


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole()
    console.push_local_ns('greet', greet)
    console.show()
    console.eval_in_thread()
    sys.exit(app.exec_())
