#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from qtpy.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                            QHBoxLayout, QComboBox, QLabel)
from pyqtconsole.console import PythonConsole
from pygments.styles import get_all_styles

welcome_msg = """Python Console v1.0
Commands starting with ! are executed as shell commands
"""


def greet():
    print("hello world")


def change_pygments_style(style):
    """change the Pygments style of the console.
    Example styles include:
      'default', 'monokai', 'vim', 'friendly', 'colorful',
      'autumn', 'rainbow_dash', and 'paraiso-dark'."""
    console.setPygmentsStyle(style)


if __name__ == '__main__':
    app = QApplication([])

    # Create main window with layout
    main_window = QWidget()
    layout = QVBoxLayout()

    # Create style selector combo box
    style_selector = QComboBox()
    styles = sorted(get_all_styles())
    style_selector.addItems(styles)
    style_selector.setCurrentText('monokai')

    # Create console
    console = PythonConsole(shell_cmd_prefix=True,
                            welcome_message=welcome_msg,
                            pygments_style='monokai')
    console.push_local_ns('greet', greet)
    console.push_local_ns('style', change_pygments_style)
    console.interpreter.locals["clear"] = console.clear
    console.eval_in_thread()

    # Connect style selector to console
    style_selector.currentTextChanged.connect(console.setPygmentsStyle)

    # Ensure proper cleanup on window close
    def on_close():
        console.exit()
        main_window.close()

    main_window.closeEvent = lambda event: (console.exit(), event.accept())

    # Add widgets to layout
    style_layout = QHBoxLayout()
    style_layout.addWidget(QLabel("Pygments Style:"))
    style_layout.addWidget(style_selector)
    style_layout.addStretch()

    layout.addLayout(style_layout)
    layout.addWidget(console)

    main_window.setLayout(layout)
    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec_())
