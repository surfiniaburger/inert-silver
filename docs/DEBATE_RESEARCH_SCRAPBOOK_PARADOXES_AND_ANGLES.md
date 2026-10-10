# Debate Research Scrapbook: Paradoxes, Prompt Lineage, & Architectural Angles

> **Status:** Living Document / Historical Reference  
> **Repository:** `silver-one` / `modular-metacog-swarm-v3`  
> **Tracking:** Evolution from $N=10$ Pilot to $N=50$ Scaling, Invariant Behavior, and Chapter-by-Chapter Roadmaps.

---

## 1. Executive Summary & Philosophy: Chapter 1 vs. Chapter 2

As our multi-agent neurosymbolic debate benchmark transitioned from initial 10-seed exploratory trials ($N=10$) to rigorous 50-seed statistical evaluation ($N=50$), maintaining scientific integrity requires a strict boundary between **System / Architectural Variables** and **Prompt Engineering Variables**.

We define two distinct historical epochs:

- **Chapter 1: The Empirical Evaluation of Systems under the Historical Prompt Lineage**
  - **Prompt Lineage:** Original un-mutated baseline prompt (`baseline_v0`) and the cumulative 355-step GEPA evolved prompts (`gepa_local`).
  - **Core Regimes Evaluated:**
    1. *Regime 1: Stationary AST Slicing Baseline* ($78.4\% \pm 5.2\%$ yield, 5 replicates, $N=250$).
    2. *Regime 2: Active Online Learning* (AST Slicing + Live Reflector Agent + Dynamic Pareto mutation library, 5 replicates, $N=250$).
    3. *Regime 3: Warm Pinned Pareto* (AST Slicing + Static Pareto library without live mutations, 5 replicates, $N=249$).
    4. *Regime 4: Progressive Escalation / Angle 4* (Cold Round 0 Baseline $\to$ Adaptive Warm Pareto Round 1 live Reflector on failure, 5 replicates, $N=250$: **$85.20\% \pm 2.28\%$ yield**, **$60.22\%$ recovery**, **18,410.9 tokens/row**, 0 accepted logic errors).
  - **Principle:** Under Chapter 1, debater system prompts and anchor rules are strictly kept invariant to ensure that all differences across runs reflect pure algorithmic mechanisms (slicing, reflection, Pareto mutation), not ad-hoc prompt tweaking.

- **Chapter 2: Targeted Grounding & Structural Formatting Shields**
  - **Motivation:** Systematic resolution of the paradoxes uncovered during Chapter 1 (the *Instruction Overload / Round 0 Anchor Trap* and the *Refinement Tax*).
  - **Target Interventions:** Angle 1 (Formatting Shield: Anchor-First Invariant Blocks) and Angle 2 (Targeted Anchoring / Syntactic Grounding).

---

## 2. Empirical Telemetry & Core Hypotheses (Chapter 1)

### Telemetry Finding 1: The "Refinement Tax" Tradeoff
- **Empirical Observation:**
  - In Regime 1 (Stationary Slicing Baseline), first-pass Round 0 yield was high ($72.0\%$, 36/50 seeds accepted on attempt 1), with only 14 seeds requiring refinement.
  - In Regime 2 (Active Online Adaptation with evolved prompt `v355`), Round 0 rejections increased:
    - Rep 1: 24 initial failure episodes $\to$ 14 recovered on Round 1 ($58.3\%$).
    - Rep 2: 26 initial failure episodes $\to$ 7 recovered on Round 1 ($26.9\%$).
    - Cumulative ($N=2$): **50 Round 0 failure episodes triggered refinement; 21 were recovered on Round 1 ($42.0\%$ recovery rate)**.
- **The Tradeoff:**
  - The live Reflector is demonstrably effective at error recovery (rescuing $42\%$ of otherwise lost runs).
  - However, **recovery capability $\neq$ efficiency**. Each Round 1 debate attempt burns $\approx 11,000$ tokens.
  - Incurring $\approx 25$ failure episodes per replicate costs $\approx 275,000$ tokens of refinement burn, offsetting the token savings achieved by slicing the Judge context.

