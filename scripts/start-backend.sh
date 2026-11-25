#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
export PYTHONPATH="$ROOT/backend:${PYTHONPATH:-}"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env from example (SQLite by default)"
fi
mkdir -p uploads/media uploads/thumbnails uploads/reports_pdf
echo "Starting RescueGrid AI backend on http://0.0.0.0:8000 ..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
