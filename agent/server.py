from __future__ import annotations

import asyncio
import logging
from typing import Any

from agent.config import AgentConfig
from agent.domain.machine_info import collect_machine_info
from agent.handlers.ping import handle_ping
from agent.handlers.scripts import handle_run_command
from agent.handlers.tunnel import handle_open_tunnel
from agent.services.command_runner import CommandRunner
from agent.services.power_service import PowerService
from agent.services.ssh_tunnel_service import SSHTunnelService
from shared.protocol.codec import decode_message, encode_message
from shared.protocol.models import EventMessage, error_response, ok_response
from shared.security.auth import validate_auth_envelope

logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.runner = CommandRunner(default_shell=config.default_shell)
        self.power_service = PowerService(self.runner)
        self.tunnel_service = SSHTunnelService()

    async def start(self) -> None:
        server = await asyncio.start_server(self.handle_client, self.config.host, self.config.port)
        sockets = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        logger.info("Agent listening on %s", sockets)
        async with server:
            await server.serve_forever()

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info("peername")
        logger.info("Accepted connection from %s", peer)
        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                message_id: str | None = None
                try:
                    message = decode_message(line)
                    message_id = message.get("id")
                    is_valid, auth_error = validate_auth_envelope(
                        message,
                        self.config.allowed_public_keys,
                        self.config.allow_insecure,
                    )
                    if not is_valid:
                        await self.send(writer, error_response(message_id, "AUTH_FAILED", auth_error or "auth failed").to_dict())
                        continue
                    response = await self.dispatch(message, writer)
                    if response is not None:
                        await self.send(writer, response)
                except Exception as exc:
                    logger.exception("Client handling error")
                    await self.send(writer, error_response(message_id, "INTERNAL_ERROR", str(exc)).to_dict())
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info("Closed connection from %s", peer)

    async def dispatch(self, message: dict[str, Any], writer: asyncio.StreamWriter) -> dict[str, Any] | None:
        action = message.get("action")
        payload = message.get("payload", {})
        message_id = message.get("id")

        if action == "ping":
            return ok_response(message_id, await handle_ping()).to_dict()

        if action == "get_status":
            return ok_response(message_id, collect_machine_info()).to_dict()

        if action == "run_command":
            result = await handle_run_command(
                self.runner,
                payload["command"],
                int(payload.get("timeout", self.config.command_timeout)),
            )
            return ok_response(message_id, result).to_dict()

        if action == "run_script":
            async def on_chunk(stream_name: str, chunk: str) -> None:
                event = EventMessage(
                    id=message_id,
                    event="script_output",
                    payload={"stream": stream_name, "chunk": chunk},
                )
                await self.send(writer, event.to_dict())

            result = await self.runner.stream_script(
                payload["script"],
                int(payload.get("timeout", self.config.script_timeout)),
                on_chunk,
                payload.get("shell"),
            )
            return ok_response(message_id, result).to_dict()

        if action == "shutdown":
            result = await self.power_service.shutdown()
            return ok_response(message_id, result).to_dict()

        if action == "reboot":
            result = await self.power_service.reboot()
            return ok_response(message_id, result).to_dict()

        if action == "open_ssh_tunnel":
            result = await handle_open_tunnel(
                self.tunnel_service,
                int(payload["local_port"]),
                payload["remote_host"],
                int(payload["remote_port"]),
            )
            return ok_response(message_id, result).to_dict()

        return error_response(message_id, "UNKNOWN_ACTION", f"Unsupported action: {action}").to_dict()

    async def send(self, writer: asyncio.StreamWriter, message: dict[str, Any]) -> None:
        writer.write(encode_message(message))
        await writer.drain()