### Quantitative Metric: Recovery Efficiency ($\tau_{\text{rec}}$)
To evaluate the economic viability of the Reflector beyond crude total token counts, we formalize **Tokens per Recovered Episode**:

$$\text{Recovery Benefit} = \text{Episodes}_{\text{Round 1 Accepted}}$$
$$\text{Refinement Cost} = \sum \text{Tokens}_{\text{Round 1 Attempts}}$$
$$\tau_{\text{rec}} = \frac{\text{Refinement Cost}}{\text{Recovery Benefit}} = \mathbf{\text{Tokens Per Recovered Episode}}$$

- Across Reps 1 & 2: $\approx 550,000$ refinement tokens were spent to yield 21 recovered rows:
  $$\tau_{\text{rec}} \approx \mathbf{26,190 \text{ tokens / recovered episode}}$$
- This provides an actionable engineering benchmark: any intervention in Chapter 2 that prevents an episode from failing Round 0 saves $\approx 26,000$ tokens on that seed.

### Core Systems Hypothesis: Induced vs. Repaired Failures
> **Working Hypothesis:** *Online adaptation is recovering failed attempts, but the instruction structure of the evolved prompt may be inducing the very syntactic failures that the Reflector subsequently repairs.*

**Competing Explanations (To be Isolated in Chapter 2):**
1. *Instruction Competition:* Advanced vulnerability analysis directives compete for model attention against the strict invariant requirement to cite verbatim line anchors.
2. *Context / Instruction Bloat:* The length of cumulative mutations increases prompt token mass, diluting syntactic compliance.
3. *Output Schema Absence:* Without an explicit output format contract, the model prioritizes natural language prose over exact bracketed citation syntax.
4. *Reasoning Burden:* Deeper semantic analysis increases generation length, pushing the model away from terse extraction.

---

## 3. The 6-Condition Factorial Ablation Matrix (Chapter 2 Design Space)

Rather than pursuing ad-hoc prompt variations, Chapter 2 is formalized as a systematic factorial matrix to isolate the contribution of each architectural layer:

| Condition | Description | AST Slice | Warm Pareto | Live Reflector | Formatting Shield | Syntactic Anchoring | Core Question Evaluated |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **A** | Unpruned Control | ✗ | ✗ | ✗ | ✗ | ✗ | Historical unpruned baseline ($N=50$) |
| **B** | Sliced Stationary | ✓ | ✗ | ✗ | ✗ | ✗ | **Regime 1:** What is the pure effect of AST Program Slicing? ($78.4\% \pm 5.2\%$) |
| **C** | Pinned Pareto | ✓ | ✓ | ✗ | ✗ | ✗ | **Angle 3:** Is the benefit from the evolved prompt prior or active online mutation? |
| **D** | Active Online | ✓ | ✓ | ✓ | ✗ | ✗ | **Regime 2:** What is the combined effect of live mutation + reflector recovery? |
| **E** | Formatting Shield | ✓ | ✓ | ✓ | ✓ | ✗ | **Angle 1:** Does an invariant output contract eliminate Round 0 anchor drops? |
| **F** | Guided Anchoring | ✓ | ✓ | ✓ | ✓ | ✓ | **Angle 2:** Does deterministic graph grounding assist evidence selection? |

---

## 4. Formal Definition of Architectural Angles

### Angle 1: The Formatting Shield (Output Contract Enforcement)
- **Question:** *Can the same reasoning prompt produce fewer anchor failures simply by moving invariant constraints into an explicit output contract?*
- **Mechanism:** Enforce an immutable, anchor-first output structure:
  ```markdown
  ### MANDATORY VERBATIM ANCHOR BLOCK
  [ANCHOR_1]: `<exact line from untrusted code>`
  [ANCHOR_2]: `<exact line from untrusted code>`
  
  ### VULNERABILITY ARGUMENT
  <debater analysis...>
  ```
- **Hypothesis:** Separates the syntactic constraint from the reasoning task, eliminating Round 0 anchor rejections without restricting cognitive reasoning depth.

