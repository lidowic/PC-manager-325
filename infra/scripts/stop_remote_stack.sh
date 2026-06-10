#!/usr/bin/env bash
set -euo pipefail

AGENT_PORT="${AGENT_PORT:-9031}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

pkill -f "x11vnc .* -rfbport $VNC_PORT" 2>/dev/null || true
pkill -f "websockify .* $NOVNC_PORT .*:$VNC_PORT" 2>/dev/null || true
pkill -f "python.*-m agent.main" 2>/dev/null || true

echo "Stopped processes bound to ports $AGENT_PORT, $VNC_PORT, $NOVNC_PORT where found."
