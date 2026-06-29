#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/demo-client"

echo "Starting sample web client on http://localhost:5500"
echo "Ensure the API is running on http://localhost:8000"
exec python3 -m http.server 5500
