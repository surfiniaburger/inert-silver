# BARRED — Failure Modes & Replay/TDD Plan

**Status:** Analysis + plan (not yet implemented).
**Source:** Qwen 3.5 9B smoke run `q9d-smoke-armC-struct-esc` (10 seeds, arm C, `--halt-on-con-win`).

---

## 1. Observed failure modes

### Mode 1: Schema rejection (4 seeds: 42, 43, 50, 51)

**Symptom:** `judge_parse_failed` — `DebateEval` validation error: `con_win requires con_candidate_id or counter_evidence`.

**Root cause:** The model outputs `winner="con_debater"` with `counter_evidence=null` and `con_candidate_id=null`. The new schema (Step 2) requires at least one for a Con win. The repair loop attempts to fix but fails. The model is still generating the old format.

**Impact:** The entire judge response is rejected. No terminal decision is recorded (phase=failed). The seed is lost, not just rejected.

**Fix:** Make `counter_evidence` structurally mandatory via discriminated union (Step 1 of Con Receipt Plan v2). The model can't omit it. If it outputs null, schema validation fails → repair loop → model gets "missing field" error → retries with the correct schema.

### Mode 2: Con receipt invalid (2 seeds: 44, 47)

**Symptom:** `counter_evidence_invalid_contract` — the model produced a Con receipt but it failed validation.

**Root cause:** 
- Seed 44: `counter_evidence_unrecognized_operation` — the receipt's operation anchor contains an unrecognized sink (Step 4's semantic check). The model invented a plausible-looking receipt with an unknown operation.
- Seed 47: `counter_evidence_invalid_contract` (generic) — the receipt failed for another reason (likely missing fields or wrong enum values).

**Impact:** The Con win is rejected. The model tried to produce a receipt but couldn't satisfy the contract.

**Fix:** The candidate-selection-only flow (v2 plan Step 1-2) would eliminate this: the model selects C1, and the runtime reconstructs the receipt from the pre-validated candidate. No model-generated receipt = no invalid receipt.

### Mode 3: Verifier logic error (1 seed: 49)

**Symptom:** `verifier_logic_error` — Pro won but the verifier found a logic error in the Pro claim.

**Root cause:** The Pro debater's argument contained a logical flaw that the verifier caught. This is the verifier working as designed — it's a quality gate, not a bug.

**Impact:** Seed is rejected. This is correct behavior (the Pro claim was flawed).

**Fix:** None needed — this is the system working correctly.

### Mode 4: Anchors too few (1 seed: 48)

**Symptom:** `anchors_too_few_after_normalization` — the judge's anchors didn't match the code after normalization.

**Root cause:** The judge provided anchors that were paraphrased or slightly different from the code. The normalization step (matching anchors to code substrings) failed.

**Impact:** Seed is rejected. This is a grounding failure — the judge couldn't anchor its verdict to the code.

**Fix:** Improve anchor normalization (fuzzy matching, or require exact substrings). Could also be a model quality issue (Qwen 9B struggles with exact verbatim copying).

### Mode 5: Con win without counter-evidence (1 seed: 50)

**Symptom:** `con_win_not_applicable` — Con won but had no concrete counter-evidence.

**Root cause:** The Con debater won the debate (persuaded the judge) but didn't provide the concrete guard/operation anchors required by the `con_win_counter_evidence` gate. The gate rejected it.

**Impact:** Con win is rejected. This is the gate working as designed — Con can't win without evidence.

**Fix:** The gate is correct. The issue is Con not producing evidence. This could be improved by the obligation-aware prompt (which tells Con what evidence to produce), but Con still needs to generate it.

### Mode 6: Judge parse failure (1 seed: 51)

**Symptom:** `judge_parse_failed` — the judge's output couldn't be parsed as valid JSON.

**Root cause:** The model produced malformed JSON (missing fields, invalid syntax). This is a model quality issue.

**Impact:** Seed is lost (no terminal decision).

