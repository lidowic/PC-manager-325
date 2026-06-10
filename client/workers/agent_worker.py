from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from client.api.agent_client import AgentClient
from client.models.machine import Machine


class AgentWorkerSignals(QObject):
    finished = pyqtSignal(object, object)
    event = pyqtSignal(object, object)


class AgentWorker(QRunnable):
    def __init__(self, api: AgentClient, machine: Machine, action: str, payload: dict | None = None) -> None:
        super().__init__()
        self.api = api
        self.machine = machine
        self.action = action
        self.payload = payload or {}
        self.signals = AgentWorkerSignals()

    def run(self) -> None:
        try:
            response = self.api.send_request(
                self.machine.host,
                self.machine.port,
                self.action,
                self.payload,
                on_event=lambda message: self.signals.event.emit(self.machine, message),
            )
        except Exception as exc:
            response = {
                "type": "response",
                "status": "error",
                "error": {"code": "CLIENT_ERROR", "message": str(exc)},
                "payload": None,
            }
        self.signals.finished.emit(self.machine, response)
