from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
)

from client.db.repository import MachineRepository


class ClientSettingsDialog(QDialog):
    def __init__(self, repository: MachineRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.setWindowTitle("Client settings")

        self.default_shell_combo = QComboBox(self)
        self.default_shell_combo.addItems(["powershell", "cmd", "bash"])
        self.auto_refresh_checkbox = QCheckBox("Refresh machine statuses on startup", self)
        self.remember_last_script_checkbox = QCheckBox("Remember last script text", self)

        form = QFormLayout()
        form.addRow("Default shell", self.default_shell_combo)
        form.addRow("", self.auto_refresh_checkbox)
        form.addRow("", self.remember_last_script_checkbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self._load_settings()

    def _load_settings(self) -> None:
        default_shell = self.repository.get_setting("default_shell", "powershell")
        index = self.default_shell_combo.findText(default_shell)
        if index >= 0:
            self.default_shell_combo.setCurrentIndex(index)
        self.auto_refresh_checkbox.setChecked(
            self.repository.get_bool_setting("auto_refresh_on_startup", True)
        )
        self.remember_last_script_checkbox.setChecked(
            self.repository.get_bool_setting("remember_last_script", True)
        )

    def accept(self) -> None:
        shell = self.default_shell_combo.currentText()
        self.repository.set_setting("default_shell", shell)
        self.repository.set_setting("last_shell", shell)
        self.repository.set_setting(
            "auto_refresh_on_startup",
            "1" if self.auto_refresh_checkbox.isChecked() else "0",
        )
        self.repository.set_setting(
            "remember_last_script",
            "1" if self.remember_last_script_checkbox.isChecked() else "0",
        )
        if not self.remember_last_script_checkbox.isChecked():
            self.repository.set_setting("last_script_text", "")
        super().accept()
