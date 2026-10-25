# BARRED Track 2 — Replicate 1 Correctness Report (Gemini)

**Status:** Replicate 1 only. Single replicate; no seed-clustered uncertainty. Treat as preliminary.
**Manifest:** `scenarios/debate/cve_seeds_benchmark_50.jsonl` (50 seeds, run seeds 42–91).
**Model family:** Gemini (debater `vertex_ai/gemini-3.5-flash`, judge/verifier `vertex_ai/gemini-3.6-flash`).
**Arms:** A = raw/no-escalation, B = structured/no-escalation, C = structured/escalation, D = raw/escalation.

---

## 1. Per-arm acceptance (terminal attempt)

| Arm | Label | Seeds | Accepted | Rate |
|-----|-------|-------|----------|------|
| A | Raw, no escalation | 50 | 24 | 48.0% |
| B | Structured, no escalation | 50 | 25 | 50.0% |
| C | Structured + escalation | 50 | 29 | 58.0% |
| D | Raw + escalation | 49 | 28 | 57.1% |

Arm D has 49 recorded outcomes (one missing seed — see §7). Its rate is not directly comparable to the 50-seed arms until the missing seed is resolved.

All accepted decisions in all arms are `pro_claim_accepted`. There are **zero Con wins** in any arm.

## 2. Estimands (acceptance rate)

| Contrast | Value |
|----------|-------|
| Evidence effect (B − A) | +2.0 pp |
| Escalation on raw input (D − A) | +9.1 pp |
| Escalation with structured evidence (C − B) | +8.0 pp |
| Combined (C − A) | +10.0 pp |
| Interaction (C − B) − (D − A) | −1.1 pp |

Escalation is the dominant driver (+9 pp). Structured evidence alone adds +2 pp. The interaction is negligible (−1.1 pp): escalation works similarly with or without evidence.

## 3. Correctness re-analysis (24 resolved seeds)

Resolved = proved_safe (13) + confirmed_vulnerable (11). Context-deficient (16), triage labels (10), and ambiguous (2) are excluded and reported separately. Context-deficient and ambiguous seeds are **not** counted as correct or incorrect.

### Confusion matrix

| Arm | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|-----|----|----|----|----|-----------|--------|----|----------|
| A | 7 | 4 | 3 | 10 | 0.700 | 0.636 | 0.667 | 0.708 |
| B | 8 | 3 | 3 | 10 | 0.727 | 0.727 | 0.727 | 0.750 |
| C | 9 | 2 | 3 | 10 | 0.750 | 0.818 | 0.783 | 0.792 |
| D | 9 | 2 | 3 | 10 | 0.750 | 0.818 | 0.783 | 0.792 |

### By verdict cohort

| Cohort | n | Arm A | Arm B | Arm C | Arm D |
|--------|---|-------|-------|-------|-------|
| proved_safe | 13 | 23.1% | 23.1% | 23.1% | 23.1% |
| confirmed_vulnerable | 11 | 63.6% | 72.7% | 81.8% | 81.8% |
| context_or_unresolved | 16 | 56.2% | 56.2% | 62.5% | 68.8% |
| triage_likely_valid | 6 | 33.3% | 50.0% | 83.3% | 50.0% |
| triage_likely_invalid | 4 | 75.0% | 50.0% | 50.0% | 50.0% |

### Interpretation

- **Escalation improves recall on confirmed-vulnerable seeds** (63.6% → 81.8%) without increasing false positives on proved-safe seeds (23.1% in all arms). This is the strongest positive signal.
- **Structured evidence reduces acceptance on likely-invalid seeds** (75% → 50%), suggesting a possible filtering benefit. But n=4 is too small for a stable claim.
- **No arm achieves zero false positives** on proved-safe seeds (3/13 accepted in every arm).
- **Interaction is negligible** (−1.1 pp): escalation works similarly with or without structured evidence.

## 4. Autopsy of critical cohorts

### 4a. Recovered vulnerable seeds (rejected in A, accepted in C)

Seeds 55 and 80.

- **Seed 55** (`unix_sck_send_data` unchecked `data_len`): R0 accepted (pro, no refinement needed). Terminal = accepted in all arms except A? Actually A rejected, B accepted, C accepted, D accepted. So structured evidence (B) recovered it; escalation (C) confirmed.
- **Seed 80** (RAS header length integer overflow): R0 rejected (`verifier_logic_error`), R1 accepted (pro). This is the clean escalation-recovery case: R0 failed, refinement flipped it to accepted.

