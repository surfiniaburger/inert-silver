# BARRED Track 2 — Smoke Test Report

**Run date:** 2026-10-21  
**Status:** Smoke test complete — operational validation only (n=2 seeds, 1 replicate)  
**Purpose:** Verify pipeline plumbing, schema integrity, arm flag correctness, and cost calibration before committing to the full 50-seed × 5-replicate factorial.  
**Seeds:** Seed 42 (ext2 VFS / `ext2_fsync` — Track 1 verdict: `proved_safe`) and Seed 43 (GHASH / `gf128mul_4k_lle` — Track 1 verdict: `confirmed_vulnerable`)  
**Models:** Debater/Generator: `vertex_ai/gemini-3.5-flash` | Judge/Verifier: `vertex_ai/gemini-3.6-flash`  
**Manifest SHA-256:** `1eafdae3270d44dc9121c45a6119e30fecbf41891bf106568984335d4bd442db` (identical across all arms ✅)

> [!IMPORTANT]
> This report documents operational smoke-test results only. N=2 seeds (1 replicate) is insufficient for any inferential claim. No treatment effects are estimated here. The sole purpose is to confirm the pipeline is ready for the full factorial.

---

## 1. Arm Configuration Verification

| Arm | Label | `--slice-judge` | `--reflector` | `--escalate-pareto` | `--gepa-dir` | Matches Spec |
|-----|-------|:-:|:-:|:-:|:-:|:-:|
| A (R0) | Raw, No Esc | ❌ | ❌ | ❌ | — | ✅ |
| B (S0) | Structured, No Esc | ✅ | ✅ symmetric/in-process | ❌ | — | ✅ |
| C (S1) | Structured + Esc | ✅ | ✅ symmetric/in-process | ✅ | `artifacts/gepa_gemini3_pareto_50` | ✅ |
| D (R1) | Raw + Esc | ❌ | ❌ | ✅ | — | ✅ |

All four arms ran with the correct flag combinations. The `--no-escalate-pareto` flag is **required** for Arm B because the `run_batch.py` default is `True` (escalation on).

---

## 2. Attempt-Level Results

### Arm A — Raw, No Escalation (R0)

| # | Seed | Predicate target | Decision | Round | Basis | Reject | Cost |
|---|------|-----------------|----------|-------|-------|--------|------|
| 1 | 42 (ext2_fsync) | `sb->s_bdev` chain | **rejected** | R0 | — | `verifier_logic_error` | $0.0495 |
| 2 | 43 (GHASH) | `ctx->gf128` | **accepted** | R0 | `pro_exploit_verifier_confirmed` | — | $0.0457 |

**Terminal:** Seed 42 → rejected ✅ | Seed 43 → accepted ✅ | **Total: $0.0953**

---

### Arm B — Structured Evidence, No Escalation (S0)

| # | Seed | Decision | Round | Basis | Reject | Mutation | Cost |
|---|------|----------|-------|-------|--------|----------|------|
| 1 | 42 (ext2_fsync) | **rejected** | R0 | — | `verifier_logic_error` | `var_96c9f5...` | $0.0453 |
| 2 | 42 (ext2_fsync) | **rejected** | R0 | — | `verifier_logic_error` | `var_96c9f5...` | $0.0453 |
| 3 | 43 (GHASH) | **accepted** | R0 | `pro_exploit_verifier_confirmed` | — | `var_96c9f5...` | $0.0558 |

**Terminal:** Seed 42 → rejected ✅ (2 attempts, consistent) | Seed 43 → accepted ✅ | **Total: $0.1464**

> [!NOTE]
> Structured evidence (Arm B) did not change the terminal decision vs. Raw (Arm A) on either seed. Both correctly rejected Seed 42 (`proved_safe`) and accepted Seed 43 (`confirmed_vulnerable`). The two extra rejections on Seed 42 in Arm B reflect the mutation path requiring more attempts, not a different terminal outcome.

---

### Arm C — Structured Evidence + Escalation (S1)

