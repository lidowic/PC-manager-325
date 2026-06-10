from __future__ import annotations

from agent.domain.machine_info import collect_machine_info


async def handle_get_status() -> dict[str, str]:
    return collect_machine_info()
