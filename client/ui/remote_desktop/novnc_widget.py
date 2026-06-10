from __future__ import annotations

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView


class NoVNCWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.view = QWebEngineView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)

    def load_url(self, url: str) -> None:
        self.view.load(QUrl(url))
