# -*- coding: utf-8 -*-
#/usr/bin/python
import sys

from pyqtconsole.qt.QtWidgets import (QApplication)
from pyqtconsole.console import PythonConsole

if __name__ == '__main__':
    from PyMca5.PyMca import PlotWindow
    app = QApplication([])

    console = PythonConsole()
    console.push_local_ns('PlotWindow', PlotWindow)
    console.show()

    console.eval_queued()

    sys.exit(app.exec_())