### Angle 2: Targeted Syntactic Anchoring (Evidence Selection Interface)
- **Question:** *Can deterministic structural information reduce the model's search space for evidence selection?*
- **Mechanism:** The verifier or pre-filter pre-extracts critical line numbers from the AST slice (e.g., branch conditions, memory allocations) and explicitly instructs debaters: *"Ground your claim on lines [X, Y, or Z]"*.
- **Hypothesis:** Introduces the graph directly into the debater evidence-selection interface, rather than merely using it to slice Judge context.

### Angle 3: Final Pinned Pareto (`--pin-pareto`, Terminal 669-Entry Frontier)
- **Question:** *Can accumulated prompt knowledge replace online adaptation? Does the final evolved warm prior reproduce the high yield and recovery of the active online system without live prompt mutation?*
- **Mechanism:** Freeze the terminal Pareto frontier produced after the 5 active online replicates at mutation step 669. Run stationary evaluation across all 50 seeds with zero Reflector calls, zero mutation writes, and zero prompt edits.
- **Empirical Findings (5 Replicates, $N=249$ Canonical Episodes):**
  - **Overall Yield:** **75.1% ± 4.8% (187/249)** — compared with **80.4% ± 5.5% (201/250)** under Active Online (Regime 2) and **78.4% ± 5.2% (196/250)** under Stationary Baseline (Regime 1).
  - **Round 0 Equivalence (60.2% vs. 57.6%):** Initial pass yields are comparable between pinned (60.2%, 150/249) and online (57.6%, 144/250), both trailing the cold baseline (72.0%, 180/250). The data is consistent with an association between complex domain directives and lower first-pass anchor compliance.
  - **Post-Failure Protocol Gap:** 
    - **Pinned:** Retrying with the *identical frozen warm prompt* achieved a **37.4% recovery rate (37/99)**.
    - **Active Online:** Graph diagnosis + targeted prompt mutation achieved a **50.4% recovery rate (57/113)**, representing an observed +13.0 pp protocol-level difference.
    - *Insight:* Frozen prompt knowledge alone does not reproduce the elevated recovery rates observed under active online reflection.
  - **Token Economics:** Mean benchmark consumption was **823,793 ± 26,160 tokens/run** (16,542 tokens/seed). Tokens per accepted row were **22,127.6 ± 1,996.2** (macro-mean) / **22,026.6** (pooled aggregate), compared to **21,571.0** (Active Online) and **20,316.3** (Baseline).
  - **Invariant Integrity:** 0 accepted logic errors across all 187 accepted rows (INV-1 = 0.0000, 100% clean). The 669-mutation Pareto ledger remained 100% immutable (SHA256 verified). Full report: [`reports/debate_benchmark_50_seed_pinned_pareto.md`](../reports/debate_benchmark_50_seed_pinned_pareto.md).

### Angle 4: Progressive Escalation (`--escalate-pareto`, Cognitive Decoupling)
- **Question:** *Can we capture both the high first-pass compliance of cold prompts and the elevated failure recovery of warm reflection by decoupling execution rounds?*
- **Mechanism:** Debaters execute Round 0 using the cold `baseline_v0` prompt (empty reflector prompt). If and only if an episode fails verification, the Judge dynamically escalates the retry to Round 1: loading the warm Pareto champion as base prompt, extracting AST/CFG failure node diagnostics, and mutating the prompt with the live GEPA Reflector.
- **Empirical Findings (5 Replicates, $N=250$ Canonical Episodes):**
  - **Overall Yield:** **85.20% ± 2.28% (213/250)** — establishing a new benchmark record (+6.8 pp over Sliced Baseline, +10.1 pp over Pinned Pareto).
  - **Round 0 Pass Rate (62.8%):** Initial pass yields averaged 62.8% (157/250), reaching up to 74.0% in Rep 4, avoiding prompt bloat and instruction competition.
  - **Round 1 Post-Failure Recovery (60.22%):** Live AST/CFG mutation from the warm Pareto prior recovered **56 out of 93 failures (60.22%)**, dwarfing static baseline retries (22.9%) and frozen Pareto retries (37.4%).
  - **Compute Economics:** Lowest token cost across all evaluated regimes at **18,410.9 ± 1,914.6 tokens / accepted row** (~10% cheaper than Baseline, ~17% cheaper than Pinned Pareto).
  - **Invariant Integrity:** 0 accepted logic errors across all 213 accepted rows (INV-1 = 0.0000, 100% clean). Full report: [`reports/debate_benchmark_50_seed_progressive_escalation.md`](../reports/debate_benchmark_50_seed_progressive_escalation.md).

