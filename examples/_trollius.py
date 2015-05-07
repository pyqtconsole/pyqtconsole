# -*- coding: utf-8 -*-
#/usr/bin/python
import trollius as asyncio
import sys
import _phome

from pyqtconsole.qt.QtWidgets import (QApplication)
from pyqtconsole.console import PythonConsole
from pyqtconsole.trollius_suport import QTrolliusEventLoop

if __name__ == '__main__':
    from PyMca5.PyMca import PlotWindow
    app = QApplication(sys.argv)
    loop = QTrolliusEventLoop(app = app)
    asyncio.set_event_loop(loop)
    
    console = PythonConsole()
    console.push_local_ns('PlotWindow', PlotWindow)
    console.show()

    def repl(console):    
        while console.isVisible():
            console.repl_nonblock()
            yield asyncio.From(asyncio.sleep(0.01))

    tasks = [asyncio.async(repl(console))]
    loop.run_until_complete(asyncio.wait(tasks))
