#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck disable=SC1091
source .venv/bin/activate

find "$ROOT_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Starting Streamlit AI demo on http://localhost:8501"
exec streamlit run app/app.py --server.port 8501 --server.headless true
