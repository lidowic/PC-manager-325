from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(slots=True)
class AgentConfig:
    host: str = "0.0.0.0"
    port: int = 9021
    allow_insecure: bool = True
    read_chunk_size: int = 4096
    command_timeout: int = 60
    script_timeout: int = 300
    default_shell: str = "auto"
    allowed_public_keys: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: str) -> "AgentConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(**data)
