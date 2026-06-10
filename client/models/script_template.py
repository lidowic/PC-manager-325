from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScriptTemplate:
    id: int | None
    name: str
    shell: str
    body: str
