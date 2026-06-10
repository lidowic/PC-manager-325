from __future__ import annotations

import platform
import socket


def collect_machine_info() -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "python_version": platform.python_version(),
    }
