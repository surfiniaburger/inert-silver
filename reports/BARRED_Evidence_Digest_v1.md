# BARRED Evidence Digest v1

**Status:** Internal research artifact — not a public README, not an experiment.
**Purpose:** Digest existing measurements before building more system. Establish which claims survive scrutiny and what experiment would genuinely change our understanding.
**Convention:** Every claim is labeled Observed / Inferred / Unresolved.

---

## 1. Digest: three questions

### A. What improved?

| Observation | Source | Status |
|-------------|--------|--------|
| Gemma progressive escalation: 85.2% accepted yield (213/250 episode slots), 56/93 Round-0 failures recovered at R1 | `reports/debate_benchmark_50_seed_progressive_escalation.md` | Observed |
| Gemini escalated aggregate: 59.2% accepted yield vs 56.0% baseline (+3.2pp, ~1.6 rows per 50-seed run) | `reports/gemini_evidence_vs_protocol_control_report.md` | Observed |
| Gemini paired ledger: baseline 140 accepted, escalated 148 accepted (+8 rows) across 250 seed–replicate pairs | `reports/gemini_seed_paired_summary.json` | Observed |
| Qwen3.5-4B compact run: 7/10 seeds accepted (42, 43, 44, 45, 46, 49, 51); 3 failed (47, 48, 50) | `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl` | Observed |
| Qwen R1 recovery: 3/6 R0-failures recovered (seeds 42, 43, 51); 3/6 failed at R1 (seeds 47, 48, 50) | `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl` | Observed |

**Inferred:** Acceptance rate improved in both Gemma and Gemini escalated conditions, but acceptance is not correctness — see Section 1C.

**Unresolved:** Whether the improvement is attributable to evidence injection, escalation policy, or their interaction.

---

### B. What caused the improvement?

| Observation | Source | Status |
|-------------|--------|--------|
| Gemini comparison changes both evidence/reflection config AND escalation protocol simultaneously | `reports/gemini_evidence_vs_protocol_control_report.md` | Observed |
| Mean paired delta accepted: +0.032; 218/250 paired observations show zero delta; CI includes zero | `reports/gemini_seed_paired_summary.json` | Observed |
| Qwen R1 recovery used `validated_con_counter_evidence` (seeds 42, 45, 46, 49, 51) and `pro_exploit_verifier_confirmed` (seed 43) | `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl` | Observed |
| Qwen R1 failures: seeds 47 (Axis E, verifier_failed), 48 (Axis C, judge_parse_failed), 50 (Axis C, judge_parse_failed) | `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl` | Observed |

**Inferred:** The aggregate improvement is real but small and uncertain. The same-seed paired analysis shows most pairs are unchanged — the uplift is concentrated in a minority of seeds (seeds 50, 51 in Gemini; seeds 42, 43, 51 in Qwen). Qwen R1 failures split between fixable plumbing (Axis C, 2/3) and true evidence/verifier failures (Axis D/E, 1/3).

**Unresolved:** Whether structured evidence alone (holding escalation constant) produces the improvement, or whether escalation policy contributes independently.

---

### C. Were the decisions actually right?

| Observation | Source | Status |
|-------------|--------|--------|
| Seed 51: benchmark labels Vulnerable, but predicate asserts symlink-overwrite via `rename()` — Gemini 3.8 Flash rejected it because POSIX `rename(2)` does not dereference symlinks | `docs/RFC_EPISTEMIC_REACH_AND_EVIDENCE_SUBSTITUTION.md` Section 2.1 | Observed (receipt) |
| Seed 46: verifiers detected upstream `INT_MAX` guard invalidating proposed integer-overflow exploit | User note in digest input | Observed |
| Qwen seed 47: verifier rejected UAF claim in `__gfs2_get_acl`, `passes_audit: false` — mechanism demonstrably false | `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl` | Observed |
| Qwen seed 49: accepted via `validated_con_counter_evidence` — deterministic guard evidence (`wbmp == NULL` check) overrode benchmark predicate | `artifacts/attempts/uzu-all-qwen-pilot-101.jsonl` | Observed |
| Gemini seed 44: baseline accepted, escalated rejected — safe-code invariant quarantine preserved | `reports/gemini_seed_paired_summary.json` | Observed |

