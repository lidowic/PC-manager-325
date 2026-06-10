from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from client.models.profile import ConnectionProfile


class ProfileDialog(QDialog):
    def __init__(self, profile: ConnectionProfile | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit profile" if profile else "Add profile")
        self._profile = profile

        self.name_input = QLineEdit(self)
        self.ssh_user_input = QLineEdit(self)
        self.private_key_input = QLineEdit(self)
        self.public_key_input = QLineEdit(self)
        self.connect_timeout_input = QSpinBox(self)
        self.connect_timeout_input.setRange(1, 300)
        self.connect_timeout_input.setValue(5)

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("SSH user", self.ssh_user_input)
        form.addRow("Private key path", self.private_key_input)
        form.addRow("Public key path", self.public_key_input)
        form.addRow("Connect timeout", self.connect_timeout_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if profile is not None:
            self._load_profile(profile)

    def _load_profile(self, profile: ConnectionProfile) -> None:
        self.name_input.setText(profile.name)
        self.ssh_user_input.setText(profile.ssh_user)
        self.private_key_input.setText(profile.private_key_path)
        self.public_key_input.setText(profile.public_key_path)
        self.connect_timeout_input.setValue(profile.connect_timeout)

    def accept(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation error", "Profile name is required.")
            return
        super().accept()

    def to_profile(self) -> ConnectionProfile:
        return ConnectionProfile(
            id=self._profile.id if self._profile else None,
            name=self.name_input.text().strip(),
            ssh_user=self.ssh_user_input.text().strip(),
            private_key_path=self.private_key_input.text().strip(),
            public_key_path=self.public_key_input.text().strip(),
            connect_timeout=self.connect_timeout_input.value(),
        )
