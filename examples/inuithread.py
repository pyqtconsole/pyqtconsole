#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from qtpy.QtWidgets import QApplication
from pyqtconsole.console import PythonConsole
from pyqtconsole.highlighter import format


def greet():
    print("hello world")


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole(formats={
        'keyword': format('darkBlue', 'bold')
    })
    console.push_local_ns('greet', greet)
    console.show()

    console.eval_queued()

    sys.exit(app.exec_())
