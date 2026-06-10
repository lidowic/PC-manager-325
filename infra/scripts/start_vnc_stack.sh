#!/usr/bin/env bash
set -euo pipefail

DISPLAY_VALUE="${DISPLAY_VALUE:-:0}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
NOVNC_WEB_DIR="${NOVNC_WEB_DIR:-/usr/share/novnc}"
LOG_DIR="${LOG_DIR:-.run}"

mkdir -p "$LOG_DIR"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd x11vnc
require_cmd websockify

if [[ ! -d "$NOVNC_WEB_DIR" ]]; then
  echo "noVNC web directory not found: $NOVNC_WEB_DIR" >&2
  echo "Install package 'novnc' or set NOVNC_WEB_DIR manually." >&2
  exit 1
fi

pkill -f "x11vnc .* -rfbport $VNC_PORT" 2>/dev/null || true
pkill -f "websockify .* $NOVNC_PORT .*:$VNC_PORT" 2>/dev/null || true

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

sleep 2

echo
echo "Ports:"
ss -ltnp | grep -E ":($VNC_PORT|$NOVNC_PORT)\b" || true
echo
echo "Logs:"
echo "  $LOG_DIR/x11vnc.log"
echo "  $LOG_DIR/websockify.log"
echo
echo "Open in browser:"
echo "  http://$(hostname -I | awk '{print $1}'):$NOVNC_PORT/vnc.html"
