from __future__ import annotations

from enum import StrEnum


class MessageType(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"


class Status(StrEnum):
    OK = "ok"
    ERROR = "error"
