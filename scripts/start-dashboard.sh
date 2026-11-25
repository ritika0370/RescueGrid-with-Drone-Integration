#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/web-dashboard"
if [ ! -f .env.local ]; then
  cp ../../.env.example .env.local 2>/dev/null || true
fi
if command -v pnpm >/dev/null 2>&1; then
  pnpm install
  exec pnpm dev
elif command -v npm >/dev/null 2>&1; then
  npm install
  exec npm run dev
else
  echo "Install Node.js and pnpm or npm first"
  exit 1
fi
