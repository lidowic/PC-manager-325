from __future__ import annotations

import ipaddress


def iter_hosts(cidr: str) -> list[str]:
    network = ipaddress.ip_network(cidr, strict=False)
    return [str(host) for host in network.hosts()]
