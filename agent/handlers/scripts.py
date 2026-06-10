from __future__ import annotations

from agent.services.command_runner import CommandRunner


async def handle_run_command(runner: CommandRunner, command: str, timeout: int) -> dict:
    return await runner.run_command(command, timeout=timeout)
