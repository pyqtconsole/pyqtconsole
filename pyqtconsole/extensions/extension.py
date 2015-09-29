# -*- coding: utf-8 -*-
from ..qt import QtCore

class ExtensionManager(object):
    def __init__(self, owner):
        self._owner = owner
        self._extension_list = []

    def install(self, ext_cls):
        ext = ext_cls()
        ext.install(self._owner)
        self._extension_list.append(ext)


class Extension(QtCore.QObject):
    # Abstract
    def install(self, parent):
        pass
