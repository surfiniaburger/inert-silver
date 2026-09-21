# Scaled Debate Benchmark Report: Final Pinned Pareto (Angle 3, N=50)

**Evaluation Date:** 2026-09-21  
**Evaluation Scope:** Scaled Benchmark across 50 Virgin Scenarios with Frozen Terminal Pareto Prompts  
**Evaluation Harness:** BARRED-Fleet Swarm (Gemma-4-12B Judge/Verifier, Gemma-4-E4B Debaters)  
**Seed Manifest:** [`scenarios/debate/cve_seeds_benchmark_50.jsonl`](../scenarios/debate/cve_seeds_benchmark_50.jsonl) (50 C codebase scenarios: 25 Safe, 25 Vulnerable)  
**Methodological Protocol:** **Regime 3 (Condition C: Final Pinned Pareto / `--pin-pareto`)** — Evaluates whether accumulated prompt knowledge can replace online adaptation. Debaters initialize with the terminal 669-entry Pareto frontier prompts produced after the five active-online replicates in `artifacts/gepa_pareto_50/pareto_frontier.json`. Unlike Regime 2 (Active Online Learning), live Reflector mutation and prompt rewrite are strictly disabled: failed Round 0 attempts retry in Round 1 using the *same warm prompt without topological mutations*, and no accepted prompts are promoted into the ledger. The Pareto frontier and mutations ledger remain 100% immutable.

---

## 1. Executive Summary: Prompt Knowledge vs. Runtime Adaptation

Angle 3 isolates the contribution of online adaptation from the contribution of the evolved Pareto prompt prior. A frozen Pareto frontier produced 36/50 accepted rows (72.0%), compared with 40.2/50 (80.4% ± 5.5%) under the five-replicate Active Online condition.

The strongest separation occurs after Round-0 failure. Pinned Pareto achieved 8/22 Round-1 recoveries (36.4%), while Active Online achieved 57/113 recoveries (50.4%) across 250 scenario episodes. Round-0 yield was nearly identical between the two warm-prompt conditions (56.0% pinned vs. 57.6% active), suggesting that the principal difference emerges during failure recovery rather than initial adjudication.

The experiment therefore provides evidence that the evolved Pareto prompt prior alone does not reproduce the recovery behavior of the live Reflector. The result supports treating online graph-informed mutation as a distinct architectural capability rather than merely accumulated prompt knowledge.

The pinned condition also preserved the existing safety invariants: zero accepted logic errors and complete anchor grounding among accepted samples. Mean token consumption was 16,822 tokens/seed, compared with 17,260 tokens/seed for Active Online, indicating a modest direct token cost (438 tokens/seed) for online adaptation while producing a higher acceptance yield.

```text
                             ROUND 0
                                │
                   ┌────────────┴────────────┐
                   │                         │
            Pinned (Frozen v669)      Online (Dynamic v355→v669)
                56.0% (28/50)             57.6% (28.8/50)
                   │                         │
                   ▼                         ▼
                FAILURE                   FAILURE
                   │                         │
                   ▼                         ▼
             same prompt retry         graph diagnosis
                   │                         │
                   ▼                   prompt mutation
             36.4% recovery                  │
               (8/22 rows)                   ▼
                                       50.4% recovery
                                        (57/113 rows)
```

---

## 2. Quantitative Performance Matrix

