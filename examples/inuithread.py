# -*- coding: utf-8 -*-
#/usr/bin/python
import sys
import _phome

from pyqtconsole.qt import QtCore
from pyqtconsole.qt.QtWidgets import (QApplication)
from pyqtconsole.console import PythonConsole

if __name__ == '__main__':
    from PyMca5.PyMca import PlotWindow
    app = QApplication([])
    
    console = PythonConsole()
    console.push_local_ns('PlotWindow', PlotWindow)
    console.show()
    
    pyconsole_input_timer = QtCore.QTimer()
    pyconsole_input_timer.timeout.connect(console.repl_nonblock)
    pyconsole_input_timer.start(10)

    sys.exit(app.exec_())
