from __future__ import annotations

import asyncio
import platform


class CommandRunner:
    def __init__(self, default_shell: str = "auto") -> None:
        self.default_shell = default_shell

    def _resolve_shell(self, requested_shell: str | None = None) -> str:
        shell = (requested_shell or self.default_shell or "auto").lower()
        if shell != "auto":
            return shell
        return "powershell" if platform.system() == "Windows" else "bash"

    async def run_command(self, command: str, timeout: int) -> dict[str, str | int]:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {"exit_code": -1, "stdout": "", "stderr": "Command timed out"}

        return {
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }

    async def stream_script(
        self,
        script: str,
        timeout: int,
        on_chunk,
        shell: str | None = None,
    ) -> dict[str, int | bool | str]:
        resolved_shell = self._resolve_shell(shell)
        process = await self._create_script_process(script, resolved_shell)

        async def pump(stream, name: str) -> None:
            while True:
                chunk = await stream.read(1024)
                if not chunk:
                    break
                await on_chunk(name, chunk.decode("utf-8", errors="replace"))

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    pump(process.stdout, "stdout"),
                    pump(process.stderr, "stderr"),
                    process.wait(),
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {"exit_code": -1, "timed_out": True, "shell": resolved_shell}

        return {"exit_code": process.returncode, "timed_out": False, "shell": resolved_shell}

    async def _create_script_process(self, script: str, shell: str):
        if shell == "powershell":
            return await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        if shell == "cmd":
            return await asyncio.create_subprocess_exec(
                "cmd",
                "/C",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        return await asyncio.create_subprocess_exec(
            "/bin/bash",
            "-lc",
            script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
