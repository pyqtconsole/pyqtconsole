#! /usr/bin/env python
# -*- coding: utf-8 -*-

from gevent import monkey; monkey.patch_all()   # noqa

import gevent
import sys

from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication
from pyqtconsole.console import PythonConsole


def greet():
    print("hello world")


class GEventProcessing:

    """Interoperability class between Qt/gevent that allows processing gevent
    tasks during Qt idle periods."""

    def __init__(self, idle_period=0.010):
        # Limit the IDLE handler's frequency while still allow for gevent
        # to trigger a microthread anytime
        self._idle_period = idle_period
        # IDLE timer: on_idle is called whenever no Qt events left for
        # processing
        self._timer = QTimer()
        self._timer.timeout.connect(self.process_events)
        self._timer.start(0)

    def __enter__(self):
        pass

    def __exit__(self, *exc_info):
        self._timer.stop()

    def process_events(self):
        # Cooperative yield, allow gevent to monitor file handles via libevent
        gevent.sleep(self._idle_period)


if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole()
    console.push_local_ns('greet', greet)
    console.show()

    console.eval_executor(gevent.spawn)

    with GEventProcessing():
        sys.exit(app.exec_())
