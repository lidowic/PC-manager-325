from __future__ import annotations

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from client.api.agent_client import AgentClient
from client.config import ClientConfig
from client.db.repository import MachineRepository
from client.models.machine import Machine
from client.ui.dashboard.dashboard_widget import DashboardWidget
from client.ui.machines.machine_dialog import MachineDialog
from client.ui.machines.profiles_manager_dialog import ProfilesManagerDialog
from client.ui.orchestration.task_form import TaskForm
from client.ui.orchestration.task_results_widget import TaskResultsWidget
from client.ui.remote_desktop.novnc_widget import NoVNCWidget
from client.ui.settings.client_settings_dialog import ClientSettingsDialog
from client.ui.terminal.ssh_client_widget import SSHClientWidget
from client.workers.agent_worker import AgentWorker


class MainWindow(QMainWindow):
    def __init__(self, config: ClientConfig) -> None:
        super().__init__()
        self.config = config
        self.api = AgentClient(config)
        self.repository = MachineRepository(config.database_path)
        self.repository.initialize()
        self.repository.bootstrap_from_config(config.machines)
        self.thread_pool = QThreadPool.globalInstance()
        self.machines = self.repository.list_machines()
        self.worker_count = 0

        self.setWindowTitle("PC Remote Admin")
        self.resize(1440, 900)

        self.dashboard = DashboardWidget(self.machines, self)
        self.task_form = TaskForm(self.repository, self)
        self.task_results = TaskResultsWidget(self)
        self.ssh_widget = SSHClientWidget(self)
        self.novnc_widget = NoVNCWidget(self)

        self.refresh_all_button = QPushButton("Refresh all", self)
        self.add_machine_button = QPushButton("Add machine", self)
        self.edit_machine_button = QPushButton("Edit machine", self)
        self.delete_machine_button = QPushButton("Delete machine", self)
        self.profiles_button = QPushButton("Profiles", self)
        self.settings_button = QPushButton("Client settings", self)
        self.shutdown_button = QPushButton("Shutdown selected", self)
        self.reboot_button = QPushButton("Reboot selected", self)

        tabs = QTabWidget(self)
        orchestration_page = QWidget(self)
        orchestration_layout = QVBoxLayout(orchestration_page)
        orchestration_layout.addWidget(self.task_form)
        orchestration_layout.addWidget(self.task_results)
        tabs.addTab(orchestration_page, "Task orchestration")
        tabs.addTab(self.ssh_widget, "SSH terminal")
        tabs.addTab(self.novnc_widget, "Remote desktop")

        left_controls = QHBoxLayout()
        left_controls.addWidget(self.refresh_all_button)
        left_controls.addWidget(self.add_machine_button)
        left_controls.addWidget(self.edit_machine_button)
        left_controls.addWidget(self.delete_machine_button)
        left_controls.addWidget(self.profiles_button)
        left_controls.addWidget(self.settings_button)
        left_controls.addWidget(self.shutdown_button)
        left_controls.addWidget(self.reboot_button)

        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addLayout(left_controls)
        left_layout.addWidget(self.dashboard)

        splitter = QSplitter(self)
        splitter.addWidget(left_panel)
        splitter.addWidget(tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        self.setCentralWidget(splitter)

        self.refresh_all_button.clicked.connect(self.refresh_all)
        self.dashboard.refresh_button.clicked.connect(self.refresh_all)
        self.add_machine_button.clicked.connect(self.add_machine)
        self.edit_machine_button.clicked.connect(self.edit_selected_machine)
        self.delete_machine_button.clicked.connect(self.delete_selected_machines)
        self.profiles_button.clicked.connect(self.manage_profiles)
        self.settings_button.clicked.connect(self.open_client_settings)
        self.shutdown_button.clicked.connect(lambda: self.run_single_action("shutdown"))
        self.reboot_button.clicked.connect(lambda: self.run_single_action("reboot"))
        self.task_form.run_button.clicked.connect(self.run_script_on_selected)
        self.dashboard.table.selectionModel().selectionChanged.connect(self.on_machine_selected)

        if self.repository.get_bool_setting("auto_refresh_on_startup", True):
            self.refresh_all()

    def on_machine_selected(self) -> None:
        machine = self.dashboard.selected_machine()
        if machine is None:
            return
        ssh_user = machine.ssh_user
        key_path = self.config.private_key_path
        connect_timeout = self.config.connect_timeout
        if machine.profile_id is not None:
            profile = self._profile_map().get(machine.profile_id)
            if profile is not None:
                if not ssh_user:
                    ssh_user = profile.ssh_user
                if profile.private_key_path:
                    key_path = profile.private_key_path
                if profile.connect_timeout:
                    connect_timeout = profile.connect_timeout
        self.ssh_widget.fill_from_machine(
            host=machine.host,
            port=machine.ssh_port,
            username=ssh_user,
            key_path=key_path,
            connect_timeout=connect_timeout,
        )
        if machine.remote_desktop_url:
            self.novnc_widget.load_url(machine.remote_desktop_url)

    def refresh_all(self) -> None:
        for machine in self.machines:
            self.start_worker(machine, "get_status")

    def add_machine(self) -> None:
        dialog = MachineDialog(parent=self, profiles=self.repository.list_profiles())
        if dialog.exec():
            created = self.repository.add_machine(dialog.to_machine())
            self.reload_machines(selected_machine_id=created.id)

    def edit_selected_machine(self) -> None:
        machine = self.dashboard.selected_machine()
        if machine is None:
            QMessageBox.warning(self, "No machine selected", "Select a machine in the dashboard first.")
            return
        dialog = MachineDialog(machine=machine, profiles=self.repository.list_profiles(), parent=self)
        if dialog.exec():
            updated = dialog.to_machine()
            updated.status = machine.status
            updated.hostname = machine.hostname
            updated.platform = machine.platform
            self.repository.update_machine(updated)
            self.reload_machines(selected_machine_id=updated.id)

    def delete_selected_machines(self) -> None:
        selected = self.dashboard.selected_machines()
        if not selected:
            QMessageBox.warning(self, "Nothing selected", "Select one or more machines to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete machines",
            f"Delete {len(selected)} selected machine(s)?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        for machine in selected:
            if machine.id is not None:
                self.repository.delete_machine(machine.id)
        self.reload_machines()

    def manage_profiles(self) -> None:
        dialog = ProfilesManagerDialog(self.repository, parent=self)
        if dialog.exec():
            self.reload_machines()
        else:
            self.reload_machines()

    def open_client_settings(self) -> None:
        dialog = ClientSettingsDialog(self.repository, parent=self)
        if dialog.exec():
            self.task_form.load_local_state()

    def run_single_action(self, action: str) -> None:
        machine = self.dashboard.selected_machine()
        if machine is None:
            QMessageBox.warning(self, "No machine selected", "Select a machine in the dashboard first.")
            return
        self.start_worker(machine, action)

    def run_script_on_selected(self) -> None:
        selected = self.dashboard.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Nothing selected", "Select one or more machines in the dashboard.")
            return
        for index in selected:
            machine = self.dashboard.model.machine_at(index.row())
            self.start_worker(machine, "run_script", self.task_form.payload())

    def start_worker(self, machine: Machine, action: str, payload: dict | None = None) -> None:
        worker = AgentWorker(self.api, machine, action, payload)
        worker.signals.finished.connect(self.on_worker_finished)
        worker.signals.event.connect(self.on_worker_event)
        self.thread_pool.start(worker)

    def on_worker_event(self, machine: Machine, message: dict) -> None:
        payload = message.get("payload", {})
        self.task_results.append_line(
            f"[{machine.name}][{payload.get('stream', 'stdout')}] {payload.get('chunk', '').rstrip()}"
        )

    def on_worker_finished(self, machine: Machine, response: dict) -> None:
        if response.get("status") == "ok":
            payload = response.get("payload") or {}
            if "hostname" in payload:
                machine.status = "online"
                machine.hostname = payload.get("hostname", "")
                machine.platform = payload.get("platform", "")
                self._refresh_machine(machine)
            else:
                self.task_results.append_line(f"[{machine.name}] OK: {payload}")
        else:
            machine.status = "offline"
            self._refresh_machine(machine)
            error = response.get("error", {}).get("message", "Unknown error")
            self.task_results.append_line(f"[{machine.name}] ERROR: {error}")

    def _refresh_machine(self, machine: Machine) -> None:
        for row, current_machine in enumerate(self.machines):
            if current_machine is machine or (
                machine.id is not None and current_machine.id == machine.id
            ):
                self.dashboard.model.update_machine(row, machine)
                break

    def reload_machines(self, selected_machine_id: int | None = None) -> None:
        previous_statuses = {
            machine.id: (machine.status, machine.hostname, machine.platform)
            for machine in self.machines
            if machine.id is not None
        }
        self.machines = self.repository.list_machines()
        for machine in self.machines:
            if machine.id in previous_statuses:
                machine.status, machine.hostname, machine.platform = previous_statuses[machine.id]
        self.dashboard.model.set_machines(self.machines)
        if selected_machine_id is not None:
            self._select_machine_by_id(selected_machine_id)

    def _select_machine_by_id(self, machine_id: int) -> None:
        for row, machine in enumerate(self.machines):
            if machine.id == machine_id:
                self.dashboard.table.selectRow(row)
                break

    def _profile_map(self):
        return {profile.id: profile for profile in self.repository.list_profiles() if profile.id is not None}
