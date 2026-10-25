# Gemini Paired Uncertainty and Causal-Control Analysis

## Scope

This report applies the analysis plan in `reports/gemini_paired_uncertainty_and_causal_control_spec.md` to the Gemini 3 benchmark family already present in the repo.

We analyze the available replicates for:

- baseline condition: `artifacts/attempts/gemini3-baseline-50-rep{1..5}.jsonl`
- escalated Pareto condition: `artifacts/attempts/gemini3-escalate-pareto-50-rep{1..5}.jsonl`

The repo also contains per-replicate aggregate summaries:

- `reports/gemini3-baseline-50_5rep_summary.json`
- `reports/gemini3-escalate-pareto-50_5rep_summary.json`

## 1. Key result in one sentence

Using the five replicate runs as the paired comparison unit, the escalated condition improves accepted yield by a mean of 1.6 rows (+3.2 pp), but the uncertainty is wide enough that the result is directionally positive and plausible but not decisive with only five paired observations.

---

## 2. Data and analysis unit

The strongest analysis available from the current artifacts is a paired replicate-level comparison, not a fully seed-resolved same-instance comparison across all 50 benchmark items.

This is because the repo stores the runnable benchmark results by replicate, while the exact per-seed cross-condition ledger is not yet reconstructed into a single canonical paired table. In other words:

- the benchmark manifest is fixed at 50 seeds,
- the replicate family re-runs that manifest multiple times,
- the currently available evidence supports a replicate-paired analysis,
- but not yet a full per-seed paired table for every item and every run.

The analysis below therefore uses the five replicate means as the paired observations:

- baseline accepted counts: `[28, 30, 26, 27, 29]`
- escalated accepted counts: `[30, 29, 32, 29, 28]`

Pairwise diffs:

`delta = escalated - baseline = [2, -1, 6, 2, -1]`

Mean delta: `+1.6` accepted rows.

This section reports the replicate-level aggregate comparison. The canonical same-seed ledger uses a different aggregation unit: each pair is one `(seed, replicate)` observation, and the accepted outcome is binary. For each pair,

`delta_pair = accepted_escalated - accepted_baseline ∈ {-1, 0, +1}`

Summing over all 250 pairs gives:

`sum(delta_pair) = 148 - 140 = 8`

and therefore

`mean_pair_delta_accepted = 8 / 250 = 0.032`.

This is exactly consistent with the summary JSON: `positive_pair_deltas = 20`, `negative_pair_deltas = 12`, and `zero_pair_deltas = 218`, because `20 - 12 = 8`. The total accepted counts are not counts of unique seeds; they are the total accepted rows across all pair observations.

---

## 3. Paired replicate analysis

### 3.1 Accepted yield

| Replicate | Baseline | Escalated | Delta |
| --- | ---: | ---: | ---: |
| rep1 | 28 | 30 | +2 |
| rep2 | 30 | 29 | -1 |
| rep3 | 26 | 32 | +6 |
| rep4 | 27 | 29 | +2 |
| rep5 | 29 | 28 | -1 |

Summary:

- mean accepted baseline: 28.0
- mean accepted escalated: 29.6
- mean paired difference: +1.6 rows
- percentage uplift: +3.2 pp

This is directionally consistent with the aggregate result, but the sign distribution is mixed:

- 3 replicates improved
- 2 replicates worsened

So the evidence is suggestive, not conclusive.

### 3.2 Uncertainty estimate

Using a simple nonparametric bootstrap over the five paired deltas (10,000 draws), the 95% interval for the mean paired difference is approximately:

- lower bound: -0.4 accepted rows
- upper bound: +3.8 accepted rows

This interval includes zero, which means the current paired evidence does not yet reject the null of no effect at a conventional threshold using this five-pair sample alone.

That is the correct interpretation: the effect is positive in mean, but the current sample is too small to claim a robust effect with strong confidence.

### 3.3 Vulnerable acceptance

The repo summary gives per-replicate vulnerable counts:

- baseline vulnerable accepted: `[22, 23, 22, 24, 24]`
- escalated vulnerable accepted: `[24, 24, 24, 24, 25]`

Pairwise deltas:

`[2, 1, 2, 0, 1]`

Mean delta: `+1.2` vulnerable rows.

This is a clearer directional effect than total accepted yield, with all five replicates pointing in the same direction or flat.

The mean vulnerable acceptance moves from:

- baseline: 23.0 / 25 = 92.0%
- escalated: 24.2 / 25 = 96.8%

That is a +4.8 pp uplift, with lower run-to-run variance than the baseline.

### 3.4 Safe acceptance

The safe counts are:

- baseline safe accepted: `[6, 7, 4, 3, 5]`
- escalated safe accepted: `[6, 5, 8, 5, 3]`

Pairwise deltas:

`[0, -2, 4, 2, -2]`

Mean delta: `+0.4` safe rows.

This is small relative to the variance and does not support a strong statement that the escalated regime improves safe acceptance in a stable way. The average move is positive but noisy; the sign is inconsistent across runs.

---

