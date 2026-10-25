# BARRED Track 2 — Experiment Specification: Evidence vs. Escalation

**Status:** Draft v2 — revised per review; blocking issues (A–D) addressed. Ready for freeze after final check.
**Purpose:** Determine whether structured evidence, escalation policy, or their interaction produces the observed acceptance improvement, and whether that improvement survives an independent predicate audit.
**Tracks:** This is Track 2 of the four-track segmentation in `reports/BARRED_Evidence_Digest_v1.md`. Track 1 (predicate audit) exit criteria are substantially complete (15 persistent-split + 10 pro-claim seeds adjudicated).

---

## 1. Research question

> Does structured evidence discharge part of a model's reasoning burden without increasing security errors, and does escalation add anything beyond evidence alone?

Secondary: where does structured evidence cease to be sufficient (Axis D ceiling), and does escalation change that ceiling?

## 2. Design: four-arm factorial

Two factors, each two levels:

- **Evidence**: Raw (R) vs. Structured (S) — whether the debater receives the raw seed code only, or the code plus a structured evidence packet (CVEFixes row, caller context, contract notes).
- **Escalation**: Off (0) vs. On (1) — whether a second refinement round with reflector feedback is permitted.

| Arm | Label | Evidence | Escalation | Estimand |
|-----|-------|----------|------------|----------|
| A | R0 | Raw | Off | Baseline acceptance |
| B | S0 | Structured | Off | Evidence effect (B − A) |
| C | S1 | Structured | On | Evidence + escalation (C − A) |
| D | R1 | Raw | On | Escalation effect on raw (D − A) |

**Interaction:** (C − B) vs. (D − A) reveals whether escalation works differently with structured evidence than with raw input. This is the correction to the original three-arm design, which could not estimate interaction.

**If compute is limited:** Run A, B, C first (three arms), leave the interaction claim (D) open. Do not claim interaction without D.

## 3. Conditions (matched to existing runs)

Each arm runs all four model-family conditions from the established ledger:

- Gemma sliced baseline (gemma_baseline)
- Gemma progressive escalation (gemma_escalated)
- Gemini baseline (gemini_baseline)
- Gemini escalation (gemini_escalated)

Escalation "On" means the progressive-escalation protocol (refinement round with reflector feedback) is enabled; "Off" means single-round debate with no refinement. Evidence "Structured" means the evidence packet is injected into the debater prompt; "Raw" means only the seed code and predicate.

Model versions, prompts, and decoding parameters are pinned per arm and held constant across arms (see Controls).

## 4. Seed manifest and replication

- **Manifest:** `scenarios/debate/cve_seeds_benchmark_50.jsonl` (50 seeds, run seeds 42–91). Same manifest as the existing Gemma/Gemini ledger, so results are directly comparable.
- **Replicates:** 5 per seed per arm per condition. Per arm: 50 seeds × 5 replicates × 4 model conditions = 1,000 seed–replicate–condition observations. Across all four arms: 4,000 seed–replicate–condition observations. These are observations, not unique API calls — retries, refinement rounds, and failed calls may increase actual calls and cost.
- **Seed recurrence:** The same 50 seeds recur across all 5 replicates and all 4 arms. Do not treat all 250 seed–replicate observations as independent (see Uncertainty).

## 5. Outcome measures

### 5.1 Terminal-attempt rule (pre-run blocker)

The outcome for each seed–replicate–condition is the **actual final attempt** under the permitted protocol, whether accepted or rejected. Do not select the latest accepted attempt when one exists — that uses the outcome to choose the observation and can inflate acceptance (a run that fails at R1 would be recorded as accepted because R0 passed).

Deterministic selection:

