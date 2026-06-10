from __future__ import annotations

import socket
import time
from typing import Callable

from client.config import ClientConfig
from shared.protocol.codec import decode_message, encode_message
from shared.protocol.models import build_request
from shared.security.keys import read_text_file
from shared.security.signatures import sign_request


class AgentClient:
    def __init__(self, config: ClientConfig) -> None:
        self.config = config
        self._private_key_cache: str | None = None
        self._public_key_cache: str | None = None

    def _load_private_key(self) -> str | None:
        if not self.config.private_key_path:
            return None
        if self._private_key_cache is None:
            self._private_key_cache = read_text_file(self.config.private_key_path)
        return self._private_key_cache

    def _load_public_key(self) -> str | None:
        if not self.config.public_key_path:
            return None
        if self._public_key_cache is None:
            self._public_key_cache = read_text_file(self.config.public_key_path)
        return self._public_key_cache

    def _signed_request(self, action: str, payload: dict, client_id: str = "qt-client") -> dict:
        request = build_request(action=action, payload=payload, client_id=client_id)
        private_key = self._load_private_key()
        public_key = self._load_public_key()
        if private_key and public_key and request.auth is not None:
            request.auth.public_key = public_key
            request.auth.signature = sign_request(
                private_key,
                action,
                payload,
                request.auth.timestamp,
            )
        return request.to_dict()

    def send_request(
        self,
        host: str,
        port: int,
        action: str,
        payload: dict | None = None,
        on_event: Callable[[dict], None] | None = None,
    ) -> dict:
        payload = payload or {}
        request = self._signed_request(action, payload)

        with socket.create_connection((host, port), timeout=self.config.connect_timeout) as sock:
            sock.sendall(encode_message(request))
            with sock.makefile("rb") as fileobj:
                while True:
                    line = fileobj.readline()
                    if not line:
                        raise ConnectionError("Agent closed connection without response")
                    message = decode_message(line)
                    if message.get("type") == "event":
                        if on_event is not None:
                            on_event(message)
                        continue
                    return message

    def ping(self, host: str, port: int) -> dict:
        started = time.perf_counter()
        response = self.send_request(host, port, "ping")
        response.setdefault("latency_ms", round((time.perf_counter() - started) * 1000, 1))
        return response
