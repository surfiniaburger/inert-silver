#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs/pinned_pareto

REPS=(2 3 4 5)
SEEDS=(43 44 45 46)

EXPECTED_SHA="516c2f76de1af896a9a410fe86133b4233fbbec25283a1d92c3dd5a2152e57d0"

for idx in "${!REPS[@]}"; do
    REP="${REPS[$idx]}"
    SEED="${SEEDS[$idx]}"
    RUN_ID="unrun-pinned-pareto-50-rep${REP}"
    OUTPUT="test_corpus_pinned_pareto_50_rep${REP}.jsonl"
    LOG="logs/pinned_pareto/rep${REP}_seed${SEED}.log"

    echo "================================================================"
    echo "Starting Pinned Pareto Replicate ${REP} (Seed: ${SEED}, Run ID: ${RUN_ID})"
    echo "Timestamp: $(date -u)"
    echo "================================================================"

    # Verify frontier integrity before run
    CURRENT_SHA=$(shasum -a 256 artifacts/gepa_pareto_50/pareto_frontier.json | awk '{print $1}')
    if [[ "${CURRENT_SHA}" != "${EXPECTED_SHA}" ]]; then
        echo "ERROR: Pareto frontier mutated before Rep ${REP}! Expected ${EXPECTED_SHA}, got ${CURRENT_SHA}" >&2
        exit 1
    fi

    uv run python scenarios/debate/run_batch.py \
        --seeds scenarios/debate/cve_seeds_benchmark_50.jsonl \
        --output "${OUTPUT}" \
        --mode record \
        --run-id "${RUN_ID}" \
        --seed "${SEED}" \
        --pin-pareto \
        --gepa-dir artifacts/gepa_pareto_50 \
        --slice-judge 2>&1 | tee "${LOG}"

    # Verify frontier integrity after run
    CURRENT_SHA=$(shasum -a 256 artifacts/gepa_pareto_50/pareto_frontier.json | awk '{print $1}')
    if [[ "${CURRENT_SHA}" != "${EXPECTED_SHA}" ]]; then
        echo "ERROR: Pareto frontier mutated during Rep ${REP}! Expected ${EXPECTED_SHA}, got ${CURRENT_SHA}" >&2
        exit 1
    fi

    ACCEPTED_COUNT=$(wc -l < "${OUTPUT}" | tr -d ' ')
    echo "Completed Replicate ${REP}: ${ACCEPTED_COUNT}/50 accepted rows."
done

echo "================================================================"
echo "All 4 Pinned Pareto Replicates (2..5) Completed Successfully!"
echo "================================================================"
