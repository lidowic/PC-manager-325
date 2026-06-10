from __future__ import annotations

import pyte


class AnsiTerminalBuffer:
    def __init__(self, columns: int = 120, rows: int = 40) -> None:
        self.columns = columns
        self.rows = rows
        self.screen = pyte.Screen(columns, rows)
        self.stream = pyte.Stream(self.screen)

    def feed(self, data: bytes) -> str:
        self.stream.feed(data.decode("utf-8", errors="replace"))
        return "\n".join("".join(line) for line in self.screen.display)

    def resize(self, columns: int, rows: int) -> None:
        self.columns = columns
        self.rows = rows
        self.screen = pyte.Screen(columns, rows)
        self.stream = pyte.Stream(self.screen)
