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
if [[ "$JUDGE_MODEL $DEBATER_MODEL $GENERATOR_MODEL $VERIFIER_MODEL" == *"vertex_ai/"* ]]; then
  DEFAULT_PROFILE="vertex_gemini"
else
  DEFAULT_PROFILE="ollama_gemma4"
fi
LLM_SAMPLING_PROFILE="${LLM_SAMPLING_PROFILE:-$DEFAULT_PROFILE}"
LLM_MAX_TOKENS="${LLM_MAX_TOKENS:-8192}"
VERTEXAI_PROJECT="${VERTEXAI_PROJECT:-$(gcloud config get-value project 2>/dev/null || true)}"
VERTEXAI_LOCATION="${VERTEXAI_LOCATION:-global}"
LITELLM_NUM_RETRIES="${LITELLM_NUM_RETRIES:-6}"
INITIAL_RETRY_DELAY="${INITIAL_RETRY_DELAY:-5.0}"
MAX_RETRY_DELAY="${MAX_RETRY_DELAY:-60.0}"

if [[ "$JUDGE_MODEL $DEBATER_MODEL $GENERATOR_MODEL $VERIFIER_MODEL" == *"vertex_ai/"* ]] && [[ -z "${VERTEXAI_PROJECT:-}" ]]; then
  echo "Error: Vertex AI model selected but VERTEXAI_PROJECT is not set. Please set VERTEXAI_PROJECT." >&2
  exit 1
fi

if [[ "$DEBATER_MODEL" == "openai/"* ]]; then
  DEBATER_API_BASE="${DEBATER_API_BASE:-${OPENAI_API_BASE:-}}"
  DEBATER_API_KEY="${DEBATER_API_KEY:-${OPENAI_API_KEY:-}}"
else
  DEBATER_API_BASE="${DEBATER_API_BASE:-}"
  DEBATER_API_KEY="${DEBATER_API_KEY:-}"
fi

if [[ "$VERIFIER_MODEL" == "openai/"* ]]; then
  VERIFIER_API_BASE="${VERIFIER_API_BASE:-${OPENAI_API_BASE:-}}"
  VERIFIER_API_KEY="${VERIFIER_API_KEY:-${OPENAI_API_KEY:-}}"
else
  VERIFIER_API_BASE="${VERIFIER_API_BASE:-}"
  VERIFIER_API_KEY="${VERIFIER_API_KEY:-}"
fi

if [[ "$JUDGE_MODEL" == "openai/"* ]]; then
  JUDGE_API_BASE="${JUDGE_API_BASE:-${OPENAI_API_BASE:-}}"
  JUDGE_API_KEY="${JUDGE_API_KEY:-${OPENAI_API_KEY:-}}"
else
  JUDGE_API_BASE="${JUDGE_API_BASE:-}"
  JUDGE_API_KEY="${JUDGE_API_KEY:-}"
fi

export JUDGE_MODEL DEBATER_MODEL GENERATOR_MODEL VERIFIER_MODEL LLM_SAMPLING_PROFILE LLM_MAX_TOKENS VERTEXAI_PROJECT VERTEXAI_LOCATION LITELLM_NUM_RETRIES INITIAL_RETRY_DELAY MAX_RETRY_DELAY LITELLM_REQUEST_TIMEOUT UZU_REASONING_EFFORT DEBATER_API_BASE DEBATER_API_KEY VERIFIER_API_BASE VERIFIER_API_KEY JUDGE_API_BASE JUDGE_API_KEY

echo "=== Debate Stack Configuration ==="
echo "Debater:  ${DEBATER_MODEL} (api_base: ${DEBATER_API_BASE:-default})"
echo "Verifier: ${VERIFIER_MODEL} (api_base: ${VERIFIER_API_BASE:-default})"
echo "Judge:    ${JUDGE_MODEL} (api_base: ${JUDGE_API_BASE:-default})"
echo "Starting debate stack on ports 9009, 9018, 9019, 9020"
echo "=================================="
exec uv run agentbeats-run scenarios/debate/barred_test.toml --serve-only
