# -*- coding: utf-8 -*-
import os

from threading import Condition
from .qt import QtCore

class Stream(QtCore.QObject):
    write_event = QtCore.Signal(str)
    flush_event = QtCore.Signal(str)

    def __init__(self):
        super(Stream, self).__init__()
        self._line_cond = Condition()
        self._buffer = ''

    def _reset_buffer(self):
        data = self._buffer
        self._buffer = ''
        return data

    def _flush(self):
        with self._line_cond:
            data = self._reset_buffer()
            self._line_cond.notify()

        return data

    def readline(self, timeout = None):
        data = ''

        with self._line_cond:
            first_linesep = self._buffer.find(os.linesep)

            # Is there already some lines in the buffer, write might have
            # been called before we read !
            if not first_linesep > -1:
                self._line_cond.wait(timeout)
                first_linesep = self._buffer.find(os.linesep)

            # Check if there really is something in the buffer after waiting
            # for line_cond. There might have been a timeout, and there is
            # still no data available
            if first_linesep > -1:
                data = self._buffer[0:first_linesep+1]

                if len(self._buffer) > len(data):
                    self._buffer = self._buffer[first_linesep+2:]
                else:
                    self._buffer = ''
            else:
                data = ''

        return data

    def write(self, data):
        with self._line_cond:
            self._buffer += data
            self.write_event.emit(data)

            if os.linesep in self._buffer:
                self._line_cond.notify()

    def flush(self):
        data = self._flush()
        self.flush_event.emit(data)
        return data
