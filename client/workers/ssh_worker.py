from __future__ import annotations

import socket
import threading
from pathlib import Path

import paramiko
from PyQt6.QtCore import QObject, pyqtSignal


class SSHWorker(QObject):
    data_received = pyqtSignal(bytes)
    error = pyqtSignal(str)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(
        self,
        host: str,
        username: str,
        key_filename: str,
        port: int = 22,
        connect_timeout: int = 10,
    ) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.key_filename = key_filename
        self.connect_timeout = connect_timeout
        self.client: paramiko.SSHClient | None = None
        self.channel: paramiko.Channel | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def connect(self) -> None:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                key_filename=str(Path(self.key_filename).expanduser()),
                allow_agent=False,
                look_for_keys=False,
                timeout=self.connect_timeout,
            )
            self.channel = self.client.invoke_shell(term="xterm-256color", width=120, height=40)
            self.channel.settimeout(0.2)
            self._running = True
            self._thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._thread.start()
            self.connected.emit()
        except Exception as exc:
            self.error.emit(str(exc))

    def _reader_loop(self) -> None:
        assert self.channel is not None
        while self._running:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if not data:
                        break
                    self.data_received.emit(data)
            except socket.timeout:
                continue
            except Exception as exc:
                self.error.emit(str(exc))
                break
        self.disconnected.emit()

    def send_text(self, text: str) -> None:
        if self.channel:
            self.channel.send(text)

    def resize_pty(self, cols: int, rows: int) -> None:
        if self.channel:
            self.channel.resize_pty(width=cols, height=rows)

    def close(self) -> None:
        self._running = False
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()