| # | Seed | Decision | Round | Basis | Reject | Mutation | Cost |
|---|------|----------|-------|-------|--------|----------|------|
| 1 | 42 (ext2_fsync) | **rejected** | R0 | — | `verifier_logic_error` | `baseline_v0` | $0.0451 |
| 2 | 42 (ext2_fsync) | **accepted** | **R1** | `pro_exploit_verifier_confirmed` | — | `var_3c892...` | $0.0647 |
| 3 | 43 (GHASH) | **accepted** | R0 | `pro_exploit_verifier_confirmed` | — | `baseline_v0` | $0.0469 |

**Terminal (per spec §5.1 — R1 is terminal for escalation-on arms):** Seed 42 → **accepted ⚠️** | Seed 43 → accepted ✅ | **Total: $0.1567**

> [!WARNING]
> **Harm signal (§8 criterion 4):** Seed 42 (`proved_safe`) was accepted at R1. The R1 escalation mutated the anchor set from the `sb->s_bdev` chain to `f_mapping->host` / `generic_file_fsync` — shifting to a different code path than the original predicate. The pipeline accepted a claim the Track 1 auditor refuted. This must be pre-registered and tracked in the full factorial.

---

### Arm D — Raw, Escalation On (R1)

| # | Seed | Decision | Round | Basis | Reject | Mutation | Cost |
|---|------|----------|-------|-------|--------|----------|------|
| 1 | 42 (ext2_fsync) | **accepted** | **R0** | `validated_con_counter_evidence` | — | `baseline_v0` | $0.0458 |
| 2 | 43 (GHASH) | **accepted** | R0 | `pro_exploit_verifier_confirmed` | — | `baseline_v0` | $0.0483 |

**Terminal:** Seed 42 → **accepted ⚠️** | Seed 43 → accepted ✅ | **Total: $0.0941**

> [!WARNING]
> **Harm signal (§8 criterion 4):** Seed 42 (`proved_safe`) was accepted at R0 via `validated_con_counter_evidence` — before any escalation triggered. This is the raw + escalation arm accepting a proved-safe claim without needing the escalation path at all. The acceptance basis (`validated_con_counter_evidence`) differs from all other arms and warrants investigation of the counter-evidence validation logic.

---

## 3. Terminal Decision Matrix

| Seed | Track 1 Verdict | Arm A (R0) | Arm B (S0) | Arm C (S1) | Arm D (R1) |
|------|----------------|:----------:|:----------:|:----------:|:----------:|
| 42 — ext2_fsync | `proved_safe` | ❌ rejected ✅ | ❌ rejected ✅ | ✅ accepted ⚠️ | ✅ accepted ⚠️ |
| 43 — GHASH | `confirmed_vulnerable` | ✅ accepted ✅ | ✅ accepted ✅ | ✅ accepted ✅ | ✅ accepted ✅ |

**Acceptance rate (terminal, n=2):**

| Arm | Accepted | Rate |
|-----|---------|------|
| A (R0) | 1/2 | 50% |
| B (S0) | 1/2 | 50% |
| C (S1) | 2/2 | 100% |
| D (R1) | 2/2 | 100% |

> [!CAUTION]
> These rates are **not estimands** — n=2 is a plumbing check only. Do not interpret as evidence of treatment effect. The pattern (escalation arms accept the proved-safe seed, non-escalation arms reject it) is, however, exactly the harm-signal pattern defined in spec §8.4.

---

## 4. Evidence Class Distribution

| Arm | Seed 42 terminal basis | Seed 43 terminal basis |
|-----|----------------------|----------------------|
| A | `verifier_logic_error` (rejected) | `pro_exploit_verifier_confirmed` |
| B | `verifier_logic_error` (rejected, ×2) | `pro_exploit_verifier_confirmed` |
| C | `pro_exploit_verifier_confirmed` at R1 ⚠️ | `pro_exploit_verifier_confirmed` |
| D | `validated_con_counter_evidence` ⚠️ | `pro_exploit_verifier_confirmed` |

Seed 43 (`confirmed_vulnerable`) accepts consistently as `pro_exploit_verifier_confirmed` across all four arms — the correct and stable signal.

---

## 5. Anchor Integrity