1. If escalation is Off: the single attempt is the outcome.
2. If escalation is On: the final refinement attempt (R1) is the outcome, regardless of its decision. R0 is retained in the attempt history but is not the outcome.
3. Tie-breaking: if multiple attempts share the maximum `refinement_round`, select the one with the highest attempt index in file order. If still tied, select the first in file order.
4. Retain the complete attempt history (every attempt, decision, reject reason, round, evidence class) in the run ledger. Reconstruct the terminal decision from raw attempts during analysis; do not trust a pre-aggregated field.

A successful R0 followed by a failed R1 is recorded as rejected. This matches deployed protocol behavior only if the deployed protocol stops on the first acceptance; document which behavior the deployed protocol actually uses and align the experiment to it.

Primary:
- **Acceptance rate** (pipeline outcome: `decision == "accepted"` at terminal attempt). Reported per arm, per condition, per seed.
- **Terminal rejection reason** distribution (`reject_reason`), preserved separately and never collapsed into a single rate.

Secondary (from the discrimination ledger):
- **Evidence class** of each accepted decision (`pro_claim_accepted`, `con_deterministic_receipt`, `con_receipt_<status>`, `con_receipt_missing`). An acceptance backed only by `con_receipt_invalid_contract` or `con_receipt_missing` does not count as deterministic defense.
- **Family discrimination** (`persistent_gemma_only`, `persistent_gemini_only`, `mixed_family_split`, `no_persistent_family_split`) per seed per arm.
- **Escalated evidence status** (`conflicting_unadjudicated_model_outcomes`, `pro_claim_needs_independent_reproduction`, `defense_receipt_recorded_needs_scope_review`, `conclusion_not_deterministically_discharged`, `no_accepted_claim_to_adjudicate`).

Tertiary (correctness, where adjudicated):
- **Independent adjudication status** per seed (proved safe / confirmed vulnerable / context-deficient), from the Track 1 ledger. Used to recompute acceptance metrics on the subset of seeds with a resolved verdict, so that "acceptance" can be compared against "correctness."

## 5.2 Canonical adjudication ledger (Track 1 reconciliation)

The Track 1 independent adjudications must be reconciled into one canonical ledger before analysis. The specification previously mixed cohort descriptions ("15 persistent-split," "33 of 50 with a verdict," "20 refuted / 3 confirmed / 3 deficient / 7 others") without explaining their relationship. Generate all Section 7.3 counts from this ledger; do not hand-count.

One row per seed (50 rows), with separate fields:

| Field | Meaning |
|-------|---------|
| `predicate_status` | Is the claimed vulnerability mechanism valid? (valid / invalid / unresolved) |
| `mechanism_status` | Was the defect demonstrated or refuted? (demonstrated / refuted / not_tested) |
| `reachability_status` | Is the defect reachable by an attacker? (reachable / not_reachable / unproven) |
| `contract_status` | Did a counter-evidence receipt hold a valid contract? (valid / invalid_contract / missing) |
| `security_verdict` | Independently adjudicated verdict: proved_safe / confirmed_vulnerable / context_deficient / not_yet |
| `adjudication_confidence` | high / medium / low |
| `adjudication_source` | Which audit report / evidence established the verdict |

Context-deficient is **not** a resolved security verdict and must not be merged into proved_safe or confirmed_vulnerable. Counts in Section 7.3 are generated from this ledger by filter, not by hand.

Current state (as of Track 1 close): 23 adjudicated (14 proved_safe, 6 confirmed_vulnerable, 3 context_deficient) + 27 not-yet. The canonical ledger is `reports/barred_gemma_gemini_discrimination_ledger.csv` plus the per-seed `BARRED_Track_1_Seed_XX_Evidence_Audit.md` reports; a dedicated canonical file should be produced before Track 2 analysis.

## 6. Controls (hold constant across all arms)

