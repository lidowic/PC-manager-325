from __future__ import annotations

from agent.services.ssh_tunnel_service import SSHTunnelService


async def handle_open_tunnel(
    service: SSHTunnelService,
    local_port: int,
    remote_host: str,
    remote_port: int,
) -> dict:
    return service.describe_tunnel(local_port, remote_host, remote_port)
