# Gemini Evidence-vs-Protocol Control and Paired Uncertainty Report

## Scope and status

This report is a supplement to the benchmark and reproducibility records. It does not replace the primary benchmark summary; it is the causal-analysis layer required to interpret whether the observed improvements are attributable to the reflector/evidence mechanism, the progressive escalation protocol, or simply run-to-run noise.

The repo already contains the necessary evidence for a first-pass paired analysis:

- `reports/gemini_seed_paired_ledger.csv`
- `reports/gemini_seed_paired_summary.json`
- `reports/gemini_paired_uncertainty_and_causal_control_spec.md`
- `reports/gemini_paired_uncertainty_and_causal_control_report.md`

This new report updates the interpretation in light of the same-seed ledger and makes the causal limit explicit.

---

## 1. What the repo can support now

The benchmark is fixed to a 50-seed manifest, run across five replicates. The canonical paired unit is therefore the same seed under the same benchmark condition across replicates, not simply the run mean.

The current artifact-backed paired ledger gives:

- 50 seeds
- 5 replicates
- 250 same-seed paired observations
- baseline accepted total: 140
- escalated accepted total: 148
- mean paired delta accepted: +0.032 per pair
- positive paired deltas: 20
- negative paired deltas: 12
- zero deltas: 218

This is the key fact: the aggregate uplift is real in descriptive terms, but the same-seed paired effect is small and highly concentrated in a minority of seeds. The current evidence is not strong enough to claim a decisive causal effect without a proper protocol-vs-evidence control.

---

## 2. Paired-seed calculation

From the canonical same-seed ledger:

| Metric | Baseline total | Escalated total | Mean paired delta |
| --- | ---: | ---: | ---: |
| accepted rows | 140 | 148 | +0.032 |
| vulnerable accepted |  |  | +0.024 |
| safe accepted |  |  | +0.008 |

The paired summary also records:

- positive accepted deltas: 20
- negative accepted deltas: 12
- zero accepted deltas: 218

This means that in a same-seed comparison, the escalated condition is not clearly better on the majority of paired observations. The effect is concentrated in a subset of seeds and therefore should be reported as suggestive rather than definitive.

The current paired summary implies a rough paired mean effect on accepted yield of about +3.2% relative to the baseline mean when weighted by pair count, but the effect is far weaker than the run-level aggregate would suggest.

---

## 3. Interpretation of the run-level vs paired-level evidence

There are two different signals in the repo:

1. Run-level aggregate evidence
   - baseline accepted mean: 28.0
   - escalated accepted mean: 29.6
   - raw uplift: +1.6 accepted rows, or about +3.2 pp

2. Same-seed paired evidence
   - mean pair delta accepted: +0.032
   - paired distribution is mostly zero, with few positive gains and some negative losses

These are not contradictory. They describe different layers of the evidence:

- the run-level aggregate is a descriptive comparison of means across repeated run families,
- the same-seed paired analysis is the stronger causal comparison because it holds the benchmark seed fixed.

The same-seed paired result is the more defensible current estimate, and it does not support a strong causal claim.

---

## 4. Why this is not yet a clean evidence-vs-protocol result

The repo does not yet contain the required 2x2 control for clean attribution.

The current escalated condition changes more than one variable at the same time:

- reflective evidence injection
- progressive escalation policy
- retry / repair mechanics
- model-side reasoning budget

So the current data cannot separate the following effects cleanly:

- evidence effect
- escalation effect
- interaction effect

This is exactly why the paired analysis is necessary but not sufficient.

The real causal-control design should compare:

1. raw input, no reflector
2. structured evidence, no escalation policy change
3. structured evidence with progressive escalation

The comparison of (2) vs (1) isolates the effect of the evidence interface. The comparison of (3) vs (2) isolates the escalation-policy effect. The remaining difference is the interaction term.

At present, that control is not available in the repo, so any stronger attribution would be over-claiming.

---

## 5. RFC failure taxonomy as applied here

The RFC distinguishes between model reasoning reach, evidence reach, and oracle labeling authority. This distinction matters because a benchmark yield increase does not automatically mean the underlying epistemic mechanism improved.

### 5.1 The strongest-supported claim

The strongest-supported claim in the current Gemini evidence is:

- the residual failures are increasingly concentrated in proof sufficiency, semantic adjudication, and final validation quality, rather than in raw pathway extraction alone.

This is consistent with the RFC idea that once the model sees the right structure, the remaining failure is often not that it cannot find the relevant code, but that it still fails to prove the vulnerability or reject the safe case correctly.

### 5.2 The weaker or still-open claims

The repo evidence does not yet establish any broad, universal claim that the reflector or progressive escalation fully substitutes for frontier reasoning.

In RFC terms:

- H1 (evidence substitution) is only partially supported and not confirmed as equivalent substitution
- H2 (evidence coverage / extraction quality) is likely relevant but still not cleanly isolated from the protocol
- H3 is the best-supported interpretation for Gemini: the remaining errors are dominated by proof sufficiency and adjudication quality, not merely by missing evidence
- H4 is not confirmed after the final artifact audit; the earlier point-estimate ratio and the later representative audit do not support treating H4 as a final conclusion

This is the correct reconciliation of the earlier discrepancy: the earlier H4 language was provisional and heuristic, while the final artifact-backed conclusion is that H4 remains open until the evidence-vs-protocol control is executed.

---

## 6. Benchmark meaning and reproducibility meaning

The earlier confusion between the fixed 50-seed benchmark and the five replicate runs is important:

- the benchmark manifest is fixed: 50 seeds
- the replicate family is repeated execution of that same fixed manifest
- mean ± SD or CI reporting refers to run-to-run variability, not to a different seed set

This means the benchmark scorecard remains the primary artifact for accepted yield, while the reproducibility doc explains the repeated-run structure. The RFC remains a supplementary interpretation layer that explains why the observed differences arise.

This separation should be preserved in both the documentation and the interpretation.

---

## 7. Recommended interpretation for the current repo

The evidence supports the following statement:

The Gemini escalated condition shows a small, directionally positive gain on accepted yield relative to baseline when viewed descriptively and in paired aggregate terms, but the same-seed ledger shows the effect is weak, sparse across seeds, and not yet strong enough to assert a decisive causal mechanism. The current data do not isolate whether the gain is caused by evidence injection, the progressive escalation protocol, or an interaction thereof.

This is the strongest defensible reading of the current repo.

---

## 8. Immediate next step

The highest-value next action is not more blind replication. It is the evidence-vs-protocol control:

- same 50-seed manifest
- same adjudication rules
- same retry budget
- compare raw input vs structured evidence vs progressive escalation

That design will answer the actual causal question:

- Is the uplift from the reflector/evidence layer?
- Or from the escalation protocol?
- Or from both together?

Without that control, the current report should remain framed as exploratory and suggestive rather than conclusive.

---

## 9. Final conclusion

The current Gemini benchmark family supports a modest improvement signal, but not a decisive causal conclusion. The paired-seed ledger is the decisive evidence currently available, and it shows a weak positive effect with substantial uncertainty and no clean separation between protocol and evidence effects. The RFC remains useful as a failure-mode explanation, but not as a replacement for the benchmark outcome record.

The recommended posture is:

- benchmark reports are canonical for outcome numbers,
- reproducibility docs explain run structure,
- RFC taxonomy explains residual failure modes,
- causal claims remain provisional until the evidence-vs-protocol ablation is run.
