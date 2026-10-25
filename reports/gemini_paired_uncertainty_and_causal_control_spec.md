# Gemini Paired Uncertainty and Causal-Control Analysis Spec

## Objective

This document specifies the immediate next analysis step for the Gemini 3 benchmark family after the 5-run aggregate summary. The goal is to replace descriptive mean comparisons with a paired, uncertainty-aware comparison that separates:

- protocol effect
- evidence effect
- model effect
- adjudication / oracle disagreement effect

The current aggregate summary already shows the broad pattern:

- baseline accepted mean: 28.0 ± 1.58 / 50
- escalated accepted mean: 29.6 ± 1.52 / 50
- raw net delta: +1.6 accepted rows (+3.2 pp)

This is useful, but it is not yet sufficient to attribute the change to the reflector or to the progressive escalation protocol with confidence.

---

## 1. Why the next step is not more run count

The project already has a replicated family (`rep1`–`rep5`) on the same 50-seed benchmark manifest. The highest-value next move is not to add more runs blindly; it is to turn the replicated data into a paired-difference analysis on the same benchmark registry.

The critical distinction is:

- benchmark manifest = fixed 50-seed holdout
- replicate family = repeated evaluation of that same manifest
- paired comparison = same seed, different condition

The strongest causal evidence comes from comparing the same seed under different conditions, not by comparing run means alone.

---

## 2. Canonical analysis unit

Use each benchmark seed as the atomic unit of comparison.

For seed i in the 50-seed manifest:

- `y_base[i]` = outcome under baseline condition
- `y_escal[i]` = outcome under escalated condition
- `delta[i] = y_escal[i] - y_base[i]`

The outcome can be defined for multiple axes:

- accepted binary: 1 if accepted, 0 otherwise
- vulnerable_accept binary: 1 if a vulnerable seed is accepted, 0 otherwise
- safe_accept binary: 1 if a safe seed is accepted, 0 otherwise
- total_cost
- cost_per_accepted
- token_use
- model_call_count

For each metric, compute the per-seed paired difference across the five replicate intervals or across the relevant same-seed paired runs.

---

## 3. Required definitions before statistical comparison

Before any inference, freeze the reducer and acceptance logic:

1. Accepted row definition
   - what counts as an accepted exploit claim?
   - is acceptance defined by benchmark verdict, final adjudicated verdict, or final accepted corpus row?

2. Vulnerable vs. safe classification
   - use the benchmark manifest class as the primary label
   - keep a separate adjudicated label field for disagreement analysis

3. Model-call accounting
   - count total model calls and total cost consistently across baseline and escalated conditions

4. Reject reason taxonomy
   - encode each failure as one of the RFC axes, not just free-form text

5. Oracle disagreement flag
   - mark cases where the benchmark label and the independently validated predicate differ

This is necessary because otherwise the delta in acceptance could be partly a measurement-definition artifact instead of a true effect.

---

## 4. Paired estimands to report

For each condition pair, report:

- mean paired delta for accepted yield
- mean paired delta for vulnerable acceptance
- mean paired delta for safe acceptance
- mean paired delta for cost per accepted row
- median paired delta for each metric
- bootstrap 95% CI for each delta
- sign test or exact paired p-value where appropriate

### Example estimands

Accepted yield delta:

`delta_accept_i = accepted_escal_i - accepted_base_i`

Vulnerable acceptance delta:

`delta_vuln_i = vuln_accept_escal_i - vuln_accept_base_i`

Safe acceptance delta:

`delta_safe_i = safe_accept_escal_i - safe_accept_base_i`

Cost efficiency delta:

`delta_cost_per_row_i = cost_per_row_escal_i - cost_per_row_base_i`

Prefer a paired, non-parametric bootstrap or permutation-based CI rather than relying on raw run-level means alone. With only five replicate pairs, a bootstrap can still provide a useful distributional estimate for the delta, but the interpretation must be cautious.

---

## 5. Uncertainty reporting requirements

Each report should explicitly separate three layers of uncertainty:

1. run-to-run variation within the same regime
2. paired difference across conditions on the same seed manifest
3. predicate / oracle disagreement uncertainty

The current 5-replicate summary is mostly layer 1. The next phase must add layer 2.

Minimum reporting standard:

- mean ± SD for baseline and escalated
- paired delta mean
- bootstrap 95% CI on delta
- note whether the CI includes zero
- percent of paired seeds where the escalated condition improves on baseline

This becomes the primary evidence for or against a true effect.

---

## 6. Protocol-vs-evidence control design

The current comparison changes both:

- escalation protocol
- evidence supplied to the reflective loop

This is not yet a clean causal attribution. A valid next test must hold everything constant except the evidence interface.

### Controlled experiment specification

Use the same 50-seed manifest, the same adjudication logic, and the same progressive retry protocol.

Then compare three conditions:

1. raw input, no reflector
2. structured evidence, no progressive escalation policy change
3. escalated reflector with deterministic evidence slices

The key comparison is:

- condition 2 vs condition 1: does evidence itself help?
- condition 3 vs condition 2: does the escalation protocol add incremental value?

This lets us distinguish:

- reflector evidence benefit
- protocol benefit
- interaction effect

This is the cleanest way to separate the “evidence mechanism” from the “escalation mechanism.”

---

## 7. Compact-model substitution test

To isolate model-family effects, run a compact-model substitution analysis on the same fixed seed set and same evidence artifacts.

### Proposed matrix

- Gemma with raw input
- Gemma with structured evidence
- Gemini baseline
- Gemini with structured evidence

Hold fixed:

- seed set
- adjudication rules
- evidence extraction pipeline
- normalization / AST / CFG slice definitions
- progressive retry layout (unless intentionally varied for protocol analysis)

Report:

- accepted yield
- vulnerable acceptance
- safe acceptance
- cost per accepted row
- number of successful recoveries by RFC failure class

This comparison answers whether the gain is mostly a model effect, an evidence effect, or an interaction effect.

---

## 8. Independent failure-taxonomy audit

Each residual failure must be classified independently with a deterministic record of:

- evidence available
- evidence missing
- whether the model used the evidence correctly
- whether the benchmark predicate itself is semantically valid
- whether there is oracle disagreement

### Required taxonomy labels

- parser coverage failure
- evidence coverage failure
- evidence sufficiency failure
- model utilization failure
- oracle mismatch / predicate invalidity

For each rejected or accepted-but-incorrect episode, record a small audit tuple:

`(available_evidence, missing_evidence, used_correctly, predicate_valid, class_label)`

For ambiguous cases, add a second reviewer or runtime witness to adjudicate.

This is important because model-level gain without causal audit risks mislabeling a sandbox artifact as a reasoning improvement.

---

## 9. Deliverables

The analyst should produce the following artifacts before making any further claim about the reflector effect:

1. paired-seed delta table for all 50 seeds across the relevant conditions
2. bootstrap 95% CI for each outcome metric
3. same-seed improvement rate table
4. evidence-control comparison report
5. compact-model substitution report
6. independent taxonomy audit table for residual failures

The benchmark report remains the canonical outcome artifact, but the paired analysis and control analysis become the causal evidence layer that justifies model-level claims.

---

## 10. Immediate next step

The next phase is not to “add more runs.”

The next phase is:

- compute the paired differences on the existing 50-seed manifest,
- estimate uncertainty around the delta,
- add the evidence-control comparison,
- and then decide whether the residual gap is genuinely due to better evidence or simply a protocol artifact.

This is the direct next step required to support the RFC hypotheses with artifact-backed evidence rather than descriptive intuition.
