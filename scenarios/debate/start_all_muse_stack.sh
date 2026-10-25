#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# Clean stale listeners on debate ports
lsof -ti:9009,9018,9019,9020 | xargs kill -9 2>/dev/null || true

# All roles -> Uzu Muse-Glimmer 30B on port 8000
export DEBATER_MODEL="openai/trymirai/Muse-Glimmer-30B-M"
export DEBATER_API_BASE="http://localhost:8000/v1"
export DEBATER_API_KEY="uzu"

export VERIFIER_MODEL="openai/trymirai/Muse-Glimmer-30B-M"
export VERIFIER_API_BASE="http://localhost:8000/v1"
export VERIFIER_API_KEY="uzu"

export GENERATOR_MODEL="openai/trymirai/Muse-Glimmer-30B-M"
export GENERATOR_API_BASE="http://localhost:8000/v1"
export GENERATOR_API_KEY="uzu"

export JUDGE_MODEL="openai/trymirai/Muse-Glimmer-30B-M"
export JUDGE_API_BASE="http://localhost:8000/v1"
export JUDGE_API_KEY="uzu"

export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="uzu"

export UZU_REASONING_EFFORT="default"
export UZU_CONTEXT_LENGTH="6144"
export SEND_MESSAGE_TIMEOUT="1800"      # Multi-turn 30B debate takes 10-15m per seed
export LITELLM_REQUEST_TIMEOUT="360"   # 30B is ~5x slower; give it 6m headroom
export LITELLM_NUM_RETRIES="3"
export LLM_SAMPLING_PROFILE="ollama_gemma4"
export LLM_MAX_TOKENS="4096"

echo "============================================================"
echo " Starting Debate Stack (All Uzu Muse-Glimmer 30B):"
echo "   Debater:   $DEBATER_MODEL -> $DEBATER_API_BASE"
echo "   Verifier:  $VERIFIER_MODEL -> $VERIFIER_API_BASE"
echo "   Judge:     $JUDGE_MODEL -> $JUDGE_API_BASE"
echo "   Generator: $GENERATOR_MODEL -> $GENERATOR_API_BASE"
echo "============================================================"

exec ./scenarios/debate/start_stack.sh