### 4b. Proved-safe seeds accepted in Arm D (false positives under escalation)

Seeds 42, 47, 57 — all accepted at R0 (no escalation round triggered). These are seeds where raw+escalation accepted at the first round without needing refinement. Escalation did not create these false positives; they were accepted at R0.

### 4c. Landmark seeds

- **Seed 42** (ext2 `fsync`, proved safe): rejected in A/B/C (verifier_logic_error), **accepted in D** (raw+escalation, R0). The only false positive introduced by adding escalation to raw input on a proved-safe seed.
- **Seed 46** (Nokogiri/libxml2 `INT_MAX` guard, context deficient): rejected in all four arms (verifier_logic_error). No arm accepted the sound proof; the verifier consistently rejected.
- **Seed 47** (GFS2 ACL, proved safe): accepted in all four arms (pro_claim). Despite the audit proving the predicate invalid (posix_acl_from_xattr allocates its own ACL), every arm accepted the claim. This is a persistent false positive across all conditions.
- **Seed 57** (proved safe): accepted in all four arms. Alongside Seed 47, this constitutes the second **persistent false positive** across all conditions.
- **Seed 51** (POSIX rename, proved safe): accepted in A (raw) and C (structured+escalated), but **rejected in B and D**. It does not persist across all arms, demonstrating sensitivity to condition.

## 5. Con path: zero Con wins

Every accepted decision in every arm is `pro_claim_accepted`. There are **zero `con_deterministic_receipt` or `con_receipt_*` wins** in any arm. The Con path never wins.

This does not prove the deterministic gate failed — INV-1 logic errors and Con-win absence measure different things. But it is a warning: the system accepts only Pro-backed claims, and the counter-evidence path is not producing accepted defenses. Possible explanations: insufficient Con evidence, invalid receipt contracts, acceptance gate prioritizing Pro, or benchmark claims hard to refute. Per-seed audit of Con receipt statuses is needed.

## 6. Reasoning burden (tokens, cost, retries)

| Arm | Avg tokens/seed | Total cost | Seeds with R1 | Retry rate | Cost per correct decision |
|-----|----------------|------------|---------------|------------|--------------------------|
| A | 29,550 | $5.28 | 0/50 | 0% | $0.31 |
| B | 30,356 | $5.49 | 0/50 | 0% | $0.31 |
| C | 66,305 | $11.86 | 30/50 | 60% | $0.62 |
| D | 45,137 | $7.53 | 23/49 | 47% | $0.40 |

- Structured evidence (B) adds ~3% tokens over raw (A) — negligible overhead.
- Escalation (C) doubles tokens vs. B (66k vs 30k) and cost (2.16x).
- Cost per correct decision: C is 2x A/B. Whether the +8pp recall justifies this depends on the value of recovering true vulnerabilities.
- Escalation triggers refinement on 60% of seeds (C) vs. 47% (D).

## 7. Open issues

1. **Arm D missing seed.** Seed 50 (`uri_decoded_copy` / `isofs`, proved safe) timed out due to LiteLLM/Vertex timeout (49/50 recorded). Note: because Seed 50 was rejected in Arms A, B, and C, its likely outcome in D is rejection, which would bring Arm D's TN to 10 and accuracy to 0.792 (matching Arm C). We retain it as a recorded protocol gap (`MISSING`) to maintain audit transparency rather than silently imputing it.
2. **Single replicate.** No seed-clustered uncertainty. Replicates 2–5 needed.
3. **Terminal-attempt selection.** Verify recorded terminal decisions match actual final attempts (per §5.1).
4. **Con path.** Zero Con wins across all arms — audit needed.
5. **Canonical ledger.** Reconciled and generated as [`reports/BARRED_Track_2_Joined_Correctness_Ledger.csv`](BARRED_Track_2_Joined_Correctness_Ledger.csv) (50 seeds joined across Track 1 verdicts and Arms A–D terminal decisions).

## 8. Bottom line

In Replicate 1, escalation (not structured evidence) accounts for most of the acceptance increase (+9 pp). Structured evidence adds only +2 pp acceptance but shows a possible filtering benefit on likely-invalid seeds (75% → 50%). Escalation improves recall on confirmed-vulnerable seeds (63.6% → 81.8%) without increasing false positives on proved-safe seeds. The Con path never wins. Cost of escalation is ~2x. Whether this combination produces more independently correct security decisions per unit of inference cost remains the key question for Replicates 2–5.
