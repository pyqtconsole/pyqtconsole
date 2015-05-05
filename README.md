# pyqtconsole

pyqtconosle is a light weight python console for Qt applications. Its made to be easy to emmbed in other Qt applications
and comes with some examples that shows how this can be done. The interpreter can run in a seperate thread, in the UI main thread or in a gevent task. Suport for asyncio might also be added in the future

## Emmbeding

* *Seperate thread* - Runs the interpreter in a seperate thread, see the example [threaded.py] (https://github.com/marcus-oscarsson/pyqtconsole/blob/master/threaded.py). Running the interpreter in a seperate thread obviusly limits the interaction with the Qt applicaion. The parts of Qt that needs to be called from the main thread to execute will not work properly. But is excelent for a 'plain' python console.

* *main thread* - Runs the interpreter in the main thread, see the example [inuithread.py](https://github.com/marcus-oscarsson/pyqtconsole/blob/master/inuithread.py). Makes full interaction with Qt possible, lenghty operations will ofcourse freezze the UI (as any lenghty operation that is called from the main thread). This is a great allternative for people who does want to use the gevent based approach but still wants full interactivity with Qt.

* *gevent* - Runs the interpreter in a gevent task, see the example [coroutine.py](https://github.com/marcus-oscarsson/pyqtconsole/blob/master/coroutine.py). Allows for full interactivity with Qt without special consideration (at least to some extent) for logner running processes. The best method if you want to use pyQtgraph, Matplotlib, PyMca or similair.
 
## Credits

The .qt submodule was taken from the pyQode (https://github.com/pyQode/pyqode.qt) project. And provides Qt4 and Qt5 compatability, the console is tested under both Qt4 and Qt5. The .qt submodule is included for easy distrubution and to provide working examples for both versions 4 and 5 of Qt.