- **Model identifiers (pinned, not named loosely):** record provider model ID, version/snapshot, inference settings (temperature, top-p, max tokens), and runtime configuration for each model family. "Gemini 3.8 Flash" and "Gemma sliced baseline" are not sufficiently precise experiment identifiers on their own.
- **Seed manifest and ordering.**
- **Acceptance rules and terminal-attempt selection** (see Section 5.1).
- **Prompt and packet freeze:** version the prompt templates, evidence-packet schema, source-selection rules, and packet-generation code. The structured-evidence arm must not receive information generated from the independent verdicts (blinded).
- **Evidence packet completeness:** some seeds may lack reliable source-version metadata, caller context, or contract information. Record packet completeness per seed; do not quietly substitute different evidence. A packet's missing fields are part of the treatment's fidelity, not a silent imputation.
- **Budgets (separate per-attempt and total):** keep comparable per-attempt limits, but report total tokens, cost, attempts, and latency. Escalation is expected to alter total consumption. Define a total budget per arm before execution.
- **Retry / token budget per attempt.**
- **Judge prompt and schema (Pydantic validation).**
- **Refinement-round cap (R0/R1 as in existing runs).**
- **Random seed / temperature (pin or document).**
- **Run order:** randomize or interleave across arms so that provider-side changes, shared mutable state, or rate limits cannot systematically favor one arm. Keep the Pareto registry frozen or isolate it per arm so one treatment cannot train another.
- **Adjudication criteria and RFC taxonomy buckets (A–E).**

Any change to a control between arms invalidates the comparison and must be recorded as a protocol deviation.


## 7. Analysis plan

### 7.1 Estimands

- Evidence effect (no escalation): B − A
- Escalation effect (raw input): D − A
- Escalation effect (with evidence): C − B
- Combined (evidence + escalation): C − A
- Interaction: (C − B) − (D − A)

### 7.2 Uncertainty

- **Do not** treat all 250 seed–replicate observations as independent. The same 50 seeds recur across replicates.
- Use a seed-clustered bootstrap or a mixed-effects model with seed as a random effect, replicate as a nested observation. Report 95% intervals on seed-level (not observation-level) units.
- Report both per-seed deltas and aggregate deltas. A seed that flips from 0/5 to 5/5 contributes more information than five seeds each moving 0→1.

### 7.3 Correctness re-analysis (two distinct outcomes)

Retain two separate outcomes throughout; never collapse them:

1. **Pipeline acceptance** — did the prescribed process accept the claim? Reported across the full 50-seed manifest for reproducibility and comparability with existing runs.
2. **Adjudicated security outcome** — was that acceptance correct for the exact claim, per independent evidence? Reported only on seeds with a resolved verdict (proved_safe or confirmed_vulnerable). Context-deficient seeds are reported separately and are neither correct nor incorrect.

Do not present acceptance uplift on invalid predicates as security improvement. If the primary scientific claim is restricted to predicates independently established as valid, pre-register that scope now; if that cohort is too small, label the result exploratory.

- Recompute acceptance metrics split by verdict on the resolved subset. This tests whether any arm's "improvement" is concentrated on seeds the audit refuted.
- Seeds without an independent verdict are reported separately; do not impute a verdict.


### 7.4 Evidence-class disaggregation

- Report acceptance split by evidence class. An arm whose uplift is entirely `pro_claim_accepted` on seeds the audit refuted is flagged, not celebrated. An arm whose uplift is `con_deterministic_receipt` on seeds the audit confirmed-vulnerable is the desired signal.

### 7.5 Family discrimination

- Report `persistent_gemma_only` / `persistent_gemini_only` counts per arm. If escalation creates persistent splits that the audit refutes, that is a harm, not a benefit.

## 8. Stopping criteria

Stop and reassess (do not continue to full replication) if any of:

