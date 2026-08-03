import sys
import code
import io
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QPlainTextEdit, QLineEdit, QPushButton, QLabel)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt


class PythonShellWindow(QDialog):
    def __init__(self, parent=None, local_vars=None):
        super().__init__(parent)
        self.setWindowTitle("Python Shell")
        self.setMinimumSize(700, 500)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(self)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Monospace", 10))
        self.output.appendPlainText("Python " + sys.version)
        self.output.appendPlainText("studio is available as 'studio'\n")
        layout.addWidget(self.output)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(">>>"))
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Monospace", 10))
        self.input_line.returnPressed.connect(self.execute)
        input_layout.addWidget(self.input_line)
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.execute)
        input_layout.addWidget(run_btn)
        layout.addLayout(input_layout)

        self.history = []
        self.history_idx = 0
        self.console = code.InteractiveConsole(locals=local_vars or {})

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up and self.history:
            self.history_idx = max(0, self.history_idx - 1)
            self.input_line.setText(self.history[self.history_idx])
        elif event.key() == Qt.Key_Down and self.history:
            self.history_idx = min(len(self.history), self.history_idx + 1)
            self.input_line.setText(
                self.history[self.history_idx] if self.history_idx < len(self.history) else ""
            )
        else:
            super().keyPressEvent(event)

    def execute(self):
        cmd = self.input_line.text()
        if not cmd.strip():
            return
        self.history.append(cmd)
        self.history_idx = len(self.history)
        self.output.appendPlainText(f">>> {cmd}")

        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            self.console.push(cmd)
        finally:
            out = sys.stdout.getvalue()
            err = sys.stderr.getvalue()
            sys.stdout, sys.stderr = old_stdout, old_stderr

        if out:
            self.output.appendPlainText(out.rstrip())
        if err:
            self.output.appendPlainText(err.rstrip())

        self.input_line.clear()
        self.output.moveCursor(QTextCursor.End)


def open_python_shell(parent=None, local_vars=None):
    shell = PythonShellWindow(parent=parent, local_vars=local_vars)
    shell.show()
    return shell
