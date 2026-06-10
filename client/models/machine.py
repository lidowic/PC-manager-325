from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Machine:
    id: int | None
    name: str
    host: str
    port: int
    ssh_port: int
    ssh_user: str
    remote_desktop_url: str
    profile_id: int | None = None
    profile_name: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "unknown"
    hostname: str = ""
    platform: str = ""
