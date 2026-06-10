from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)

from client.db.repository import MachineRepository
from client.models.script_template import ScriptTemplate


class TaskForm(QWidget):
    def __init__(self, repository: MachineRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.script_edit = QTextEdit(self)
        self.script_edit.setPlaceholderText("Get-ComputerInfo | Select-Object WindowsProductName\nwhoami\n")
        self.shell_combo = QComboBox(self)
        self.shell_combo.addItems(["powershell", "cmd", "bash"])
        self.template_combo = QComboBox(self)
        self.load_template_button = QPushButton("Load template", self)
        self.save_template_button = QPushButton("Save as template", self)
        self.delete_template_button = QPushButton("Delete template", self)
        self.run_button = QPushButton("Run on selected machines", self)

        templates_row = QHBoxLayout()
        templates_row.addWidget(self.template_combo)
        templates_row.addWidget(self.load_template_button)
        templates_row.addWidget(self.save_template_button)
        templates_row.addWidget(self.delete_template_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Templates", self))
        layout.addLayout(templates_row)
        layout.addWidget(QLabel("Script", self))
        layout.addWidget(self.script_edit)
        layout.addWidget(QLabel("Shell", self))
        layout.addWidget(self.shell_combo)
        layout.addWidget(self.run_button)

        self.load_template_button.clicked.connect(self.load_selected_template)
        self.save_template_button.clicked.connect(self.save_current_template)
        self.delete_template_button.clicked.connect(self.delete_selected_template)
        self.script_edit.textChanged.connect(self.persist_local_state)
        self.shell_combo.currentTextChanged.connect(self.persist_local_state)

        self.load_local_state()
        self.refresh_templates()

    def payload(self) -> dict:
        return {
            "script": self.script_edit.toPlainText(),
            "shell": self.shell_combo.currentText(),
        }

    def refresh_templates(self) -> None:
        current = self.template_combo.currentText()
        self.template_combo.clear()
        self.template_combo.addItems(self.repository.list_template_names())
        index = self.template_combo.findText(current)
        if index >= 0:
            self.template_combo.setCurrentIndex(index)

    def load_selected_template(self) -> None:
        name = self.template_combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, "No template", "There are no saved templates yet.")
            return
        template = self.repository.get_template_by_name(name)
        if template is None:
            QMessageBox.warning(self, "Missing template", "Selected template was not found.")
            self.refresh_templates()
            return
        self.script_edit.setPlainText(template.body)
        index = self.shell_combo.findText(template.shell)
        if index >= 0:
            self.shell_combo.setCurrentIndex(index)

    def save_current_template(self) -> None:
        name, ok = QInputDialog.getText(self, "Save template", "Template name")
        if not ok or not name.strip():
            return
        self.repository.upsert_template(
            ScriptTemplate(
                id=None,
                name=name.strip(),
                shell=self.shell_combo.currentText(),
                body=self.script_edit.toPlainText(),
            )
        )
        self.refresh_templates()
        index = self.template_combo.findText(name.strip())
        if index >= 0:
            self.template_combo.setCurrentIndex(index)

    def delete_selected_template(self) -> None:
        name = self.template_combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, "No template", "Choose a template to delete.")
            return
        self.repository.delete_template(name)
        self.refresh_templates()

    def load_local_state(self) -> None:
        shell_to_use = self.repository.get_setting(
            "last_shell",
            self.repository.get_setting("default_shell", "powershell"),
        )
        shell_index = self.shell_combo.findText(shell_to_use)
        if shell_index >= 0:
            self.shell_combo.setCurrentIndex(shell_index)
        if self.repository.get_bool_setting("remember_last_script", True):
            self.script_edit.setPlainText(self.repository.get_setting("last_script_text", ""))
        else:
            self.script_edit.clear()

    def persist_local_state(self) -> None:
        self.repository.set_setting("last_shell", self.shell_combo.currentText())
        if self.repository.get_bool_setting("remember_last_script", True):
            self.repository.set_setting("last_script_text", self.script_edit.toPlainText())
