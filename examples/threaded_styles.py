import sys

from pygments.styles import get_all_styles
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from pyqtconsole.console import PythonConsole

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


if __name__ == "__main__":
    app = QApplication([])

    # Create main window with layout
    main_window = QWidget()
    layout = QVBoxLayout()

    # Create style selector combo box
    INITIAL_STYLE = "github-dark"
    style_selector = QComboBox()
    styles = sorted(get_all_styles())
    style_selector.addItems(styles)
    style_selector.setCurrentText(INITIAL_STYLE)

    # Create console
    console = PythonConsole(
        shell_cmd_prefix=True,
        welcome_message=welcome_msg,
        pygments_style=INITIAL_STYLE,
        inprompt=">>>",
        outprompt=" ",
    )
    console.push_local_ns("greet", greet)
    console.push_local_ns("style", change_pygments_style)
    console.interpreter.locals["clear"] = console.clear
    console.eval_in_thread()

    # Connect style selector to console
    style_selector.currentTextChanged.connect(console.setPygmentsStyle)

    # Ensure proper cleanup on window close
    def closeEvent(event):
        """Stop the console's background thread before closing.

        Required because the console runs in a separate thread (via eval_in_thread).
        Without this cleanup, the thread continues running after the window closes,
        causing crashes when it tries to access destroyed Qt objects.
        """
        console.exit()
        event.accept()

    main_window.closeEvent = closeEvent

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
