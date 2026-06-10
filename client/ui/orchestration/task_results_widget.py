from __future__ import annotations

from PyQt6.QtWidgets import QPlainTextEdit


class TaskResultsWidget(QPlainTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def append_line(self, text: str) -> None:
        current = self.toPlainText()
        self.setPlainText(f"{current}{text}\n" if current else f"{text}\n")
