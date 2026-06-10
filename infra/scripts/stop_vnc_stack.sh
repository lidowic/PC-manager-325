#!/usr/bin/env bash
set -euo pipefail

VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

pkill -f "x11vnc .* -rfbport $VNC_PORT" 2>/dev/null || true
pkill -f "websockify .* $NOVNC_PORT .*:$VNC_PORT" 2>/dev/null || true

echo "Stopped VNC/noVNC processes if they were running."
