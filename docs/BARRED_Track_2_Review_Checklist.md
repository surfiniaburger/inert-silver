# BARRED Track 2 — Review Checklist (Replicate 1, Gemini)

Derived from the Track 2 review. These items must be resolved before the Replicate 1 numbers are treated as final or published.

## Blocking (resolve before publication)

- [ ] **Arm D missing seed.** Arm D has 49 recorded outcomes vs. 50 for A/B/C. Identify the missing seed and its final attempt. If it is a genuine protocol failure, report it rather than silently excluding it. Recompute D−A and the interaction with the complete denominator.
- [ ] **Terminal-attempt selection.** Verify that the recorded terminal decision matches the actual final attempt in the permitted protocol (per Track 2 spec §5.1). Preserve rejected attempts and reasons; do not trust a pre-aggregated field.
- [ ] **Adjudication cohort definition.** Reconcile the 28-case cohort (13 proved-safe + 11 confirmed-vulnerable + 4 likely-invalid) against the canonical Track 1 ledger. Produce one canonical row per seed with `predicate_status`, `mechanism_status`, `reachability_status`, `contract_status`, `security_verdict`, `adjudication_confidence`, `adjudication_source`. Generate all correctness counts from that ledger, not by hand. Keep context-deficient and not-yet-adjudicated seeds separate (they are not resolved verdicts).
- [ ] **Interaction uncertainty.** The interaction point estimate (−1.1 pp) is not established as negligible. Compute seed-clustered bootstrap 95% intervals for each estimand. State which interval outcomes trigger continuation, futility, or inconclusive status.
- [ ] **Con path audit.** Every accepted decision in every arm is `pro_claim_accepted` (zero Con wins). Determine why: insufficient Con evidence, invalid receipt contract, acceptance gate prioritizing Pro, or benchmark claims hard to refute. Inspect per-seed acceptance evidence classes, Con receipt statuses, rejection reasons, and verifier decisions. Do not describe zero Con wins as proof that the deterministic gate failed — INV-1 logic errors and Con-win absence measure different things.

## Analysis improvements (before publication)

- [ ] **Cost per independently correct decision** as a primary efficiency metric (not just cost per accepted row). Report alongside sensitivity, false-positive acceptance, and total cost.
- [ ] **Correctness-aware paired contrasts.** For each adjudicated seed, compare A, B, C, D on the actual terminal decision. Keep unresolved predicates separate; do not impute verdicts.
- [ ] **Evidence-class disaggregation.** Report acceptance split by evidence class (`pro_claim_accepted`, `con_deterministic_receipt`, `con_receipt_<status>`, `con_receipt_missing`). Flag any arm whose uplift is concentrated on `pro_claim_accepted` for seeds the audit refuted.
- [ ] **Family discrimination.** Report `persistent_gemma_only` / `persistent_gemini_only` counts per arm. If escalation creates persistent splits that the audit refutes, flag as harm.
- [ ] **False-positive acceptance reporting.** Report counts and uncertainty for `pro_claim_accepted` on proved-safe seeds. A lack of statistical significance in a small cohort is not evidence of no safety regression.

## Framing / reporting

- [ ] **Reframe the central finding:** not "structured evidence reduces reasoning load" but "in Replicate 1, escalation accounts for most of the acceptance increase while structured evidence shows a possible filtering benefit on likely-invalid claims."
- [ ] **Label as Replicate 1** throughout. Do not change model, prompts, or protocol and then call the next run a replication of the same condition.
- [ ] **Report the 28-case cohort honestly:** 13 proved-safe, 11 confirmed-vulnerable, 4 likely-invalid = 28. State the mapping to the canonical ledger and the adjudication confidence of each.
- [ ] **Report Con-win absence as a diagnostic**, not as a gate-failure verdict. Note the distinction between INV-1 logic errors and Con-win absence.

## Execution gating

- [ ] **Resolve Arm D's missing seed and recompute all contrasts** before any further analysis is finalized.
- [ ] **Continue to Replicates 2–5 only when compute permits**, preserving the frozen protocol. Replicates establish whether seed-level patterns persist and provide seed-clustered uncertainty estimates.
- [ ] **Do not launch the full run until the four blocking issues (sample-size arithmetic, terminal-attempt rule, adjudication-count reconciliation, invalid-predicate handling) in the Track 2 spec are fixed** — already addressed in v2, but verify before freeze.

## Status

- Track 2 spec: v2 (blocking issues A–D addressed).
- Replicate 1 analysis: draft (pending the items above).
- Con path audit: not started.
- Canonical adjudication ledger: not yet produced (counts are hand-derived from the discrimination CSV + per-seed reports).
