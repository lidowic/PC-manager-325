#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DISPLAY_VALUE="${DISPLAY_VALUE:-:0}"
AGENT_CONFIG="${AGENT_CONFIG:-$ROOT_DIR/infra/configs/agent.example.yaml}"
AGENT_HOST="${AGENT_HOST:-0.0.0.0}"
AGENT_PORT="${AGENT_PORT:-9031}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
NOVNC_WEB_DIR="${NOVNC_WEB_DIR:-/usr/share/novnc}"
LOG_DIR="${LOG_DIR:-$ROOT_DIR/.run}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ALLOW_INSECURE="${ALLOW_INSECURE:-true}"

mkdir -p "$LOG_DIR"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd "$PYTHON_BIN"
require_cmd x11vnc
require_cmd websockify

if [[ ! -d "$NOVNC_WEB_DIR" ]]; then
  echo "noVNC web directory not found: $NOVNC_WEB_DIR" >&2
  echo "Install package 'novnc' or set NOVNC_WEB_DIR manually." >&2
  exit 1
fi

if [[ ! -f "$AGENT_CONFIG" ]]; then
  cat >"$AGENT_CONFIG" <<EOF
host: $AGENT_HOST
port: $AGENT_PORT
allow_insecure: $ALLOW_INSECURE
read_chunk_size: 4096
command_timeout: 60
script_timeout: 300
allowed_public_keys: []
EOF
  echo "Created agent config: $AGENT_CONFIG"
fi

pkill -f "x11vnc .* -rfbport $VNC_PORT" 2>/dev/null || true
pkill -f "websockify .* $NOVNC_PORT .*:$VNC_PORT" 2>/dev/null || true
pkill -f "python.*-m agent.main --config $AGENT_CONFIG" 2>/dev/null || true

echo "Starting x11vnc on display $DISPLAY_VALUE port $VNC_PORT"
nohup x11vnc \
  -display "$DISPLAY_VALUE" \
  -forever \
  -shared \
  -nopw \
  -listen 0.0.0.0 \
  -rfbport "$VNC_PORT" \
  >"$LOG_DIR/x11vnc.log" 2>&1 &

echo "Starting noVNC/websockify on port $NOVNC_PORT"
nohup websockify \
  --web "$NOVNC_WEB_DIR" \
  "$NOVNC_PORT" \
  "127.0.0.1:$VNC_PORT" \
  >"$LOG_DIR/websockify.log" 2>&1 &

echo "Starting agent on port $AGENT_PORT"
nohup "$PYTHON_BIN" -m agent.main --config "$AGENT_CONFIG" \
  >"$LOG_DIR/agent.log" 2>&1 &

sleep 2

echo
echo "Processes:"
ss -ltnp | grep -E ":($AGENT_PORT|$VNC_PORT|$NOVNC_PORT)\b" || true
echo
echo "Logs:"
echo "  Agent:      $LOG_DIR/agent.log"
echo "  x11vnc:     $LOG_DIR/x11vnc.log"
echo "  websockify: $LOG_DIR/websockify.log"
echo
echo "noVNC URL:"
echo "  http://$(hostname -I | awk '{print $1}'):$NOVNC_PORT/vnc.html"
