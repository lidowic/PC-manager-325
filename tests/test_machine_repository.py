import tempfile
from pathlib import Path

from client.config import MachineConfig
from client.db.repository import MachineRepository
from client.models.machine import Machine
from client.models.profile import ConnectionProfile
from client.models.script_template import ScriptTemplate


def test_machine_repository_crud_and_bootstrap() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "client.db"
        repository = MachineRepository(str(db_path))
        repository.initialize()
        repository.bootstrap_from_config(
            [
                MachineConfig(
                    name="pc-01",
                    host="192.168.0.10",
                    port=9021,
                    ssh_port=22,
                    ssh_user="Administrator",
                    remote_desktop_url="http://192.168.0.10:6080/vnc.html",
                )
            ]
        )

        machines = repository.list_machines()
        assert len(machines) == 1
        machine = machines[0]
        assert machine.id is not None

        created = repository.add_machine(
            Machine(
                id=None,
                name="pc-02",
                host="192.168.0.11",
                port=9021,
                ssh_port=22,
                ssh_user="Administrator",
                remote_desktop_url="",
            )
        )
        assert created.id is not None

        created.name = "pc-02-renamed"
        repository.update_machine(created)

        names = [item.name for item in repository.list_machines()]
        assert "pc-02-renamed" in names

        repository.delete_machine(created.id)
        names = [item.name for item in repository.list_machines()]
        assert names == ["pc-01"]


def test_repository_profiles_tags_templates_and_settings() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "client.db"
        repository = MachineRepository(str(db_path))
        repository.initialize()

        profile = repository.add_profile(
            ConnectionProfile(
                id=None,
                name="default-admin",
                ssh_user="Administrator",
                private_key_path="C:/keys/id_ed25519",
                public_key_path="C:/keys/id_ed25519.pub",
                connect_timeout=10,
            )
        )
        assert profile.id is not None

        created = repository.add_machine(
            Machine(
                id=None,
                name="pc-03",
                host="192.168.0.12",
                port=9021,
                ssh_port=22,
                ssh_user="",
                remote_desktop_url="",
                profile_id=profile.id,
                tags=["lab", "windows"],
            )
        )

        machine = repository.list_machines()[0]
        assert machine.profile_name == "default-admin"
        assert machine.tags == ["lab", "windows"]

        repository.upsert_template(
            ScriptTemplate(
                id=None,
                name="whoami",
                shell="powershell",
                body="whoami",
            )
        )
        template = repository.get_template_by_name("whoami")
        assert template is not None
        assert template.body == "whoami"

        repository.set_setting("default_shell", "powershell")
        assert repository.get_setting("default_shell") == "powershell"

        repository.delete_machine(created.id)
