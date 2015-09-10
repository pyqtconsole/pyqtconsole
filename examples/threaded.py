# -*- coding: utf-8 -*-
#/usr/bin/python
import sys
import _phome

from pyqtconsole.qt.QtWidgets import (QApplication)
from pyqtconsole.console import PythonConsole

if __name__ == '__main__':
    app = QApplication([])

    console = PythonConsole()
    console.show()
    console.eval_in_thread()
    sys.exit(app.exec_())
