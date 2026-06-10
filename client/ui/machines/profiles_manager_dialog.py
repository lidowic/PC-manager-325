from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from client.db.repository import MachineRepository
from client.models.profile import ConnectionProfile
from client.ui.machines.profile_dialog import ProfileDialog


class ProfilesManagerDialog(QDialog):
    def __init__(self, repository: MachineRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.setWindowTitle("Connection profiles")
        self.resize(500, 360)

        self.list_widget = QListWidget(self)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.add_button = QPushButton("Add", self)
        self.edit_button = QPushButton("Edit", self)
        self.delete_button = QPushButton("Delete", self)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.add_button)
        buttons_row.addWidget(self.edit_button)
        buttons_row.addWidget(self.delete_button)

        close_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        close_buttons.rejected.connect(self.reject)
        close_buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(buttons_row)
        layout.addWidget(close_buttons)

        self.add_button.clicked.connect(self.add_profile)
        self.edit_button.clicked.connect(self.edit_selected_profile)
        self.delete_button.clicked.connect(self.delete_selected_profile)

        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        self.profiles = self.repository.list_profiles()
        self.list_widget.clear()
        for profile in self.profiles:
            label = f"{profile.name} | user={profile.ssh_user or '-'} | timeout={profile.connect_timeout}s"
            self.list_widget.addItem(label)

    def selected_profile(self) -> ConnectionProfile | None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.profiles):
            return None
        return self.profiles[row]

    def add_profile(self) -> None:
        dialog = ProfileDialog(parent=self)
        if dialog.exec():
            self.repository.add_profile(dialog.to_profile())
            self.refresh_profiles()

    def edit_selected_profile(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            QMessageBox.warning(self, "Nothing selected", "Select a profile first.")
            return
        dialog = ProfileDialog(profile=profile, parent=self)
        if dialog.exec():
            self.repository.update_profile(dialog.to_profile())
            self.refresh_profiles()

    def delete_selected_profile(self) -> None:
        profile = self.selected_profile()
        if profile is None:
            QMessageBox.warning(self, "Nothing selected", "Select a profile first.")
            return
        answer = QMessageBox.question(
            self,
            "Delete profile",
            f"Delete profile '{profile.name}'?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.repository.delete_profile(profile.id)
        self.refresh_profiles()
