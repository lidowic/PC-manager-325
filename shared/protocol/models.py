from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from shared.protocol.enums import MessageType, Status


@dataclass(slots=True)
class AuthEnvelope:
    client_id: str
    timestamp: int
    public_key: str | None = None
    signature: str | None = None


@dataclass(slots=True)
class RequestMessage:
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    auth: AuthEnvelope | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = MessageType.REQUEST.value

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.auth is None:
            data["auth"] = None
        return data


@dataclass(slots=True)
class ResponseMessage:
    id: str | None
    status: str
    payload: dict[str, Any] | None = None
    error: dict[str, str] | None = None
    type: str = MessageType.RESPONSE.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EventMessage:
    id: str | None
    event: str
    payload: dict[str, Any] = field(default_factory=dict)
    type: str = MessageType.EVENT.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_request(
    action: str,
    payload: dict[str, Any] | None = None,
    client_id: str = "client",
) -> RequestMessage:
    return RequestMessage(
        action=action,
        payload=payload or {},
        auth=AuthEnvelope(client_id=client_id, timestamp=int(time.time())),
    )


def ok_response(message_id: str | None, payload: dict[str, Any] | None = None) -> ResponseMessage:
    return ResponseMessage(id=message_id, status=Status.OK.value, payload=payload or {}, error=None)


def error_response(message_id: str | None, code: str, message: str) -> ResponseMessage:
    return ResponseMessage(
        id=message_id,
        status=Status.ERROR.value,
        payload=None,
        error={"code": code, "message": message},
    )