**Fix:** The structured output repair loop should handle this. But Qwen 9B may be producing output too malformed to repair.

---

## 2. How replay + TDD can solve these

### Replay infrastructure

The system has cassette-based replay (`--mode replay`). Cassettes record all LLM calls and responses. A replay re-executes the pipeline using cached responses — no new API calls, no cost, deterministic.

**How to use replay for TDD:**

1. **Record a cassette** from a successful run (e.g., the Qwen 3.5 9B smoke run that completed 2 seeds). The cassette captures the exact LLM responses.
2. **Modify the code** (e.g., add discriminated union, candidate selection, simplified prompt).
3. **Replay the cassette** with the new code. The pipeline re-executes using the cached responses, but the new code processes them differently.
4. **Compare outcomes:** Did the new code produce different (better) results? Did it crash? Did it handle the old responses gracefully?

### TDD approach

1. **Write a failing test** that simulates Mode 1 (judge outputs `winner=con_debater` with `counter_evidence=null`). Assert that the new code rejects it with `outcome=unresolved` instead of crashing with `judge_parse_failed`.

2. **Implement the fix** (discriminated union + candidate selection). The test should now pass.

3. **Replay the cassette** to verify the fix works on real model output. If the replay produces different results (e.g., `unresolved` instead of `judge_parse_failed`), the fix is working.

4. **Add regression tests** for each failure mode:
   - Mode 1: null receipt → unresolved (not crash)
   - Mode 2: invalid receipt → rejected (not accepted)
   - Mode 4: too few anchors → rejected (not crash)
   - Mode 5: Con win without evidence → rejected (not accepted)

### Replay limitations

- Replay uses cached responses. If the new code changes the prompt (obligation-aware section), the cached responses won't match the new prompt. The replay will fail on cache miss.
- **Solution:** Replay is useful for testing code logic changes (e.g., the halt condition, terminal-attempt selection) but not for testing prompt changes (which require new model calls).
- For prompt changes, use a small smoke run (2 seeds) on a fast model (Qwen 4B) to validate.

### Recommended sequence

1. **Write TDD tests** for all 6 failure modes using mocked LLM responses (no API calls). Verify the new code handles each gracefully.
2. **Implement the discriminated union** (Step 1 of v2 plan) + candidate-selection-only flow. Verify tests pass.
3. **Replay the Qwen 3.5 9B smoke cassette** (if available) to verify the fix works on real (cached) model output.
4. **Run a new Qwen 3.5 9B smoke** (2 seeds) with the new code to validate prompt changes.
5. **Run a Gemma 12B smoke** (2 seeds) to check if the stronger model produces valid receipts.

### What to look for in results

After the fix, the funnel should show:

| Metric | Before (current) | Target (after fix) |
|--------|-----------------|-------------------|
| `con_win_defended` (halt on valid receipt) | 0 | > 0 |
| `counter_evidence_missing` (judge omitted receipt) | 4-7 | 0 (schema requires it) |
| `counter_evidence_invalid_candidate_id` (unknown candidate) | 0 | ≥ 0 (model may select invalid ID) |
| `validated_con_counter_evidence` (Con accepted with valid receipt) | 0 | ≥ 0 |
| `outcome: unresolved` in checkpoints (model abstained) | 0 | ≥ 0 (replaces `judge_parse_failed` crashes) |

The key change: `counter_evidence_missing` and `judge_parse_failed` (crashes) should be replaced by `unresolved` (controlled abstention). And if the candidate selection works, some Con wins should produce `deterministically_confirmed` receipts.

### One important note

The `counter_evidence_missing` failure in Mode 1 is because the model outputs `winner="con_debater"` with `counter_evidence=null`. The discriminated union makes `counter_evidence` required for `con_win`. But Pydantic's repair loop needs to handle this gracefully — it should ask the model to fill in the missing field, not crash. The repair loop already exists (`repair_on_fail=True`), but it may not be effective for this specific failure. Test this with the TDD approach.