| Metric | Regime 1: Sliced Baseline Mean ($N=5$) | Regime 2: Active Online Mean ($N=5$) | **Regime 3: Final Pinned Pareto Rep 1 (`unrun-pinned-pareto-50-rep1`)** | Contrast: Reg 3 vs. Reg 1 (Baseline) | Contrast: Reg 3 vs. Reg 2 (Online) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Seeds Evaluated** | 50 (25 S / 25 V) | 50 (25 S / 25 V) | **50 (25 S / 25 V)** | Invariant ($N=50$) | Invariant ($N=50$) |
| **Prompt Provenance** | Cold (`baseline_v0`) | Dynamic ($355 \to 669$ muts) | **Frozen Terminal ($669$ muts)** | Evolved vs. Cold | Frozen vs. Evolving |
| **Accepted Training Rows** | 39.20 ± 2.59 (78.4% ± 5.2%) | 40.20 ± 2.77 (80.4% ± 5.5%) | **36 / 50 (72.0%)** | -6.4% | -8.4% |
| **95% Wilson CI (Yield)** | [72.9%, 83.0%] | [73.5%, 87.3%] | **[58.3%, 82.5%]** | Overlapping | Overlapping |
| **Round 0 Accepted Rows** | 36.00 ± 2.00 (72.0%) | 28.80 ± 2.49 (57.6%) | **28 / 50 (56.0%)** | -16.0% (Anchor Gap) | -1.6% (Near-Identical) |
| **Round 0 Rejections** | 14.00 ± 2.00 (28.0%) | 21.20 ± 2.49 (42.4%) | **22 / 50 (44.0%)** | +16.0% | +1.6% |
| **Round 1 Recoveries** | 3.20 ± 1.30 (22.9%) | 11.40 ± 3.21 (50.4%) | **8 / 22 (36.4%)** | +13.5% | -14.0% (Post-Failure Gap) |
| **Accepted Logic Errors (INV-1)** | **0.0000 ± 0.0000** | **0.0000 ± 0.0000** | **0 (0.0000)** | Invariant (100% clean) | Invariant (100% clean) |
| **Attempt Logic Errors** | 3.60 ± 2.61 (5.4%) | 7.20 ± 1.30 (9.7%) | **4 / 72 (5.6%)** | +0.2% | -4.1% |
| **Total Attempts** | 67.20 ± 3.27 (1.34/seed) | 74.00 ± 5.74 (1.48/seed) | **72 (1.44/seed)** | +0.10/seed | -0.04/seed |
| **Total Benchmark Tokens** | 791,116.8 ± 64,572.6 | 863,003.4 ± 46,854.9 | **841,103** | +6.3% | -2.5% |
| **Mean Tokens / Seed** | 15,822.3 ± 1,291.5 | 17,260.1 ± 937.1 | **16,822.1** | +6.3% (+1,000 tok) | -2.5% (-438 tok) |
| **Tokens / Accepted Row** | 20,316.3 ± 2,820.5 | 21,571.0 ± 2,179.0 | **23,364.0** | +15.0% | +8.3% (Yield dilution) |
| **Safe Accepted Rate** | 18.20 ± 2.39 (72.8%) | 19.60 ± 2.07 (78.4%) | **18 / 25 (72.0%)** | -0.8% | -6.4% |
| **Vulnerable Accepted Rate** | 21.00 ± 0.71 (84.0%) | 20.60 ± 1.14 (82.4%) | **18 / 25 (72.0%)** | -12.0% | -10.4% |

---

## 3. Detailed Empirical Analysis

### A. The Separation: Epistemic Adaptation vs. Prompt Memory
The primary architectural insight from Angle 3 is that **the warm Pareto frontier does not transfer its full benefit into a frozen policy**.

At initial evaluation (Round 0), the frozen warm prompt and the actively adapting system perform nearly identically:
- **Pinned (v669):** 56.0% (28/50)
- **Active Online (v355):** 57.6% (28.8/50)

However, when an initial attempt fails, their trajectories decouple:
- In the **Pinned** condition, debaters re-debate the refined sample using the *identical static prompt*, recovering only **8 of 22 failed episodes (36.4%)**.
- In the **Active Online** condition, the Reflector analyzes the specific AST/CFG failure node and injects a mutated prompt directive tailored to the observed failure signature, achieving a **50.4% cumulative recovery rate (57/113)**.

The live Reflector is therefore not primarily optimizing the initial pass; it is functioning as a **runtime epistemic control loop** that intervenes after the swarm discovers that its first attempt was rejected.

### B. Support for the Instruction Competition Hypothesis
The observation that Round-0 compliance dropped from 72.0% in the cold baseline to ~56–57% in both warm-prompt conditions provides strong correlational evidence for a warm-prompt-associated Round-0 compliance degradation. 

