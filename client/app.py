from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from client.config import ClientConfig
from client.ui.main_window import MainWindow


def run_app(config: ClientConfig) -> int:
    app = QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    return app.exec()
