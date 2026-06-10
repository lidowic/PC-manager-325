# PC Remote Admin for Windows

Система удаленного администрирования компьютеров в локальной сети по архитектуре `client-agent`.

## Стек

- `Python 3.12+`
- `PyQt6`
- `asyncio`
- `Paramiko`
- `pyte`
- `QWebEngineView`
- `JSON over TCP`

## Быстрый старт на Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m agent.main --config infra/configs/agent.example.yaml
```

Клиент:

```powershell
.venv\Scripts\Activate.ps1
python -m client.main --config infra/configs/client.example.yaml
```

## Конфиги

- агент: [infra/configs/agent.example.yaml](/C:/da/infra/configs/agent.example.yaml)
- клиент: [infra/configs/client.example.yaml](/C:/da/infra/configs/client.example.yaml)

В `client.example.yaml` хранятся общие настройки клиента и путь к базе:

- `database_path`
- `private_key_path`
- `public_key_path`
- `connect_timeout`

Секция `machines` оставлена как стартовый список для первого запуска. Если база пуста, эти машины будут один раз импортированы в `SQLite`, дальше управление списком идет через GUI.

В локальной `SQLite` базе дополнительно хранятся:

- метки машин
- профили подключения
- шаблоны скриптов
- локальные настройки клиента

В `run_script` теперь можно передавать shell:

- `powershell`
- `cmd`
- `bash`

По умолчанию для Windows-агента используется `powershell`.

## Полезные скрипты

- запуск агента: [infra/scripts/start_agent_windows.ps1](/C:/da/infra/scripts/start_agent_windows.ps1)
- пример запуска VNC/web gateway: [infra/scripts/start_windows_vnc.ps1](/C:/da/infra/scripts/start_windows_vnc.ps1)

## Ограничения

- встроенный `SSH terminal` работает, если на Windows-машине включен OpenSSH Server
- вкладка `Remote desktop` ожидает web URL; для Windows это может быть `noVNC`, Guacamole или другой web gateway
