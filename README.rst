pyqtconsole
===========

|Version| |Python| |License| |Tests|

pyqtconsole is a lightweight python console for Qt applications. It's made to
be easy to embed in other Qt applications and comes with some examples that
show how this can be done. The interpreter can run in a separate thread, in
the UI main thread or in a gevent task.

Installing
~~~~~~~~~~

Simply type::

    pip install pyqtconsole

Or to install a development version from local checkout, type::

    pip install -e .

Simple usage
~~~~~~~~~~~~

The following snippet shows how to create a console that will execute user
input in a separate thread. Be aware that long running tasks will still block
the main thread due to the GIL. See the ``examples`` directory for more
examples.

.. code-block:: python

    import sys
    from threading import Thread
    from PyQt5.QtWidgets import QApplication

    from pyqtconsole.console import PythonConsole

    app = QApplication([])
    console = PythonConsole()
    console.show()
    console.eval_in_thread()

    sys.exit(app.exec_())

Embedding
~~~~~~~~~

* *Separate thread* - Runs the interpreter in a separate thread, see the
  example threaded.py_. Running the interpreter in a separate thread obviously
  limits the interaction with the Qt application. The parts of Qt that needs
  to be called from the main thread will not work properly, but is excellent
  way for having a 'plain' python console in your Qt app.

* *main thread* - Runs the interpreter in the main thread, see the example
  inuithread.py_. Makes full interaction with Qt possible, lenghty operations
  will of course freeze the UI (as any lenghty operation that is called from
  the main thread). This is a great alternative for people who does not want
  to use the gevent based approach but still wants full interactivity with Qt.

* *gevent* - Runs the interpreter in a gevent task, see the example
  `_gevent.py`_. Allows for full interactivity with Qt without special
  consideration (at least to some extent) for longer running processes. The
  best method if you want to use pyQtgraph, Matplotlib, PyMca or similar.

Customizing syntax highlighting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The coloring of the syntax highlighting can be customized by passing a
``formats`` dictionary to the ``PythonConsole`` constructer. This dictionary
must be shaped as follows:

.. code-block:: python

    import pyqtconsole.highlighter as hl
    console = PythonConsole(formats={
        'keyword':    hl.format('blue', 'bold'),
        'operator':   hl.format('red'),
        'brace':      hl.format('darkGray'),
        'defclass':   hl.format('black', 'bold'),
        'string':     hl.format('magenta'),
        'string2':    hl.format('darkMagenta'),
        'comment':    hl.format('darkGreen', 'italic'),
        'self':       hl.format('black', 'italic'),
        'numbers':    hl.format('brown'),
        'inprompt':   hl.format('darkBlue', 'bold'),
        'outprompt':  hl.format('darkRed', 'bold'),
    })

All keys are optional and default to the value shown above if left unspecified.

Credits
~~~~~~~

This module depends on QtPy which provides a compatibility layer for
Qt4 and Qt5. The console is tested under both Qt4 and Qt5.


.. _threaded.py: https://github.com/marcus-oscarsson/pyqtconsole/blob/master/examples/threaded.py
.. _inuithread.py: https://github.com/marcus-oscarsson/pyqtconsole/blob/master/examples/inuithread.py
.. _`_gevent.py`: https://github.com/marcus-oscarsson/pyqtconsole/blob/master/examples/_gevent.py
.. _QtPy: https://github.com/spyder-ide/qtpy


.. Badges:

.. |Version| image::    https://img.shields.io/pypi/v/pyqtconsole.svg
   :target:             https://pypi.org/project/pyqtconsole
   :alt:                Latest Version

.. |Python| image::     https://img.shields.io/pypi/pyversions/pyqtconsole.svg
   :target:             https://pypi.org/project/pyqtconsole#files
   :alt:                Python versions

.. |License| image::    https://img.shields.io/pypi/l/pyqtconsole.svg
   :target:             https://github.com/marcus-oscarsson/pyqtconsole/blob/master/LICENSE
   :alt:                License: MIT

.. |Tests| image::      https://github.com/pyqtconsole/pyqtconsole/workflows/Tests/badge.svg
   :target:             https://github.com/pyqtconsole/pyqtconsole/actions?query=Tests
   :alt:                Test status
