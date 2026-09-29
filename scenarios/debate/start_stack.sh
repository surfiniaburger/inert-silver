#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# Clean stale listeners from previous runs.
lsof -ti:9009,9018,9019,9020 | xargs kill -9 2>/dev/null || true

JUDGE_MODEL="${JUDGE_MODEL:-ollama/gemma-4-12b-fast}"
DEBATER_MODEL="${DEBATER_MODEL:-ollama/gemma-4-e4b}"
GENERATOR_MODEL="${GENERATOR_MODEL:-ollama/gemma-4-e4b}"
VERIFIER_MODEL="${VERIFIER_MODEL:-ollama/gemma-4-12b-fast}"
LLM_SAMPLING_PROFILE="${LLM_SAMPLING_PROFILE:-ollama_gemma4}"
LLM_MAX_TOKENS="${LLM_MAX_TOKENS:-8192}"
export JUDGE_MODEL DEBATER_MODEL GENERATOR_MODEL VERIFIER_MODEL LLM_SAMPLING_PROFILE LLM_MAX_TOKENS

echo "Starting debate stack on ports 9009, 9018, 9019, 9020"
exec uv run agentbeats-run scenarios/debate/barred_test.toml --serve-only