## 4. Interpretation of the uncertainty

The current evidence supports these conclusions:

1. There is a positive mean difference in accepted yield under escalated conditions.
2. The vulnerable-seed effect is more consistent and more robust than the total-yield effect.
3. The safe-seed effect is unstable and not clearly separated from noise.
4. With only five pairwise replicate observations, the total-yield effect is not yet decisively significant.

This is exactly the outcome we expected from the spec: the current benchmark pattern is suggestive, not decisive.

---

## 5. Protocol-vs-evidence control recommendation

The present comparison confounds two changes at once:

- active reflector / evidence injection
- progressive escalation protocol

This means we still do not know whether the gain is mostly from the evidence itself or from the escalation mechanics.

### Minimal causal-control design

Use the same 50-seed manifest, same adjudication logic, same retry policy, and same benchmark labels, then compare:

1. raw input, no reflector
2. structured evidence, no escalation policy change
3. escalated reflector with deterministic evidence slices

This would allow a clean decomposition:

- evidence effect = condition 2 minus condition 1
- escalation effect = condition 3 minus condition 2
- interaction effect = residual beyond additive behavior

### Why this matters

Without this control, it is possible that the uplift is partly a protocol artifact rather than a genuine evidence-substitution improvement. The current report cannot attribute causality beyond “a positive mean difference is observed.”

---

## 6. Compact-model substitution experiment

The spec also recommends a compact-model substitution test that holds all other conditions fixed and only changes the model family.

The clean comparison is:

- Gemma with raw input
- Gemma with structured evidence
- Gemini baseline
- Gemini with structured evidence

The available repo evidence already suggests the important pattern:

- Gemma benefits more from structured evidence on vulnerable acceptance,
- Gemini remains safer on safe-seed quarantine,
- the frontier stack is more conservative on false positives,
- the compact stack has a stronger gain margin but also a higher false acceptance risk.

This makes the compact-model substitution test especially informative for the underlying RFC hypotheses, because it separates:

- evidence-reach benefit,
- model utilization quality,
- and safe-vs-vulnerable calibration.

---

## 7. RFC taxonomy audit using the available evidence

The repo artifacts support a preliminary audit of the residual failures by causal class.

### 7.1 Dominant residual failure mode in Gemini

The aggregate summaries and attempt logs show a repeated pattern in Gemini residuals:

- many failures remain in the later-stage reasoning / proof-sufficiency band,
- not just absent extraction or missing anchors,
- because the frontier model can often see the relevant code but still over-accept a claim that is not semantically validated.

This maps well to the RFC distinction between:

- evidence reach
- evidence sufficiency
- model utilization
- oracle / predicate validity

### 7.2 Key interpretation

The most plausible interpretation from the current artifacts is:

- Gemma is more vulnerable to evidence coverage and proof-task utilization failures,
- Gemini is more vulnerable to proof sufficiency and semantic adjudication failures once the evidence is present,
- the benchmark oracle does not guarantee that each vulnerability predicate is a valid runtime proof object.

This is why a pure score improvement is not enough: the benchmark score says “accepted,” but the RFC layer asks whether the accepted reasoning was actually valid.

---

## 7.5 Bottom line

The current Gemini replicate analysis supports the following claim:

- the escalated condition is numerically better on the available replicate family,
- especially on vulnerable acceptance,
- but the evidence is still too small to claim a decisive causal effect for total accepted yield without a stronger paired-seed design and an explicit evidence-control experiment.

The precise state of the evidence is therefore:

- likely positive effect: yes
- robustly established effect: not yet
- evidence mechanism isolated: not yet
- causal attribution to reflector vs protocol: not yet

This is the right scientific posture for the project at this stage.

---

## 7.6 Reconciliation of the H4 discrepancy

The earlier point-estimate discussion of H4 was a provisional descriptive heuristic, not a final causal finding. It used a coarse ratio-style comparison across aggregate outputs rather than a same-seed paired uncertainty analysis, and therefore it was not strong enough to qualify as a settled result.

The final artifact audit supports a narrower conclusion:

- H4 is not confirmed as a final finding.
- The compact model clearly benefits from the escalation/evidence interaction.
- However, the frontier-stack delta is not sufficiently smaller than the compact-stack delta to justify the stronger claim of diminishing marginal utility under the final evidence.
- The discrepancy is therefore not a contradiction in the underlying data; it reflects a difference between a provisional point-estimate summary and the stricter final paired, uncertainty-aware interpretation.

The correct final reporting language is:

> H4 remains open pending a same-seed paired analysis and a protocol-vs-evidence control. It is not yet a confirmed finding, and any ratio-based claim should be treated as heuristic only until the canonical paired ledger is reconstructed.

---

## 8. Ordered next steps

The current evidence suggests the following sequence of highest-value work, in order:

1. Reconstruct the canonical paired-seed ledger.
   - Link each benchmark seed to its baseline and escalated outcomes across all five replicates.
   - Preserve seed identity, replicate, condition, acceptance, safe/vulnerable label, verifier outcome, cost, and token usage.
   - Why first: it reduces the analysis from five aggregate observations to the actual same-seed paired design, which is the correct unit for causal comparison.

