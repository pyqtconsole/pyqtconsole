# -*- coding: utf-8 -*-
#/usr/bin/python
from gevent import monkey; monkey.patch_all()

import gevent
import sys

from pyqtconsole.qt.QtCore import QTimer
from pyqtconsole.qt.QtWidgets import QApplication
from pyqtconsole.console import PythonConsole


def gevent_wait():
    try:
        gevent.wait(0.01)
    except:
        gevent.sleep(0.01)


def greet():
    print("hello world")


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole()
    console.push_local_ns('greet', greet)
    console.show()

    gevent_timer = QTimer()
    gevent_timer.timeout.connect(gevent_wait)
    gevent_timer.start(0)

    task = gevent.spawn(console.repl)

    sys.exit(app.exec_())
