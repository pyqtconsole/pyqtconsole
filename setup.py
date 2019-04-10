#!/usr/bin/env python
import pyqtconsole
from setuptools import setup

setup(
    name='pyqtconsole',
    version=pyqtconsole.__version__,
    description=pyqtconsole.__description__,
    author=pyqtconsole.__author__,
    author_email=pyqtconsole.__author_email__,
    url=pyqtconsole.__url__,
    license='MIT',
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    keywords='interactive interpreter console shell autocompletion jedi qt',
    packages=['pyqtconsole', 'pyqtconsole.qt', 'pyqtconsole.extensions'],
    python_requires='>=2.7',
    extras_require={
        'autocomplete': ['jedi'],
    },
    zip_safe=True,
    include_package_data=True,
)
