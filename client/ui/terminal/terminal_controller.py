from __future__ import annotations

from client.ui.terminal.ansi_renderer import AnsiTerminalBuffer


class TerminalController:
    def __init__(self, columns: int = 120, rows: int = 40) -> None:
        self.buffer = AnsiTerminalBuffer(columns=columns, rows=rows)

    def on_data(self, data: bytes) -> str:
        return self.buffer.feed(data)

    def resize(self, columns: int, rows: int) -> None:
        self.buffer.resize(columns, rows)
