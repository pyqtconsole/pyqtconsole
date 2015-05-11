#!/usr/bin/env python
import pyqtconsole
from distutils.core import setup

setup(name='pyqtconsole',
    version=pyqtconsole.__version__,
    description=pyqtconsole.__description__,
    author=pyqtconsole.__author__,
    author_email=pyqtconsole.__author_email__,
    url=pyqtconsole.__url__,
    packages=['pyqtconsole', 'pyqtconsole.qt'])