---

## 5. Current Experimental Lineage Tracker

| Epoch | Replicate / Run ID | Date | Seed | Prompts Used | Yield (%) | Accept/Attempts | Tokens / Accepted Row | Accepted Logic Errors (INV-1) |
|---|---|---|---|---|---|---|---|---|
| **$N=10$ Pilot** | `baseline-001..005` | 2026-09-08 | 42..46 | `baseline_v0` | 74.0% | 37/50 | 25,300 | 0/37 (0.0%) |
| **$N=10$ Pilot** | `pareto-001..005` | 2026-09-09 | 42..46 | GEPA Online | 88.0% | 44/50 | 19,850 | 0/44 (0.0%) |
| **Regime 1 ($N=50$)** | `unrun-sliced-baseline-rep1..5` | 2026-09-11 | 42..46 | `baseline_v0` (Sliced) | 78.4% | 196/250 | 21,411 | 0/196 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep1` | 2026-09-13 | 42 | GEPA Live (Sliced) | 80.0% | 40/50 | 21,844 | 0/40 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep2` | 2026-09-14 | 43 | GEPA Live (Sliced) | 76.0% | 38/50 | 24,329 | 0/38 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep3` | 2026-09-21 | 44 | GEPA Live (Sliced) | 78.0% | 39/50 | 20,568 | 0/39 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep4` | 2026-09-21 | 45 | GEPA Live (Sliced) | 90.0% | 45/50 | 18,526 | 0/45 (0.0%) |
| **Regime 2 ($N=50$)** | `unrun-sliced-pareto-50-rep5` | 2026-09-21 | 46 | GEPA Live (Sliced) | 78.0% | 39/50 | 22,586 | 0/39 (0.0%) |
| **Regime 3 (Angle 3)** | `unrun-pinned-pareto-50-rep1` | 2026-09-21 | 42 | Terminal Pinned (v669) | 72.0% | 36/50 | 23,364 | 0/36 (0.0%) |
| **Regime 3 (Angle 3)** | `unrun-pinned-pareto-50-rep2` | 2026-09-22 | 43 | Terminal Pinned (v669) | 80.0% | 40/50 | 20,107 | 0/40 (0.0%) |
| **Regime 3 (Angle 3)** | `unrun-pinned-pareto-50-rep3` | 2026-09-22 | 44 | Terminal Pinned (v669) | 70.0% | 35/50 | 23,603 | 0/35 (0.0%) |
| **Regime 3 (Angle 3)** | `unrun-pinned-pareto-50-rep4` | 2026-09-22 | 45 | Terminal Pinned (v669) | 73.5% | 36/49 | 23,772 | 0/36 (0.0%) |
| **Regime 3 (Angle 3)** | `unrun-pinned-pareto-50-rep5` | 2026-09-22 | 46 | Terminal Pinned (v669) | 80.0% | 40/50 | 19,793 | 0/40 (0.0%) |
| **Regime 3 Mean (N=5)** | `unrun-pinned-pareto-50-rep1..5` | 2026-09-22 | 42..46 | Terminal Pinned (v669) | **75.1% ± 4.8%** | **187/249** | **22,128** | **0/187 (0.0%)** |
| **Regime 4 (Angle 4)** | `unrun-escalate-pareto-50-rep1` | 2026-09-23 | 42 | Cold R0 $\to$ Warm Adaptive R1 | 86.0% | 43/50 | 19,523 | 0/43 (0.0%) |
| **Regime 4 (Angle 4)** | `unrun-escalate-pareto-50-rep2` | 2026-09-23 | 43 | Cold R0 $\to$ Warm Adaptive R1 | 88.0% | 44/50 | 17,273 | 0/44 (0.0%) |
| **Regime 4 (Angle 4)** | `unrun-escalate-pareto-50-rep3` | 2026-09-23 | 44 | Cold R0 $\to$ Warm Adaptive R1 | 82.0% | 41/50 | 20,809 | 0/41 (0.0%) |
| **Regime 4 (Angle 4)** | `unrun-escalate-pareto-50-rep4` | 2026-09-24 | 45 | Cold R0 $\to$ Warm Adaptive R1 | 86.0% | 43/50 | 15,889 | 0/43 (0.0%) |
| **Regime 4 (Angle 4)** | `unrun-escalate-pareto-50-rep5` | 2026-09-24 | 46 | Cold R0 $\to$ Warm Adaptive R1 | 84.0% | 42/50 | 18,560 | 0/42 (0.0%) |
| **Regime 4 Mean (N=5)** | `unrun-escalate-pareto-50-rep1..5` | 2026-09-24 | 42..46 | Cold R0 $\to$ Warm Adaptive R1 | **85.20% ± 2.28%** | **213/250** | **18,411** | **0/213 (0.0%)** |

