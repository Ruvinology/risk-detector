#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
  pip install -q -r requirements.txt
fi

# shellcheck disable=SC1091
source .venv/bin/activate

find "$ROOT_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

PORT="${1:-8000}"
PID="$(lsof -ti:"$PORT" 2>/dev/null || true)"
if [[ -n "$PID" ]]; then
  echo "Stopping existing process on port $PORT (pid $PID)..."
  kill "$PID" 2>/dev/null || true
  sleep 2
fi

echo "Starting ScamShield API on http://localhost:$PORT"
exec uvicorn api.main:app --host 127.0.0.1 --port "$PORT" --reload
