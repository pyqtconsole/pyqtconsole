# pyqtconsole

pyqtconosle is a light weight python console for Qt applications. Its made to be easy to emmbed in other Qt applications
and comes with some examples that shows how this can be done. The interpreter can run in a seperate thread, in the UI main thread or in a gevent task. Suport for asyncio might also be added in the future

## Emmbeding

* Running the interpreter in a seperate thread, see the example threaded.py. Running the interpreter in a seperate thread obviusly limits the interaction with the Qt applicaion. The parts of Qt that needs to be called from the main thread to execute will not work properly.
