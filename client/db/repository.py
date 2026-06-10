from __future__ import annotations

import sqlite3
from pathlib import Path

from client.config import MachineConfig
from client.models.machine import Machine
from client.models.profile import ConnectionProfile
from client.models.script_template import ScriptTemplate


class MachineRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS machines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    ssh_port INTEGER NOT NULL,
                    ssh_user TEXT NOT NULL DEFAULT '',
                    remote_desktop_url TEXT NOT NULL DEFAULT '',
                    profile_id INTEGER NULL,
                    FOREIGN KEY (profile_id) REFERENCES connection_profiles(id) ON DELETE SET NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS connection_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    ssh_user TEXT NOT NULL DEFAULT '',
                    private_key_path TEXT NOT NULL DEFAULT '',
                    public_key_path TEXT NOT NULL DEFAULT '',
                    connect_timeout INTEGER NOT NULL DEFAULT 5
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS machine_tags (
                    machine_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (machine_id, tag_id),
                    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS script_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    shell TEXT NOT NULL,
                    body TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS client_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self._migrate_schema(connection)

    def bootstrap_from_config(self, machines: list[MachineConfig]) -> None:
        if not machines or self.count() > 0:
            return
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO machines (name, host, port, ssh_port, ssh_user, remote_desktop_url)
                VALUES (:name, :host, :port, :ssh_port, :ssh_user, :remote_desktop_url)
                """,
                [
                    {
                        "name": machine.name,
                        "host": machine.host,
                        "port": machine.port,
                        "ssh_port": machine.ssh_port,
                        "ssh_user": machine.ssh_user,
                        "remote_desktop_url": machine.remote_desktop_url,
                    }
                    for machine in machines
                ],
            )

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM machines").fetchone()
        return int(row[0])

    def list_machines(self) -> list[Machine]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    m.id,
                    m.name,
                    m.host,
                    m.port,
                    m.ssh_port,
                    m.ssh_user,
                    m.remote_desktop_url,
                    m.profile_id,
                    cp.name AS profile_name,
                    GROUP_CONCAT(t.name, ', ') AS tags
                FROM machines m
                LEFT JOIN connection_profiles cp ON cp.id = m.profile_id
                LEFT JOIN machine_tags mt ON mt.machine_id = m.id
                LEFT JOIN tags t ON t.id = mt.tag_id
                GROUP BY
                    m.id,
                    m.name,
                    m.host,
                    m.port,
                    m.ssh_port,
                    m.ssh_user,
                    m.remote_desktop_url,
                    m.profile_id,
                    cp.name
                ORDER BY m.name COLLATE NOCASE, m.id
                """
            ).fetchall()
        return [self._row_to_machine(row) for row in rows]

    def add_machine(self, machine: Machine) -> Machine:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO machines (name, host, port, ssh_port, ssh_user, remote_desktop_url, profile_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    machine.name,
                    machine.host,
                    machine.port,
                    machine.ssh_port,
                    machine.ssh_user,
                    machine.remote_desktop_url,
                    machine.profile_id,
                ),
            )
            machine.id = int(cursor.lastrowid)
            self._replace_machine_tags(connection, machine.id, machine.tags)
        return machine

    def update_machine(self, machine: Machine) -> None:
        if machine.id is None:
            raise ValueError("Machine must have an id before update")
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE machines
                SET name = ?, host = ?, port = ?, ssh_port = ?, ssh_user = ?, remote_desktop_url = ?, profile_id = ?
                WHERE id = ?
                """,
                (
                    machine.name,
                    machine.host,
                    machine.port,
                    machine.ssh_port,
                    machine.ssh_user,
                    machine.remote_desktop_url,
                    machine.profile_id,
                    machine.id,
                ),
            )
            self._replace_machine_tags(connection, machine.id, machine.tags)

    def delete_machine(self, machine_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM machines WHERE id = ?", (machine_id,))

    def list_profiles(self) -> list[ConnectionProfile]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, ssh_user, private_key_path, public_key_path, connect_timeout
                FROM connection_profiles
                ORDER BY name COLLATE NOCASE, id
                """
            ).fetchall()
        return [
            ConnectionProfile(
                id=int(row["id"]),
                name=str(row["name"]),
                ssh_user=str(row["ssh_user"]),
                private_key_path=str(row["private_key_path"]),
                public_key_path=str(row["public_key_path"]),
                connect_timeout=int(row["connect_timeout"]),
            )
            for row in rows
        ]

    def add_profile(self, profile: ConnectionProfile) -> ConnectionProfile:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO connection_profiles (name, ssh_user, private_key_path, public_key_path, connect_timeout)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    profile.name,
                    profile.ssh_user,
                    profile.private_key_path,
                    profile.public_key_path,
                    profile.connect_timeout,
                ),
            )
            profile.id = int(cursor.lastrowid)
        return profile

    def update_profile(self, profile: ConnectionProfile) -> None:
        if profile.id is None:
            raise ValueError("Profile must have an id before update")
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE connection_profiles
                SET name = ?, ssh_user = ?, private_key_path = ?, public_key_path = ?, connect_timeout = ?
                WHERE id = ?
                """,
                (
                    profile.name,
                    profile.ssh_user,
                    profile.private_key_path,
                    profile.public_key_path,
                    profile.connect_timeout,
                    profile.id,
                ),
            )

    def delete_profile(self, profile_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE machines SET profile_id = NULL WHERE profile_id = ?",
                (profile_id,),
            )
            connection.execute("DELETE FROM connection_profiles WHERE id = ?", (profile_id,))

    def list_template_names(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM script_templates ORDER BY name COLLATE NOCASE, id"
            ).fetchall()
        return [str(row["name"]) for row in rows]

    def get_template_by_name(self, name: str) -> ScriptTemplate | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, shell, body FROM script_templates WHERE name = ?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return ScriptTemplate(
            id=int(row["id"]),
            name=str(row["name"]),
            shell=str(row["shell"]),
            body=str(row["body"]),
        )

    def upsert_template(self, template: ScriptTemplate) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id FROM script_templates WHERE name = ?",
                (template.name,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO script_templates (name, shell, body) VALUES (?, ?, ?)",
                    (template.name, template.shell, template.body),
                )
            else:
                connection.execute(
                    "UPDATE script_templates SET shell = ?, body = ? WHERE name = ?",
                    (template.shell, template.body, template.name),
                )

    def delete_template(self, name: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM script_templates WHERE name = ?", (name,))

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM client_settings WHERE key = ?",
                (key,),
            ).fetchone()
        return default if row is None else str(row["value"])

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO client_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        return self.get_setting(key, "1" if default else "0").lower() in {"1", "true", "yes", "on"}

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _row_to_machine(self, row: sqlite3.Row) -> Machine:
        return Machine(
            id=int(row["id"]),
            name=str(row["name"]),
            host=str(row["host"]),
            port=int(row["port"]),
            ssh_port=int(row["ssh_port"]),
            ssh_user=str(row["ssh_user"]),
            remote_desktop_url=str(row["remote_desktop_url"]),
            profile_id=int(row["profile_id"]) if row["profile_id"] is not None else None,
            profile_name=str(row["profile_name"] or ""),
            tags=self._parse_tags(row["tags"]),
        )

    def _replace_machine_tags(self, connection: sqlite3.Connection, machine_id: int, tags: list[str]) -> None:
        connection.execute("DELETE FROM machine_tags WHERE machine_id = ?", (machine_id,))
        normalized_tags = []
        for tag in tags:
            value = tag.strip()
            if value and value.lower() not in {item.lower() for item in normalized_tags}:
                normalized_tags.append(value)
        for tag in normalized_tags:
            connection.execute(
                "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                (tag,),
            )
            tag_row = connection.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
            if tag_row is not None:
                connection.execute(
                    "INSERT OR IGNORE INTO machine_tags (machine_id, tag_id) VALUES (?, ?)",
                    (machine_id, int(tag_row["id"])),
                )

    def _parse_tags(self, raw_tags: str | None) -> list[str]:
        if not raw_tags:
            return []
        return [item.strip() for item in str(raw_tags).split(",") if item.strip()]

    def _migrate_schema(self, connection: sqlite3.Connection) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute("PRAGMA table_info(machines)").fetchall()
        }
        if "profile_id" not in columns:
            connection.execute("ALTER TABLE machines ADD COLUMN profile_id INTEGER NULL")
