from __future__ import annotations

from pathlib import Path


def read_text_file(path: str | Path) -> str:
    return Path(path).expanduser().read_text(encoding="utf-8").strip()
