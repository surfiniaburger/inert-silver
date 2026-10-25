# A Debate Benchmark Can Report a Win Without Proving the Claim That Won

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

## What I Benchmarked

In code-security review, an accepted outcome tells us that a pipeline approved a specific predicate; it does not establish that the predicate describes a real vulnerability.

Seed 51 from our earlier local 50-seed analysis made the distinction concrete: the historical label marked the code vulnerable, while our local review questioned the specific claim of an arbitrary-file overwrite through a `mktemp()`/`rename()` symlink race. The issue was whether POSIX `rename()` would follow the destination symlink as the predicate required. This is a local analysis of a different seed—not a result confirmed by the new Kaggle task.

The RFC gives us three separate questions to ask about a decision:

- **Model reasoning reach:** What can the model establish from the code and its technical knowledge?
- **Reflector evidence reach:** Which structural facts can deterministic tools extract and put in front of the model?
- **Oracle labeling authority:** What does the benchmark’s historical label tell us—and, just as importantly, what does it not prove about the exact predicate?

Keeping these separate stops an accepted benchmark outcome from becoming its own proof of correctness.

The RFC’s evidence-substitution hypothesis is that structured, deterministic evidence can extend a model’s effective verification reach without increasing model size. It is a hypothesis to test—not a claim of equivalence: the reflector can miss relevant code, a syntax slice may not prove a runtime contract, and a model can fail to use evidence it receives.

BARRED asks two debaters to argue whether a code snippet satisfies a security predicate; a judge, verifier, and deterministic evidence gates determine whether the outcome is accepted. In the local BARRED stack, we ran the same 50-seed corpus across five replicates, comparing a raw-input baseline with progressive escalation and reflector evidence. Because the escalated condition changes both evidence and protocol, this comparison cannot isolate the evidence effect.

## Models Tested

- **Compact stack:** Ollama Gemma 4-E4B debaters with Gemma 4-12B-fast judging and verification.
- **Frontier stack:** Vertex AI Gemini 3.5 Flash debaters with Gemini 3.8 Flash judging and verification.

We chose these stacks to compare a compact model with a frontier model under the same seed set and acceptance framework. The judge/verifier is a separate role in each pipeline, not an independent ground-truth oracle; that is why the RFC also asks whether predicates are valid, rather than treating the judge’s decision as proof.

Separately, the ten-seed Kaggle task was run with Gemini 3.7, but the reported run produced empty debate replies and failed the non-empty-statement checks, so it is diagnostic—not a valid score. Our one-seed local smoke test used Gemini 3 Flash Preview with a 2,048-token cap; it passed all six assertions and accepted that case, but does not validate or reproduce the Kaggle run.

## Findings

Across five paired runs, mean accepted yield rose from 28.0 to 29.6 of 50 seeds (+1.6 rows per run, or +3.2 percentage points). The matched seed-by-replicate ledger makes the size and concentration of that change clearer: 148 versus 140 accepted outcomes across 250 pairs, with 20 gains, 12 losses, and 218 ties—a net gain of eight. The 95% bootstrap interval over the five run-level differences is approximately −0.4 to +3.8 rows and includes zero. The result is a modest positive signal, not decisive evidence of a stable gain; and since reflector evidence and escalation protocol changed together, it cannot tell us which caused the difference.

A second local comparison shows why total acceptance is a poor standalone score. On the same 50-item holdout, the Gemma baseline’s five-run mean accepted 80% of safe-labeled cases and 84% of vulnerable-labeled cases; the reported Gemini baseline run accepted 24% and 88%, respectively. This is an illustrative calibration contrast, not a definitive model ranking: the replicate counts differ, and historical labels do not certify every specific predicate. It is still a reason to report safe- and vulnerable-labeled outcomes separately and audit disputed claims.

The RFC taxonomy helped us avoid calling every rejected case “hallucination.” Its evidence pipeline asks four different questions: did the structured output parse, did the reflector capture the relevant code, was that evidence enough to establish the runtime claim, and did the model use it correctly? A separate seven-axis diagnosis also distinguishes reasoning and extraction failures from invalid predicates, oracle disagreements, and genuine ambiguity. We treat these as case-level diagnostic labels, not as proof by themselves.

That distinction changed one local result. In a representative 50-seed Gemini escalated run, an early summary classified 18 of 20 terminal failures as evidence-insufficiency cases. A later case-level audit revised the split to 9 evidence-insufficiency, 5 model-reasoning, 4 predicate-invalidity, 1 parser/interface, and 1 semantic-ambiguity case. This corrected breakdown is from one local run—not the five-run family and not the Kaggle task—and illustrates why the taxonomy has to be supported by the code and the case record.

### What I would measure next (not yet run)

The local runs above compare a raw-input baseline with an escalated, reflector-assisted condition; they do not isolate the causes of the difference. The following are proposed follow-ups, not completed experiments:

1. **Separate evidence from orchestration.** On the same 50 seeds, hold the model, adjudication rules, and retry budget fixed. Compare (a) raw input with the baseline protocol, (b) structured evidence with the baseline protocol, and (c) structured evidence with progressive escalation. The contrast between (b) and (a) estimates the evidence contribution under the baseline protocol; (c) versus (b) estimates the added effect of progressive escalation when structured evidence is present. These three arms do **not** estimate a formal evidence-by-protocol interaction. To measure that interaction, add a fourth arm: raw input with progressive escalation. Report outcomes per matched seed and replicate, separating vulnerable acceptance from safe-case false acceptance, and include token use and cost.
2. **Audit disputed predicates and residual failures independently.** Re-examine the case records, code anchors, and relevant runtime or platform contracts for disputed predicates and failures. Record the evidence supporting each RFC classification—parser coverage, evidence coverage, evidence sufficiency, model utilization, or predicate validity—and distinguish model-audited interpretations from independently verified conclusions. This case-level audit is not complete.
3. **Test compact-model substitution under matched conditions.** Compare Gemma with structured evidence against Gemini baseline behavior using the same seed manifest, adjudication rules, and retry budget. Measure vulnerable acceptance, safe-case false acceptance, predicate/mechanism validity, tokens, and cost. The existing local comparisons motivate this test but do not complete it: the model-stack and protocol differences mean they cannot establish that Gemma plus evidence substitutes for Gemini.

These controls matter because the Kaggle Gemini 3.7 run currently available to us produced empty debate replies and is not a valid score, while the one-seed local Gemini 3 Flash Preview smoke test used a different model and a local-only token cap. Neither result confirms these planned experiments or the local RFC interpretations on Kaggle.

## My Benchmark

[Code Boundary Decisions on Kaggle](https://www.kaggle.com/benchmarks/surfiniaburger/code-boundary-decisions)

#kagglechallenge
