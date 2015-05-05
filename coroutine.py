# -*- coding: utf-8 -*-
#/usr/bin/python
from gevent import monkey; monkey.patch_all()

import gevent
import sys

from pyqtconsole.qt import QtCore
from pyqtconsole.qt.QtWidgets import (QApplication)
from pyqtconsole.console import PythonConsole

def gevent_wait():
    gevent.wait(timeout=0.01)

if __name__ == '__main__':
    from PyMca5.PyMca import PlotWindow
    app = QApplication([])

    console = PythonConsole()
    console.push_local_ns('PlotWindow', PlotWindow)
    console.show()

    gevent_timer = QtCore.QTimer()
    gevent_timer.timeout.connect(gevent_wait)
    gevent_timer.start(0)

    task = gevent.spawn(console.repl)

    sys.exit(app.exec_())
