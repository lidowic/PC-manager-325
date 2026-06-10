from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QTableView, QVBoxLayout, QWidget

from client.models.machine import Machine
from client.ui.dashboard.machines_table import MachinesTableModel


class DashboardWidget(QWidget):
    def __init__(self, machines: list[Machine], parent=None) -> None:
        super().__init__(parent)
        self.model = MachinesTableModel(machines)
        self.table = QTableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.refresh_button = QPushButton("Refresh status", self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

    def selected_machine(self) -> Machine | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.machine_at(indexes[0].row())

    def selected_machines(self) -> list[Machine]:
        return [self.model.machine_at(index.row()) for index in self.table.selectionModel().selectedRows()]
