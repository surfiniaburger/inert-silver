#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8000}"
MODEL="${MODEL:-trymirai/Qwen3.5-9B-M}"

echo "Starting Uzu OpenAI-compatible proxy on http://localhost:${PORT} with model ${MODEL}..."
exec .venv-uzu/bin/python scripts/uzu_proxy.py --port "$PORT" --model "$MODEL"