1. **Protocol deviation:** A control (model version, prompt, acceptance rule, budget) changes between arms mid-run.
2. **Label invalidity:** Track 1 finds that a substantial fraction (>25%) of the 50 seeds have invalid predicates, and the acceptance metric has not been redefined to exclude them. (Track 1 exit gate.)
3. **No signal:** Define the minimum meaningful effect as 5 percentage points (2.5 additional acceptances per 50 seeds), justified substantively (a change smaller than this is not actionable). After 2 arms × 2 replicates, treat that stage as a **technical and safety pilot**, not a strong inferential stopping test — 50 seed clusters are too few for a reliable seed-clustered interval. Pre-register whether the full five replicates will be completed unless a safety or protocol failure triggers a pause. State explicitly which interval outcomes trigger continuation, futility, or inconclusive status.
4. **Harm signal:** Any arm shows an increase in `pro_claim_accepted` on seeds independently adjudicated as "proved safe" (false-positive acceptance). Specify a practical harm threshold in advance (e.g., ≥ 1 seed flipped to false-positive acceptance, or any seed moving from 0/5 to ≥ 2/5) in addition to any statistical test. A lack of statistical significance in a small adjudicated cohort must not be described as evidence of no safety regression. Report false-positive acceptance counts and their uncertainty.
5. **Cost overrun:** Cumulative token cost exceeds 2× the three-arm estimate without completing arm D.

If a stopping criterion fires, write a partial-results report and reassess before spending more.

## 9. Deliverables

1. **Experiment specification** (this document, frozen before any run).
2. **Run ledger** (per-arm, per-condition, per-seed, per-replicate attempt JSONL, matching the existing artifact format under `artifacts/attempts/`).
3. **Paired analysis report** (seed-level deltas, bootstrap intervals, evidence-class disaggregation, family-discrimination counts, correctness re-analysis) as `reports/BARRED_Track_2_Paired_Results.md`.
4. **Updated discrimination ledger** (re-run `build_gemma_gemini_discrimination_ledger.py` on the new arm outputs if the arm changes the condition set).

## 10. What this experiment does NOT establish

- It does not establish that any model is "correct." Acceptance is a pipeline outcome; correctness requires an independent audit (Track 1).
- It does not establish that structured evidence is safe to deploy. A higher acceptance rate on invalid predicates is a harm.
- It does not generalize beyond the 50-seed manifest. Replication on a different seed set is a separate study.
- It does not resolve the Axis D ceiling (evidence sufficiency) — that is Track 3.

## 10.5 Recommended execution sequence (per review)

1. **Freeze the protocol.** Correct observation counts, terminal-attempt selection, canonical adjudication counts, model identifiers, packet schema, and stopping rules (all addressed in this v2).
2. **Run a small operational smoke test.** Verify all four arms, output schemas, retry behavior, cost accounting, frozen configuration, and ledger reconstruction on a few seeds. Do not use the smoke test to select a favorable treatment or estimate the final effect.
3. **Execute the matched factorial.** Run all four arms with the same manifest and five replicates per seed and model condition, unless a pre-registered safety or protocol stop is triggered.
4. **Reconstruct the ledger from raw attempts.** Verify that the recorded terminal decision matches the actual final attempt. Preserve rejected attempts and reasons, not just successful outcomes.
5. **Analyze before interpreting.** Calculate paired treatment effects and seed-clustered intervals; then disaggregate by evidence class, model-family disagreement, and independently adjudicated verdict.

## 11. Open questions (resolved per review)

1. **Run D in the first batch?** Yes — required to estimate the interaction. (Resolved: include D.)
2. **Include Track 1 verdicts in the evidence packet?** No — blinds the agents; verdicts used only in post-hoc correctness re-analysis. (Resolved: blinded.)
3. **Add Qwen as a fifth model family?** Not yet — keep as diagnostic appendix. (Resolved: appendix.)

Additional reviewer decisions adopted:

- Retain all four arms from the beginning; do not collapse to three.
- Treat a structured evidence packet as a treatment whose provenance must be auditable, not as automatically valid evidence.
- For Qwen, preserve outputs and the independent Seed 51 finding as a predicate-invalidity case study; two Qwen models agreeing is diagnostic, not an independent correctness oracle.