---

## 6. Controlled Decomposition Matrix & Chapter 2 Roadmap

### A. The 5-Condition Clean Decomposition
To cleanly separate **prior quality**, **accumulated knowledge**, and **runtime adaptation**, the controlled evaluation space is formalized as:

```text
                               BARRED-Fleet
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                     PROMPT PRIOR          ADAPTATION
                         │                     │
                   ┌─────┴─────┐               │
                   │           │               │
               baseline      warm             live
                 v0        v355/v669        reflector
                   │           │               │
                   ▼           ▼               ▼
                  R0          R0              R0
                   │           │               │
                   └───────────┼───────────────┘
                               │
                            failure
                               │
                     ┌─────────┴─────────┐
                     │                   │
                 frozen retry         mutation
                     │                   │
                   R1 same             R1 new
                     │                   │
                     ▼                   ▼
```

1. **Condition A: Cold Baseline (`baseline_v0`)** — High Round-0 compliance (72.0%), low failure recovery (22.9%), no prior specialization.
2. **Condition B: Frozen Initial Warm (`v355`)** — Isolates starting prior quality without subsequent accumulation.
3. **Condition C: Frozen Terminal Warm (`v669`)** — Evaluates whether 669 accumulated mutations can replace live adaptation. (Result: 75.1% ± 4.8% yield, 37.4% recovery across 5 replicates, N=249).
4. **Condition D: Active Dynamic Adaptation (`v355 → mutation`)** — Full runtime adaptation: 80.4% yield, 50.4% recovery.
5. **Condition E: Progressive Escalation / Angle 4 (`baseline_v0 R0 → warm v669 mutation R1`)** — Tests the Cognitive Decoupling Hypothesis. (Result: **85.20% ± 2.28% net yield**, **60.22% failure recovery (56/93)**, **18,410.9 tokens/row** across 5 replicates, $N=250$).

### B. Chapter 2: Structural Grounding Interventions (Next)
With Angle 3 having established that the warm prior induces Round-0 compliance drops that online mutation subsequently repairs, and Angle 4 proving that progressive escalation decouples cold triage from deep repair, Chapter 2 directly targets the root cause:
- **Angle 1: Formatting Shield (Output Contract Enforcement):** Enforce immutable anchor-first block syntax to prevent Instruction Competition from dropping Round 0 anchors.
- **Angle 2: Targeted Syntactic Grounding:** Pass candidate AST lines directly to debaters to guide search.
- **Target Benchmark:** Evaluate Angle 1 + Angle 4 to determine whether the Formatting Shield recovers the initial Round 0 pass rate from 62.8% to >75%, potentially pushing net yield above **92%**.
