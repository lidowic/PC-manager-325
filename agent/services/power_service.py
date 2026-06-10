from __future__ import annotations

import platform

from agent.services.command_runner import CommandRunner


class PowerService:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    async def shutdown(self) -> dict:
        if platform.system() == "Windows":
            return await self.runner.run_command("shutdown /s /t 0", timeout=10)
        return await self.runner.run_command("sudo shutdown now", timeout=10)

    async def reboot(self) -> dict:
        if platform.system() == "Windows":
            return await self.runner.run_command("shutdown /r /t 0", timeout=10)
        return await self.runner.run_command("sudo reboot", timeout=10)
