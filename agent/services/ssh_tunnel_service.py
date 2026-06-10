from __future__ import annotations


class SSHTunnelService:
    def describe_tunnel(self, local_port: int, remote_host: str, remote_port: int) -> dict[str, str | int]:
        return {
            "local_port": local_port,
            "remote_host": remote_host,
            "remote_port": remote_port,
            "message": "Use system ssh for the actual tunnel setup on the client side.",
        }
