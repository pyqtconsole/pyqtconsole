# pyqtconsole

pyqtconosle is a light weight python console for Qt applications. Its made to be easy to emmbed in other Qt applications
and comes with some examples that shows how this can be done. The interpreter can run in a seperate thread, in the UI main thread or in a gevent task. Suport for asyncio might also be added in the future

## Emmbeding

* *Seperate thread* - Runs the interpreter in a seperate thread, see the example threaded.py.Running the interpreter in a seperate thread obviusly limits the interaction with the Qt applicaion. The parts of Qt that needs to be called from the main thread to execute will not work properly. But is excelent for a 'plain' python console.

* *main thread* - Runs the interpreter in the main thread, see the example inuithread.py. Makes full interaction with Qt possible, lenghty operations will ofcourse freezze the UI (as any lenghty operation that is called from the main thread). This is a great allternative for people who does want to use the gevent based approach but still wants full interactivity with Qt.

* *gevent* - Runs the interpreter in a gevent task, see the example coroutine.py.
