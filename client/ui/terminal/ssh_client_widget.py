from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent, QTextCursor
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from client.ui.terminal.terminal_controller import TerminalController
from client.workers.ssh_worker import SSHWorker


class TerminalTextEdit(QPlainTextEdit):
    def __init__(self, send_callback: Callable[[str], None], parent=None) -> None:
        super().__init__(parent)
        self.send_callback = send_callback
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont("Consolas", 10))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        mapping = {
            Qt.Key.Key_Return: "\r",
            Qt.Key.Key_Enter: "\r",
            Qt.Key.Key_Backspace: "\x7f",
            Qt.Key.Key_Tab: "\t",
            Qt.Key.Key_Left: "\x1b[D",
            Qt.Key.Key_Right: "\x1b[C",
            Qt.Key.Key_Up: "\x1b[A",
            Qt.Key.Key_Down: "\x1b[B",
            Qt.Key.Key_Home: "\x1b[H",
            Qt.Key.Key_End: "\x1b[F",
            Qt.Key.Key_Delete: "\x1b[3~",
        }
        if event.key() in mapping:
            self.send_callback(mapping[event.key()])
            return
        text = event.text()
        if text:
            self.send_callback(text)
            return
        super().keyPressEvent(event)


class SSHClientWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.worker: SSHWorker | None = None
        self.controller = TerminalController()
        self.connect_timeout = 10

        self.host_input = QLineEdit(self)
        self.port_input = QLineEdit("22", self)
        self.user_input = QLineEdit(self)
        self.key_input = QLineEdit(self)
        self.connect_button = QPushButton("Connect", self)
        self.disconnect_button = QPushButton("Disconnect", self)
        self.status_label = QLabel("Disconnected", self)
        self.terminal = TerminalTextEdit(self._send_text, self)
        self.terminal.setReadOnly(False)

        form = QFormLayout()
        form.addRow("Host", self.host_input)
        form.addRow("Port", self.port_input)
        form.addRow("User", self.user_input)
        form.addRow("Private key", self.key_input)

        buttons = QHBoxLayout()
        buttons.addWidget(self.connect_button)
        buttons.addWidget(self.disconnect_button)
        buttons.addWidget(self.status_label)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.terminal)

        self.connect_button.clicked.connect(self.connect_ssh)
        self.disconnect_button.clicked.connect(self.disconnect_ssh)

    def fill_from_machine(
        self,
        host: str,
        port: int,
        username: str,
        key_path: str,
        connect_timeout: int = 10,
    ) -> None:
        self.host_input.setText(host)
        self.port_input.setText(str(port))
        self.user_input.setText(username)
        self.connect_timeout = connect_timeout
        if key_path:
            self.key_input.setText(key_path)

    def connect_ssh(self) -> None:
        self.disconnect_ssh()
        self.worker = SSHWorker(
            host=self.host_input.text().strip(),
            port=int(self.port_input.text().strip() or "22"),
            username=self.user_input.text().strip(),
            key_filename=self.key_input.text().strip(),
            connect_timeout=self.connect_timeout,
        )
        self.worker.data_received.connect(self._on_data)
        self.worker.error.connect(self._on_error)
        self.worker.connected.connect(lambda: self.status_label.setText("Connected"))
        self.worker.disconnected.connect(lambda: self.status_label.setText("Disconnected"))
        self.worker.connect()

    def disconnect_ssh(self) -> None:
        if self.worker is not None:
            self.worker.close()
            self.worker = None
        self.status_label.setText("Disconnected")

    def _send_text(self, text: str) -> None:
        if self.worker:
            self.worker.send_text(text)

    def _on_data(self, data: bytes) -> None:
        rendered = self.controller.on_data(data)
        self.terminal.setPlainText(rendered)
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.terminal.setTextCursor(cursor)

    def _on_error(self, message: str) -> None:
        self.status_label.setText("Error")
        QMessageBox.critical(self, "SSH error", message)

    def closeEvent(self, event) -> None:
        self.disconnect_ssh()
        super().closeEvent(event)
