#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# Clean any existing listeners on debate ports
lsof -ti:9009,9018,9019,9020 | xargs kill -9 2>/dev/null || true

# Debater & Verifier -> Uzu Qwen on port 8000
export DEBATER_MODEL="openai/trymirai/Qwen3.5-4B-M"
export DEBATER_API_BASE="http://localhost:8000/v1"
export DEBATER_API_KEY="uzu"

export VERIFIER_MODEL="openai/trymirai/Qwen3.5-4B-M"
export VERIFIER_API_BASE="http://localhost:8000/v1"
export VERIFIER_API_KEY="uzu"

# Generator
export GENERATOR_MODEL="openai/trymirai/Qwen3.5-4B-M"

# Judge -> Gemma 12B in LM Studio on port 1234
export JUDGE_MODEL="openai/google/gemma-4-12b-qat"
export JUDGE_API_BASE="http://localhost:1234/v1"
export JUDGE_API_KEY="lm-studio"

export LLM_SAMPLING_PROFILE="ollama_gemma4"
export LLM_MAX_TOKENS="8192"

echo "============================================================"
echo " Starting Debate Stack:"
echo "   Debater:  $DEBATER_MODEL -> $DEBATER_API_BASE"
echo "   Verifier: $VERIFIER_MODEL -> $VERIFIER_API_BASE"
echo "   Judge:    $JUDGE_MODEL -> $JUDGE_API_BASE"
echo "============================================================"

exec ./scenarios/debate/start_stack.sh