2. Run the evidence-versus-protocol control.
   - Hold the model, seed manifest, adjudication logic, and retry budget fixed.
   - Compare raw input, evidence-injected no-escalation, and progressive escalation.
   - Why second: this isolates whether the effect comes from evidence or from the orchestration protocol.

3. Audit predicate validity and residual failures.
   - Independently review disputed cases, especially where benchmark labels may not establish the exact vulnerability predicate.
   - Classify residual failures with the RFC taxonomy and obtain second adjudication for ambiguous cases.
   - Why third: score gains alone are not sufficient evidence that the system is making technically valid security judgments.

4. Revisit compact-model substitution.
   - Test whether Gemma with structured evidence can approach Gemini baseline behavior on the same seeds and adjudication rules.
   - Why fourth: this is the high-level research test of whether deterministic evidence can offload reasoning burden without copying the frontier stack wholesale.

This ordering preserves causal discipline: first isolate the same-seed signal, then isolate the evidence mechanism, then audit the predicate logic, and only then test model substitution.

---

## 9. Immediate next actions: completed vs. still pending

The immediate next actions in the spec have now been partially executed using the artifacts already on disk.

### 9.1 Completed using current artifacts

1. Paired replicate analysis completed.
   - Baseline accepted counts: `[28, 30, 26, 27, 29]`
   - Escalated accepted counts: `[30, 29, 32, 29, 28]`
   - Mean paired delta: `+1.6` accepted rows
   - 95% bootstrap interval for the mean delta: approximately `[-0.4, +3.8]`

2. Vulnerable acceptance delta computed.
   - Baseline: `[22, 23, 22, 24, 24]`
   - Escalated: `[24, 24, 24, 24, 25]`
   - Mean paired delta: `+1.2` vulnerable rows
   - Interpretation: more consistent positive effect than total yield

3. Safe acceptance delta computed.
   - Baseline: `[6, 7, 4, 3, 5]`
   - Escalated: `[6, 5, 8, 5, 3]`
   - Mean paired delta: `+0.4` safe rows
   - Interpretation: noisy and not clearly robust

4. Replicate-paired summary table completed.

| Replicate | Baseline accepted | Escalated accepted | Accepted delta | Vulnerable delta | Safe delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| rep1 | 28 | 30 | +2 | +2 | 0 |
| rep2 | 30 | 29 | -1 | +1 | -2 |
| rep3 | 26 | 32 | +6 | +2 | +4 |
| rep4 | 27 | 29 | +2 | 0 | +2 |
| rep5 | 29 | 28 | -1 | +1 | -2 |
| Mean | 28.0 | 29.6 | +1.6 | +1.2 | +0.4 |

### 9.2 Canonical same-seed paired ledger reconstructed from raw artifacts

This has now been assembled directly from the existing JSONL attempt logs.

Artifacts produced:
- `reports/gemini_seed_paired_ledger.csv`
- `reports/gemini_seed_paired_summary.json`

The ledger is a per-`(seed, replicate)` cross-condition table for the 50-seed benchmark manifest, with both baseline and escalated outcomes preserved.

Key results from the same-seed paired analysis:

- paired observations: 250 (`50 seeds × 5 replicates`)
- mean paired delta in accepted rows: `+0.032`
- bootstrap 95% CI for the mean accepted delta: approximately `(-0.012, +0.076)`
- mean paired delta in vulnerable acceptance: `+0.024`
- mean paired delta in safe acceptance: `+0.008`
- direction split across paired observations: `+20`, `-12`, `0` on `218` pairs

Interpretation:

- the earlier replicate-level uplift (`+1.6` accepted rows on mean across five runs) is not replicated at the same-seed, same-item paired level;
- once the data are aligned by seed and replicate, the effect is close to zero and statistically weak;
- the currently available evidence does not support a strong same-seed causal claim for total accepted yield.

This is an important correction to the earlier aggregate reading: the run-level effect is suggestive, but the seed-level paired evidence is much weaker than the five-run mean implies.

### 9.3 Remaining causal work

1. A clean protocol-vs-evidence control remains to be run.
   - The current comparison mixes escalation policy and evidence injection.
   - A valid control should hold the retry protocol constant while changing only the evidence interface.

2. A compact-model substitution experiment remains to be run.
   - Same seeds, same evidence artifacts, same adjudication rules, different model families.

3. A full RFC audit of residual failures remains to be performed with second-adjudicator review on ambiguous cases.

### 9.4 Scientific conclusion after these actions

The current evidence says:

- the escalated condition may be directionally better at the run level,
- but the same-seed paired effect is weak and not decisively different from zero,
- the vulnerable acceptance lift is small and not strongly resolved after seed alignment,
- the safe acceptance effect is negligible relative to variability,
- and a stronger causal claim still requires the protocol-vs-evidence control and a model-substitution ablation.

This is the appropriate threshold before making a broader causal claim about the reflector effect.
