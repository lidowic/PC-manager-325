from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(slots=True)
class MachineConfig:
    name: str
    host: str
    port: int = 9021
    ssh_port: int = 22
    ssh_user: str = ""
    remote_desktop_url: str = ""


@dataclass(slots=True)
class ClientConfig:
    machines: list[MachineConfig] = field(default_factory=list)
    private_key_path: str = ""
    public_key_path: str = ""
    database_path: str = "client.db"
    connect_timeout: int = 5

    @classmethod
    def from_file(cls, path: str) -> "ClientConfig":
        config_path = Path(path)
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        machines = []
        for item in data.get("machines", []):
            normalized = dict(item)
            if "remote_desktop_url" not in normalized and "novnc_url" in normalized:
                normalized["remote_desktop_url"] = normalized["novnc_url"]
            machines.append(MachineConfig(**normalized))
        database_path = data.get("database_path", "client.db")
        if not Path(database_path).is_absolute():
            database_path = str((config_path.parent / database_path).resolve())
        return cls(
            machines=machines,
            private_key_path=data.get("private_key_path", ""),
            public_key_path=data.get("public_key_path", ""),
            database_path=database_path,
            connect_timeout=data.get("connect_timeout", 5),
        )
