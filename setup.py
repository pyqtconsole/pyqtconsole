import setuptools
import pyqtconsole


with open("README.rst", "r") as fh:
    long_description = fh.read()


setuptools.setup(name='pyqtconsole',
                 version=pyqtconsole.__version__,
                 description=pyqtconsole.__description__,
                 author=pyqtconsole.__author__,
                 author_email=pyqtconsole.__author_email__,
                 url=pyqtconsole.__url__,
                 long_description=long_description,
                 packages=['pyqtconsole', 'pyqtconsole.qt', 'pyqtconsole.extensions'])