**Inferred:** Benchmark labels, vulnerability predicates, verifier decisions, and actual security properties are four different variables. A deterministic gate can consistently enforce an invalid predicate. Disagreement with a benchmark oracle does not, by itself, establish that the model is correct.

**Priority:** Question C is a priority, not a footnote. If the benchmark predicate is wrong, improving agreement with it makes the score look better while making the security conclusion worse.

**Unresolved:** Independent adjudication of disputed predicates (seeds 46, 51, 47) — has the vulnerability mechanism been independently verified as valid or invalid?

---

## 2. Four-track work segmentation

| Track | Question | Deliverable | Priority |
|-------|----------|-------------|----------|
| **01** | Evidence and predicate audit — are we measuring the right thing? | Case-level evidence and adjudication ledger | **First** |
| **02** | Evidence-versus-protocol — what actually produces the improvement? | Experiment specification + paired results report | Second |
| **03** | Evidence sufficiency — what can deterministic analysis establish on its own? | Evidence-sufficiency matrix + failure examples | Third |
| **04** | Compact-model substitution — can better evidence reduce need for expensive reasoning? | Model-substitution report with quality/cost trade-offs | Fourth |

**Track ordering rationale:** No experiment can establish meaningful security improvement if the benchmark's ground truth is unreliable. Track 1 must complete before Track 2 is meaningful.

---

## 3. Experiment design correction (Track 2)

The three-arm design from "From Benchmark Yield to Evidence Sufficiency":

| Arm | Input | Escalation |
|-----|-------|------------|
| A | Raw | Off |
| B | Structured evidence | Off |
| C | Structured evidence | On |

Estimates: evidence effect without escalation (B − A); incremental escalation effect with evidence (C − B).

**Correction:** Three arms cannot estimate whether evidence and escalation interact. To estimate interaction, add a fourth arm:

| Arm | Input | Escalation |
|-----|-------|------------|
| D | Raw | On |

With all four arms: (C − B) vs (D − A) reveals whether escalation works differently with structured evidence than raw input.

**Controls (hold constant across all arms):** model version, seed manifest, acceptance rules, retry/token budget, adjudication criteria.

**Uncertainty method:** The same 50 seeds recur across replicates — do not treat all 250 seed–replicate observations as independent. Use uncertainty estimates that account for repeated seeds.

**If compute is limited:** Start with three arms (A, B, C), leave the interaction claim (D) open.

---

## 4. Claim ledger (Track 1 input)

| # | Claim | Observed measurement | Denominator / scope | What it does NOT establish | Status |
|---|-------|---------------------|---------------------|---------------------------|--------|
| C1 | Progressive escalation improves accepted yield | Gemma: 85.2% vs baseline; Gemini: 59.2% vs 56.0% | Fixed 50-seed manifest, 5 replicates | Whether decisions are correct; whether evidence caused the improvement | Observed |
| C2 | Round-1 recovery recovers R0 failures | Gemma: 56/93 (60.2%) R0 failures recovered | Same 50 seeds, repeated | Whether recovered decisions are correct | Observed |
| C3 | Qwen R1 recovers R0 failures with structured evidence | 3/6 R0 failures recovered (seeds 42, 43, 51) | 10 seeds, 1 replicate | Whether recovery generalizes beyond this manifest | Observed |
| C4 | Qwen R1 failures are fixable plumbing | 2/3 R1 failures were Axis C (parser/interface, schema dropout) | 10 seeds | Whether Axis C is fixable without model changes | Observed |
| C5 | Qwen R1 failures include true evidence ceiling | 1/3 R1 failure was Axis D (evidence insufficiency); 1/3 Axis E (predicate invalidity) | 10 seeds | Whether Axis D is fundamental or addressable | Observed |
| C6 | Same-seed paired Gemini effect is uncertain | Mean delta +0.032, 218/250 zero deltas, CI includes zero | 250 seed–replicate pairs | Whether the effect generalizes beyond 50 seeds | Observed |
| C7 | Disputed predicates exist | Seeds 51, 46, 47 show model-oracle disagreement | Specific seeds | Whether the model is right or the benchmark is wrong | Unresolved |

