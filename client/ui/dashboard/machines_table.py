from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from client.models.machine import Machine


class MachinesTableModel(QAbstractTableModel):
    HEADERS = ["Name", "IP", "Agent Port", "Tags", "Profile", "Status", "Hostname", "Platform"]

    def __init__(self, machines: list[Machine]) -> None:
        super().__init__()
        self.machines = machines

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.machines)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        machine = self.machines[index.row()]
        return [
            machine.name,
            machine.host,
            machine.port,
            ", ".join(machine.tags),
            machine.profile_name,
            machine.status,
            machine.hostname,
            machine.platform,
        ][index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def machine_at(self, row: int) -> Machine:
        return self.machines[row]

    def set_machines(self, machines: list[Machine]) -> None:
        self.beginResetModel()
        self.machines = machines
        self.endResetModel()

    def update_machine(self, row: int, machine: Machine) -> None:
        self.machines[row] = machine
        top_left = self.index(row, 0)
        bottom_right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
