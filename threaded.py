# -*- coding: utf-8 -*-
#/usr/bin/python
import sys

from threading import Thread
from pyqtconsole.qt.QtWidgets import (QApplication)
from pyqtconsole.console import PythonConsole

if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole()
    console.show()

    ct = Thread(target = console.repl)
    ct.start()

    sys.exit(app.exec_())