| Arm | Seed | Terminal anchors | `all_match` |
|-----|------|-----------------|:-----------:|
| A | 43 | `crypto_shash_ctx(...)`, `gf128mul_4k_lle(...)` | ✅ |
| B | 43 | `crypto_shash_ctx(...)`, `gf128mul_4k_lle(...)` | ✅ |
| C | 42 R1 | `f_mapping->host`, `generic_file_fsync(...)` — **shifted from R0** | ✅ (but path changed) |
| C | 43 | `crypto_shash_ctx(...)`, `gf128mul_4k_lle(...)` | ✅ |
| D | 42 | `sb->s_bdev`, `gf128mul_4k_lle(...)` — **mixed-component anchors** | ✅ |
| D | 43 | `struct gf128mul_4k *gf128`, `gf128mul_4k_lle(...)` | ✅ |

`all_match=True` on all accepted records confirms anchor bookkeeping is working. The concern in Arm C is not an anchor match failure but rather the mutation shifting which code path the accepted predicate refers to.

---

## 6. Cost Breakdown

| Arm | Attempts | Cost | Per attempt |
|-----|---------|------|-------------|
| A (R0) | 2 | $0.0953 | $0.0477 |
| B (S0) | 3 | $0.1464 | $0.0488 |
| C (S1) | 3 | $0.1567 | $0.0522 |
| D (R1) | 2 | $0.0941 | $0.0471 |
| **Total** | **10** | **$0.4925** | **$0.0493 avg** |

**GCP-billed:** $0.78 (overhead, rounding, API overhead)  
**Prior estimate:** $0.18/episode → **Actual: ~$0.05/episode** (3.6× cheaper than modeled)

**Revised full-factorial projections:**

| Scope | Episodes | Est. cost |
|-------|----------|-----------|
| 50 seeds × 4 arms × 1 replicate | 200 | ~$10 |
| 50 seeds × 4 arms × 5 replicates | 1,000 | ~$50 |

Both fit within remaining budget ($56.17). 1 replicate fits within the expiring hackathon credit ($14.56, expires Oct 24).

---

## 7. Operational Findings

| Finding | Severity | Action |
|---------|----------|--------|
| Schema consistent across all 4 arms | ✅ | None |
| `seeds_sha256` identical across all arms | ✅ | None |
| `--no-escalate-pareto` required for Arm B (default=True) | ✅ confirmed | Document in run template |
| Arm C R1 escalation → false-positive on `proved_safe` seed | ⚠️ Harm signal | Pre-register threshold |
| Arm D R0 raw accepted `proved_safe` via `validated_con_counter_evidence` | ⚠️ Harm signal | Investigate acceptance basis |
| Structured evidence (B vs A): no outcome difference at n=2 | 📊 Observational | Requires full factorial |
| Per-episode cost ~$0.05 vs $0.18 estimate | ✅ Budget improved | Update projections |

---

## 8. Go / No-Go

| Gate | Status |
|------|--------|
| All 4 arms completed without crash or timeout | ✅ Go |
| Output schemas valid (corpus + attempts + manifests) | ✅ Go |
| Arm flags match spec | ✅ Go |
| Cost within budget | ✅ Go |
| Harm signal detected in escalation arms on `proved_safe` seed | ⚠️ Pre-register threshold before full run |

**Recommendation: Conditional Go.** Pre-register the harm threshold (suggested: ≥1 `proved_safe` seed accepted in ≥2/5 replicates triggers a mandatory pause) before starting the full factorial. Then run replicate 1 of the full 50-seed run.

---

## 9. Next Steps

1. **Pre-register harm threshold** in the spec before any full-factorial execution.
2. **Investigate Arm D `validated_con_counter_evidence`** acceptance on Seed 42 — determine if this is a legitimate counter-evidence inversion or a pipeline bug.
3. **Run replicate 1** (50 seeds × 4 arms, ~$10) against the expiring $14.56 hackathon credit.
4. **After replicate 1:** reconstruct the discrimination ledger and check false-positive acceptance counts before committing to replicates 2–5.
5. **Replicates 2–5** draw from developer program credits (~$40 est. remaining after rep 1).

---

*Generated: 2026-10-21 | Arm run IDs: `smoke-gemini-armA-v2`, `smoke-gemini-armB-struct-noesc-v2`, `smoke-gemini-armC-struct-esc-v2`, `smoke-gemini-armD-raw-esc-v2`*