The evolved directives in the 669-mutation frontier (e.g., sink-specific guard checks, bounds invariants, reachability chains) encourage richer vulnerability arguments. However, this semantic richness appears to compete with strict compliance for verbatim anchor extraction:
- 12 attempts failed on `anchors_too_few_after_normalization`.
- 11 attempts failed on `verifier_failed`.

Crucially, this observation **supports** the Instruction Competition Hypothesis, but does not prove its causal mechanism. Chapter 2's **Formatting Shield** intervention (isolating verbatim anchors into an explicit output contract block) will serve as the causal test: if the Formatting Shield restores Round-0 yield to ~72% while retaining the warm prior's analytical depth, the instruction competition mechanism is causally confirmed.

### C. The Economics of Adaptation: Token Tradeoffs
A nuanced economic tradeoff emerges when analyzing token consumption:
1. **Per-Seed Consumption:** Freezing the warm Pareto frontier reduced mean benchmark consumption from **17,260.1 down to 16,822.1 tokens/seed** (a saving of 438 tokens/seed). This indicates that the live Reflector agent's graph diagnosis passes contribute a modest direct computational overhead.
2. **Per-Accepted-Row Consumption:** Because the pinned condition yielded fewer accepted training samples (36 vs. 40.2), its cost per accepted row was actually **higher** (**23,364 vs. 21,571 tokens/accepted row**). 

**The Core Tradeoff:** *Adaptation costs modest tokens per evaluation episode, but the absence of adaptation costs accepted ground-truth rows.*

---

## 4. Diagnostics & Adjudication Observations

### A. Adjudication Split
In this single replicate, accepted outcomes were split **29 Pro / 7 Con** (compared with an average of 21.6 Pro / 18.6 Con in Regime 2). Given the sample size of 36 accepted rows, this asymmetry should be treated as an observational diagnostic that may be influenced by scenario composition and stochastic sampling, rather than an inherent property of the warm Pareto prompt.

### B. Acceptance Breakdown by Safety Class
- **Safe Scenarios:** 18 / 25 (72.0%) accepted (Regime 2 mean: 78.4%).
- **Vulnerable Scenarios:** 18 / 25 (72.0%) accepted (Regime 2 mean: 82.4%).

The active system's advantage appeared across both classes, with a wider gap on vulnerable cases (10.4% difference) than safe cases (6.4% difference). Multi-replicate pinned benchmarks will be needed to verify whether this class asymmetry is systematic.

---

## 5. Architectural Receipts & Verification Hashes

| Item | Value |
| :--- | :--- |
| **Run ID** | `unrun-pinned-pareto-50-rep1` |
| **Run Command** | `uv run python scenarios/debate/run_batch.py --seeds scenarios/debate/cve_seeds_benchmark_50.jsonl --output test_corpus_pinned_pareto_50_rep1.jsonl --mode record --run-id unrun-pinned-pareto-50-rep1 --seed 42 --pin-pareto --gepa-dir artifacts/gepa_pareto_50 --slice-judge` |
| **Output Corpus** | [`test_corpus_pinned_pareto_50_rep1.jsonl`](../test_corpus_pinned_pareto_50_rep1.jsonl) (36 accepted rows) |
| **Attempts Log** | [`artifacts/attempts/unrun-pinned-pareto-50-rep1.jsonl`](../artifacts/attempts/unrun-pinned-pareto-50-rep1.jsonl) (72 attempt records) |
| **Manifest** | [`artifacts/runs/unrun-pinned-pareto-50-rep1/batch_manifest.json`](../artifacts/runs/unrun-pinned-pareto-50-rep1/batch_manifest.json) (50 items completed) |
| **Frontier SHA256 (Pre & Post)** | `516c2f76de1af896a9a410fe86133b4233fbbec25283a1d92c3dd5a2152e57d0` (Verified Immutable) |
| **Ledger Mutation Count** | `669` (0 mutations added, Verified Immutable) |
