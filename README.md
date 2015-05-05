# pyqtconsole

pyqtconosle is a light weight python console for Qt applications. Its made to be easy to embed in other Qt applications
and comes with some examples that shows how this can be done. The interpreter can run in a separate thread, in the UI main thread or in a gevent task. Support for asyncio might also be added in the future

## Embedding

* *Separate thread* - Runs the interpreter in a separate thread, see the example [threaded.py] (https://github.com/marcus-oscarsson/pyqtconsole/blob/master/threaded.py). Running the interpreter in a separate thread obviously limits the interaction with the Qt application. The parts of Qt that needs to be called from the main thread will not work properly, but is excellent way for having a 'plain' python console in your Qt app.

* *main thread* - Runs the interpreter in the main thread, see the example [inuithread.py](https://github.com/marcus-oscarsson/pyqtconsole/blob/master/inuithread.py). Makes full interaction with Qt possible, lenghty operations will of course freeze the UI (as any lenghty operation that is called from the main thread). This is a great alternative for people who does not want to use the gevent based approach but still wants full interactivity with Qt.

* *gevent* - Runs the interpreter in a gevent task, see the example [coroutine.py](https://github.com/marcus-oscarsson/pyqtconsole/blob/master/coroutine.py). Allows for full interactivity with Qt without special consideration (at least to some extent) for longer running processes. The best method if you want to use pyQtgraph, Matplotlib, PyMca or similar.
 
## Credits

The .qt sub module was taken from the pyQode (https://github.com/pyQode/pyqode.qt) project. And provides Qt4 and Qt5 compatibility, the console is tested under both Qt4 and Qt5. The .qt sub module is included for easy distribution and to provide working examples for both versions 4 and 5 of Qt.
