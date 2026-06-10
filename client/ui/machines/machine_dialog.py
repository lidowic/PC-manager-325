from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from client.models.machine import Machine
from client.models.profile import ConnectionProfile


class MachineDialog(QDialog):
    def __init__(
        self,
        machine: Machine | None = None,
        profiles: list[ConnectionProfile] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit machine" if machine else "Add machine")
        self._machine = machine
        self._profiles = profiles or []

        self.name_input = QLineEdit(self)
        self.host_input = QLineEdit(self)
        self.agent_port_input = QSpinBox(self)
        self.agent_port_input.setRange(1, 65535)
        self.agent_port_input.setValue(9021)
        self.ssh_port_input = QSpinBox(self)
        self.ssh_port_input.setRange(1, 65535)
        self.ssh_port_input.setValue(22)
        self.ssh_user_input = QLineEdit(self)
        self.remote_desktop_input = QLineEdit(self)
        self.profile_combo = QComboBox(self)
        self.tags_input = QLineEdit(self)

        self.profile_combo.addItem("No profile", None)
        for profile in self._profiles:
            self.profile_combo.addItem(profile.name, profile.id)

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("Host", self.host_input)
        form.addRow("Agent port", self.agent_port_input)
        form.addRow("SSH port", self.ssh_port_input)
        form.addRow("SSH user", self.ssh_user_input)
        form.addRow("Profile", self.profile_combo)
        form.addRow("Tags", self.tags_input)
        form.addRow("Remote desktop URL", self.remote_desktop_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if machine is not None:
            self._load_machine(machine)

    def _load_machine(self, machine: Machine) -> None:
        self.name_input.setText(machine.name)
        self.host_input.setText(machine.host)
        self.agent_port_input.setValue(machine.port)
        self.ssh_port_input.setValue(machine.ssh_port)
        self.ssh_user_input.setText(machine.ssh_user)
        profile_index = self.profile_combo.findData(machine.profile_id)
        if profile_index >= 0:
            self.profile_combo.setCurrentIndex(profile_index)
        self.tags_input.setText(", ".join(machine.tags))
        self.remote_desktop_input.setText(machine.remote_desktop_url)

    def accept(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation error", "Machine name is required.")
            return
        if not self.host_input.text().strip():
            QMessageBox.warning(self, "Validation error", "Host is required.")
            return
        super().accept()

    def to_machine(self) -> Machine:
        return Machine(
            id=self._machine.id if self._machine else None,
            name=self.name_input.text().strip(),
            host=self.host_input.text().strip(),
            port=self.agent_port_input.value(),
            ssh_port=self.ssh_port_input.value(),
            ssh_user=self.ssh_user_input.text().strip(),
            profile_id=self.profile_combo.currentData(),
            tags=[item.strip() for item in self.tags_input.text().split(",") if item.strip()],
            remote_desktop_url=self.remote_desktop_input.text().strip(),
        )
