from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConnectionProfile:
    id: int | None
    name: str
    ssh_user: str = ""
    private_key_path: str = ""
    public_key_path: str = ""
    connect_timeout: int = 5
