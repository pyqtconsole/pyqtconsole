Changelog
~~~~~~~~~

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