---

## 5. Predicate audit (Track 1, in progress)

| Seed | Benchmark label | Claimed predicate | Agent decision | Evidence | Independent verdict needed? |
|------|----------------|-------------------|----------------|----------|---------------------------|
| 46 | Safe | Integer overflow → OOB write | Accepted via an invalid-contract counter-evidence path | Narrowing cast is present; the claimed libxml2 `INT_MAX` guard is not in the supplied snippet | **Unresolved** — omitted libxml2 implementation/version |
| 47 | Vulnerable | UAF in `__gfs2_get_acl` | Rejected (`passes_audit: false`) | `data` is input arg, not allocated; `kfree(data)` frees original buffer | Yes — confirm UAF mechanism is structurally impossible |
| 49 | Vulnerable | OOB write in `gdImageWBMPCtx` | Accepted via an invalid-contract counter-evidence path | `wbmp == NULL` handles allocation failure, but `createwbmp()` size arithmetic is omitted | **Unresolved** — guard is not sufficient proof |
| 51 | Vulnerable | Symlink overwrite via `rename(tmpname, PASSWD_FILE)` | Rejected (POSIX semantics) | `rename(2)` does not dereference symlinks; destination hardcoded | Yes — confirm POSIX semantics apply |

**Track 1 deliverable:** A matched Gemma/Gemini 50-seed, five-replicate discrimination ledger, with a separate predicate-adjudication status for high-priority family splits. Qwen is a supporting parser-contract appendix, not the primary population.

---

## 6. Decision gate (Track 1 exit criteria)

Before proceeding to Track 2 (evidence-versus-protocol experiment), the following must be resolved:

- [x] Matched Gemma/Gemini five-replicate, 50-seed discrimination ledger reconciled (primary Track 1 population; 1,000 condition outcomes in `reports/BARRED_Gemma_Gemini_Discrimination_Ledger.md`)
- [ ] High-priority persistent Gemma/Gemini splits independently predicate-adjudicated
- [x] Qwen pilot appendix: seeds 47/48/50 classified, with Axis C confirmed as plumbing rather than evidence insufficiency
- [ ] Experiment specification drafted (arms A–D, controls, uncertainty method, stopping criteria)

If Track 1 finds that the benchmark predicate is invalid for a substantial fraction of seeds, Track 2's acceptance metric must be redefined before running — otherwise we optimize agreement with an invalid label.

---

## 7. Next steps (in order)

1. **Track 1:** Complete predicate audit for seeds 46, 47, 49, 51 (independent adjudication).
2. **Track 1:** Complete case-level RFC taxonomy classification for Qwen run failures.
3. **Track 2:** Draft experiment specification (four-arm design, controls, uncertainty method).
4. **Track 3:** Evidence-sufficiency matrix — what AST/CFG exposes vs. misses per seed.
5. **Track 4:** Compact-model substitution — only after Tracks 1–3 validate predicates and stabilize protocol.

**Central hypothesis to preserve:**

> Can deterministic evidence discharge part of a model's reasoning burden without increasing security errors — and where does that evidence cease to be sufficient?

This gives BARRED a sharper research direction than simply building a larger swarm or optimizing acceptance yield.

---

**Checklist:** 0 of 5 sections marked complete — Track 1 (Sections 4–5) is the immediate focus.
