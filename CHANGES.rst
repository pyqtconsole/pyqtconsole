Changelog
~~~~~~~~~

v1.3.0
------
Date: 17.02.2026

- migrated from ``setup.py`` + ``setup.cfg`` to ``pyproject.toml``
- dropped official support for Python 3.8 and added 3.13 and 3.14 (no code changes)
- fixed issue with displaying syntax errors for Python 3.13
- fixed issue with multibyte characters (emojis) breaking the input (`#87 <https://github.com/pyqtconsole/pyqtconsole/issues/87>`__)
- added optional built-in method to clear all input (`#58 <https://github.com/pyqtconsole/pyqtconsole/issues/58>`__)
- added optional escape character to execute system commands (e.g ``!ls -l``) (`#93 <https://github.com/pyqtconsole/pyqtconsole/issues/93>`__)
- added option to change the prompt placeholder strings (`#68 <https://github.com/pyqtconsole/pyqtconsole/issues/68>`__)
- fixed issues in string highlighting (`#69 <https://github.com/pyqtconsole/pyqtconsole/issues/69>`__)

v1.2.3
------
Date: 19.09.2023

- fixed indentation and autocomplete conflict (#74)
- replaced ``QRegExp`` for compatibility with QT6 (#76)

v1.2.2
------
Date: 18.10.2021

- fixed PyQt warning because of explicit integer type
- fixed jedi autocomplete because of method rename

v1.2.1
------
Date: 17.03.2020

- fix accepting input with AltGr modifier on win10 (#53)


v1.2.0
------
Date: 17.03.2020

- add PySide2 compatibility
- add Ctrl-U shortcut to clear the input buffer
- use standard QtPy package to provide the compatibility layer
- hide the cursor during the execution of a python command
- mimic shell behaviour when using up and down key to go to end of history
- fix crash when closing the interpreter window of the threaded example
- disable excepthook on displaying exception
- write '\n' before syntax errors for consistency

Thanks to @roberthdevries and @irgolic for their contributions!


v1.1.5
------
Date: 25.11.2019

- fix TypeError in highlighter when called without formats


v1.1.4
------
Date: 21.11.2019

- fix AttributeError due to QueuedConnection on PyQt<5.11 (#23)
- fix exception on import when started within spyder (#26)
- fix gevent example to incorporate interoperability code for gevent/Qt (#28)
- fix not waiting for empty line when entering code blocks before applying input (#30)
- fix TypeError during compilation step on python 3.8
- allow user to override syntax highlighting color preferences (#29)
  note that this is provisional API
- automate release process (#34)
